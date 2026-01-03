"""
Servicio de Prefactibilidad Ambiental.

Encapsula la lógica de análisis de prefactibilidad ambiental,
separando la lógica de negocio de los endpoints HTTP.
"""

import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.gis.analisis import analizar_proyecto_espacial
from app.services.rag.busqueda import BuscadorLegal
from app.services.reglas import MotorReglasSSEIA, SistemaAlertas, ClasificacionSEIA
from app.services.llm import GeneradorInformes, SeccionInforme

logger = logging.getLogger(__name__)


@dataclass
class ResultadoAnalisis:
    """Resultado completo de un análisis de prefactibilidad."""

    # Identificación
    id: str
    fecha_analisis: str

    # Datos de entrada
    datos_proyecto: dict

    # Resultados GIS
    resultado_gis: dict

    # Clasificación SEIA
    clasificacion: ClasificacionSEIA

    # Alertas
    alertas: list
    alertas_dict: list[dict]

    # Normativa
    normativa_relevante: list[dict]

    # Informe LLM (opcional)
    informe: Optional[dict] = None

    # Métricas
    tiempo_total_ms: int = 0
    tiempo_gis_ms: int = 0
    tiempo_rag_ms: int = 0
    tiempo_llm_ms: int = 0
    tokens_usados: int = 0

    @property
    def alertas_criticas(self) -> int:
        """Cuenta alertas críticas."""
        return sum(1 for a in self.alertas_dict if a.get("nivel") == "CRITICA")

    @property
    def alertas_altas(self) -> int:
        """Cuenta alertas altas."""
        return sum(1 for a in self.alertas_dict if a.get("nivel") == "ALTA")


class ServicioPrefactibilidad:
    """
    Servicio que encapsula la lógica de análisis de prefactibilidad.

    Unifica la lógica de `analizar_prefactibilidad` y `analisis_rapido`
    en un solo método parametrizable.
    """

    def __init__(
        self,
        buscador: Optional[BuscadorLegal] = None,
        motor_reglas: Optional[MotorReglasSSEIA] = None,
        sistema_alertas: Optional[SistemaAlertas] = None,
        generador: Optional[GeneradorInformes] = None,
    ):
        """
        Inicializa el servicio con sus dependencias.

        Args:
            buscador: Buscador de normativa legal (RAG)
            motor_reglas: Motor de reglas SEIA
            sistema_alertas: Sistema de alertas
            generador: Generador de informes LLM
        """
        self.buscador = buscador or BuscadorLegal()
        self.motor_reglas = motor_reglas or MotorReglasSSEIA()
        self.sistema_alertas = sistema_alertas or SistemaAlertas()
        self.generador = generador or GeneradorInformes()

    async def ejecutar_analisis(
        self,
        db: AsyncSession,
        geojson: dict,
        datos_proyecto: dict,
        generar_informe: bool = True,
        secciones: Optional[list[str]] = None,
    ) -> ResultadoAnalisis:
        """
        Ejecuta un análisis completo de prefactibilidad.

        Args:
            db: Sesión de base de datos
            geojson: Geometría del proyecto en formato GeoJSON
            datos_proyecto: Diccionario con datos del proyecto
            generar_informe: Si True, genera informe con LLM
            secciones: Secciones específicas a generar (opcional)

        Returns:
            ResultadoAnalisis con todos los datos del análisis
        """
        inicio = time.time()
        logger.info(f"Iniciando análisis de prefactibilidad: {datos_proyecto.get('nombre')}")

        # 1. Ejecutar análisis espacial GIS
        logger.info("Ejecutando análisis GIS...")
        inicio_gis = time.time()
        resultado_gis = await analizar_proyecto_espacial(db, geojson)
        tiempo_gis = int((time.time() - inicio_gis) * 1000)

        # 2. Ejecutar motor de reglas SEIA
        logger.info("Ejecutando motor de reglas SEIA...")
        clasificacion = self.motor_reglas.clasificar_proyecto(resultado_gis, datos_proyecto)

        # 3. Generar alertas
        logger.info("Generando alertas...")
        alertas = self.sistema_alertas.generar_alertas(resultado_gis, datos_proyecto)
        alertas_dict = [a.to_dict() for a in alertas]

        # 4. Buscar normativa relevante
        logger.info("Buscando normativa relevante...")
        inicio_rag = time.time()
        normativa_relevante = await self._buscar_normativa_contextual(
            db, clasificacion, alertas
        )
        tiempo_rag = int((time.time() - inicio_rag) * 1000)

        # 5. Generar informe con LLM (si se solicita)
        informe_dict = None
        tiempo_llm = 0
        tokens_usados = 0

        if generar_informe:
            logger.info("Generando informe con LLM...")
            inicio_llm = time.time()

            # Mapear secciones si se especificaron
            secciones_a_generar = None
            if secciones:
                secciones_a_generar = [SeccionInforme(s) for s in secciones]

            try:
                informe = await self.generador.generar_informe(
                    datos_proyecto=datos_proyecto,
                    resultado_gis=resultado_gis,
                    normativa_relevante=normativa_relevante,
                    secciones_a_generar=secciones_a_generar,
                )
                informe_dict = {
                    "secciones": [
                        {
                            "seccion": s.seccion.value,
                            "titulo": s.titulo,
                            "contenido": s.contenido,
                        }
                        for s in informe.secciones
                    ],
                    "texto_completo": informe.to_texto_plano(),
                }
                # Estimar tokens (aproximado)
                tokens_usados = len(informe.to_texto_plano()) // 4
            except Exception as e:
                logger.error(f"Error generando informe LLM: {e}")
                informe_dict = {"error": str(e)}

            tiempo_llm = int((time.time() - inicio_llm) * 1000)

        tiempo_total = int((time.time() - inicio) * 1000)

        return ResultadoAnalisis(
            id=str(uuid.uuid4())[:8].upper(),
            fecha_analisis=datetime.now().isoformat(),
            datos_proyecto=datos_proyecto,
            resultado_gis=resultado_gis,
            clasificacion=clasificacion,
            alertas=alertas,
            alertas_dict=alertas_dict,
            normativa_relevante=normativa_relevante,
            informe=informe_dict,
            tiempo_total_ms=tiempo_total,
            tiempo_gis_ms=tiempo_gis,
            tiempo_rag_ms=tiempo_rag,
            tiempo_llm_ms=tiempo_llm,
            tokens_usados=tokens_usados,
        )

    async def _buscar_normativa_contextual(
        self,
        db: AsyncSession,
        clasificacion: ClasificacionSEIA,
        alertas: list,
    ) -> list[dict]:
        """
        Busca normativa relevante basada en el contexto del análisis.

        Args:
            db: Sesión de base de datos
            clasificacion: Resultado de clasificación SEIA
            alertas: Lista de alertas generadas

        Returns:
            Lista de diccionarios con normativa relevante
        """
        try:
            normativa = []

            # Buscar por triggers detectados
            for trigger in clasificacion.triggers[:3]:
                query = f"Art. 11 letra {trigger.letra.value} {trigger.descripcion}"
                resultados = await self.buscador.buscar(db, query, limite=3)
                for r in resultados:
                    normativa.append({
                        "contenido": r.contenido,
                        "documento": r.documento_titulo,
                        "seccion": r.seccion,
                        "relevancia": f"Trigger {trigger.letra.value}",
                    })

            # Buscar por componentes ambientales afectados
            componentes_query = set()
            for alerta in alertas[:5]:
                for comp in alerta.componentes_afectados:
                    componentes_query.add(comp.value.replace("_", " "))

            for comp in list(componentes_query)[:3]:
                resultados = await self.buscador.buscar(db, f"normativa {comp}", limite=2)
                for r in resultados:
                    normativa.append({
                        "contenido": r.contenido,
                        "documento": r.documento_titulo,
                        "seccion": r.seccion,
                        "relevancia": f"Componente: {comp}",
                    })

            return normativa
        except Exception as e:
            logger.warning(f"RAG no disponible, omitiendo búsqueda de normativa: {e}")
            return []
