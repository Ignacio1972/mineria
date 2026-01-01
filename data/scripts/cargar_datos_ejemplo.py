#!/usr/bin/env python3
"""
Script para cargar datos GIS de ejemplo en la base de datos.
Estos datos son ficticios y solo para propósitos de desarrollo/testing.
Para producción, usar datos oficiales de IDE Chile, CONAF, DGA, etc.
"""

import asyncio
import asyncpg
from typing import Any


# Datos de ejemplo para la Región de Antofagasta
AREAS_PROTEGIDAS_EJEMPLO = [
    {
        "nombre": "Reserva Nacional Los Flamencos",
        "tipo": "Reserva Nacional",
        "categoria": "SNASPE",
        "region": "Antofagasta",
        "comuna": "San Pedro de Atacama",
        "superficie_ha": 73987,
        "wkt": "MULTIPOLYGON(((-68.2 -23.1, -67.8 -23.1, -67.8 -23.5, -68.2 -23.5, -68.2 -23.1)))",
    },
    {
        "nombre": "Parque Nacional Llullaillaco",
        "tipo": "Parque Nacional",
        "categoria": "SNASPE",
        "region": "Antofagasta",
        "comuna": "Antofagasta",
        "superficie_ha": 268671,
        "wkt": "MULTIPOLYGON(((-68.8 -24.6, -68.4 -24.6, -68.4 -25.0, -68.8 -25.0, -68.8 -24.6)))",
    },
    {
        "nombre": "Monumento Natural La Portada",
        "tipo": "Monumento Natural",
        "categoria": "SNASPE",
        "region": "Antofagasta",
        "comuna": "Antofagasta",
        "superficie_ha": 31,
        "wkt": "MULTIPOLYGON(((-70.42 -23.48, -70.40 -23.48, -70.40 -23.50, -70.42 -23.50, -70.42 -23.48)))",
    },
]

GLACIARES_EJEMPLO = [
    {
        "nombre": "Glaciar El Tatio",
        "tipo": "Glaciarete",
        "cuenca": "Salar de Atacama",
        "region": "Antofagasta",
        "superficie_km2": 0.8,
        "altitud_min_m": 4200,
        "altitud_max_m": 4800,
        "wkt": "MULTIPOLYGON(((-68.02 -22.32, -68.00 -22.32, -68.00 -22.34, -68.02 -22.34, -68.02 -22.32)))",
    },
    {
        "nombre": "Campo de nieve Licancabur",
        "tipo": "Campo de nieve",
        "cuenca": "Salar de Atacama",
        "region": "Antofagasta",
        "superficie_km2": 0.3,
        "altitud_min_m": 5500,
        "altitud_max_m": 5920,
        "wkt": "MULTIPOLYGON(((-67.88 -22.83, -67.86 -22.83, -67.86 -22.85, -67.88 -22.85, -67.88 -22.83)))",
    },
]

CUERPOS_AGUA_EJEMPLO = [
    {
        "nombre": "Río Loa",
        "tipo": "Río",
        "cuenca": "Río Loa",
        "region": "Antofagasta",
        "es_sitio_ramsar": False,
        "wkt": "LINESTRING(-69.5 -21.5, -69.0 -22.0, -68.5 -22.5, -70.0 -23.5)",
    },
    {
        "nombre": "Salar de Atacama",
        "tipo": "Salar",
        "cuenca": "Salar de Atacama",
        "region": "Antofagasta",
        "es_sitio_ramsar": True,
        "wkt": "POLYGON((-68.5 -23.0, -68.0 -23.0, -68.0 -23.8, -68.5 -23.8, -68.5 -23.0))",
    },
    {
        "nombre": "Laguna Chaxa",
        "tipo": "Laguna",
        "cuenca": "Salar de Atacama",
        "region": "Antofagasta",
        "es_sitio_ramsar": True,
        "wkt": "POLYGON((-68.18 -23.28, -68.16 -23.28, -68.16 -23.30, -68.18 -23.30, -68.18 -23.28))",
    },
]

COMUNIDADES_INDIGENAS_EJEMPLO = [
    {
        "nombre": "Comunidad Atacameña de Toconao",
        "pueblo": "Atacameño",
        "tipo": "Comunidad",
        "region": "Antofagasta",
        "comuna": "San Pedro de Atacama",
        "es_adi": True,
        "nombre_adi": "ADI Atacama La Grande",
        "wkt": "POINT(-68.0 -23.2)",
    },
    {
        "nombre": "Comunidad Atacameña de Socaire",
        "pueblo": "Atacameño",
        "tipo": "Comunidad",
        "region": "Antofagasta",
        "comuna": "San Pedro de Atacama",
        "es_adi": True,
        "nombre_adi": "ADI Atacama La Grande",
        "wkt": "POINT(-67.9 -23.6)",
    },
    {
        "nombre": "Comunidad Atacameña de Peine",
        "pueblo": "Atacameño",
        "tipo": "Comunidad",
        "region": "Antofagasta",
        "comuna": "San Pedro de Atacama",
        "es_adi": True,
        "nombre_adi": "ADI Atacama La Grande",
        "wkt": "POINT(-68.1 -23.7)",
    },
    {
        "nombre": "Comunidad Quechua de Ollagüe",
        "pueblo": "Quechua",
        "tipo": "Comunidad",
        "region": "Antofagasta",
        "comuna": "Ollagüe",
        "es_adi": False,
        "nombre_adi": None,
        "wkt": "POINT(-68.25 -21.22)",
    },
]

CENTROS_POBLADOS_EJEMPLO = [
    {
        "nombre": "Antofagasta",
        "tipo": "Ciudad",
        "region": "Antofagasta",
        "comuna": "Antofagasta",
        "poblacion": 361873,
        "wkt": "POINT(-70.4 -23.65)",
    },
    {
        "nombre": "Calama",
        "tipo": "Ciudad",
        "region": "Antofagasta",
        "comuna": "Calama",
        "poblacion": 165731,
        "wkt": "POINT(-68.93 -22.46)",
    },
    {
        "nombre": "San Pedro de Atacama",
        "tipo": "Pueblo",
        "region": "Antofagasta",
        "comuna": "San Pedro de Atacama",
        "poblacion": 10996,
        "wkt": "POINT(-68.2 -22.91)",
    },
    {
        "nombre": "Tocopilla",
        "tipo": "Ciudad",
        "region": "Antofagasta",
        "comuna": "Tocopilla",
        "poblacion": 25186,
        "wkt": "POINT(-70.2 -22.09)",
    },
    {
        "nombre": "Taltal",
        "tipo": "Ciudad",
        "region": "Antofagasta",
        "comuna": "Taltal",
        "poblacion": 13317,
        "wkt": "POINT(-70.48 -25.41)",
    },
]

REGIONES_EJEMPLO = [
    {
        "codigo": "02",
        "nombre": "Antofagasta",
        "wkt": "MULTIPOLYGON(((-70.6 -21.0, -67.0 -21.0, -67.0 -26.1, -70.6 -26.1, -70.6 -21.0)))",
    },
]

COMUNAS_EJEMPLO = [
    {
        "codigo": "02101",
        "nombre": "Antofagasta",
        "region_codigo": "02",
        "provincia": "Antofagasta",
        "wkt": "MULTIPOLYGON(((-70.6 -23.3, -69.5 -23.3, -69.5 -24.5, -70.6 -24.5, -70.6 -23.3)))",
    },
    {
        "codigo": "02201",
        "nombre": "Calama",
        "region_codigo": "02",
        "provincia": "El Loa",
        "wkt": "MULTIPOLYGON(((-69.5 -21.5, -67.5 -21.5, -67.5 -23.3, -69.5 -23.3, -69.5 -21.5)))",
    },
    {
        "codigo": "02203",
        "nombre": "San Pedro de Atacama",
        "region_codigo": "02",
        "provincia": "El Loa",
        "wkt": "MULTIPOLYGON(((-68.5 -22.5, -67.0 -22.5, -67.0 -24.5, -68.5 -24.5, -68.5 -22.5)))",
    },
]


async def cargar_datos(db_url: str):
    """Carga los datos de ejemplo en la base de datos."""

    conn = await asyncpg.connect(db_url)

    try:
        print("Cargando datos de ejemplo...")

        # Regiones
        print("  - Regiones...")
        for r in REGIONES_EJEMPLO:
            await conn.execute("""
                INSERT INTO gis.regiones (codigo, nombre, geom)
                VALUES ($1, $2, ST_GeomFromText($3, 4326))
                ON CONFLICT (codigo) DO NOTHING
            """, r["codigo"], r["nombre"], r["wkt"])

        # Comunas
        print("  - Comunas...")
        for c in COMUNAS_EJEMPLO:
            await conn.execute("""
                INSERT INTO gis.comunas (codigo, nombre, region_codigo, provincia, geom)
                VALUES ($1, $2, $3, $4, ST_GeomFromText($5, 4326))
                ON CONFLICT (codigo) DO NOTHING
            """, c["codigo"], c["nombre"], c["region_codigo"], c["provincia"], c["wkt"])

        # Áreas protegidas
        print("  - Áreas protegidas...")
        for ap in AREAS_PROTEGIDAS_EJEMPLO:
            await conn.execute("""
                INSERT INTO gis.areas_protegidas
                (nombre, tipo, categoria, region, comuna, superficie_ha, geom)
                VALUES ($1, $2, $3, $4, $5, $6, ST_GeomFromText($7, 4326))
            """, ap["nombre"], ap["tipo"], ap["categoria"], ap["region"],
                ap["comuna"], ap["superficie_ha"], ap["wkt"])

        # Glaciares
        print("  - Glaciares...")
        for g in GLACIARES_EJEMPLO:
            await conn.execute("""
                INSERT INTO gis.glaciares
                (nombre, tipo, cuenca, region, superficie_km2, altitud_min_m, altitud_max_m, geom)
                VALUES ($1, $2, $3, $4, $5, $6, $7, ST_GeomFromText($8, 4326))
            """, g["nombre"], g["tipo"], g["cuenca"], g["region"],
                g["superficie_km2"], g["altitud_min_m"], g["altitud_max_m"], g["wkt"])

        # Cuerpos de agua
        print("  - Cuerpos de agua...")
        for ca in CUERPOS_AGUA_EJEMPLO:
            await conn.execute("""
                INSERT INTO gis.cuerpos_agua
                (nombre, tipo, cuenca, region, es_sitio_ramsar, geom)
                VALUES ($1, $2, $3, $4, $5, ST_GeomFromText($6, 4326))
            """, ca["nombre"], ca["tipo"], ca["cuenca"], ca["region"],
                ca["es_sitio_ramsar"], ca["wkt"])

        # Comunidades indígenas
        print("  - Comunidades indígenas...")
        for ci in COMUNIDADES_INDIGENAS_EJEMPLO:
            await conn.execute("""
                INSERT INTO gis.comunidades_indigenas
                (nombre, pueblo, tipo, region, comuna, es_adi, nombre_adi, geom)
                VALUES ($1, $2, $3, $4, $5, $6, $7, ST_GeomFromText($8, 4326))
            """, ci["nombre"], ci["pueblo"], ci["tipo"], ci["region"],
                ci["comuna"], ci["es_adi"], ci["nombre_adi"], ci["wkt"])

        # Centros poblados
        print("  - Centros poblados...")
        for cp in CENTROS_POBLADOS_EJEMPLO:
            await conn.execute("""
                INSERT INTO gis.centros_poblados
                (nombre, tipo, region, comuna, poblacion, geom)
                VALUES ($1, $2, $3, $4, $5, ST_GeomFromText($6, 4326))
            """, cp["nombre"], cp["tipo"], cp["region"], cp["comuna"],
                cp["poblacion"], cp["wkt"])

        print("\n✓ Datos de ejemplo cargados exitosamente!")

        # Mostrar resumen
        tables = [
            ("gis.regiones", "Regiones"),
            ("gis.comunas", "Comunas"),
            ("gis.areas_protegidas", "Áreas protegidas"),
            ("gis.glaciares", "Glaciares"),
            ("gis.cuerpos_agua", "Cuerpos de agua"),
            ("gis.comunidades_indigenas", "Comunidades indígenas"),
            ("gis.centros_poblados", "Centros poblados"),
        ]

        print("\nResumen de datos cargados:")
        for table, name in tables:
            count = await conn.fetchval(f"SELECT COUNT(*) FROM {table}")
            print(f"  {name}: {count} registros")

    finally:
        await conn.close()


if __name__ == "__main__":
    import os

    db_url = os.getenv(
        "DATABASE_URL",
        "postgresql://mineria:mineria_dev_2024@localhost:5432/mineria"
    )

    asyncio.run(cargar_datos(db_url))
