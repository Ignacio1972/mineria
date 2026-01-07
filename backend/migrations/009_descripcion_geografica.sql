-- Migración: Agregar campos de descripción geográfica automática
-- Fecha: 2026-01-03
-- Descripción: Agrega campos para almacenar descripción geográfica generada automáticamente
--              al ingresar el polígono del proyecto

-- Agregar columnas al modelo Proyecto
ALTER TABLE proyectos.proyectos
ADD COLUMN IF NOT EXISTS descripcion_geografica TEXT,
ADD COLUMN IF NOT EXISTS descripcion_geografica_fecha TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS descripcion_geografica_fuente VARCHAR(20) DEFAULT 'auto';

-- Comentarios para documentación
COMMENT ON COLUMN proyectos.proyectos.descripcion_geografica IS 'Descripción narrativa del lugar geográfico donde se emplaza el proyecto, generada automáticamente desde análisis GIS + LLM';
COMMENT ON COLUMN proyectos.proyectos.descripcion_geografica_fecha IS 'Fecha de generación o última actualización de la descripción geográfica';
COMMENT ON COLUMN proyectos.proyectos.descripcion_geografica_fuente IS 'Origen de la descripción: auto (generada por sistema) o manual (editada por usuario)';

-- Índice para búsquedas por fuente
CREATE INDEX IF NOT EXISTS idx_proyectos_desc_geo_fuente
ON proyectos.proyectos(descripcion_geografica_fuente)
WHERE descripcion_geografica IS NOT NULL;
