-- ============================================================================
-- Migración 004: Agregar proyecto_id a acciones_pendientes
-- Fecha: 2026-01-03
-- Descripción: Agrega FK directa a proyecto para queries eficientes
--              Resuelve BUG-006 de la auditoría
-- ============================================================================

-- Agregar columna proyecto_id
ALTER TABLE asistente.acciones_pendientes
ADD COLUMN IF NOT EXISTS proyecto_id INTEGER;

-- Crear índice para búsquedas por proyecto
CREATE INDEX IF NOT EXISTS idx_acciones_pendientes_proyecto_id
ON asistente.acciones_pendientes(proyecto_id);

-- Agregar FK a proyectos.proyectos
ALTER TABLE asistente.acciones_pendientes
DROP CONSTRAINT IF EXISTS fk_acciones_pendientes_proyecto;

ALTER TABLE asistente.acciones_pendientes
ADD CONSTRAINT fk_acciones_pendientes_proyecto
FOREIGN KEY (proyecto_id)
REFERENCES proyectos.proyectos(id)
ON DELETE SET NULL;

-- ============================================================================
-- Poblar datos existentes desde parametros JSONB o conversacion
-- ============================================================================

-- Paso 1: Desde parametros->>'proyecto_id' (herramientas como actualizar_proyecto)
UPDATE asistente.acciones_pendientes ap
SET proyecto_id = (ap.parametros->>'proyecto_id')::INTEGER
WHERE ap.proyecto_id IS NULL
  AND ap.parametros->>'proyecto_id' IS NOT NULL
  AND (ap.parametros->>'proyecto_id') ~ '^\d+$';

-- Paso 2: Desde conversacion.proyecto_activo_id (fallback)
UPDATE asistente.acciones_pendientes ap
SET proyecto_id = c.proyecto_activo_id
FROM asistente.conversaciones c
WHERE ap.conversacion_id = c.id
  AND ap.proyecto_id IS NULL
  AND c.proyecto_activo_id IS NOT NULL;

-- ============================================================================
-- Comentario de documentación
-- ============================================================================
COMMENT ON COLUMN asistente.acciones_pendientes.proyecto_id IS
'FK directa al proyecto asociado a la acción. Permite queries eficientes sin JOIN a conversaciones.';
