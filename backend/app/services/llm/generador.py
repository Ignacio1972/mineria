"""
Generador de Informes de Prefactibilidad Ambiental

Integra los resultados de GIS, RAG, motor de reglas y LLM
para generar informes estructurados de prefactibilidad.
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Optional
from enum import Enum
from datetime import datetime
import asyncio

from app.services.llm.cliente import ClienteLLM, get_cliente_llm
from app.services.llm.prompts import GestorPrompts, TipoPrompt, ContextoPrompt
from app.services.reglas.seia import MotorReglasSSEIA, ClasificacionSEIA
from app.services.reglas.alertas import SistemaAlertas

logger = logging.getLogger(__name__)


class SeccionInforme(str, Enum):
    """Secciones del informe de prefactibilidad"""
    RESUMEN_EJECUTIVO = "resumen_ejecutivo"
    DESCRIPCION_PROYECTO = "descripcion_proyecto"
    ANALISIS_TERRITORIAL = "analisis_territorial"
    EVALUACION_SEIA = "evaluacion_seia"
    NORMATIVA_APLICABLE = "normativa_aplicable"
    ALERTAS_AMBIENTALES = "alertas_ambientales"
    PERMISOS_REQUERIDOS = "permisos_requeridos"
    LINEA_BASE_SUGERIDA = "linea_base_sugerida"
    RECOMENDACIONES = "recomendaciones"
    CONCLUSION = "conclusion"


@dataclass
class SeccionGenerada:
    """Representa una sección del informe generada"""
    seccion: SeccionInforme
    titulo: str
    contenido: str
    metadata: dict = field(default_factory=dict)
    tokens_usados: int = 0
    tiempo_generacion_ms: int = 0


@dataclass
class InformePrefactibilidad:
    """Informe completo de prefactibilidad ambiental"""
    id: str
    fecha_generacion: datetime
    datos_proyecto: dict[str, Any]
    resultado_gis: dict[str, Any]
    clasificacion_seia: ClasificacionSEIA
    alertas: list[dict[str, Any]]
    secciones: list[SeccionGenerada]
    normativa_citada: list[dict[str, Any]]
    tokens_totales: int = 0
    tiempo_total_ms: int = 0
    version_modelo: str = ""

    def to_dict(self) -> dict:
        """Convierte el informe a diccionario para serialización."""
        return {
            "id": self.id,
            "fecha_generacion": self.fecha_generacion.isoformat(),
            "datos_proyecto": self.datos_proyecto,
            "resultado_gis": self.resultado_gis,
            "clasificacion_seia": self.clasificacion_seia.to_dict(),
            "alertas": self.alertas,
            "secciones": [
                {
                    "seccion": s.seccion.value,
                    "titulo": s.titulo,
                    "contenido": s.contenido,
                    "metadata": s.metadata,
                }
                for s in self.secciones
            ],
            "normativa_citada": self.normativa_citada,
            "metricas": {
                "tokens_totales": self.tokens_totales,
                "tiempo_total_ms": self.tiempo_total_ms,
                "version_modelo": self.version_modelo,
            }
        }

    def to_texto_plano(self) -> str:
        """Genera versión en texto plano del informe."""
        lineas = []
        lineas.append("=" * 80)
        lineas.append("INFORME DE PREFACTIBILIDAD AMBIENTAL")
        lineas.append("=" * 80)
        lineas.append(f"\nProyecto: {self.datos_proyecto.get('nombre', 'N/D')}")
        lineas.append(f"Fecha: {self.fecha_generacion.strftime('%d/%m/%Y %H:%M')}")
        lineas.append(f"ID Informe: {self.id}")
        lineas.append("\n" + "-" * 80)

        for seccion in self.secciones:
            lineas.append(f"\n## {seccion.titulo.upper()}\n")
            lineas.append(seccion.contenido)
            lineas.append("\n" + "-" * 40)

        lineas.append("\n" + "=" * 80)
        lineas.append("FIN DEL INFORME")
        lineas.append("=" * 80)

        return "\n".join(lineas)


class GeneradorInformes:
    """
    Generador de informes de prefactibilidad ambiental.

    Orquesta la generación del informe integrando:
    - Análisis espacial GIS
    - Búsqueda RAG de normativa
    - Motor de reglas SEIA
    - Generación de texto con LLM
    """

    # Títulos de secciones
    TITULOS_SECCIONES = {
        SeccionInforme.RESUMEN_EJECUTIVO: "Resumen Ejecutivo",
        SeccionInforme.DESCRIPCION_PROYECTO: "Descripción del Proyecto",
        SeccionInforme.ANALISIS_TERRITORIAL: "Análisis Territorial",
        SeccionInforme.EVALUACION_SEIA: "Evaluación SEIA - Vía de Ingreso",
        SeccionInforme.NORMATIVA_APLICABLE: "Normativa Ambiental Aplicable",
        SeccionInforme.ALERTAS_AMBIENTALES: "Alertas Ambientales Identificadas",
        SeccionInforme.PERMISOS_REQUERIDOS: "Permisos Ambientales Sectoriales",
        SeccionInforme.LINEA_BASE_SUGERIDA: "Línea Base Ambiental Sugerida",
        SeccionInforme.RECOMENDACIONES: "Recomendaciones",
        SeccionInforme.CONCLUSION: "Conclusión",
    }

    def __init__(
        self,
        cliente_llm: Optional[ClienteLLM] = None,
        motor_reglas: Optional[MotorReglasSSEIA] = None,
        sistema_alertas: Optional[SistemaAlertas] = None,
    ):
        """
        Inicializa el generador de informes.

        Args:
            cliente_llm: Cliente LLM opcional (usa singleton si no se proporciona)
            motor_reglas: Motor de reglas SEIA opcional
            sistema_alertas: Sistema de alertas opcional
        """
        self.cliente_llm = cliente_llm or get_cliente_llm()
        self.motor_reglas = motor_reglas or MotorReglasSSEIA()
        self.sistema_alertas = sistema_alertas or SistemaAlertas()
        self.gestor_prompts = GestorPrompts()
        logger.info("GeneradorInformes inicializado")

    async def generar_informe(
        self,
        datos_proyecto: dict[str, Any],
        resultado_gis: dict[str, Any],
        normativa_relevante: list[dict[str, Any]],
        secciones_a_generar: Optional[list[SeccionInforme]] = None,
    ) -> InformePrefactibilidad:
        """
        Genera un informe completo de prefactibilidad ambiental.

        Args:
            datos_proyecto: Datos del proyecto minero
            resultado_gis: Resultado del análisis espacial
            normativa_relevante: Fragmentos de normativa del RAG
            secciones_a_generar: Lista opcional de secciones a incluir

        Returns:
            InformePrefactibilidad con todas las secciones generadas
        """
        import time
        import uuid

        inicio = time.time()
        logger.info(f"Iniciando generación de informe para: {datos_proyecto.get('nombre', 'N/D')}")

        # 1. Ejecutar motor de reglas SEIA
        clasificacion = self.motor_reglas.clasificar_proyecto(resultado_gis, datos_proyecto)
        logger.info(f"Clasificación SEIA: {clasificacion.via_ingreso.value}")

        # 2. Generar alertas
        alertas = self.sistema_alertas.generar_alertas(resultado_gis, datos_proyecto)
        alertas_dict = [a.to_dict() for a in alertas]
        logger.info(f"Alertas generadas: {len(alertas)}")

        # 3. Preparar contexto para prompts
        contexto = ContextoPrompt(
            datos_proyecto=datos_proyecto,
            resultado_gis=resultado_gis,
            clasificacion_seia=clasificacion.to_dict(),
            alertas=alertas_dict,
            normativa_relevante=normativa_relevante,
        )

        # 4. Determinar secciones a generar
        if secciones_a_generar is None:
            secciones_a_generar = list(SeccionInforme)

        # 5. Generar secciones EN PARALELO para evitar timeout
        tokens_totales = 0

        async def generar_seccion_safe(seccion: SeccionInforme) -> SeccionGenerada:
            """Wrapper que captura errores por sección."""
            try:
                return await self._generar_seccion(seccion, contexto, clasificacion, alertas_dict)
            except Exception as e:
                logger.error(f"Error generando sección {seccion.value}: {e}")
                return SeccionGenerada(
                    seccion=seccion,
                    titulo=self.TITULOS_SECCIONES[seccion],
                    contenido=f"[Error al generar esta sección: {str(e)}]",
                    metadata={"error": str(e)},
                )

        # Ejecutar todas las secciones en paralelo
        tareas = [generar_seccion_safe(seccion) for seccion in secciones_a_generar]
        resultados = await asyncio.gather(*tareas)

        # Ordenar resultados según orden original y calcular tokens
        seccion_orden = {s: i for i, s in enumerate(secciones_a_generar)}
        secciones_generadas = sorted(resultados, key=lambda x: seccion_orden.get(x.seccion, 999))

        for seccion_gen in secciones_generadas:
            tokens_totales += seccion_gen.tokens_usados
            logger.debug(f"Sección generada: {seccion_gen.seccion.value}")

        # 6. Extraer normativa citada
        normativa_citada = self._extraer_normativa_citada(clasificacion, alertas_dict)

        # 7. Crear informe final
        tiempo_total = int((time.time() - inicio) * 1000)

        informe = InformePrefactibilidad(
            id=str(uuid.uuid4())[:8].upper(),
            fecha_generacion=datetime.now(),
            datos_proyecto=datos_proyecto,
            resultado_gis=resultado_gis,
            clasificacion_seia=clasificacion,
            alertas=alertas_dict,
            secciones=secciones_generadas,
            normativa_citada=normativa_citada,
            tokens_totales=tokens_totales,
            tiempo_total_ms=tiempo_total,
            version_modelo=self.cliente_llm.config.modelo,
        )

        logger.info(f"Informe generado: {informe.id} ({tiempo_total}ms, {tokens_totales} tokens)")
        return informe

    async def _generar_seccion(
        self,
        seccion: SeccionInforme,
        contexto: ContextoPrompt,
        clasificacion: ClasificacionSEIA,
        alertas: list[dict],
    ) -> SeccionGenerada:
        """Genera una sección específica del informe."""
        import time

        inicio = time.time()
        titulo = self.TITULOS_SECCIONES[seccion]

        # Mapear sección a tipo de prompt
        tipo_prompt = self._mapear_seccion_a_prompt(seccion)

        if tipo_prompt:
            # Generar con LLM
            prompt = self.gestor_prompts.construir_prompt(tipo_prompt, contexto)
            prompt_sistema = self.gestor_prompts.obtener_prompt_sistema()

            respuesta = await self.cliente_llm.generar(
                prompt_usuario=prompt,
                prompt_sistema=prompt_sistema,
            )

            contenido = respuesta.contenido
            tokens = respuesta.tokens_totales
        else:
            # Generar contenido estático/estructurado
            contenido = self._generar_contenido_estatico(seccion, contexto, clasificacion, alertas)
            tokens = 0

        tiempo_ms = int((time.time() - inicio) * 1000)

        return SeccionGenerada(
            seccion=seccion,
            titulo=titulo,
            contenido=contenido,
            metadata={"tipo_generacion": "llm" if tipo_prompt else "estatico"},
            tokens_usados=tokens,
            tiempo_generacion_ms=tiempo_ms,
        )

    def _mapear_seccion_a_prompt(self, seccion: SeccionInforme) -> Optional[TipoPrompt]:
        """Mapea una sección del informe a su tipo de prompt."""
        mapeo = {
            SeccionInforme.RESUMEN_EJECUTIVO: TipoPrompt.RESUMEN_EJECUTIVO,
            SeccionInforme.ANALISIS_TERRITORIAL: TipoPrompt.ANALISIS_GIS,
            SeccionInforme.EVALUACION_SEIA: TipoPrompt.EVALUACION_TRIGGERS,
            SeccionInforme.NORMATIVA_APLICABLE: TipoPrompt.NORMATIVA_APLICABLE,
            SeccionInforme.PERMISOS_REQUERIDOS: TipoPrompt.PERMISOS_SECTORIALES,
            SeccionInforme.LINEA_BASE_SUGERIDA: TipoPrompt.LINEA_BASE,
            SeccionInforme.RECOMENDACIONES: TipoPrompt.RECOMENDACIONES,
        }
        return mapeo.get(seccion)

    def _generar_contenido_estatico(
        self,
        seccion: SeccionInforme,
        contexto: ContextoPrompt,
        clasificacion: ClasificacionSEIA,
        alertas: list[dict],
    ) -> str:
        """Genera contenido estático para secciones que no requieren LLM."""

        if seccion == SeccionInforme.DESCRIPCION_PROYECTO:
            return self._generar_descripcion_proyecto(contexto.datos_proyecto)

        elif seccion == SeccionInforme.ALERTAS_AMBIENTALES:
            return self._generar_seccion_alertas(alertas)

        elif seccion == SeccionInforme.CONCLUSION:
            return self._generar_conclusion(clasificacion, alertas)

        return "[Contenido no disponible]"

    def _generar_descripcion_proyecto(self, datos: dict) -> str:
        """Genera la sección de descripción del proyecto."""
        lineas = []

        lineas.append(f"**Nombre del Proyecto:** {datos.get('nombre', 'No especificado')}")
        lineas.append(f"**Titular:** {datos.get('titular', 'No especificado')}")
        lineas.append(f"**Región:** {datos.get('region', 'No especificada')}")
        lineas.append(f"**Comuna:** {datos.get('comuna', 'No especificada')}")
        lineas.append("")
        lineas.append("### Características Técnicas")
        lineas.append(f"- **Tipo de minería:** {datos.get('tipo_mineria', 'No especificado')}")
        lineas.append(f"- **Mineral principal:** {datos.get('mineral_principal', 'No especificado')}")
        lineas.append(f"- **Fase del proyecto:** {datos.get('fase', 'No especificada')}")
        lineas.append(f"- **Superficie:** {datos.get('superficie_ha', 'N/D')} hectáreas")
        lineas.append(f"- **Vida útil estimada:** {datos.get('vida_util_anos', 'N/D')} años")
        lineas.append("")
        lineas.append("### Recursos y Personal")
        lineas.append(f"- **Uso de agua:** {datos.get('uso_agua_lps', 'N/D')} L/s")
        lineas.append(f"- **Fuente de agua:** {datos.get('fuente_agua', 'No especificada')}")
        lineas.append(f"- **Energía requerida:** {datos.get('energia_mw', 'N/D')} MW")
        lineas.append(f"- **Trabajadores (construcción):** {datos.get('trabajadores_construccion', 'N/D')}")
        lineas.append(f"- **Trabajadores (operación):** {datos.get('trabajadores_operacion', 'N/D')}")
        lineas.append("")
        lineas.append("### Inversión")
        lineas.append(f"- **Inversión estimada:** {datos.get('inversion_musd', 'N/D')} MUSD")

        if datos.get('descripcion'):
            lineas.append("")
            lineas.append("### Descripción Adicional")
            lineas.append(datos['descripcion'])

        return "\n".join(lineas)

    def _generar_seccion_alertas(self, alertas: list[dict]) -> str:
        """Genera la sección de alertas ambientales."""
        if not alertas:
            return "No se identificaron alertas ambientales significativas en el análisis."

        lineas = []
        lineas.append(f"Se identificaron **{len(alertas)} alertas** ambientales:\n")

        # Agrupar por nivel
        por_nivel = {}
        for a in alertas:
            nivel = a.get("nivel", "INFO")
            if nivel not in por_nivel:
                por_nivel[nivel] = []
            por_nivel[nivel].append(a)

        for nivel in ["CRITICA", "ALTA", "MEDIA", "BAJA", "INFO"]:
            if nivel in por_nivel:
                lineas.append(f"\n### Alertas de Nivel {nivel} ({len(por_nivel[nivel])})\n")
                for a in por_nivel[nivel]:
                    lineas.append(f"**{a.get('titulo', 'Sin título')}**")
                    lineas.append(f"- Categoría: {a.get('categoria', 'N/D')}")
                    lineas.append(f"- Descripción: {a.get('descripcion', 'N/D')}")
                    if a.get("acciones_requeridas"):
                        lineas.append("- Acciones requeridas:")
                        for accion in a["acciones_requeridas"][:3]:
                            lineas.append(f"  - {accion}")
                    lineas.append("")

        return "\n".join(lineas)

    def _generar_conclusion(
        self,
        clasificacion: ClasificacionSEIA,
        alertas: list[dict]
    ) -> str:
        """Genera la sección de conclusión."""
        lineas = []

        via = clasificacion.via_ingreso.value
        confianza = clasificacion.confianza * 100
        num_triggers = len(clasificacion.triggers)

        lineas.append("### Clasificación Final\n")
        lineas.append(f"Basado en el análisis realizado, se recomienda que el proyecto ingrese al SEIA como:")
        lineas.append(f"\n**{via}** (Nivel de confianza: {confianza:.0f}%)\n")
        lineas.append(f"*{clasificacion.justificacion}*\n")

        lineas.append("### Fundamento\n")
        if num_triggers > 0:
            lineas.append(f"Se detectaron **{num_triggers} trigger(s)** del Artículo 11 de la Ley 19.300:")
            for t in clasificacion.triggers[:5]:
                lineas.append(f"- Letra {t.letra.value}): {t.descripcion} ({t.severidad.value})")
        else:
            lineas.append("No se detectaron triggers del Artículo 11 que requieran EIA.")

        alertas_criticas = sum(1 for a in alertas if a.get("nivel") == "CRITICA")
        alertas_altas = sum(1 for a in alertas if a.get("nivel") == "ALTA")

        if alertas_criticas or alertas_altas:
            lineas.append(f"\nSe identificaron {alertas_criticas} alerta(s) crítica(s) y {alertas_altas} alerta(s) alta(s).")

        lineas.append("\n### Disclaimer\n")
        lineas.append("*Este informe es un análisis preliminar de prefactibilidad ambiental basado en "
                     "información espacial y normativa disponible. No reemplaza la evaluación formal "
                     "del Servicio de Evaluación Ambiental (SEA) ni la opinión de expertos especializados. "
                     "Se recomienda validar los hallazgos con profesionales del área antes de tomar "
                     "decisiones de inversión o de ingreso al SEIA.*")

        return "\n".join(lineas)

    def _extraer_normativa_citada(
        self,
        clasificacion: ClasificacionSEIA,
        alertas: list[dict]
    ) -> list[dict]:
        """Extrae la normativa citada en el análisis."""
        normativa = set()

        # Normativa de triggers
        for t in clasificacion.triggers:
            normativa.add(t.fundamento_legal)

        # Normativa de alertas
        for a in alertas:
            for n in a.get("normativa_relacionada", []):
                normativa.add(n)

        return [{"referencia": n} for n in sorted(normativa)]

    async def generar_seccion_individual(
        self,
        seccion: SeccionInforme,
        datos_proyecto: dict[str, Any],
        resultado_gis: dict[str, Any],
        normativa_relevante: list[dict[str, Any]],
    ) -> SeccionGenerada:
        """
        Genera una sección individual del informe.

        Útil para regenerar secciones específicas o para
        generación incremental.
        """
        # Ejecutar análisis necesarios
        clasificacion = self.motor_reglas.clasificar_proyecto(resultado_gis, datos_proyecto)
        alertas = self.sistema_alertas.generar_alertas(resultado_gis, datos_proyecto)
        alertas_dict = [a.to_dict() for a in alertas]

        contexto = ContextoPrompt(
            datos_proyecto=datos_proyecto,
            resultado_gis=resultado_gis,
            clasificacion_seia=clasificacion.to_dict(),
            alertas=alertas_dict,
            normativa_relevante=normativa_relevante,
        )

        return await self._generar_seccion(seccion, contexto, clasificacion, alertas_dict)
