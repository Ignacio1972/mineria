"""
Endpoints CRUD para Clientes.
"""
from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.session import get_db
from app.db.models import Cliente, Proyecto
from app.schemas.cliente import (
    ClienteCreate,
    ClienteUpdate,
    ClienteResponse,
    ClienteListResponse,
)

router = APIRouter()


@router.get("", response_model=ClienteListResponse)
async def listar_clientes(
    busqueda: Optional[str] = Query(None, description="Buscar por razon social"),
    activo: Optional[bool] = Query(None, description="Filtrar por estado activo"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Listar clientes con paginacion y filtros."""
    query = select(Cliente)

    # Filtros
    if busqueda:
        query = query.where(Cliente.razon_social.ilike(f"%{busqueda}%"))
    if activo is not None:
        query = query.where(Cliente.activo == activo)

    # Contar total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Paginacion
    query = query.order_by(Cliente.razon_social)
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    clientes = result.scalars().all()

    # Agregar cantidad de proyectos
    items = []
    for cliente in clientes:
        count = await db.execute(
            select(func.count()).where(Proyecto.cliente_id == cliente.id)
        )
        cliente_dict = {
            "id": cliente.id,
            "rut": cliente.rut,
            "razon_social": cliente.razon_social,
            "nombre_fantasia": cliente.nombre_fantasia,
            "email": cliente.email,
            "telefono": cliente.telefono,
            "direccion": cliente.direccion,
            "notas": cliente.notas,
            "activo": cliente.activo,
            "created_at": cliente.created_at,
            "updated_at": cliente.updated_at,
            "cantidad_proyectos": count.scalar() or 0
        }
        items.append(ClienteResponse.model_validate(cliente_dict))

    return ClienteListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size if total > 0 else 0,
    )


@router.post("", response_model=ClienteResponse, status_code=201)
async def crear_cliente(
    data: ClienteCreate,
    db: AsyncSession = Depends(get_db),
):
    """Crear nuevo cliente."""
    # Verificar RUT unico si se proporciona
    if data.rut:
        existe = await db.execute(
            select(Cliente).where(Cliente.rut == data.rut)
        )
        if existe.scalar():
            raise HTTPException(400, f"Ya existe un cliente con RUT {data.rut}")

    cliente = Cliente(**data.model_dump())
    db.add(cliente)
    await db.commit()
    await db.refresh(cliente)

    return ClienteResponse.model_validate({
        "id": cliente.id,
        "rut": cliente.rut,
        "razon_social": cliente.razon_social,
        "nombre_fantasia": cliente.nombre_fantasia,
        "email": cliente.email,
        "telefono": cliente.telefono,
        "direccion": cliente.direccion,
        "notas": cliente.notas,
        "activo": cliente.activo,
        "created_at": cliente.created_at,
        "updated_at": cliente.updated_at,
        "cantidad_proyectos": 0
    })


@router.get("/{cliente_id}", response_model=ClienteResponse)
async def obtener_cliente(
    cliente_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Obtener cliente por ID."""
    result = await db.execute(select(Cliente).where(Cliente.id == cliente_id))
    cliente = result.scalar()

    if not cliente:
        raise HTTPException(404, "Cliente no encontrado")

    count = await db.execute(
        select(func.count()).where(Proyecto.cliente_id == cliente.id)
    )

    return ClienteResponse.model_validate({
        "id": cliente.id,
        "rut": cliente.rut,
        "razon_social": cliente.razon_social,
        "nombre_fantasia": cliente.nombre_fantasia,
        "email": cliente.email,
        "telefono": cliente.telefono,
        "direccion": cliente.direccion,
        "notas": cliente.notas,
        "activo": cliente.activo,
        "created_at": cliente.created_at,
        "updated_at": cliente.updated_at,
        "cantidad_proyectos": count.scalar() or 0
    })


@router.put("/{cliente_id}", response_model=ClienteResponse)
async def actualizar_cliente(
    cliente_id: UUID,
    data: ClienteUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Actualizar cliente."""
    result = await db.execute(select(Cliente).where(Cliente.id == cliente_id))
    cliente = result.scalar()

    if not cliente:
        raise HTTPException(404, "Cliente no encontrado")

    # Verificar RUT unico si se cambia
    if data.rut and data.rut != cliente.rut:
        existe = await db.execute(
            select(Cliente).where(Cliente.rut == data.rut, Cliente.id != cliente_id)
        )
        if existe.scalar():
            raise HTTPException(400, f"Ya existe un cliente con RUT {data.rut}")

    # Actualizar campos
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(cliente, key, value)

    await db.commit()
    await db.refresh(cliente)

    count = await db.execute(
        select(func.count()).where(Proyecto.cliente_id == cliente.id)
    )

    return ClienteResponse.model_validate({
        "id": cliente.id,
        "rut": cliente.rut,
        "razon_social": cliente.razon_social,
        "nombre_fantasia": cliente.nombre_fantasia,
        "email": cliente.email,
        "telefono": cliente.telefono,
        "direccion": cliente.direccion,
        "notas": cliente.notas,
        "activo": cliente.activo,
        "created_at": cliente.created_at,
        "updated_at": cliente.updated_at,
        "cantidad_proyectos": count.scalar() or 0
    })


@router.delete("/{cliente_id}", status_code=204)
async def eliminar_cliente(
    cliente_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Eliminar cliente (soft delete: marca como inactivo)."""
    result = await db.execute(select(Cliente).where(Cliente.id == cliente_id))
    cliente = result.scalar()

    if not cliente:
        raise HTTPException(404, "Cliente no encontrado")

    # Verificar si tiene proyectos activos
    proyectos = await db.execute(
        select(func.count()).where(
            Proyecto.cliente_id == cliente_id,
            Proyecto.estado != "archivado"
        )
    )
    if proyectos.scalar() > 0:
        raise HTTPException(
            400,
            "No se puede eliminar cliente con proyectos activos. Archive los proyectos primero."
        )

    cliente.activo = False
    await db.commit()
