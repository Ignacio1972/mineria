-- =============================================================================
-- MIGRACION 007: Mejoras Estructura EIA/DIA v2.0
-- =============================================================================
-- Fecha: Enero 2026
-- Descripcion: Implementa mejoras de alta prioridad para cobertura 100% SEIA
--
-- Incluye:
-- 1. Tipos enumerados nuevos
-- 2. Proceso de evaluacion (ICSARA/Adendas)
-- 3. Medidas de mitigacion e impactos
-- 4. Estructura DIA diferenciada
-- 5. Dimensiones detalladas de medio humano
-- =============================================================================

BEGIN;

-- =============================================================================
-- PARTE 1: TIPOS ENUMERADOS
-- =============================================================================

-- Instrumento ambiental (EIA vs DIA)
DO $$ BEGIN
    CREATE TYPE instrumento_ambiental AS ENUM ('EIA', 'DIA');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- Estados del proceso de evaluacion
DO $$ BEGIN
    CREATE TYPE estado_evaluacion_enum AS ENUM (
        'no_ingresado',        -- Proyecto en preparacion
        'ingresado',           -- Enviado a e-SEIA
        'en_admisibilidad',    -- 5 dias habiles
        'admitido',            -- Pasa a evaluacion
        'inadmitido',          -- Rechazado formalmente
        'en_evaluacion',       -- Analisis OAECA
        'icsara_emitido',      -- Esperando respuesta
        'adenda_en_revision',  -- Adenda presentada
        'ice_emitido',         -- Informe Consolidado de Evaluacion
        'en_comision',         -- Votacion regional
        'rca_aprobada',        -- Favorable
        'rca_rechazada',       -- Desfavorable
        'desistido',           -- Titular retira
        'caducado'             -- Sin actividad por plazo
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- Resultado de la RCA
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

-- Estados de ICSARA
DO $$ BEGIN
    CREATE TYPE estado_icsara_enum AS ENUM (
        'emitido',
        'respondido',
        'parcialmente_respondido',
        'vencido'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- Estados de Adenda
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

-- Resultado de revision de Adenda
DO $$ BEGIN
    CREATE TYPE resultado_revision_enum AS ENUM (
        'suficiente',
        'insuficiente',
        'parcialmente_suficiente'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- Tipos de medidas de mitigacion
DO $$ BEGIN
    CREATE TYPE tipo_medida_enum AS ENUM (
        'prevencion',
        'minimizacion',
        'restauracion',
        'reparacion',
        'compensacion'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- Fases del proyecto
DO $$ BEGIN
    CREATE TYPE fase_proyecto_enum AS ENUM (
        'construccion',
        'operacion',
        'cierre'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- Estados de medidas
DO $$ BEGIN
    CREATE TYPE estado_medida_enum AS ENUM (
        'propuesta',
        'en_revision',
        'aprobada',
        'rechazada',
        'en_ejecucion',
        'completada',
        'verificada'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- Tipos de impacto
DO $$ BEGIN
    CREATE TYPE tipo_impacto_enum AS ENUM (
        'directo',
        'indirecto',
        'acumulativo',
        'sinergico'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- Caracter del impacto
DO $$ BEGIN
    CREATE TYPE caracter_impacto_enum AS ENUM (
        'positivo',
        'negativo',
        'neutro'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- Probabilidad de impacto
DO $$ BEGIN
    CREATE TYPE probabilidad_enum AS ENUM (
        'cierta',
        'probable',
        'poco_probable',
        'improbable'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- Extension del impacto
DO $$ BEGIN
    CREATE TYPE extension_enum AS ENUM (
        'puntual',
        'local',
        'regional',
        'extensa'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- Duracion del impacto
DO $$ BEGIN
    CREATE TYPE duracion_enum AS ENUM (
        'temporal',
        'permanente',
        'periodica'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- Reversibilidad del impacto
DO $$ BEGIN
    CREATE TYPE reversibilidad_enum AS ENUM (
        'reversible',
        'parcialmente_reversible',
        'irreversible'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- Magnitud del impacto
DO $$ BEGIN
    CREATE TYPE magnitud_enum AS ENUM (
        'baja',
        'media',
        'alta',
        'muy_alta'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- Significancia del impacto
DO $$ BEGIN
    CREATE TYPE significancia_enum AS ENUM (
        'no_significativo',
        'poco_significativo',
        'significativo',
        'muy_significativo'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- Estado del impacto
DO $$ BEGIN
    CREATE TYPE estado_impacto_enum AS ENUM (
        'identificado',
        'evaluado',
        'mitigado',
        'residual'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;


-- =============================================================================
-- PARTE 2: TABLAS DE PROCESO DE EVALUACION
-- =============================================================================

-- Tabla principal de proceso de evaluacion
CREATE TABLE IF NOT EXISTS proyectos.proceso_evaluacion (
    id SERIAL PRIMARY KEY,
    proyecto_id INTEGER NOT NULL REFERENCES proyectos.proyectos(id) ON DELETE CASCADE,

    -- Estado administrativo
    estado_evaluacion estado_evaluacion_enum NOT NULL DEFAULT 'no_ingresado',
    fecha_ingreso DATE,
    fecha_admisibilidad DATE,
    fecha_rca DATE,
    resultado_rca resultado_rca_enum,

    -- Plazos
    plazo_legal_dias INTEGER DEFAULT 120,  -- EIA=120, DIA=60
    dias_transcurridos INTEGER DEFAULT 0,
    dias_suspension INTEGER DEFAULT 0,     -- Por Adendas

    -- Resolucion
    numero_rca VARCHAR(50),
    url_rca TEXT,
    condiciones_rca JSONB,  -- Array de condiciones

    -- Metadatos
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT uk_proceso_proyecto UNIQUE (proyecto_id)
);

-- Indices
CREATE INDEX IF NOT EXISTS idx_proceso_eval_estado
    ON proyectos.proceso_evaluacion(estado_evaluacion);
CREATE INDEX IF NOT EXISTS idx_proceso_eval_fechas
    ON proyectos.proceso_evaluacion(fecha_ingreso, fecha_rca);

-- Comentarios
COMMENT ON TABLE proyectos.proceso_evaluacion IS
    'Gestiona el ciclo de vida de evaluacion SEIA de un proyecto';
COMMENT ON COLUMN proyectos.proceso_evaluacion.condiciones_rca IS
    'Array de condiciones de la RCA favorable con condiciones';


-- Tabla de ICSARA
CREATE TABLE IF NOT EXISTS proyectos.icsara (
    id SERIAL PRIMARY KEY,
    proceso_evaluacion_id INTEGER NOT NULL
        REFERENCES proyectos.proceso_evaluacion(id) ON DELETE CASCADE,

    -- Identificacion
    numero_icsara INTEGER NOT NULL,  -- 1, 2, (3 excepcional)
    fecha_emision DATE NOT NULL,
    fecha_limite_respuesta DATE NOT NULL,

    -- Contenido
    observaciones JSONB NOT NULL DEFAULT '[]'::jsonb,
    total_observaciones INTEGER DEFAULT 0,
    observaciones_por_oaeca JSONB DEFAULT '{}'::jsonb,

    -- Estado
    estado estado_icsara_enum NOT NULL DEFAULT 'emitido',

    -- Archivo PDF original
    archivo_id INTEGER,

    -- Metadatos
    created_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT uk_icsara_proceso_numero UNIQUE (proceso_evaluacion_id, numero_icsara)
);

-- Indices
CREATE INDEX IF NOT EXISTS idx_icsara_proceso
    ON proyectos.icsara(proceso_evaluacion_id);
CREATE INDEX IF NOT EXISTS idx_icsara_estado
    ON proyectos.icsara(estado);

-- Comentarios
COMMENT ON TABLE proyectos.icsara IS
    'Informe Consolidado de Solicitud de Aclaraciones, Rectificaciones y Ampliaciones';
COMMENT ON COLUMN proyectos.icsara.observaciones IS
    'Array de observaciones: [{id, oaeca, capitulo_eia, tipo, texto, prioridad, estado}]';
COMMENT ON COLUMN proyectos.icsara.observaciones_por_oaeca IS
    'Conteo de observaciones por organismo: {"SAG": 5, "DGA": 3}';


-- Tabla de Adendas
CREATE TABLE IF NOT EXISTS proyectos.adenda (
    id SERIAL PRIMARY KEY,
    icsara_id INTEGER NOT NULL REFERENCES proyectos.icsara(id) ON DELETE CASCADE,

    -- Identificacion
    numero_adenda INTEGER NOT NULL,
    fecha_presentacion DATE NOT NULL,

    -- Contenido
    respuestas JSONB NOT NULL DEFAULT '[]'::jsonb,
    total_respuestas INTEGER DEFAULT 0,
    observaciones_resueltas INTEGER DEFAULT 0,
    observaciones_pendientes INTEGER DEFAULT 0,

    -- Evaluacion de la Adenda
    estado estado_adenda_enum NOT NULL DEFAULT 'presentada',
    fecha_revision DATE,
    resultado_revision resultado_revision_enum,

    -- Archivo PDF
    archivo_id INTEGER,

    -- Metadatos
    created_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT uk_adenda_icsara_numero UNIQUE (icsara_id, numero_adenda)
);

-- Indices
CREATE INDEX IF NOT EXISTS idx_adenda_icsara
    ON proyectos.adenda(icsara_id);
CREATE INDEX IF NOT EXISTS idx_adenda_estado
    ON proyectos.adenda(estado);

-- Comentarios
COMMENT ON TABLE proyectos.adenda IS
    'Documento de respuesta del titular a observaciones del ICSARA';
COMMENT ON COLUMN proyectos.adenda.respuestas IS
    'Array de respuestas: [{observacion_id, respuesta, anexos_referenciados, estado, calificacion_sea}]';


-- =============================================================================
-- PARTE 3: TABLAS DE IMPACTOS Y MEDIDAS DE MITIGACION
-- =============================================================================

-- Tabla de impactos ambientales
CREATE TABLE IF NOT EXISTS proyectos.impactos_ambientales (
    id SERIAL PRIMARY KEY,
    estructura_eia_id INTEGER NOT NULL
        REFERENCES proyectos.estructura_eia(id) ON DELETE CASCADE,

    -- Identificacion
    codigo VARCHAR(20) NOT NULL,  -- "IMP-001"
    nombre VARCHAR(200) NOT NULL,
    descripcion TEXT NOT NULL,

    -- Clasificacion
    tipo_impacto tipo_impacto_enum NOT NULL,
    componente_ambiental VARCHAR(50) NOT NULL,
    fase_generacion fase_proyecto_enum[] NOT NULL,

    -- Caracterizacion
    caracter caracter_impacto_enum NOT NULL,
    probabilidad probabilidad_enum NOT NULL,
    extension extension_enum NOT NULL,
    duracion duracion_enum NOT NULL,
    reversibilidad reversibilidad_enum NOT NULL,

    -- Evaluacion
    magnitud magnitud_enum NOT NULL,
    significancia significancia_enum NOT NULL,
    requiere_mitigacion BOOLEAN DEFAULT false,

    -- Vinculacion Art. 11
    literal_art11 CHAR(1),  -- a, b, c, d, e, f (si aplica)

    -- Estado
    estado estado_impacto_enum NOT NULL DEFAULT 'identificado',

    -- Metadatos
    created_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT uk_impacto_estructura_codigo UNIQUE (estructura_eia_id, codigo)
);

-- Indices
CREATE INDEX IF NOT EXISTS idx_impactos_estructura
    ON proyectos.impactos_ambientales(estructura_eia_id);
CREATE INDEX IF NOT EXISTS idx_impactos_componente
    ON proyectos.impactos_ambientales(componente_ambiental);
CREATE INDEX IF NOT EXISTS idx_impactos_significancia
    ON proyectos.impactos_ambientales(significancia);
CREATE INDEX IF NOT EXISTS idx_impactos_art11
    ON proyectos.impactos_ambientales(literal_art11) WHERE literal_art11 IS NOT NULL;

-- Comentarios
COMMENT ON TABLE proyectos.impactos_ambientales IS
    'Impactos ambientales identificados y evaluados para el proyecto';


-- Tabla de medidas de mitigacion
CREATE TABLE IF NOT EXISTS proyectos.medidas_mitigacion (
    id SERIAL PRIMARY KEY,
    estructura_eia_id INTEGER NOT NULL
        REFERENCES proyectos.estructura_eia(id) ON DELETE CASCADE,

    -- Identificacion
    codigo VARCHAR(20) NOT NULL,  -- "MIT-001", "REP-001", "COMP-001"
    nombre VARCHAR(200) NOT NULL,
    descripcion TEXT NOT NULL,

    -- Clasificacion
    tipo_medida tipo_medida_enum NOT NULL,
    jerarquia_mitigacion INTEGER NOT NULL CHECK (jerarquia_mitigacion BETWEEN 1 AND 4),
    -- 1=Prevencion, 2=Minimizacion, 3=Reparacion, 4=Compensacion

    -- Vinculacion a impactos (redundante pero util para consultas)
    impactos_asociados JSONB NOT NULL DEFAULT '[]'::jsonb,
    capitulo_eia INTEGER DEFAULT 5,

    -- Aplicacion
    fase_aplicacion fase_proyecto_enum[] NOT NULL,
    lugar_aplicacion TEXT,
    coordenadas_utm JSONB,  -- { "este": 123456, "norte": 654321, "huso": 19 }
    superficie_intervenida_ha DECIMAL(10,2),

    -- Indicadores (OBLIGATORIOS segun DS 40)
    indicador_cumplimiento TEXT NOT NULL,
    meta_o_estandar TEXT NOT NULL,
    forma_control TEXT NOT NULL,
    oportunidad_control TEXT NOT NULL,

    -- Responsabilidad
    responsable_ejecucion VARCHAR(100),
    responsable_verificacion VARCHAR(100),
    costo_estimado_usd DECIMAL(12,2),

    -- Estado
    estado estado_medida_enum NOT NULL DEFAULT 'propuesta',

    -- Metadatos
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT uk_medida_estructura_codigo UNIQUE (estructura_eia_id, codigo)
);

-- Indices
CREATE INDEX IF NOT EXISTS idx_medidas_estructura
    ON proyectos.medidas_mitigacion(estructura_eia_id);
CREATE INDEX IF NOT EXISTS idx_medidas_tipo
    ON proyectos.medidas_mitigacion(tipo_medida);
CREATE INDEX IF NOT EXISTS idx_medidas_jerarquia
    ON proyectos.medidas_mitigacion(jerarquia_mitigacion);
CREATE INDEX IF NOT EXISTS idx_medidas_fase
    ON proyectos.medidas_mitigacion USING GIN(fase_aplicacion);

-- Comentarios
COMMENT ON TABLE proyectos.medidas_mitigacion IS
    'Medidas de mitigacion, reparacion y compensacion del proyecto';
COMMENT ON COLUMN proyectos.medidas_mitigacion.jerarquia_mitigacion IS
    '1=Prevencion (evitar), 2=Minimizacion (reducir), 3=Reparacion, 4=Compensacion (ultima opcion)';


-- Tabla de vinculacion medida-impacto
CREATE TABLE IF NOT EXISTS proyectos.medida_impacto (
    id SERIAL PRIMARY KEY,
    medida_id INTEGER NOT NULL
        REFERENCES proyectos.medidas_mitigacion(id) ON DELETE CASCADE,
    impacto_id INTEGER NOT NULL
        REFERENCES proyectos.impactos_ambientales(id) ON DELETE CASCADE,

    -- Efectividad
    reduccion_esperada_porcentaje INTEGER CHECK (reduccion_esperada_porcentaje BETWEEN 0 AND 100),
    impacto_residual_esperado significancia_enum,

    CONSTRAINT uk_medida_impacto UNIQUE (medida_id, impacto_id)
);

-- Indices
CREATE INDEX IF NOT EXISTS idx_medida_impacto_medida
    ON proyectos.medida_impacto(medida_id);
CREATE INDEX IF NOT EXISTS idx_medida_impacto_impacto
    ON proyectos.medida_impacto(impacto_id);

-- Comentarios
COMMENT ON TABLE proyectos.medida_impacto IS
    'Vincula medidas de mitigacion con los impactos que atienden';


-- =============================================================================
-- PARTE 4: ESTRUCTURA DIA DIFERENCIADA
-- =============================================================================

-- Agregar columna para diferenciar EIA vs DIA en capitulos
ALTER TABLE asistente_config.capitulos_eia
    ADD COLUMN IF NOT EXISTS aplica_instrumento instrumento_ambiental[]
    DEFAULT ARRAY['EIA'::instrumento_ambiental];

-- Tabla de configuracion por instrumento
CREATE TABLE IF NOT EXISTS asistente_config.estructura_por_instrumento (
    id SERIAL PRIMARY KEY,
    instrumento instrumento_ambiental NOT NULL,
    tipo_proyecto_id INTEGER REFERENCES asistente_config.tipos_proyecto(id),

    -- Configuracion de estructura
    capitulos_requeridos INTEGER[] NOT NULL,
    max_paginas_resumen INTEGER NOT NULL,
    requiere_linea_base BOOLEAN DEFAULT true,
    requiere_prediccion_impactos BOOLEAN DEFAULT true,
    requiere_plan_mitigacion BOOLEAN DEFAULT true,

    -- Plazos legales
    plazo_evaluacion_dias INTEGER NOT NULL,
    plazo_prorroga_dias INTEGER NOT NULL,
    max_icsara INTEGER DEFAULT 2,

    -- Metadatos
    activo BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT uk_estructura_instrumento_tipo UNIQUE (instrumento, tipo_proyecto_id)
);

-- Comentarios
COMMENT ON TABLE asistente_config.estructura_por_instrumento IS
    'Configuracion de estructura segun instrumento (EIA vs DIA) y tipo de proyecto';

-- Datos iniciales: Configuracion EIA y DIA para mineria
INSERT INTO asistente_config.estructura_por_instrumento
    (instrumento, tipo_proyecto_id, capitulos_requeridos, max_paginas_resumen,
     requiere_linea_base, requiere_prediccion_impactos, requiere_plan_mitigacion,
     plazo_evaluacion_dias, plazo_prorroga_dias, max_icsara)
VALUES
    -- EIA Mineria (11 capitulos, 120+60 dias)
    ('EIA', 1, ARRAY[1,2,3,4,5,6,7,8,9,10,11], 30, true, true, true, 120, 60, 2),
    -- DIA Mineria (5 capitulos principales, 60+30 dias)
    ('DIA', 1, ARRAY[1,2,8,9,11], 20, false, false, false, 60, 30, 2)
ON CONFLICT (instrumento, tipo_proyecto_id) DO NOTHING;

-- Agregar capitulo especifico para DIA: Justificacion inexistencia Art. 11
INSERT INTO asistente_config.capitulos_eia
    (tipo_proyecto_id, numero, titulo, descripcion, contenido_requerido,
     es_obligatorio, orden, aplica_instrumento)
VALUES (
    1,  -- Mineria
    2,  -- Numero de capitulo
    'Justificacion de Inexistencia de Efectos Art. 11',
    'Demostracion punto por punto de que el proyecto NO genera efectos significativos segun Art. 11 Ley 19.300',
    '[
        "Analisis literal a) - Riesgo para salud de poblacion",
        "Analisis literal b) - Efectos sobre recursos naturales renovables",
        "Analisis literal c) - Reasentamiento o alteracion de sistemas de vida",
        "Analisis literal d) - Localizacion en areas protegidas o sitios prioritarios",
        "Analisis literal e) - Alteracion de valor paisajistico o turistico",
        "Analisis literal f) - Alteracion de patrimonio cultural",
        "Conclusion general de inexistencia de efectos significativos",
        "Declaracion jurada del titular"
    ]'::jsonb,
    true,
    2,
    ARRAY['DIA'::instrumento_ambiental]
)
ON CONFLICT DO NOTHING;


-- =============================================================================
-- PARTE 5: DIMENSIONES DETALLADAS DE MEDIO HUMANO
-- =============================================================================

-- Insertar/actualizar componentes de linea base para medio humano detallado
-- Usando ON CONFLICT para evitar duplicados

-- 1. Dimension Geografica
INSERT INTO asistente_config.componentes_linea_base
    (tipo_proyecto_id, capitulo_numero, codigo, nombre, descripcion,
     metodologia, variables_monitorear, estudios_requeridos,
     duracion_estimada_dias, es_obligatorio, orden)
VALUES (
    1, 3, 'medio_humano_geografico',
    'Medio Humano - Dimension Geografica',
    'Distribucion espacial de la poblacion en el area de influencia',
    'Analisis cartografico, censos INE, encuestas territoriales',
    '["Localidades y asentamientos", "Distancias a centros urbanos", "Vias de acceso", "Conectividad territorial", "Zonificacion territorial (IPT)"]'::jsonb,
    '["Mapa de localidades y asentamientos", "Analisis de accesibilidad", "Caracterizacion territorial"]'::jsonb,
    30, true, 301
)
ON CONFLICT (tipo_proyecto_id, codigo) DO UPDATE SET
    descripcion = EXCLUDED.descripcion,
    metodologia = EXCLUDED.metodologia,
    variables_monitorear = EXCLUDED.variables_monitorear;

-- 2. Dimension Demografica
INSERT INTO asistente_config.componentes_linea_base
    (tipo_proyecto_id, capitulo_numero, codigo, nombre, descripcion,
     metodologia, variables_monitorear, estudios_requeridos,
     duracion_estimada_dias, es_obligatorio, orden)
VALUES (
    1, 3, 'medio_humano_demografico',
    'Medio Humano - Dimension Demografica',
    'Estructura y dinamica poblacional del area de influencia',
    'Analisis de datos censales INE, encuestas sociodemograficas, proyecciones poblacionales',
    '["Poblacion total", "Densidad poblacional", "Estructura etaria (piramide)", "Distribucion por sexo", "Tasas de natalidad y mortalidad", "Migracion", "Proyeccion poblacional"]'::jsonb,
    '["Informe demografico", "Piramide poblacional", "Analisis de tendencias demograficas"]'::jsonb,
    30, true, 302
)
ON CONFLICT (tipo_proyecto_id, codigo) DO UPDATE SET
    descripcion = EXCLUDED.descripcion,
    metodologia = EXCLUDED.metodologia,
    variables_monitorear = EXCLUDED.variables_monitorear;

-- 3. Dimension Antropologica
INSERT INTO asistente_config.componentes_linea_base
    (tipo_proyecto_id, capitulo_numero, codigo, nombre, descripcion,
     metodologia, variables_monitorear, estudios_requeridos,
     duracion_estimada_dias, es_obligatorio, orden)
VALUES (
    1, 3, 'medio_humano_antropologico',
    'Medio Humano - Dimension Antropologica',
    'Cultura, identidad y sistemas de creencias de las comunidades del area de influencia',
    'Etnografia, entrevistas en profundidad, observacion participante, grupos focales',
    '["Identidad territorial", "Valores y creencias", "Tradiciones y costumbres", "Festividades locales", "Practicas religiosas y ceremoniales", "Historia local", "Percepcion del territorio"]'::jsonb,
    '["Estudio antropologico", "Mapeo cultural participativo", "Entrevistas cualitativas"]'::jsonb,
    60, true, 303
)
ON CONFLICT (tipo_proyecto_id, codigo) DO UPDATE SET
    descripcion = EXCLUDED.descripcion,
    metodologia = EXCLUDED.metodologia,
    variables_monitorear = EXCLUDED.variables_monitorear;

-- 4. Dimension Socioeconomica
INSERT INTO asistente_config.componentes_linea_base
    (tipo_proyecto_id, capitulo_numero, codigo, nombre, descripcion,
     metodologia, variables_monitorear, estudios_requeridos,
     duracion_estimada_dias, es_obligatorio, orden)
VALUES (
    1, 3, 'medio_humano_socioeconomico',
    'Medio Humano - Dimension Socioeconomica',
    'Actividades productivas, empleo e ingresos de la poblacion del area de influencia',
    'Encuestas socioeconomicas, analisis de datos CASEN, entrevistas a actores clave',
    '["Actividades economicas principales", "Tasas de empleo y desempleo", "Niveles de ingreso", "Pobreza multidimensional", "Estructura productiva local", "Cadenas de valor", "Economias de subsistencia"]'::jsonb,
    '["Estudio socioeconomico", "Caracterizacion productiva", "Analisis de empleo local"]'::jsonb,
    45, true, 304
)
ON CONFLICT (tipo_proyecto_id, codigo) DO UPDATE SET
    descripcion = EXCLUDED.descripcion,
    metodologia = EXCLUDED.metodologia,
    variables_monitorear = EXCLUDED.variables_monitorear;

-- 5. Dimension Bienestar Social
INSERT INTO asistente_config.componentes_linea_base
    (tipo_proyecto_id, capitulo_numero, codigo, nombre, descripcion,
     metodologia, variables_monitorear, estudios_requeridos,
     duracion_estimada_dias, es_obligatorio, orden)
VALUES (
    1, 3, 'medio_humano_bienestar',
    'Medio Humano - Dimension Bienestar Social',
    'Calidad de vida y acceso a servicios de la poblacion del area de influencia',
    'Analisis de coberturas sectoriales, encuestas de satisfaccion, datos MINSAL/MINEDUC',
    '["Cobertura de salud", "Establecimientos educacionales", "Calidad de vivienda", "Servicios basicos (agua potable, electricidad, alcantarillado)", "Transporte publico", "Espacios publicos", "Seguridad ciudadana", "Organizaciones comunitarias"]'::jsonb,
    '["Informe de bienestar social", "Analisis de coberturas", "Mapeo de servicios"]'::jsonb,
    45, true, 305
)
ON CONFLICT (tipo_proyecto_id, codigo) DO UPDATE SET
    descripcion = EXCLUDED.descripcion,
    metodologia = EXCLUDED.metodologia,
    variables_monitorear = EXCLUDED.variables_monitorear;

-- 6. Grupos Vulnerables (transversal)
INSERT INTO asistente_config.componentes_linea_base
    (tipo_proyecto_id, capitulo_numero, codigo, nombre, descripcion,
     metodologia, variables_monitorear, estudios_requeridos,
     duracion_estimada_dias, es_obligatorio, orden)
VALUES (
    1, 3, 'grupos_vulnerables',
    'Identificacion de Grupos Vulnerables',
    'Caracterizacion de grupos especialmente vulnerables a impactos del proyecto',
    'Mapeo de vulnerabilidad, analisis de riesgos sociales, entrevistas focalizadas',
    '["Adultos mayores", "Ninos y adolescentes", "Personas en situacion de discapacidad", "Mujeres jefas de hogar", "Comunidades aisladas", "Poblacion en pobreza extrema", "Migrantes"]'::jsonb,
    '["Mapa de vulnerabilidad", "Analisis de riesgos sociales", "Propuesta de medidas diferenciadas"]'::jsonb,
    30, true, 306
)
ON CONFLICT (tipo_proyecto_id, codigo) DO UPDATE SET
    descripcion = EXCLUDED.descripcion,
    metodologia = EXCLUDED.metodologia,
    variables_monitorear = EXCLUDED.variables_monitorear;

-- 7. Pueblos Indigenas (detallado, condicional)
INSERT INTO asistente_config.componentes_linea_base
    (tipo_proyecto_id, capitulo_numero, codigo, nombre, descripcion,
     metodologia, variables_monitorear, estudios_requeridos,
     duracion_estimada_dias, es_obligatorio, condicion_activacion, orden)
VALUES (
    1, 3, 'pueblos_indigenas_detalle',
    'Pueblos Indigenas - Caracterizacion Completa',
    'Caracterizacion de pueblos originarios segun Convenio 169 OIT y Ley 19.253',
    'Etnografia participativa, consulta previa, mapeo territorial indigena, entrevistas con autoridades tradicionales',
    '[
        "Pueblos presentes (mapuche, aymara, atacameno, diaguita, etc.)",
        "Comunidades y asociaciones indigenas",
        "Tierras indigenas (ADI, ADIS)",
        "Sitios de significacion cultural y espiritual",
        "Practicas ceremoniales y religiosas",
        "Sistemas de vida y costumbres",
        "Uso del territorio y recursos naturales",
        "Economias tradicionales",
        "Organizacion social y autoridades tradicionales",
        "Lengua y transmision cultural",
        "Relacion con el agua y la tierra",
        "Rutas de trashumancia (si aplica)"
    ]'::jsonb,
    '[
        "Certificado de pertinencia indigena (CONADI)",
        "Estudio antropologico de pueblos indigenas",
        "Mapeo territorial participativo",
        "Actas de reuniones con comunidades y autoridades",
        "Informe de susceptibilidad de afectacion directa para CPLI"
    ]'::jsonb,
    90, false,
    '{"presencia_indigena": true}'::jsonb,
    307
)
ON CONFLICT (tipo_proyecto_id, codigo) DO UPDATE SET
    descripcion = EXCLUDED.descripcion,
    metodologia = EXCLUDED.metodologia,
    variables_monitorear = EXCLUDED.variables_monitorear,
    estudios_requeridos = EXCLUDED.estudios_requeridos;


-- =============================================================================
-- PARTE 6: CAMPOS ADICIONALES EN DOCUMENTOS LEGALES
-- =============================================================================

-- Agregar campos para guias SEA en tabla de documentos
ALTER TABLE legal.documentos
    ADD COLUMN IF NOT EXISTS sector VARCHAR(50);

ALTER TABLE legal.documentos
    ADD COLUMN IF NOT EXISTS edicion VARCHAR(20);

ALTER TABLE legal.documentos
    ADD COLUMN IF NOT EXISTS url_fuente_oficial TEXT;

-- Crear vista para busqueda de guias SEA
CREATE OR REPLACE VIEW legal.v_guias_sea AS
SELECT
    d.id,
    d.titulo,
    d.numero AS codigo,
    d.tipo,
    d.categoria,
    d.sector,
    d.edicion,
    d.fecha_publicacion,
    d.url_fuente_oficial,
    d.triggers_art11,
    d.componentes_ambientales,
    d.estado
FROM legal.documentos d
WHERE d.tipo IN (
    'Guia Metodologica',
    'Guia Sectorial',
    'Instructivo',
    'Ordinario',
    'Criterio de Evaluacion',
    'Manual'
)
ORDER BY d.fecha_publicacion DESC;

COMMENT ON VIEW legal.v_guias_sea IS
    'Vista consolidada de guias, instructivos y criterios del SEA para busqueda RAG';


-- =============================================================================
-- PARTE 7: TRIGGERS Y FUNCIONES AUXILIARES
-- =============================================================================

-- Funcion para actualizar updated_at
CREATE OR REPLACE FUNCTION proyectos.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger para proceso_evaluacion
DROP TRIGGER IF EXISTS update_proceso_evaluacion_updated_at ON proyectos.proceso_evaluacion;
CREATE TRIGGER update_proceso_evaluacion_updated_at
    BEFORE UPDATE ON proyectos.proceso_evaluacion
    FOR EACH ROW EXECUTE FUNCTION proyectos.update_updated_at_column();

-- Trigger para medidas_mitigacion
DROP TRIGGER IF EXISTS update_medidas_mitigacion_updated_at ON proyectos.medidas_mitigacion;
CREATE TRIGGER update_medidas_mitigacion_updated_at
    BEFORE UPDATE ON proyectos.medidas_mitigacion
    FOR EACH ROW EXECUTE FUNCTION proyectos.update_updated_at_column();


-- =============================================================================
-- PARTE 8: PERMISOS
-- =============================================================================

-- Asignar permisos a las nuevas tablas (ajustar segun esquema de permisos)
GRANT SELECT, INSERT, UPDATE, DELETE ON proyectos.proceso_evaluacion TO mineria;
GRANT SELECT, INSERT, UPDATE, DELETE ON proyectos.icsara TO mineria;
GRANT SELECT, INSERT, UPDATE, DELETE ON proyectos.adenda TO mineria;
GRANT SELECT, INSERT, UPDATE, DELETE ON proyectos.impactos_ambientales TO mineria;
GRANT SELECT, INSERT, UPDATE, DELETE ON proyectos.medidas_mitigacion TO mineria;
GRANT SELECT, INSERT, UPDATE, DELETE ON proyectos.medida_impacto TO mineria;
GRANT SELECT, INSERT, UPDATE, DELETE ON asistente_config.estructura_por_instrumento TO mineria;

-- Secuencias
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA proyectos TO mineria;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA asistente_config TO mineria;


COMMIT;

-- =============================================================================
-- FIN DE MIGRACION 007
-- =============================================================================
