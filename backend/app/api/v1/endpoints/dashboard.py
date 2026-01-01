"""
Endpoints para Dashboard.
"""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models import Cliente, Proyecto, Analisis

router = APIRouter()


@router.get("/stats")
async def obtener_estadisticas(db: AsyncSession = Depends(get_db)):
    """
    Retorna estadisticas para el dashboard principal.
    """
    # Total clientes
    total_clientes = await db.scalar(
        select(func.count(Cliente.id))
    ) or 0

    # Total proyectos
    total_proyectos = await db.scalar(
        select(func.count(Proyecto.id))
    ) or 0

    # Proyectos en borrador
    proyectos_borrador = await db.scalar(
        select(func.count(Proyecto.id))
        .where(Proyecto.estado == "borrador")
    ) or 0

    # Proyectos analizados
    proyectos_analizados = await db.scalar(
        select(func.count(Proyecto.id))
        .where(Proyecto.estado == "analizado")
    ) or 0

    # Analisis de los ultimos 7 dias
    hace_7_dias = datetime.utcnow() - timedelta(days=7)
    analisis_semana = await db.scalar(
        select(func.count(Analisis.id))
        .where(Analisis.fecha_analisis >= hace_7_dias)
    ) or 0

    # Total EIA recomendados
    total_eia = await db.scalar(
        select(func.count(Analisis.id))
        .where(Analisis.via_ingreso_recomendada == "EIA")
    ) or 0

    # Total DIA recomendados
    total_dia = await db.scalar(
        select(func.count(Analisis.id))
        .where(Analisis.via_ingreso_recomendada == "DIA")
    ) or 0

    return {
        "total_clientes": total_clientes,
        "total_proyectos": total_proyectos,
        "proyectos_borrador": proyectos_borrador,
        "proyectos_analizados": proyectos_analizados,
        "analisis_semana": analisis_semana,
        "total_eia": total_eia,
        "total_dia": total_dia,
    }


@router.get("/analisis-recientes")
async def obtener_analisis_recientes(
    limite: int = Query(default=5, le=20),
    db: AsyncSession = Depends(get_db)
):
    """
    Retorna los N analisis mas recientes con datos del proyecto.
    """
    query = (
        select(
            Analisis.id,
            Analisis.proyecto_id,
            Proyecto.nombre.label("proyecto_nombre"),
            Analisis.via_ingreso_recomendada.label("via_ingreso"),
            Analisis.confianza_clasificacion.label("confianza"),
            Analisis.fecha_analisis.label("fecha"),
            Analisis.triggers_eia,
        )
        .join(Proyecto, Analisis.proyecto_id == Proyecto.id)
        .order_by(Analisis.fecha_analisis.desc())
        .limit(limite)
    )

    result = await db.execute(query)
    rows = result.all()

    # Calcular alertas_criticas desde triggers_eia
    analisis_list = []
    for row in rows:
        alertas_criticas = 0
        triggers = row.triggers_eia
        if triggers and isinstance(triggers, list):
            alertas_criticas = sum(
                1 for t in triggers
                if isinstance(t, dict) and t.get("severidad") == "CRITICA"
            )

        analisis_list.append({
            "id": str(row.id),
            "proyecto_id": str(row.proyecto_id),
            "proyecto_nombre": row.proyecto_nombre,
            "via_ingreso": row.via_ingreso,
            "confianza": float(row.confianza) if row.confianza else 0,
            "fecha": row.fecha.isoformat() if row.fecha else None,
            "alertas_criticas": alertas_criticas,
        })

    return analisis_list
