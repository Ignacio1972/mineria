"""
Endpoints para gestion de documentos y documentación requerida SEA.
"""
import hashlib
import aiofiles
from uuid import UUID, uuid4
from pathlib import Path
from typing import Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.db.models import Proyecto, DocumentoProyecto
from app.schemas.documento import (
    DocumentoResponse,
    DocumentoListResponse,
    CategoriaDocumento,
    CategoriaDocumentoSEA,
    DocumentosRequeridosResponse,
    ValidacionCompletitudResponse,
    ValidacionCartografiaResponse,
    RequerimientoDocumentoResponse,
)
from app.services.documentacion import DocumentacionService, ValidadorCartografia
from app.core.config import settings

router = APIRouter()

# Configuracion
UPLOAD_DIR = Path(getattr(settings, 'UPLOAD_DIR', '/var/www/mineria/uploads'))
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/jpg",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/zip",
    "application/x-zip-compressed",
    # Formatos GIS
    "application/geo+json",
    "application/vnd.google-earth.kml+xml",
    "application/gml+xml",
}

# Extensiones GIS permitidas
GIS_EXTENSIONS = {".shp", ".geojson", ".json", ".kml", ".gml", ".zip"}


@router.post("/proyectos/{proyecto_id}/documentos", response_model=DocumentoResponse, status_code=201)
async def subir_documento(
    proyecto_id: int,
    archivo: UploadFile = File(...),
    nombre: str = Form(...),
    categoria: CategoriaDocumento = Form(CategoriaDocumento.OTRO),
    categoria_sea: Optional[CategoriaDocumentoSEA] = Form(None),
    descripcion: Optional[str] = Form(None),
    profesional_responsable: Optional[str] = Form(None),
    fecha_documento: Optional[date] = Form(None),
    fecha_vigencia: Optional[date] = Form(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Subir documento a un proyecto.

    - **categoria**: Categoría legacy (legal, tecnico, ambiental, cartografia, otro)
    - **categoria_sea**: Categoría específica SEA (cartografia_planos, estudio_aire, etc.)
    - **profesional_responsable**: Nombre del profesional responsable del documento
    - **fecha_documento**: Fecha del documento
    - **fecha_vigencia**: Fecha de vigencia (para certificados)
    """
    # Verificar proyecto
    result = await db.execute(select(Proyecto).where(Proyecto.id == proyecto_id))
    proyecto = result.scalar()

    if not proyecto:
        raise HTTPException(404, "Proyecto no encontrado")

    if proyecto.estado == "archivado":
        raise HTTPException(400, "No se pueden agregar documentos a proyectos archivados")

    # Validar tipo de archivo
    extension = Path(archivo.filename).suffix.lower() if archivo.filename else ""

    # Permitir archivos GIS aunque el MIME type sea genérico
    is_gis_file = extension in GIS_EXTENSIONS
    if not is_gis_file and archivo.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            400,
            f"Tipo de archivo no permitido: {archivo.content_type}. "
            f"Permitidos: PDF, PNG, JPG, DOC, DOCX, XLS, XLSX, ZIP, GeoJSON, KML, GML"
        )

    # Leer contenido para validar tamano
    content = await archivo.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(400, f"Archivo demasiado grande. Maximo: {MAX_FILE_SIZE // (1024*1024)}MB")

    # Crear directorio del proyecto
    proyecto_dir = UPLOAD_DIR / str(proyecto_id)
    proyecto_dir.mkdir(parents=True, exist_ok=True)

    # Generar nombre unico
    doc_id = uuid4()
    archivo_path = proyecto_dir / f"{doc_id}{extension}"

    # Guardar archivo
    async with aiofiles.open(archivo_path, 'wb') as f:
        await f.write(content)

    # Calcular checksum
    checksum = hashlib.sha256(content).hexdigest()

    # Auto-detectar categoria_sea si es cartografía
    if not categoria_sea and (is_gis_file or categoria == CategoriaDocumento.CARTOGRAFIA):
        categoria_sea = CategoriaDocumentoSEA.CARTOGRAFIA_PLANOS

    # Crear registro en BD
    documento = DocumentoProyecto(
        id=doc_id,
        proyecto_id=proyecto_id,
        nombre=nombre,
        nombre_original=archivo.filename or "archivo",
        categoria=categoria.value,
        categoria_sea=categoria_sea.value if categoria_sea else "otro",
        descripcion=descripcion,
        archivo_path=str(archivo_path),
        mime_type=archivo.content_type,
        tamano_bytes=len(content),
        checksum_sha256=checksum,
        profesional_responsable=profesional_responsable,
        fecha_documento=fecha_documento,
        fecha_vigencia=fecha_vigencia,
    )

    db.add(documento)
    await db.commit()
    await db.refresh(documento)

    # Validar cartografía automáticamente si es archivo GIS
    if is_gis_file or categoria_sea == CategoriaDocumentoSEA.CARTOGRAFIA_PLANOS:
        try:
            validador = ValidadorCartografia(db)
            await validador.validar_documento(doc_id)
        except Exception as e:
            # No fallar el upload por error de validación
            pass

    return _documento_to_response(documento)


@router.get("/proyectos/{proyecto_id}/documentos", response_model=DocumentoListResponse)
async def listar_documentos_proyecto(
    proyecto_id: int,
    categoria: Optional[CategoriaDocumento] = Query(None),
    categoria_sea: Optional[CategoriaDocumentoSEA] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Listar documentos de un proyecto.

    Filtros opcionales:
    - **categoria**: Filtrar por categoría legacy
    - **categoria_sea**: Filtrar por categoría SEA específica
    """
    # Verificar proyecto
    result = await db.execute(select(Proyecto).where(Proyecto.id == proyecto_id))
    if not result.scalar():
        raise HTTPException(404, "Proyecto no encontrado")

    query = select(DocumentoProyecto).where(DocumentoProyecto.proyecto_id == proyecto_id)

    if categoria:
        query = query.where(DocumentoProyecto.categoria == categoria.value)

    if categoria_sea:
        query = query.where(DocumentoProyecto.categoria_sea == categoria_sea.value)

    query = query.order_by(DocumentoProyecto.created_at.desc())

    result = await db.execute(query)
    documentos = result.scalars().all()

    total_bytes = sum(d.tamano_bytes for d in documentos)

    items = [_documento_to_response(d) for d in documentos]

    return DocumentoListResponse(
        items=items,
        total=len(documentos),
        total_bytes=total_bytes,
        total_mb=round(total_bytes / (1024 * 1024), 2),
    )


@router.get("/proyectos/{proyecto_id}/requeridos", response_model=DocumentosRequeridosResponse)
async def obtener_documentos_requeridos(
    proyecto_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Obtener lista de documentos requeridos para un proyecto según SEA.

    Retorna todos los documentos requeridos para el tipo de proyecto,
    indicando cuáles son obligatorios según la vía de evaluación (DIA/EIA)
    y cuáles ya han sido subidos.
    """
    service = DocumentacionService(db)
    try:
        return await service.obtener_documentos_requeridos(proyecto_id)
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.get("/proyectos/{proyecto_id}/validar-completitud", response_model=ValidacionCompletitudResponse)
async def validar_completitud_documentacion(
    proyecto_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Validar completitud de documentación de un proyecto.

    Verifica qué documentos obligatorios faltan y retorna:
    - Porcentaje de completitud
    - Lista de documentos obligatorios faltantes
    - Lista de documentos opcionales faltantes
    - Alertas y recomendaciones
    - Indicador de si puede continuar con el análisis
    """
    service = DocumentacionService(db)
    try:
        return await service.validar_completitud(proyecto_id)
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.get("/proyectos/{proyecto_id}/documentos-por-seccion")
async def obtener_documentos_por_seccion(
    proyecto_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Obtener documentos requeridos agrupados por sección del EIA.

    Útil para mostrar el progreso por capítulo del estudio.
    """
    service = DocumentacionService(db)
    try:
        return await service.obtener_resumen_por_seccion(proyecto_id)
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.post("/{documento_id}/vincular-categoria")
async def vincular_documento_categoria(
    documento_id: UUID,
    categoria_sea: CategoriaDocumentoSEA,
    db: AsyncSession = Depends(get_db),
):
    """
    Vincular un documento existente a una categoría SEA específica.

    Útil cuando se sube un documento sin categoría y luego se quiere
    asignar a un requerimiento específico.
    """
    service = DocumentacionService(db)
    try:
        documento = await service.vincular_documento_a_categoria(
            documento_id,
            categoria_sea.value
        )
        return _documento_to_response(documento)
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.post("/proyectos/{proyecto_id}/marcar-no-aplica")
async def marcar_documento_no_aplica(
    proyecto_id: int,
    categoria_sea: CategoriaDocumentoSEA,
    observaciones: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Marcar una categoría de documento como 'no aplica' para el proyecto.

    Útil cuando un documento requerido no es aplicable al proyecto específico.
    Debe incluir una justificación en observaciones.
    """
    service = DocumentacionService(db)
    try:
        validacion = await service.marcar_no_aplica(
            proyecto_id,
            categoria_sea.value,
            observaciones
        )
        return {
            "mensaje": f"Categoría {categoria_sea.value} marcada como 'no aplica'",
            "estado": validacion.estado
        }
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.post("/{documento_id}/validar-cartografia", response_model=ValidacionCartografiaResponse)
async def validar_cartografia_documento(
    documento_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Validar un documento de cartografía.

    Verifica:
    - Formato del archivo (Shapefile, GeoJSON, KML, GML)
    - Sistema de referencia (debe ser WGS84/EPSG:4326)
    - Estructura del archivo
    - Número de features
    - Bounding box
    - Área total (para polígonos)
    """
    validador = ValidadorCartografia(db)
    resultado = await validador.validar_documento(documento_id)

    if not resultado.valido and "no encontrado" in str(resultado.errores):
        raise HTTPException(404, "Documento no encontrado")

    return resultado


@router.get("/{documento_id}/descargar")
async def descargar_documento(
    documento_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Descargar documento."""
    result = await db.execute(select(DocumentoProyecto).where(DocumentoProyecto.id == documento_id))
    documento = result.scalar()

    if not documento:
        raise HTTPException(404, "Documento no encontrado")

    archivo_path = Path(documento.archivo_path)
    if not archivo_path.exists():
        raise HTTPException(404, "Archivo no encontrado en el servidor")

    return FileResponse(
        path=archivo_path,
        filename=documento.nombre_original,
        media_type=documento.mime_type,
    )


@router.delete("/{documento_id}", status_code=204)
async def eliminar_documento(
    documento_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Eliminar documento."""
    result = await db.execute(select(DocumentoProyecto).where(DocumentoProyecto.id == documento_id))
    documento = result.scalar()

    if not documento:
        raise HTTPException(404, "Documento no encontrado")

    # Verificar que proyecto no este archivado
    proyecto_result = await db.execute(
        select(Proyecto).where(Proyecto.id == documento.proyecto_id)
    )
    proyecto = proyecto_result.scalar()

    if proyecto and proyecto.estado == "archivado":
        raise HTTPException(400, "No se pueden eliminar documentos de proyectos archivados")

    # Eliminar archivo fisico
    archivo_path = Path(documento.archivo_path)
    if archivo_path.exists():
        archivo_path.unlink()

    # Eliminar registro
    await db.delete(documento)
    await db.commit()


@router.patch("/{documento_id}", response_model=DocumentoResponse)
async def actualizar_documento(
    documento_id: UUID,
    nombre: Optional[str] = Form(None),
    categoria_sea: Optional[CategoriaDocumentoSEA] = Form(None),
    descripcion: Optional[str] = Form(None),
    profesional_responsable: Optional[str] = Form(None),
    fecha_documento: Optional[date] = Form(None),
    fecha_vigencia: Optional[date] = Form(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Actualizar metadatos de un documento.

    Permite actualizar nombre, categoría SEA, descripción,
    profesional responsable y fechas.
    """
    result = await db.execute(select(DocumentoProyecto).where(DocumentoProyecto.id == documento_id))
    documento = result.scalar()

    if not documento:
        raise HTTPException(404, "Documento no encontrado")

    if nombre is not None:
        documento.nombre = nombre
    if categoria_sea is not None:
        documento.categoria_sea = categoria_sea.value
    if descripcion is not None:
        documento.descripcion = descripcion
    if profesional_responsable is not None:
        documento.profesional_responsable = profesional_responsable
    if fecha_documento is not None:
        documento.fecha_documento = fecha_documento
    if fecha_vigencia is not None:
        documento.fecha_vigencia = fecha_vigencia

    await db.commit()
    await db.refresh(documento)

    return _documento_to_response(documento)


def _documento_to_response(documento: DocumentoProyecto) -> DocumentoResponse:
    """Convierte un documento a su respuesta."""
    return DocumentoResponse(
        id=documento.id,
        proyecto_id=documento.proyecto_id,
        nombre=documento.nombre,
        nombre_original=documento.nombre_original,
        categoria=documento.categoria,
        categoria_sea=documento.categoria_sea,
        descripcion=documento.descripcion,
        archivo_path=documento.archivo_path,
        mime_type=documento.mime_type,
        tamano_bytes=documento.tamano_bytes,
        tamano_mb=round(documento.tamano_bytes / (1024 * 1024), 2),
        checksum_sha256=documento.checksum_sha256,
        num_paginas=documento.num_paginas,
        validacion_formato=documento.validacion_formato,
        profesional_responsable=documento.profesional_responsable,
        fecha_documento=documento.fecha_documento,
        fecha_vigencia=documento.fecha_vigencia,
        esta_vigente=documento.esta_vigente if hasattr(documento, 'esta_vigente') else True,
        created_at=documento.created_at,
    )
