"""
Endpoints API para Generación de EIA (Fase 4).

Proporciona endpoints para compilar, generar, validar y exportar documentos EIA.
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.generacion_eia import GeneracionEIAService
from app.schemas.generacion_eia import (
    # Requests
    CompilarDocumentoRequest,
    GenerarCapituloRequest,
    RegenerarSeccionRequest,
    VersionEIACreate,
    ValidacionRequest,
    ExportacionRequest,
    DocumentoEIAUpdate,
    # Responses
    DocumentoEIAResponse,
    DocumentoCompletoResponse,
    GeneracionResponse,
    ContenidoCapitulo,
    VersionEIAResponse,
    ResultadoValidacion,
    ExportacionResponse,
    ProgresoGeneracion,
    # Enums
    FormatoExportacionEnum,
    SeveridadEnum
)

router = APIRouter()

# Instancia del servicio
generacion_service = GeneracionEIAService()


# =============================================================================
# ENDPOINTS DE DOCUMENTO
# =============================================================================

@router.post(
    "/{proyecto_id}/compilar",
    response_model=GeneracionResponse,
    summary="Compilar documento EIA completo",
    description="Genera todos los capítulos del EIA para un proyecto. "
                "Puede regenerar capítulos existentes si se especifica."
)
async def compilar_documento(
    proyecto_id: int,
    request: CompilarDocumentoRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Compila un documento EIA completo generando todos los capítulos.

    - **proyecto_id**: ID del proyecto
    - **incluir_capitulos**: Lista de capítulos a generar (1-11). Si no se especifica, genera todos.
    - **regenerar_existentes**: Si True, regenera capítulos que ya existen.
    """
    try:
        resultado = await generacion_service.compilar_documento(
            db=db,
            proyecto_id=proyecto_id,
            request=request
        )
        return resultado
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al compilar documento: {str(e)}")


@router.post(
    "/{proyecto_id}/capitulo/{capitulo_num}",
    response_model=ContenidoCapitulo,
    summary="Generar capítulo específico",
    description="Genera un capítulo específico del EIA usando IA."
)
async def generar_capitulo(
    proyecto_id: int,
    capitulo_num: int,
    regenerar: bool = Query(False, description="Regenerar aunque ya exista"),
    instrucciones: Optional[str] = Query(None, description="Instrucciones adicionales"),
    db: AsyncSession = Depends(get_db)
):
    """
    Genera un capítulo específico del EIA.

    - **proyecto_id**: ID del proyecto
    - **capitulo_num**: Número del capítulo (1-11)
    - **regenerar**: Si True, regenera aunque el capítulo ya exista
    - **instrucciones**: Instrucciones adicionales para la generación
    """
    if capitulo_num < 1 or capitulo_num > 11:
        raise HTTPException(
            status_code=400,
            detail="El número de capítulo debe estar entre 1 y 11"
        )

    try:
        resultado = await generacion_service.generar_capitulo(
            db=db,
            proyecto_id=proyecto_id,
            capitulo_numero=capitulo_num,
            instrucciones_adicionales=instrucciones,
            regenerar=regenerar
        )
        return resultado
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar capítulo: {str(e)}")


@router.post(
    "/{proyecto_id}/regenerar",
    response_model=dict,
    summary="Regenerar sección específica",
    description="Regenera una sección específica de un capítulo con instrucciones personalizadas."
)
async def regenerar_seccion(
    proyecto_id: int,
    request: RegenerarSeccionRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Regenera una sección específica de un capítulo.

    - **proyecto_id**: ID del proyecto
    - **capitulo_numero**: Número del capítulo
    - **seccion_codigo**: Código de la sección a regenerar
    - **instrucciones**: Instrucciones para la regeneración
    """
    try:
        texto = await generacion_service.regenerar_seccion(
            db=db,
            proyecto_id=proyecto_id,
            request=request
        )
        return {"texto_regenerado": texto}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al regenerar sección: {str(e)}")


@router.get(
    "/{proyecto_id}/documento",
    response_model=DocumentoEIAResponse,
    summary="Obtener documento EIA",
    description="Obtiene el documento EIA actual de un proyecto."
)
async def get_documento(
    proyecto_id: int,
    version: Optional[int] = Query(None, description="Versión específica (null = última)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Obtiene el documento EIA de un proyecto.

    - **proyecto_id**: ID del proyecto
    - **version**: Versión específica a obtener (opcional, default = última)
    """
    try:
        documento = await generacion_service.get_documento(
            db=db,
            proyecto_id=proyecto_id,
            version=version
        )

        if not documento:
            raise HTTPException(
                status_code=404,
                detail=f"No existe documento EIA para el proyecto {proyecto_id}"
            )

        return documento
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener documento: {str(e)}")


@router.get(
    "/{proyecto_id}/documento/completo",
    response_model=DocumentoCompletoResponse,
    summary="Obtener documento completo con relaciones",
    description="Obtiene el documento EIA con todas sus relaciones (versiones, exportaciones, observaciones)."
)
async def get_documento_completo(
    proyecto_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Obtiene el documento EIA completo con todas sus relaciones.

    - **proyecto_id**: ID del proyecto
    """
    try:
        documento = await generacion_service.get_documento_completo(
            db=db,
            proyecto_id=proyecto_id
        )

        if not documento:
            raise HTTPException(
                status_code=404,
                detail=f"No existe documento EIA para el proyecto {proyecto_id}"
            )

        return documento
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener documento: {str(e)}")


@router.patch(
    "/{proyecto_id}/documento",
    response_model=DocumentoEIAResponse,
    summary="Actualizar documento EIA",
    description="Actualiza los datos de un documento EIA existente."
)
async def actualizar_documento(
    proyecto_id: int,
    update_data: DocumentoEIAUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Actualiza los datos de un documento EIA.

    - **proyecto_id**: ID del proyecto
    - **titulo**: Nuevo título (opcional)
    - **estado**: Nuevo estado (opcional)
    - **contenido_capitulos**: Contenido actualizado (opcional)
    - **metadatos**: Metadatos actualizados (opcional)
    """
    try:
        documento = await generacion_service.actualizar_documento(
            db=db,
            proyecto_id=proyecto_id,
            update_data=update_data
        )
        return documento
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar documento: {str(e)}")


# =============================================================================
# ENDPOINTS DE VERSIONADO
# =============================================================================

@router.post(
    "/{proyecto_id}/version",
    response_model=VersionEIAResponse,
    summary="Crear nueva versión",
    description="Crea un snapshot del documento actual como nueva versión."
)
async def crear_version(
    proyecto_id: int,
    request: VersionEIACreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Crea una nueva versión del documento (snapshot).

    - **proyecto_id**: ID del proyecto
    - **cambios**: Descripción de los cambios realizados
    - **creado_por**: Usuario que crea la versión (opcional)
    """
    try:
        version = await generacion_service.crear_version(
            db=db,
            proyecto_id=proyecto_id,
            cambios=request.cambios,
            creado_por=request.creado_por
        )
        return version
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear versión: {str(e)}")


@router.get(
    "/{proyecto_id}/versiones",
    response_model=List[VersionEIAResponse],
    summary="Listar versiones",
    description="Lista todas las versiones guardadas del documento."
)
async def listar_versiones(
    proyecto_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Lista todas las versiones de un documento EIA.

    - **proyecto_id**: ID del proyecto
    """
    try:
        versiones = await generacion_service.listar_versiones(
            db=db,
            proyecto_id=proyecto_id
        )
        return versiones
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar versiones: {str(e)}")


@router.post(
    "/{proyecto_id}/restaurar/{version_num}",
    response_model=DocumentoEIAResponse,
    summary="Restaurar versión",
    description="Restaura el documento a una versión anterior."
)
async def restaurar_version(
    proyecto_id: int,
    version_num: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Restaura el documento a una versión anterior.

    - **proyecto_id**: ID del proyecto
    - **version_num**: Número de versión a restaurar
    """
    try:
        documento = await generacion_service.restaurar_version(
            db=db,
            proyecto_id=proyecto_id,
            version_a_restaurar=version_num
        )
        return documento
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al restaurar versión: {str(e)}")


# =============================================================================
# ENDPOINTS DE VALIDACIÓN
# =============================================================================

@router.post(
    "/{proyecto_id}/validar",
    response_model=ResultadoValidacion,
    summary="Validar documento contra SEA",
    description="Valida el documento EIA contra reglas del SEA/ICSARA."
)
async def validar_documento(
    proyecto_id: int,
    nivel_severidad: SeveridadEnum = Query(
        SeveridadEnum.INFO,
        description="Nivel mínimo de severidad a reportar"
    ),
    db: AsyncSession = Depends(get_db)
):
    """
    Valida el documento contra reglas SEA.

    - **proyecto_id**: ID del proyecto
    - **nivel_severidad**: Nivel mínimo de severidad (info, warning, error)
    """
    try:
        resultado = await generacion_service.validar_documento(
            db=db,
            proyecto_id=proyecto_id,
            nivel_severidad_minima=nivel_severidad
        )
        return resultado
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al validar documento: {str(e)}")


@router.get(
    "/{proyecto_id}/validaciones",
    response_model=ResultadoValidacion,
    summary="Obtener validaciones",
    description="Obtiene las últimas validaciones del documento."
)
async def get_validaciones(
    proyecto_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Obtiene las validaciones del documento.

    - **proyecto_id**: ID del proyecto
    """
    try:
        # Ejecuta validación para obtener resultados actualizados
        resultado = await generacion_service.validar_documento(
            db=db,
            proyecto_id=proyecto_id,
            nivel_severidad_minima=SeveridadEnum.INFO
        )
        return resultado
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener validaciones: {str(e)}")


# =============================================================================
# ENDPOINTS DE EXPORTACIÓN
# =============================================================================

@router.post(
    "/{proyecto_id}/exportar/{formato}",
    response_model=ExportacionResponse,
    summary="Exportar documento",
    description="Exporta el documento EIA a un formato específico (PDF, DOCX, e-SEIA XML)."
)
async def exportar_documento(
    proyecto_id: int,
    formato: FormatoExportacionEnum,
    request: Optional[ExportacionRequest] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Exporta el documento a un formato específico.

    - **proyecto_id**: ID del proyecto
    - **formato**: Formato de exportación (pdf, docx, eseia_xml)
    - **configuracion**: Configuración de exportación (opcional)
    """
    try:
        config = request.configuracion if request else None

        resultado = await generacion_service.exportar(
            db=db,
            proyecto_id=proyecto_id,
            formato=formato.value,
            config=config
        )
        return resultado
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al exportar documento: {str(e)}")


@router.get(
    "/{proyecto_id}/exports",
    response_model=List[ExportacionResponse],
    summary="Listar exportaciones",
    description="Lista todas las exportaciones realizadas del documento."
)
async def listar_exportaciones(
    proyecto_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Lista todas las exportaciones de un documento.

    - **proyecto_id**: ID del proyecto
    """
    try:
        exportaciones = await generacion_service.listar_exportaciones(
            db=db,
            proyecto_id=proyecto_id
        )
        return exportaciones
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar exportaciones: {str(e)}")


@router.get(
    "/{proyecto_id}/export/{exportacion_id}",
    summary="Descargar exportación",
    description="Descarga un archivo de exportación específico."
)
async def descargar_exportacion(
    proyecto_id: int,
    exportacion_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Descarga un archivo exportado.

    - **proyecto_id**: ID del proyecto
    - **exportacion_id**: ID de la exportación
    """
    try:
        resultado = await generacion_service.exportador.get_archivo_exportacion(
            db=db,
            exportacion_id=exportacion_id
        )

        if not resultado:
            raise HTTPException(
                status_code=404,
                detail="Exportación no encontrada o archivo no disponible"
            )

        contenido, filename, content_type = resultado

        return Response(
            content=contenido,
            media_type=content_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al descargar exportación: {str(e)}")


# =============================================================================
# ENDPOINTS DE PROGRESO
# =============================================================================

@router.get(
    "/{proyecto_id}/progreso",
    response_model=List[ProgresoGeneracion],
    summary="Obtener progreso de generación",
    description="Obtiene el progreso de generación por capítulo."
)
async def get_progreso(
    proyecto_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Obtiene el progreso de generación por capítulo.

    - **proyecto_id**: ID del proyecto
    """
    try:
        progreso = await generacion_service.get_progreso_generacion(
            db=db,
            proyecto_id=proyecto_id
        )
        return progreso
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener progreso: {str(e)}")


# =============================================================================
# ENDPOINTS DE CAPÍTULOS INDIVIDUALES
# =============================================================================

@router.put(
    "/{proyecto_id}/capitulo/{capitulo_num}/contenido",
    response_model=ContenidoCapitulo,
    summary="Actualizar contenido de capítulo",
    description="Actualiza manualmente el contenido de un capítulo específico."
)
async def actualizar_capitulo(
    proyecto_id: int,
    capitulo_num: int,
    contenido: str,
    titulo: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Actualiza el contenido de un capítulo.

    - **proyecto_id**: ID del proyecto
    - **capitulo_num**: Número del capítulo (1-11)
    - **contenido**: Nuevo contenido del capítulo
    - **titulo**: Nuevo título (opcional)
    """
    if capitulo_num < 1 or capitulo_num > 11:
        raise HTTPException(
            status_code=400,
            detail="El número de capítulo debe estar entre 1 y 11"
        )

    try:
        resultado = await generacion_service.actualizar_capitulo(
            db=db,
            proyecto_id=proyecto_id,
            capitulo_numero=capitulo_num,
            contenido=contenido,
            titulo=titulo
        )
        return resultado
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar capítulo: {str(e)}")
