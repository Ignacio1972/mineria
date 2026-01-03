"""
Endpoints CRUD para Proyectos.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from geoalchemy2.shape import from_shape, to_shape
from shapely.geometry import shape, mapping, MultiPolygon

from app.db.session import get_db
from app.db.models import Proyecto, Cliente, DocumentoProyecto, Analisis
from app.schemas.proyecto import (
    ProyectoCreate,
    ProyectoUpdate,
    ProyectoGeometriaUpdate,
    ProyectoResponse,
    ProyectoConGeometriaResponse,
    ProyectoListResponse,
    EstadoProyecto,
    CambioEstadoRequest,
)

router = APIRouter()


def proyecto_to_dict(proyecto: Proyecto, cliente: Optional[Cliente] = None) -> dict:
    """Convierte modelo a diccionario para respuesta."""
    return {
        "id": proyecto.id,
        "nombre": proyecto.nombre,
        "cliente_id": proyecto.cliente_id,
        "tipo_mineria": proyecto.tipo_mineria,
        "mineral_principal": proyecto.mineral_principal,
        "fase": proyecto.fase,
        "titular": proyecto.titular,
        "region": proyecto.region,
        "comuna": proyecto.comuna,
        "superficie_ha": float(proyecto.superficie_ha) if proyecto.superficie_ha else None,
        "produccion_estimada": proyecto.produccion_estimada,
        "vida_util_anos": proyecto.vida_util_anos,
        "uso_agua_lps": float(proyecto.uso_agua_lps) if proyecto.uso_agua_lps else None,
        "fuente_agua": proyecto.fuente_agua,
        "energia_mw": float(proyecto.energia_mw) if proyecto.energia_mw else None,
        "trabajadores_construccion": proyecto.trabajadores_construccion,
        "trabajadores_operacion": proyecto.trabajadores_operacion,
        "inversion_musd": float(proyecto.inversion_musd) if proyecto.inversion_musd else None,
        "descripcion": proyecto.descripcion,
        "descarga_diaria_ton": float(proyecto.descarga_diaria_ton) if proyecto.descarga_diaria_ton else None,
        "emisiones_co2_ton_ano": float(proyecto.emisiones_co2_ton_ano) if proyecto.emisiones_co2_ton_ano else None,
        "requiere_reasentamiento": proyecto.requiere_reasentamiento or False,
        "afecta_patrimonio": proyecto.afecta_patrimonio or False,
        "estado": proyecto.estado or "borrador",
        "porcentaje_completado": proyecto.porcentaje_completado or 0,
        "tiene_geometria": proyecto.geom is not None,
        "puede_analizar": proyecto.geom is not None and proyecto.estado != "archivado",
        "afecta_glaciares": proyecto.afecta_glaciares or False,
        "dist_area_protegida_km": float(proyecto.dist_area_protegida_km) if proyecto.dist_area_protegida_km else None,
        "dist_comunidad_indigena_km": float(proyecto.dist_comunidad_indigena_km) if proyecto.dist_comunidad_indigena_km else None,
        "dist_centro_poblado_km": float(proyecto.dist_centro_poblado_km) if proyecto.dist_centro_poblado_km else None,
        "cliente_razon_social": cliente.razon_social if cliente else None,
        "created_at": proyecto.created_at,
        "updated_at": proyecto.updated_at,
    }


@router.get("", response_model=ProyectoListResponse)
async def listar_proyectos(
    cliente_id: Optional[str] = Query(None),
    estado: Optional[EstadoProyecto] = Query(None),
    region: Optional[str] = Query(None),
    busqueda: Optional[str] = Query(None, description="Buscar por nombre"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Listar proyectos con paginacion y filtros."""
    query = select(Proyecto, Cliente).outerjoin(Cliente, Proyecto.cliente_id == Cliente.id)

    # Filtros
    if cliente_id:
        query = query.where(Proyecto.cliente_id == cliente_id)
    if estado:
        query = query.where(Proyecto.estado == estado.value)
    if region:
        query = query.where(Proyecto.region == region)
    if busqueda:
        query = query.where(Proyecto.nombre.ilike(f"%{busqueda}%"))

    # Excluir archivados por defecto (a menos que se pida explicitamente)
    if estado != EstadoProyecto.ARCHIVADO:
        query = query.where(Proyecto.estado != "archivado")

    # Contar total
    count_subq = select(Proyecto.id).select_from(Proyecto)
    if cliente_id:
        count_subq = count_subq.where(Proyecto.cliente_id == cliente_id)
    if estado:
        count_subq = count_subq.where(Proyecto.estado == estado.value)
    elif estado != EstadoProyecto.ARCHIVADO:
        count_subq = count_subq.where(Proyecto.estado != "archivado")
    if region:
        count_subq = count_subq.where(Proyecto.region == region)
    if busqueda:
        count_subq = count_subq.where(Proyecto.nombre.ilike(f"%{busqueda}%"))

    count_query = select(func.count()).select_from(count_subq.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Ordenar y paginar
    query = query.order_by(Proyecto.updated_at.desc().nullslast())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    rows = result.all()

    items = []
    for proyecto, cliente in rows:
        # Contar documentos y analisis
        docs_count = await db.execute(
            select(func.count()).where(DocumentoProyecto.proyecto_id == proyecto.id)
        )
        analisis_count = await db.execute(
            select(func.count()).where(Analisis.proyecto_id == proyecto.id)
        )
        ultimo = await db.execute(
            select(Analisis.fecha_analisis)
            .where(Analisis.proyecto_id == proyecto.id)
            .order_by(Analisis.fecha_analisis.desc())
            .limit(1)
        )

        data = proyecto_to_dict(proyecto, cliente)
        data["total_documentos"] = docs_count.scalar() or 0
        data["total_analisis"] = analisis_count.scalar() or 0
        data["ultimo_analisis"] = ultimo.scalar()

        items.append(ProyectoResponse.model_validate(data))

    return ProyectoListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size if total > 0 else 0,
    )


@router.post("", response_model=ProyectoResponse, status_code=201)
async def crear_proyecto(
    data: ProyectoCreate,
    db: AsyncSession = Depends(get_db),
):
    """Crear nuevo proyecto."""
    # Verificar cliente si se proporciona
    cliente = None
    if data.cliente_id:
        cliente_result = await db.execute(
            select(Cliente).where(Cliente.id == data.cliente_id, Cliente.activo == True)
        )
        cliente = cliente_result.scalar()
        if not cliente:
            raise HTTPException(400, "Cliente no encontrado o inactivo")

    # Preparar datos
    proyecto_data = data.model_dump(exclude={"geometria"})

    # Procesar geometria si existe
    if data.geometria:
        geom_shape = shape(data.geometria.model_dump())
        # Convertir Polygon a MultiPolygon si es necesario
        if geom_shape.geom_type == "Polygon":
            geom_shape = MultiPolygon([geom_shape])
        proyecto_data["geom"] = from_shape(geom_shape, srid=4326)

    proyecto = Proyecto(**proyecto_data)
    db.add(proyecto)
    await db.commit()
    await db.refresh(proyecto)

    response_data = proyecto_to_dict(proyecto, cliente)
    response_data["total_documentos"] = 0
    response_data["total_analisis"] = 0
    response_data["ultimo_analisis"] = None

    return ProyectoResponse.model_validate(response_data)


@router.get("/{proyecto_id}", response_model=ProyectoConGeometriaResponse)
async def obtener_proyecto(
    proyecto_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Obtener proyecto por ID con geometria."""
    result = await db.execute(
        select(Proyecto, Cliente)
        .outerjoin(Cliente, Proyecto.cliente_id == Cliente.id)
        .where(Proyecto.id == proyecto_id)
    )
    row = result.first()

    if not row:
        raise HTTPException(404, "Proyecto no encontrado")

    proyecto, cliente = row

    # Contadores
    docs_count = await db.execute(
        select(func.count()).where(DocumentoProyecto.proyecto_id == proyecto.id)
    )
    analisis_count = await db.execute(
        select(func.count()).where(Analisis.proyecto_id == proyecto.id)
    )
    ultimo = await db.execute(
        select(Analisis.fecha_analisis)
        .where(Analisis.proyecto_id == proyecto.id)
        .order_by(Analisis.fecha_analisis.desc())
        .limit(1)
    )

    data = proyecto_to_dict(proyecto, cliente)
    data["total_documentos"] = docs_count.scalar() or 0
    data["total_analisis"] = analisis_count.scalar() or 0
    data["ultimo_analisis"] = ultimo.scalar()

    # Agregar geometria
    if proyecto.geom:
        geom_shape = to_shape(proyecto.geom)
        data["geometria"] = mapping(geom_shape)
    else:
        data["geometria"] = None

    return ProyectoConGeometriaResponse.model_validate(data)


@router.put("/{proyecto_id}", response_model=ProyectoResponse)
async def actualizar_proyecto(
    proyecto_id: int,
    data: ProyectoUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Actualizar proyecto (sin geometria)."""
    result = await db.execute(select(Proyecto).where(Proyecto.id == proyecto_id))
    proyecto = result.scalar()

    if not proyecto:
        raise HTTPException(404, "Proyecto no encontrado")

    if proyecto.estado == "archivado":
        raise HTTPException(400, "No se puede modificar un proyecto archivado")

    # Verificar cliente si se cambia
    cliente = None
    if data.cliente_id:
        cliente_result = await db.execute(
            select(Cliente).where(Cliente.id == data.cliente_id, Cliente.activo == True)
        )
        cliente = cliente_result.scalar()
        if not cliente:
            raise HTTPException(400, "Cliente no encontrado o inactivo")

    # Actualizar campos
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(proyecto, key, value)

    await db.commit()
    await db.refresh(proyecto)

    # Obtener cliente actualizado
    if proyecto.cliente_id and not cliente:
        result = await db.execute(select(Cliente).where(Cliente.id == proyecto.cliente_id))
        cliente = result.scalar()

    docs_count = await db.execute(
        select(func.count()).where(DocumentoProyecto.proyecto_id == proyecto.id)
    )
    analisis_count = await db.execute(
        select(func.count()).where(Analisis.proyecto_id == proyecto.id)
    )

    response_data = proyecto_to_dict(proyecto, cliente)
    response_data["total_documentos"] = docs_count.scalar() or 0
    response_data["total_analisis"] = analisis_count.scalar() or 0
    response_data["ultimo_analisis"] = None

    return ProyectoResponse.model_validate(response_data)


@router.patch("/{proyecto_id}/geometria", response_model=ProyectoResponse)
async def actualizar_geometria(
    proyecto_id: int,
    data: ProyectoGeometriaUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Actualizar solo la geometria del proyecto."""
    result = await db.execute(select(Proyecto).where(Proyecto.id == proyecto_id))
    proyecto = result.scalar()

    if not proyecto:
        raise HTTPException(404, "Proyecto no encontrado")

    if proyecto.estado == "archivado":
        raise HTTPException(400, "No se puede modificar un proyecto archivado")

    # Procesar geometria
    geom_shape = shape(data.geometria.model_dump())
    if geom_shape.geom_type == "Polygon":
        geom_shape = MultiPolygon([geom_shape])

    proyecto.geom = from_shape(geom_shape, srid=4326)

    await db.commit()
    await db.refresh(proyecto)

    # El trigger habra actualizado estado y campos pre-calculados
    cliente = None
    if proyecto.cliente_id:
        result = await db.execute(select(Cliente).where(Cliente.id == proyecto.cliente_id))
        cliente = result.scalar()

    response_data = proyecto_to_dict(proyecto, cliente)
    response_data["total_documentos"] = 0
    response_data["total_analisis"] = 0
    response_data["ultimo_analisis"] = None

    return ProyectoResponse.model_validate(response_data)


@router.patch("/{proyecto_id}/estado")
async def cambiar_estado(
    proyecto_id: int,
    data: CambioEstadoRequest,
    db: AsyncSession = Depends(get_db),
):
    """Cambiar estado del proyecto."""
    result = await db.execute(select(Proyecto).where(Proyecto.id == proyecto_id))
    proyecto = result.scalar()

    if not proyecto:
        raise HTTPException(404, "Proyecto no encontrado")

    estado_actual = proyecto.estado

    # Validar transiciones permitidas
    transiciones_validas = {
        "borrador": ["completo", "archivado"],
        "completo": ["con_geometria", "archivado"],
        "con_geometria": ["analizado", "archivado"],
        "analizado": ["en_revision", "archivado"],
        "en_revision": ["aprobado", "rechazado"],
        "aprobado": ["archivado"],
        "rechazado": ["en_revision", "archivado"],
        "archivado": [],
    }

    if data.estado.value not in transiciones_validas.get(estado_actual, []):
        raise HTTPException(
            400,
            f"Transicion no permitida: {estado_actual} -> {data.estado.value}"
        )

    proyecto.estado = data.estado.value
    await db.commit()

    return {"mensaje": f"Estado cambiado de {estado_actual} a {data.estado.value}"}


@router.post("/{proyecto_id}/restaurar")
async def restaurar_proyecto(
    proyecto_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Restaurar un proyecto archivado.

    El proyecto vuelve al estado 'borrador' para ser re-evaluado.
    """
    result = await db.execute(select(Proyecto).where(Proyecto.id == proyecto_id))
    proyecto = result.scalar()

    if not proyecto:
        raise HTTPException(404, "Proyecto no encontrado")

    if proyecto.estado != "archivado":
        raise HTTPException(400, f"El proyecto no está archivado (estado: {proyecto.estado})")

    # Determinar estado de restauración basado en datos del proyecto
    if proyecto.geom is not None:
        nuevo_estado = "con_geometria"
    elif proyecto.porcentaje_completado and proyecto.porcentaje_completado >= 80:
        nuevo_estado = "completo"
    else:
        nuevo_estado = "borrador"

    proyecto.estado = nuevo_estado
    await db.commit()

    return {
        "mensaje": f"Proyecto restaurado exitosamente",
        "estado_anterior": "archivado",
        "estado_actual": nuevo_estado
    }


@router.delete("/{proyecto_id}", status_code=204)
async def eliminar_proyecto(
    proyecto_id: int,
    hard_delete: bool = Query(False, description="Eliminar permanentemente (solo borradores sin análisis)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Eliminar proyecto.

    - Por defecto: soft delete (archiva el proyecto)
    - Con hard_delete=true: elimina permanentemente (solo proyectos en borrador sin análisis)
    """
    result = await db.execute(select(Proyecto).where(Proyecto.id == proyecto_id))
    proyecto = result.scalar()

    if not proyecto:
        raise HTTPException(404, "Proyecto no encontrado")

    if proyecto.estado == "archivado":
        raise HTTPException(400, "El proyecto ya está archivado")

    if hard_delete:
        # Hard delete solo permitido para borradores
        if proyecto.estado != "borrador":
            raise HTTPException(
                400,
                f"Solo se pueden eliminar permanentemente proyectos en borrador. "
                f"Estado actual: {proyecto.estado}"
            )

        # Verificar que no tenga análisis
        analisis_count = await db.execute(
            select(func.count()).where(Analisis.proyecto_id == proyecto_id)
        )
        if analisis_count.scalar() > 0:
            raise HTTPException(
                400,
                "No se puede eliminar permanentemente: el proyecto tiene análisis registrados. "
                "Use soft delete (archivar) en su lugar."
            )

        # Hard delete - las cascadas eliminan documentos e historial
        await db.delete(proyecto)
        await db.commit()
    else:
        # Soft delete - archivar
        proyecto.estado = "archivado"
        await db.commit()


@router.get("/{proyecto_id}/analisis")
async def historial_analisis_proyecto(
    proyecto_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Obtener historial de analisis del proyecto."""
    result = await db.execute(select(Proyecto).where(Proyecto.id == proyecto_id))
    if not result.scalar():
        raise HTTPException(404, "Proyecto no encontrado")

    analisis = await db.execute(
        select(Analisis)
        .where(Analisis.proyecto_id == proyecto_id)
        .order_by(Analisis.fecha_analisis.desc())
    )

    return [
        {
            "id": a.id,
            "fecha_analisis": a.fecha_analisis,
            "tipo_analisis": a.tipo_analisis,
            "via_ingreso_recomendada": a.via_ingreso_recomendada,
            "confianza_clasificacion": float(a.confianza_clasificacion) if a.confianza_clasificacion else None,
        }
        for a in analisis.scalars().all()
    ]
