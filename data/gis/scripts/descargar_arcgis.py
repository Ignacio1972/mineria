#!/usr/bin/env python3
"""
Script para descargar capas desde ArcGIS REST Services y cargar a PostGIS.

Uso:
    python descargar_arcgis.py --capa snaspe
    python descargar_arcgis.py --capa snaspe --solo-descargar
    python descargar_arcgis.py --listar

Autor: Sistema Prefactibilidad Ambiental Minera
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from urllib.request import urlopen
from urllib.parse import quote

# Configuración base
BASE_URL = "https://services7.arcgis.com/UeyripQFTg6pfUe5/ArcGIS/rest/services"
DATA_DIR = "/var/www/mineria/data/gis"
PAGE_SIZE = 2000

# Configuración de PostGIS
PG_CONFIG = {
    "host": "localhost",
    "port": "5433",
    "dbname": "mineria",
    "user": "mineria",
    "password": "mineria_dev_2024"
}

# Catálogo de capas disponibles
CAPAS = {
    "snaspe": {
        "nombre": "Áreas SNASPE",
        "servicio": "Áreas_SNASPE_de_Chile",
        "tabla_destino": "gis.areas_protegidas",
        "carpeta_destino": "areas_protegidas",
        "archivo": "snaspe_arcgis_nacional_{year}.geojson",
        "mapeo_campos": {
            "nombre": "snaspe",
            "tipo": "tipo",
            "categoria": "'SNASPE'",
            "region": "nom_region",
            "comuna": "descrip",
            "superficie_ha": "superficie",
            "fuente": "'ArcGIS REST - SNASPE Chile'"
        }
    },
    "ramsar": {
        "nombre": "Sitios Ramsar",
        "servicio": "Sitios_Ramsar",
        "tabla_destino": "gis.areas_protegidas",
        "carpeta_destino": "areas_protegidas",
        "archivo": "ramsar_arcgis_nacional_{year}.geojson",
        "mapeo_campos": {
            "nombre": "nombre",
            "tipo": "'Sitio Ramsar'",
            "categoria": "'Ramsar'",
            "region": "region",
            "superficie_ha": "superficie",
            "fuente": "'ArcGIS REST - Sitios Ramsar'"
        }
    },
    "glaciares_aysen": {
        "nombre": "Glaciares Región de Aysén",
        "servicio": "Glaciares_Región_de_Aysén",
        "tabla_destino": "gis.glaciares",
        "carpeta_destino": "glaciares",
        "archivo": "glaciares_arcgis_aysen_{year}.geojson",
        "mapeo_campos": {
            "nombre": "nombre",
            "tipo": "tipo",
            "superficie_km2": "area_km2",
            "fuente": "'ArcGIS REST - Glaciares Aysén'"
        }
    },
    "glaciares_ohiggins": {
        "nombre": "Glaciares Región de O'Higgins",
        "servicio": "Glaciares_Región_de_O´Higgins",
        "tabla_destino": "gis.glaciares",
        "carpeta_destino": "glaciares",
        "archivo": "glaciares_arcgis_ohiggins_{year}.geojson",
        "mapeo_campos": {
            "nombre": "nombre",
            "tipo": "tipo",
            "superficie_km2": "area_km2",
            "fuente": "'ArcGIS REST - Glaciares OHiggins'"
        }
    },
    "regiones": {
        "nombre": "Regiones de Chile",
        "servicio": "División_político_administrativa_de_Chile",
        "layer_id": 0,  # Algunas capas tienen múltiples layers
        "tabla_destino": "gis.regiones",
        "carpeta_destino": "regiones",
        "archivo": "regiones_arcgis_{year}.geojson",
        "mapeo_campos": {
            "codigo": "cod_regi",
            "nombre": "nom_regi"
        }
    },
    "comunas": {
        "nombre": "Comunas de Chile",
        "servicio": "comunas",
        "tabla_destino": "gis.comunas",
        "carpeta_destino": "comunas",
        "archivo": "comunas_arcgis_{year}.geojson",
        "mapeo_campos": {
            "codigo": "cod_comuna",
            "nombre": "nom_comuna",
            "region_codigo": "cod_regi",
            "provincia": "nom_prov"
        }
    }
}


def get_service_url(servicio, layer_id=0):
    """Construye la URL del servicio ArcGIS."""
    encoded = quote(servicio, safe='')
    return f"{BASE_URL}/{encoded}/FeatureServer/{layer_id}"


def get_total_count(servicio, layer_id=0):
    """Obtiene el total de registros en la capa."""
    url = f"{get_service_url(servicio, layer_id)}/query?where=1=1&returnCountOnly=true&f=json"
    try:
        with urlopen(url, timeout=30) as response:
            data = json.loads(response.read().decode())
            return data.get('count', 0)
    except Exception as e:
        print(f"Error obteniendo conteo: {e}")
        return 0


def download_page(servicio, layer_id=0, offset=0):
    """Descarga una página de resultados."""
    url = (
        f"{get_service_url(servicio, layer_id)}/query?"
        f"where=1=1&outFields=*&f=geojson&resultOffset={offset}&resultRecordCount={PAGE_SIZE}"
    )
    try:
        with urlopen(url, timeout=120) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        print(f"Error descargando página (offset={offset}): {e}")
        return None


def download_layer(capa_id):
    """Descarga una capa completa con paginación."""
    if capa_id not in CAPAS:
        print(f"Error: Capa '{capa_id}' no encontrada")
        return None

    config = CAPAS[capa_id]
    servicio = config['servicio']
    layer_id = config.get('layer_id', 0)

    print(f"\n{'='*60}")
    print(f"Descargando: {config['nombre']}")
    print(f"Servicio: {servicio}")
    print(f"{'='*60}")

    # Obtener total
    total = get_total_count(servicio, layer_id)
    if total == 0:
        print("No se encontraron registros")
        return None

    print(f"Total registros: {total}")

    # Descargar con paginación
    all_features = []
    offset = 0
    page = 1

    while offset < total:
        print(f"  Página {page}: descargando registros {offset+1}-{min(offset+PAGE_SIZE, total)}...")
        data = download_page(servicio, layer_id, offset)

        if data and 'features' in data:
            all_features.extend(data['features'])
            print(f"    ✓ {len(data['features'])} features descargados")
        else:
            print(f"    ✗ Error en página {page}")
            break

        offset += PAGE_SIZE
        page += 1

    print(f"\nTotal features descargados: {len(all_features)}")

    # Crear GeoJSON final
    year = datetime.now().year
    geojson = {
        "type": "FeatureCollection",
        "name": capa_id,
        "crs": {
            "type": "name",
            "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}
        },
        "metadata": {
            "fuente": "ArcGIS REST Services",
            "servicio": servicio,
            "url": get_service_url(servicio, layer_id),
            "fecha_descarga": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_features": len(all_features)
        },
        "features": all_features
    }

    # Guardar archivo
    carpeta = os.path.join(DATA_DIR, "procesados", config['carpeta_destino'])
    os.makedirs(carpeta, exist_ok=True)

    archivo = config['archivo'].format(year=year)
    filepath = os.path.join(carpeta, archivo)

    with open(filepath, 'w') as f:
        json.dump(geojson, f)

    size_mb = os.path.getsize(filepath) / 1024 / 1024
    print(f"\n✓ Guardado: {filepath}")
    print(f"  Tamaño: {size_mb:.2f} MB")

    return filepath


def load_to_postgis(capa_id, filepath):
    """Carga un GeoJSON a PostGIS usando ogr2ogr."""
    if capa_id not in CAPAS:
        print(f"Error: Capa '{capa_id}' no encontrada")
        return False

    config = CAPAS[capa_id]
    tabla = config['tabla_destino']
    tabla_temp = f"{tabla}_temp"

    print(f"\n{'='*60}")
    print(f"Cargando a PostGIS: {tabla}")
    print(f"{'='*60}")

    # Construir connection string
    pg_conn = (
        f"PG:host={PG_CONFIG['host']} "
        f"port={PG_CONFIG['port']} "
        f"dbname={PG_CONFIG['dbname']} "
        f"user={PG_CONFIG['user']} "
        f"password={PG_CONFIG['password']}"
    )

    # Cargar con ogr2ogr a tabla temporal
    cmd = [
        "ogr2ogr", "-f", "PostgreSQL",
        pg_conn,
        filepath,
        "-nln", tabla_temp,
        "-overwrite",
        "-lco", "GEOMETRY_NAME=geom",
        "-nlt", "PROMOTE_TO_MULTI",
        "-t_srs", "EPSG:4326"
    ]

    print("Ejecutando ogr2ogr...")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"Error ogr2ogr: {result.stderr}")
        return False

    print("✓ Datos cargados en tabla temporal")

    # Construir INSERT con mapeo de campos
    mapeo = config['mapeo_campos']
    campos_destino = list(mapeo.keys())
    campos_origen = list(mapeo.values())

    # Agregar geom
    campos_destino.append("geom")
    campos_origen.append("geom")

    insert_sql = f"""
    INSERT INTO {tabla} ({', '.join(campos_destino)})
    SELECT {', '.join(campos_origen)}
    FROM {tabla_temp};
    """

    # Ejecutar en PostgreSQL via docker
    psql_cmd = [
        "docker", "exec", "mineria_postgis",
        "psql", "-U", PG_CONFIG['user'], "-d", PG_CONFIG['dbname'],
        "-c", insert_sql
    ]

    print("Insertando datos con mapeo de campos...")
    result = subprocess.run(psql_cmd, capture_output=True, text=True)

    if "INSERT" in result.stdout:
        count = result.stdout.strip().split()[-1]
        print(f"✓ {count} registros insertados en {tabla}")
    else:
        print(f"Resultado: {result.stdout}")
        if result.stderr:
            print(f"Error: {result.stderr}")

    # Limpiar tabla temporal
    drop_cmd = [
        "docker", "exec", "mineria_postgis",
        "psql", "-U", PG_CONFIG['user'], "-d", PG_CONFIG['dbname'],
        "-c", f"DROP TABLE IF EXISTS {tabla_temp};"
    ]
    subprocess.run(drop_cmd, capture_output=True)
    print("✓ Tabla temporal eliminada")

    return True


def listar_capas():
    """Lista las capas disponibles."""
    print("\n" + "="*60)
    print("CAPAS DISPONIBLES")
    print("="*60)

    for capa_id, config in CAPAS.items():
        print(f"\n  {capa_id}:")
        print(f"    Nombre: {config['nombre']}")
        print(f"    Tabla destino: {config['tabla_destino']}")

        # Intentar obtener conteo
        total = get_total_count(config['servicio'], config.get('layer_id', 0))
        if total > 0:
            print(f"    Registros disponibles: {total}")


def actualizar_catalogo(capa_id, filepath, count):
    """Actualiza el catálogo de capas."""
    catalogo_path = os.path.join(DATA_DIR, "catalogo.json")

    try:
        with open(catalogo_path) as f:
            catalogo = json.load(f)
    except:
        return

    # Buscar la capa en el catálogo
    config = CAPAS[capa_id]
    for capa in catalogo.get('capas', []):
        if capa['id'] == config['carpeta_destino'] or capa['id'] in capa_id:
            archivo_info = {
                "archivo": os.path.basename(filepath),
                "fuente": "ArcGIS REST Services",
                "fecha_descarga": datetime.now().strftime("%Y-%m-%d"),
                "registros": count,
                "cargado_bd": True
            }

            # Evitar duplicados
            archivos = capa.get('archivos', [])
            archivos = [a for a in archivos if a['archivo'] != archivo_info['archivo']]
            archivos.append(archivo_info)
            capa['archivos'] = archivos
            break

    catalogo['actualizado'] = datetime.now().strftime("%Y-%m-%d")

    with open(catalogo_path, 'w') as f:
        json.dump(catalogo, f, indent=2, ensure_ascii=False)

    print(f"✓ Catálogo actualizado: {catalogo_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Descarga capas desde ArcGIS REST Services y carga a PostGIS"
    )
    parser.add_argument(
        "--capa", "-c",
        help="ID de la capa a descargar (ej: snaspe, ramsar, regiones)"
    )
    parser.add_argument(
        "--listar", "-l",
        action="store_true",
        help="Listar capas disponibles"
    )
    parser.add_argument(
        "--solo-descargar", "-d",
        action="store_true",
        help="Solo descargar, no cargar a PostGIS"
    )
    parser.add_argument(
        "--solo-cargar", "-p",
        help="Solo cargar a PostGIS desde archivo existente"
    )

    args = parser.parse_args()

    if args.listar:
        listar_capas()
        return

    if args.solo_cargar:
        if not args.capa:
            print("Error: Se requiere --capa para identificar el mapeo")
            sys.exit(1)
        load_to_postgis(args.capa, args.solo_cargar)
        return

    if not args.capa:
        print("Error: Se requiere --capa o --listar")
        parser.print_help()
        sys.exit(1)

    # Descargar
    filepath = download_layer(args.capa)

    if filepath and not args.solo_descargar:
        # Cargar a PostGIS
        load_to_postgis(args.capa, filepath)

        # Actualizar catálogo
        with open(filepath) as f:
            data = json.load(f)
            count = len(data.get('features', []))
        actualizar_catalogo(args.capa, filepath, count)


if __name__ == "__main__":
    main()
