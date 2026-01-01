"""
Endpoints para gestion de categorias del corpus RAG.

Proporciona CRUD completo para la taxonomia jerarquica de documentos.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from pydantic import BaseModel, Field

from app.db.session import get_db
from app.db.models.corpus import Categoria


router = APIRouter()


# ============================================================================
# SCHEMAS
# ============================================================================

class CategoriaBase(BaseModel):
    """Schema base para categoria."""
    codigo: str = Field(..., min_length=1, max_length=100)
    nombre: str = Field(..., min_length=1, max_length=255)
    descripcion: Optional[str] = None
    tipo_documentos_permitidos: Optional[List[str]] = None
    icono: Optional[str] = None
    color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')


class CategoriaCreate(CategoriaBase):
    """Schema para crear categoria."""
    parent_id: Optional[int] = None


class CategoriaUpdate(BaseModel):
    """Schema para actualizar categoria."""
    nombre: Optional[str] = Field(None, min_length=1, max_length=255)
    descripcion: Optional[str] = None
    tipo_documentos_permitidos: Optional[List[str]] = None
    icono: Optional[str] = None
    color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    activo: Optional[bool] = None


class CategoriaResponse(CategoriaBase):
    """Schema de respuesta para categoria."""
    id: int
    parent_id: Optional[int]
    nivel: int
    orden: int
    activo: bool
    cantidad_documentos: int = 0

    class Config:
        from_attributes = True


class CategoriaArbolResponse(CategoriaResponse):
    """Categoria con hijos anidados para vista de arbol."""
    hijos: List["CategoriaArbolResponse"] = []


class CategoriaPathResponse(BaseModel):
    """Respuesta con path completo de categoria."""
    id: int
    codigo: str
    nombre: str
    path: str
    nivel: int


# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

async def contar_documentos_categoria(db: AsyncSession, categoria_id: int) -> int:
    """Cuenta documentos en una categoria (sin incluir subcategorias)."""
    from app.db.models.legal import Documento
    result = await db.execute(
        select(func.count(Documento.id)).where(Documento.categoria_id == categoria_id)
    )
    return result.scalar() or 0


async def contar_documentos_con_subcategorias(db: AsyncSession) -> dict:
    """
    Cuenta documentos por categoría INCLUYENDO subcategorías.
    Retorna un diccionario {categoria_id: cantidad_total}.
    Usa una sola consulta SQL eficiente con CTE recursiva.
    """
    query = text("""
        WITH RECURSIVE categoria_tree AS (
            -- Para cada categoría, obtener su árbol de descendientes
            SELECT
                c.id as root_id,
                c.id as descendant_id
            FROM legal.categorias c

            UNION ALL

            SELECT
                ct.root_id,
                c.id as descendant_id
            FROM legal.categorias c
            INNER JOIN categoria_tree ct ON c.parent_id = ct.descendant_id
        ),
        conteos AS (
            -- Contar documentos por cada categoría raíz (incluyendo sus descendientes)
            SELECT
                ct.root_id as categoria_id,
                COUNT(d.id) as cantidad
            FROM categoria_tree ct
            LEFT JOIN legal.documentos d ON d.categoria_id = ct.descendant_id
            GROUP BY ct.root_id
        )
        SELECT categoria_id, cantidad FROM conteos
    """)

    result = await db.execute(query)
    return {row[0]: row[1] for row in result.fetchall()}


async def obtener_ids_descendientes(db: AsyncSession, categoria_id: int) -> List[int]:
    """Obtiene IDs de una categoria y todos sus descendientes."""
    query = text("""
        WITH RECURSIVE descendientes AS (
            SELECT id FROM legal.categorias WHERE id = :cat_id
            UNION ALL
            SELECT c.id FROM legal.categorias c
            JOIN descendientes d ON c.parent_id = d.id
        )
        SELECT id FROM descendientes
    """)
    result = await db.execute(query, {"cat_id": categoria_id})
    return [row[0] for row in result.fetchall()]


def construir_arbol(categorias: List[Categoria]) -> List[dict]:
    """Construye arbol jerarquico desde lista plana de categorias."""
    categorias_dict = {}
    raices = []

    # Primer paso: crear diccionario con todas las categorias
    for cat in categorias:
        categorias_dict[cat.id] = {
            "id": cat.id,
            "codigo": cat.codigo,
            "nombre": cat.nombre,
            "descripcion": cat.descripcion,
            "parent_id": cat.parent_id,
            "nivel": cat.nivel,
            "orden": cat.orden,
            "activo": cat.activo,
            "icono": cat.icono,
            "color": cat.color,
            "tipo_documentos_permitidos": cat.tipo_documentos_permitidos or [],
            "cantidad_documentos": 0,
            "hijos": []
        }

    # Segundo paso: construir jerarquia
    for cat in categorias:
        if cat.parent_id is None:
            raices.append(categorias_dict[cat.id])
        else:
            parent = categorias_dict.get(cat.parent_id)
            if parent:
                parent["hijos"].append(categorias_dict[cat.id])

    # Ordenar por 'orden' en cada nivel
    def ordenar_hijos(nodo):
        nodo["hijos"].sort(key=lambda x: x["orden"])
        for hijo in nodo["hijos"]:
            ordenar_hijos(hijo)

    raices.sort(key=lambda x: x["orden"])
    for raiz in raices:
        ordenar_hijos(raiz)

    return raices


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get(
    "/",
    response_model=List[CategoriaResponse],
    summary="Listar categorias",
    description="Lista todas las categorias del corpus con filtros opcionales."
)
async def listar_categorias(
    solo_raiz: bool = Query(False, description="Solo categorias de nivel 1"),
    incluir_inactivas: bool = Query(False, description="Incluir categorias desactivadas"),
    parent_id: Optional[int] = Query(None, description="Filtrar por categoria padre"),
    db: AsyncSession = Depends(get_db),
) -> List[CategoriaResponse]:
    """Lista categorias con filtros opcionales."""
    query = select(Categoria)

    if solo_raiz:
        query = query.where(Categoria.parent_id.is_(None))
    elif parent_id is not None:
        query = query.where(Categoria.parent_id == parent_id)

    if not incluir_inactivas:
        query = query.where(Categoria.activo == True)

    query = query.order_by(Categoria.nivel, Categoria.orden, Categoria.nombre)

    result = await db.execute(query)
    categorias = result.scalars().all()

    # Obtener conteo de documentos INCLUYENDO subcategorías (una sola consulta)
    conteos = await contar_documentos_con_subcategorias(db)

    # Agregar conteo de documentos
    respuestas = []
    for cat in categorias:
        cantidad = conteos.get(cat.id, 0)
        resp = CategoriaResponse(
            id=cat.id,
            codigo=cat.codigo,
            nombre=cat.nombre,
            descripcion=cat.descripcion,
            tipo_documentos_permitidos=cat.tipo_documentos_permitidos or [],
            icono=cat.icono,
            color=cat.color,
            parent_id=cat.parent_id,
            nivel=cat.nivel,
            orden=cat.orden,
            activo=cat.activo,
            cantidad_documentos=cantidad,
        )
        respuestas.append(resp)

    return respuestas


@router.get(
    "/arbol",
    summary="Obtener arbol de categorias",
    description="Retorna la taxonomia completa como arbol jerarquico."
)
async def obtener_arbol_categorias(
    incluir_inactivas: bool = Query(False, description="Incluir categorias desactivadas"),
    db: AsyncSession = Depends(get_db),
) -> List[dict]:
    """Retorna taxonomia como arbol jerarquico para navegacion."""
    query = select(Categoria)

    if not incluir_inactivas:
        query = query.where(Categoria.activo == True)

    query = query.order_by(Categoria.nivel, Categoria.orden)

    result = await db.execute(query)
    categorias = result.scalars().all()

    return construir_arbol(categorias)


@router.post(
    "/",
    response_model=CategoriaResponse,
    status_code=201,
    summary="Crear categoria",
    description="Crea una nueva categoria en la taxonomia."
)
async def crear_categoria(
    categoria: CategoriaCreate,
    db: AsyncSession = Depends(get_db),
) -> CategoriaResponse:
    """Crea una nueva categoria."""
    # Verificar que codigo no existe
    existe = await db.execute(
        select(Categoria).where(Categoria.codigo == categoria.codigo)
    )
    if existe.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail=f"Ya existe una categoria con codigo '{categoria.codigo}'"
        )

    # Calcular nivel basado en padre
    nivel = 1
    if categoria.parent_id:
        parent = await db.get(Categoria, categoria.parent_id)
        if not parent:
            raise HTTPException(status_code=404, detail="Categoria padre no encontrada")
        if not parent.activo:
            raise HTTPException(status_code=400, detail="La categoria padre esta desactivada")
        nivel = parent.nivel + 1
        if nivel > 5:
            raise HTTPException(status_code=400, detail="Nivel maximo de anidamiento es 5")

    # Calcular orden (al final de siblings)
    orden_query = select(func.coalesce(func.max(Categoria.orden), 0) + 1).where(
        Categoria.parent_id == categoria.parent_id if categoria.parent_id else Categoria.parent_id.is_(None)
    )
    orden_result = await db.execute(orden_query)
    orden = orden_result.scalar()

    # Crear categoria
    nueva = Categoria(
        codigo=categoria.codigo,
        nombre=categoria.nombre,
        descripcion=categoria.descripcion,
        tipo_documentos_permitidos=categoria.tipo_documentos_permitidos,
        icono=categoria.icono,
        color=categoria.color,
        parent_id=categoria.parent_id,
        nivel=nivel,
        orden=orden,
    )
    db.add(nueva)
    await db.commit()
    await db.refresh(nueva)

    return CategoriaResponse(
        id=nueva.id,
        codigo=nueva.codigo,
        nombre=nueva.nombre,
        descripcion=nueva.descripcion,
        tipo_documentos_permitidos=nueva.tipo_documentos_permitidos or [],
        icono=nueva.icono,
        color=nueva.color,
        parent_id=nueva.parent_id,
        nivel=nueva.nivel,
        orden=nueva.orden,
        activo=nueva.activo,
        cantidad_documentos=0,
    )


@router.get(
    "/{categoria_id}",
    response_model=CategoriaResponse,
    summary="Obtener categoria",
    description="Obtiene una categoria por su ID."
)
async def obtener_categoria(
    categoria_id: int,
    db: AsyncSession = Depends(get_db),
) -> CategoriaResponse:
    """Obtiene una categoria por ID."""
    categoria = await db.get(Categoria, categoria_id)
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoria no encontrada")

    cantidad = await contar_documentos_categoria(db, categoria.id)

    return CategoriaResponse(
        id=categoria.id,
        codigo=categoria.codigo,
        nombre=categoria.nombre,
        descripcion=categoria.descripcion,
        tipo_documentos_permitidos=categoria.tipo_documentos_permitidos or [],
        icono=categoria.icono,
        color=categoria.color,
        parent_id=categoria.parent_id,
        nivel=categoria.nivel,
        orden=categoria.orden,
        activo=categoria.activo,
        cantidad_documentos=cantidad,
    )


@router.get(
    "/{categoria_id}/path",
    response_model=CategoriaPathResponse,
    summary="Obtener path de categoria",
    description="Obtiene el path completo de una categoria en la jerarquia."
)
async def obtener_path_categoria(
    categoria_id: int,
    db: AsyncSession = Depends(get_db),
) -> CategoriaPathResponse:
    """Obtiene el path completo de una categoria."""
    categoria = await db.get(Categoria, categoria_id)
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoria no encontrada")

    # Usar funcion SQL para obtener path
    result = await db.execute(
        text("SELECT legal.get_categoria_path(:cat_id)"),
        {"cat_id": categoria_id}
    )
    path = result.scalar() or categoria.nombre

    return CategoriaPathResponse(
        id=categoria.id,
        codigo=categoria.codigo,
        nombre=categoria.nombre,
        path=path,
        nivel=categoria.nivel,
    )


@router.put(
    "/{categoria_id}",
    response_model=CategoriaResponse,
    summary="Actualizar categoria",
    description="Actualiza una categoria existente."
)
async def actualizar_categoria(
    categoria_id: int,
    datos: CategoriaUpdate,
    db: AsyncSession = Depends(get_db),
) -> CategoriaResponse:
    """Actualiza una categoria existente."""
    categoria = await db.get(Categoria, categoria_id)
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoria no encontrada")

    # Actualizar campos proporcionados
    update_data = datos.model_dump(exclude_unset=True)
    for campo, valor in update_data.items():
        setattr(categoria, campo, valor)

    await db.commit()
    await db.refresh(categoria)

    cantidad = await contar_documentos_categoria(db, categoria.id)

    return CategoriaResponse(
        id=categoria.id,
        codigo=categoria.codigo,
        nombre=categoria.nombre,
        descripcion=categoria.descripcion,
        tipo_documentos_permitidos=categoria.tipo_documentos_permitidos or [],
        icono=categoria.icono,
        color=categoria.color,
        parent_id=categoria.parent_id,
        nivel=categoria.nivel,
        orden=categoria.orden,
        activo=categoria.activo,
        cantidad_documentos=cantidad,
    )


@router.delete(
    "/{categoria_id}",
    status_code=204,
    summary="Eliminar categoria",
    description="Elimina una categoria y sus subcategorias."
)
async def eliminar_categoria(
    categoria_id: int,
    forzar: bool = Query(False, description="Eliminar aunque tenga documentos"),
    db: AsyncSession = Depends(get_db),
):
    """Elimina una categoria."""
    categoria = await db.get(Categoria, categoria_id)
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoria no encontrada")

    # Verificar documentos asociados (incluye subcategorias)
    ids_descendientes = await obtener_ids_descendientes(db, categoria_id)

    from app.db.models.legal import Documento
    docs_count_result = await db.execute(
        select(func.count(Documento.id)).where(Documento.categoria_id.in_(ids_descendientes))
    )
    docs_count = docs_count_result.scalar() or 0

    if docs_count > 0 and not forzar:
        raise HTTPException(
            status_code=400,
            detail=f"La categoria tiene {docs_count} documento(s) asociados. "
                   f"Use forzar=true para eliminar de todos modos."
        )

    # Eliminar (cascade eliminara subcategorias)
    await db.delete(categoria)
    await db.commit()


@router.get(
    "/{categoria_id}/documentos",
    summary="Listar documentos de categoria",
    description="Lista documentos de una categoria, opcionalmente incluyendo subcategorias."
)
async def listar_documentos_categoria(
    categoria_id: int,
    incluir_subcategorias: bool = Query(True, description="Incluir documentos de subcategorias"),
    limite: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Lista documentos de una categoria."""
    categoria = await db.get(Categoria, categoria_id)
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoria no encontrada")

    from app.db.models.legal import Documento

    if incluir_subcategorias:
        ids = await obtener_ids_descendientes(db, categoria_id)
        query = select(Documento).where(Documento.categoria_id.in_(ids))
        count_query = select(func.count(Documento.id)).where(Documento.categoria_id.in_(ids))
    else:
        query = select(Documento).where(Documento.categoria_id == categoria_id)
        count_query = select(func.count(Documento.id)).where(Documento.categoria_id == categoria_id)

    # Obtener total
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Obtener documentos paginados
    query = query.order_by(Documento.created_at.desc()).limit(limite).offset(offset)
    result = await db.execute(query)
    documentos = result.scalars().all()

    return {
        "categoria_id": categoria_id,
        "categoria_nombre": categoria.nombre,
        "incluye_subcategorias": incluir_subcategorias,
        "total": total,
        "limite": limite,
        "offset": offset,
        "documentos": [
            {
                "id": d.id,
                "titulo": d.titulo,
                "tipo": d.tipo,
                "numero": d.numero,
                "fecha_publicacion": d.fecha_publicacion.isoformat() if d.fecha_publicacion else None,
                "estado": d.estado,
                "tiene_archivo": d.archivo_id is not None,
            }
            for d in documentos
        ],
    }


@router.post(
    "/{categoria_id}/reordenar",
    summary="Reordenar categoria",
    description="Cambia la posicion de una categoria entre sus hermanos."
)
async def reordenar_categoria(
    categoria_id: int,
    nueva_posicion: int = Query(..., ge=0, description="Nueva posicion (0-based)"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Reordena una categoria entre sus hermanos."""
    categoria = await db.get(Categoria, categoria_id)
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoria no encontrada")

    # Obtener hermanos
    if categoria.parent_id:
        siblings_query = select(Categoria).where(
            Categoria.parent_id == categoria.parent_id,
            Categoria.activo == True
        ).order_by(Categoria.orden)
    else:
        siblings_query = select(Categoria).where(
            Categoria.parent_id.is_(None),
            Categoria.activo == True
        ).order_by(Categoria.orden)

    result = await db.execute(siblings_query)
    siblings = list(result.scalars().all())

    if nueva_posicion >= len(siblings):
        nueva_posicion = len(siblings) - 1

    # Remover de posicion actual y agregar en nueva
    siblings.remove(categoria)
    siblings.insert(nueva_posicion, categoria)

    # Actualizar ordenes
    for i, sib in enumerate(siblings):
        sib.orden = i

    await db.commit()

    return {
        "mensaje": "Categoria reordenada",
        "categoria_id": categoria_id,
        "nueva_posicion": nueva_posicion,
    }
