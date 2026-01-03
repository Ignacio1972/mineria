#!/usr/bin/env python3
"""
Script para cargar la división político-administrativa de Chile.
Carga regiones y comunas necesarias para geocodificación inversa.
"""
import os
import sys
from sqlalchemy import create_engine, text

# Configuración de base de datos
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://mineria:mineria_dev_2024@localhost:5433/mineria"
)



def cargar_datos_minimos():
    """Carga datos mínimos de regiones principales para testing."""
    engine = create_engine(DATABASE_URL)

    # Datos mínimos de regiones con bounding boxes aproximados
    regiones_minimas = [
        ("13", "Metropolitana", "POLYGON((-71.5 -34.2, -69.8 -34.2, -69.8 -32.9, -71.5 -32.9, -71.5 -34.2))"),
        ("05", "Valparaiso", "POLYGON((-72.0 -34.0, -70.0 -34.0, -70.0 -32.0, -72.0 -32.0, -72.0 -34.0))"),
        ("06", "O'Higgins", "POLYGON((-71.8 -35.1, -70.0 -35.1, -70.0 -33.8, -71.8 -33.8, -71.8 -35.1))"),
        ("07", "Maule", "POLYGON((-72.5 -36.5, -70.3 -36.5, -70.3 -34.7, -72.5 -34.7, -72.5 -36.5))"),
        ("08", "Biobio", "POLYGON((-73.5 -38.5, -71.0 -38.5, -71.0 -36.0, -73.5 -36.0, -73.5 -38.5))"),
    ]

    comunas_minimas = [
        # Región Metropolitana
        ("13101", "Santiago", "13", "Santiago", "POLYGON((-70.68 -33.48, -70.62 -33.48, -70.62 -33.42, -70.68 -33.42, -70.68 -33.48))"),
        ("13115", "Lo Barnechea", "13", "Santiago", "POLYGON((-70.55 -33.45, -70.30 -33.45, -70.30 -33.25, -70.55 -33.25, -70.55 -33.45))"),
        ("13201", "Puente Alto", "13", "Cordillera", "POLYGON((-70.60 -33.65, -70.45 -33.65, -70.45 -33.55, -70.60 -33.55, -70.60 -33.65))"),
        ("13401", "San Bernardo", "13", "Maipo", "POLYGON((-70.75 -33.65, -70.60 -33.65, -70.60 -33.55, -70.75 -33.55, -70.75 -33.65))"),
        ("13301", "Colina", "13", "Chacabuco", "POLYGON((-70.75 -33.25, -70.55 -33.25, -70.55 -33.15, -70.75 -33.15, -70.75 -33.25))"),
    ]

    print("Insertando datos mínimos de regiones...")
    with engine.connect() as conn:
        for codigo, nombre, geom_wkt in regiones_minimas:
            conn.execute(text("""
                INSERT INTO gis.regiones (codigo, nombre, geom)
                VALUES (:codigo, :nombre, ST_Multi(ST_GeomFromText(:geom, 4326)))
                ON CONFLICT (codigo) DO UPDATE SET
                    nombre = EXCLUDED.nombre,
                    geom = EXCLUDED.geom
            """), {"codigo": codigo, "nombre": nombre, "geom": geom_wkt})
        conn.commit()

    print("Insertando datos mínimos de comunas...")
    with engine.connect() as conn:
        for codigo, nombre, region_codigo, provincia, geom_wkt in comunas_minimas:
            conn.execute(text("""
                INSERT INTO gis.comunas (codigo, nombre, region_codigo, provincia, geom)
                VALUES (:codigo, :nombre, :region_codigo, :provincia,
                        ST_Multi(ST_GeomFromText(:geom, 4326)))
                ON CONFLICT (codigo) DO UPDATE SET
                    nombre = EXCLUDED.nombre,
                    region_codigo = EXCLUDED.region_codigo,
                    provincia = EXCLUDED.provincia,
                    geom = EXCLUDED.geom
            """), {
                "codigo": codigo,
                "nombre": nombre,
                "region_codigo": region_codigo,
                "provincia": provincia,
                "geom": geom_wkt
            })
        conn.commit()

    print("Datos mínimos insertados.")


def verificar_datos():
    """Verifica los datos cargados."""
    engine = create_engine(DATABASE_URL)

    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM gis.regiones"))
        print(f"Total regiones: {result.scalar()}")

        result = conn.execute(text("SELECT COUNT(*) FROM gis.comunas"))
        print(f"Total comunas: {result.scalar()}")

        # Mostrar algunas
        result = conn.execute(text("""
            SELECT c.nombre as comuna, r.nombre as region
            FROM gis.comunas c
            JOIN gis.regiones r ON c.region_codigo = r.codigo
            LIMIT 10
        """))
        print("\nEjemplos de comunas:")
        for row in result:
            print(f"  - {row.comuna}, {row.region}")


if __name__ == "__main__":
    cargar_datos_minimos()
    verificar_datos()
