"""
Endpoints para gestion de documentos.
"""
import hashlib
import aiofiles
from uuid import UUID, uuid4
from pathlib import Path
from typing import Optional
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
)
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
}


@router.post("/proyectos/{proyecto_id}/documentos", response_model=DocumentoResponse, status_code=201)
async def subir_documento(
    proyecto_id: int,
    archivo: UploadFile = File(...),
    nombre: str = Form(...),
    categoria: CategoriaDocumento = Form(CategoriaDocumento.OTRO),
    descripcion: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
):
    """Subir documento a un proyecto."""
    # Verificar proyecto
    result = await db.execute(select(Proyecto).where(Proyecto.id == proyecto_id))
    proyecto = result.scalar()

    if not proyecto:
        raise HTTPException(404, "Proyecto no encontrado")

    if proyecto.estado == "archivado":
        raise HTTPException(400, "No se pueden agregar documentos a proyectos archivados")

    # Validar tipo de archivo
    if archivo.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            400,
            f"Tipo de archivo no permitido: {archivo.content_type}. "
            f"Permitidos: PDF, PNG, JPG, DOC, DOCX, XLS, XLSX, ZIP"
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
    extension = Path(archivo.filename).suffix if archivo.filename else ""
    archivo_path = proyecto_dir / f"{doc_id}{extension}"

    # Guardar archivo
    async with aiofiles.open(archivo_path, 'wb') as f:
        await f.write(content)

    # Calcular checksum
    checksum = hashlib.sha256(content).hexdigest()

    # Crear registro en BD
    documento = DocumentoProyecto(
        id=doc_id,
        proyecto_id=proyecto_id,
        nombre=nombre,
        nombre_original=archivo.filename or "archivo",
        categoria=categoria.value,
        descripcion=descripcion,
        archivo_path=str(archivo_path),
        mime_type=archivo.content_type,
        tamano_bytes=len(content),
        checksum_sha256=checksum,
    )

    db.add(documento)
    await db.commit()
    await db.refresh(documento)

    return DocumentoResponse.model_validate({
        "id": documento.id,
        "proyecto_id": documento.proyecto_id,
        "nombre": documento.nombre,
        "nombre_original": documento.nombre_original,
        "categoria": documento.categoria,
        "descripcion": documento.descripcion,
        "archivo_path": documento.archivo_path,
        "mime_type": documento.mime_type,
        "tamano_bytes": documento.tamano_bytes,
        "tamano_mb": round(documento.tamano_bytes / (1024 * 1024), 2),
        "checksum_sha256": documento.checksum_sha256,
        "created_at": documento.created_at,
    })


@router.get("/proyectos/{proyecto_id}/documentos", response_model=DocumentoListResponse)
async def listar_documentos_proyecto(
    proyecto_id: int,
    categoria: Optional[CategoriaDocumento] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Listar documentos de un proyecto."""
    # Verificar proyecto
    result = await db.execute(select(Proyecto).where(Proyecto.id == proyecto_id))
    if not result.scalar():
        raise HTTPException(404, "Proyecto no encontrado")

    query = select(DocumentoProyecto).where(DocumentoProyecto.proyecto_id == proyecto_id)

    if categoria:
        query = query.where(DocumentoProyecto.categoria == categoria.value)

    query = query.order_by(DocumentoProyecto.created_at.desc())

    result = await db.execute(query)
    documentos = result.scalars().all()

    total_bytes = sum(d.tamano_bytes for d in documentos)

    items = [
        DocumentoResponse.model_validate({
            "id": d.id,
            "proyecto_id": d.proyecto_id,
            "nombre": d.nombre,
            "nombre_original": d.nombre_original,
            "categoria": d.categoria,
            "descripcion": d.descripcion,
            "archivo_path": d.archivo_path,
            "mime_type": d.mime_type,
            "tamano_bytes": d.tamano_bytes,
            "tamano_mb": round(d.tamano_bytes / (1024 * 1024), 2),
            "checksum_sha256": d.checksum_sha256,
            "created_at": d.created_at,
        })
        for d in documentos
    ]

    return DocumentoListResponse(
        items=items,
        total=len(documentos),
        total_bytes=total_bytes,
        total_mb=round(total_bytes / (1024 * 1024), 2),
    )


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
