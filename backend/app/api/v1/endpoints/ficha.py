"""
Endpoints de Ficha Acumulativa del Proyecto.

Expone el FichaService via REST para gestionar características,
PAS, análisis Art. 11, diagnósticos y progreso del proyecto.
"""
import logging
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.asistente.ficha import FichaService, get_ficha_service
from app.schemas.ficha import (
    # Características
    CaracteristicaCreate,
    CaracteristicaUpdate,
    CaracteristicaResponse,
    CaracteristicasByCategoriaResponse,
    CaracteristicaBulkCreate,
    CategoriaCaracteristica,
    # PAS
    PASProyectoCreate,
    PASProyectoUpdate,
    PASProyectoResponse,
    EstadoPASEnum,
    # Análisis Art. 11
    AnalisisArt11Create,
    AnalisisArt11Update,
    AnalisisArt11Response,
    # Diagnóstico
    DiagnosticoResponse,
    # Ficha consolidada
    FichaProyectoResponse,
    FichaResumenResponse,
    # Progreso
    ProgresoFichaResponse,
    # Asistente
    GuardarRespuestaAsistente,
    GuardarRespuestasAsistenteRequest,
    GuardarRespuestasAsistenteResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# Dependencias
# =============================================================================

async def get_service(db: AsyncSession = Depends(get_db)) -> FichaService:
    """Obtiene el servicio de ficha."""
    return get_ficha_service(db)


# =============================================================================
# Ficha Consolidada
# =============================================================================

@router.get(
    "/{proyecto_id}",
    response_model=FichaProyectoResponse,
    summary="Obtener ficha completa",
    description="Obtiene la ficha acumulativa completa del proyecto con todas sus características, análisis y diagnóstico."
)
async def obtener_ficha_completa(
    proyecto_id: int = Path(..., description="ID del proyecto"),
    service: FichaService = Depends(get_service)
):
    """
    Obtiene la ficha consolidada del proyecto.

    Incluye:
    - Información general del proyecto
    - Tipo y subtipo de proyecto
    - Ubicación vigente
    - Características por categoría
    - Análisis Art. 11 por literal
    - Diagnóstico actual
    - PAS identificados
    - Estadísticas de progreso
    """
    ficha = await service.get_ficha_completa(proyecto_id)
    if not ficha:
        raise HTTPException(
            status_code=404,
            detail=f"Proyecto con ID {proyecto_id} no encontrado"
        )
    return ficha


@router.get(
    "/{proyecto_id}/resumen",
    response_model=FichaResumenResponse,
    summary="Obtener resumen de ficha",
    description="Obtiene un resumen de la ficha para listados."
)
async def obtener_ficha_resumen(
    proyecto_id: int = Path(..., description="ID del proyecto"),
    service: FichaService = Depends(get_service)
):
    """Obtiene resumen de la ficha para listados."""
    resumen = await service.get_ficha_resumen(proyecto_id)
    if not resumen:
        raise HTTPException(
            status_code=404,
            detail=f"Proyecto con ID {proyecto_id} no encontrado"
        )
    return resumen


# =============================================================================
# Características
# =============================================================================

@router.get(
    "/{proyecto_id}/caracteristicas",
    response_model=List[CaracteristicaResponse],
    summary="Listar características",
    description="Obtiene todas las características del proyecto."
)
async def listar_caracteristicas(
    proyecto_id: int = Path(..., description="ID del proyecto"),
    categoria: Optional[CategoriaCaracteristica] = Query(
        None, description="Filtrar por categoría"
    ),
    service: FichaService = Depends(get_service)
):
    """Lista las características del proyecto."""
    caracteristicas = await service.get_caracteristicas(
        proyecto_id,
        categoria=categoria.value if categoria else None
    )
    return [CaracteristicaResponse.model_validate(c) for c in caracteristicas]


@router.get(
    "/{proyecto_id}/caracteristicas/por-categoria",
    response_model=CaracteristicasByCategoriaResponse,
    summary="Características por categoría",
    description="Obtiene las características agrupadas por categoría."
)
async def obtener_caracteristicas_por_categoria(
    proyecto_id: int = Path(..., description="ID del proyecto"),
    service: FichaService = Depends(get_service)
):
    """Obtiene características agrupadas por categoría."""
    return await service.get_caracteristicas_by_categoria(proyecto_id)


@router.post(
    "/{proyecto_id}/caracteristicas",
    response_model=CaracteristicaResponse,
    status_code=201,
    summary="Crear característica",
    description="Crea o actualiza una característica del proyecto (upsert)."
)
async def crear_caracteristica(
    proyecto_id: int,
    data: CaracteristicaCreate,
    service: FichaService = Depends(get_service)
):
    """Crea o actualiza una característica."""
    caracteristica = await service.guardar_caracteristica(proyecto_id, data)
    await service.db.commit()
    return CaracteristicaResponse.model_validate(caracteristica)


@router.post(
    "/{proyecto_id}/caracteristicas/bulk",
    response_model=List[CaracteristicaResponse],
    status_code=201,
    summary="Crear características en lote",
    description="Crea múltiples características de una vez."
)
async def crear_caracteristicas_bulk(
    proyecto_id: int,
    data: CaracteristicaBulkCreate,
    service: FichaService = Depends(get_service)
):
    """Crea múltiples características."""
    caracteristicas = await service.guardar_caracteristicas_bulk(
        proyecto_id,
        data.caracteristicas
    )
    await service.db.commit()
    return [CaracteristicaResponse.model_validate(c) for c in caracteristicas]


@router.get(
    "/{proyecto_id}/caracteristicas/{categoria}/{clave}",
    response_model=CaracteristicaResponse,
    summary="Obtener característica",
    description="Obtiene una característica específica."
)
async def obtener_caracteristica(
    proyecto_id: int,
    categoria: CategoriaCaracteristica,
    clave: str,
    service: FichaService = Depends(get_service)
):
    """Obtiene una característica específica."""
    caracteristica = await service.get_caracteristica(
        proyecto_id, categoria.value, clave
    )
    if not caracteristica:
        raise HTTPException(
            status_code=404,
            detail=f"Característica '{categoria.value}.{clave}' no encontrada"
        )
    return CaracteristicaResponse.model_validate(caracteristica)


@router.patch(
    "/{proyecto_id}/caracteristicas/{categoria}/{clave}",
    response_model=CaracteristicaResponse,
    summary="Actualizar característica",
    description="Actualiza una característica existente."
)
async def actualizar_caracteristica(
    proyecto_id: int,
    categoria: CategoriaCaracteristica,
    clave: str,
    data: CaracteristicaUpdate,
    service: FichaService = Depends(get_service)
):
    """Actualiza una característica existente."""
    caracteristica = await service.get_caracteristica(
        proyecto_id, categoria.value, clave
    )
    if not caracteristica:
        raise HTTPException(
            status_code=404,
            detail=f"Característica '{categoria.value}.{clave}' no encontrada"
        )

    # Actualizar campos
    for field, value in data.model_dump(exclude_unset=True).items():
        if value is not None:
            if field == 'fuente':
                setattr(caracteristica, field, value.value)
            else:
                setattr(caracteristica, field, value)

    await service.db.commit()
    return CaracteristicaResponse.model_validate(caracteristica)


@router.post(
    "/{proyecto_id}/caracteristicas/{categoria}/{clave}/validar",
    response_model=CaracteristicaResponse,
    summary="Validar característica",
    description="Marca una característica como validada."
)
async def validar_caracteristica(
    proyecto_id: int,
    categoria: CategoriaCaracteristica,
    clave: str,
    validado_por: str = Query(..., description="Usuario que valida"),
    service: FichaService = Depends(get_service)
):
    """Valida una característica."""
    caracteristica = await service.validar_caracteristica(
        proyecto_id, categoria.value, clave, validado_por
    )
    if not caracteristica:
        raise HTTPException(
            status_code=404,
            detail=f"Característica '{categoria.value}.{clave}' no encontrada"
        )
    await service.db.commit()
    return CaracteristicaResponse.model_validate(caracteristica)


@router.delete(
    "/{proyecto_id}/caracteristicas/{categoria}/{clave}",
    status_code=204,
    summary="Eliminar característica",
    description="Elimina una característica del proyecto."
)
async def eliminar_caracteristica(
    proyecto_id: int,
    categoria: CategoriaCaracteristica,
    clave: str,
    service: FichaService = Depends(get_service)
):
    """Elimina una característica."""
    eliminado = await service.eliminar_caracteristica(
        proyecto_id, categoria.value, clave
    )
    if not eliminado:
        raise HTTPException(
            status_code=404,
            detail=f"Característica '{categoria.value}.{clave}' no encontrada"
        )
    await service.db.commit()
    return None


# =============================================================================
# PAS del Proyecto
# =============================================================================

@router.get(
    "/{proyecto_id}/pas",
    response_model=List[PASProyectoResponse],
    summary="Listar PAS",
    description="Obtiene los PAS identificados del proyecto."
)
async def listar_pas(
    proyecto_id: int = Path(..., description="ID del proyecto"),
    service: FichaService = Depends(get_service)
):
    """Lista los PAS del proyecto."""
    pas_list = await service.get_pas(proyecto_id)
    return [PASProyectoResponse.model_validate(p) for p in pas_list]


@router.post(
    "/{proyecto_id}/pas",
    response_model=PASProyectoResponse,
    status_code=201,
    summary="Crear/Actualizar PAS",
    description="Crea o actualiza un PAS del proyecto (upsert por artículo)."
)
async def crear_pas(
    proyecto_id: int,
    data: PASProyectoCreate,
    service: FichaService = Depends(get_service)
):
    """Crea o actualiza un PAS."""
    pas = await service.guardar_pas(proyecto_id, data)
    await service.db.commit()
    return PASProyectoResponse.model_validate(pas)


@router.get(
    "/{proyecto_id}/pas/{articulo}",
    response_model=PASProyectoResponse,
    summary="Obtener PAS",
    description="Obtiene un PAS específico por artículo."
)
async def obtener_pas(
    proyecto_id: int,
    articulo: int = Path(..., ge=100, le=200),
    service: FichaService = Depends(get_service)
):
    """Obtiene un PAS específico."""
    pas = await service.get_pas_by_articulo(proyecto_id, articulo)
    if not pas:
        raise HTTPException(
            status_code=404,
            detail=f"PAS artículo {articulo} no encontrado"
        )
    return PASProyectoResponse.model_validate(pas)


@router.patch(
    "/{proyecto_id}/pas/{articulo}",
    response_model=PASProyectoResponse,
    summary="Actualizar estado PAS",
    description="Actualiza el estado de un PAS."
)
async def actualizar_pas(
    proyecto_id: int,
    articulo: int,
    data: PASProyectoUpdate,
    service: FichaService = Depends(get_service)
):
    """Actualiza el estado de un PAS."""
    pas = await service.get_pas_by_articulo(proyecto_id, articulo)
    if not pas:
        raise HTTPException(
            status_code=404,
            detail=f"PAS artículo {articulo} no encontrado"
        )

    if data.estado:
        pas = await service.actualizar_estado_pas(
            proyecto_id,
            articulo,
            data.estado.value,
            data.justificacion
        )
    await service.db.commit()
    return PASProyectoResponse.model_validate(pas)


# =============================================================================
# Análisis Art. 11
# =============================================================================

@router.get(
    "/{proyecto_id}/art11",
    response_model=List[AnalisisArt11Response],
    summary="Listar análisis Art. 11",
    description="Obtiene el análisis de cada literal del Art. 11."
)
async def listar_analisis_art11(
    proyecto_id: int = Path(..., description="ID del proyecto"),
    service: FichaService = Depends(get_service)
):
    """Lista el análisis Art. 11 del proyecto."""
    analisis = await service.get_analisis_art11(proyecto_id)
    return [AnalisisArt11Response.model_validate(a) for a in analisis]


@router.get(
    "/{proyecto_id}/art11/{literal}",
    response_model=AnalisisArt11Response,
    summary="Obtener análisis de literal",
    description="Obtiene el análisis de un literal específico (a-f)."
)
async def obtener_analisis_literal(
    proyecto_id: int,
    literal: str = Path(..., pattern="^[a-f]$"),
    service: FichaService = Depends(get_service)
):
    """Obtiene análisis de un literal específico."""
    analisis = await service.get_analisis_literal(proyecto_id, literal)
    if not analisis:
        raise HTTPException(
            status_code=404,
            detail=f"Análisis del literal '{literal}' no encontrado"
        )
    return AnalisisArt11Response.model_validate(analisis)


@router.post(
    "/{proyecto_id}/art11",
    response_model=AnalisisArt11Response,
    status_code=201,
    summary="Crear/Actualizar análisis literal",
    description="Crea o actualiza el análisis de un literal Art. 11."
)
async def crear_analisis_art11(
    proyecto_id: int,
    data: AnalisisArt11Create,
    service: FichaService = Depends(get_service)
):
    """Crea o actualiza análisis de literal Art. 11."""
    analisis = await service.guardar_analisis_art11(proyecto_id, data)
    await service.db.commit()
    return AnalisisArt11Response.model_validate(analisis)


@router.patch(
    "/{proyecto_id}/art11/{literal}",
    response_model=AnalisisArt11Response,
    summary="Actualizar análisis literal",
    description="Actualiza el análisis de un literal específico."
)
async def actualizar_analisis_art11(
    proyecto_id: int,
    literal: str = Path(..., pattern="^[a-f]$"),
    data: AnalisisArt11Update = None,
    service: FichaService = Depends(get_service)
):
    """Actualiza análisis de un literal."""
    analisis = await service.get_analisis_literal(proyecto_id, literal)
    if not analisis:
        raise HTTPException(
            status_code=404,
            detail=f"Análisis del literal '{literal}' no encontrado"
        )

    # Actualizar campos
    if data:
        for field, value in data.model_dump(exclude_unset=True).items():
            if value is not None:
                if field == 'estado':
                    setattr(analisis, field, value.value)
                else:
                    setattr(analisis, field, value)

    await service.db.commit()
    return AnalisisArt11Response.model_validate(analisis)


# =============================================================================
# Diagnóstico
# =============================================================================

@router.get(
    "/{proyecto_id}/diagnostico",
    response_model=DiagnosticoResponse,
    summary="Obtener diagnóstico actual",
    description="Obtiene el diagnóstico más reciente del proyecto."
)
async def obtener_diagnostico(
    proyecto_id: int = Path(..., description="ID del proyecto"),
    service: FichaService = Depends(get_service)
):
    """Obtiene el diagnóstico actual del proyecto."""
    diagnostico = await service.get_diagnostico_actual(proyecto_id)
    if not diagnostico:
        raise HTTPException(
            status_code=404,
            detail=f"No hay diagnóstico para el proyecto {proyecto_id}"
        )
    return DiagnosticoResponse.model_validate(diagnostico)


# =============================================================================
# Progreso
# =============================================================================

@router.get(
    "/{proyecto_id}/progreso",
    response_model=ProgresoFichaResponse,
    summary="Obtener progreso",
    description="Calcula el progreso de completitud de la ficha."
)
async def obtener_progreso(
    proyecto_id: int = Path(..., description="ID del proyecto"),
    service: FichaService = Depends(get_service)
):
    """Calcula el progreso de la ficha."""
    return await service.calcular_progreso(proyecto_id)


# =============================================================================
# Respuestas del Asistente
# =============================================================================

@router.post(
    "/{proyecto_id}/respuestas-asistente",
    response_model=GuardarRespuestasAsistenteResponse,
    summary="Guardar respuestas del asistente",
    description="Guarda respuestas recopiladas por el asistente en la ficha."
)
async def guardar_respuestas_asistente(
    proyecto_id: int,
    respuestas: List[GuardarRespuestaAsistente],
    service: FichaService = Depends(get_service)
):
    """
    Guarda respuestas del asistente en la ficha.

    Este endpoint es usado por el AsistenteService cuando el usuario
    responde preguntas durante la conversación.
    """
    resultado = await service.guardar_respuestas_asistente(proyecto_id, respuestas)
    await service.db.commit()
    return resultado
