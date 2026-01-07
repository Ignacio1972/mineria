-- ===========================================================================
-- Migración: Sistema de Documentación Requerida según SEA
-- Versión: 1.0
-- Fecha: Enero 2026
-- Descripción: Nuevas categorías de documentos SEA, tabla de requerimientos
--              por tipo de proyecto, y validación de completitud
-- ===========================================================================

BEGIN;

-- ===========================================================================
-- 1. Crear nuevo ENUM con categorías específicas del SEA
-- ===========================================================================
DO $$
BEGIN
    -- Crear el nuevo tipo si no existe
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'categoria_documento_sea') THEN
        CREATE TYPE proyectos.categoria_documento_sea AS ENUM (
            -- Documentos geográficos/cartográficos
            'cartografia_planos',        -- Cartografía/Planos en WGS84

            -- Documentos de personal
            'titulo_profesional',        -- Títulos/cédulas de especialistas
            'certificado_consultora',    -- Permisos de operación de consultoras
            'certificado_laboratorio',   -- Laboratorios acreditados

            -- Estudios técnicos especializados
            'estudio_aire',              -- Modelamiento de aire
            'estudio_agua',              -- Modelamiento de agua
            'estudio_suelo',             -- Modelamiento de suelo
            'estudio_flora',             -- Estudio de flora
            'estudio_fauna',             -- Estudio de fauna
            'estudio_social',            -- Estudio social/línea base social
            'estudio_arqueologico',      -- Estudio arqueológico
            'estudio_ruido',             -- Estudio de ruido
            'estudio_vibraciones',       -- Estudio de vibraciones
            'estudio_paisaje',           -- Estudio de paisaje
            'estudio_hidrogeologico',    -- Estudio hidrogeológico

            -- Documentos legales y permisos
            'resolucion_sanitaria',      -- Certificados de servicios de salud
            'antecedente_pas',           -- Documentación técnica para PAS
            'certificado_pertenencia',   -- Propiedad o tenencia del terreno
            'contrato_servidumbre',      -- Contratos de servidumbre

            -- Participación ciudadana
            'acta_participacion',        -- Minutas de reuniones con comunidades
            'compromiso_voluntario',     -- Acuerdos firmados con comunidades
            'consulta_indigena',         -- Documentación consulta indígena

            -- Evaluaciones de riesgo
            'evaluacion_riesgo',         -- Evaluaciones de riesgo (químicos, salud)
            'plan_emergencia',           -- Planes de emergencia
            'plan_cierre',               -- Plan de cierre

            -- Otros documentos técnicos
            'memoria_tecnica',           -- Memoria técnica del proyecto
            'cronograma',                -- Cronograma de actividades
            'presupuesto_ambiental',     -- Presupuesto medidas ambientales
            'otro'                       -- Otros documentos
        );
    END IF;
END $$;

-- ===========================================================================
-- 2. Agregar columna de subcategoría a documentos existente
-- ===========================================================================
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'proyectos'
        AND table_name = 'documentos'
        AND column_name = 'categoria_sea'
    ) THEN
        ALTER TABLE proyectos.documentos
        ADD COLUMN categoria_sea proyectos.categoria_documento_sea DEFAULT 'otro';

        -- Migrar categorías existentes
        UPDATE proyectos.documentos SET categoria_sea = 'cartografia_planos' WHERE categoria = 'cartografia';
        UPDATE proyectos.documentos SET categoria_sea = 'memoria_tecnica' WHERE categoria = 'tecnico';
        UPDATE proyectos.documentos SET categoria_sea = 'estudio_flora' WHERE categoria = 'ambiental';

        -- Crear índice
        CREATE INDEX IF NOT EXISTS idx_documentos_categoria_sea
            ON proyectos.documentos(categoria_sea);
    END IF;
END $$;

-- ===========================================================================
-- 3. Agregar campos adicionales a documentos
-- ===========================================================================
DO $$
BEGIN
    -- Campo para validación de formato
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'proyectos'
        AND table_name = 'documentos'
        AND column_name = 'validacion_formato'
    ) THEN
        ALTER TABLE proyectos.documentos
        ADD COLUMN validacion_formato JSONB DEFAULT '{}'::jsonb;

        COMMENT ON COLUMN proyectos.documentos.validacion_formato IS
            'Resultado de validación: {valido: bool, errores: [], warnings: [], crs: string, etc}';
    END IF;

    -- Campo para contenido extraído (OCR/texto)
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'proyectos'
        AND table_name = 'documentos'
        AND column_name = 'contenido_extraido'
    ) THEN
        ALTER TABLE proyectos.documentos
        ADD COLUMN contenido_extraido TEXT;
    END IF;

    -- Campo para número de páginas
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'proyectos'
        AND table_name = 'documentos'
        AND column_name = 'num_paginas'
    ) THEN
        ALTER TABLE proyectos.documentos
        ADD COLUMN num_paginas INTEGER;
    END IF;

    -- Campo para profesional responsable
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'proyectos'
        AND table_name = 'documentos'
        AND column_name = 'profesional_responsable'
    ) THEN
        ALTER TABLE proyectos.documentos
        ADD COLUMN profesional_responsable VARCHAR(200);
    END IF;

    -- Campo para fecha del documento
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'proyectos'
        AND table_name = 'documentos'
        AND column_name = 'fecha_documento'
    ) THEN
        ALTER TABLE proyectos.documentos
        ADD COLUMN fecha_documento DATE;
    END IF;

    -- Campo para vigencia
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'proyectos'
        AND table_name = 'documentos'
        AND column_name = 'fecha_vigencia'
    ) THEN
        ALTER TABLE proyectos.documentos
        ADD COLUMN fecha_vigencia DATE;

        COMMENT ON COLUMN proyectos.documentos.fecha_vigencia IS
            'Fecha hasta la cual es válido el documento (ej: certificados)';
    END IF;
END $$;

-- ===========================================================================
-- 4. Tabla de requerimientos de documentos por tipo de proyecto
-- ===========================================================================
CREATE TABLE IF NOT EXISTS asistente_config.requerimientos_documentos (
    id SERIAL PRIMARY KEY,

    -- Vinculación a tipo/subtipo de proyecto
    tipo_proyecto_id INTEGER REFERENCES asistente_config.tipos_proyecto(id) ON DELETE CASCADE,
    subtipo_proyecto_id INTEGER REFERENCES asistente_config.subtipos_proyecto(id) ON DELETE SET NULL,

    -- Categoría del documento
    categoria_sea proyectos.categoria_documento_sea NOT NULL,

    -- Obligatoriedad
    es_obligatorio BOOLEAN DEFAULT false,
    obligatorio_para_dia BOOLEAN DEFAULT false,  -- Obligatorio solo para DIA
    obligatorio_para_eia BOOLEAN DEFAULT false,  -- Obligatorio solo para EIA

    -- Descripción y ayuda
    nombre_display VARCHAR(200) NOT NULL,
    descripcion TEXT,
    notas_sea TEXT,  -- Notas específicas del SEA

    -- Validaciones requeridas
    formatos_permitidos TEXT[] DEFAULT ARRAY['application/pdf'],
    tamano_max_mb INTEGER DEFAULT 50,
    requiere_firma_digital BOOLEAN DEFAULT false,
    requiere_profesional_responsable BOOLEAN DEFAULT false,

    -- Para cartografía
    requiere_crs_wgs84 BOOLEAN DEFAULT false,
    formatos_gis_permitidos TEXT[] DEFAULT ARRAY['shp', 'geojson', 'kml', 'gml'],

    -- Orden de presentación
    orden INTEGER DEFAULT 100,
    seccion_eia VARCHAR(50),  -- Capítulo del EIA donde va (ej: 'linea_base', 'descripcion_proyecto')

    -- Metadatos
    activo BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Un requerimiento por categoría por tipo/subtipo
    UNIQUE(tipo_proyecto_id, subtipo_proyecto_id, categoria_sea)
);

CREATE INDEX IF NOT EXISTS idx_req_docs_tipo ON asistente_config.requerimientos_documentos(tipo_proyecto_id);
CREATE INDEX IF NOT EXISTS idx_req_docs_subtipo ON asistente_config.requerimientos_documentos(subtipo_proyecto_id);
CREATE INDEX IF NOT EXISTS idx_req_docs_categoria ON asistente_config.requerimientos_documentos(categoria_sea);
CREATE INDEX IF NOT EXISTS idx_req_docs_activo ON asistente_config.requerimientos_documentos(activo) WHERE activo = true;

-- Trigger para updated_at
CREATE OR REPLACE FUNCTION asistente_config.fn_req_docs_updated()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_req_docs_updated ON asistente_config.requerimientos_documentos;
CREATE TRIGGER trg_req_docs_updated
    BEFORE UPDATE ON asistente_config.requerimientos_documentos
    FOR EACH ROW EXECUTE FUNCTION asistente_config.fn_req_docs_updated();

-- ===========================================================================
-- 5. Tabla de validación de documentos del proyecto
-- ===========================================================================
CREATE TABLE IF NOT EXISTS proyectos.documentos_validacion (
    id SERIAL PRIMARY KEY,
    proyecto_id INTEGER NOT NULL REFERENCES proyectos.proyectos(id) ON DELETE CASCADE,

    -- Referencia al requerimiento
    requerimiento_id INTEGER REFERENCES asistente_config.requerimientos_documentos(id) ON DELETE SET NULL,
    categoria_sea proyectos.categoria_documento_sea NOT NULL,

    -- Estado de cumplimiento
    estado VARCHAR(20) DEFAULT 'pendiente'
        CHECK (estado IN ('pendiente', 'subido', 'validando', 'aprobado', 'rechazado', 'no_aplica')),

    -- Documento asociado (si se ha subido)
    documento_id UUID REFERENCES proyectos.documentos(id) ON DELETE SET NULL,

    -- Validaciones
    validacion_formato BOOLEAN,
    validacion_contenido BOOLEAN,
    validacion_firma BOOLEAN,

    -- Observaciones
    observaciones TEXT,
    observaciones_sea TEXT,  -- Observaciones del SEA (si aplica)

    -- Metadatos
    validado_por VARCHAR(100),
    validado_fecha TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Un registro por categoría por proyecto
    UNIQUE(proyecto_id, categoria_sea)
);

CREATE INDEX IF NOT EXISTS idx_doc_val_proyecto ON proyectos.documentos_validacion(proyecto_id);
CREATE INDEX IF NOT EXISTS idx_doc_val_estado ON proyectos.documentos_validacion(estado);
CREATE INDEX IF NOT EXISTS idx_doc_val_categoria ON proyectos.documentos_validacion(categoria_sea);

-- ===========================================================================
-- 6. Insertar requerimientos base para proyectos mineros
-- ===========================================================================

-- Primero obtenemos el ID del tipo minería si existe
DO $$
DECLARE
    v_tipo_mineria_id INTEGER;
BEGIN
    SELECT id INTO v_tipo_mineria_id FROM asistente_config.tipos_proyecto WHERE codigo = 'mineria' LIMIT 1;

    IF v_tipo_mineria_id IS NOT NULL THEN
        -- Cartografía (obligatorio para ambos)
        INSERT INTO asistente_config.requerimientos_documentos
            (tipo_proyecto_id, categoria_sea, es_obligatorio, obligatorio_para_dia, obligatorio_para_eia,
             nombre_display, descripcion, notas_sea, requiere_crs_wgs84, orden, seccion_eia)
        VALUES
            (v_tipo_mineria_id, 'cartografia_planos', true, true, true,
             'Cartografía y Planos del Proyecto',
             'Planos georreferenciados del área del proyecto, accesos, instalaciones y área de influencia',
             'Formato digital en WGS84 (Datum oficial). Debe incluir área de influencia, ubicación proyecto, accesos, uso suelo existente',
             true, 10, 'descripcion_proyecto')
        ON CONFLICT (tipo_proyecto_id, subtipo_proyecto_id, categoria_sea) DO NOTHING;

        -- Títulos profesionales (obligatorio para EIA)
        INSERT INTO asistente_config.requerimientos_documentos
            (tipo_proyecto_id, categoria_sea, es_obligatorio, obligatorio_para_dia, obligatorio_para_eia,
             nombre_display, descripcion, notas_sea, requiere_profesional_responsable, orden, seccion_eia)
        VALUES
            (v_tipo_mineria_id, 'titulo_profesional', false, false, true,
             'Títulos Profesionales de Especialistas',
             'Cédulas o títulos de los profesionales que elaboraron el estudio',
             'Deben estar colegiados (si aplica)',
             true, 20, 'anexos')
        ON CONFLICT (tipo_proyecto_id, subtipo_proyecto_id, categoria_sea) DO NOTHING;

        -- Certificados de consultora
        INSERT INTO asistente_config.requerimientos_documentos
            (tipo_proyecto_id, categoria_sea, es_obligatorio, obligatorio_para_dia, obligatorio_para_eia,
             nombre_display, descripcion, notas_sea, orden, seccion_eia)
        VALUES
            (v_tipo_mineria_id, 'certificado_consultora', false, false, true,
             'Certificados de Consultoras',
             'Permisos de operación de consultoras ambientales',
             'Validez probada',
             25, 'anexos')
        ON CONFLICT (tipo_proyecto_id, subtipo_proyecto_id, categoria_sea) DO NOTHING;

        -- Certificados de laboratorio
        INSERT INTO asistente_config.requerimientos_documentos
            (tipo_proyecto_id, categoria_sea, es_obligatorio, obligatorio_para_dia, obligatorio_para_eia,
             nombre_display, descripcion, notas_sea, orden, seccion_eia)
        VALUES
            (v_tipo_mineria_id, 'certificado_laboratorio', false, false, true,
             'Certificados de Laboratorios Acreditados',
             'Acreditación de laboratorios que realizaron análisis',
             'Laboratorios acreditados por INN o equivalente',
             26, 'anexos')
        ON CONFLICT (tipo_proyecto_id, subtipo_proyecto_id, categoria_sea) DO NOTHING;

        -- Estudios especializados (obligatorios para EIA)
        INSERT INTO asistente_config.requerimientos_documentos
            (tipo_proyecto_id, categoria_sea, es_obligatorio, obligatorio_para_dia, obligatorio_para_eia,
             nombre_display, descripcion, notas_sea, orden, seccion_eia)
        VALUES
            (v_tipo_mineria_id, 'estudio_aire', false, false, true,
             'Estudio de Calidad del Aire',
             'Modelamiento de emisiones atmosféricas y calidad del aire',
             'Reportes técnicos con metodología clara, según guía SEA',
             30, 'linea_base'),
            (v_tipo_mineria_id, 'estudio_agua', false, false, true,
             'Estudio de Recursos Hídricos',
             'Modelamiento hidrológico e hidrogeológico',
             'Incluir balance hídrico y calidad de aguas',
             31, 'linea_base'),
            (v_tipo_mineria_id, 'estudio_suelo', false, false, true,
             'Estudio de Suelos',
             'Caracterización edafológica y geoquímica de suelos',
             'Incluir capacidad de uso y contaminación de fondo',
             32, 'linea_base'),
            (v_tipo_mineria_id, 'estudio_flora', false, false, true,
             'Estudio de Flora y Vegetación',
             'Catastro de flora y formaciones vegetacionales',
             'Incluir especies en categoría de conservación',
             33, 'linea_base'),
            (v_tipo_mineria_id, 'estudio_fauna', false, false, true,
             'Estudio de Fauna',
             'Catastro de fauna terrestre y acuática',
             'Incluir especies en categoría de conservación',
             34, 'linea_base'),
            (v_tipo_mineria_id, 'estudio_social', false, false, true,
             'Línea Base Social',
             'Caracterización socioeconómica y cultural del área',
             'Incluir demografía, actividades económicas, patrimonio cultural',
             35, 'linea_base'),
            (v_tipo_mineria_id, 'estudio_arqueologico', false, false, true,
             'Estudio Arqueológico',
             'Prospección y evaluación de sitios arqueológicos',
             'Según normativa CMN',
             36, 'linea_base'),
            (v_tipo_mineria_id, 'estudio_ruido', false, false, true,
             'Estudio de Ruido',
             'Modelamiento de ruido y vibraciones',
             'Según DS 38/2011 MMA',
             37, 'linea_base'),
            (v_tipo_mineria_id, 'estudio_hidrogeologico', false, false, true,
             'Estudio Hidrogeológico',
             'Caracterización de acuíferos y aguas subterráneas',
             'Incluir modelo conceptual y numérico si aplica',
             38, 'linea_base')
        ON CONFLICT (tipo_proyecto_id, subtipo_proyecto_id, categoria_sea) DO NOTHING;

        -- Resolución sanitaria
        INSERT INTO asistente_config.requerimientos_documentos
            (tipo_proyecto_id, categoria_sea, es_obligatorio, obligatorio_para_dia, obligatorio_para_eia,
             nombre_display, descripcion, notas_sea, orden, seccion_eia)
        VALUES
            (v_tipo_mineria_id, 'resolucion_sanitaria', false, false, false,
             'Resoluciones Sanitarias',
             'Certificados de servicios de salud (si proyecto requiere)',
             'Según tipología del proyecto',
             40, 'anexos')
        ON CONFLICT (tipo_proyecto_id, subtipo_proyecto_id, categoria_sea) DO NOTHING;

        -- Antecedentes PAS
        INSERT INTO asistente_config.requerimientos_documentos
            (tipo_proyecto_id, categoria_sea, es_obligatorio, obligatorio_para_dia, obligatorio_para_eia,
             nombre_display, descripcion, notas_sea, orden, seccion_eia)
        VALUES
            (v_tipo_mineria_id, 'antecedente_pas', true, true, true,
             'Antecedentes de PAS',
             'Documentación técnica por cada permiso ambiental sectorial requerido',
             'Cumplimiento de requisitos específicos de cada PAS según DS 40/2012',
             50, 'pas')
        ON CONFLICT (tipo_proyecto_id, subtipo_proyecto_id, categoria_sea) DO NOTHING;

        -- Actas de participación
        INSERT INTO asistente_config.requerimientos_documentos
            (tipo_proyecto_id, categoria_sea, es_obligatorio, obligatorio_para_dia, obligatorio_para_eia,
             nombre_display, descripcion, notas_sea, orden, seccion_eia)
        VALUES
            (v_tipo_mineria_id, 'acta_participacion', false, false, true,
             'Actas de Participación Ciudadana',
             'Minutas de reuniones con comunidades',
             'Evidencia de consulta previa y participación ciudadana anticipada',
             60, 'participacion')
        ON CONFLICT (tipo_proyecto_id, subtipo_proyecto_id, categoria_sea) DO NOTHING;

        -- Certificado de pertenencia
        INSERT INTO asistente_config.requerimientos_documentos
            (tipo_proyecto_id, categoria_sea, es_obligatorio, obligatorio_para_dia, obligatorio_para_eia,
             nombre_display, descripcion, notas_sea, orden, seccion_eia)
        VALUES
            (v_tipo_mineria_id, 'certificado_pertenencia', true, true, true,
             'Certificados de Pertenencia/Propiedad',
             'Documentos de propiedad o tenencia del terreno',
             'Vigencia legal actualizada. Incluir pertenencias mineras si aplica',
             70, 'descripcion_proyecto')
        ON CONFLICT (tipo_proyecto_id, subtipo_proyecto_id, categoria_sea) DO NOTHING;

        -- Evaluaciones de riesgo
        INSERT INTO asistente_config.requerimientos_documentos
            (tipo_proyecto_id, categoria_sea, es_obligatorio, obligatorio_para_dia, obligatorio_para_eia,
             nombre_display, descripcion, notas_sea, orden, seccion_eia)
        VALUES
            (v_tipo_mineria_id, 'evaluacion_riesgo', false, false, true,
             'Evaluaciones de Riesgo',
             'Evaluación de riesgos químicos, salud ocupacional y ambiental',
             'Por especialistas acreditados',
             80, 'prediccion_impactos')
        ON CONFLICT (tipo_proyecto_id, subtipo_proyecto_id, categoria_sea) DO NOTHING;

        -- Compromisos voluntarios
        INSERT INTO asistente_config.requerimientos_documentos
            (tipo_proyecto_id, categoria_sea, es_obligatorio, obligatorio_para_dia, obligatorio_para_eia,
             nombre_display, descripcion, notas_sea, orden, seccion_eia)
        VALUES
            (v_tipo_mineria_id, 'compromiso_voluntario', false, false, false,
             'Compromisos Voluntarios',
             'Documentos firmados con comunidades (si existen)',
             'Acuerdos de negociación previa, convenios con comunidades',
             90, 'participacion')
        ON CONFLICT (tipo_proyecto_id, subtipo_proyecto_id, categoria_sea) DO NOTHING;

        -- Plan de cierre
        INSERT INTO asistente_config.requerimientos_documentos
            (tipo_proyecto_id, categoria_sea, es_obligatorio, obligatorio_para_dia, obligatorio_para_eia,
             nombre_display, descripcion, notas_sea, orden, seccion_eia)
        VALUES
            (v_tipo_mineria_id, 'plan_cierre', true, true, true,
             'Plan de Cierre',
             'Plan de cierre de faenas según Ley 20.551',
             'Obligatorio para proyectos mineros',
             95, 'plan_cierre')
        ON CONFLICT (tipo_proyecto_id, subtipo_proyecto_id, categoria_sea) DO NOTHING;

        -- Memoria técnica
        INSERT INTO asistente_config.requerimientos_documentos
            (tipo_proyecto_id, categoria_sea, es_obligatorio, obligatorio_para_dia, obligatorio_para_eia,
             nombre_display, descripcion, notas_sea, orden, seccion_eia)
        VALUES
            (v_tipo_mineria_id, 'memoria_tecnica', true, true, true,
             'Memoria Técnica del Proyecto',
             'Descripción técnica detallada del proyecto',
             'Incluir procesos, equipos, insumos, productos',
             5, 'descripcion_proyecto')
        ON CONFLICT (tipo_proyecto_id, subtipo_proyecto_id, categoria_sea) DO NOTHING;

        -- Consulta indígena
        INSERT INTO asistente_config.requerimientos_documentos
            (tipo_proyecto_id, categoria_sea, es_obligatorio, obligatorio_para_dia, obligatorio_para_eia,
             nombre_display, descripcion, notas_sea, orden, seccion_eia)
        VALUES
            (v_tipo_mineria_id, 'consulta_indigena', false, false, false,
             'Documentación Consulta Indígena',
             'Proceso de consulta a pueblos indígenas según Convenio 169 OIT',
             'Requerido si hay afectación a grupos humanos indígenas (Art. 11 letra d)',
             65, 'participacion')
        ON CONFLICT (tipo_proyecto_id, subtipo_proyecto_id, categoria_sea) DO NOTHING;

        RAISE NOTICE '✅ Requerimientos de documentos insertados para minería (tipo_id=%)', v_tipo_mineria_id;
    ELSE
        RAISE NOTICE '⚠️ Tipo de proyecto minería no encontrado, insertando requerimientos genéricos';

        -- Insertar requerimientos genéricos (sin tipo específico)
        INSERT INTO asistente_config.requerimientos_documentos
            (tipo_proyecto_id, categoria_sea, es_obligatorio, obligatorio_para_dia, obligatorio_para_eia,
             nombre_display, descripcion, orden, seccion_eia)
        VALUES
            (NULL, 'cartografia_planos', true, true, true, 'Cartografía y Planos', 'Planos georreferenciados en WGS84', 10, 'descripcion_proyecto'),
            (NULL, 'titulo_profesional', false, false, true, 'Títulos Profesionales', 'Títulos de especialistas', 20, 'anexos'),
            (NULL, 'estudio_aire', false, false, true, 'Estudio de Aire', 'Modelamiento atmosférico', 30, 'linea_base'),
            (NULL, 'estudio_agua', false, false, true, 'Estudio de Agua', 'Modelamiento hídrico', 31, 'linea_base'),
            (NULL, 'estudio_suelo', false, false, true, 'Estudio de Suelos', 'Caracterización de suelos', 32, 'linea_base'),
            (NULL, 'estudio_flora', false, false, true, 'Estudio de Flora', 'Catastro de flora', 33, 'linea_base'),
            (NULL, 'estudio_fauna', false, false, true, 'Estudio de Fauna', 'Catastro de fauna', 34, 'linea_base'),
            (NULL, 'estudio_social', false, false, true, 'Línea Base Social', 'Caracterización social', 35, 'linea_base'),
            (NULL, 'antecedente_pas', true, true, true, 'Antecedentes PAS', 'Documentación para PAS', 50, 'pas'),
            (NULL, 'acta_participacion', false, false, true, 'Actas de Participación', 'Minutas de reuniones', 60, 'participacion'),
            (NULL, 'certificado_pertenencia', true, true, true, 'Certificados de Pertenencia', 'Propiedad del terreno', 70, 'descripcion_proyecto'),
            (NULL, 'evaluacion_riesgo', false, false, true, 'Evaluaciones de Riesgo', 'Riesgos del proyecto', 80, 'prediccion_impactos'),
            (NULL, 'compromiso_voluntario', false, false, false, 'Compromisos Voluntarios', 'Acuerdos con comunidades', 90, 'participacion'),
            (NULL, 'memoria_tecnica', true, true, true, 'Memoria Técnica', 'Descripción del proyecto', 5, 'descripcion_proyecto')
        ON CONFLICT (tipo_proyecto_id, subtipo_proyecto_id, categoria_sea) DO NOTHING;
    END IF;
END $$;

-- ===========================================================================
-- 7. Función para obtener documentos requeridos de un proyecto
-- ===========================================================================
CREATE OR REPLACE FUNCTION proyectos.fn_documentos_requeridos(
    p_proyecto_id INTEGER
)
RETURNS TABLE (
    requerimiento_id INTEGER,
    categoria_sea proyectos.categoria_documento_sea,
    nombre_display VARCHAR(200),
    descripcion TEXT,
    notas_sea TEXT,
    es_obligatorio BOOLEAN,
    obligatorio_segun_via BOOLEAN,
    seccion_eia VARCHAR(50),
    orden INTEGER,
    documento_id UUID,
    documento_nombre VARCHAR(255),
    estado_cumplimiento VARCHAR(20),
    formatos_permitidos TEXT[],
    requiere_crs_wgs84 BOOLEAN
) AS $$
DECLARE
    v_tipo_proyecto_id INTEGER;
    v_subtipo_proyecto_id INTEGER;
    v_via_evaluacion VARCHAR(10);
BEGIN
    -- Obtener tipo y subtipo del proyecto
    SELECT p.tipo_proyecto_id, p.subtipo_proyecto_id,
           COALESCE(d.via_sugerida, 'EIA')
    INTO v_tipo_proyecto_id, v_subtipo_proyecto_id, v_via_evaluacion
    FROM proyectos.proyectos p
    LEFT JOIN LATERAL (
        SELECT via_sugerida FROM proyectos.proyecto_diagnosticos
        WHERE proyecto_id = p.id ORDER BY version DESC LIMIT 1
    ) d ON true
    WHERE p.id = p_proyecto_id;

    RETURN QUERY
    SELECT
        r.id AS requerimiento_id,
        r.categoria_sea,
        r.nombre_display,
        r.descripcion,
        r.notas_sea,
        r.es_obligatorio,
        CASE
            WHEN r.es_obligatorio THEN true
            WHEN v_via_evaluacion = 'DIA' AND r.obligatorio_para_dia THEN true
            WHEN v_via_evaluacion = 'EIA' AND r.obligatorio_para_eia THEN true
            ELSE false
        END AS obligatorio_segun_via,
        r.seccion_eia,
        r.orden,
        doc.id AS documento_id,
        doc.nombre AS documento_nombre,
        COALESCE(val.estado, 'pendiente') AS estado_cumplimiento,
        r.formatos_permitidos,
        r.requiere_crs_wgs84
    FROM asistente_config.requerimientos_documentos r
    LEFT JOIN proyectos.documentos doc ON doc.proyecto_id = p_proyecto_id
        AND doc.categoria_sea = r.categoria_sea
    LEFT JOIN proyectos.documentos_validacion val ON val.proyecto_id = p_proyecto_id
        AND val.categoria_sea = r.categoria_sea
    WHERE r.activo = true
      AND (r.tipo_proyecto_id IS NULL OR r.tipo_proyecto_id = v_tipo_proyecto_id)
      AND (r.subtipo_proyecto_id IS NULL OR r.subtipo_proyecto_id = v_subtipo_proyecto_id)
    ORDER BY r.orden, r.nombre_display;
END;
$$ LANGUAGE plpgsql;

-- ===========================================================================
-- 8. Función para validar completitud de documentación
-- ===========================================================================
CREATE OR REPLACE FUNCTION proyectos.fn_validar_completitud_docs(
    p_proyecto_id INTEGER
)
RETURNS TABLE (
    es_completo BOOLEAN,
    total_requeridos INTEGER,
    total_obligatorios INTEGER,
    total_subidos INTEGER,
    obligatorios_faltantes TEXT[],
    opcionales_faltantes TEXT[],
    porcentaje_completitud NUMERIC
) AS $$
DECLARE
    v_tipo_proyecto_id INTEGER;
    v_via_evaluacion VARCHAR(10);
BEGIN
    -- Obtener vía de evaluación
    SELECT p.tipo_proyecto_id, COALESCE(d.via_sugerida, 'EIA')
    INTO v_tipo_proyecto_id, v_via_evaluacion
    FROM proyectos.proyectos p
    LEFT JOIN LATERAL (
        SELECT via_sugerida FROM proyectos.proyecto_diagnosticos
        WHERE proyecto_id = p.id ORDER BY version DESC LIMIT 1
    ) d ON true
    WHERE p.id = p_proyecto_id;

    RETURN QUERY
    WITH requerimientos AS (
        SELECT
            r.categoria_sea,
            r.nombre_display,
            CASE
                WHEN r.es_obligatorio THEN true
                WHEN v_via_evaluacion = 'DIA' AND r.obligatorio_para_dia THEN true
                WHEN v_via_evaluacion = 'EIA' AND r.obligatorio_para_eia THEN true
                ELSE false
            END AS es_obligatorio_final,
            EXISTS (
                SELECT 1 FROM proyectos.documentos doc
                WHERE doc.proyecto_id = p_proyecto_id
                AND doc.categoria_sea = r.categoria_sea
            ) AS tiene_documento
        FROM asistente_config.requerimientos_documentos r
        WHERE r.activo = true
          AND (r.tipo_proyecto_id IS NULL OR r.tipo_proyecto_id = v_tipo_proyecto_id)
    ),
    stats AS (
        SELECT
            COUNT(*) AS total,
            COUNT(*) FILTER (WHERE es_obligatorio_final) AS obligatorios,
            COUNT(*) FILTER (WHERE tiene_documento) AS subidos,
            ARRAY_AGG(nombre_display) FILTER (WHERE es_obligatorio_final AND NOT tiene_documento) AS oblig_faltantes,
            ARRAY_AGG(nombre_display) FILTER (WHERE NOT es_obligatorio_final AND NOT tiene_documento) AS opc_faltantes
        FROM requerimientos
    )
    SELECT
        (COALESCE(ARRAY_LENGTH(s.oblig_faltantes, 1), 0) = 0) AS es_completo,
        s.total::INTEGER AS total_requeridos,
        s.obligatorios::INTEGER AS total_obligatorios,
        s.subidos::INTEGER AS total_subidos,
        COALESCE(s.oblig_faltantes, ARRAY[]::TEXT[]) AS obligatorios_faltantes,
        COALESCE(s.opc_faltantes, ARRAY[]::TEXT[]) AS opcionales_faltantes,
        CASE WHEN s.total > 0 THEN ROUND((s.subidos::NUMERIC / s.total) * 100, 1) ELSE 0 END AS porcentaje_completitud
    FROM stats s;
END;
$$ LANGUAGE plpgsql;

-- ===========================================================================
-- 9. Vista de estado de documentación por proyecto
-- ===========================================================================
CREATE OR REPLACE VIEW proyectos.v_estado_documentacion AS
SELECT
    p.id AS proyecto_id,
    p.nombre AS proyecto_nombre,
    (SELECT es_completo FROM proyectos.fn_validar_completitud_docs(p.id)) AS documentacion_completa,
    (SELECT total_requeridos FROM proyectos.fn_validar_completitud_docs(p.id)) AS docs_requeridos,
    (SELECT total_subidos FROM proyectos.fn_validar_completitud_docs(p.id)) AS docs_subidos,
    (SELECT porcentaje_completitud FROM proyectos.fn_validar_completitud_docs(p.id)) AS porcentaje_completitud,
    (SELECT obligatorios_faltantes FROM proyectos.fn_validar_completitud_docs(p.id)) AS docs_faltantes
FROM proyectos.proyectos p
WHERE p.estado != 'archivado';

COMMIT;

-- ===========================================================================
-- Verificación
-- ===========================================================================
DO $$
DECLARE
    v_count_reqs INTEGER;
    v_count_cols INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_count_reqs FROM asistente_config.requerimientos_documentos;
    SELECT COUNT(*) INTO v_count_cols
    FROM information_schema.columns
    WHERE table_schema = 'proyectos' AND table_name = 'documentos' AND column_name = 'categoria_sea';

    IF v_count_cols > 0 AND v_count_reqs > 0 THEN
        RAISE NOTICE '✅ Migración completada: % requerimientos de documentos configurados', v_count_reqs;
    ELSE
        RAISE WARNING '⚠️ Migración incompleta: cols=%, reqs=%', v_count_cols, v_count_reqs;
    END IF;
END $$;
