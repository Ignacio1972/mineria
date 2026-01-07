"""
Servicio de Generación de Descripción Geográfica Automática.

Genera una descripción narrativa del lugar geográfico donde se emplaza
un proyecto, utilizando datos GIS y LLM.
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from geoalchemy2.shape import to_shape
from shapely.geometry import mapping

from app.db.models.proyecto import Proyecto
from app.services.gis.analisis import analizar_proyecto_espacial
from app.services.llm.cliente import ClienteLLM

logger = logging.getLogger(__name__)


PROMPT_DESCRIPCION_GEOGRAFICA = """Eres un experto en geografía y análisis territorial de Chile.

A partir de los siguientes datos GIS de un proyecto, genera una descripción geográfica narrativa, clara y profesional del lugar donde se emplaza.

**DATOS DEL PROYECTO:**
- Nombre: {nombre_proyecto}
- Superficie: {superficie_ha} hectáreas
- Región: {region}
- Comuna: {comuna}

**ANÁLISIS ESPACIAL:**
{analisis_gis}

**INSTRUCCIONES:**
1. Escribe en español de Chile, usando terminología técnica apropiada
2. Extensión: 150-300 palabras
3. Estructura:
   - Párrafo 1: Ubicación administrativa y superficie
   - Párrafo 2: Características físicas del terreno (altitud, tipo de zona, clima si aplica)
   - Párrafo 3: Entorno y proximidades (áreas protegidas, comunidades, centros poblados, cursos de agua)
4. Usa datos concretos (distancias, nombres de lugares)
5. Tono: profesional, objetivo, descriptivo
6. NO menciones el tipo de proyecto ni actividades (enfócate solo en la geografía)
7. NO inventes datos que no estén en la información proporcionada

**FORMATO DE SALIDA:**
Retorna SOLO el texto de la descripción, sin título, sin metadatos, sin formato markdown.
"""


class ServicioDescripcionGeografica:
    """
    Servicio para generar descripciones geográficas automáticas de proyectos.
    """

    def __init__(self, llm_client: Optional[ClienteLLM] = None):
        """
        Inicializa el servicio.

        Args:
            llm_client: Cliente LLM (si no se proporciona, se crea uno nuevo)
        """
        self.llm_client = llm_client or ClienteLLM()

    async def generar_descripcion(
        self,
        db: AsyncSession,
        proyecto_id: int,
        forzar_regeneracion: bool = False
    ) -> Dict[str, Any]:
        """
        Genera la descripción geográfica para un proyecto.

        Args:
            db: Sesión de base de datos
            proyecto_id: ID del proyecto
            forzar_regeneracion: Si True, regenera aunque ya exista

        Returns:
            Dict con:
                - descripcion: texto generado
                - fecha_generacion: datetime
                - fuente: 'auto'
                - tokens_usados: int
                - tiempo_ms: int

        Raises:
            ValueError: Si el proyecto no existe o no tiene geometría
        """
        logger.info(f"Generando descripción geográfica para proyecto {proyecto_id}")

        # 1. Cargar proyecto
        result = await db.execute(
            select(Proyecto).where(Proyecto.id == proyecto_id)
        )
        proyecto = result.scalar_one_or_none()

        if not proyecto:
            raise ValueError(f"Proyecto {proyecto_id} no encontrado")

        if not proyecto.tiene_geometria:
            raise ValueError(f"Proyecto {proyecto_id} no tiene geometría definida")

        # 2. Verificar si ya tiene descripción
        if proyecto.descripcion_geografica and not forzar_regeneracion:
            logger.info(f"Proyecto {proyecto_id} ya tiene descripción geográfica")
            return {
                "descripcion": proyecto.descripcion_geografica,
                "fecha_generacion": proyecto.descripcion_geografica_fecha,
                "fuente": proyecto.descripcion_geografica_fuente,
                "regenerada": False
            }

        # 3. Ejecutar análisis GIS
        logger.debug(f"Ejecutando análisis GIS para proyecto {proyecto_id}")
        # Convertir geometría a GeoJSON
        geom_shape = to_shape(proyecto.geom)
        geojson = mapping(geom_shape)
        analisis_gis = await analizar_proyecto_espacial(db, geojson)

        # 4. Construir contexto para LLM
        contexto_gis = self._construir_contexto_gis(analisis_gis)

        # 5. Generar prompt
        prompt = PROMPT_DESCRIPCION_GEOGRAFICA.format(
            nombre_proyecto=proyecto.nombre,
            superficie_ha=proyecto.superficie_ha or "No especificada",
            region=proyecto.region or "No especificada",
            comuna=proyecto.comuna or "No especificada",
            analisis_gis=contexto_gis
        )

        # 6. Llamar a LLM
        logger.debug("Generando descripción con LLM")
        respuesta = await self.llm_client.generar(
            prompt_usuario=prompt,
            temperatura=0.7,  # Un poco más creativo para narrativa
            max_tokens=1000
        )

        descripcion = respuesta.contenido.strip()

        # 7. Guardar en proyecto
        proyecto.descripcion_geografica = descripcion
        proyecto.descripcion_geografica_fecha = datetime.utcnow()
        proyecto.descripcion_geografica_fuente = 'auto'

        await db.commit()
        await db.refresh(proyecto)

        logger.info(
            f"Descripción geográfica generada para proyecto {proyecto_id}. "
            f"Tokens: {respuesta.tokens_totales}, Tiempo: {respuesta.tiempo_ms}ms"
        )

        return {
            "descripcion": descripcion,
            "fecha_generacion": proyecto.descripcion_geografica_fecha,
            "fuente": "auto",
            "tokens_usados": respuesta.tokens_totales,
            "tiempo_ms": respuesta.tiempo_ms,
            "regenerada": True
        }

    def _construir_contexto_gis(self, analisis: dict) -> str:
        """
        Construye texto legible desde el análisis GIS.

        Args:
            analisis: Resultado de analizar_proyecto_espacial

        Returns:
            Texto formateado con datos GIS
        """
        lineas = []

        # Áreas protegidas (lista ordenada por distancia, el primero es el más cercano)
        areas_protegidas = analisis.get("areas_protegidas", [])
        if areas_protegidas:
            mas_cercana = areas_protegidas[0]
            dist_m = mas_cercana.get("distancia_m", 0)
            dist_km = dist_m / 1000 if dist_m else 0
            lineas.append(
                f"- Área protegida más cercana: {mas_cercana.get('nombre', 'Desconocida')} "
                f"({mas_cercana.get('tipo', 'N/D')}) a {dist_km:.1f} km"
            )
        else:
            lineas.append("- No hay áreas protegidas en un radio de 50 km")

        # Comunidades indígenas (lista ordenada por distancia)
        comunidades = analisis.get("comunidades_indigenas", [])
        if comunidades:
            mas_cercana = comunidades[0]
            dist_m = mas_cercana.get("distancia_m", 0)
            dist_km = dist_m / 1000 if dist_m else 0
            pueblo = mas_cercana.get("pueblo", "Indígena")
            lineas.append(
                f"- Comunidad indígena más cercana: {mas_cercana.get('nombre', 'Desconocida')} "
                f"({pueblo}) a {dist_km:.1f} km"
            )
        else:
            lineas.append("- No hay comunidades indígenas identificadas en un radio de 20 km")

        # Centros poblados (lista ordenada por distancia)
        centros_poblados = analisis.get("centros_poblados", [])
        if centros_poblados:
            mas_cercano = centros_poblados[0]
            dist_m = mas_cercano.get("distancia_m", 0)
            dist_km = dist_m / 1000 if dist_m else 0
            lineas.append(
                f"- Centro poblado más cercano: {mas_cercano.get('nombre', 'Desconocido')} "
                f"a {dist_km:.1f} km"
            )

        # Glaciares (verificar si alguno intersecta)
        glaciares = analisis.get("glaciares", [])
        glaciares_afectados = [g for g in glaciares if g.get("intersecta")]
        if glaciares_afectados:
            lineas.append(f"- El proyecto intersecta {len(glaciares_afectados)} glaciar(es)")

        # Cuerpos de agua
        cuerpos_agua = analisis.get("cuerpos_agua", [])
        if cuerpos_agua:
            cuerpos_intersectados = [c for c in cuerpos_agua if c.get("intersecta")]
            if cuerpos_intersectados:
                nombres = ", ".join([c.get("nombre", "Sin nombre") for c in cuerpos_intersectados[:2]])
                lineas.append(f"- Cuerpos de agua intersectados: {nombres}")

        # Alertas importantes (solo críticas y altas)
        alertas = analisis.get("alertas", [])
        if alertas:
            alertas_criticas = [
                a for a in alertas
                if a.get("tipo") in ["CRITICA", "ALTA"]
            ]
            for alerta in alertas_criticas[:3]:  # Max 3 alertas
                lineas.append(f"- {alerta.get('mensaje', '')}")

        # Si no hay datos
        if not lineas:
            lineas.append("- No se dispone de información espacial detallada")

        return "\n".join(lineas)


async def generar_descripcion_proyecto(
    db: AsyncSession,
    proyecto_id: int,
    forzar_regeneracion: bool = False
) -> Dict[str, Any]:
    """
    Función helper para generar descripción geográfica.

    Args:
        db: Sesión de base de datos
        proyecto_id: ID del proyecto
        forzar_regeneracion: Si True, regenera aunque ya exista

    Returns:
        Dict con descripción y metadatos
    """
    servicio = ServicioDescripcionGeografica()
    return await servicio.generar_descripcion(db, proyecto_id, forzar_regeneracion)
