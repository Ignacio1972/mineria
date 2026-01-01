import logging
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from shapely.geometry import shape
from shapely import wkt
import json

from app.core.config import settings

logger = logging.getLogger(__name__)


async def analizar_proyecto_espacial(
    db: AsyncSession,
    geojson: dict,
) -> dict[str, Any]:
    """
    Analiza espacialmente un polígono de proyecto contra las capas GIS.

    Args:
        db: Sesión de base de datos
        geojson: GeoJSON del polígono del proyecto

    Returns:
        Diccionario con resultados del análisis espacial
    """
    logger.info("Iniciando análisis espacial de proyecto")

    # Convertir GeoJSON a WKT
    geom = shape(geojson)
    wkt_geom = geom.wkt
    logger.debug(f"Geometría convertida a WKT ({len(wkt_geom)} caracteres)")

    # Usar la función SQL definida en el esquema
    query = text("""
        SELECT gis.analizar_proyecto(ST_GeomFromText(:wkt, 4326)) as resultado
    """)

    result = await db.execute(query, {"wkt": wkt_geom})
    row = result.fetchone()

    if row and row.resultado:
        logger.info("Análisis completado usando función SQL")
        # Normalizar nulls a listas vacías
        resultado = row.resultado
        for key in ["glaciares", "cuerpos_agua", "areas_protegidas",
                    "comunidades_indigenas", "centros_poblados", "sitios_patrimoniales"]:
            if resultado.get(key) is None:
                resultado[key] = []
        if "alertas" not in resultado:
            resultado["alertas"] = []
        return resultado

    # Si no hay función, hacer queries individuales
    logger.info("Función SQL no disponible, usando análisis manual")
    return await _analisis_manual(db, wkt_geom)


async def _analisis_manual(db: AsyncSession, wkt_geom: str) -> dict[str, Any]:
    """Análisis manual si la función SQL no está disponible."""

    resultado = {
        "areas_protegidas": [],
        "glaciares": [],
        "cuerpos_agua": [],
        "comunidades_indigenas": [],
        "centros_poblados": [],
        "sitios_patrimoniales": [],
        "alertas": [],
    }

    # Áreas protegidas
    query = text("""
        SELECT
            id,
            nombre,
            tipo,
            categoria,
            ST_Intersects(geom, ST_GeomFromText(:wkt, 4326)) as intersecta,
            ST_Distance(geom::geography, ST_GeomFromText(:wkt, 4326)::geography) as distancia_m
        FROM gis.areas_protegidas
        WHERE ST_DWithin(
            geom::geography,
            ST_GeomFromText(:wkt, 4326)::geography,
            :buffer
        )
        ORDER BY distancia_m
    """)

    result = await db.execute(query, {
        "wkt": wkt_geom,
        "buffer": settings.BUFFER_AREAS_PROTEGIDAS_M
    })

    for row in result.fetchall():
        area = {
            "id": row.id,
            "nombre": row.nombre,
            "tipo": row.tipo,
            "categoria": row.categoria,
            "intersecta": row.intersecta,
            "distancia_m": round(row.distancia_m, 2) if row.distancia_m else None,
        }
        resultado["areas_protegidas"].append(area)

        if row.intersecta:
            resultado["alertas"].append({
                "tipo": "CRITICA",
                "categoria": "area_protegida",
                "mensaje": f"El proyecto intersecta con {row.tipo}: {row.nombre}",
                "trigger_eia": "Art. 11 letra d) - Localización en áreas protegidas",
            })

    # Glaciares
    query = text("""
        SELECT
            id,
            nombre,
            tipo,
            ST_Intersects(geom, ST_GeomFromText(:wkt, 4326)) as intersecta,
            ST_Distance(geom::geography, ST_GeomFromText(:wkt, 4326)::geography) as distancia_m
        FROM gis.glaciares
        WHERE ST_DWithin(
            geom::geography,
            ST_GeomFromText(:wkt, 4326)::geography,
            :buffer
        )
        ORDER BY distancia_m
    """)

    result = await db.execute(query, {
        "wkt": wkt_geom,
        "buffer": settings.BUFFER_GLACIARES_M
    })

    for row in result.fetchall():
        glaciar = {
            "id": row.id,
            "nombre": row.nombre,
            "tipo": row.tipo,
            "intersecta": row.intersecta,
            "distancia_m": round(row.distancia_m, 2) if row.distancia_m else None,
        }
        resultado["glaciares"].append(glaciar)

        if row.intersecta:
            resultado["alertas"].append({
                "tipo": "CRITICA",
                "categoria": "glaciar",
                "mensaje": f"El proyecto intersecta con glaciar: {row.nombre or 'Sin nombre'}",
                "trigger_eia": "Art. 11 letra b) - Efectos adversos sobre recursos naturales renovables",
            })

    # Comunidades indígenas
    query = text("""
        SELECT
            id,
            nombre,
            pueblo,
            es_adi,
            nombre_adi,
            ST_Distance(geom::geography, ST_GeomFromText(:wkt, 4326)::geography) as distancia_m
        FROM gis.comunidades_indigenas
        WHERE ST_DWithin(
            geom::geography,
            ST_GeomFromText(:wkt, 4326)::geography,
            :buffer
        )
        ORDER BY distancia_m
    """)

    result = await db.execute(query, {
        "wkt": wkt_geom,
        "buffer": settings.BUFFER_COMUNIDADES_M
    })

    for row in result.fetchall():
        comunidad = {
            "id": row.id,
            "nombre": row.nombre,
            "pueblo": row.pueblo,
            "es_adi": row.es_adi,
            "nombre_adi": row.nombre_adi,
            "distancia_m": round(row.distancia_m, 2) if row.distancia_m else None,
        }
        resultado["comunidades_indigenas"].append(comunidad)

        if row.distancia_m and row.distancia_m < 5000:
            resultado["alertas"].append({
                "tipo": "ALTA",
                "categoria": "comunidad_indigena",
                "mensaje": f"Comunidad {row.pueblo} '{row.nombre}' a {round(row.distancia_m)}m - Requiere consulta indígena",
                "trigger_eia": "Art. 11 letra c) y d) - Reasentamiento o alteración sistemas de vida",
            })

    # Cuerpos de agua
    query = text("""
        SELECT
            id,
            nombre,
            tipo,
            es_sitio_ramsar,
            ST_Intersects(geom, ST_GeomFromText(:wkt, 4326)) as intersecta,
            ST_Distance(geom::geography, ST_GeomFromText(:wkt, 4326)::geography) as distancia_m
        FROM gis.cuerpos_agua
        WHERE ST_DWithin(
            geom::geography,
            ST_GeomFromText(:wkt, 4326)::geography,
            :buffer
        )
        ORDER BY distancia_m
    """)

    result = await db.execute(query, {
        "wkt": wkt_geom,
        "buffer": settings.BUFFER_CUERPOS_AGUA_M
    })

    for row in result.fetchall():
        cuerpo = {
            "id": row.id,
            "nombre": row.nombre,
            "tipo": row.tipo,
            "es_sitio_ramsar": row.es_sitio_ramsar,
            "intersecta": row.intersecta,
            "distancia_m": round(row.distancia_m, 2) if row.distancia_m else None,
        }
        resultado["cuerpos_agua"].append(cuerpo)

        if row.intersecta or (row.distancia_m and row.distancia_m < 500):
            resultado["alertas"].append({
                "tipo": "ALTA",
                "categoria": "cuerpo_agua",
                "mensaje": f"{row.tipo} '{row.nombre or 'Sin nombre'}' {'intersectado' if row.intersecta else f'a {round(row.distancia_m)}m'}",
                "trigger_eia": "Art. 11 letra b) - Efectos sobre recursos hídricos",
            })

    # Centros poblados
    query = text("""
        SELECT
            id,
            nombre,
            tipo,
            poblacion,
            ST_Distance(geom::geography, ST_GeomFromText(:wkt, 4326)::geography) as distancia_m
        FROM gis.centros_poblados
        WHERE ST_DWithin(
            geom::geography,
            ST_GeomFromText(:wkt, 4326)::geography,
            :buffer
        )
        ORDER BY distancia_m
    """)

    result = await db.execute(query, {
        "wkt": wkt_geom,
        "buffer": settings.BUFFER_CENTROS_POBLADOS_M
    })

    for row in result.fetchall():
        centro = {
            "id": row.id,
            "nombre": row.nombre,
            "tipo": row.tipo,
            "poblacion": row.poblacion,
            "distancia_m": round(row.distancia_m, 2) if row.distancia_m else None,
        }
        resultado["centros_poblados"].append(centro)

        if row.distancia_m and row.distancia_m < 2000:
            resultado["alertas"].append({
                "tipo": "MEDIA",
                "categoria": "centro_poblado",
                "mensaje": f"{row.tipo or 'Centro poblado'} '{row.nombre}' a {round(row.distancia_m)}m ({row.poblacion or 'N/D'} hab.)",
                "trigger_eia": "Art. 11 letra a) - Riesgo para salud de la población",
            })

    return resultado


def evaluar_triggers_eia(resultado_gis: dict, datos_proyecto: dict) -> dict[str, Any]:
    """
    Evalúa los triggers del Art. 11 de la Ley 19.300 para determinar si
    el proyecto debe ingresar como DIA o EIA.

    Returns:
        Diccionario con clasificación y triggers detectados
    """
    logger.info("Evaluando triggers SEIA Art. 11")
    triggers = []
    requiere_eia = False

    # a) Riesgo para salud de la población
    centros_cercanos = [
        c for c in resultado_gis.get("centros_poblados", [])
        if c.get("distancia_m", float("inf")) < 2000
    ]
    if centros_cercanos:
        triggers.append({
            "letra": "a",
            "descripcion": "Riesgo para la salud de la población",
            "detalle": f"{len(centros_cercanos)} centro(s) poblado(s) a menos de 2km",
            "severidad": "MEDIA",
        })

    # b) Efectos adversos significativos sobre recursos naturales
    if resultado_gis.get("glaciares"):
        glaciares_afectados = [g for g in resultado_gis["glaciares"] if g.get("intersecta")]
        if glaciares_afectados:
            triggers.append({
                "letra": "b",
                "descripcion": "Efectos adversos sobre recursos naturales renovables",
                "detalle": f"Intersección con {len(glaciares_afectados)} glaciar(es)",
                "severidad": "CRITICA",
            })
            requiere_eia = True

    cuerpos_afectados = [c for c in resultado_gis.get("cuerpos_agua", []) if c.get("intersecta")]
    if cuerpos_afectados:
        triggers.append({
            "letra": "b",
            "descripcion": "Efectos adversos sobre recursos hídricos",
            "detalle": f"Intersección con {len(cuerpos_afectados)} cuerpo(s) de agua",
            "severidad": "ALTA",
        })

    # c) Reasentamiento de comunidades humanas
    # Se evalúa con datos del proyecto

    # d) Localización en áreas protegidas
    areas_afectadas = [a for a in resultado_gis.get("areas_protegidas", []) if a.get("intersecta")]
    if areas_afectadas:
        triggers.append({
            "letra": "d",
            "descripcion": "Localización en áreas protegidas",
            "detalle": f"Intersección con: {', '.join(a['nombre'] for a in areas_afectadas)}",
            "severidad": "CRITICA",
        })
        requiere_eia = True

    # Comunidades indígenas cercanas (implica c y d)
    comunidades_cercanas = [
        c for c in resultado_gis.get("comunidades_indigenas", [])
        if c.get("distancia_m", float("inf")) < 10000
    ]
    if comunidades_cercanas:
        triggers.append({
            "letra": "c/d",
            "descripcion": "Alteración significativa de sistemas de vida de grupos humanos / Pueblos indígenas",
            "detalle": f"{len(comunidades_cercanas)} comunidad(es) indígena(s) en radio de 10km",
            "severidad": "ALTA",
        })

    # Clasificación final
    if requiere_eia or any(t["severidad"] == "CRITICA" for t in triggers):
        clasificacion = "EIA"
        confianza = 0.9
    elif any(t["severidad"] == "ALTA" for t in triggers):
        clasificacion = "EIA"
        confianza = 0.7
    elif triggers:
        clasificacion = "DIA"
        confianza = 0.6
    else:
        clasificacion = "DIA"
        confianza = 0.8

    logger.info(f"Evaluación SEIA: {clasificacion} (confianza={confianza}, triggers={len(triggers)})")

    return {
        "via_ingreso_recomendada": clasificacion,
        "confianza": confianza,
        "triggers": triggers,
        "resumen": f"Se detectaron {len(triggers)} trigger(s) del Art. 11",
    }
