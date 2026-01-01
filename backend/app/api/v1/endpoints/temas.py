"""
Endpoints para gestion de temas del corpus RAG.

Los temas permiten clasificar fragmentos de documentos para
mejorar la precision de las busquedas RAG.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel, Field

from app.db.session import get_db
from app.db.models.corpus import Tema, FragmentoTema
from app.db.models.legal import Fragmento


router = APIRouter()


# ============================================================================
# SCHEMAS
# ============================================================================

class TemaBase(BaseModel):
    """Schema base para tema."""
    codigo: str = Field(..., min_length=1, max_length=50)
    nombre: str = Field(..., min_length=1, max_length=100)
    descripcion: Optional[str] = None
    grupo: Optional[str] = Field(None, max_length=50)
    keywords: Optional[List[str]] = None
    color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    icono: Optional[str] = None


class TemaCreate(TemaBase):
    """Schema para crear tema."""
    pass


class TemaUpdate(BaseModel):
    """Schema para actualizar tema."""
    nombre: Optional[str] = Field(None, min_length=1, max_length=100)
    descripcion: Optional[str] = None
    grupo: Optional[str] = None
    keywords: Optional[List[str]] = None
    color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    icono: Optional[str] = None
    activo: Optional[bool] = None


class TemaResponse(TemaBase):
    """Schema de respuesta para tema."""
    id: int
    activo: bool
    cantidad_fragmentos: int = 0

    class Config:
        from_attributes = True


class TemaEstadisticas(BaseModel):
    """Estadisticas de un tema."""
    tema_id: int
    codigo: str
    nombre: str
    cantidad_fragmentos: int
    documentos_distintos: int


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get(
    "/",
    response_model=List[TemaResponse],
    summary="Listar temas",
    description="Lista todos los temas disponibles para clasificacion."
)
async def listar_temas(
    grupo: Optional[str] = Query(None, description="Filtrar por grupo"),
    incluir_inactivos: bool = Query(False, description="Incluir temas desactivados"),
    db: AsyncSession = Depends(get_db),
) -> List[TemaResponse]:
    """Lista temas con conteo de fragmentos."""
    query = select(Tema)

    if grupo:
        query = query.where(Tema.grupo == grupo)

    if not incluir_inactivos:
        query = query.where(Tema.activo == True)

    query = query.order_by(Tema.grupo, Tema.nombre)

    result = await db.execute(query)
    temas = result.scalars().all()

    # Agregar conteo de fragmentos
    respuestas = []
    for tema in temas:
        count_result = await db.execute(
            select(func.count(FragmentoTema.fragmento_id))
            .where(FragmentoTema.tema_id == tema.id)
        )
        cantidad = count_result.scalar() or 0

        respuestas.append(TemaResponse(
            id=tema.id,
            codigo=tema.codigo,
            nombre=tema.nombre,
            descripcion=tema.descripcion,
            grupo=tema.grupo,
            keywords=tema.keywords,
            color=tema.color,
            icono=tema.icono,
            activo=tema.activo,
            cantidad_fragmentos=cantidad,
        ))

    return respuestas


@router.get(
    "/grupos",
    summary="Listar grupos de temas",
    description="Lista los grupos de temas disponibles."
)
async def listar_grupos_temas(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Lista grupos de temas con conteo."""
    result = await db.execute(
        select(Tema.grupo, func.count(Tema.id))
        .where(Tema.activo == True)
        .group_by(Tema.grupo)
        .order_by(Tema.grupo)
    )
    grupos = result.fetchall()

    return {
        "grupos": [
            {"grupo": g[0] or "sin_grupo", "cantidad_temas": g[1]}
            for g in grupos
        ],
        "descripciones": {
            "componente_ambiental": "Agua, aire, suelo, flora, fauna, glaciares",
            "patrimonio": "Arqueologico, paleontologico",
            "social": "Pueblos indigenas, comunidades",
            "procedimiento": "PAC, seguimiento, fiscalizacion",
            "territorio": "Areas protegidas, zonas especiales",
            "instrumento": "DIA, EIA, RCA",
            "sector": "Mineria, energia, otros",
            "metodologia": "Impactos, linea base, medidas",
        },
    }


@router.post(
    "/",
    response_model=TemaResponse,
    status_code=201,
    summary="Crear tema",
    description="Crea un nuevo tema para clasificacion."
)
async def crear_tema(
    tema: TemaCreate,
    db: AsyncSession = Depends(get_db),
) -> TemaResponse:
    """Crea un nuevo tema."""
    # Verificar codigo unico
    existe = await db.execute(
        select(Tema).where(Tema.codigo == tema.codigo)
    )
    if existe.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail=f"Ya existe un tema con codigo '{tema.codigo}'"
        )

    nuevo = Tema(
        codigo=tema.codigo,
        nombre=tema.nombre,
        descripcion=tema.descripcion,
        grupo=tema.grupo,
        keywords=tema.keywords or [],
        color=tema.color,
        icono=tema.icono,
    )
    db.add(nuevo)
    await db.commit()
    await db.refresh(nuevo)

    return TemaResponse(
        id=nuevo.id,
        codigo=nuevo.codigo,
        nombre=nuevo.nombre,
        descripcion=nuevo.descripcion,
        grupo=nuevo.grupo,
        keywords=nuevo.keywords,
        color=nuevo.color,
        icono=nuevo.icono,
        activo=nuevo.activo,
        cantidad_fragmentos=0,
    )


@router.get(
    "/estadisticas",
    response_model=List[TemaEstadisticas],
    summary="Estadisticas de temas",
    description="Obtiene estadisticas de uso de cada tema."
)
async def estadisticas_temas(
    db: AsyncSession = Depends(get_db),
) -> List[TemaEstadisticas]:
    """Obtiene estadisticas de temas."""
    # Query con conteos
    result = await db.execute(
        select(
            Tema.id,
            Tema.codigo,
            Tema.nombre,
            func.count(FragmentoTema.fragmento_id).label("cantidad_fragmentos"),
            func.count(func.distinct(Fragmento.documento_id)).label("documentos_distintos"),
        )
        .outerjoin(FragmentoTema, Tema.id == FragmentoTema.tema_id)
        .outerjoin(Fragmento, FragmentoTema.fragmento_id == Fragmento.id)
        .where(Tema.activo == True)
        .group_by(Tema.id, Tema.codigo, Tema.nombre)
        .order_by(func.count(FragmentoTema.fragmento_id).desc())
    )
    rows = result.fetchall()

    return [
        TemaEstadisticas(
            tema_id=row[0],
            codigo=row[1],
            nombre=row[2],
            cantidad_fragmentos=row[3] or 0,
            documentos_distintos=row[4] or 0,
        )
        for row in rows
    ]


@router.get(
    "/{tema_id}",
    response_model=TemaResponse,
    summary="Obtener tema",
    description="Obtiene un tema por ID."
)
async def obtener_tema(
    tema_id: int,
    db: AsyncSession = Depends(get_db),
) -> TemaResponse:
    """Obtiene un tema."""
    tema = await db.get(Tema, tema_id)
    if not tema:
        raise HTTPException(status_code=404, detail="Tema no encontrado")

    count_result = await db.execute(
        select(func.count(FragmentoTema.fragmento_id))
        .where(FragmentoTema.tema_id == tema.id)
    )
    cantidad = count_result.scalar() or 0

    return TemaResponse(
        id=tema.id,
        codigo=tema.codigo,
        nombre=tema.nombre,
        descripcion=tema.descripcion,
        grupo=tema.grupo,
        keywords=tema.keywords,
        color=tema.color,
        icono=tema.icono,
        activo=tema.activo,
        cantidad_fragmentos=cantidad,
    )


@router.get(
    "/{tema_id}/fragmentos",
    summary="Fragmentos de un tema",
    description="Lista fragmentos clasificados con un tema."
)
async def listar_fragmentos_tema(
    tema_id: int,
    limite: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Lista fragmentos de un tema."""
    tema = await db.get(Tema, tema_id)
    if not tema:
        raise HTTPException(status_code=404, detail="Tema no encontrado")

    # Contar total
    total_result = await db.execute(
        select(func.count(FragmentoTema.fragmento_id))
        .where(FragmentoTema.tema_id == tema_id)
    )
    total = total_result.scalar() or 0

    # Obtener fragmentos con documento
    from app.db.models.legal import Documento

    result = await db.execute(
        select(Fragmento, Documento.titulo, FragmentoTema.confianza, FragmentoTema.detectado_por)
        .join(FragmentoTema, Fragmento.id == FragmentoTema.fragmento_id)
        .join(Documento, Fragmento.documento_id == Documento.id)
        .where(FragmentoTema.tema_id == tema_id)
        .order_by(FragmentoTema.confianza.desc())
        .limit(limite)
        .offset(offset)
    )
    rows = result.fetchall()

    return {
        "tema": {"id": tema.id, "codigo": tema.codigo, "nombre": tema.nombre},
        "total": total,
        "limite": limite,
        "offset": offset,
        "fragmentos": [
            {
                "id": frag.id,
                "documento_id": frag.documento_id,
                "documento_titulo": doc_titulo,
                "seccion": frag.seccion,
                "contenido": frag.contenido[:500] + "..." if len(frag.contenido) > 500 else frag.contenido,
                "confianza": confianza,
                "detectado_por": detectado_por,
            }
            for frag, doc_titulo, confianza, detectado_por in rows
        ],
    }


@router.put(
    "/{tema_id}",
    response_model=TemaResponse,
    summary="Actualizar tema",
    description="Actualiza un tema existente."
)
async def actualizar_tema(
    tema_id: int,
    datos: TemaUpdate,
    db: AsyncSession = Depends(get_db),
) -> TemaResponse:
    """Actualiza un tema."""
    tema = await db.get(Tema, tema_id)
    if not tema:
        raise HTTPException(status_code=404, detail="Tema no encontrado")

    update_data = datos.model_dump(exclude_unset=True)
    for campo, valor in update_data.items():
        setattr(tema, campo, valor)

    await db.commit()
    await db.refresh(tema)

    count_result = await db.execute(
        select(func.count(FragmentoTema.fragmento_id))
        .where(FragmentoTema.tema_id == tema.id)
    )
    cantidad = count_result.scalar() or 0

    return TemaResponse(
        id=tema.id,
        codigo=tema.codigo,
        nombre=tema.nombre,
        descripcion=tema.descripcion,
        grupo=tema.grupo,
        keywords=tema.keywords,
        color=tema.color,
        icono=tema.icono,
        activo=tema.activo,
        cantidad_fragmentos=cantidad,
    )


@router.delete(
    "/{tema_id}",
    status_code=204,
    summary="Eliminar tema",
    description="Elimina un tema (desactiva si tiene fragmentos asociados)."
)
async def eliminar_tema(
    tema_id: int,
    forzar: bool = Query(False, description="Eliminar aunque tenga fragmentos"),
    db: AsyncSession = Depends(get_db),
):
    """Elimina o desactiva un tema."""
    tema = await db.get(Tema, tema_id)
    if not tema:
        raise HTTPException(status_code=404, detail="Tema no encontrado")

    # Verificar si tiene fragmentos
    count_result = await db.execute(
        select(func.count(FragmentoTema.fragmento_id))
        .where(FragmentoTema.tema_id == tema_id)
    )
    cantidad = count_result.scalar() or 0

    if cantidad > 0 and not forzar:
        # Desactivar en lugar de eliminar
        tema.activo = False
        await db.commit()
        return

    # Eliminar (cascade eliminara relaciones)
    await db.delete(tema)
    await db.commit()


@router.post(
    "/{tema_id}/keywords",
    summary="Agregar keywords",
    description="Agrega keywords para deteccion automatica."
)
async def agregar_keywords_tema(
    tema_id: int,
    keywords: List[str] = Query(..., description="Lista de keywords a agregar"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Agrega keywords a un tema."""
    tema = await db.get(Tema, tema_id)
    if not tema:
        raise HTTPException(status_code=404, detail="Tema no encontrado")

    # Agregar sin duplicar
    keywords_actuales = set(tema.keywords or [])
    keywords_nuevos = set(kw.lower().strip() for kw in keywords if kw.strip())
    keywords_agregados = keywords_nuevos - keywords_actuales

    tema.keywords = list(keywords_actuales | keywords_nuevos)
    await db.commit()

    return {
        "mensaje": f"Se agregaron {len(keywords_agregados)} keywords",
        "keywords_agregados": list(keywords_agregados),
        "total_keywords": len(tema.keywords),
    }
