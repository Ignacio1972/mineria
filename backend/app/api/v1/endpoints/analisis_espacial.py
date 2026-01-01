from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import Any
import time

from app.db.session import get_db
from app.services.gis.analisis import analizar_proyecto_espacial, evaluar_triggers_eia


router = APIRouter()


class GeometryInput(BaseModel):
    """GeoJSON Geometry input."""
    type: str = Field(..., description="Tipo de geometría (Polygon, MultiPolygon)")
    coordinates: list = Field(..., description="Coordenadas del polígono")


class ProyectoInput(BaseModel):
    """Datos básicos del proyecto para análisis."""
    nombre: str = Field(..., description="Nombre del proyecto")
    geometria: GeometryInput = Field(..., description="Polígono del proyecto en GeoJSON")
    tipo_mineria: str | None = Field(None, description="Tipo de minería")
    mineral_principal: str | None = Field(None, description="Mineral principal")

    class Config:
        json_schema_extra = {
            "example": {
                "nombre": "Proyecto Minero Ejemplo",
                "geometria": {
                    "type": "Polygon",
                    "coordinates": [[
                        [-69.5, -23.5],
                        [-69.4, -23.5],
                        [-69.4, -23.4],
                        [-69.5, -23.4],
                        [-69.5, -23.5]
                    ]]
                },
                "tipo_mineria": "Cielo abierto",
                "mineral_principal": "Cobre"
            }
        }


class AnalisisResponse(BaseModel):
    """Respuesta del análisis espacial."""
    proyecto: str
    tiempo_ms: int
    resultado_gis: dict[str, Any]
    clasificacion_seia: dict[str, Any]
    alertas: list[dict[str, Any]]


@router.post(
    "/analisis-espacial",
    response_model=AnalisisResponse,
    summary="Análisis espacial de proyecto",
    description="""
    Realiza un análisis espacial del polígono del proyecto contra las capas GIS
    (áreas protegidas, glaciares, cuerpos de agua, comunidades indígenas, etc.)
    y evalúa los triggers del Art. 11 de la Ley 19.300.
    """
)
async def analisis_espacial(
    proyecto: ProyectoInput,
    db: AsyncSession = Depends(get_db),
) -> AnalisisResponse:
    """Endpoint principal de análisis espacial."""

    start_time = time.time()

    try:
        # Convertir a dict para GeoJSON
        geojson = proyecto.geometria.model_dump()

        # Análisis espacial
        resultado_gis = await analizar_proyecto_espacial(db, geojson)

        # Evaluar triggers SEIA
        clasificacion = evaluar_triggers_eia(
            resultado_gis,
            proyecto.model_dump()
        )

        tiempo_ms = int((time.time() - start_time) * 1000)

        return AnalisisResponse(
            proyecto=proyecto.nombre,
            tiempo_ms=tiempo_ms,
            resultado_gis=resultado_gis,
            clasificacion_seia=clasificacion,
            alertas=resultado_gis.get("alertas", []),
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error en análisis espacial: {str(e)}"
        )


TABLAS_GIS_PERMITIDAS = {
    "areas_protegidas",
    "glaciares",
    "cuerpos_agua",
    "comunidades_indigenas",
    "centros_poblados",
    "sitios_patrimoniales",
    "regiones",
    "comunas",
    "bienes_nacionales_protegidos",
}

TABLAS_GIS_NOMBRES = {
    "areas_protegidas": "Áreas Protegidas",
    "glaciares": "Glaciares",
    "cuerpos_agua": "Cuerpos de Agua",
    "comunidades_indigenas": "Comunidades Indígenas",
    "centros_poblados": "Centros Poblados",
    "sitios_patrimoniales": "Sitios Patrimoniales",
    "regiones": "Regiones",
    "comunas": "Comunas",
    "bienes_nacionales_protegidos": "Bienes Nacionales Protegidos",
}


@router.get(
    "/capas",
    summary="Listar capas GIS disponibles",
    description="Retorna las capas GIS disponibles y su cantidad de registros."
)
async def listar_capas(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """Lista las capas GIS disponibles."""
    from sqlalchemy import text

    capas = {}

    for tabla in TABLAS_GIS_PERMITIDAS:
        nombre = TABLAS_GIS_NOMBRES.get(tabla, tabla)
        try:
            result = await db.execute(
                text(f"SELECT COUNT(*) FROM gis.{tabla}")
            )
            count = result.scalar()
            capas[tabla] = {
                "nombre": nombre,
                "registros": count,
                "url_geojson": f"/api/v1/gis/capas/{tabla}/geojson",
                "url_wms": f"http://localhost:9085/geoserver/mineria/wms?service=WMS&version=1.1.0&request=GetMap&layers=mineria:{tabla}",
            }
        except Exception:
            capas[tabla] = {
                "nombre": nombre,
                "registros": 0,
                "error": "Tabla no disponible",
            }

    return {"capas": capas}


@router.get(
    "/capas/{capa}/geojson",
    summary="Obtener capa en formato GeoJSON",
    description="Retorna los features de una capa GIS en formato GeoJSON."
)
async def obtener_capa_geojson(
    capa: str,
    bbox: str | None = None,
    limit: int = 1000,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Obtiene los datos de una capa en formato GeoJSON.

    - **capa**: Nombre de la capa (areas_protegidas, glaciares, etc.)
    - **bbox**: Bounding box opcional (minx,miny,maxx,maxy)
    - **limit**: Límite de registros (default 1000)
    """
    from sqlalchemy import text

    if capa not in TABLAS_GIS_PERMITIDAS:
        raise HTTPException(
            status_code=400,
            detail=f"Capa '{capa}' no permitida. Capas disponibles: {list(TABLAS_GIS_PERMITIDAS)}"
        )

    # Construir query según la capa
    columns_map = {
        "areas_protegidas": "id, nombre, tipo, categoria, region, superficie_ha",
        "glaciares": "id, nombre, tipo, cuenca, region, superficie_km2",
        "cuerpos_agua": "id, nombre, tipo, cuenca, region, es_sitio_ramsar",
        "comunidades_indigenas": "id, nombre, pueblo, tipo, region, es_adi, nombre_adi",
        "centros_poblados": "id, nombre, tipo, region, comuna, poblacion",
        "sitios_patrimoniales": "id, nombre, tipo, categoria, region",
        "regiones": "id, codigo, nombre",
        "comunas": "id, codigo, nombre, region_codigo, provincia",
    }

    columns = columns_map.get(capa, "id, nombre")

    # Query base
    query = f"""
        SELECT
            {columns},
            ST_AsGeoJSON(geom)::json as geometry
        FROM gis.{capa}
    """

    # Filtro por bbox si se proporciona
    if bbox:
        try:
            minx, miny, maxx, maxy = map(float, bbox.split(","))
            query += f"""
                WHERE ST_Intersects(
                    geom,
                    ST_MakeEnvelope({minx}, {miny}, {maxx}, {maxy}, 4326)
                )
            """
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Formato de bbox inválido. Usar: minx,miny,maxx,maxy"
            )

    query += f" LIMIT {min(limit, 5000)}"

    try:
        result = await db.execute(text(query))
        rows = result.mappings().all()

        features = []
        for row in rows:
            row_dict = dict(row)
            geometry = row_dict.pop("geometry")
            features.append({
                "type": "Feature",
                "geometry": geometry,
                "properties": row_dict,
            })

        return {
            "type": "FeatureCollection",
            "name": capa,
            "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
            "features": features,
            "totalFeatures": len(features),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo capa: {str(e)}"
        )
