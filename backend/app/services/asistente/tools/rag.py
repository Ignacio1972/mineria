"""
Herramientas RAG del asistente.
Busqueda semantica en corpus legal y documentacion del sistema.
"""
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from .base import (
    Herramienta,
    ResultadoHerramienta,
    CategoriaHerramienta,
    PermisoHerramienta,
    registro_herramientas,
)
from app.services.rag.embeddings import get_embedding_service

logger = logging.getLogger(__name__)


# Tipos de documentos prioritarios (interpretacion oficial del SEA)
TIPOS_PRIORITARIOS = ['Guía SEA', 'Criterio SEA', 'Instructivo', 'Instructivo SEA', 'Criterio', 'Manual']
# Tipos de documentos base (leyes y reglamentos)
TIPOS_BASE = ['Ley', 'Reglamento']


@registro_herramientas.registrar
class BuscarNormativa(Herramienta):
    """Busca fragmentos relevantes en el corpus legal con priorizacion de Guias/Instructivos/Criterios."""

    nombre = "buscar_normativa"
    descripcion = """Busca fragmentos relevantes en el corpus legal del sistema.
IMPORTANTE: Esta herramienta usa busqueda en DOS PASOS para mayor precision:
1. Primero busca en Guias SEA, Criterios e Instructivos (interpretacion oficial)
2. Luego complementa con Leyes y Reglamentos (normativa base)

Usa esta herramienta SIEMPRE que el usuario pregunte sobre:
- Normativa ambiental chilena
- Requisitos legales del SEIA (umbrales, plazos, metodologias)
- Articulos especificos de leyes o reglamentos
- Fundamentos para clasificacion DIA/EIA
- Triggers del Articulo 11
- Procedimientos administrativos
- Participacion ciudadana o consulta indigena

IMPORTANTE: Cada resultado incluye 'documento_id', 'documento_tipo' y 'url_documento'.
Los resultados de Guias/Criterios/Instructivos aparecen primero porque contienen
la interpretacion OFICIAL del SEA con datos especificos."""
    categoria = CategoriaHerramienta.RAG
    requiere_confirmacion = False
    permisos = [PermisoHerramienta.LECTURA]

    def __init__(self):
        self.embedding_service = get_embedding_service()
        self._db: Optional[AsyncSession] = None

    def set_db(self, db: AsyncSession):
        """Establece la sesion de base de datos."""
        self._db = db

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Consulta de busqueda semantica en lenguaje natural"
                },
                "top_k": {
                    "type": "integer",
                    "description": "Numero total de resultados a retornar (se distribuyen entre tipos prioritarios y base)",
                    "default": 8,
                    "minimum": 1,
                    "maximum": 20
                },
                "temas": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Filtrar por temas especificos. Opciones: areas_protegidas, glaciares, agua, comunidades_indigenas, eia, dia, patrimonio, participacion_ciudadana"
                },
                "tipo_documento": {
                    "type": "string",
                    "description": "Filtrar por tipo especifico (omitir para busqueda en dos pasos)",
                    "enum": ["Ley", "Reglamento", "Guía SEA", "Criterio SEA", "Instructivo"]
                },
                "solo_prioritarios": {
                    "type": "boolean",
                    "description": "Si es true, solo busca en Guias/Criterios/Instructivos",
                    "default": False
                }
            },
            "required": ["query"]
        }

    async def _buscar_en_tipos(
        self,
        db: AsyncSession,
        embedding_str: str,
        tipos: List[str],
        limite: int,
        temas: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Busca fragmentos en tipos de documentos especificos."""

        tipos_str = "', '".join(tipos)
        sql = f"""
            SELECT
                f.id as fragmento_id,
                f.documento_id,
                d.titulo as documento_titulo,
                d.tipo as documento_tipo,
                f.numero_seccion as articulo,
                f.seccion,
                f.contenido,
                f.temas,
                1 - (f.embedding <=> '{embedding_str}'::vector) as similitud
            FROM legal.fragmentos f
            JOIN legal.documentos d ON f.documento_id = d.id
            WHERE d.estado = 'vigente'
            AND d.tipo IN ('{tipos_str}')
            AND f.embedding IS NOT NULL
        """

        params = {"limite": limite}

        if temas:
            sql += " AND f.temas && :temas"
            params["temas"] = temas

        sql += f"""
            ORDER BY f.embedding <=> '{embedding_str}'::vector
            LIMIT :limite
        """

        result = await db.execute(text(sql), params)
        rows = result.fetchall()

        fragmentos = []
        for row in rows:
            if row.similitud >= 0.3:  # Umbral minimo
                fragmentos.append({
                    "fragmento_id": row.fragmento_id,
                    "documento_id": row.documento_id,
                    "documento_titulo": row.documento_titulo,
                    "documento_tipo": row.documento_tipo,
                    "articulo": row.articulo,
                    "seccion": row.seccion,
                    "contenido": row.contenido[:1000],
                    "temas": row.temas or [],
                    "similitud": round(row.similitud, 4),
                    "url_documento": f"/corpus?doc={row.documento_id}",
                })

        return fragmentos

    async def ejecutar(
        self,
        query: str,
        top_k: int = 8,
        temas: Optional[List[str]] = None,
        tipo_documento: Optional[str] = None,
        solo_prioritarios: bool = False,
        db: Optional[AsyncSession] = None,
        **kwargs
    ) -> ResultadoHerramienta:
        """Ejecuta busqueda semantica en corpus legal con priorizacion de Guias/Criterios/Instructivos."""

        db = db or self._db
        if not db:
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error="No hay sesion de base de datos disponible"
            )

        try:
            # Generar embedding de la query
            query_embedding = self.embedding_service.embed_text(query)
            embedding_str = '[' + ','.join(str(x) for x in query_embedding) + ']'

            fragmentos = []
            metodo_busqueda = "dos_pasos"

            # Si se especifica tipo_documento, busqueda simple filtrada
            if tipo_documento:
                metodo_busqueda = "filtrado"
                fragmentos = await self._buscar_en_tipos(
                    db, embedding_str, [tipo_documento], top_k, temas
                )

            # Si solo_prioritarios, buscar solo en Guias/Criterios/Instructivos
            elif solo_prioritarios:
                metodo_busqueda = "solo_prioritarios"
                fragmentos = await self._buscar_en_tipos(
                    db, embedding_str, TIPOS_PRIORITARIOS, top_k, temas
                )

            # Busqueda en dos pasos (comportamiento por defecto)
            else:
                # Paso 1: Buscar en tipos prioritarios (70% de resultados)
                limite_prioritarios = max(1, int(top_k * 0.7))
                fragmentos_prioritarios = await self._buscar_en_tipos(
                    db, embedding_str, TIPOS_PRIORITARIOS, limite_prioritarios, temas
                )

                # Paso 2: Buscar en tipos base (30% de resultados)
                limite_base = max(1, top_k - len(fragmentos_prioritarios))
                fragmentos_base = await self._buscar_en_tipos(
                    db, embedding_str, TIPOS_BASE, limite_base, temas
                )

                # Combinar: prioritarios primero, luego base
                fragmentos = fragmentos_prioritarios + fragmentos_base

                # Log para debugging
                logger.info(
                    f"Busqueda dos pasos: {len(fragmentos_prioritarios)} prioritarios + "
                    f"{len(fragmentos_base)} base = {len(fragmentos)} total"
                )

            # Marcar origen de cada fragmento para claridad
            for frag in fragmentos:
                frag["es_prioritario"] = frag["documento_tipo"] in TIPOS_PRIORITARIOS

            return ResultadoHerramienta(
                exito=True,
                contenido={
                    "query": query,
                    "metodo_busqueda": metodo_busqueda,
                    "total_encontrados": len(fragmentos),
                    "fragmentos_prioritarios": sum(1 for f in fragmentos if f.get("es_prioritario")),
                    "fragmentos_base": sum(1 for f in fragmentos if not f.get("es_prioritario")),
                    "fragmentos": fragmentos,
                    "nota": "Los fragmentos de Guias/Criterios/Instructivos (es_prioritario=true) contienen interpretacion oficial del SEA y datos especificos."
                },
                metadata={
                    "top_k": top_k,
                    "metodo": metodo_busqueda,
                    "filtros": {"temas": temas, "tipo": tipo_documento, "solo_prioritarios": solo_prioritarios}
                }
            )

        except Exception as e:
            logger.error(f"Error en busqueda normativa: {e}")
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error=str(e)
            )


@registro_herramientas.registrar
class BuscarDocumentacion(Herramienta):
    """Busca en la documentacion del sistema."""

    nombre = "buscar_documentacion"
    descripcion = """Busca en la documentacion del sistema de prefactibilidad.
Usa esta herramienta cuando el usuario pregunte sobre:
- Como usar el sistema
- Funcionalidades disponibles
- Proceso de analisis
- Significado de clasificaciones o alertas"""
    categoria = CategoriaHerramienta.RAG
    requiere_confirmacion = False
    permisos = [PermisoHerramienta.LECTURA]

    def __init__(self):
        self.embedding_service = get_embedding_service()
        self._db: Optional[AsyncSession] = None

    def set_db(self, db: AsyncSession):
        """Establece la sesion de base de datos."""
        self._db = db

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Consulta sobre el sistema"
                },
                "top_k": {
                    "type": "integer",
                    "description": "Numero de resultados",
                    "default": 5,
                    "minimum": 1,
                    "maximum": 10
                }
            },
            "required": ["query"]
        }

    async def ejecutar(
        self,
        query: str,
        top_k: int = 5,
        db: Optional[AsyncSession] = None,
        **kwargs
    ) -> ResultadoHerramienta:
        """Ejecuta busqueda en documentacion del sistema."""

        db = db or self._db
        if not db:
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error="No hay sesion de base de datos disponible"
            )

        try:
            # Generar embedding
            query_embedding = self.embedding_service.embed_text(query)
            embedding_str = '[' + ','.join(str(x) for x in query_embedding) + ']'

            sql = f"""
                SELECT
                    id,
                    tipo,
                    titulo,
                    contenido,
                    tags,
                    1 - (embedding <=> '{embedding_str}'::vector) as similitud
                FROM asistente.documentacion_sistema
                WHERE activo = TRUE
                AND embedding IS NOT NULL
                ORDER BY embedding <=> '{embedding_str}'::vector
                LIMIT :limite
            """

            result = await db.execute(text(sql), {"limite": top_k})
            rows = result.fetchall()

            documentos = []
            for row in rows:
                if row.similitud >= 0.25:
                    documentos.append({
                        "id": str(row.id),
                        "tipo": row.tipo,
                        "titulo": row.titulo,
                        "contenido": row.contenido[:800],
                        "tags": row.tags or [],
                        "similitud": round(row.similitud, 4),
                    })

            return ResultadoHerramienta(
                exito=True,
                contenido={
                    "query": query,
                    "total_encontrados": len(documentos),
                    "documentos": documentos,
                },
            )

        except Exception as e:
            logger.error(f"Error en busqueda documentacion: {e}")
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error=str(e)
            )


@registro_herramientas.registrar
class ObtenerEstadisticasCorpus(Herramienta):
    """Obtiene estadísticas del corpus legal RAG."""

    nombre = "obtener_estadisticas_corpus"
    descripcion = """Obtiene estadísticas completas del corpus legal del sistema.
Usa esta herramienta cuando el usuario pregunte:
- ¿Cuántos documentos hay en el corpus?
- ¿Cuántos fragmentos tiene el sistema?
- Estadísticas del corpus legal
- ¿Qué tipos de documentos hay?
- ¿Cuántas categorías existen?
- Estado del corpus RAG
- ¿Cuántos temas hay disponibles?"""
    categoria = CategoriaHerramienta.RAG
    requiere_confirmacion = False
    permisos = [PermisoHerramienta.LECTURA]

    def __init__(self):
        self._db: Optional[AsyncSession] = None

    def set_db(self, db: AsyncSession):
        self._db = db

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "incluir_detalle": {
                    "type": "boolean",
                    "description": "Si es true, incluye detalles adicionales como documentos por categoría y temas disponibles",
                    "default": False
                }
            }
        }

    async def ejecutar(
        self,
        incluir_detalle: bool = False,
        db: Optional[AsyncSession] = None,
        **kwargs
    ) -> ResultadoHerramienta:
        """Obtiene estadísticas del corpus legal."""

        db = db or self._db
        if not db:
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error="No hay sesion de base de datos disponible"
            )

        try:
            # Estadísticas generales
            stats_sql = """
                SELECT
                    (SELECT COUNT(*) FROM legal.documentos) as total_documentos,
                    (SELECT COUNT(*) FROM legal.documentos WHERE estado = 'vigente') as documentos_vigentes,
                    (SELECT COUNT(*) FROM legal.fragmentos) as total_fragmentos,
                    (SELECT COUNT(*) FROM legal.fragmentos WHERE embedding IS NOT NULL) as fragmentos_con_embedding,
                    (SELECT COUNT(*) FROM legal.categorias WHERE activo = true) as total_categorias,
                    (SELECT COUNT(*) FROM legal.temas WHERE activo = true) as total_temas,
                    (SELECT COUNT(*) FROM legal.colecciones) as total_colecciones,
                    (SELECT COUNT(*) FROM legal.archivos_originales) as total_archivos
            """
            result = await db.execute(text(stats_sql))
            row = result.fetchone()

            stats = {
                "resumen": {
                    "total_documentos": row.total_documentos,
                    "documentos_vigentes": row.documentos_vigentes,
                    "total_fragmentos": row.total_fragmentos,
                    "fragmentos_con_embedding": row.fragmentos_con_embedding,
                    "cobertura_embeddings": f"{(row.fragmentos_con_embedding / row.total_fragmentos * 100):.1f}%" if row.total_fragmentos > 0 else "0%",
                    "total_categorias": row.total_categorias,
                    "total_temas": row.total_temas,
                    "total_colecciones": row.total_colecciones,
                    "total_archivos": row.total_archivos,
                }
            }

            # Documentos por tipo
            tipo_sql = """
                SELECT tipo, COUNT(*) as cantidad
                FROM legal.documentos
                WHERE tipo IS NOT NULL
                GROUP BY tipo
                ORDER BY cantidad DESC
            """
            result_tipo = await db.execute(text(tipo_sql))
            stats["por_tipo"] = {r.tipo: r.cantidad for r in result_tipo.fetchall()}

            # Documentos por estado
            estado_sql = """
                SELECT estado, COUNT(*) as cantidad
                FROM legal.documentos
                GROUP BY estado
                ORDER BY cantidad DESC
            """
            result_estado = await db.execute(text(estado_sql))
            stats["por_estado"] = {r.estado: r.cantidad for r in result_estado.fetchall()}

            if incluir_detalle:
                # Documentos por categoría (nivel 1)
                categoria_sql = """
                    SELECT c.nombre, COUNT(d.id) as cantidad
                    FROM legal.categorias c
                    LEFT JOIN legal.documentos d ON d.categoria_id = c.id
                    WHERE c.nivel = 1 AND c.activo = true
                    GROUP BY c.id, c.nombre
                    ORDER BY cantidad DESC
                """
                result_cat = await db.execute(text(categoria_sql))
                stats["por_categoria"] = {r.nombre: r.cantidad for r in result_cat.fetchall()}

                # Temas disponibles con conteo de fragmentos
                temas_sql = """
                    SELECT t.codigo, t.nombre, t.grupo, COUNT(ft.fragmento_id) as fragmentos_asociados
                    FROM legal.temas t
                    LEFT JOIN legal.fragmentos_temas ft ON ft.tema_id = t.id
                    WHERE t.activo = true
                    GROUP BY t.id, t.codigo, t.nombre, t.grupo
                    ORDER BY fragmentos_asociados DESC
                    LIMIT 20
                """
                result_temas = await db.execute(text(temas_sql))
                stats["temas_disponibles"] = [
                    {
                        "codigo": r.codigo,
                        "nombre": r.nombre,
                        "grupo": r.grupo,
                        "fragmentos_asociados": r.fragmentos_asociados
                    }
                    for r in result_temas.fetchall()
                ]

                # Top 5 documentos con más fragmentos
                top_docs_sql = """
                    SELECT d.titulo, d.tipo, COUNT(f.id) as total_fragmentos
                    FROM legal.documentos d
                    JOIN legal.fragmentos f ON f.documento_id = d.id
                    GROUP BY d.id, d.titulo, d.tipo
                    ORDER BY total_fragmentos DESC
                    LIMIT 5
                """
                result_top = await db.execute(text(top_docs_sql))
                stats["documentos_con_mas_fragmentos"] = [
                    {
                        "titulo": r.titulo,
                        "tipo": r.tipo,
                        "fragmentos": r.total_fragmentos
                    }
                    for r in result_top.fetchall()
                ]

                # Colecciones con conteo
                colecciones_sql = """
                    SELECT c.nombre, c.descripcion, COUNT(dc.documento_id) as documentos
                    FROM legal.colecciones c
                    LEFT JOIN legal.documentos_colecciones dc ON dc.coleccion_id = c.id
                    GROUP BY c.id, c.nombre, c.descripcion
                    ORDER BY documentos DESC
                """
                result_col = await db.execute(text(colecciones_sql))
                stats["colecciones"] = [
                    {
                        "nombre": r.nombre,
                        "descripcion": r.descripcion,
                        "documentos": r.documentos
                    }
                    for r in result_col.fetchall()
                ]

            return ResultadoHerramienta(
                exito=True,
                contenido=stats,
                metadata={"incluye_detalle": incluir_detalle}
            )

        except Exception as e:
            logger.error(f"Error obteniendo estadisticas del corpus: {e}")
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error=str(e)
            )


@registro_herramientas.registrar
class ExplicarClasificacion(Herramienta):
    """Explica la clasificacion DIA/EIA de un analisis."""

    nombre = "explicar_clasificacion"
    descripcion = """Genera una explicacion detallada de por que un proyecto fue clasificado como DIA o EIA.
Usa esta herramienta cuando el usuario pregunte:
- ¿Por que este proyecto es EIA?
- ¿Que triggers activo este proyecto?
- Explicame la clasificacion del analisis"""
    categoria = CategoriaHerramienta.RAG
    requiere_confirmacion = False
    permisos = [PermisoHerramienta.LECTURA]

    def __init__(self):
        self._db: Optional[AsyncSession] = None

    def set_db(self, db: AsyncSession):
        self._db = db

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "analisis_id": {
                    "type": "integer",
                    "description": "ID del analisis a explicar. Proporcionar este O proyecto_id."
                },
                "proyecto_id": {
                    "type": "integer",
                    "description": "ID del proyecto (usa el ultimo analisis). Proporcionar este O analisis_id."
                }
            }
        }

    async def ejecutar(
        self,
        analisis_id: Optional[int] = None,
        proyecto_id: Optional[int] = None,
        db: Optional[AsyncSession] = None,
        **kwargs
    ) -> ResultadoHerramienta:
        """Obtiene y explica la clasificacion de un analisis."""

        db = db or self._db
        if not db:
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error="No hay sesion de base de datos disponible"
            )

        try:
            # Obtener analisis
            if analisis_id:
                sql = """
                    SELECT a.*, p.nombre as proyecto_nombre
                    FROM proyectos.analisis a
                    JOIN proyectos.proyectos p ON a.proyecto_id = p.id
                    WHERE a.id = :id
                """
                result = await db.execute(text(sql), {"id": analisis_id})
            else:
                sql = """
                    SELECT a.*, p.nombre as proyecto_nombre
                    FROM proyectos.analisis a
                    JOIN proyectos.proyectos p ON a.proyecto_id = p.id
                    WHERE a.proyecto_id = :proyecto_id
                    ORDER BY a.fecha_analisis DESC
                    LIMIT 1
                """
                result = await db.execute(text(sql), {"proyecto_id": proyecto_id})

            row = result.fetchone()
            if not row:
                return ResultadoHerramienta(
                    exito=False,
                    contenido=None,
                    error="Analisis no encontrado"
                )

            # Construir explicacion estructurada
            explicacion = {
                "proyecto_id": row.proyecto_id,
                "proyecto_nombre": row.proyecto_nombre,
                "clasificacion": row.via_ingreso_recomendada,
                "confianza": row.confianza,
                "puntaje_matriz": row.puntaje_matriz,
                "triggers_detectados": row.triggers_detectados or [],
                "alertas": row.alertas or [],
                "resumen": row.resumen,
                "fecha_analisis": row.fecha_analisis.isoformat() if row.fecha_analisis else None,
            }

            # Agregar fundamentos legales por trigger
            fundamentos = []
            triggers = row.triggers_detectados or []
            for trigger in triggers:
                letra = trigger.get("letra", "")
                if letra == "a":
                    fundamentos.append({
                        "letra": "a",
                        "articulo": "Art. 11 letra a) Ley 19.300",
                        "descripcion": "Riesgo para la salud de la poblacion"
                    })
                elif letra == "b":
                    fundamentos.append({
                        "letra": "b",
                        "articulo": "Art. 11 letra b) Ley 19.300",
                        "descripcion": "Efectos adversos sobre recursos naturales renovables"
                    })
                elif letra == "c":
                    fundamentos.append({
                        "letra": "c",
                        "articulo": "Art. 11 letra c) Ley 19.300",
                        "descripcion": "Reasentamiento de comunidades humanas"
                    })
                elif letra == "d":
                    fundamentos.append({
                        "letra": "d",
                        "articulo": "Art. 11 letra d) Ley 19.300",
                        "descripcion": "Localizacion en o proxima a areas protegidas, sitios prioritarios o glaciares"
                    })
                elif letra == "e":
                    fundamentos.append({
                        "letra": "e",
                        "articulo": "Art. 11 letra e) Ley 19.300",
                        "descripcion": "Alteracion significativa del patrimonio cultural"
                    })
                elif letra == "f":
                    fundamentos.append({
                        "letra": "f",
                        "articulo": "Art. 11 letra f) Ley 19.300",
                        "descripcion": "Alteracion significativa del valor paisajistico o turistico"
                    })

            explicacion["fundamentos_legales"] = fundamentos

            return ResultadoHerramienta(
                exito=True,
                contenido=explicacion,
            )

        except Exception as e:
            logger.error(f"Error explicando clasificacion: {e}")
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error=str(e)
            )
