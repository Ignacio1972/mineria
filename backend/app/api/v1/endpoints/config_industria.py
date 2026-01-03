"""
Endpoints de Configuración por Industria.

Proporciona acceso a la configuración de tipos de proyecto,
subtipos, umbrales SEIA, PAS, normativa, OAECA, impactos,
anexos y árboles de preguntas.
"""
import logging
from typing import Optional, Dict, Any, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.config_industria import ConfigIndustriaService, get_config_industria_service
from app.schemas.config_industria import (
    # Tipos
    TipoProyectoResponse,
    TipoProyectoConSubtipos,
    TiposProyectoListResponse,
    # Subtipos
    SubtipoProyectoResponse,
    # Configuración completa
    ConfigIndustriaCompleta,
    ConfigIndustriaResumen,
    # Umbrales
    UmbralSEIAResponse,
    EvaluarUmbralRequest,
    EvaluarUmbralResponse,
    # PAS
    PASPorTipoResponse,
    PASAplicableResponse,
    PASListResponse,
    # Normativa
    NormativaPorTipoResponse,
    NormativaListResponse,
    # OAECA
    OAECAPorTipoResponse,
    # Impactos
    ImpactoPorTipoResponse,
    # Anexos
    AnexoPorTipoResponse,
    # Preguntas
    ArbolPreguntaResponse,
    PreguntasListResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# Dependencias
# =============================================================================

async def get_service(db: AsyncSession = Depends(get_db)) -> ConfigIndustriaService:
    """Obtiene el servicio de configuración por industria."""
    return get_config_industria_service(db)


# =============================================================================
# Tipos de Proyecto
# =============================================================================

@router.get(
    "/tipos",
    response_model=TiposProyectoListResponse,
    summary="Listar tipos de proyecto",
    description="Obtiene todos los tipos de proyecto disponibles con sus subtipos."
)
async def listar_tipos(
    solo_activos: bool = Query(True, description="Filtrar solo tipos activos"),
    service: ConfigIndustriaService = Depends(get_service)
):
    """Lista todos los tipos de proyecto (industrias) configurados."""
    tipos = await service.get_tipos_proyecto(solo_activos=solo_activos)

    return TiposProyectoListResponse(
        tipos=[
            TipoProyectoConSubtipos(
                id=t.id,
                codigo=t.codigo,
                nombre=t.nombre,
                letra_art3=t.letra_art3,
                descripcion=t.descripcion,
                activo=t.activo,
                created_at=t.created_at,
                subtipos=[
                    SubtipoProyectoResponse.model_validate(s)
                    for s in t.subtipos if s.activo or not solo_activos
                ]
            )
            for t in tipos
        ],
        total=len(tipos)
    )


@router.get(
    "/tipos/{codigo}",
    response_model=TipoProyectoConSubtipos,
    summary="Obtener tipo de proyecto",
    description="Obtiene un tipo de proyecto específico por código."
)
async def obtener_tipo(
    codigo: str,
    service: ConfigIndustriaService = Depends(get_service)
):
    """Obtiene un tipo de proyecto por su código."""
    tipo = await service.get_tipo_por_codigo(codigo)
    if not tipo:
        raise HTTPException(status_code=404, detail=f"Tipo de proyecto '{codigo}' no encontrado")

    return TipoProyectoConSubtipos(
        id=tipo.id,
        codigo=tipo.codigo,
        nombre=tipo.nombre,
        letra_art3=tipo.letra_art3,
        descripcion=tipo.descripcion,
        activo=tipo.activo,
        created_at=tipo.created_at,
        subtipos=[SubtipoProyectoResponse.model_validate(s) for s in tipo.subtipos]
    )


# =============================================================================
# Subtipos de Proyecto
# =============================================================================

@router.get(
    "/tipos/{tipo_codigo}/subtipos",
    response_model=List[SubtipoProyectoResponse],
    summary="Listar subtipos",
    description="Obtiene los subtipos de un tipo de proyecto."
)
async def listar_subtipos(
    tipo_codigo: str,
    solo_activos: bool = Query(True),
    service: ConfigIndustriaService = Depends(get_service)
):
    """Lista los subtipos de un tipo de proyecto."""
    subtipos = await service.get_subtipos(tipo_codigo, solo_activos=solo_activos)
    return [SubtipoProyectoResponse.model_validate(s) for s in subtipos]


# =============================================================================
# Configuración Completa
# =============================================================================

@router.get(
    "/tipos/{tipo_codigo}/config",
    response_model=ConfigIndustriaCompleta,
    summary="Configuración completa",
    description="Obtiene toda la configuración para un tipo/subtipo de proyecto."
)
async def obtener_config_completa(
    tipo_codigo: str,
    subtipo_codigo: Optional[str] = Query(None, description="Código del subtipo"),
    service: ConfigIndustriaService = Depends(get_service)
):
    """
    Obtiene la configuración completa de una industria.

    Incluye:
    - Información del tipo y subtipo
    - Subtipos disponibles
    - Umbrales SEIA
    - PAS típicos
    - Normativa aplicable
    - OAECA relevantes
    - Impactos típicos
    - Anexos requeridos
    - Árbol de preguntas
    """
    config = await service.get_config_completa(tipo_codigo, subtipo_codigo)
    if not config:
        raise HTTPException(
            status_code=404,
            detail=f"Configuración no encontrada para tipo '{tipo_codigo}'"
        )
    return config


@router.get(
    "/resumen",
    response_model=List[ConfigIndustriaResumen],
    summary="Resumen de configuraciones",
    description="Obtiene un resumen de la configuración de todas las industrias."
)
async def obtener_resumen_config(
    service: ConfigIndustriaService = Depends(get_service)
):
    """Obtiene resumen de configuración de todas las industrias."""
    tipos = await service.get_tipos_proyecto()
    resumenes = []

    for tipo in tipos:
        config = await service.get_config_completa(tipo.codigo)
        if config:
            resumenes.append(ConfigIndustriaResumen(
                tipo=TipoProyectoResponse.model_validate(tipo),
                num_subtipos=len(config.subtipos_disponibles),
                num_umbrales=len(config.umbrales),
                num_pas=len(config.pas),
                num_normativas=len(config.normativa),
                num_preguntas=len(config.preguntas)
            ))

    return resumenes


# =============================================================================
# Umbrales SEIA
# =============================================================================

@router.get(
    "/tipos/{tipo_codigo}/umbrales",
    response_model=List[UmbralSEIAResponse],
    summary="Listar umbrales SEIA",
    description="Obtiene los umbrales de ingreso SEIA para un tipo de proyecto."
)
async def listar_umbrales(
    tipo_codigo: str,
    subtipo_codigo: Optional[str] = Query(None),
    service: ConfigIndustriaService = Depends(get_service)
):
    """Lista los umbrales SEIA de un tipo de proyecto."""
    tipo = await service.get_tipo_por_codigo(tipo_codigo)
    if not tipo:
        raise HTTPException(status_code=404, detail=f"Tipo '{tipo_codigo}' no encontrado")

    subtipo_id = None
    if subtipo_codigo:
        subtipo = await service.get_subtipo_por_codigo(tipo_codigo, subtipo_codigo)
        if subtipo:
            subtipo_id = subtipo.id

    umbrales = await service.get_umbrales(tipo.id, subtipo_id)
    return [UmbralSEIAResponse.model_validate(u) for u in umbrales]


@router.post(
    "/evaluar-umbral",
    response_model=EvaluarUmbralResponse,
    summary="Evaluar umbral SEIA",
    description="Evalúa si un proyecto cumple umbrales de ingreso al SEIA."
)
async def evaluar_umbral(
    request: EvaluarUmbralRequest,
    service: ConfigIndustriaService = Depends(get_service)
):
    """
    Evalúa si un proyecto cumple umbral de ingreso SEIA.

    Ejemplo de uso:
    ```json
    {
        "tipo_proyecto_codigo": "mineria",
        "parametros": {"tonelaje_mensual": 4500}
    }
    ```
    """
    resultado = await service.evaluar_umbral(
        tipo_codigo=request.tipo_proyecto_codigo,
        parametros=request.parametros,
        subtipo_codigo=request.subtipo_codigo
    )

    if not resultado:
        raise HTTPException(
            status_code=404,
            detail=f"No se pudo evaluar umbral para tipo '{request.tipo_proyecto_codigo}'"
        )

    return resultado


# =============================================================================
# PAS (Permisos Ambientales Sectoriales)
# =============================================================================

@router.get(
    "/tipos/{tipo_codigo}/pas",
    response_model=PASListResponse,
    summary="Listar PAS",
    description="Obtiene los PAS típicos de un tipo de proyecto."
)
async def listar_pas(
    tipo_codigo: str,
    subtipo_codigo: Optional[str] = Query(None),
    service: ConfigIndustriaService = Depends(get_service)
):
    """Lista los PAS típicos de un tipo de proyecto."""
    tipo = await service.get_tipo_por_codigo(tipo_codigo)
    if not tipo:
        raise HTTPException(status_code=404, detail=f"Tipo '{tipo_codigo}' no encontrado")

    subtipo_id = None
    if subtipo_codigo:
        subtipo = await service.get_subtipo_por_codigo(tipo_codigo, subtipo_codigo)
        if subtipo:
            subtipo_id = subtipo.id

    pas_list = await service.get_pas(tipo.id, subtipo_id)
    return PASListResponse(
        pas=[PASPorTipoResponse.model_validate(p) for p in pas_list],
        total=len(pas_list)
    )


@router.post(
    "/tipos/{tipo_codigo}/pas/aplicables",
    response_model=List[PASAplicableResponse],
    summary="Identificar PAS aplicables",
    description="Identifica los PAS que aplican según características del proyecto."
)
async def identificar_pas_aplicables(
    tipo_codigo: str,
    caracteristicas: Dict[str, Any],
    subtipo_codigo: Optional[str] = Query(None),
    service: ConfigIndustriaService = Depends(get_service)
):
    """
    Identifica los PAS aplicables según características del proyecto.

    Ejemplo de características:
    ```json
    {
        "tiene_relaves": true,
        "tiene_botadero": true,
        "interviene_cauce": false
    }
    ```
    """
    resultado = await service.get_pas_aplicables(
        tipo_codigo=tipo_codigo,
        caracteristicas=caracteristicas,
        subtipo_codigo=subtipo_codigo
    )
    return resultado


# =============================================================================
# Normativa
# =============================================================================

@router.get(
    "/tipos/{tipo_codigo}/normativa",
    response_model=NormativaListResponse,
    summary="Listar normativa",
    description="Obtiene la normativa aplicable a un tipo de proyecto."
)
async def listar_normativa(
    tipo_codigo: str,
    service: ConfigIndustriaService = Depends(get_service)
):
    """Lista la normativa aplicable a un tipo de proyecto."""
    tipo = await service.get_tipo_por_codigo(tipo_codigo)
    if not tipo:
        raise HTTPException(status_code=404, detail=f"Tipo '{tipo_codigo}' no encontrado")

    normativas = await service.get_normativa(tipo.id)
    return NormativaListResponse(
        normativas=[NormativaPorTipoResponse.model_validate(n) for n in normativas],
        total=len(normativas)
    )


# =============================================================================
# OAECA
# =============================================================================

@router.get(
    "/tipos/{tipo_codigo}/oaeca",
    response_model=List[OAECAPorTipoResponse],
    summary="Listar OAECA",
    description="Obtiene los OAECA relevantes para un tipo de proyecto."
)
async def listar_oaeca(
    tipo_codigo: str,
    service: ConfigIndustriaService = Depends(get_service)
):
    """Lista los OAECA relevantes para un tipo de proyecto."""
    tipo = await service.get_tipo_por_codigo(tipo_codigo)
    if not tipo:
        raise HTTPException(status_code=404, detail=f"Tipo '{tipo_codigo}' no encontrado")

    oaecas = await service.get_oaeca(tipo.id)
    return [OAECAPorTipoResponse.model_validate(o) for o in oaecas]


# =============================================================================
# Impactos
# =============================================================================

@router.get(
    "/tipos/{tipo_codigo}/impactos",
    response_model=List[ImpactoPorTipoResponse],
    summary="Listar impactos típicos",
    description="Obtiene los impactos típicos de un tipo de proyecto."
)
async def listar_impactos(
    tipo_codigo: str,
    subtipo_codigo: Optional[str] = Query(None),
    service: ConfigIndustriaService = Depends(get_service)
):
    """Lista los impactos típicos de un tipo de proyecto."""
    tipo = await service.get_tipo_por_codigo(tipo_codigo)
    if not tipo:
        raise HTTPException(status_code=404, detail=f"Tipo '{tipo_codigo}' no encontrado")

    subtipo_id = None
    if subtipo_codigo:
        subtipo = await service.get_subtipo_por_codigo(tipo_codigo, subtipo_codigo)
        if subtipo:
            subtipo_id = subtipo.id

    impactos = await service.get_impactos(tipo.id, subtipo_id)
    return [ImpactoPorTipoResponse.model_validate(i) for i in impactos]


# =============================================================================
# Anexos
# =============================================================================

@router.get(
    "/tipos/{tipo_codigo}/anexos",
    response_model=List[AnexoPorTipoResponse],
    summary="Listar anexos",
    description="Obtiene los anexos requeridos para un tipo de proyecto."
)
async def listar_anexos(
    tipo_codigo: str,
    subtipo_codigo: Optional[str] = Query(None),
    service: ConfigIndustriaService = Depends(get_service)
):
    """Lista los anexos requeridos para un tipo de proyecto."""
    tipo = await service.get_tipo_por_codigo(tipo_codigo)
    if not tipo:
        raise HTTPException(status_code=404, detail=f"Tipo '{tipo_codigo}' no encontrado")

    subtipo_id = None
    if subtipo_codigo:
        subtipo = await service.get_subtipo_por_codigo(tipo_codigo, subtipo_codigo)
        if subtipo:
            subtipo_id = subtipo.id

    anexos = await service.get_anexos(tipo.id, subtipo_id)
    return [AnexoPorTipoResponse.model_validate(a) for a in anexos]


@router.post(
    "/tipos/{tipo_codigo}/anexos/aplicables",
    response_model=List[AnexoPorTipoResponse],
    summary="Identificar anexos aplicables",
    description="Identifica los anexos que aplican según características del proyecto."
)
async def identificar_anexos_aplicables(
    tipo_codigo: str,
    caracteristicas: Dict[str, Any],
    subtipo_codigo: Optional[str] = Query(None),
    service: ConfigIndustriaService = Depends(get_service)
):
    """Identifica los anexos aplicables según características del proyecto."""
    anexos = await service.get_anexos_aplicables(
        tipo_codigo=tipo_codigo,
        caracteristicas=caracteristicas,
        subtipo_codigo=subtipo_codigo
    )
    return [AnexoPorTipoResponse.model_validate(a) for a in anexos]


# =============================================================================
# Árbol de Preguntas
# =============================================================================

@router.get(
    "/tipos/{tipo_codigo}/preguntas",
    response_model=PreguntasListResponse,
    summary="Listar preguntas",
    description="Obtiene el árbol de preguntas para un tipo de proyecto."
)
async def listar_preguntas(
    tipo_codigo: str,
    subtipo_codigo: Optional[str] = Query(None),
    service: ConfigIndustriaService = Depends(get_service)
):
    """Lista las preguntas del árbol para un tipo de proyecto."""
    tipo = await service.get_tipo_por_codigo(tipo_codigo)
    if not tipo:
        raise HTTPException(status_code=404, detail=f"Tipo '{tipo_codigo}' no encontrado")

    subtipo_id = None
    if subtipo_codigo:
        subtipo = await service.get_subtipo_por_codigo(tipo_codigo, subtipo_codigo)
        if subtipo:
            subtipo_id = subtipo.id

    preguntas = await service.get_preguntas(tipo.id, subtipo_id)
    return PreguntasListResponse(
        preguntas=[ArbolPreguntaResponse.model_validate(p) for p in preguntas],
        total=len(preguntas)
    )


@router.post(
    "/tipos/{tipo_codigo}/preguntas/siguiente",
    response_model=Optional[ArbolPreguntaResponse],
    summary="Siguiente pregunta",
    description="Obtiene la siguiente pregunta del árbol según respuestas previas."
)
async def obtener_siguiente_pregunta(
    tipo_codigo: str,
    respuestas_previas: Dict[str, Any],
    subtipo_codigo: Optional[str] = Query(None),
    service: ConfigIndustriaService = Depends(get_service)
):
    """
    Obtiene la siguiente pregunta del árbol.

    Ejemplo de respuestas previas:
    ```json
    {
        "nombre_proyecto": "Mina Los Andes",
        "tipo_extraccion": "rajo_abierto",
        "tonelaje_mensual": 6000
    }
    ```
    """
    pregunta = await service.get_siguiente_pregunta(
        tipo_codigo=tipo_codigo,
        respuestas_previas=respuestas_previas,
        subtipo_codigo=subtipo_codigo
    )

    if pregunta:
        return ArbolPreguntaResponse.model_validate(pregunta)
    return None


@router.post(
    "/tipos/{tipo_codigo}/preguntas/progreso",
    summary="Calcular progreso",
    description="Calcula el progreso de recopilación de información."
)
async def calcular_progreso(
    tipo_codigo: str,
    respuestas_previas: Dict[str, Any],
    subtipo_codigo: Optional[str] = Query(None),
    service: ConfigIndustriaService = Depends(get_service)
):
    """Calcula el progreso de recopilación."""
    respondidas, total = await service.calcular_progreso(
        tipo_codigo=tipo_codigo,
        respuestas_previas=respuestas_previas,
        subtipo_codigo=subtipo_codigo
    )

    porcentaje = (respondidas / total * 100) if total > 0 else 0

    return {
        "preguntas_respondidas": respondidas,
        "preguntas_totales": total,
        "porcentaje": round(porcentaje, 1),
        "completado": respondidas >= total
    }
