-- ===========================================================================
-- Migración: Tablas Extendidas del Esquema Proyectos
-- Versión: 1.0
-- Fecha: Enero 2026
-- Descripción: Tablas para ficha acumulativa, ubicaciones, PAS, diagnósticos
--              y conversaciones del asistente por proyecto
-- ===========================================================================

BEGIN;

-- ===========================================================================
-- 1. proyecto_ubicaciones
-- Almacena geometrías del proyecto con análisis GIS cacheado
-- ===========================================================================
CREATE TABLE IF NOT EXISTS proyectos.proyecto_ubicaciones (
    id SERIAL PRIMARY KEY,
    proyecto_id INTEGER NOT NULL REFERENCES proyectos.proyectos(id) ON DELETE CASCADE,

    -- Geometría (puede ser punto, polígono, multipolígono)
    geometria GEOMETRY(GEOMETRY, 4326) NOT NULL,

    -- División político-administrativa
    regiones TEXT[],
    provincias TEXT[],
    comunas TEXT[],

    -- Alcance territorial
    alcance VARCHAR(20) CHECK (alcance IN ('comunal', 'regional', 'bi_regional', 'nacional')),
    superficie_ha NUMERIC(12, 4),

    -- Cache del análisis GIS (evita recalcular)
    analisis_gis_cache JSONB DEFAULT '{}'::jsonb,
    analisis_gis_fecha TIMESTAMPTZ,

    -- Versionamiento (permite múltiples ubicaciones históricas)
    version INTEGER DEFAULT 1,
    es_vigente BOOLEAN DEFAULT true,

    -- Metadatos
    fuente VARCHAR(50) DEFAULT 'manual', -- 'manual', 'kml', 'geojson', 'shp'
    archivo_origen VARCHAR(255),

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ubicaciones_proyecto
    ON proyectos.proyecto_ubicaciones(proyecto_id);
CREATE INDEX IF NOT EXISTS idx_ubicaciones_geom
    ON proyectos.proyecto_ubicaciones USING GIST(geometria);
CREATE INDEX IF NOT EXISTS idx_ubicaciones_vigente
    ON proyectos.proyecto_ubicaciones(proyecto_id, es_vigente) WHERE es_vigente = true;

-- Trigger para updated_at
CREATE OR REPLACE FUNCTION proyectos.fn_ubicaciones_updated()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_ubicaciones_updated ON proyectos.proyecto_ubicaciones;
CREATE TRIGGER trg_ubicaciones_updated
    BEFORE UPDATE ON proyectos.proyecto_ubicaciones
    FOR EACH ROW EXECUTE FUNCTION proyectos.fn_ubicaciones_updated();

-- ===========================================================================
-- 2. proyecto_caracteristicas
-- Ficha acumulativa estructurada (clave-valor por categoría)
-- ===========================================================================
CREATE TABLE IF NOT EXISTS proyectos.proyecto_caracteristicas (
    id SERIAL PRIMARY KEY,
    proyecto_id INTEGER NOT NULL REFERENCES proyectos.proyectos(id) ON DELETE CASCADE,

    -- Clasificación
    categoria VARCHAR(50) NOT NULL, -- 'identificacion', 'tecnico', 'obras', 'fases', 'insumos', 'emisiones', 'social', 'ambiental'
    clave VARCHAR(100) NOT NULL,

    -- Valores (texto o numérico para comparaciones)
    valor TEXT,
    valor_numerico NUMERIC,
    unidad VARCHAR(50),

    -- Origen del dato
    fuente VARCHAR(20) DEFAULT 'manual', -- 'manual', 'asistente', 'documento', 'gis'
    documento_id UUID REFERENCES proyectos.documentos(id) ON DELETE SET NULL,
    pregunta_codigo VARCHAR(50), -- Referencia al árbol de preguntas

    -- Validación
    validado BOOLEAN DEFAULT false,
    validado_por VARCHAR(100),
    validado_fecha TIMESTAMPTZ,

    -- Metadatos
    notas TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Una sola entrada por proyecto/categoria/clave
    UNIQUE(proyecto_id, categoria, clave)
);

CREATE INDEX IF NOT EXISTS idx_caracteristicas_proyecto
    ON proyectos.proyecto_caracteristicas(proyecto_id);
CREATE INDEX IF NOT EXISTS idx_caracteristicas_categoria
    ON proyectos.proyecto_caracteristicas(proyecto_id, categoria);
CREATE INDEX IF NOT EXISTS idx_caracteristicas_clave
    ON proyectos.proyecto_caracteristicas(clave);

-- Trigger para updated_at
DROP TRIGGER IF EXISTS trg_caracteristicas_updated ON proyectos.proyecto_caracteristicas;
CREATE TRIGGER trg_caracteristicas_updated
    BEFORE UPDATE ON proyectos.proyecto_caracteristicas
    FOR EACH ROW EXECUTE FUNCTION proyectos.fn_ubicaciones_updated();

-- ===========================================================================
-- 3. proyecto_pas
-- Permisos Ambientales Sectoriales identificados para el proyecto
-- ===========================================================================
CREATE TABLE IF NOT EXISTS proyectos.proyecto_pas (
    id SERIAL PRIMARY KEY,
    proyecto_id INTEGER NOT NULL REFERENCES proyectos.proyectos(id) ON DELETE CASCADE,

    -- Identificación del PAS
    articulo INTEGER NOT NULL,
    nombre VARCHAR(200) NOT NULL,
    organismo VARCHAR(100) NOT NULL,

    -- Estado del trámite
    estado VARCHAR(30) DEFAULT 'identificado'
        CHECK (estado IN ('identificado', 'requerido', 'no_aplica', 'en_tramite', 'aprobado', 'rechazado')),
    obligatorio BOOLEAN DEFAULT false,

    -- Justificación
    justificacion TEXT,
    condicion_activada JSONB, -- Qué condición lo activó

    -- Documentación
    documento_id UUID REFERENCES proyectos.documentos(id) ON DELETE SET NULL,
    numero_resolucion VARCHAR(100),
    fecha_resolucion DATE,

    -- Metadatos
    identificado_por VARCHAR(20) DEFAULT 'sistema', -- 'sistema', 'usuario', 'asistente'
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Un PAS por artículo por proyecto
    UNIQUE(proyecto_id, articulo)
);

CREATE INDEX IF NOT EXISTS idx_pas_proyecto
    ON proyectos.proyecto_pas(proyecto_id);
CREATE INDEX IF NOT EXISTS idx_pas_articulo
    ON proyectos.proyecto_pas(articulo);
CREATE INDEX IF NOT EXISTS idx_pas_estado
    ON proyectos.proyecto_pas(estado);

-- Trigger para updated_at
DROP TRIGGER IF EXISTS trg_pas_updated ON proyectos.proyecto_pas;
CREATE TRIGGER trg_pas_updated
    BEFORE UPDATE ON proyectos.proyecto_pas
    FOR EACH ROW EXECUTE FUNCTION proyectos.fn_ubicaciones_updated();

-- ===========================================================================
-- 4. proyecto_analisis_art11
-- Análisis de literales del Artículo 11 (DIA vs EIA)
-- ===========================================================================
CREATE TABLE IF NOT EXISTS proyectos.proyecto_analisis_art11 (
    id SERIAL PRIMARY KEY,
    proyecto_id INTEGER NOT NULL REFERENCES proyectos.proyectos(id) ON DELETE CASCADE,

    -- Literal analizado
    literal CHAR(1) NOT NULL CHECK (literal IN ('a', 'b', 'c', 'd', 'e', 'f')),

    -- Estado del análisis
    estado VARCHAR(20) DEFAULT 'pendiente'
        CHECK (estado IN ('pendiente', 'no_aplica', 'probable', 'confirmado')),

    -- Justificación y evidencias
    justificacion TEXT,
    evidencias JSONB DEFAULT '[]'::jsonb,

    -- Origen del análisis
    fuente_gis BOOLEAN DEFAULT false,
    fuente_usuario BOOLEAN DEFAULT false,
    fuente_asistente BOOLEAN DEFAULT false,

    -- Metadatos
    confianza INTEGER CHECK (confianza BETWEEN 0 AND 100),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Un análisis por literal por proyecto
    UNIQUE(proyecto_id, literal)
);

CREATE INDEX IF NOT EXISTS idx_art11_proyecto
    ON proyectos.proyecto_analisis_art11(proyecto_id);
CREATE INDEX IF NOT EXISTS idx_art11_estado
    ON proyectos.proyecto_analisis_art11(estado);

-- Trigger para updated_at
DROP TRIGGER IF EXISTS trg_art11_updated ON proyectos.proyecto_analisis_art11;
CREATE TRIGGER trg_art11_updated
    BEFORE UPDATE ON proyectos.proyecto_analisis_art11
    FOR EACH ROW EXECUTE FUNCTION proyectos.fn_ubicaciones_updated();

-- ===========================================================================
-- 5. proyecto_diagnosticos
-- Resultados de diagnóstico de prefactibilidad
-- ===========================================================================
CREATE TABLE IF NOT EXISTS proyectos.proyecto_diagnosticos (
    id SERIAL PRIMARY KEY,
    proyecto_id INTEGER NOT NULL REFERENCES proyectos.proyectos(id) ON DELETE CASCADE,

    -- Versión del diagnóstico
    version INTEGER DEFAULT 1,

    -- Resultado principal
    via_sugerida VARCHAR(10) CHECK (via_sugerida IN ('DIA', 'EIA', 'NO_SEIA', 'INDEFINIDO')),
    confianza INTEGER CHECK (confianza BETWEEN 0 AND 100),

    -- Detalles del análisis
    literales_gatillados CHAR(1)[] DEFAULT '{}',

    -- Umbral SEIA
    cumple_umbral_seia BOOLEAN,
    umbral_evaluado JSONB, -- {parametro, valor_proyecto, valor_umbral, resultado}

    -- PAS y alertas
    permisos_identificados JSONB DEFAULT '[]'::jsonb,
    alertas JSONB DEFAULT '[]'::jsonb,
    recomendaciones JSONB DEFAULT '[]'::jsonb,

    -- Referencia a la ubicación usada
    ubicacion_version_id INTEGER REFERENCES proyectos.proyecto_ubicaciones(id) ON DELETE SET NULL,

    -- Resumen para el usuario
    resumen TEXT,

    -- Metadatos
    generado_por VARCHAR(20) DEFAULT 'sistema', -- 'sistema', 'asistente', 'usuario'
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_diagnosticos_proyecto
    ON proyectos.proyecto_diagnosticos(proyecto_id);
CREATE INDEX IF NOT EXISTS idx_diagnosticos_version
    ON proyectos.proyecto_diagnosticos(proyecto_id, version DESC);
CREATE INDEX IF NOT EXISTS idx_diagnosticos_via
    ON proyectos.proyecto_diagnosticos(via_sugerida);

-- ===========================================================================
-- 6. proyecto_conversaciones
-- Conversaciones del asistente específicas por proyecto (flujo EIA)
-- Nota: Diferente de asistente.conversaciones (chat general)
-- ===========================================================================
CREATE TABLE IF NOT EXISTS proyectos.proyecto_conversaciones (
    id SERIAL PRIMARY KEY,
    proyecto_id INTEGER NOT NULL REFERENCES proyectos.proyectos(id) ON DELETE CASCADE,

    -- Estado de la conversación
    estado VARCHAR(20) DEFAULT 'activa' CHECK (estado IN ('activa', 'pausada', 'completada', 'archivada')),
    fase VARCHAR(50) DEFAULT 'prefactibilidad', -- 'prefactibilidad', 'estructuracion', 'recopilacion', 'generacion'

    -- Progreso
    progreso_porcentaje INTEGER DEFAULT 0 CHECK (progreso_porcentaje BETWEEN 0 AND 100),
    ultima_pregunta_codigo VARCHAR(50),

    -- Resumen acumulativo (para contexto LLM)
    resumen_actual TEXT,
    tokens_acumulados INTEGER DEFAULT 0,

    -- Metadatos
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_proy_conv_proyecto
    ON proyectos.proyecto_conversaciones(proyecto_id);
CREATE INDEX IF NOT EXISTS idx_proy_conv_estado
    ON proyectos.proyecto_conversaciones(estado);
CREATE INDEX IF NOT EXISTS idx_proy_conv_fase
    ON proyectos.proyecto_conversaciones(fase);

-- Trigger para updated_at
DROP TRIGGER IF EXISTS trg_proy_conv_updated ON proyectos.proyecto_conversaciones;
CREATE TRIGGER trg_proy_conv_updated
    BEFORE UPDATE ON proyectos.proyecto_conversaciones
    FOR EACH ROW EXECUTE FUNCTION proyectos.fn_ubicaciones_updated();

-- ===========================================================================
-- 7. conversacion_mensajes
-- Mensajes individuales de las conversaciones de proyecto
-- ===========================================================================
CREATE TABLE IF NOT EXISTS proyectos.conversacion_mensajes (
    id SERIAL PRIMARY KEY,
    conversacion_id INTEGER NOT NULL REFERENCES proyectos.proyecto_conversaciones(id) ON DELETE CASCADE,

    -- Contenido del mensaje
    rol VARCHAR(20) NOT NULL CHECK (rol IN ('user', 'assistant', 'system')),
    contenido TEXT NOT NULL,

    -- Documento adjunto (si aplica)
    documento_adjunto_id UUID REFERENCES proyectos.documentos(id) ON DELETE SET NULL,

    -- Acciones ejecutadas por el asistente
    acciones_ejecutadas JSONB DEFAULT '[]'::jsonb,

    -- Tracking de uso
    tokens_usados INTEGER DEFAULT 0,
    modelo_usado VARCHAR(50),

    -- Metadatos
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_conv_msg_conversacion
    ON proyectos.conversacion_mensajes(conversacion_id);
CREATE INDEX IF NOT EXISTS idx_conv_msg_created
    ON proyectos.conversacion_mensajes(conversacion_id, created_at);
CREATE INDEX IF NOT EXISTS idx_conv_msg_rol
    ON proyectos.conversacion_mensajes(rol);

-- ===========================================================================
-- 8. Agregar campos faltantes a proyectos.proyectos
-- ===========================================================================

-- Agregar referencia al tipo de proyecto de la configuración
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'proyectos'
        AND table_name = 'proyectos'
        AND column_name = 'tipo_proyecto_id'
    ) THEN
        ALTER TABLE proyectos.proyectos
        ADD COLUMN tipo_proyecto_id INTEGER REFERENCES asistente_config.tipos_proyecto(id);
    END IF;
END $$;

-- Agregar referencia al subtipo
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'proyectos'
        AND table_name = 'proyectos'
        AND column_name = 'subtipo_proyecto_id'
    ) THEN
        ALTER TABLE proyectos.proyectos
        ADD COLUMN subtipo_proyecto_id INTEGER REFERENCES asistente_config.subtipos_proyecto(id);
    END IF;
END $$;

-- Índices para los nuevos campos
CREATE INDEX IF NOT EXISTS idx_proyectos_tipo_proyecto
    ON proyectos.proyectos(tipo_proyecto_id);
CREATE INDEX IF NOT EXISTS idx_proyectos_subtipo_proyecto
    ON proyectos.proyectos(subtipo_proyecto_id);

-- ===========================================================================
-- 9. Vista para ficha completa del proyecto
-- ===========================================================================
CREATE OR REPLACE VIEW proyectos.v_ficha_proyecto AS
SELECT
    p.id AS proyecto_id,
    p.nombre,
    p.estado,
    tp.codigo AS tipo_codigo,
    tp.nombre AS tipo_nombre,
    sp.codigo AS subtipo_codigo,
    sp.nombre AS subtipo_nombre,

    -- Ubicación vigente
    u.regiones,
    u.comunas,
    u.alcance,
    u.superficie_ha AS superficie_calculada,

    -- Características agrupadas por categoría
    (
        SELECT jsonb_object_agg(c.clave, c.valor)
        FROM proyectos.proyecto_caracteristicas c
        WHERE c.proyecto_id = p.id AND c.categoria = 'identificacion'
    ) AS identificacion,
    (
        SELECT jsonb_object_agg(c.clave, COALESCE(c.valor_numerico::text, c.valor))
        FROM proyectos.proyecto_caracteristicas c
        WHERE c.proyecto_id = p.id AND c.categoria = 'tecnico'
    ) AS tecnico,
    (
        SELECT jsonb_object_agg(c.clave, c.valor)
        FROM proyectos.proyecto_caracteristicas c
        WHERE c.proyecto_id = p.id AND c.categoria = 'obras'
    ) AS obras,

    -- Último diagnóstico
    d.via_sugerida,
    d.confianza AS diagnostico_confianza,
    d.literales_gatillados,

    -- Conteo de PAS
    (SELECT COUNT(*) FROM proyectos.proyecto_pas pas WHERE pas.proyecto_id = p.id) AS total_pas,
    (SELECT COUNT(*) FROM proyectos.proyecto_pas pas WHERE pas.proyecto_id = p.id AND pas.obligatorio) AS pas_obligatorios,

    p.created_at,
    p.updated_at

FROM proyectos.proyectos p
LEFT JOIN asistente_config.tipos_proyecto tp ON tp.id = p.tipo_proyecto_id
LEFT JOIN asistente_config.subtipos_proyecto sp ON sp.id = p.subtipo_proyecto_id
LEFT JOIN LATERAL (
    SELECT * FROM proyectos.proyecto_ubicaciones
    WHERE proyecto_id = p.id AND es_vigente = true
    ORDER BY version DESC LIMIT 1
) u ON true
LEFT JOIN LATERAL (
    SELECT * FROM proyectos.proyecto_diagnosticos
    WHERE proyecto_id = p.id
    ORDER BY version DESC LIMIT 1
) d ON true;

-- ===========================================================================
-- 10. Función helper para guardar característica
-- ===========================================================================
CREATE OR REPLACE FUNCTION proyectos.fn_guardar_caracteristica(
    p_proyecto_id INTEGER,
    p_categoria VARCHAR(50),
    p_clave VARCHAR(100),
    p_valor TEXT,
    p_valor_numerico NUMERIC DEFAULT NULL,
    p_unidad VARCHAR(50) DEFAULT NULL,
    p_fuente VARCHAR(20) DEFAULT 'manual'
)
RETURNS proyectos.proyecto_caracteristicas AS $$
DECLARE
    v_result proyectos.proyecto_caracteristicas;
BEGIN
    INSERT INTO proyectos.proyecto_caracteristicas (
        proyecto_id, categoria, clave, valor, valor_numerico, unidad, fuente
    ) VALUES (
        p_proyecto_id, p_categoria, p_clave, p_valor, p_valor_numerico, p_unidad, p_fuente
    )
    ON CONFLICT (proyecto_id, categoria, clave)
    DO UPDATE SET
        valor = EXCLUDED.valor,
        valor_numerico = EXCLUDED.valor_numerico,
        unidad = EXCLUDED.unidad,
        fuente = EXCLUDED.fuente,
        updated_at = NOW()
    RETURNING * INTO v_result;

    RETURN v_result;
END;
$$ LANGUAGE plpgsql;

-- ===========================================================================
-- 11. Función helper para evaluar umbral
-- ===========================================================================
CREATE OR REPLACE FUNCTION proyectos.fn_evaluar_umbral_seia(
    p_tipo_id INTEGER,
    p_subtipo_id INTEGER,
    p_parametro VARCHAR(100),
    p_valor NUMERIC
)
RETURNS TABLE (
    cumple BOOLEAN,
    umbral_id INTEGER,
    operador VARCHAR(10),
    valor_umbral NUMERIC,
    resultado VARCHAR(50),
    norma_referencia VARCHAR(100)
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        CASE
            WHEN u.operador = '>=' THEN p_valor >= u.valor
            WHEN u.operador = '>' THEN p_valor > u.valor
            WHEN u.operador = '<=' THEN p_valor <= u.valor
            WHEN u.operador = '<' THEN p_valor < u.valor
            WHEN u.operador = '=' THEN p_valor = u.valor
            ELSE false
        END AS cumple,
        u.id AS umbral_id,
        u.operador,
        u.valor AS valor_umbral,
        u.resultado,
        u.norma_referencia
    FROM asistente_config.umbrales_seia u
    WHERE u.tipo_proyecto_id = p_tipo_id
      AND (u.subtipo_id IS NULL OR u.subtipo_id = p_subtipo_id)
      AND u.parametro = p_parametro
      AND u.activo = true
    ORDER BY u.subtipo_id NULLS LAST
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

COMMIT;

-- ===========================================================================
-- Verificación
-- ===========================================================================
DO $$
DECLARE
    v_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_count
    FROM information_schema.tables
    WHERE table_schema = 'proyectos'
    AND table_name IN (
        'proyecto_ubicaciones',
        'proyecto_caracteristicas',
        'proyecto_pas',
        'proyecto_analisis_art11',
        'proyecto_diagnosticos',
        'proyecto_conversaciones',
        'conversacion_mensajes'
    );

    IF v_count = 7 THEN
        RAISE NOTICE '✅ Migración completada: 7 tablas creadas en proyectos.*';
    ELSE
        RAISE WARNING '⚠️ Migración incompleta: solo % tablas encontradas', v_count;
    END IF;
END $$;
