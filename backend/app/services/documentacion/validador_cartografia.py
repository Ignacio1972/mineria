"""
Validador de archivos de cartografía (Shapefile, GeoJSON, KML, GML).
Verifica formato, CRS (debe ser WGS84/EPSG:4326), y extrae metadatos.
"""
import json
import logging
import os
import tempfile
import zipfile
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.documento import DocumentoProyecto
from app.schemas.documento import ValidacionCartografiaResponse

logger = logging.getLogger(__name__)

# CRS válidos para SEA (WGS84)
CRS_WGS84_VALIDOS = [
    "EPSG:4326",
    "urn:ogc:def:crs:OGC:1.3:CRS84",
    "urn:ogc:def:crs:EPSG::4326",
    "WGS 84",
    "WGS84",
]

# Base path para storage
STORAGE_BASE_PATH = "/var/www/mineria/storage"


class ValidadorCartografia:
    """Validador de archivos de cartografía."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def validar_documento(
        self,
        documento_id: UUID
    ) -> ValidacionCartografiaResponse:
        """
        Valida un documento de cartografía.
        Soporta: .shp (en .zip), .geojson, .json, .kml, .gml
        """
        # Obtener documento
        documento = await self.db.get(DocumentoProyecto, documento_id)
        if not documento:
            return ValidacionCartografiaResponse(
                documento_id=documento_id,
                valido=False,
                errores=["Documento no encontrado"]
            )

        # Construir ruta completa
        archivo_path = os.path.join(STORAGE_BASE_PATH, documento.archivo_path)

        if not os.path.exists(archivo_path):
            return ValidacionCartografiaResponse(
                documento_id=documento_id,
                valido=False,
                errores=[f"Archivo no encontrado: {documento.archivo_path}"]
            )

        # Detectar tipo de archivo
        extension = Path(documento.nombre_original).suffix.lower()
        mime_type = documento.mime_type

        try:
            if extension == ".zip" or "zip" in mime_type:
                resultado = await self._validar_shapefile_zip(archivo_path)
            elif extension in [".geojson", ".json"]:
                resultado = await self._validar_geojson(archivo_path)
            elif extension == ".kml":
                resultado = await self._validar_kml(archivo_path)
            elif extension == ".gml":
                resultado = await self._validar_gml(archivo_path)
            else:
                return ValidacionCartografiaResponse(
                    documento_id=documento_id,
                    valido=False,
                    errores=[f"Formato no soportado: {extension}"]
                )

            resultado.documento_id = documento_id

            # Actualizar documento con resultado de validación
            await self._guardar_validacion(documento, resultado)

            return resultado

        except Exception as e:
            logger.error(f"Error validando cartografía {documento_id}: {e}")
            return ValidacionCartografiaResponse(
                documento_id=documento_id,
                valido=False,
                errores=[f"Error procesando archivo: {str(e)}"]
            )

    async def _validar_shapefile_zip(
        self,
        archivo_path: str
    ) -> ValidacionCartografiaResponse:
        """Valida un Shapefile comprimido en ZIP."""
        errores = []
        warnings = []

        # Extraer ZIP a directorio temporal
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                with zipfile.ZipFile(archivo_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
            except zipfile.BadZipFile:
                return ValidacionCartografiaResponse(
                    documento_id=UUID("00000000-0000-0000-0000-000000000000"),
                    valido=False,
                    errores=["Archivo ZIP corrupto o inválido"]
                )

            # Buscar archivos .shp
            shp_files = list(Path(temp_dir).rglob("*.shp"))

            if not shp_files:
                return ValidacionCartografiaResponse(
                    documento_id=UUID("00000000-0000-0000-0000-000000000000"),
                    valido=False,
                    errores=["No se encontró archivo .shp en el ZIP"]
                )

            if len(shp_files) > 1:
                warnings.append(f"ZIP contiene {len(shp_files)} shapefiles, usando el primero")

            shp_path = shp_files[0]

            # Verificar archivos requeridos del shapefile
            base_path = shp_path.with_suffix("")
            archivos_requeridos = [".shp", ".shx", ".dbf"]
            archivos_opcionales = [".prj", ".cpg", ".sbn", ".sbx"]

            for ext in archivos_requeridos:
                if not base_path.with_suffix(ext).exists():
                    errores.append(f"Falta archivo requerido: {base_path.name}{ext}")

            prj_existe = base_path.with_suffix(".prj").exists()
            if not prj_existe:
                warnings.append("Falta archivo .prj (proyección). Se asume WGS84 pero se recomienda incluirlo")

            if errores:
                return ValidacionCartografiaResponse(
                    documento_id=UUID("00000000-0000-0000-0000-000000000000"),
                    valido=False,
                    errores=errores,
                    warnings=warnings
                )

            # Usar GDAL/OGR para validar
            return await self._validar_con_ogr(str(shp_path), warnings)

    async def _validar_geojson(
        self,
        archivo_path: str
    ) -> ValidacionCartografiaResponse:
        """Valida un archivo GeoJSON."""
        errores = []
        warnings = []

        try:
            with open(archivo_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            return ValidacionCartografiaResponse(
                documento_id=UUID("00000000-0000-0000-0000-000000000000"),
                valido=False,
                errores=[f"JSON inválido: {str(e)}"]
            )
        except UnicodeDecodeError:
            # Intentar con otra codificación
            try:
                with open(archivo_path, 'r', encoding='latin-1') as f:
                    data = json.load(f)
                warnings.append("Archivo con codificación latin-1, se recomienda UTF-8")
            except Exception as e:
                return ValidacionCartografiaResponse(
                    documento_id=UUID("00000000-0000-0000-0000-000000000000"),
                    valido=False,
                    errores=[f"Error de codificación: {str(e)}"]
                )

        # Validar estructura GeoJSON
        if not isinstance(data, dict):
            errores.append("Estructura GeoJSON inválida")
            return ValidacionCartografiaResponse(
                documento_id=UUID("00000000-0000-0000-0000-000000000000"),
                valido=False,
                errores=errores
            )

        geojson_type = data.get("type")
        if geojson_type not in ["FeatureCollection", "Feature", "GeometryCollection",
                                 "Point", "MultiPoint", "LineString", "MultiLineString",
                                 "Polygon", "MultiPolygon"]:
            errores.append(f"Tipo GeoJSON no reconocido: {geojson_type}")

        # Detectar CRS
        crs_detectado = None
        crs_es_wgs84 = True  # GeoJSON por especificación es WGS84

        if "crs" in data:
            crs_info = data["crs"]
            if isinstance(crs_info, dict):
                props = crs_info.get("properties", {})
                crs_detectado = props.get("name", str(crs_info))

                # Verificar si es WGS84
                crs_es_wgs84 = any(
                    crs_valido.lower() in crs_detectado.lower()
                    for crs_valido in CRS_WGS84_VALIDOS
                )

                if not crs_es_wgs84:
                    errores.append(f"CRS no es WGS84: {crs_detectado}. SEA requiere EPSG:4326")
        else:
            crs_detectado = "EPSG:4326 (implícito)"
            warnings.append("GeoJSON sin CRS explícito, asumiendo WGS84 según especificación")

        # Contar features y detectar tipo de geometría
        num_features = 0
        tipos_geometria = set()
        bbox = None

        if geojson_type == "FeatureCollection":
            features = data.get("features", [])
            num_features = len(features)
            for feat in features:
                if isinstance(feat, dict) and "geometry" in feat:
                    geom = feat["geometry"]
                    if geom and "type" in geom:
                        tipos_geometria.add(geom["type"])

            bbox = data.get("bbox")

        elif geojson_type == "Feature":
            num_features = 1
            geom = data.get("geometry", {})
            if geom and "type" in geom:
                tipos_geometria.add(geom["type"])

        else:
            # Es una geometría directa
            num_features = 1
            tipos_geometria.add(geojson_type)

        tipo_geometria = ", ".join(tipos_geometria) if tipos_geometria else None

        # Calcular área si es polígono (aproximado)
        area_total_ha = None
        if "Polygon" in tipo_geometria or "MultiPolygon" in tipo_geometria:
            area_total_ha = await self._calcular_area_geojson(data)

        return ValidacionCartografiaResponse(
            documento_id=UUID("00000000-0000-0000-0000-000000000000"),
            valido=len(errores) == 0,
            crs_detectado=crs_detectado,
            crs_es_wgs84=crs_es_wgs84,
            tipo_geometria=tipo_geometria,
            num_features=num_features,
            bbox=bbox,
            area_total_ha=area_total_ha,
            errores=errores,
            warnings=warnings
        )

    async def _validar_kml(
        self,
        archivo_path: str
    ) -> ValidacionCartografiaResponse:
        """Valida un archivo KML."""
        warnings = []
        errores = []

        try:
            import xml.etree.ElementTree as ET
            tree = ET.parse(archivo_path)
            root = tree.getroot()

            # KML namespace
            ns = {'kml': 'http://www.opengis.net/kml/2.2'}

            # Buscar placemarks
            placemarks = root.findall('.//kml:Placemark', ns)
            if not placemarks:
                # Intentar sin namespace
                placemarks = root.findall('.//Placemark')

            num_features = len(placemarks)

            # Detectar tipos de geometría
            tipos_geometria = set()
            for pm in placemarks:
                for geom_type in ['Point', 'LineString', 'Polygon', 'MultiGeometry']:
                    if pm.find(f'.//kml:{geom_type}', ns) is not None or pm.find(f'.//{geom_type}') is not None:
                        tipos_geometria.add(geom_type)

            tipo_geometria = ", ".join(tipos_geometria) if tipos_geometria else "Desconocido"

            # KML siempre usa WGS84
            crs_detectado = "EPSG:4326 (KML estándar)"

            if num_features == 0:
                warnings.append("No se encontraron elementos Placemark en el KML")

            return ValidacionCartografiaResponse(
                documento_id=UUID("00000000-0000-0000-0000-000000000000"),
                valido=True,
                crs_detectado=crs_detectado,
                crs_es_wgs84=True,
                tipo_geometria=tipo_geometria,
                num_features=num_features,
                errores=errores,
                warnings=warnings
            )

        except ET.ParseError as e:
            return ValidacionCartografiaResponse(
                documento_id=UUID("00000000-0000-0000-0000-000000000000"),
                valido=False,
                errores=[f"XML/KML inválido: {str(e)}"]
            )

    async def _validar_gml(
        self,
        archivo_path: str
    ) -> ValidacionCartografiaResponse:
        """Valida un archivo GML."""
        # Similar a KML pero con namespaces GML
        warnings = []

        try:
            import xml.etree.ElementTree as ET
            tree = ET.parse(archivo_path)
            root = tree.getroot()

            # Detectar CRS del atributo srsName
            crs_detectado = None
            for elem in root.iter():
                srs = elem.get('srsName')
                if srs:
                    crs_detectado = srs
                    break

            crs_es_wgs84 = False
            if crs_detectado:
                crs_es_wgs84 = any(
                    crs_valido.lower() in crs_detectado.lower()
                    for crs_valido in CRS_WGS84_VALIDOS
                )
                if not crs_es_wgs84:
                    warnings.append(f"CRS detectado: {crs_detectado}. Verificar si es WGS84")
            else:
                warnings.append("No se detectó CRS en el GML")

            return ValidacionCartografiaResponse(
                documento_id=UUID("00000000-0000-0000-0000-000000000000"),
                valido=True,
                crs_detectado=crs_detectado or "No detectado",
                crs_es_wgs84=crs_es_wgs84,
                tipo_geometria="GML",
                num_features=0,  # Requeriría parsing más complejo
                warnings=warnings
            )

        except ET.ParseError as e:
            return ValidacionCartografiaResponse(
                documento_id=UUID("00000000-0000-0000-0000-000000000000"),
                valido=False,
                errores=[f"XML/GML inválido: {str(e)}"]
            )

    async def _validar_con_ogr(
        self,
        archivo_path: str,
        warnings_previos: List[str]
    ) -> ValidacionCartografiaResponse:
        """
        Valida usando GDAL/OGR (más preciso para Shapefiles).
        Requiere que osgeo esté instalado.
        """
        errores = []
        warnings = warnings_previos.copy()

        try:
            from osgeo import ogr, osr

            # Abrir archivo
            ds = ogr.Open(archivo_path)
            if ds is None:
                return ValidacionCartografiaResponse(
                    documento_id=UUID("00000000-0000-0000-0000-000000000000"),
                    valido=False,
                    errores=["No se pudo abrir el archivo con OGR"],
                    warnings=warnings
                )

            layer = ds.GetLayer(0)
            if layer is None:
                return ValidacionCartografiaResponse(
                    documento_id=UUID("00000000-0000-0000-0000-000000000000"),
                    valido=False,
                    errores=["No se encontró capa en el archivo"],
                    warnings=warnings
                )

            # Obtener CRS
            srs = layer.GetSpatialRef()
            crs_detectado = None
            crs_es_wgs84 = False

            if srs:
                crs_detectado = srs.GetAttrValue("AUTHORITY", 0)
                if crs_detectado:
                    epsg = srs.GetAttrValue("AUTHORITY", 1)
                    if epsg:
                        crs_detectado = f"{crs_detectado}:{epsg}"

                # Verificar si es WGS84
                wgs84 = osr.SpatialReference()
                wgs84.ImportFromEPSG(4326)
                crs_es_wgs84 = srs.IsSame(wgs84)

                if not crs_es_wgs84:
                    errores.append(f"CRS no es WGS84 (EPSG:4326): {crs_detectado}")
            else:
                warnings.append("No se detectó sistema de referencia espacial")
                crs_detectado = "No definido"

            # Contar features
            num_features = layer.GetFeatureCount()

            # Detectar tipo de geometría
            geom_type = ogr.GeometryTypeToName(layer.GetGeomType())

            # Obtener extent
            extent = layer.GetExtent()
            bbox = [extent[0], extent[2], extent[1], extent[3]] if extent else None

            # Calcular área total
            area_total_ha = None
            if "Polygon" in geom_type:
                area_total = 0
                layer.ResetReading()
                for feature in layer:
                    geom = feature.GetGeometryRef()
                    if geom:
                        # Área en unidades del CRS (grados si WGS84)
                        area_total += geom.GetArea()

                # Convertir a hectáreas (aproximado para WGS84)
                if crs_es_wgs84 and area_total > 0:
                    # 1 grado ≈ 111km en el ecuador
                    # Muy aproximado, mejor usar proyección local
                    area_total_ha = area_total * (111000 ** 2) / 10000

            ds = None  # Cerrar dataset

            return ValidacionCartografiaResponse(
                documento_id=UUID("00000000-0000-0000-0000-000000000000"),
                valido=len(errores) == 0,
                crs_detectado=crs_detectado,
                crs_es_wgs84=crs_es_wgs84,
                tipo_geometria=geom_type,
                num_features=num_features,
                bbox=bbox,
                area_total_ha=round(area_total_ha, 2) if area_total_ha else None,
                errores=errores,
                warnings=warnings
            )

        except ImportError:
            # GDAL no disponible, usar validación básica
            warnings.append("GDAL/OGR no disponible, validación limitada")
            return ValidacionCartografiaResponse(
                documento_id=UUID("00000000-0000-0000-0000-000000000000"),
                valido=True,
                crs_detectado="No verificado (GDAL no disponible)",
                crs_es_wgs84=False,
                tipo_geometria="Shapefile",
                warnings=warnings
            )

        except Exception as e:
            logger.error(f"Error en validación OGR: {e}")
            return ValidacionCartografiaResponse(
                documento_id=UUID("00000000-0000-0000-0000-000000000000"),
                valido=False,
                errores=[f"Error procesando con OGR: {str(e)}"],
                warnings=warnings
            )

    async def _calcular_area_geojson(self, data: dict) -> Optional[float]:
        """Calcula área aproximada de un GeoJSON en hectáreas."""
        try:
            # Intentar usar shapely si está disponible
            from shapely.geometry import shape
            from shapely.ops import transform
            import pyproj

            total_area = 0

            if data.get("type") == "FeatureCollection":
                features = data.get("features", [])
            elif data.get("type") == "Feature":
                features = [data]
            else:
                features = [{"geometry": data}]

            for feat in features:
                geom_data = feat.get("geometry")
                if not geom_data:
                    continue

                geom = shape(geom_data)

                # Transformar a proyección de área (UTM zona apropiada)
                # Usar centroide para determinar zona UTM
                centroid = geom.centroid
                utm_zone = int((centroid.x + 180) / 6) + 1
                hemisphere = 'north' if centroid.y >= 0 else 'south'

                # Crear transformación
                project = pyproj.Transformer.from_crs(
                    "EPSG:4326",
                    f"+proj=utm +zone={utm_zone} +{hemisphere} +datum=WGS84",
                    always_xy=True
                ).transform

                geom_utm = transform(project, geom)
                total_area += geom_utm.area

            # Convertir m² a hectáreas
            return round(total_area / 10000, 2) if total_area > 0 else None

        except ImportError:
            logger.debug("shapely/pyproj no disponibles para cálculo de área")
            return None
        except Exception as e:
            logger.warning(f"Error calculando área: {e}")
            return None

    async def _guardar_validacion(
        self,
        documento: DocumentoProyecto,
        resultado: ValidacionCartografiaResponse
    ):
        """Guarda el resultado de validación en el documento."""
        documento.validacion_formato = {
            "valido": resultado.valido,
            "crs": resultado.crs_detectado,
            "crs_es_wgs84": resultado.crs_es_wgs84,
            "tipo_geometria": resultado.tipo_geometria,
            "num_features": resultado.num_features,
            "bbox": resultado.bbox,
            "area_ha": resultado.area_total_ha,
            "errores": resultado.errores,
            "warnings": resultado.warnings
        }

        await self.db.commit()
