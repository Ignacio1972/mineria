-- Migración 010: Checklist de Componentes EIA y Workflow de Fases
-- Fecha: 2026-01-07
-- Objetivo: Agregar tabla de componentes EIA y campos de progreso al proyecto

-- ============================================================================
-- 1. TABLA: componentes_eia_checklist
-- ============================================================================
-- Almacena los 17 componentes EIA que deben completarse para cada proyecto
-- Se genera automáticamente durante el análisis completo

CREATE TABLE IF NOT EXISTS proyectos.componentes_eia_checklist (
    id SERIAL PRIMARY KEY,
    proyecto_id INTEGER NOT NULL REFERENCES proyectos.proyectos(id) ON DELETE CASCADE,
    analisis_id INTEGER REFERENCES proyectos.analisis(id) ON DELETE SET NULL,

    -- Identificación del componente
    componente VARCHAR(100) NOT NULL,  -- Clave única (ej: "linea_base_flora")
    capitulo INTEGER NOT NULL,         -- Capítulo EIA (1-11)
    nombre VARCHAR(200) NOT NULL,
    descripcion TEXT,

    -- Estado del componente
    requerido BOOLEAN DEFAULT true,
    prioridad VARCHAR(20) DEFAULT 'media',  -- 'alta' | 'media' | 'baja'
    estado VARCHAR(20) DEFAULT 'pendiente', -- 'pendiente' | 'en_progreso' | 'completado'
    progreso_porcentaje INTEGER DEFAULT 0,

    -- Material de apoyo del corpus RAG
    material_rag JSONB DEFAULT '[]'::jsonb,      -- Array de {documento_id, titulo, contenido, similitud}
    sugerencias_busqueda JSONB DEFAULT '[]'::jsonb, -- Array de strings con queries sugeridas

    -- Justificación de inclusión
    razon_inclusion TEXT,                        -- Por qué este componente es necesario
    triggers_relacionados VARCHAR[] DEFAULT '{}', -- Triggers Art. 11 relacionados (ej: ['c', 'e'])

    -- Auditoría
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraint: Un solo registro por componente por proyecto
    UNIQUE(proyecto_id, componente)
);

-- Índices para performance
CREATE INDEX idx_componentes_checklist_proyecto ON proyectos.componentes_eia_checklist(proyecto_id);
CREATE INDEX idx_componentes_checklist_estado ON proyectos.componentes_eia_checklist(estado);
CREATE INDEX idx_componentes_checklist_capitulo ON proyectos.componentes_eia_checklist(capitulo);

-- Comentarios
COMMENT ON TABLE proyectos.componentes_eia_checklist IS 'Checklist de componentes EIA generado durante análisis completo';
COMMENT ON COLUMN proyectos.componentes_eia_checklist.material_rag IS 'Fragmentos del corpus RAG relevantes para este componente';
COMMENT ON COLUMN proyectos.componentes_eia_checklist.triggers_relacionados IS 'Literales Art. 11 que justifican este componente';

-- ============================================================================
-- 2. MODIFICACIÓN: Añadir campos de workflow a proyectos.proyectos
-- ============================================================================
-- Agregar campos para trackear la fase actual y progreso global del proyecto

ALTER TABLE proyectos.proyectos
ADD COLUMN IF NOT EXISTS fase_actual VARCHAR(50) DEFAULT 'identificacion';

ALTER TABLE proyectos.proyectos
ADD COLUMN IF NOT EXISTS progreso_global INTEGER DEFAULT 0;

-- Comentarios
COMMENT ON COLUMN proyectos.proyectos.fase_actual IS 'Fase actual del workflow: identificacion | prefactibilidad | recopilacion | generacion | refinamiento';
COMMENT ON COLUMN proyectos.proyectos.progreso_global IS 'Progreso global del proyecto (0-100%)';

-- Crear índice para consultas por fase
CREATE INDEX IF NOT EXISTS idx_proyectos_fase_actual ON proyectos.proyectos(fase_actual);

-- ============================================================================
-- 3. FUNCIÓN: Actualizar timestamp updated_at automáticamente
-- ============================================================================

CREATE OR REPLACE FUNCTION proyectos.actualizar_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger para actualizar updated_at en componentes_eia_checklist
DROP TRIGGER IF EXISTS trigger_actualizar_updated_at ON proyectos.componentes_eia_checklist;
CREATE TRIGGER trigger_actualizar_updated_at
    BEFORE UPDATE ON proyectos.componentes_eia_checklist
    FOR EACH ROW
    EXECUTE FUNCTION proyectos.actualizar_updated_at();

-- ============================================================================
-- 4. VERIFICACIÓN
-- ============================================================================

-- Verificar que la tabla se creó correctamente
DO $$
BEGIN
    IF EXISTS (
        SELECT FROM information_schema.tables
        WHERE table_schema = 'proyectos'
        AND table_name = 'componentes_eia_checklist'
    ) THEN
        RAISE NOTICE 'Tabla proyectos.componentes_eia_checklist creada exitosamente';
    ELSE
        RAISE EXCEPTION 'Error: No se pudo crear la tabla componentes_eia_checklist';
    END IF;

    IF EXISTS (
        SELECT FROM information_schema.columns
        WHERE table_schema = 'proyectos'
        AND table_name = 'proyectos'
        AND column_name IN ('fase_actual', 'progreso_global')
    ) THEN
        RAISE NOTICE 'Campos fase_actual y progreso_global añadidos exitosamente';
    ELSE
        RAISE EXCEPTION 'Error: No se pudieron añadir los campos de workflow';
    END IF;
END $$;
