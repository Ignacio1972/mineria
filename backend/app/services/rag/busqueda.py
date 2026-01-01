"""
Servicio de búsqueda semántica sobre el corpus legal.
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.services.rag.embeddings import get_embedding_service
from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class ResultadoBusqueda:
    """Resultado de búsqueda semántica."""
    fragmento_id: int
    documento_id: int
    documento_titulo: str
    documento_tipo: str
    seccion: str
    contenido: str
    temas: List[str]
    similitud: float


class BuscadorLegal:
    """Buscador semántico sobre corpus legal."""

    def __init__(self):
        self.embedding_service = get_embedding_service()

    async def buscar(
        self,
        db: AsyncSession,
        query: str,
        limite: int = 10,
        filtro_tipo: Optional[str] = None,
        filtro_temas: Optional[List[str]] = None,
        umbral_similitud: float = 0.3,
    ) -> List[ResultadoBusqueda]:
        """
        Busca fragmentos relevantes usando similitud semántica.

        Args:
            db: Sesión de base de datos
            query: Consulta en lenguaje natural
            limite: Número máximo de resultados
            filtro_tipo: Filtrar por tipo de documento ('Ley', 'Reglamento', etc.)
            filtro_temas: Filtrar por temas específicos
            umbral_similitud: Similitud mínima para incluir resultado

        Returns:
            Lista de resultados ordenados por similitud
        """
        logger.info(f"Búsqueda semántica: '{query[:50]}...' (limite={limite}, tipo={filtro_tipo})")

        # Generar embedding de la query
        query_embedding = self.embedding_service.embed_text(query)

        # Convertir embedding a formato string para pgvector
        embedding_str = '[' + ','.join(str(x) for x in query_embedding) + ']'

        # Construir query SQL
        sql = f"""
            SELECT
                f.id as fragmento_id,
                f.documento_id,
                d.titulo as documento_titulo,
                d.tipo as documento_tipo,
                f.seccion,
                f.contenido,
                f.temas,
                1 - (f.embedding <=> '{embedding_str}'::vector) as similitud
            FROM legal.fragmentos f
            JOIN legal.documentos d ON f.documento_id = d.id
            WHERE d.estado = 'vigente'
        """

        params = {"limite": limite}

        if filtro_tipo:
            sql += " AND d.tipo = :tipo"
            params["tipo"] = filtro_tipo

        if filtro_temas:
            sql += " AND f.temas && :temas"
            params["temas"] = filtro_temas

        sql += f"""
            ORDER BY f.embedding <=> '{embedding_str}'::vector
            LIMIT :limite
        """

        result = await db.execute(text(sql), params)
        rows = result.fetchall()

        resultados = []
        for row in rows:
            if row.similitud >= umbral_similitud:
                resultados.append(ResultadoBusqueda(
                    fragmento_id=row.fragmento_id,
                    documento_id=row.documento_id,
                    documento_titulo=row.documento_titulo,
                    documento_tipo=row.documento_tipo,
                    seccion=row.seccion,
                    contenido=row.contenido,
                    temas=row.temas or [],
                    similitud=round(row.similitud, 4),
                ))

        logger.info(f"Búsqueda completada: {len(resultados)} resultados encontrados")
        return resultados

    async def buscar_por_contexto_gis(
        self,
        db: AsyncSession,
        resultado_gis: Dict[str, Any],
        limite_por_tema: int = 3,
    ) -> Dict[str, List[ResultadoBusqueda]]:
        """
        Busca normativa relevante basada en el contexto GIS.

        Analiza el resultado del análisis espacial y busca normativa
        relacionada con los elementos detectados.

        Args:
            db: Sesión de base de datos
            resultado_gis: Resultado del análisis espacial
            limite_por_tema: Resultados máximos por tema

        Returns:
            Diccionario con resultados agrupados por tema
        """
        resultados = {}

        # Áreas protegidas
        if resultado_gis.get("areas_protegidas"):
            areas = resultado_gis["areas_protegidas"]
            if any(a.get("intersecta") for a in areas):
                query = "proyecto minero dentro de área protegida SNASPE requisitos evaluación ambiental"
            else:
                query = "proyecto cercano a área protegida evaluación impacto"

            resultados["areas_protegidas"] = await self.buscar(
                db, query,
                limite=limite_por_tema,
                filtro_temas=["areas_protegidas"],
            )

        # Glaciares
        if resultado_gis.get("glaciares"):
            glaciares = resultado_gis["glaciares"]
            if any(g.get("intersecta") for g in glaciares):
                query = "protección glaciares ambiente periglaciar prohibición intervención"
            else:
                query = "glaciares evaluación impacto ambiental minería"

            resultados["glaciares"] = await self.buscar(
                db, query,
                limite=limite_por_tema,
                filtro_temas=["glaciares", "agua"],
            )

        # Comunidades indígenas
        if resultado_gis.get("comunidades_indigenas"):
            comunidades = resultado_gis["comunidades_indigenas"]
            cercanas = [c for c in comunidades if c.get("distancia_m", float("inf")) < 10000]

            if cercanas:
                query = "consulta indígena participación pueblos originarios evaluación impacto SEIA"
                resultados["comunidades_indigenas"] = await self.buscar(
                    db, query,
                    limite=limite_por_tema,
                    filtro_temas=["comunidades_indigenas", "participacion"],
                )

        # Cuerpos de agua
        if resultado_gis.get("cuerpos_agua"):
            cuerpos = resultado_gis["cuerpos_agua"]
            if any(c.get("intersecta") or c.get("distancia_m", float("inf")) < 500 for c in cuerpos):
                query = "uso agua proyecto minero DGA derechos aprovechamiento"
                resultados["agua"] = await self.buscar(
                    db, query,
                    limite=limite_por_tema,
                    filtro_temas=["agua"],
                )

        # Siempre buscar normativa general SEIA
        resultados["seia_general"] = await self.buscar(
            db,
            "ingreso sistema evaluación impacto ambiental proyecto minero DIA EIA",
            limite=limite_por_tema,
            filtro_temas=["eia", "dia"],
        )

        return resultados

    async def obtener_estadisticas(self, db: AsyncSession) -> Dict[str, Any]:
        """Obtiene estadísticas del corpus legal indexado."""

        # Total documentos
        result = await db.execute(text("SELECT COUNT(*) FROM legal.documentos"))
        total_docs = result.scalar()

        # Total fragmentos
        result = await db.execute(text("SELECT COUNT(*) FROM legal.fragmentos"))
        total_fragmentos = result.scalar()

        # Por tipo de documento
        result = await db.execute(text("""
            SELECT tipo, COUNT(*) as cantidad
            FROM legal.documentos
            GROUP BY tipo
            ORDER BY cantidad DESC
        """))
        por_tipo = {row.tipo: row.cantidad for row in result.fetchall()}

        # Temas más comunes
        result = await db.execute(text("""
            SELECT unnest(temas) as tema, COUNT(*) as cantidad
            FROM legal.fragmentos
            GROUP BY tema
            ORDER BY cantidad DESC
            LIMIT 10
        """))
        temas_comunes = {row.tema: row.cantidad for row in result.fetchall()}

        return {
            "total_documentos": total_docs,
            "total_fragmentos": total_fragmentos,
            "documentos_por_tipo": por_tipo,
            "temas_mas_comunes": temas_comunes,
        }
