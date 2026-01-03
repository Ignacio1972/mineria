-- Migración simplificada para tablas ICSARA
-- Solo crea las tablas necesarias para el Gestor ICSARA/Adendas

-- Parte 1: Tipos enumerados para proceso de evaluación
DO $$ BEGIN
    CREATE TYPE estado_evaluacion_enum AS ENUM (
        'no_ingresado',
        'ingresado',
        'en_admisibilidad',
        'admitido',
        'inadmitido',
        'en_evaluacion',
        'icsara_emitido',
        'adenda_en_revision',
        'ice_emitido',
        'en_comision',
        'rca_aprobada',
        'rca_rechazada',
        'desistido',
        'caducado'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE resultado_rca_enum AS ENUM (
        'favorable',
        'favorable_con_condiciones',
        'desfavorable',
        'desistimiento',
        'caducidad'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE estado_icsara_enum AS ENUM (
        'emitido',
        'respondido',
        'parcialmente_respondido',
        'vencido'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE estado_adenda_enum AS ENUM (
        'en_elaboracion',
        'presentada',
        'en_revision',
        'aceptada',
        'con_observaciones',
        'rechazada'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE resultado_revision_enum AS ENUM (
        'suficiente',
        'insuficiente',
        'parcialmente_suficiente'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- Parte 2: Tabla proceso_evaluacion
CREATE TABLE IF NOT EXISTS proyectos.proceso_evaluacion (
    id SERIAL PRIMARY KEY,
    proyecto_id INTEGER NOT NULL REFERENCES proyectos.proyectos(id) ON DELETE CASCADE,
    estado_evaluacion estado_evaluacion_enum NOT NULL DEFAULT 'no_ingresado',
    fecha_ingreso DATE,
    fecha_admisibilidad DATE,
    fecha_rca DATE,
    resultado_rca resultado_rca_enum,
    plazo_legal_dias INTEGER DEFAULT 120,
    dias_transcurridos INTEGER DEFAULT 0,
    dias_suspension INTEGER DEFAULT 0,
    numero_rca VARCHAR(50),
    url_rca TEXT,
    condiciones_rca JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uk_proceso_proyecto UNIQUE (proyecto_id)
);

CREATE INDEX IF NOT EXISTS idx_proceso_eval_estado ON proyectos.proceso_evaluacion(estado_evaluacion);
CREATE INDEX IF NOT EXISTS idx_proceso_eval_fechas ON proyectos.proceso_evaluacion(fecha_ingreso, fecha_rca);

COMMENT ON TABLE proyectos.proceso_evaluacion IS 'Gestiona el ciclo de vida de evaluación SEIA de un proyecto';

-- Parte 3: Tabla ICSARA
CREATE TABLE IF NOT EXISTS proyectos.icsara (
    id SERIAL PRIMARY KEY,
    proceso_evaluacion_id INTEGER NOT NULL REFERENCES proyectos.proceso_evaluacion(id) ON DELETE CASCADE,
    numero_icsara INTEGER NOT NULL,
    fecha_emision DATE NOT NULL,
    fecha_limite_respuesta DATE NOT NULL,
    observaciones JSONB NOT NULL DEFAULT '[]'::jsonb,
    total_observaciones INTEGER DEFAULT 0,
    observaciones_por_oaeca JSONB DEFAULT '{}'::jsonb,
    estado estado_icsara_enum NOT NULL DEFAULT 'emitido',
    archivo_id INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uk_icsara_proceso_numero UNIQUE (proceso_evaluacion_id, numero_icsara)
);

CREATE INDEX IF NOT EXISTS idx_icsara_proceso ON proyectos.icsara(proceso_evaluacion_id);
CREATE INDEX IF NOT EXISTS idx_icsara_estado ON proyectos.icsara(estado);

COMMENT ON TABLE proyectos.icsara IS 'Informe Consolidado de Solicitud de Aclaraciones, Rectificaciones y Ampliaciones';
COMMENT ON COLUMN proyectos.icsara.observaciones IS 'Array de observaciones: [{id, oaeca, capitulo_eia, tipo, texto, prioridad, estado}]';

-- Parte 4: Tabla Adenda
CREATE TABLE IF NOT EXISTS proyectos.adenda (
    id SERIAL PRIMARY KEY,
    icsara_id INTEGER NOT NULL REFERENCES proyectos.icsara(id) ON DELETE CASCADE,
    numero_adenda INTEGER NOT NULL,
    fecha_presentacion DATE NOT NULL,
    respuestas JSONB NOT NULL DEFAULT '[]'::jsonb,
    total_respuestas INTEGER DEFAULT 0,
    observaciones_resueltas INTEGER DEFAULT 0,
    observaciones_pendientes INTEGER DEFAULT 0,
    estado estado_adenda_enum NOT NULL DEFAULT 'presentada',
    fecha_revision DATE,
    resultado_revision resultado_revision_enum,
    archivo_id INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uk_adenda_icsara_numero UNIQUE (icsara_id, numero_adenda)
);

CREATE INDEX IF NOT EXISTS idx_adenda_icsara ON proyectos.adenda(icsara_id);
CREATE INDEX IF NOT EXISTS idx_adenda_estado ON proyectos.adenda(estado);

COMMENT ON TABLE proyectos.adenda IS 'Documento de respuesta del titular a observaciones del ICSARA';
COMMENT ON COLUMN proyectos.adenda.respuestas IS 'Array de respuestas: [{observacion_id, respuesta, anexos_referenciados, estado, calificacion_sea}]';

-- Parte 5: Trigger para actualizar updated_at
CREATE OR REPLACE FUNCTION proyectos.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_proceso_evaluacion_updated_at ON proyectos.proceso_evaluacion;
CREATE TRIGGER update_proceso_evaluacion_updated_at
    BEFORE UPDATE ON proyectos.proceso_evaluacion
    FOR EACH ROW EXECUTE FUNCTION proyectos.update_updated_at_column();

-- Parte 6: Permisos
GRANT SELECT, INSERT, UPDATE, DELETE ON proyectos.proceso_evaluacion TO mineria;
GRANT SELECT, INSERT, UPDATE, DELETE ON proyectos.icsara TO mineria;
GRANT SELECT, INSERT, UPDATE, DELETE ON proyectos.adenda TO mineria;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA proyectos TO mineria;
