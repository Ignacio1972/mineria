-- ============================================
-- ÍNDICES GEOGRÁFICOS PARA OPTIMIZACIÓN
-- ============================================
-- Ejecutar manualmente si la BD ya existe:
-- docker exec -i mineria_postgis psql -U mineria -d mineria < 04_add_geography_indexes.sql

-- Los índices sobre geometry::geography permiten usar ST_DWithin eficientemente

CREATE INDEX IF NOT EXISTS idx_areas_protegidas_geog
    ON gis.areas_protegidas USING GIST((geom::geography));

CREATE INDEX IF NOT EXISTS idx_glaciares_geog
    ON gis.glaciares USING GIST((geom::geography));

CREATE INDEX IF NOT EXISTS idx_cuerpos_agua_geog
    ON gis.cuerpos_agua USING GIST((geom::geography));

CREATE INDEX IF NOT EXISTS idx_comunidades_indigenas_geog
    ON gis.comunidades_indigenas USING GIST((geom::geography));

CREATE INDEX IF NOT EXISTS idx_centros_poblados_geog
    ON gis.centros_poblados USING GIST((geom::geography));

CREATE INDEX IF NOT EXISTS idx_sitios_patrimoniales_geog
    ON gis.sitios_patrimoniales USING GIST((geom::geography));

-- Actualizar estadísticas para el planificador de queries
ANALYZE gis.areas_protegidas;
ANALYZE gis.glaciares;
ANALYZE gis.cuerpos_agua;
ANALYZE gis.comunidades_indigenas;
ANALYZE gis.centros_poblados;
ANALYZE gis.sitios_patrimoniales;

-- Verificar índices creados
SELECT
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size
FROM pg_indexes
WHERE schemaname = 'gis'
    AND indexname LIKE '%geog%'
ORDER BY tablename;
