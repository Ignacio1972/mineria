"""
Gestor de Prompts Especializados

Prompts diseñados para análisis de prefactibilidad ambiental
de proyectos mineros en Chile, con énfasis en normativa SEIA.
"""

import logging
from enum import Enum
from typing import Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class TipoPrompt(str, Enum):
    """Tipos de prompts disponibles"""
    SISTEMA_BASE = "sistema_base"
    RESUMEN_EJECUTIVO = "resumen_ejecutivo"
    ANALISIS_GIS = "analisis_gis"
    EVALUACION_TRIGGERS = "evaluacion_triggers"
    NORMATIVA_APLICABLE = "normativa_aplicable"
    RECOMENDACIONES = "recomendaciones"
    PERMISOS_SECTORIALES = "permisos_sectoriales"
    LINEA_BASE = "linea_base"
    MEDIDAS_MITIGACION = "medidas_mitigacion"


@dataclass
class ContextoPrompt:
    """Contexto para personalizar prompts"""
    datos_proyecto: dict[str, Any]
    resultado_gis: dict[str, Any]
    clasificacion_seia: dict[str, Any]
    alertas: list[dict[str, Any]]
    normativa_relevante: list[dict[str, Any]]


class GestorPrompts:
    """
    Gestor de prompts especializados para análisis ambiental.

    Proporciona prompts optimizados para:
    - Análisis de prefactibilidad ambiental
    - Evaluación de triggers SEIA
    - Generación de secciones de informes
    - Recomendaciones técnicas y legales
    """

    # Prompt de sistema base para todos los análisis
    SISTEMA_BASE = """Eres un experto en evaluación de impacto ambiental en Chile, especializado en:
- Sistema de Evaluación de Impacto Ambiental (SEIA)
- Ley 19.300 sobre Bases Generales del Medio Ambiente
- DS 40/2012 Reglamento del SEIA
- Normativa sectorial ambiental chilena
- Proyectos mineros y sus impactos ambientales

Tu rol es proporcionar análisis técnicos rigurosos para informes de prefactibilidad ambiental.

INSTRUCCIONES IMPORTANTES:
1. SIEMPRE cita la normativa específica que fundamenta tus conclusiones
2. Sé preciso y técnico, evitando ambigüedades
3. Cuando hay incertidumbre, indícalo explícitamente
4. Usa terminología técnica del SEIA chileno
5. Estructura tus respuestas de forma clara y profesional
6. No inventes datos ni normativa - usa solo lo proporcionado en el contexto
7. Indica cuando se requiere análisis adicional o validación de expertos"""

    # Templates de prompts por tipo
    TEMPLATES = {
        TipoPrompt.RESUMEN_EJECUTIVO: """
Genera un RESUMEN EJECUTIVO para el informe de prefactibilidad ambiental del siguiente proyecto minero.

DATOS DEL PROYECTO:
{datos_proyecto}

CLASIFICACIÓN SEIA:
- Vía de ingreso recomendada: {via_ingreso}
- Nivel de confianza: {confianza}
- Triggers Art. 11 detectados: {num_triggers}

PRINCIPALES ALERTAS:
{alertas_resumen}

INSTRUCCIONES:
1. Redacta un resumen ejecutivo de 3-4 párrafos
2. Incluye: descripción breve del proyecto, principales hallazgos del análisis espacial, clasificación recomendada y justificación
3. Menciona los triggers críticos si los hay
4. Cierra con una conclusión sobre viabilidad preliminar
5. Usa un tono técnico pero accesible

Formato de respuesta:
```
RESUMEN EJECUTIVO

[Párrafo 1: Descripción del proyecto]

[Párrafo 2: Hallazgos principales del análisis]

[Párrafo 3: Clasificación y justificación]

[Párrafo 4: Conclusión y siguientes pasos]
```
""",

        TipoPrompt.ANALISIS_GIS: """
Analiza los resultados del análisis espacial GIS para el proyecto minero.

DATOS DEL PROYECTO:
- Nombre: {nombre_proyecto}
- Tipo de minería: {tipo_mineria}
- Superficie: {superficie_ha} hectáreas
- Región: {region}

RESULTADOS DEL ANÁLISIS ESPACIAL:
{resultado_gis_json}

INSTRUCCIONES:
1. Interpreta cada capa GIS analizada (áreas protegidas, glaciares, cuerpos de agua, etc.)
2. Para cada elemento encontrado, evalúa su significancia ambiental
3. Identifica las restricciones territoriales más relevantes
4. Destaca los elementos que generan triggers del Art. 11
5. Usa distancias y datos específicos del análisis

Estructura tu respuesta en:
1. ÁREAS DE SENSIBILIDAD AMBIENTAL
2. RESTRICCIONES TERRITORIALES
3. ELEMENTOS CRÍTICOS IDENTIFICADOS
4. CONSIDERACIONES PARA LA LÍNEA BASE
""",

        TipoPrompt.EVALUACION_TRIGGERS: """
Evalúa técnicamente los triggers del Artículo 11 de la Ley 19.300 detectados.

PROYECTO: {nombre_proyecto}

TRIGGERS DETECTADOS:
{triggers_json}

CONTEXTO DEL ANÁLISIS GIS:
{contexto_gis}

INSTRUCCIONES:
1. Para cada trigger, explica POR QUÉ aplica según la normativa
2. Cita el artículo y letra específica de la Ley 19.300
3. Relaciona con los elementos GIS que lo activan
4. Evalúa la severidad y certeza de cada trigger
5. Concluye sobre la vía de ingreso al SEIA

Estructura:
Para cada trigger:
- Letra del Art. 11: [a/b/c/d/e/f]
- Descripción legal: [texto del artículo]
- Elementos que lo activan: [del análisis GIS]
- Severidad: [Crítica/Alta/Media/Baja]
- Fundamento técnico: [explicación]

CONCLUSIÓN SOBRE VÍA DE INGRESO:
[DIA o EIA, con justificación técnico-legal]
""",

        TipoPrompt.NORMATIVA_APLICABLE: """
Identifica y describe la normativa ambiental aplicable al proyecto.

DATOS DEL PROYECTO:
{datos_proyecto}

ALERTAS Y COMPONENTES AFECTADOS:
{alertas_json}

FRAGMENTOS NORMATIVOS DEL CORPUS LEGAL:
{normativa_rag}

INSTRUCCIONES:
1. Lista la normativa aplicable organizada por componente ambiental
2. Para cada norma, indica:
   - Nombre y número (ej: "Ley 19.300", "DS 40/2012")
   - Artículos relevantes
   - Cómo aplica al proyecto específico
3. Distingue entre normativa de carácter general y sectorial
4. Identifica los permisos ambientales sectoriales (PAS) potencialmente requeridos

Estructura:
1. NORMATIVA GENERAL AMBIENTAL
2. NORMATIVA SECTORIAL POR COMPONENTE
3. PERMISOS AMBIENTALES SECTORIALES (PAS)
4. OTRAS AUTORIZACIONES REQUERIDAS
""",

        TipoPrompt.RECOMENDACIONES: """
Genera recomendaciones técnicas para el desarrollo del proyecto.

PROYECTO: {nombre_proyecto}
VÍA DE INGRESO: {via_ingreso}
CONFIANZA: {confianza}

TRIGGERS DETECTADOS:
{triggers_resumen}

ALERTAS PRINCIPALES:
{alertas_resumen}

INSTRUCCIONES:
1. Genera recomendaciones específicas y accionables
2. Organiza por prioridad (Críticas, Altas, Medias)
3. Para cada recomendación indica:
   - Acción específica a realizar
   - Componente ambiental relacionado
   - Normativa que la fundamenta
   - Plazo sugerido (pre-ingreso, durante evaluación)
4. Incluye recomendaciones para:
   - Estudios adicionales requeridos
   - Ajustes de diseño del proyecto
   - Permisos a gestionar
   - Relacionamiento comunitario

Formato:
RECOMENDACIONES CRÍTICAS (antes de ingresar al SEIA):
1. [Recomendación]
   - Fundamento: [normativa]
   - Responsable sugerido: [área/especialista]

RECOMENDACIONES ALTAS (incluir en el EIA/DIA):
[...]

RECOMENDACIONES DE MEJORA CONTINUA:
[...]
""",

        TipoPrompt.PERMISOS_SECTORIALES: """
Identifica los Permisos Ambientales Sectoriales (PAS) requeridos.

DATOS DEL PROYECTO:
{datos_proyecto}

COMPONENTES AMBIENTALES AFECTADOS:
{componentes}

ALERTAS DETECTADAS:
{alertas_json}

INSTRUCCIONES:
1. Revisa cada componente ambiental afectado
2. Identifica los PAS del DS 40/2012 que podrían aplicar
3. Para cada PAS indica:
   - Número y nombre (ej: "PAS 155 - Obras en cauces")
   - Servicio que lo otorga
   - Por qué aplicaría al proyecto
   - Requisitos principales
4. Distingue entre PAS obligatorios y probables

Estructura:
PAS OBLIGATORIOS:
- [Número]: [Nombre]
  - Servicio: [ej: DGA, SAG, CONAF]
  - Aplicabilidad: [razón]
  - Requisitos clave: [lista]

PAS PROBABLES (requieren confirmación):
[...]

OTRAS AUTORIZACIONES SECTORIALES:
[...]
""",

        TipoPrompt.LINEA_BASE: """
Define los componentes de línea base ambiental requeridos.

PROYECTO: {nombre_proyecto}
VÍA DE INGRESO: {via_ingreso}

RESULTADO ANÁLISIS GIS:
{resultado_gis_resumen}

TRIGGERS Y ALERTAS:
{triggers_alertas}

INSTRUCCIONES:
1. Identifica los componentes ambientales que requieren caracterización
2. Para cada componente define:
   - Área de influencia sugerida (directa/indirecta)
   - Parámetros a evaluar
   - Metodologías recomendadas
   - Estacionalidad de muestreos
3. Prioriza según los triggers detectados
4. Considera requisitos del DS 40/2012 Art. 18

Estructura por componente:
[COMPONENTE]
- Área de influencia: [descripción]
- Parámetros: [lista]
- Metodología: [descripción]
- Estacionalidad: [requisitos temporales]
- Justificación: [por qué es necesario]
""",

        TipoPrompt.MEDIDAS_MITIGACION: """
Propone medidas de mitigación, reparación y compensación.

PROYECTO: {nombre_proyecto}
TIPO: {tipo_mineria}

IMPACTOS IDENTIFICADOS:
{impactos}

COMPONENTES AFECTADOS:
{componentes}

INSTRUCCIONES:
1. Para cada impacto significativo propone medidas según jerarquía:
   a) Evitar/Prevenir
   b) Minimizar/Mitigar
   c) Reparar/Restaurar
   d) Compensar
2. Las medidas deben ser:
   - Específicas y verificables
   - Técnicamente factibles
   - Proporcionales al impacto
3. Incluye indicadores de seguimiento
4. Referencia normativa cuando aplique

Formato:
IMPACTO: [descripción]
Componente: [ambiental]
Severidad: [alta/media/baja]

MEDIDAS:
1. Prevención: [medida]
   - Indicador: [cómo se verifica]
2. Mitigación: [medida]
   - Indicador: [...]
3. Compensación (si aplica): [medida]
   - Indicador: [...]
"""
    }

    def __init__(self):
        logger.info("GestorPrompts inicializado")

    def obtener_prompt_sistema(self) -> str:
        """Retorna el prompt de sistema base."""
        return self.SISTEMA_BASE

    def construir_prompt(
        self,
        tipo: TipoPrompt,
        contexto: ContextoPrompt
    ) -> str:
        """
        Construye un prompt personalizado con el contexto proporcionado.

        Args:
            tipo: Tipo de prompt a construir
            contexto: Contexto con datos del proyecto y análisis

        Returns:
            Prompt formateado listo para enviar al LLM
        """
        template = self.TEMPLATES.get(tipo)
        if not template:
            raise ValueError(f"Tipo de prompt no soportado: {tipo}")

        # Preparar variables de formato
        variables = self._preparar_variables(contexto)

        # Formatear template
        try:
            prompt = template.format(**variables)
            logger.debug(f"Prompt construido: {tipo.value} ({len(prompt)} chars)")
            return prompt
        except KeyError as e:
            logger.error(f"Variable faltante en template: {e}")
            raise

    def _preparar_variables(self, contexto: ContextoPrompt) -> dict[str, Any]:
        """Prepara las variables para formatear los templates."""
        import json

        datos = contexto.datos_proyecto
        gis = contexto.resultado_gis
        clasif = contexto.clasificacion_seia
        alertas = contexto.alertas

        # Resumen de alertas
        alertas_criticas = [a for a in alertas if a.get("nivel") == "CRITICA"]
        alertas_altas = [a for a in alertas if a.get("nivel") == "ALTA"]
        alertas_resumen = ""
        if alertas_criticas:
            alertas_resumen += f"CRÍTICAS ({len(alertas_criticas)}):\n"
            for a in alertas_criticas[:3]:
                alertas_resumen += f"- {a.get('titulo', 'N/D')}\n"
        if alertas_altas:
            alertas_resumen += f"\nALTAS ({len(alertas_altas)}):\n"
            for a in alertas_altas[:3]:
                alertas_resumen += f"- {a.get('titulo', 'N/D')}\n"

        # Resumen de triggers
        triggers = clasif.get("triggers", [])
        triggers_resumen = ""
        for t in triggers[:5]:
            triggers_resumen += f"- Art. 11 letra {t.get('letra', 'N/D')}: {t.get('descripcion', 'N/D')}\n"
            triggers_resumen += f"  Severidad: {t.get('severidad', 'N/D')}\n"

        # Componentes afectados
        componentes = set()
        for a in alertas:
            componentes.update(a.get("componentes_afectados", []))

        # Resumen GIS
        gis_resumen = []
        if gis.get("areas_protegidas"):
            gis_resumen.append(f"- {len(gis['areas_protegidas'])} área(s) protegida(s)")
        if gis.get("glaciares"):
            gis_resumen.append(f"- {len(gis['glaciares'])} glaciar(es)")
        if gis.get("cuerpos_agua"):
            gis_resumen.append(f"- {len(gis['cuerpos_agua'])} cuerpo(s) de agua")
        if gis.get("comunidades_indigenas"):
            gis_resumen.append(f"- {len(gis['comunidades_indigenas'])} comunidad(es) indígena(s)")

        return {
            # Datos del proyecto
            "datos_proyecto": json.dumps(datos, indent=2, ensure_ascii=False),
            "nombre_proyecto": datos.get("nombre", "Proyecto Sin Nombre"),
            "tipo_mineria": datos.get("tipo_mineria", "No especificado"),
            "superficie_ha": datos.get("superficie_ha", "N/D"),
            "region": datos.get("region", "N/D"),

            # Clasificación SEIA
            "via_ingreso": clasif.get("via_ingreso_recomendada", "N/D"),
            "confianza": f"{clasif.get('confianza', 0) * 100:.0f}%",
            "num_triggers": len(triggers),

            # Triggers
            "triggers_json": json.dumps(triggers, indent=2, ensure_ascii=False),
            "triggers_resumen": triggers_resumen or "No se detectaron triggers.",

            # Alertas
            "alertas_json": json.dumps(alertas[:10], indent=2, ensure_ascii=False),
            "alertas_resumen": alertas_resumen or "No se detectaron alertas críticas o altas.",

            # GIS
            "resultado_gis_json": json.dumps(gis, indent=2, ensure_ascii=False),
            "resultado_gis_resumen": "\n".join(gis_resumen) or "Sin elementos GIS detectados.",
            "contexto_gis": "\n".join(gis_resumen),

            # Normativa
            "normativa_rag": json.dumps(
                contexto.normativa_relevante[:10],
                indent=2,
                ensure_ascii=False
            ),

            # Componentes
            "componentes": ", ".join(sorted(componentes)) or "No especificados",

            # Combinados
            "triggers_alertas": f"TRIGGERS:\n{triggers_resumen}\nALERTAS:\n{alertas_resumen}",
            "impactos": alertas_resumen,
        }

    def obtener_tipos_disponibles(self) -> list[str]:
        """Retorna la lista de tipos de prompts disponibles."""
        return [t.value for t in TipoPrompt]
