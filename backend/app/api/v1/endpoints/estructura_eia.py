"""
Endpoints de Estructura EIA (Fase 2).

Permite generar y gestionar la estructura del EIA para proyectos
que requieren Estudio de Impacto Ambiental.
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.estructura_eia.service import (
    EstructuraEIAService,
    get_estructura_eia_service,
)
from app.schemas.estructura_eia import (
    EstructuraEIAResponse,
    EstructuraEIAResumen,
    CapituloConEstado,
    CapituloEIAResponse,
    PASConEstado,
    AnexoRequerido,
    ComponenteLineaBaseResponse,
    ComponenteLineaBaseEnPlan,
    EstimacionComplejidad,
    ActualizarCapituloRequest,
    ActualizarPASRequest,
    ActualizarAnexoRequest,
    ResumenEstructuraParaAsistente,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# Dependencias
# =============================================================================

def get_servicio(db: AsyncSession = Depends(get_db)) -> EstructuraEIAService:
    """Obtiene instancia del servicio de estructura EIA."""
    return get_estructura_eia_service(db)


# =============================================================================
# Endpoints de Generación
# =============================================================================

@router.post(
    "/generar/{proyecto_id}",
    response_model=EstructuraEIAResponse,
    summary="Generar estructura EIA para un proyecto",
    description="""
    Genera la estructura completa del EIA para un proyecto específico.

    La estructura incluye:
    - **11 capítulos** según Art. 18 DS 40, adaptados al tipo de proyecto
    - **Lista de PAS** (Permisos Ambientales Sectoriales) aplicables
    - **Anexos técnicos** requeridos según características
    - **Plan de línea base** con componentes ambientales a caracterizar
    - **Estimación de complejidad** (nivel, tiempo, recursos, riesgos)

    Si ya existe una estructura, se puede forzar regeneración con `forzar=true`.
    """,
)
async def generar_estructura(
    proyecto_id: int,
    forzar: bool = Query(False, description="Forzar regeneración si ya existe"),
    servicio: EstructuraEIAService = Depends(get_servicio),
) -> EstructuraEIAResponse:
    """Genera la estructura del EIA para un proyecto."""
    logger.info(f"Generando estructura EIA para proyecto {proyecto_id}")

    resultado = await servicio.generar_estructura(
        proyecto_id=proyecto_id,
        forzar_regenerar=forzar,
    )

    if not resultado:
        raise HTTPException(
            status_code=400,
            detail="No se pudo generar la estructura. Verifique que el proyecto existe y tiene tipo asignado."
        )

    return resultado


# =============================================================================
# Endpoints de Consulta de Estructura
# =============================================================================

@router.get(
    "/proyecto/{proyecto_id}",
    response_model=EstructuraEIAResponse,
    summary="Obtener estructura EIA de un proyecto",
    description="Retorna la estructura EIA más reciente del proyecto.",
)
async def get_estructura(
    proyecto_id: int,
    version: Optional[int] = Query(None, description="Versión específica (por defecto la última)"),
    servicio: EstructuraEIAService = Depends(get_servicio),
) -> EstructuraEIAResponse:
    """Obtiene la estructura EIA de un proyecto."""
    estructura = await servicio.get_estructura_proyecto(proyecto_id, version)

    if not estructura:
        raise HTTPException(
            status_code=404,
            detail=f"No existe estructura EIA para el proyecto {proyecto_id}"
        )

    return await servicio._convertir_a_response(estructura)


@router.get(
    "/proyecto/{proyecto_id}/resumen",
    response_model=ResumenEstructuraParaAsistente,
    summary="Obtener resumen de estructura para asistente",
    description="Retorna un resumen de la estructura formateado para el asistente IA.",
)
async def get_resumen_estructura(
    proyecto_id: int,
    servicio: EstructuraEIAService = Depends(get_servicio),
) -> ResumenEstructuraParaAsistente:
    """Obtiene resumen de estructura para el asistente."""
    return await servicio.get_resumen_para_asistente(proyecto_id)


# =============================================================================
# Endpoints de Capítulos
# =============================================================================

@router.get(
    "/proyecto/{proyecto_id}/capitulos",
    response_model=List[CapituloConEstado],
    summary="Obtener capítulos del EIA",
    description="Retorna la lista de capítulos del EIA con su estado y progreso.",
)
async def get_capitulos(
    proyecto_id: int,
    servicio: EstructuraEIAService = Depends(get_servicio),
) -> List[CapituloConEstado]:
    """Obtiene los capítulos del EIA de un proyecto."""
    estructura = await servicio.get_estructura_proyecto(proyecto_id)

    if not estructura:
        raise HTTPException(
            status_code=404,
            detail=f"No existe estructura EIA para el proyecto {proyecto_id}"
        )

    return [CapituloConEstado(**c) for c in (estructura.capitulos or [])]


@router.patch(
    "/proyecto/{proyecto_id}/capitulo/{numero}",
    response_model=CapituloConEstado,
    summary="Actualizar estado de un capítulo",
    description="Actualiza el estado y progreso de un capítulo específico.",
)
async def actualizar_capitulo(
    proyecto_id: int,
    numero: int,
    datos: ActualizarCapituloRequest,
    servicio: EstructuraEIAService = Depends(get_servicio),
) -> CapituloConEstado:
    """Actualiza el estado de un capítulo."""
    estructura = await servicio.actualizar_estado_capitulo(
        proyecto_id=proyecto_id,
        capitulo_numero=numero,
        estado=datos.estado.value,
        progreso=datos.progreso_porcentaje,
    )

    if not estructura:
        raise HTTPException(
            status_code=404,
            detail=f"No se encontró el capítulo {numero} del proyecto {proyecto_id}"
        )

    # Buscar el capítulo actualizado
    for cap in estructura.capitulos:
        if cap.get("numero") == numero:
            return CapituloConEstado(**cap)

    raise HTTPException(status_code=404, detail=f"Capítulo {numero} no encontrado")


# =============================================================================
# Endpoints de PAS (Permisos Ambientales Sectoriales)
# =============================================================================

@router.get(
    "/proyecto/{proyecto_id}/pas",
    response_model=List[PASConEstado],
    summary="Obtener PAS requeridos",
    description="Retorna la lista de PAS identificados con su estado de tramitación.",
)
async def get_pas(
    proyecto_id: int,
    servicio: EstructuraEIAService = Depends(get_servicio),
) -> List[PASConEstado]:
    """Obtiene los PAS requeridos de un proyecto."""
    estructura = await servicio.get_estructura_proyecto(proyecto_id)

    if not estructura:
        raise HTTPException(
            status_code=404,
            detail=f"No existe estructura EIA para el proyecto {proyecto_id}"
        )

    return [PASConEstado(**p) for p in (estructura.pas_requeridos or [])]


@router.patch(
    "/proyecto/{proyecto_id}/pas/{articulo}",
    response_model=PASConEstado,
    summary="Actualizar estado de un PAS",
    description="Actualiza el estado de tramitación de un PAS específico.",
)
async def actualizar_pas(
    proyecto_id: int,
    articulo: int,
    datos: ActualizarPASRequest,
    servicio: EstructuraEIAService = Depends(get_servicio),
) -> PASConEstado:
    """Actualiza el estado de un PAS."""
    estructura = await servicio.actualizar_estado_pas(
        proyecto_id=proyecto_id,
        articulo=articulo,
        estado=datos.estado.value,
    )

    if not estructura:
        raise HTTPException(
            status_code=404,
            detail=f"No se encontró el PAS Art. {articulo} del proyecto {proyecto_id}"
        )

    # Buscar el PAS actualizado
    for pas in estructura.pas_requeridos:
        if pas.get("articulo") == articulo:
            return PASConEstado(**pas)

    raise HTTPException(status_code=404, detail=f"PAS Art. {articulo} no encontrado")


# =============================================================================
# Endpoints de Anexos
# =============================================================================

@router.get(
    "/proyecto/{proyecto_id}/anexos",
    response_model=List[AnexoRequerido],
    summary="Obtener anexos requeridos",
    description="Retorna la lista de anexos técnicos requeridos con su estado.",
)
async def get_anexos(
    proyecto_id: int,
    servicio: EstructuraEIAService = Depends(get_servicio),
) -> List[AnexoRequerido]:
    """Obtiene los anexos requeridos de un proyecto."""
    estructura = await servicio.get_estructura_proyecto(proyecto_id)

    if not estructura:
        raise HTTPException(
            status_code=404,
            detail=f"No existe estructura EIA para el proyecto {proyecto_id}"
        )

    return [AnexoRequerido(**a) for a in (estructura.anexos_requeridos or [])]


@router.patch(
    "/proyecto/{proyecto_id}/anexo/{codigo}",
    response_model=AnexoRequerido,
    summary="Actualizar estado de un anexo",
    description="Actualiza el estado de elaboración de un anexo técnico.",
)
async def actualizar_anexo(
    proyecto_id: int,
    codigo: str,
    datos: ActualizarAnexoRequest,
    servicio: EstructuraEIAService = Depends(get_servicio),
) -> AnexoRequerido:
    """Actualiza el estado de un anexo."""
    estructura = await servicio.actualizar_estado_anexo(
        proyecto_id=proyecto_id,
        codigo=codigo,
        estado=datos.estado.value,
    )

    if not estructura:
        raise HTTPException(
            status_code=404,
            detail=f"No se encontró el anexo {codigo} del proyecto {proyecto_id}"
        )

    # Buscar el anexo actualizado
    for anexo in estructura.anexos_requeridos:
        if anexo.get("codigo") == codigo:
            return AnexoRequerido(**anexo)

    raise HTTPException(status_code=404, detail=f"Anexo {codigo} no encontrado")


# =============================================================================
# Endpoints de Línea Base
# =============================================================================

@router.get(
    "/proyecto/{proyecto_id}/linea-base",
    response_model=List[ComponenteLineaBaseEnPlan],
    summary="Obtener plan de línea base",
    description="Retorna el plan de línea base con componentes ambientales a caracterizar.",
)
async def get_linea_base(
    proyecto_id: int,
    servicio: EstructuraEIAService = Depends(get_servicio),
) -> List[ComponenteLineaBaseEnPlan]:
    """Obtiene el plan de línea base de un proyecto."""
    estructura = await servicio.get_estructura_proyecto(proyecto_id)

    if not estructura:
        raise HTTPException(
            status_code=404,
            detail=f"No existe estructura EIA para el proyecto {proyecto_id}"
        )

    return [ComponenteLineaBaseEnPlan(**c) for c in (estructura.plan_linea_base or [])]


# =============================================================================
# Endpoints de Complejidad
# =============================================================================

@router.get(
    "/proyecto/{proyecto_id}/complejidad",
    response_model=EstimacionComplejidad,
    summary="Obtener estimación de complejidad",
    description="""
    Retorna la estimación de complejidad del EIA.

    La estimación considera:
    - Triggers Art. 11 activados
    - Número de PAS requeridos
    - Componentes de línea base
    - Sensibilidad territorial
    - Escala del proyecto
    """,
)
async def get_complejidad(
    proyecto_id: int,
    servicio: EstructuraEIAService = Depends(get_servicio),
) -> EstimacionComplejidad:
    """Obtiene la estimación de complejidad de un proyecto."""
    estructura = await servicio.get_estructura_proyecto(proyecto_id)

    if not estructura:
        raise HTTPException(
            status_code=404,
            detail=f"No existe estructura EIA para el proyecto {proyecto_id}"
        )

    if not estructura.estimacion_complejidad:
        raise HTTPException(
            status_code=404,
            detail="La estructura no tiene estimación de complejidad"
        )

    return EstimacionComplejidad(**estructura.estimacion_complejidad)


# =============================================================================
# Endpoints de Configuración por Tipo
# =============================================================================

@router.get(
    "/tipos/{tipo_codigo}/capitulos",
    response_model=List[CapituloEIAResponse],
    summary="Obtener capítulos configurados para un tipo",
    description="Retorna los capítulos EIA configurados para un tipo de proyecto.",
)
async def get_capitulos_tipo(
    tipo_codigo: str,
    servicio: EstructuraEIAService = Depends(get_servicio),
) -> List[CapituloEIAResponse]:
    """Obtiene los capítulos configurados para un tipo de proyecto."""
    capitulos = await servicio.get_capitulos_tipo(tipo_codigo)

    if not capitulos:
        raise HTTPException(
            status_code=404,
            detail=f"No hay capítulos configurados para el tipo '{tipo_codigo}'"
        )

    return [
        CapituloEIAResponse(
            id=c.id,
            tipo_proyecto_id=c.tipo_proyecto_id,
            numero=c.numero,
            titulo=c.titulo,
            descripcion=c.descripcion,
            contenido_requerido=c.contenido_requerido or [],
            es_obligatorio=c.es_obligatorio,
            orden=c.orden,
            activo=c.activo,
        )
        for c in capitulos
    ]


@router.get(
    "/tipos/{tipo_codigo}/linea-base",
    response_model=List[ComponenteLineaBaseResponse],
    summary="Obtener componentes de línea base para un tipo",
    description="Retorna los componentes de línea base configurados para un tipo de proyecto.",
)
async def get_componentes_tipo(
    tipo_codigo: str,
    servicio: EstructuraEIAService = Depends(get_servicio),
) -> List[ComponenteLineaBaseResponse]:
    """Obtiene los componentes de línea base configurados para un tipo."""
    componentes = await servicio.get_componentes_linea_base(tipo_codigo)

    if not componentes:
        raise HTTPException(
            status_code=404,
            detail=f"No hay componentes de línea base configurados para el tipo '{tipo_codigo}'"
        )

    return [
        ComponenteLineaBaseResponse(
            id=c.id,
            tipo_proyecto_id=c.tipo_proyecto_id,
            subtipo_id=c.subtipo_id,
            capitulo_numero=c.capitulo_numero,
            codigo=c.codigo,
            nombre=c.nombre,
            descripcion=c.descripcion,
            metodologia=c.metodologia,
            variables_monitorear=c.variables_monitorear or [],
            estudios_requeridos=c.estudios_requeridos or [],
            duracion_estimada_dias=c.duracion_estimada_dias,
            es_obligatorio=c.es_obligatorio,
            orden=c.orden,
            activo=c.activo,
        )
        for c in componentes
    ]
