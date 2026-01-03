"""
Endpoints de Recopilacion Guiada (Fase 3).

Permite la recopilacion de contenido del EIA capitulo por capitulo,
con validacion de consistencia y extraccion de documentos.
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.recopilacion.service import RecopilacionService
from app.schemas.recopilacion import (
    IniciarCapituloResponse,
    SeccionConPreguntas,
    ContenidoEIAResponse,
    GuardarRespuestasRequest,
    CapituloProgreso,
    ProgresoGeneralEIA,
    ValidacionConsistenciaResponse,
    VincularDocumentoRequest,
    ExtraccionDocumentoRequest,
    ExtraccionDocumentoResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# Dependencias
# =============================================================================

def get_servicio(db: AsyncSession = Depends(get_db)) -> RecopilacionService:
    """Obtiene instancia del servicio de recopilacion."""
    return RecopilacionService(db)


# =============================================================================
# Endpoints de Navegacion y Capitulos
# =============================================================================

@router.post(
    "/{proyecto_id}/capitulo/{num}/iniciar",
    response_model=IniciarCapituloResponse,
    summary="Iniciar recopilacion de un capitulo",
    description="""
    Inicia o retoma la recopilacion de un capitulo del EIA.

    Retorna:
    - Lista de secciones del capitulo
    - Preguntas por seccion con respuestas existentes
    - Progreso actual del capitulo
    - Mensaje de bienvenida contextual
    """,
)
async def iniciar_capitulo(
    proyecto_id: int,
    num: int,
    servicio: RecopilacionService = Depends(get_servicio),
) -> IniciarCapituloResponse:
    """Inicia la recopilacion de un capitulo."""
    logger.info(f"Iniciando recopilacion capitulo {num} para proyecto {proyecto_id}")

    try:
        return await servicio.iniciar_capitulo(proyecto_id, num)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error iniciando capitulo: {e}")
        raise HTTPException(status_code=500, detail="Error al iniciar capitulo")


@router.get(
    "/{proyecto_id}/capitulo/{num}/preguntas",
    response_model=IniciarCapituloResponse,
    summary="Obtener preguntas de un capitulo",
    description="Retorna todas las preguntas del capitulo con sus respuestas actuales.",
)
async def get_preguntas_capitulo(
    proyecto_id: int,
    num: int,
    servicio: RecopilacionService = Depends(get_servicio),
) -> IniciarCapituloResponse:
    """Obtiene las preguntas de un capitulo."""
    try:
        return await servicio.iniciar_capitulo(proyecto_id, num)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# =============================================================================
# Endpoints de Secciones
# =============================================================================

@router.get(
    "/{proyecto_id}/seccion/{capitulo}/{codigo}",
    response_model=SeccionConPreguntas,
    summary="Obtener preguntas de una seccion",
    description="Retorna las preguntas de una seccion especifica con sus respuestas.",
)
async def get_seccion(
    proyecto_id: int,
    capitulo: int,
    codigo: str,
    servicio: RecopilacionService = Depends(get_servicio),
) -> SeccionConPreguntas:
    """Obtiene las preguntas de una seccion."""
    try:
        return await servicio.get_preguntas_seccion(proyecto_id, capitulo, codigo)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post(
    "/{proyecto_id}/seccion/{codigo}",
    response_model=ContenidoEIAResponse,
    summary="Guardar respuestas de una seccion",
    description="""
    Guarda las respuestas de una seccion.

    El sistema:
    - Actualiza el contenido de la seccion
    - Recalcula el progreso
    - Actualiza el estado (pendiente/en_progreso/completado)
    """,
)
async def guardar_seccion(
    proyecto_id: int,
    codigo: str,
    datos: GuardarRespuestasRequest,
    capitulo: int = Query(..., description="Numero del capitulo"),
    servicio: RecopilacionService = Depends(get_servicio),
) -> ContenidoEIAResponse:
    """Guarda las respuestas de una seccion."""
    logger.info(f"Guardando seccion {codigo} cap {capitulo} proyecto {proyecto_id}")

    respuestas_dict = {r.codigo_pregunta: r.valor for r in datos.respuestas}

    try:
        return await servicio.guardar_respuestas(
            proyecto_id, capitulo, codigo, respuestas_dict
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error guardando seccion: {e}")
        raise HTTPException(status_code=500, detail="Error al guardar respuestas")


# =============================================================================
# Endpoints de Progreso
# =============================================================================

@router.get(
    "/{proyecto_id}/progreso",
    response_model=ProgresoGeneralEIA,
    summary="Obtener progreso general del EIA",
    description="""
    Retorna el progreso general del EIA con:
    - Total de capitulos y completados
    - Progreso porcentual
    - Inconsistencias detectadas
    - Detalle por capitulo
    """,
)
async def get_progreso_general(
    proyecto_id: int,
    servicio: RecopilacionService = Depends(get_servicio),
) -> ProgresoGeneralEIA:
    """Obtiene el progreso general del EIA."""
    try:
        return await servicio.get_progreso_general(proyecto_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/{proyecto_id}/progreso/{capitulo}",
    response_model=CapituloProgreso,
    summary="Obtener progreso de un capitulo",
    description="Retorna el progreso detallado de un capitulo especifico.",
)
async def get_progreso_capitulo(
    proyecto_id: int,
    capitulo: int,
    servicio: RecopilacionService = Depends(get_servicio),
) -> CapituloProgreso:
    """Obtiene el progreso de un capitulo."""
    try:
        return await servicio.get_progreso_capitulo(proyecto_id, capitulo)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# =============================================================================
# Endpoints de Validacion
# =============================================================================

@router.post(
    "/{proyecto_id}/validar",
    response_model=ValidacionConsistenciaResponse,
    summary="Validar consistencia del EIA",
    description="""
    Valida la consistencia entre capitulos del EIA.

    Detecta inconsistencias como:
    - Coordenadas diferentes entre capitulos
    - Superficies no coincidentes
    - Referencias cruzadas invalidas
    - Datos contradictorios

    Opcionalmente se pueden especificar capitulos a validar.
    """,
)
async def validar_consistencia(
    proyecto_id: int,
    capitulos: Optional[List[int]] = Query(None, description="Capitulos a validar"),
    servicio: RecopilacionService = Depends(get_servicio),
) -> ValidacionConsistenciaResponse:
    """Valida la consistencia entre capitulos."""
    logger.info(f"Validando consistencia proyecto {proyecto_id}")

    try:
        return await servicio.validar_consistencia(proyecto_id, capitulos)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error validando consistencia: {e}")
        raise HTTPException(status_code=500, detail="Error al validar consistencia")


@router.get(
    "/{proyecto_id}/inconsistencias",
    response_model=ValidacionConsistenciaResponse,
    summary="Obtener inconsistencias detectadas",
    description="Retorna las inconsistencias detectadas sin re-evaluar.",
)
async def get_inconsistencias(
    proyecto_id: int,
    servicio: RecopilacionService = Depends(get_servicio),
) -> ValidacionConsistenciaResponse:
    """Obtiene las inconsistencias detectadas."""
    try:
        return await servicio.validar_consistencia(proyecto_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# =============================================================================
# Endpoints de Documentos
# =============================================================================

@router.post(
    "/{proyecto_id}/vincular-documento",
    response_model=ContenidoEIAResponse,
    summary="Vincular documento a seccion",
    description="Vincula un documento existente a una seccion del EIA.",
)
async def vincular_documento(
    proyecto_id: int,
    datos: VincularDocumentoRequest,
    servicio: RecopilacionService = Depends(get_servicio),
) -> ContenidoEIAResponse:
    """Vincula un documento a una seccion."""
    logger.info(
        f"Vinculando doc {datos.documento_id} a seccion {datos.seccion_codigo} "
        f"cap {datos.capitulo_numero} proyecto {proyecto_id}"
    )

    try:
        return await servicio.vincular_documento(
            proyecto_id,
            datos.documento_id,
            datos.capitulo_numero,
            datos.seccion_codigo,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error vinculando documento: {e}")
        raise HTTPException(status_code=500, detail="Error al vincular documento")


@router.post(
    "/{proyecto_id}/extraer-documento",
    response_model=ExtraccionDocumentoResponse,
    summary="Extraer datos de documento",
    description="""
    Extrae datos de un documento tecnico usando IA (Claude Vision).

    El sistema:
    - Procesa el documento con OCR/Vision
    - Extrae datos estructurados
    - Sugiere mapeo a secciones del EIA
    - Retorna datos con nivel de confianza
    """,
)
async def extraer_documento(
    proyecto_id: int,
    datos: ExtraccionDocumentoRequest,
    db: AsyncSession = Depends(get_db),
) -> ExtraccionDocumentoResponse:
    """Extrae datos de un documento."""
    from app.services.recopilacion.extraccion import ExtraccionDocumentosService

    logger.info(f"Extrayendo datos de doc {datos.documento_id} proyecto {proyecto_id}")

    try:
        servicio_extraccion = ExtraccionDocumentosService(db)
        resultado = await servicio_extraccion.extraer_datos_documento(
            proyecto_id=proyecto_id,
            documento_id=datos.documento_id,
            tipo_documento=datos.tipo_documento,
            forzar_reprocesar=datos.forzar_reprocesar or False
        )
        return resultado
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error extrayendo documento: {e}")
        raise HTTPException(status_code=500, detail="Error al extraer datos del documento")
