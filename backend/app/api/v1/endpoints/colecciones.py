"""
Endpoints para gestion de colecciones del corpus RAG.

Las colecciones son agrupaciones tematicas transversales de documentos.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from pydantic import BaseModel, Field

from app.db.session import get_db
from app.db.models.corpus import Coleccion, DocumentoColeccion
from app.db.models.legal import Documento


router = APIRouter()


# ============================================================================
# SCHEMAS
# ============================================================================

class ColeccionBase(BaseModel):
    """Schema base para coleccion."""
    codigo: str = Field(..., min_length=1, max_length=50)
    nombre: str = Field(..., min_length=1, max_length=255)
    descripcion: Optional[str] = None
    es_publica: bool = True
    color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    icono: Optional[str] = None


class ColeccionCreate(ColeccionBase):
    """Schema para crear coleccion."""
    pass


class ColeccionUpdate(BaseModel):
    """Schema para actualizar coleccion."""
    nombre: Optional[str] = Field(None, min_length=1, max_length=255)
    descripcion: Optional[str] = None
    es_publica: Optional[bool] = None
    color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    icono: Optional[str] = None


class ColeccionResponse(ColeccionBase):
    """Schema de respuesta para coleccion."""
    id: int
    orden: int
    cantidad_documentos: int = 0

    class Config:
        from_attributes = True


class ColeccionDetalleResponse(ColeccionResponse):
    """Respuesta completa con documentos."""
    documentos: List[dict] = []


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get(
    "/",
    response_model=List[ColeccionResponse],
    summary="Listar colecciones",
    description="Lista todas las colecciones del corpus."
)
async def listar_colecciones(
    solo_publicas: bool = Query(True, description="Solo colecciones publicas"),
    db: AsyncSession = Depends(get_db),
) -> List[ColeccionResponse]:
    """Lista colecciones."""
    query = select(Coleccion)

    if solo_publicas:
        query = query.where(Coleccion.es_publica == True)

    query = query.order_by(Coleccion.orden, Coleccion.nombre)

    result = await db.execute(query)
    colecciones = result.scalars().all()

    # Agregar conteo de documentos
    respuestas = []
    for col in colecciones:
        count_result = await db.execute(
            select(func.count(DocumentoColeccion.documento_id))
            .where(DocumentoColeccion.coleccion_id == col.id)
        )
        cantidad = count_result.scalar() or 0

        respuestas.append(ColeccionResponse(
            id=col.id,
            codigo=col.codigo,
            nombre=col.nombre,
            descripcion=col.descripcion,
            es_publica=col.es_publica,
            color=col.color,
            icono=col.icono,
            orden=col.orden,
            cantidad_documentos=cantidad,
        ))

    return respuestas


@router.post(
    "/",
    response_model=ColeccionResponse,
    status_code=201,
    summary="Crear coleccion",
    description="Crea una nueva coleccion."
)
async def crear_coleccion(
    coleccion: ColeccionCreate,
    db: AsyncSession = Depends(get_db),
) -> ColeccionResponse:
    """Crea una nueva coleccion."""
    # Verificar codigo unico
    existe = await db.execute(
        select(Coleccion).where(Coleccion.codigo == coleccion.codigo)
    )
    if existe.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail=f"Ya existe una coleccion con codigo '{coleccion.codigo}'"
        )

    # Calcular orden
    orden_result = await db.execute(
        select(func.coalesce(func.max(Coleccion.orden), 0) + 1)
    )
    orden = orden_result.scalar()

    nueva = Coleccion(
        codigo=coleccion.codigo,
        nombre=coleccion.nombre,
        descripcion=coleccion.descripcion,
        es_publica=coleccion.es_publica,
        color=coleccion.color,
        icono=coleccion.icono,
        orden=orden,
    )
    db.add(nueva)
    await db.commit()
    await db.refresh(nueva)

    return ColeccionResponse(
        id=nueva.id,
        codigo=nueva.codigo,
        nombre=nueva.nombre,
        descripcion=nueva.descripcion,
        es_publica=nueva.es_publica,
        color=nueva.color,
        icono=nueva.icono,
        orden=nueva.orden,
        cantidad_documentos=0,
    )


@router.get(
    "/{coleccion_id}",
    response_model=ColeccionDetalleResponse,
    summary="Obtener coleccion",
    description="Obtiene una coleccion con sus documentos."
)
async def obtener_coleccion(
    coleccion_id: int,
    limite_documentos: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> ColeccionDetalleResponse:
    """Obtiene una coleccion con sus documentos."""
    coleccion = await db.get(Coleccion, coleccion_id)
    if not coleccion:
        raise HTTPException(status_code=404, detail="Coleccion no encontrada")

    # Obtener documentos
    docs_result = await db.execute(
        select(Documento, DocumentoColeccion.orden, DocumentoColeccion.notas)
        .join(DocumentoColeccion, Documento.id == DocumentoColeccion.documento_id)
        .where(DocumentoColeccion.coleccion_id == coleccion_id)
        .order_by(DocumentoColeccion.orden, Documento.titulo)
        .limit(limite_documentos)
    )
    docs_data = docs_result.fetchall()

    # Contar total
    total_result = await db.execute(
        select(func.count(DocumentoColeccion.documento_id))
        .where(DocumentoColeccion.coleccion_id == coleccion_id)
    )
    total = total_result.scalar() or 0

    return ColeccionDetalleResponse(
        id=coleccion.id,
        codigo=coleccion.codigo,
        nombre=coleccion.nombre,
        descripcion=coleccion.descripcion,
        es_publica=coleccion.es_publica,
        color=coleccion.color,
        icono=coleccion.icono,
        orden=coleccion.orden,
        cantidad_documentos=total,
        documentos=[
            {
                "id": doc.id,
                "titulo": doc.titulo,
                "tipo": doc.tipo,
                "estado": doc.estado,
                "orden_en_coleccion": orden,
                "notas": notas,
            }
            for doc, orden, notas in docs_data
        ],
    )


@router.put(
    "/{coleccion_id}",
    response_model=ColeccionResponse,
    summary="Actualizar coleccion",
    description="Actualiza una coleccion existente."
)
async def actualizar_coleccion(
    coleccion_id: int,
    datos: ColeccionUpdate,
    db: AsyncSession = Depends(get_db),
) -> ColeccionResponse:
    """Actualiza una coleccion."""
    coleccion = await db.get(Coleccion, coleccion_id)
    if not coleccion:
        raise HTTPException(status_code=404, detail="Coleccion no encontrada")

    update_data = datos.model_dump(exclude_unset=True)
    for campo, valor in update_data.items():
        setattr(coleccion, campo, valor)

    await db.commit()
    await db.refresh(coleccion)

    # Contar documentos
    count_result = await db.execute(
        select(func.count(DocumentoColeccion.documento_id))
        .where(DocumentoColeccion.coleccion_id == coleccion.id)
    )
    cantidad = count_result.scalar() or 0

    return ColeccionResponse(
        id=coleccion.id,
        codigo=coleccion.codigo,
        nombre=coleccion.nombre,
        descripcion=coleccion.descripcion,
        es_publica=coleccion.es_publica,
        color=coleccion.color,
        icono=coleccion.icono,
        orden=coleccion.orden,
        cantidad_documentos=cantidad,
    )


@router.delete(
    "/{coleccion_id}",
    status_code=204,
    summary="Eliminar coleccion",
    description="Elimina una coleccion (no elimina los documentos)."
)
async def eliminar_coleccion(
    coleccion_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Elimina una coleccion."""
    coleccion = await db.get(Coleccion, coleccion_id)
    if not coleccion:
        raise HTTPException(status_code=404, detail="Coleccion no encontrada")

    await db.delete(coleccion)
    await db.commit()


@router.post(
    "/{coleccion_id}/documentos/{documento_id}",
    status_code=201,
    summary="Agregar documento a coleccion",
    description="Agrega un documento a una coleccion."
)
async def agregar_documento_coleccion(
    coleccion_id: int,
    documento_id: int,
    notas: Optional[str] = Query(None, description="Notas sobre el documento en la coleccion"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Agrega documento a coleccion."""
    # Verificar existencia
    coleccion = await db.get(Coleccion, coleccion_id)
    if not coleccion:
        raise HTTPException(status_code=404, detail="Coleccion no encontrada")

    documento = await db.get(Documento, documento_id)
    if not documento:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    # Verificar no existe ya
    existe = await db.execute(
        select(DocumentoColeccion).where(
            DocumentoColeccion.coleccion_id == coleccion_id,
            DocumentoColeccion.documento_id == documento_id,
        )
    )
    if existe.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="El documento ya esta en la coleccion")

    # Calcular orden
    orden_result = await db.execute(
        select(func.coalesce(func.max(DocumentoColeccion.orden), 0) + 1)
        .where(DocumentoColeccion.coleccion_id == coleccion_id)
    )
    orden = orden_result.scalar()

    relacion = DocumentoColeccion(
        coleccion_id=coleccion_id,
        documento_id=documento_id,
        orden=orden,
        notas=notas,
    )
    db.add(relacion)
    await db.commit()

    return {
        "mensaje": "Documento agregado a coleccion",
        "coleccion": {"id": coleccion.id, "nombre": coleccion.nombre},
        "documento": {"id": documento.id, "titulo": documento.titulo},
    }


@router.delete(
    "/{coleccion_id}/documentos/{documento_id}",
    status_code=204,
    summary="Quitar documento de coleccion",
    description="Quita un documento de una coleccion."
)
async def quitar_documento_coleccion(
    coleccion_id: int,
    documento_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Quita documento de coleccion."""
    result = await db.execute(
        delete(DocumentoColeccion).where(
            DocumentoColeccion.coleccion_id == coleccion_id,
            DocumentoColeccion.documento_id == documento_id,
        )
    )

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Documento no encontrado en la coleccion")

    await db.commit()
