-- ===========================================================================
-- Migracion: Estructura DIA Diferenciada
-- Version: 1.0
-- Fecha: Enero 2026
-- Descripcion: Soporte para generar DIAs ademas de EIAs
-- ===========================================================================

-- ===========================================================================
-- 1. Crear tipo enum instrumento_ambiental
-- ===========================================================================
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'instrumento_ambiental') THEN
        CREATE TYPE instrumento_ambiental AS ENUM ('EIA', 'DIA');
        RAISE NOTICE 'Tipo instrumento_ambiental creado';
    ELSE
        RAISE NOTICE 'Tipo instrumento_ambiental ya existe';
    END IF;
END $$;

-- ===========================================================================
-- 2. Agregar columna aplica_instrumento a capitulos_eia
-- ===========================================================================
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'asistente_config'
        AND table_name = 'capitulos_eia'
        AND column_name = 'aplica_instrumento'
    ) THEN
        ALTER TABLE asistente_config.capitulos_eia
        ADD COLUMN aplica_instrumento instrumento_ambiental[] DEFAULT ARRAY['EIA'::instrumento_ambiental];

        -- Actualizar capitulos existentes para que apliquen a EIA
        UPDATE asistente_config.capitulos_eia
        SET aplica_instrumento = ARRAY['EIA'::instrumento_ambiental]
        WHERE aplica_instrumento IS NULL;

        RAISE NOTICE 'Columna aplica_instrumento agregada a capitulos_eia';
    ELSE
        RAISE NOTICE 'Columna aplica_instrumento ya existe';
    END IF;
END $$;

COMMENT ON COLUMN asistente_config.capitulos_eia.aplica_instrumento
IS 'Instrumentos ambientales a los que aplica este capitulo (EIA, DIA o ambos)';

-- ===========================================================================
-- 3. Agregar columna instrumento a estructura_eia (instancia por proyecto)
-- ===========================================================================
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'proyectos'
        AND table_name = 'estructura_eia'
        AND column_name = 'instrumento'
    ) THEN
        ALTER TABLE proyectos.estructura_eia
        ADD COLUMN instrumento instrumento_ambiental DEFAULT 'EIA'::instrumento_ambiental;

        RAISE NOTICE 'Columna instrumento agregada a estructura_eia';
    ELSE
        RAISE NOTICE 'Columna instrumento ya existe en estructura_eia';
    END IF;
END $$;

COMMENT ON COLUMN proyectos.estructura_eia.instrumento
IS 'Tipo de instrumento ambiental: EIA o DIA';

-- ===========================================================================
-- 4. Crear tabla estructura_por_instrumento
-- ===========================================================================
CREATE TABLE IF NOT EXISTS asistente_config.estructura_por_instrumento (
    id SERIAL PRIMARY KEY,
    instrumento instrumento_ambiental NOT NULL,
    tipo_proyecto_id INTEGER REFERENCES asistente_config.tipos_proyecto(id) ON DELETE CASCADE,

    -- Configuracion de estructura
    capitulos_requeridos INTEGER[] NOT NULL,
    max_paginas_resumen INTEGER NOT NULL,
    requiere_linea_base BOOLEAN DEFAULT true,
    requiere_prediccion_impactos BOOLEAN DEFAULT true,
    requiere_plan_mitigacion BOOLEAN DEFAULT true,
    requiere_plan_contingencias BOOLEAN DEFAULT true,
    requiere_plan_seguimiento BOOLEAN DEFAULT true,

    -- Plazos legales (Art. 15 y 18 Ley 19.300)
    plazo_evaluacion_dias INTEGER NOT NULL,
    plazo_prorroga_dias INTEGER NOT NULL,
    max_icsara INTEGER DEFAULT 2,

    -- Metadatos
    activo BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(instrumento, tipo_proyecto_id)
);

CREATE INDEX IF NOT EXISTS idx_estructura_instrumento
ON asistente_config.estructura_por_instrumento(instrumento);

CREATE INDEX IF NOT EXISTS idx_estructura_tipo_proyecto
ON asistente_config.estructura_por_instrumento(tipo_proyecto_id);

COMMENT ON TABLE asistente_config.estructura_por_instrumento
IS 'Configuracion de estructura segun tipo de instrumento ambiental (EIA vs DIA)';

COMMENT ON COLUMN asistente_config.estructura_por_instrumento.capitulos_requeridos
IS 'Numeros de capitulos requeridos para este instrumento';

COMMENT ON COLUMN asistente_config.estructura_por_instrumento.max_paginas_resumen
IS 'Maximo de paginas del resumen ejecutivo (30 EIA, 20 DIA)';

COMMENT ON COLUMN asistente_config.estructura_por_instrumento.plazo_evaluacion_dias
IS 'Plazo legal de evaluacion en dias habiles (120 EIA, 60 DIA)';

-- ===========================================================================
-- 5. DATOS INICIALES: Configuracion EIA y DIA para Mineria
-- ===========================================================================
DO $$
DECLARE
    v_tipo_mineria_id INTEGER;
BEGIN
    SELECT id INTO v_tipo_mineria_id
    FROM asistente_config.tipos_proyecto
    WHERE codigo = 'mineria';

    IF v_tipo_mineria_id IS NULL THEN
        RAISE NOTICE 'Tipo mineria no encontrado, saltando datos de estructura_por_instrumento';
        RETURN;
    END IF;

    -- Configuracion EIA Mineria (11 capitulos, 120 dias)
    INSERT INTO asistente_config.estructura_por_instrumento (
        instrumento, tipo_proyecto_id, capitulos_requeridos,
        max_paginas_resumen, requiere_linea_base, requiere_prediccion_impactos,
        requiere_plan_mitigacion, requiere_plan_contingencias, requiere_plan_seguimiento,
        plazo_evaluacion_dias, plazo_prorroga_dias, max_icsara
    ) VALUES (
        'EIA', v_tipo_mineria_id, ARRAY[1,2,3,4,5,6,7,8,9,10,11],
        30, true, true, true, true, true,
        120, 60, 2
    ) ON CONFLICT (instrumento, tipo_proyecto_id) DO UPDATE SET
        capitulos_requeridos = EXCLUDED.capitulos_requeridos,
        max_paginas_resumen = EXCLUDED.max_paginas_resumen,
        plazo_evaluacion_dias = EXCLUDED.plazo_evaluacion_dias;

    -- Configuracion DIA Mineria (5 capitulos, 60 dias)
    -- Segun Art. 19 DS 40: Descripcion, Justificacion Art.11, Normativa, PAS, Compromisos
    INSERT INTO asistente_config.estructura_por_instrumento (
        instrumento, tipo_proyecto_id, capitulos_requeridos,
        max_paginas_resumen, requiere_linea_base, requiere_prediccion_impactos,
        requiere_plan_mitigacion, requiere_plan_contingencias, requiere_plan_seguimiento,
        plazo_evaluacion_dias, plazo_prorroga_dias, max_icsara
    ) VALUES (
        'DIA', v_tipo_mineria_id, ARRAY[1,2,8,9,11],
        20, false, false, false, false, false,
        60, 30, 2
    ) ON CONFLICT (instrumento, tipo_proyecto_id) DO UPDATE SET
        capitulos_requeridos = EXCLUDED.capitulos_requeridos,
        max_paginas_resumen = EXCLUDED.max_paginas_resumen,
        plazo_evaluacion_dias = EXCLUDED.plazo_evaluacion_dias;

    RAISE NOTICE 'Configuracion EIA/DIA para mineria insertada correctamente';
END $$;

-- ===========================================================================
-- 6. Actualizar capitulos existentes para indicar que aplican a EIA
-- ===========================================================================
UPDATE asistente_config.capitulos_eia
SET aplica_instrumento = ARRAY['EIA'::instrumento_ambiental]
WHERE aplica_instrumento IS NULL OR aplica_instrumento = '{}';

-- Capitulos que aplican tanto a EIA como DIA
-- Cap 1 (Descripcion), Cap 8 (Normativa), Cap 9 (PAS), Cap 11 (Compromisos)
UPDATE asistente_config.capitulos_eia
SET aplica_instrumento = ARRAY['EIA'::instrumento_ambiental, 'DIA'::instrumento_ambiental]
WHERE numero IN (1, 8, 9, 11);

DO $$ BEGIN RAISE NOTICE 'Capitulos actualizados con aplica_instrumento'; END $$;

-- ===========================================================================
-- 7. Insertar capitulo especifico DIA: Justificacion inexistencia Art. 11
-- ===========================================================================
DO $$
DECLARE
    v_tipo_mineria_id INTEGER;
    v_exists BOOLEAN;
BEGIN
    SELECT id INTO v_tipo_mineria_id
    FROM asistente_config.tipos_proyecto
    WHERE codigo = 'mineria';

    IF v_tipo_mineria_id IS NULL THEN
        RAISE NOTICE 'Tipo mineria no encontrado';
        RETURN;
    END IF;

    -- Verificar si ya existe capitulo 2 para DIA
    SELECT EXISTS (
        SELECT 1 FROM asistente_config.capitulos_eia
        WHERE tipo_proyecto_id = v_tipo_mineria_id
        AND numero = 2
        AND 'DIA' = ANY(aplica_instrumento)
    ) INTO v_exists;

    IF NOT v_exists THEN
        -- Actualizar capitulo 2 existente (Area de Influencia) para que sea solo EIA
        UPDATE asistente_config.capitulos_eia
        SET aplica_instrumento = ARRAY['EIA'::instrumento_ambiental]
        WHERE tipo_proyecto_id = v_tipo_mineria_id AND numero = 2;

        -- El capitulo 2 en DIA es "Justificacion de Inexistencia de Efectos Art. 11"
        -- Lo manejamos con contenido diferenciado en el servicio
        RAISE NOTICE 'Capitulo 2 configurado solo para EIA';
    END IF;
END $$;

-- ===========================================================================
-- 8. Crear vista para consultar estructura por instrumento
-- ===========================================================================
CREATE OR REPLACE VIEW asistente_config.v_capitulos_por_instrumento AS
SELECT
    c.id,
    c.tipo_proyecto_id,
    tp.codigo AS tipo_proyecto_codigo,
    tp.nombre AS tipo_proyecto_nombre,
    c.numero,
    c.titulo,
    c.descripcion,
    c.contenido_requerido,
    c.es_obligatorio,
    c.orden,
    c.aplica_instrumento,
    'EIA' = ANY(c.aplica_instrumento) AS aplica_eia,
    'DIA' = ANY(c.aplica_instrumento) AS aplica_dia
FROM asistente_config.capitulos_eia c
JOIN asistente_config.tipos_proyecto tp ON c.tipo_proyecto_id = tp.id
WHERE c.activo = true
ORDER BY c.tipo_proyecto_id, c.orden;

COMMENT ON VIEW asistente_config.v_capitulos_por_instrumento
IS 'Vista de capitulos con indicadores de aplicacion por instrumento';

-- ===========================================================================
-- 9. Crear funcion para obtener capitulos segun instrumento
-- ===========================================================================
CREATE OR REPLACE FUNCTION asistente_config.get_capitulos_instrumento(
    p_tipo_proyecto_id INTEGER,
    p_instrumento instrumento_ambiental
)
RETURNS TABLE (
    id INTEGER,
    numero INTEGER,
    titulo VARCHAR(200),
    descripcion TEXT,
    contenido_requerido JSONB,
    es_obligatorio BOOLEAN,
    orden INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.id,
        c.numero,
        c.titulo,
        c.descripcion,
        c.contenido_requerido,
        c.es_obligatorio,
        c.orden
    FROM asistente_config.capitulos_eia c
    WHERE c.tipo_proyecto_id = p_tipo_proyecto_id
    AND c.activo = true
    AND p_instrumento = ANY(c.aplica_instrumento)
    ORDER BY c.orden;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION asistente_config.get_capitulos_instrumento
IS 'Retorna capitulos aplicables a un instrumento especifico (EIA o DIA)';

-- ===========================================================================
-- Fin de la migracion
-- ===========================================================================
