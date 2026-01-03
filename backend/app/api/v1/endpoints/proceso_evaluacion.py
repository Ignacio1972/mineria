"""
Endpoints de Proceso de Evaluacion SEIA (Gestor ICSARA/Adendas).

Permite gestionar el ciclo de vida de evaluacion ambiental:
- Ingreso y admisibilidad
- ICSARA y observaciones
- Adendas y respuestas
- RCA final
"""
import logging
from typing import List, Optional
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.proceso_evaluacion.service import ProcesoEvaluacionService
from app.schemas.proceso_evaluacion import (
    ProcesoEvaluacionCreate,
    ProcesoEvaluacionResponse,
    ResumenProcesoEvaluacion,
    PlazoEvaluacion,
    TimelineEvaluacion,
    ICSARACreate,
    ICSARAResponse,
    AdendaCreate,
    AdendaResponse,
    RegistrarRCA,
    RegistrarAdmisibilidad,
    ActualizarEstadoObservacion,
    EstadisticasICSARA,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# Dependencias
# =============================================================================

def get_servicio(db: AsyncSession = Depends(get_db)) -> ProcesoEvaluacionService:
    """Obtiene instancia del servicio de proceso evaluacion."""
    return ProcesoEvaluacionService(db)


# =============================================================================
# Endpoints de Proceso de Evaluacion
# =============================================================================

@router.post(
    "/{proyecto_id}/iniciar",
    response_model=ProcesoEvaluacionResponse,
    summary="Iniciar proceso de evaluacion SEIA",
    description="""
    Inicia el proceso de evaluacion ambiental para un proyecto.

    Registra:
    - Fecha de ingreso al SEIA
    - Plazo legal de evaluacion (120 dias para EIA, 60 para DIA)
    - Estado inicial como "ingresado"
    """,
)
async def iniciar_proceso(
    proyecto_id: int = Path(..., description="ID del proyecto"),
    fecha_ingreso: date = Query(..., description="Fecha de ingreso al SEIA"),
    instrumento: str = Query(..., regex="^(EIA|DIA)$", description="Tipo de instrumento"),
    servicio: ProcesoEvaluacionService = Depends(get_servicio),
) -> ProcesoEvaluacionResponse:
    """Inicia el proceso de evaluacion para un proyecto."""
    logger.info(f"Iniciando proceso de evaluacion para proyecto {proyecto_id}")

    plazo = 120 if instrumento == "EIA" else 60

    try:
        proceso = await servicio.iniciar_proceso(
            proyecto_id=proyecto_id,
            fecha_ingreso=fecha_ingreso,
            plazo_legal_dias=plazo,
        )
        return ProcesoEvaluacionResponse.model_validate(proceso.to_dict())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/{proyecto_id}",
    response_model=ProcesoEvaluacionResponse,
    summary="Obtener proceso de evaluacion",
    description="Retorna el proceso de evaluacion completo de un proyecto.",
)
async def obtener_proceso(
    proyecto_id: int = Path(..., description="ID del proyecto"),
    servicio: ProcesoEvaluacionService = Depends(get_servicio),
) -> ProcesoEvaluacionResponse:
    """Obtiene el proceso de evaluacion de un proyecto."""
    proceso = await servicio.get_proceso_by_proyecto(proyecto_id)

    if not proceso:
        raise HTTPException(
            status_code=404,
            detail=f"No existe proceso de evaluacion para el proyecto {proyecto_id}"
        )

    return ProcesoEvaluacionResponse.model_validate(proceso.to_dict())


@router.get(
    "/{proyecto_id}/resumen",
    response_model=ResumenProcesoEvaluacion,
    summary="Obtener resumen del proceso",
    description="Retorna un resumen del proceso con proxima accion y alertas.",
)
async def obtener_resumen(
    proyecto_id: int = Path(..., description="ID del proyecto"),
    servicio: ProcesoEvaluacionService = Depends(get_servicio),
) -> ResumenProcesoEvaluacion:
    """Obtiene resumen del proceso de evaluacion."""
    resumen = await servicio.get_resumen_proceso(proyecto_id)

    if not resumen:
        raise HTTPException(
            status_code=404,
            detail=f"No existe proceso de evaluacion para el proyecto {proyecto_id}"
        )

    return resumen


@router.get(
    "/{proyecto_id}/plazos",
    response_model=PlazoEvaluacion,
    summary="Obtener informacion de plazos",
    description="Retorna informacion detallada de plazos del proceso.",
)
async def obtener_plazos(
    proyecto_id: int = Path(..., description="ID del proyecto"),
    servicio: ProcesoEvaluacionService = Depends(get_servicio),
) -> PlazoEvaluacion:
    """Obtiene informacion de plazos del proceso."""
    proceso = await servicio.get_proceso_by_proyecto(proyecto_id)

    if not proceso:
        raise HTTPException(
            status_code=404,
            detail=f"No existe proceso de evaluacion para el proyecto {proyecto_id}"
        )

    return await servicio.calcular_plazo_restante(proceso.id)


@router.get(
    "/{proyecto_id}/timeline",
    response_model=TimelineEvaluacion,
    summary="Obtener timeline de evaluacion",
    description="Retorna el timeline de estados del proceso.",
)
async def obtener_timeline(
    proyecto_id: int = Path(..., description="ID del proyecto"),
    servicio: ProcesoEvaluacionService = Depends(get_servicio),
) -> TimelineEvaluacion:
    """Obtiene timeline del proceso de evaluacion."""
    return await servicio.get_timeline_evaluacion(proyecto_id)


@router.post(
    "/{proyecto_id}/admisibilidad",
    response_model=ProcesoEvaluacionResponse,
    summary="Registrar admisibilidad",
    description="Registra el resultado de admisibilidad (5 dias habiles).",
)
async def registrar_admisibilidad(
    proyecto_id: int = Path(..., description="ID del proyecto"),
    datos: RegistrarAdmisibilidad = ...,
    servicio: ProcesoEvaluacionService = Depends(get_servicio),
) -> ProcesoEvaluacionResponse:
    """Registra resultado de admisibilidad."""
    proceso = await servicio.get_proceso_by_proyecto(proyecto_id)

    if not proceso:
        raise HTTPException(
            status_code=404,
            detail=f"No existe proceso de evaluacion para el proyecto {proyecto_id}"
        )

    try:
        proceso = await servicio.registrar_admisibilidad(
            proceso_id=proceso.id,
            resultado=datos.resultado,
            fecha=datos.fecha,
            observaciones=datos.observaciones,
        )
        return ProcesoEvaluacionResponse.model_validate(proceso.to_dict())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# Endpoints de ICSARA
# =============================================================================

@router.post(
    "/{proyecto_id}/icsara",
    response_model=ICSARAResponse,
    summary="Registrar ICSARA",
    description="""
    Registra un nuevo ICSARA con sus observaciones.

    El ICSARA contiene las observaciones de los OAECA
    (Organismos con Competencia Ambiental).
    """,
)
async def registrar_icsara(
    proyecto_id: int = Path(..., description="ID del proyecto"),
    datos: ICSARACreate = ...,
    servicio: ProcesoEvaluacionService = Depends(get_servicio),
) -> ICSARAResponse:
    """Registra un nuevo ICSARA."""
    proceso = await servicio.get_proceso_by_proyecto(proyecto_id)

    if not proceso:
        raise HTTPException(
            status_code=404,
            detail=f"No existe proceso de evaluacion para el proyecto {proyecto_id}"
        )

    try:
        # Convertir observaciones a diccionarios
        observaciones = [obs.model_dump() for obs in datos.observaciones] if datos.observaciones else []

        icsara = await servicio.registrar_icsara(
            proceso_id=proceso.id,
            numero=datos.numero_icsara,
            fecha_emision=datos.fecha_emision,
            fecha_limite_respuesta=datos.fecha_limite_respuesta,
            observaciones=observaciones,
        )
        return ICSARAResponse.model_validate(icsara.to_dict())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/{proyecto_id}/icsara/{numero}",
    response_model=ICSARAResponse,
    summary="Obtener ICSARA",
    description="Retorna un ICSARA especifico por numero.",
)
async def obtener_icsara(
    proyecto_id: int = Path(..., description="ID del proyecto"),
    numero: int = Path(..., description="Numero de ICSARA"),
    servicio: ProcesoEvaluacionService = Depends(get_servicio),
) -> ICSARAResponse:
    """Obtiene un ICSARA especifico."""
    proceso = await servicio.get_proceso_by_proyecto(proyecto_id)

    if not proceso:
        raise HTTPException(
            status_code=404,
            detail=f"No existe proceso de evaluacion para el proyecto {proyecto_id}"
        )

    # Buscar ICSARA por numero
    icsara = None
    for i in (proceso.icsaras or []):
        if i.numero_icsara == numero:
            icsara = i
            break

    if not icsara:
        raise HTTPException(
            status_code=404,
            detail=f"No existe ICSARA #{numero} para el proyecto {proyecto_id}"
        )

    return ICSARAResponse.model_validate(icsara.to_dict())


@router.get(
    "/{proyecto_id}/estadisticas-icsara",
    response_model=EstadisticasICSARA,
    summary="Obtener estadisticas de ICSARA",
    description="Retorna estadisticas de observaciones por tipo, prioridad, organismo, etc.",
)
async def obtener_estadisticas_icsara(
    proyecto_id: int = Path(..., description="ID del proyecto"),
    servicio: ProcesoEvaluacionService = Depends(get_servicio),
) -> EstadisticasICSARA:
    """Obtiene estadisticas de observaciones ICSARA."""
    stats = await servicio.get_estadisticas_icsara(proyecto_id)

    if not stats:
        raise HTTPException(
            status_code=404,
            detail=f"No hay observaciones ICSARA para el proyecto {proyecto_id}"
        )

    return stats


@router.put(
    "/{proyecto_id}/icsara/{icsara_id}/observacion/{observacion_id}",
    response_model=ICSARAResponse,
    summary="Actualizar estado de observacion",
    description="Actualiza el estado de una observacion especifica.",
)
async def actualizar_estado_observacion(
    proyecto_id: int = Path(..., description="ID del proyecto"),
    icsara_id: int = Path(..., description="ID del ICSARA"),
    observacion_id: str = Path(..., description="ID de la observacion"),
    datos: ActualizarEstadoObservacion = ...,
    servicio: ProcesoEvaluacionService = Depends(get_servicio),
) -> ICSARAResponse:
    """Actualiza el estado de una observacion."""
    try:
        icsara = await servicio.actualizar_estado_observacion(
            icsara_id=icsara_id,
            observacion_id=observacion_id,
            nuevo_estado=datos.estado.value,
        )
        return ICSARAResponse.model_validate(icsara.to_dict())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# Endpoints de Adenda
# =============================================================================

@router.post(
    "/{proyecto_id}/icsara/{icsara_id}/adenda",
    response_model=AdendaResponse,
    summary="Registrar Adenda",
    description="""
    Registra una Adenda como respuesta a un ICSARA.

    La Adenda contiene las respuestas del titular a las
    observaciones de los organismos.
    """,
)
async def registrar_adenda(
    proyecto_id: int = Path(..., description="ID del proyecto"),
    icsara_id: int = Path(..., description="ID del ICSARA"),
    datos: AdendaCreate = ...,
    servicio: ProcesoEvaluacionService = Depends(get_servicio),
) -> AdendaResponse:
    """Registra una nueva Adenda."""
    try:
        # Convertir respuestas a diccionarios
        respuestas = [resp.model_dump() for resp in datos.respuestas] if datos.respuestas else []

        adenda = await servicio.registrar_adenda(
            icsara_id=icsara_id,
            numero=datos.numero_adenda,
            fecha_presentacion=datos.fecha_presentacion,
            respuestas=respuestas,
        )
        return AdendaResponse.model_validate(adenda.to_dict())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/{proyecto_id}/icsara/{icsara_id}/adenda/{numero}",
    response_model=AdendaResponse,
    summary="Obtener Adenda",
    description="Retorna una Adenda especifica.",
)
async def obtener_adenda(
    proyecto_id: int = Path(..., description="ID del proyecto"),
    icsara_id: int = Path(..., description="ID del ICSARA"),
    numero: int = Path(..., description="Numero de Adenda"),
    servicio: ProcesoEvaluacionService = Depends(get_servicio),
) -> AdendaResponse:
    """Obtiene una Adenda especifica."""
    icsara = await servicio.get_icsara(icsara_id)

    if not icsara:
        raise HTTPException(
            status_code=404,
            detail=f"No existe ICSARA con ID {icsara_id}"
        )

    # Buscar Adenda por numero
    adenda = None
    for a in (icsara.adendas or []):
        if a.numero_adenda == numero:
            adenda = a
            break

    if not adenda:
        raise HTTPException(
            status_code=404,
            detail=f"No existe Adenda #{numero} para ICSARA {icsara_id}"
        )

    return AdendaResponse.model_validate(adenda.to_dict())


# =============================================================================
# Endpoints de RCA
# =============================================================================

@router.post(
    "/{proyecto_id}/rca",
    response_model=ProcesoEvaluacionResponse,
    summary="Registrar RCA",
    description="""
    Registra la Resolucion de Calificacion Ambiental (RCA) final.

    Resultados posibles:
    - favorable: Proyecto aprobado
    - favorable_con_condiciones: Aprobado con condiciones
    - desfavorable: Proyecto rechazado
    """,
)
async def registrar_rca(
    proyecto_id: int = Path(..., description="ID del proyecto"),
    datos: RegistrarRCA = ...,
    servicio: ProcesoEvaluacionService = Depends(get_servicio),
) -> ProcesoEvaluacionResponse:
    """Registra la RCA final."""
    proceso = await servicio.get_proceso_by_proyecto(proyecto_id)

    if not proceso:
        raise HTTPException(
            status_code=404,
            detail=f"No existe proceso de evaluacion para el proyecto {proyecto_id}"
        )

    try:
        # Convertir condiciones a diccionarios si existen
        condiciones = [c.model_dump() for c in datos.condiciones] if datos.condiciones else None

        proceso = await servicio.registrar_rca(
            proceso_id=proceso.id,
            resultado=datos.resultado.value,
            numero_rca=datos.numero_rca,
            fecha=datos.fecha,
            condiciones=condiciones,
            url=datos.url,
        )
        return ProcesoEvaluacionResponse.model_validate(proceso.to_dict())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
