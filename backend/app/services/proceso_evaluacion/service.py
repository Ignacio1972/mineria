"""
Servicio de Proceso de Evaluación SEIA.

Gestiona el ciclo de vida de evaluación ambiental:
- Ingreso y admisibilidad
- ICSARA y observaciones
- Adendas y respuestas
- RCA final

Según D.S. 40/2012 y Ley 19.300.
"""
import logging
from datetime import date, timedelta
from typing import Optional, List, Dict, Any, Literal

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.proceso_evaluacion import (
    ProcesoEvaluacion,
    ICSARA,
    Adenda,
    EstadoEvaluacion,
    EstadoICSARA,
    EstadoAdenda,
    EstadoObservacionICSARA,
    OAECAS_MINERIA,
    ESTADOS_TIMELINE,
)
from app.db.models.proyecto import Proyecto
from app.schemas.proceso_evaluacion import (
    ProcesoEvaluacionCreate,
    ICSARACreate,
    AdendaCreate,
    RegistrarRCA,
    RegistrarAdmisibilidad,
    ActualizarEstadoObservacion,
    ObservacionICSARA,
    RespuestaAdenda,
    ResumenProcesoEvaluacion,
    PlazoEvaluacion,
    TimelineEvaluacion,
    EstadoTimeline,
    EstadisticasICSARA,
)

logger = logging.getLogger(__name__)


class ProcesoEvaluacionService:
    """Gestiona el ciclo de vida de evaluación SEIA."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # PROCESO DE EVALUACIÓN
    # =========================================================================

    async def iniciar_proceso(
        self,
        proyecto_id: int,
        fecha_ingreso: date,
        plazo_legal_dias: int = 120
    ) -> ProcesoEvaluacion:
        """
        Inicia el proceso de evaluación para un proyecto.

        Args:
            proyecto_id: ID del proyecto
            fecha_ingreso: Fecha de ingreso al SEIA
            plazo_legal_dias: 120 para EIA, 60 para DIA

        Returns:
            ProcesoEvaluacion creado
        """
        # Verificar que el proyecto existe
        proyecto = await self.db.get(Proyecto, proyecto_id)
        if not proyecto:
            raise ValueError(f"Proyecto {proyecto_id} no encontrado")

        # Verificar si ya existe proceso
        existente = await self.get_proceso_by_proyecto(proyecto_id)
        if existente:
            raise ValueError(f"El proyecto {proyecto_id} ya tiene un proceso de evaluación")

        # Crear proceso
        proceso = ProcesoEvaluacion(
            proyecto_id=proyecto_id,
            estado_evaluacion=EstadoEvaluacion.INGRESADO.value,
            fecha_ingreso=fecha_ingreso,
            plazo_legal_dias=plazo_legal_dias,
            dias_transcurridos=0,
            dias_suspension=0,
        )

        self.db.add(proceso)
        await self.db.commit()

        # Recargar con relaciones para evitar lazy loading
        proceso = await self.get_proceso(proceso.id, cargar_icsaras=True)

        logger.info(f"Proceso de evaluación iniciado para proyecto {proyecto_id}")
        return proceso

    async def get_proceso_by_proyecto(
        self,
        proyecto_id: int,
        cargar_icsaras: bool = True
    ) -> Optional[ProcesoEvaluacion]:
        """Obtiene el proceso de evaluación de un proyecto."""
        query = select(ProcesoEvaluacion).where(
            ProcesoEvaluacion.proyecto_id == proyecto_id
        )

        if cargar_icsaras:
            query = query.options(
                selectinload(ProcesoEvaluacion.icsaras).selectinload(ICSARA.adendas)
            )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_proceso(
        self,
        proceso_id: int,
        cargar_icsaras: bool = True
    ) -> Optional[ProcesoEvaluacion]:
        """Obtiene un proceso de evaluación por ID."""
        query = select(ProcesoEvaluacion).where(
            ProcesoEvaluacion.id == proceso_id
        )

        if cargar_icsaras:
            query = query.options(
                selectinload(ProcesoEvaluacion.icsaras).selectinload(ICSARA.adendas)
            )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def registrar_admisibilidad(
        self,
        proceso_id: int,
        resultado: Literal["admitido", "inadmitido"],
        fecha: date,
        observaciones: Optional[str] = None
    ) -> ProcesoEvaluacion:
        """
        Registra el resultado de admisibilidad (5 días hábiles).

        Args:
            proceso_id: ID del proceso
            resultado: "admitido" o "inadmitido"
            fecha: Fecha del pronunciamiento
            observaciones: Observaciones si es inadmitido
        """
        proceso = await self.get_proceso(proceso_id)
        if not proceso:
            raise ValueError(f"Proceso {proceso_id} no encontrado")

        proceso.fecha_admisibilidad = fecha

        if resultado == "admitido":
            proceso.estado_evaluacion = EstadoEvaluacion.ADMITIDO.value
            # Pasar directamente a evaluación
            proceso.estado_evaluacion = EstadoEvaluacion.EN_EVALUACION.value
        else:
            proceso.estado_evaluacion = EstadoEvaluacion.INADMITIDO.value

        await self.db.commit()
        await self.db.refresh(proceso)

        logger.info(f"Admisibilidad registrada para proceso {proceso_id}: {resultado}")
        return proceso

    async def actualizar_dias_transcurridos(
        self,
        proceso_id: int
    ) -> ProcesoEvaluacion:
        """Actualiza los días transcurridos desde el ingreso."""
        proceso = await self.get_proceso(proceso_id)
        if not proceso or not proceso.fecha_ingreso:
            raise ValueError(f"Proceso {proceso_id} no válido")

        dias = (date.today() - proceso.fecha_ingreso).days
        proceso.dias_transcurridos = max(0, dias)

        await self.db.commit()
        await self.db.refresh(proceso)
        return proceso

    async def actualizar_estado(
        self,
        proceso_id: int,
        nuevo_estado: EstadoEvaluacion
    ) -> ProcesoEvaluacion:
        """Actualiza el estado del proceso de evaluación."""
        proceso = await self.get_proceso(proceso_id)
        if not proceso:
            raise ValueError(f"Proceso {proceso_id} no encontrado")

        proceso.estado_evaluacion = nuevo_estado.value

        await self.db.commit()
        await self.db.refresh(proceso)

        logger.info(f"Estado de proceso {proceso_id} actualizado a: {nuevo_estado.value}")
        return proceso

    # =========================================================================
    # ICSARA
    # =========================================================================

    async def registrar_icsara(
        self,
        proceso_id: int,
        numero: int,
        fecha_emision: date,
        fecha_limite_respuesta: date,
        observaciones: Optional[List[Dict[str, Any]]] = None
    ) -> ICSARA:
        """
        Registra un nuevo ICSARA con sus observaciones.

        Args:
            proceso_id: ID del proceso de evaluación
            numero: Número de ICSARA (1, 2, o excepcionalmente 3)
            fecha_emision: Fecha de emisión
            fecha_limite_respuesta: Fecha límite para responder
            observaciones: Lista de observaciones

        Returns:
            ICSARA creado
        """
        proceso = await self.get_proceso(proceso_id)
        if not proceso:
            raise ValueError(f"Proceso {proceso_id} no encontrado")

        # Validar número de ICSARA
        if numero > 3:
            raise ValueError("El número máximo de ICSARA es 3 (excepcionalmente)")

        icsaras_existentes = len(proceso.icsaras or [])
        if numero != icsaras_existentes + 1:
            raise ValueError(f"El siguiente ICSARA debe ser el número {icsaras_existentes + 1}")

        # Procesar observaciones
        obs_procesadas = []
        conteo_oaeca: Dict[str, int] = {}

        for i, obs in enumerate(observaciones or []):
            # Asignar ID si no tiene
            if "id" not in obs:
                obs["id"] = f"OBS-{i+1:03d}"
            if "estado" not in obs:
                obs["estado"] = EstadoObservacionICSARA.PENDIENTE.value

            obs_procesadas.append(obs)

            # Contar por OAECA
            oaeca = obs.get("oaeca", "Sin organismo")
            conteo_oaeca[oaeca] = conteo_oaeca.get(oaeca, 0) + 1

        # Crear ICSARA
        icsara = ICSARA(
            proceso_evaluacion_id=proceso_id,
            numero_icsara=numero,
            fecha_emision=fecha_emision,
            fecha_limite_respuesta=fecha_limite_respuesta,
            observaciones=obs_procesadas,
            total_observaciones=len(obs_procesadas),
            observaciones_por_oaeca=conteo_oaeca,
            estado=EstadoICSARA.EMITIDO.value,
        )

        self.db.add(icsara)

        # Actualizar estado del proceso
        proceso.estado_evaluacion = EstadoEvaluacion.ICSARA_EMITIDO.value

        await self.db.commit()
        await self.db.refresh(icsara)

        logger.info(f"ICSARA #{numero} registrado para proceso {proceso_id} con {len(obs_procesadas)} observaciones")
        return icsara

    async def get_icsara(self, icsara_id: int) -> Optional[ICSARA]:
        """Obtiene un ICSARA por ID."""
        query = select(ICSARA).where(ICSARA.id == icsara_id).options(
            selectinload(ICSARA.adendas)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def agregar_observacion(
        self,
        icsara_id: int,
        observacion: Dict[str, Any]
    ) -> ICSARA:
        """Agrega una observación a un ICSARA existente."""
        icsara = await self.get_icsara(icsara_id)
        if not icsara:
            raise ValueError(f"ICSARA {icsara_id} no encontrado")

        icsara.agregar_observacion(observacion)

        await self.db.commit()
        await self.db.refresh(icsara)
        return icsara

    async def actualizar_estado_observacion(
        self,
        icsara_id: int,
        observacion_id: str,
        nuevo_estado: str
    ) -> ICSARA:
        """Actualiza el estado de una observación específica."""
        icsara = await self.get_icsara(icsara_id)
        if not icsara:
            raise ValueError(f"ICSARA {icsara_id} no encontrado")

        if not icsara.actualizar_estado_observacion(observacion_id, nuevo_estado):
            raise ValueError(f"Observación {observacion_id} no encontrada en ICSARA {icsara_id}")

        await self.db.commit()
        await self.db.refresh(icsara)
        return icsara

    # =========================================================================
    # ADENDAS
    # =========================================================================

    async def registrar_adenda(
        self,
        icsara_id: int,
        numero: int,
        fecha_presentacion: date,
        respuestas: Optional[List[Dict[str, Any]]] = None
    ) -> Adenda:
        """
        Registra una nueva Adenda como respuesta a un ICSARA.

        Args:
            icsara_id: ID del ICSARA que responde
            numero: Número de Adenda
            fecha_presentacion: Fecha de presentación
            respuestas: Lista de respuestas a observaciones

        Returns:
            Adenda creada
        """
        icsara = await self.get_icsara(icsara_id)
        if not icsara:
            raise ValueError(f"ICSARA {icsara_id} no encontrado")

        # Procesar respuestas y contar
        resueltas = 0
        pendientes = 0

        for resp in (respuestas or []):
            estado = resp.get("estado", "")
            if estado == "respondida":
                resueltas += 1
            else:
                pendientes += 1

        # Crear Adenda
        adenda = Adenda(
            icsara_id=icsara_id,
            numero_adenda=numero,
            fecha_presentacion=fecha_presentacion,
            respuestas=respuestas or [],
            total_respuestas=len(respuestas or []),
            observaciones_resueltas=resueltas,
            observaciones_pendientes=pendientes,
            estado=EstadoAdenda.PRESENTADA.value,
        )

        self.db.add(adenda)

        # Actualizar estado del ICSARA
        if pendientes == 0 and resueltas > 0:
            icsara.estado = EstadoICSARA.RESPONDIDO.value
        elif resueltas > 0:
            icsara.estado = EstadoICSARA.PARCIALMENTE_RESPONDIDO.value

        # Actualizar estado del proceso
        proceso = await self.get_proceso(icsara.proceso_evaluacion_id)
        if proceso:
            proceso.estado_evaluacion = EstadoEvaluacion.ADENDA_EN_REVISION.value

            # Calcular días de suspensión (desde ICSARA hasta Adenda)
            if icsara.fecha_emision:
                dias_suspension = (fecha_presentacion - icsara.fecha_emision).days
                proceso.dias_suspension += dias_suspension

        await self.db.commit()
        await self.db.refresh(adenda)

        logger.info(f"Adenda #{numero} registrada para ICSARA {icsara_id}")
        return adenda

    async def get_adenda(self, adenda_id: int) -> Optional[Adenda]:
        """Obtiene una Adenda por ID."""
        return await self.db.get(Adenda, adenda_id)

    async def actualizar_respuesta_adenda(
        self,
        adenda_id: int,
        observacion_id: str,
        estado: str,
        calificacion: Optional[str] = None
    ) -> Adenda:
        """Actualiza una respuesta específica en la Adenda."""
        adenda = await self.get_adenda(adenda_id)
        if not adenda:
            raise ValueError(f"Adenda {adenda_id} no encontrada")

        if not adenda.actualizar_respuesta(observacion_id, estado, calificacion):
            raise ValueError(f"Respuesta para observación {observacion_id} no encontrada")

        await self.db.commit()
        await self.db.refresh(adenda)
        return adenda

    # =========================================================================
    # RCA
    # =========================================================================

    async def registrar_rca(
        self,
        proceso_id: int,
        resultado: str,
        numero_rca: str,
        fecha: date,
        condiciones: Optional[List[Dict[str, Any]]] = None,
        url: Optional[str] = None
    ) -> ProcesoEvaluacion:
        """
        Registra la Resolución de Calificación Ambiental (RCA).

        Args:
            proceso_id: ID del proceso
            resultado: favorable, favorable_con_condiciones, desfavorable
            numero_rca: Número de la RCA
            fecha: Fecha de la RCA
            condiciones: Condiciones (si aplica)
            url: URL del documento

        Returns:
            ProcesoEvaluacion actualizado
        """
        proceso = await self.get_proceso(proceso_id)
        if not proceso:
            raise ValueError(f"Proceso {proceso_id} no encontrado")

        proceso.fecha_rca = fecha
        proceso.resultado_rca = resultado
        proceso.numero_rca = numero_rca
        proceso.url_rca = url
        proceso.condiciones_rca = condiciones

        # Actualizar estado según resultado
        if resultado in ["favorable", "favorable_con_condiciones"]:
            proceso.estado_evaluacion = EstadoEvaluacion.RCA_APROBADA.value
        else:
            proceso.estado_evaluacion = EstadoEvaluacion.RCA_RECHAZADA.value

        await self.db.commit()
        await self.db.refresh(proceso)

        logger.info(f"RCA registrada para proceso {proceso_id}: {resultado}")
        return proceso

    # =========================================================================
    # CONSULTAS Y RESÚMENES
    # =========================================================================

    async def get_resumen_proceso(
        self,
        proyecto_id: int
    ) -> Optional[ResumenProcesoEvaluacion]:
        """Obtiene resumen del proceso de evaluación."""
        proceso = await self.get_proceso_by_proyecto(proyecto_id)
        if not proceso:
            return None

        # Obtener nombre del proyecto
        proyecto = await self.db.get(Proyecto, proyecto_id)
        proyecto_nombre = proyecto.nombre if proyecto else None

        # Calcular estadísticas
        obs_por_oaeca = proceso.get_observaciones_por_oaeca()
        oaeca_criticos = sorted(
            obs_por_oaeca.items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]

        # Determinar próxima acción
        proxima_accion, fecha_limite, alerta = self._determinar_proxima_accion(proceso)

        # Contar adendas
        total_adendas = sum(len(i.adendas or []) for i in (proceso.icsaras or []))
        ultima_adenda_fecha = None
        for icsara in (proceso.icsaras or []):
            for adenda in (icsara.adendas or []):
                if not ultima_adenda_fecha or (adenda.fecha_presentacion and adenda.fecha_presentacion > ultima_adenda_fecha):
                    ultima_adenda_fecha = adenda.fecha_presentacion

        # Obtener label del estado
        estado_label = self._get_estado_label(proceso.estado_evaluacion)

        return ResumenProcesoEvaluacion(
            proyecto_id=proyecto_id,
            proyecto_nombre=proyecto_nombre,
            estado_actual=proceso.estado_evaluacion,
            estado_label=estado_label,
            fecha_ingreso=proceso.fecha_ingreso,
            dias_transcurridos=proceso.dias_transcurridos,
            dias_restantes=proceso.dias_restantes,
            porcentaje_plazo=proceso.porcentaje_plazo,
            total_icsara=proceso.total_icsara,
            icsara_actual=proceso.icsara_actual.numero_icsara if proceso.icsara_actual else None,
            observaciones_totales=proceso.total_observaciones,
            observaciones_pendientes=proceso.observaciones_pendientes,
            observaciones_resueltas=proceso.total_observaciones - proceso.observaciones_pendientes,
            observaciones_por_oaeca=obs_por_oaeca,
            oaeca_criticos=[o[0] for o in oaeca_criticos],
            total_adendas=total_adendas,
            ultima_adenda_fecha=ultima_adenda_fecha,
            proxima_accion=proxima_accion,
            fecha_limite=fecha_limite,
            alerta=alerta,
        )

    def _determinar_proxima_accion(
        self,
        proceso: ProcesoEvaluacion
    ) -> tuple[str, Optional[date], Optional[str]]:
        """Determina la próxima acción requerida."""
        estado = proceso.estado_evaluacion
        fecha_limite = None
        alerta = None

        if estado == EstadoEvaluacion.NO_INGRESADO.value:
            return "Ingresar proyecto al SEIA", None, None

        if estado == EstadoEvaluacion.INGRESADO.value:
            return "Esperar pronunciamiento de admisibilidad", None, None

        if estado == EstadoEvaluacion.EN_ADMISIBILIDAD.value:
            return "En revisión de admisibilidad (5 días hábiles)", None, None

        if estado == EstadoEvaluacion.EN_EVALUACION.value:
            return "En evaluación por OAECA", None, None

        if estado == EstadoEvaluacion.ICSARA_EMITIDO.value:
            icsara_actual = proceso.icsara_actual
            if icsara_actual:
                fecha_limite = icsara_actual.fecha_limite_respuesta
                dias = icsara_actual.dias_para_responder
                if dias <= 7:
                    alerta = f"Quedan {dias} días para responder ICSARA"
                return f"Responder ICSARA #{icsara_actual.numero_icsara}", fecha_limite, alerta
            return "Responder ICSARA", None, None

        if estado == EstadoEvaluacion.ADENDA_EN_REVISION.value:
            return "Adenda en revisión por SEA", None, None

        if estado == EstadoEvaluacion.ICE_EMITIDO.value:
            return "Esperar votación de Comisión Evaluadora", None, None

        if estado == EstadoEvaluacion.EN_COMISION.value:
            return "En votación regional", None, None

        if estado in [EstadoEvaluacion.RCA_APROBADA.value, EstadoEvaluacion.RCA_RECHAZADA.value]:
            return "Proceso finalizado", None, None

        return "Sin acción definida", None, None

    def _get_estado_label(self, estado: str) -> str:
        """Obtiene el label legible del estado."""
        labels = {
            "no_ingresado": "No ingresado",
            "ingresado": "Ingresado",
            "en_admisibilidad": "En admisibilidad",
            "admitido": "Admitido",
            "inadmitido": "Inadmitido",
            "en_evaluacion": "En evaluación",
            "icsara_emitido": "ICSARA emitido",
            "adenda_en_revision": "Adenda en revisión",
            "ice_emitido": "ICE emitido",
            "en_comision": "En comisión",
            "rca_aprobada": "RCA aprobada",
            "rca_rechazada": "RCA rechazada",
            "desistido": "Desistido",
            "caducado": "Caducado",
        }
        return labels.get(estado, estado)

    async def calcular_plazo_restante(
        self,
        proceso_id: int
    ) -> PlazoEvaluacion:
        """Calcula información detallada de plazos."""
        proceso = await self.get_proceso(proceso_id)
        if not proceso:
            raise ValueError(f"Proceso {proceso_id} no encontrado")

        dias_efectivos = proceso.dias_transcurridos - proceso.dias_suspension
        dias_restantes = max(0, proceso.plazo_legal_dias - dias_efectivos)
        porcentaje = (dias_efectivos / proceso.plazo_legal_dias * 100) if proceso.plazo_legal_dias else 0

        # Determinar estado del plazo
        if dias_restantes == 0:
            estado_plazo = "vencido"
        elif dias_restantes <= 15:
            estado_plazo = "critico"
        elif dias_restantes <= 30:
            estado_plazo = "alerta"
        else:
            estado_plazo = "normal"

        # Calcular fecha límite estimada
        fecha_limite = None
        if proceso.fecha_ingreso:
            fecha_limite = proceso.fecha_ingreso + timedelta(days=proceso.plazo_legal_dias + proceso.dias_suspension)

        return PlazoEvaluacion(
            plazo_legal_dias=proceso.plazo_legal_dias,
            dias_transcurridos=proceso.dias_transcurridos,
            dias_suspension=proceso.dias_suspension,
            dias_efectivos=dias_efectivos,
            dias_restantes=dias_restantes,
            porcentaje_transcurrido=min(100, porcentaje),
            estado_plazo=estado_plazo,
            fecha_limite_estimada=fecha_limite,
        )

    async def get_timeline_evaluacion(
        self,
        proyecto_id: int
    ) -> TimelineEvaluacion:
        """Obtiene el timeline del proceso de evaluación."""
        proceso = await self.get_proceso_by_proyecto(proyecto_id)

        estados: List[EstadoTimeline] = []
        estado_actual = proceso.estado_evaluacion if proceso else EstadoEvaluacion.NO_INGRESADO.value

        for est, nombre, desc in ESTADOS_TIMELINE:
            est_value = est.value

            # Determinar si está completado, actual o pendiente
            if proceso and self._estado_completado(proceso, est_value):
                estado_item = "completado"
            elif est_value == estado_actual:
                estado_item = "actual"
            else:
                estado_item = "pendiente"

            # Obtener fecha si está disponible
            fecha = None
            if proceso:
                fecha = self._get_fecha_estado(proceso, est_value)

            estados.append(EstadoTimeline(
                id=est_value,
                nombre=nombre,
                descripcion=desc,
                estado=estado_item,
                fecha=fecha,
                icono=self._get_icono_estado(est_value),
            ))

        # Calcular progreso
        completados = sum(1 for e in estados if e.estado == "completado")
        progreso = int((completados / len(estados)) * 100) if estados else 0

        return TimelineEvaluacion(
            proyecto_id=proyecto_id,
            estados=estados,
            estado_actual=estado_actual,
            progreso_porcentaje=progreso,
        )

    def _estado_completado(self, proceso: ProcesoEvaluacion, estado: str) -> bool:
        """Verifica si un estado ya fue completado."""
        orden_estados = [e[0].value for e in ESTADOS_TIMELINE]
        estado_actual = proceso.estado_evaluacion

        try:
            idx_actual = orden_estados.index(estado_actual)
            idx_estado = orden_estados.index(estado)
            return idx_estado < idx_actual
        except ValueError:
            return False

    def _get_fecha_estado(self, proceso: ProcesoEvaluacion, estado: str) -> Optional[date]:
        """Obtiene la fecha asociada a un estado."""
        if estado == "ingresado":
            return proceso.fecha_ingreso
        if estado in ["admitido", "inadmitido", "en_admisibilidad"]:
            return proceso.fecha_admisibilidad
        if estado in ["rca_aprobada", "rca_rechazada"]:
            return proceso.fecha_rca
        return None

    def _get_icono_estado(self, estado: str) -> str:
        """Obtiene el icono para un estado."""
        iconos = {
            "no_ingresado": "file-text",
            "ingresado": "upload",
            "en_admisibilidad": "clock",
            "admitido": "check-circle",
            "inadmitido": "x-circle",
            "en_evaluacion": "search",
            "icsara_emitido": "file-warning",
            "adenda_en_revision": "file-check",
            "ice_emitido": "file-text",
            "en_comision": "users",
            "rca_aprobada": "check-circle-2",
            "rca_rechazada": "x-octagon",
        }
        return iconos.get(estado, "circle")

    async def get_estadisticas_icsara(
        self,
        proyecto_id: int
    ) -> Optional[EstadisticasICSARA]:
        """Obtiene estadísticas de observaciones ICSARA."""
        proceso = await self.get_proceso_by_proyecto(proyecto_id)
        if not proceso or not proceso.icsaras:
            return None

        # Agregar todas las observaciones
        todas_obs = []
        for icsara in proceso.icsaras:
            todas_obs.extend(icsara.observaciones or [])

        if not todas_obs:
            return None

        # Contar por tipo
        por_tipo: Dict[str, int] = {}
        por_prioridad: Dict[str, int] = {}
        por_oaeca: Dict[str, int] = {}
        por_capitulo: Dict[int, int] = {}
        por_estado: Dict[str, int] = {}

        for obs in todas_obs:
            tipo = obs.get("tipo", "sin_tipo")
            prioridad = obs.get("prioridad", "sin_prioridad")
            oaeca = obs.get("oaeca", "sin_organismo")
            capitulo = obs.get("capitulo_eia", 0)
            estado = obs.get("estado", "pendiente")

            por_tipo[tipo] = por_tipo.get(tipo, 0) + 1
            por_prioridad[prioridad] = por_prioridad.get(prioridad, 0) + 1
            por_oaeca[oaeca] = por_oaeca.get(oaeca, 0) + 1
            por_capitulo[capitulo] = por_capitulo.get(capitulo, 0) + 1
            por_estado[estado] = por_estado.get(estado, 0) + 1

        # Encontrar máximos
        oaeca_max = max(por_oaeca.items(), key=lambda x: x[1])[0] if por_oaeca else ""
        capitulo_max = max(por_capitulo.items(), key=lambda x: x[1])[0] if por_capitulo else 0

        return EstadisticasICSARA(
            total_observaciones=len(todas_obs),
            por_tipo=por_tipo,
            por_prioridad=por_prioridad,
            por_oaeca=por_oaeca,
            por_capitulo=por_capitulo,
            por_estado=por_estado,
            oaeca_mas_observaciones=oaeca_max,
            capitulo_mas_observaciones=capitulo_max,
        )
