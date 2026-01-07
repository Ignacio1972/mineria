"""
Servicio de Componentes EIA.

Genera checklist de los 23 componentes necesarios para el EIA según el Decreto 40,
determina cuáles son requeridos según el proyecto, y busca material RAG relevante
para cada uno. Cumplimiento 100% con la estructura del Art. 18 DS 40.
"""

import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models.proyecto import ComponenteEIAChecklist
from app.services.rag.busqueda import BuscadorLegal

logger = logging.getLogger(__name__)


# Definición de los 23 componentes EIA (cumplimiento 100% Decreto 40)
COMPONENTES_EIA = {
    "indice_resumen_ejecutivo": {
        "capitulo": 0,
        "nombre": "Índice y Resumen Ejecutivo",
        "descripcion": "Índice completo del EIA y resumen ejecutivo de máximo 30 páginas en lenguaje sencillo y accesible al público",
        "prioridad": "alta",
        "requerido_siempre": True,
        "queries_rag": [
            "resumen ejecutivo EIA contenidos mínimos estructura",
            "índice estudio impacto ambiental organización capítulos",
            "síntesis proyecto impactos medidas lenguaje no técnico",
        ],
    },
    "desc_proyecto_general": {
        "capitulo": 1,
        "nombre": "Descripción General del Proyecto",
        "descripcion": "Antecedentes generales, objetivos, justificación y localización del proyecto",
        "prioridad": "alta",
        "requerido_siempre": True,
        "queries_rag": [
            "descripción proyecto minero EIA contenidos mínimos",
            "antecedentes generales proyecto evaluación ambiental",
            "localización proyecto minero sistema evaluación",
        ],
    },
    "area_influencia": {
        "capitulo": 2,
        "nombre": "Área de Influencia",
        "descripcion": "Delimitación del área de influencia por componente ambiental",
        "prioridad": "alta",
        "requerido_siempre": True,
        "queries_rag": [
            "área de influencia proyecto definición metodología",
            "determinación área de influencia componentes ambientales",
            "delimitación área de influencia EIA minería",
        ],
    },
    "linea_base_fisico": {
        "capitulo": 3,
        "nombre": "Línea de Base - Medio Físico",
        "descripcion": "Caracterización de clima, aire, ruido, suelos, aguas superficiales y subterráneas, geología",
        "prioridad": "alta",
        "requerido_siempre": True,
        "queries_rag": [
            "línea de base medio físico EIA componentes",
            "caracterización suelos geología aguas proyecto minero",
            "calidad aire ruido clima evaluación ambiental",
        ],
    },
    "linea_base_biotico": {
        "capitulo": 3,
        "nombre": "Línea de Base - Medio Biótico",
        "descripcion": "Caracterización de flora, vegetación, fauna y ecosistemas",
        "prioridad": "alta",
        "requerido_siempre": False,
        "condiciones": ["trigger_e", "areas_protegidas"],
        "queries_rag": [
            "línea de base biótica flora fauna EIA",
            "caracterización vegetación ecosistemas proyecto minero",
            "especies protegidas conservación evaluación impacto",
            "metodología muestreo flora fauna ambiental",
        ],
    },
    "linea_base_humano": {
        "capitulo": 3,
        "nombre": "Línea de Base - Medio Humano",
        "descripcion": "Dimensión geográfica, demográfica, antropológica, socioeconómica y bienestar social",
        "prioridad": "alta",
        "requerido_siempre": True,
        "queries_rag": [
            "línea de base medio humano dimensiones socioeconómicas",
            "caracterización población comunidades proyecto minero",
            "dimensión antropológica bienestar social EIA",
        ],
    },
    "linea_base_patrimonio": {
        "capitulo": 3,
        "nombre": "Línea de Base - Patrimonio Cultural",
        "descripcion": "Caracterización de patrimonio arqueológico, histórico, paleontológico",
        "prioridad": "media",
        "requerido_siempre": False,
        "condiciones": ["trigger_f"],
        "queries_rag": [
            "patrimonio cultural arqueológico evaluación impacto ambiental",
            "línea de base patrimonio arqueológico paleontológico",
            "sitios arqueológicos proyecto minero hallazgos",
        ],
    },
    "linea_base_paisaje": {
        "capitulo": 3,
        "nombre": "Línea de Base - Paisaje",
        "descripcion": "Caracterización visual del territorio, singularidades paisajísticas, cuencas visuales y puntos de observación relevantes",
        "prioridad": "media",
        "requerido_siempre": False,
        "condiciones": ["trigger_e", "paisaje_singular"],
        "queries_rag": [
            "línea de base paisaje caracterización visual territorio",
            "evaluación impacto paisajístico cuencas visuales",
            "singularidades paisajísticas valor escénico proyecto minero",
        ],
    },
    "linea_base_areas_protegidas": {
        "capitulo": 3,
        "nombre": "Línea de Base - Áreas Protegidas",
        "descripcion": "Descripción de parques nacionales, reservas, santuarios, sitios prioritarios u otras áreas protegidas cercanas al proyecto",
        "prioridad": "alta",
        "requerido_siempre": False,
        "condiciones": ["areas_protegidas"],
        "queries_rag": [
            "áreas protegidas parques nacionales reservas naturales SNASPE",
            "sitios prioritarios conservación biodiversidad",
            "santuarios de la naturaleza protección legal ambiental",
        ],
    },
    "linea_base_uso_territorio": {
        "capitulo": 3,
        "nombre": "Línea de Base - Uso Actual del Territorio",
        "descripcion": "Usos de suelo existentes (urbano, agrícola, industrial, protegido), planificación territorial y actividades económicas",
        "prioridad": "alta",
        "requerido_siempre": True,
        "queries_rag": [
            "uso de suelo planificación territorial evaluación ambiental",
            "instrumentos planificación territorial proyecto minero",
            "actividades económicas uso territorio línea base",
        ],
    },
    "prediccion_impactos": {
        "capitulo": 4,
        "nombre": "Predicción y Evaluación de Impactos",
        "descripcion": "Metodología de evaluación de impactos, matriz de impactos, valoración",
        "prioridad": "alta",
        "requerido_siempre": True,
        "queries_rag": [
            "predicción evaluación impactos ambientales metodología",
            "matriz de impactos proyecto minero valoración",
            "identificación impactos significativos EIA",
        ],
    },
    "efectos_art11": {
        "capitulo": 4,
        "nombre": "Descripción de Efectos Art. 11",
        "descripcion": "Análisis detallado de los efectos que gatillan EIA según Art. 11",
        "prioridad": "alta",
        "requerido_siempre": True,
        "queries_rag": [
            "artículo 11 Ley 19300 efectos características circunstancias",
            "literales artículo 11 evaluación impacto ambiental",
            "análisis efectos adversos significativos EIA",
        ],
    },
    "riesgo_salud": {
        "capitulo": 4,
        "nombre": "Riesgo a la Salud de la Población",
        "descripcion": "Evaluación de riesgos para la salud pública",
        "prioridad": "alta",
        "requerido_siempre": False,
        "condiciones": ["trigger_c"],
        "queries_rag": [
            "riesgo salud población proyecto minero evaluación",
            "literal c artículo 11 riesgo salud SEIA",
            "evaluación sanitaria impactos salud pública",
        ],
    },
    "plan_mitigacion": {
        "capitulo": 5,
        "nombre": "Plan de Medidas de Mitigación/Reparación/Compensación",
        "descripcion": "Jerarquía de mitigación: evitar, minimizar, reparar, compensar",
        "prioridad": "alta",
        "requerido_siempre": True,
        "queries_rag": [
            "plan de medidas de mitigación reparación compensación",
            "jerarquía de mitigación proyecto minero EIA",
            "medidas ambientales impactos significativos",
        ],
    },
    "plan_contingencias": {
        "capitulo": 6,
        "nombre": "Plan de Prevención de Contingencias",
        "descripcion": "Escenarios de emergencia, riesgos y medidas de respuesta",
        "prioridad": "alta",
        "requerido_siempre": True,
        "queries_rag": [
            "plan prevención contingencias accidentes emergencias",
            "gestión de emergencias proyecto minero ambiental",
            "riesgos operacionales medidas prevención",
        ],
    },
    "plan_seguimiento": {
        "capitulo": 7,
        "nombre": "Plan de Seguimiento Ambiental",
        "descripcion": "Indicadores ambientales, frecuencia de monitoreo, responsables",
        "prioridad": "alta",
        "requerido_siempre": True,
        "queries_rag": [
            "plan de seguimiento ambiental monitoreo EIA",
            "indicadores ambientales frecuencia monitoreo",
            "fiscalización seguimiento variables ambientales",
        ],
    },
    "monitoreo_participativo": {
        "capitulo": 7,
        "nombre": "Monitoreo Participativo",
        "descripcion": "Incorporación de la comunidad local en el seguimiento del proyecto: informes periódicos, capacitaciones, visitas de terreno y canales de comunicación",
        "prioridad": "media",
        "requerido_siempre": True,
        "queries_rag": [
            "monitoreo participativo comunidad seguimiento ambiental",
            "participación comunidades monitoreo proyecto minero",
            "vigilancia ciudadana seguimiento ambiental local",
        ],
    },
    "plan_cumplimiento": {
        "capitulo": 9,
        "nombre": "Plan de Cumplimiento de Legislación",
        "descripcion": "Normativa ambiental aplicable y forma de cumplimiento",
        "prioridad": "media",
        "requerido_siempre": True,
        "queries_rag": [
            "plan cumplimiento legislación ambiental aplicable",
            "normativa vigente proyecto minero SEIA",
        ],
    },
    "pas_requeridos": {
        "capitulo": 9,
        "nombre": "Permisos Ambientales Sectoriales",
        "descripcion": "PAS aplicables según DS 40",
        "prioridad": "alta",
        "requerido_siempre": True,
        "queries_rag": [
            "permisos ambientales sectoriales DS 40 aplicables",
            "PAS proyecto minero evaluación ambiental",
            "permisos sectoriales artículo DS 40 reglamento",
        ],
    },
    "compromisos_voluntarios": {
        "capitulo": 10,
        "nombre": "Compromisos Ambientales Voluntarios",
        "descripcion": "Medidas adicionales propuestas por el titular",
        "prioridad": "baja",
        "requerido_siempre": False,
        "queries_rag": [
            "compromisos ambientales voluntarios titular proyecto",
        ],
    },
    "participacion_ciudadana": {
        "capitulo": 8,
        "nombre": "Participación Ciudadana",
        "descripcion": "Proceso de consulta pública y respuesta a observaciones",
        "prioridad": "media",
        "requerido_siempre": True,
        "queries_rag": [
            "participación ciudadana EIA proceso consulta pública",
            "observaciones ciudadanas respuesta titular SEIA",
        ],
    },
    "fichas_resumen": {
        "capitulo": 11,
        "nombre": "Fichas Resumen por Fase",
        "descripcion": "Fichas de construcción, operación y cierre del proyecto",
        "prioridad": "alta",
        "requerido_siempre": True,
        "queries_rag": [
            "fichas resumen fases proyecto construcción operación cierre",
            "caracterización actividades fases proyecto minero",
        ],
    },
    "apendices_anexos": {
        "capitulo": 12,
        "nombre": "Apéndices y Anexos",
        "descripcion": "Informes técnicos especializados, resultados de laboratorio, certificados profesionales, equipo elaborador, bibliografía, planos y cartografía",
        "prioridad": "media",
        "requerido_siempre": True,
        "queries_rag": [
            "anexos apéndices EIA documentación técnica informes",
            "equipo elaborador profesionales estudio impacto ambiental",
            "bibliografía referencias técnicas evaluación ambiental",
        ],
    },
}


class ServicioComponentesEIA:
    """Servicio para generar y gestionar checklist de componentes EIA."""

    def __init__(self, buscador: BuscadorLegal):
        """
        Inicializa el servicio.

        Args:
            buscador: Instancia del buscador RAG
        """
        self.buscador = buscador

    async def generar_checklist(
        self,
        db: AsyncSession,
        proyecto_id: int,
        analisis_id: Optional[int],
        clasificacion: Dict[str, Any],
        resultado_gis: Dict[str, Any],
    ) -> List[ComponenteEIAChecklist]:
        """
        Genera el checklist completo de componentes EIA.

        Args:
            db: Sesión de base de datos
            proyecto_id: ID del proyecto
            analisis_id: ID del análisis (opcional)
            clasificacion: Resultado de clasificación DIA/EIA
            resultado_gis: Resultado del análisis espacial

        Returns:
            Lista de componentes del checklist creados
        """
        logger.info(f"Generando checklist EIA para proyecto {proyecto_id}")

        # 1. Determinar componentes requeridos
        componentes_requeridos = self._determinar_componentes(
            clasificacion=clasificacion,
            resultado_gis=resultado_gis,
        )

        logger.info(f"Componentes requeridos: {len(componentes_requeridos)}")

        # 2. Crear registros de componentes con material RAG
        componentes_creados = []

        for comp_key in componentes_requeridos:
            comp_def = COMPONENTES_EIA[comp_key]

            # Buscar material RAG para este componente
            material_rag, sugerencias = await self._buscar_material_componente(
                db=db,
                componente_def=comp_def,
                componente_key=comp_key,
            )

            # Determinar razón de inclusión
            razon_inclusion = self._generar_razon_inclusion(
                comp_key=comp_key,
                comp_def=comp_def,
                clasificacion=clasificacion,
                resultado_gis=resultado_gis,
            )

            # Crear registro
            componente = ComponenteEIAChecklist(
                proyecto_id=proyecto_id,
                analisis_id=analisis_id,
                componente=comp_key,
                capitulo=comp_def["capitulo"],
                nombre=comp_def["nombre"],
                descripcion=comp_def["descripcion"],
                requerido=comp_def["requerido_siempre"],
                prioridad=comp_def["prioridad"],
                estado="pendiente",
                progreso_porcentaje=0,
                material_rag=material_rag,
                sugerencias_busqueda=sugerencias,
                razon_inclusion=razon_inclusion,
                triggers_relacionados=self._extraer_triggers(clasificacion),
            )

            db.add(componente)
            componentes_creados.append(componente)

        # 3. Guardar en base de datos
        await db.commit()

        # Refrescar objetos para obtener IDs
        for componente in componentes_creados:
            await db.refresh(componente)

        logger.info(f"Checklist creado: {len(componentes_creados)} componentes")
        return componentes_creados

    def _determinar_componentes(
        self,
        clasificacion: Dict[str, Any],
        resultado_gis: Dict[str, Any],
    ) -> List[str]:
        """
        Determina qué componentes son necesarios según el proyecto.

        Args:
            clasificacion: Resultado de clasificación DIA/EIA
            resultado_gis: Resultado del análisis espacial

        Returns:
            Lista de claves de componentes requeridos
        """
        componentes = []

        # Obtener triggers
        triggers_eia = clasificacion.get("triggers_eia", {})
        triggers_activos = [k for k, v in triggers_eia.items() if v.get("aplica", False)]

        # 1. Incluir todos los componentes requeridos siempre
        for comp_key, comp_def in COMPONENTES_EIA.items():
            if comp_def["requerido_siempre"]:
                componentes.append(comp_key)

        # 2. Evaluar componentes condicionales
        for comp_key, comp_def in COMPONENTES_EIA.items():
            if comp_def["requerido_siempre"]:
                continue  # Ya incluido

            condiciones = comp_def.get("condiciones", [])

            # Línea base biótica
            if comp_key == "linea_base_biotico":
                # Trigger e) o áreas protegidas cercanas
                if "e" in triggers_activos:
                    componentes.append(comp_key)
                    continue

                # Áreas protegidas detectadas
                areas_protegidas = resultado_gis.get("areas_protegidas", [])
                if any(a.get("intersecta") or a.get("distancia_m", float("inf")) < 5000 for a in areas_protegidas):
                    componentes.append(comp_key)
                    continue

            # Patrimonio cultural
            elif comp_key == "linea_base_patrimonio":
                if "f" in triggers_activos:
                    componentes.append(comp_key)
                    continue

            # Riesgo a la salud
            elif comp_key == "riesgo_salud":
                if "c" in triggers_activos:
                    componentes.append(comp_key)
                    continue

            # Línea base paisaje
            elif comp_key == "linea_base_paisaje":
                # Trigger e) o paisaje singular detectado
                if "e" in triggers_activos:
                    componentes.append(comp_key)
                    continue
                # Verificar si hay paisaje singular en clasificación
                if clasificacion.get("paisaje_singular", False):
                    componentes.append(comp_key)
                    continue

            # Línea base áreas protegidas
            elif comp_key == "linea_base_areas_protegidas":
                areas_protegidas = resultado_gis.get("areas_protegidas", [])
                if any(a.get("intersecta") or a.get("distancia_m", float("inf")) < 10000 for a in areas_protegidas):
                    componentes.append(comp_key)
                    continue

            # Compromisos voluntarios (siempre se ofrece como opción)
            elif comp_key == "compromisos_voluntarios":
                # Siempre se incluye como opción, pero no es obligatorio
                componentes.append(comp_key)
                continue

        return list(set(componentes))  # Eliminar duplicados

    async def _buscar_material_componente(
        self,
        db: AsyncSession,
        componente_def: Dict[str, Any],
        componente_key: str,
    ) -> tuple[List[Dict[str, Any]], List[str]]:
        """
        Busca material RAG relevante para un componente.

        Args:
            db: Sesión de base de datos
            componente_def: Definición del componente
            componente_key: Clave del componente

        Returns:
            Tupla (material_rag, sugerencias_busqueda)
        """
        queries = componente_def.get("queries_rag", [])

        if not queries:
            return [], []

        # Ejecutar máximo 2 queries por componente
        queries_a_ejecutar = queries[:2]
        queries_sugerencias = queries[2:] if len(queries) > 2 else []

        material_rag = []

        for query in queries_a_ejecutar:
            try:
                resultados = await self.buscador.buscar(
                    db=db,
                    query=query,
                    limite=3,  # Máximo 3 fragmentos por query
                    umbral_similitud=0.5,
                )

                for r in resultados:
                    material_rag.append({
                        "documento_id": r.documento_id,
                        "titulo": r.documento_titulo,
                        "contenido": r.contenido[:500],  # Limitar a 500 caracteres
                        "similitud": r.similitud,
                    })

            except Exception as e:
                logger.error(f"Error buscando material para {componente_key}: {e}")

        # Limitar a máximo 5 fragmentos totales
        material_rag = material_rag[:5]

        return material_rag, queries_sugerencias

    def _generar_razon_inclusion(
        self,
        comp_key: str,
        comp_def: Dict[str, Any],
        clasificacion: Dict[str, Any],
        resultado_gis: Dict[str, Any],
    ) -> str:
        """
        Genera la razón por la que este componente es necesario.

        Args:
            comp_key: Clave del componente
            comp_def: Definición del componente
            clasificacion: Resultado de clasificación
            resultado_gis: Resultado GIS

        Returns:
            Texto explicativo
        """
        if comp_def["requerido_siempre"]:
            return "Componente obligatorio para todo EIA según la normativa vigente."

        triggers_eia = clasificacion.get("triggers_eia", {})
        triggers_activos = [k for k, v in triggers_eia.items() if v.get("aplica", False)]

        # Casos específicos
        if comp_key == "linea_base_biotico":
            if "e" in triggers_activos:
                return "Requerido por literal e) del Art. 11: efectos adversos significativos sobre flora, fauna o ecosistemas."

            areas_protegidas = resultado_gis.get("areas_protegidas", [])
            areas_cercanas = [a for a in areas_protegidas if a.get("distancia_m", float("inf")) < 5000]
            if areas_cercanas:
                return f"Proyecto cercano a {len(areas_cercanas)} área(s) protegida(s). Requiere caracterización biótica."

        elif comp_key == "linea_base_patrimonio":
            if "f" in triggers_activos:
                return "Requerido por literal f) del Art. 11: alteración significativa de monumentos o patrimonio cultural."

        elif comp_key == "riesgo_salud":
            if "c" in triggers_activos:
                return "Requerido por literal c) del Art. 11: riesgo para la salud de la población."

        elif comp_key == "linea_base_paisaje":
            if "e" in triggers_activos:
                return "Requerido por literal e) del Art. 11: efectos adversos sobre el valor paisajístico o turístico."
            if clasificacion.get("paisaje_singular", False):
                return "Proyecto ubicado en zona con singularidades paisajísticas reconocidas."

        elif comp_key == "linea_base_areas_protegidas":
            areas_protegidas = resultado_gis.get("areas_protegidas", [])
            areas_cercanas = [a for a in areas_protegidas if a.get("distancia_m", float("inf")) < 10000]
            if areas_cercanas:
                nombres = [a.get("nombre", "Área protegida") for a in areas_cercanas[:3]]
                return f"Proyecto cercano a áreas protegidas: {', '.join(nombres)}. Requiere descripción detallada."

        elif comp_key == "compromisos_voluntarios":
            return "Componente opcional para medidas ambientales adicionales propuestas por el titular."

        return "Componente incluido por precaución según las características del proyecto."

    def _extraer_triggers(self, clasificacion: Dict[str, Any]) -> List[str]:
        """
        Extrae la lista de triggers activos.

        Args:
            clasificacion: Resultado de clasificación

        Returns:
            Lista de literales activos (ej: ['a', 'b', 'e'])
        """
        triggers_eia = clasificacion.get("triggers_eia", {})
        return [k for k, v in triggers_eia.items() if v.get("aplica", False)]
