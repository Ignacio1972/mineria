-- Habilitar extensiones necesarias
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS vector;  -- pgvector para búsqueda semántica

-- Verificar instalación
SELECT PostGIS_Version();
