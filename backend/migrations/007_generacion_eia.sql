-- ========================================
-- MIGRACIÓN 007: FASE 4 - GENERACIÓN DE EIA
-- ========================================
-- Sistema de compilación, generación, validación y exportación de documentos EIA

BEGIN;

-- ========================================
-- TABLA: documentos_eia
-- Almacena documentos EIA generados con versionado
-- ========================================
CREATE TABLE IF NOT EXISTS proyectos.documentos_eia (
    id SERIAL PRIMARY KEY,
    proyecto_id INTEGER NOT NULL REFERENCES proyectos.proyectos(id) ON DELETE CASCADE,
    version INTEGER DEFAULT 1,
    estado VARCHAR(30) DEFAULT 'borrador',  -- borrador, en_revision, validado, final
    titulo VARCHAR(500),
    contenido_capitulos JSONB,              -- Texto generado por capítulo
    metadatos JSONB,                        -- {fecha, autores, revisores, etc}
    validaciones JSONB,                     -- Resultados de validación SEA
    estadisticas JSONB,                     -- {paginas, palabras, figuras, tablas}
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT chk_estado_documento CHECK (estado IN ('borrador', 'en_revision', 'validado', 'final'))
);

CREATE INDEX IF NOT EXISTS idx_documentos_proyecto ON proyectos.documentos_eia(proyecto_id);
CREATE INDEX IF NOT EXISTS idx_documentos_estado ON proyectos.documentos_eia(estado);

COMMENT ON TABLE proyectos.documentos_eia IS 'Documentos EIA generados por proyecto con versionado';
COMMENT ON COLUMN proyectos.documentos_eia.contenido_capitulos IS 'Estructura: {"1": {"titulo": "...", "contenido": "...", "subsecciones": {...}}, ...}';
COMMENT ON COLUMN proyectos.documentos_eia.metadatos IS 'Metadata del documento: fecha generación, autores, empresa consultora, etc';
COMMENT ON COLUMN proyectos.documentos_eia.estadisticas IS 'Estadísticas: número páginas, palabras, figuras, tablas, anexos';

-- ========================================
-- TABLA: versiones_eia
-- Historial de versiones de documentos EIA
-- ========================================
CREATE TABLE IF NOT EXISTS proyectos.versiones_eia (
    id SERIAL PRIMARY KEY,
    documento_id INTEGER NOT NULL REFERENCES proyectos.documentos_eia(id) ON DELETE CASCADE,
    version INTEGER NOT NULL,
    cambios TEXT NOT NULL,                  -- Descripción de cambios realizados
    contenido_snapshot JSONB,               -- Snapshot completo de contenido_capitulos
    creado_por VARCHAR(100),                -- Usuario que creó la versión
    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(documento_id, version)
);

CREATE INDEX IF NOT EXISTS idx_versiones_documento ON proyectos.versiones_eia(documento_id);

COMMENT ON TABLE proyectos.versiones_eia IS 'Historial de versiones de documentos EIA con snapshots';
COMMENT ON COLUMN proyectos.versiones_eia.contenido_snapshot IS 'Copia completa del contenido en esa versión para comparación';

-- ========================================
-- TABLA: exportaciones_eia
-- Registro de exportaciones generadas
-- ========================================
CREATE TABLE IF NOT EXISTS proyectos.exportaciones_eia (
    id SERIAL PRIMARY KEY,
    documento_id INTEGER NOT NULL REFERENCES proyectos.documentos_eia(id) ON DELETE CASCADE,
    formato VARCHAR(20) NOT NULL,           -- pdf, docx, eseia_xml
    archivo_path VARCHAR(500),              -- Ruta del archivo generado
    tamano_bytes BIGINT,
    generado_exitoso BOOLEAN DEFAULT FALSE,
    error_mensaje TEXT,
    configuracion JSONB,                    -- Configuración de exportación (estilos, etc)
    created_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT chk_formato_export CHECK (formato IN ('pdf', 'docx', 'eseia_xml'))
);

CREATE INDEX IF NOT EXISTS idx_exportaciones_documento ON proyectos.exportaciones_eia(documento_id);
CREATE INDEX IF NOT EXISTS idx_exportaciones_formato ON proyectos.exportaciones_eia(formato);

COMMENT ON TABLE proyectos.exportaciones_eia IS 'Registro de exportaciones de documentos EIA en diferentes formatos';
COMMENT ON COLUMN proyectos.exportaciones_eia.configuracion IS 'Config de exportación: estilos, márgenes, fuentes, logos, etc';

-- ========================================
-- TABLA: reglas_validacion_sea
-- Reglas de validación de documentos según requisitos SEA
-- ========================================
CREATE TABLE IF NOT EXISTS asistente_config.reglas_validacion_sea (
    id SERIAL PRIMARY KEY,
    tipo_proyecto_id INTEGER REFERENCES asistente_config.tipos_proyecto(id) ON DELETE SET NULL,
    capitulo_numero INTEGER,                -- NULL = aplica a todo el documento
    codigo_regla VARCHAR(50) UNIQUE NOT NULL,
    descripcion TEXT NOT NULL,
    tipo_validacion VARCHAR(30) NOT NULL,   -- contenido, formato, referencia, completitud
    criterio JSONB NOT NULL,                -- Regla de validación en formato estructurado
    mensaje_error TEXT NOT NULL,
    mensaje_sugerencia TEXT,                -- Sugerencia para corregir
    severidad VARCHAR(20) DEFAULT 'warning',
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT chk_tipo_validacion CHECK (tipo_validacion IN ('contenido', 'formato', 'referencia', 'completitud', 'normativa')),
    CONSTRAINT chk_severidad CHECK (severidad IN ('error', 'warning', 'info'))
);

CREATE INDEX IF NOT EXISTS idx_reglas_tipo ON asistente_config.reglas_validacion_sea(tipo_proyecto_id);
CREATE INDEX IF NOT EXISTS idx_reglas_capitulo ON asistente_config.reglas_validacion_sea(capitulo_numero);
CREATE INDEX IF NOT EXISTS idx_reglas_activo ON asistente_config.reglas_validacion_sea(activo);

COMMENT ON TABLE asistente_config.reglas_validacion_sea IS 'Reglas de validación de documentos EIA según requisitos SEA/ICSARA';
COMMENT ON COLUMN asistente_config.reglas_validacion_sea.criterio IS 'Estructura: {"tipo": "longitud_minima", "valor": 1000} o {"tipo": "campo_requerido", "campo": "descripcion_proyecto"}';

-- ========================================
-- TABLA: templates_capitulos
-- Templates de capítulos EIA por industria
-- ========================================
CREATE TABLE IF NOT EXISTS asistente_config.templates_capitulos (
    id SERIAL PRIMARY KEY,
    tipo_proyecto_id INTEGER NOT NULL REFERENCES asistente_config.tipos_proyecto(id) ON DELETE CASCADE,
    capitulo_numero INTEGER NOT NULL,
    titulo VARCHAR(200) NOT NULL,
    template_prompt TEXT NOT NULL,          -- Prompt para Claude al generar el capítulo
    estructura_esperada JSONB,              -- Estructura de subsecciones esperadas
    instrucciones_generacion TEXT,          -- Instrucciones específicas para generación
    ejemplos TEXT,                          -- Ejemplos de redacción del corpus SEA
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(tipo_proyecto_id, capitulo_numero)
);

CREATE INDEX IF NOT EXISTS idx_templates_tipo ON asistente_config.templates_capitulos(tipo_proyecto_id);

COMMENT ON TABLE asistente_config.templates_capitulos IS 'Templates de capítulos EIA por tipo de proyecto/industria';
COMMENT ON COLUMN asistente_config.templates_capitulos.template_prompt IS 'Prompt base para Claude con placeholders para datos del proyecto';
COMMENT ON COLUMN asistente_config.templates_capitulos.estructura_esperada IS 'Subsecciones y elementos que debe contener el capítulo';

-- ========================================
-- TABLA: observaciones_validacion
-- Observaciones detectadas en validaciones de documentos
-- ========================================
CREATE TABLE IF NOT EXISTS proyectos.observaciones_validacion (
    id SERIAL PRIMARY KEY,
    documento_id INTEGER NOT NULL REFERENCES proyectos.documentos_eia(id) ON DELETE CASCADE,
    regla_id INTEGER REFERENCES asistente_config.reglas_validacion_sea(id) ON DELETE SET NULL,
    capitulo_numero INTEGER,
    seccion VARCHAR(100),
    tipo_observacion VARCHAR(30) NOT NULL,
    severidad VARCHAR(20) NOT NULL,
    mensaje TEXT NOT NULL,
    sugerencia TEXT,
    contexto JSONB,                         -- Información adicional sobre la observación
    estado VARCHAR(20) DEFAULT 'pendiente', -- pendiente, corregida, ignorada
    created_at TIMESTAMPTZ DEFAULT NOW(),
    resuelta_at TIMESTAMPTZ,

    CONSTRAINT chk_estado_obs CHECK (estado IN ('pendiente', 'corregida', 'ignorada'))
);

CREATE INDEX IF NOT EXISTS idx_observaciones_documento ON proyectos.observaciones_validacion(documento_id);
CREATE INDEX IF NOT EXISTS idx_observaciones_estado ON proyectos.observaciones_validacion(estado);
CREATE INDEX IF NOT EXISTS idx_observaciones_severidad ON proyectos.observaciones_validacion(severidad);

COMMENT ON TABLE proyectos.observaciones_validacion IS 'Observaciones detectadas durante validación de documentos EIA';

-- ========================================
-- FUNCIÓN: Actualizar timestamp updated_at
-- ========================================
CREATE OR REPLACE FUNCTION update_documento_eia_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_documentos_eia_updated ON proyectos.documentos_eia;

CREATE TRIGGER trg_documentos_eia_updated
    BEFORE UPDATE ON proyectos.documentos_eia
    FOR EACH ROW
    EXECUTE FUNCTION update_documento_eia_timestamp();

-- ========================================
-- DATOS INICIALES: Reglas de validación básicas
-- ========================================

-- Reglas generales aplicables a todos los documentos
INSERT INTO asistente_config.reglas_validacion_sea (tipo_proyecto_id, capitulo_numero, codigo_regla, descripcion, tipo_validacion, criterio, mensaje_error, mensaje_sugerencia, severidad) VALUES
-- Validaciones generales de documento
(NULL, NULL, 'DOC_TITULO_REQ', 'El documento debe tener un título', 'completitud', '{"tipo": "campo_requerido", "campo": "titulo"}', 'El documento no tiene título', 'Ingrese un título descriptivo para el documento EIA', 'error'),
(NULL, NULL, 'DOC_METADATOS_REQ', 'El documento debe tener metadatos básicos', 'completitud', '{"tipo": "campos_requeridos", "campos": ["fecha", "empresa_consultora"]}', 'Faltan metadatos básicos del documento', 'Complete la información de fecha de elaboración y empresa consultora', 'warning'),

-- Validaciones de Capítulo 1: Resumen Ejecutivo
(NULL, 1, 'CAP1_LONG_MIN', 'El resumen ejecutivo debe tener una extensión mínima', 'contenido', '{"tipo": "longitud_minima", "palabras": 500}', 'El resumen ejecutivo es demasiado corto', 'Amplíe el resumen ejecutivo con información clave del proyecto', 'warning'),
(NULL, 1, 'CAP1_LONG_MAX', 'El resumen ejecutivo no debe exceder extensión máxima', 'contenido', '{"tipo": "longitud_maxima", "palabras": 3000}', 'El resumen ejecutivo es demasiado extenso', 'Condense el resumen ejecutivo a los aspectos más relevantes', 'warning'),

-- Validaciones de Capítulo 2: Descripción del Proyecto
(NULL, 2, 'CAP2_UBICACION_REQ', 'Debe especificarse la ubicación del proyecto', 'completitud', '{"tipo": "campo_requerido", "campo": "ubicacion"}', 'Falta información de ubicación del proyecto', 'Incluya coordenadas UTM, región, comuna y descripción de accesos', 'error'),
(NULL, 2, 'CAP2_COMPONENTES_REQ', 'Deben describirse los componentes del proyecto', 'completitud', '{"tipo": "campo_requerido", "campo": "componentes"}', 'Faltan componentes del proyecto', 'Describa obras, partes y acciones del proyecto', 'error'),

-- Validaciones de Capítulo 3: Antecedentes
(NULL, 3, 'CAP3_TITULAR_REQ', 'Deben incluirse antecedentes del titular', 'completitud', '{"tipo": "campo_requerido", "campo": "titular"}', 'Faltan antecedentes del titular', 'Incluya RUT, razón social y representante legal', 'error'),

-- Validaciones de Capítulo 5: Línea de Base
(NULL, 5, 'CAP5_AREA_INFLUENCIA', 'Debe justificarse el área de influencia', 'contenido', '{"tipo": "campo_requerido", "campo": "justificacion_area_influencia"}', 'Falta justificación del área de influencia', 'Incluya metodología y criterios para definir el área de influencia', 'error'),

-- Validaciones de Capítulo 6: Impactos
(NULL, 6, 'CAP6_MATRIZ_REQ', 'Debe incluirse matriz de evaluación de impactos', 'completitud', '{"tipo": "campo_requerido", "campo": "matriz_impactos"}', 'Falta la matriz de evaluación de impactos', 'Incluya matriz con identificación, evaluación y calificación de impactos', 'error'),

-- Validaciones de Capítulo 7: Medidas de mitigación
(NULL, 7, 'CAP7_PLAN_MEDIDAS', 'Debe incluirse plan de medidas de mitigación', 'completitud', '{"tipo": "campo_requerido", "campo": "plan_medidas"}', 'Falta el plan de medidas de mitigación', 'Describa medidas de mitigación, reparación y compensación', 'error'),

-- Validaciones de Capítulo 8: Plan de seguimiento
(NULL, 8, 'CAP8_INDICADORES', 'Debe incluirse indicadores de seguimiento', 'completitud', '{"tipo": "campo_requerido", "campo": "indicadores"}', 'Faltan indicadores de seguimiento ambiental', 'Defina indicadores, frecuencia y metodología de seguimiento', 'error'),

-- Validaciones de Capítulo 10: Normas ambientales
(NULL, 10, 'CAP10_NORMATIVA', 'Debe identificarse normativa ambiental aplicable', 'normativa', '{"tipo": "campo_requerido", "campo": "normativa_aplicable"}', 'Falta identificación de normativa ambiental', 'Liste toda la normativa ambiental aplicable al proyecto', 'error')
ON CONFLICT (codigo_regla) DO NOTHING;

-- ========================================
-- DATOS INICIALES: Templates básicos para Minería
-- ========================================

-- Obtener el ID del tipo de proyecto Minería
DO $$
DECLARE
    mineria_id INTEGER;
BEGIN
    SELECT id INTO mineria_id FROM asistente_config.tipos_proyecto WHERE nombre = 'Minería' LIMIT 1;

    IF mineria_id IS NOT NULL THEN
        -- Templates de capítulos para proyectos mineros
        INSERT INTO asistente_config.templates_capitulos (tipo_proyecto_id, capitulo_numero, titulo, template_prompt, estructura_esperada, instrucciones_generacion) VALUES

        (mineria_id, 1, 'Resumen Ejecutivo',
         'Genera un resumen ejecutivo para un proyecto minero que incluya: descripción general del proyecto, objetivo, ubicación, inversión, principales componentes, área de influencia, impactos significativos identificados y medidas de mitigación clave. Usa un estilo técnico y objetivo.',
         '{"secciones": ["descripcion_general", "objetivo", "ubicacion", "inversion", "componentes", "area_influencia", "impactos", "medidas_mitigacion"]}',
         'El resumen debe ser conciso pero completo, máximo 2-3 páginas. Enfocarse en aspectos ambientales relevantes.'),

        (mineria_id, 2, 'Descripción del Proyecto',
         'Genera una descripción detallada del proyecto minero incluyendo: antecedentes generales, objetivos, justificación, ubicación geográfica, accesos, componentes principales (obras, partes y acciones), etapas (construcción, operación, cierre), cronograma, mano de obra, servicios requeridos y vida útil.',
         '{"secciones": ["antecedentes", "objetivos", "justificacion", "ubicacion", "accesos", "componentes", "etapas", "cronograma", "mano_obra", "servicios", "vida_util"]}',
         'Debe ser exhaustivo y técnico. Incluir todas las obras civiles, instalaciones, equipos y procesos. Especificar coordenadas UTM y altitudes.'),

        (mineria_id, 3, 'Antecedentes',
         'Genera la sección de antecedentes que incluya: identificación del titular (RUT, razón social, domicilio), representante legal, empresa consultora responsable del estudio, profesionales que participaron, y marco normativo aplicable.',
         '{"secciones": ["titular", "representante_legal", "consultora", "equipo_profesional", "marco_normativo"]}',
         'Verificar que toda la información legal y de contacto esté completa y correcta.'),

        (mineria_id, 5, 'Línea de Base',
         'Genera la línea de base ambiental del proyecto minero cubriendo: medio físico (geología, geomorfología, suelos, hidrología, hidrogeología, clima, calidad aire), medio biótico (flora, fauna, ecosistemas), medio humano (demografía, actividades económicas, patrimonio cultural), y justificación del área de influencia.',
         '{"secciones": ["area_influencia", "medio_fisico", "medio_biotico", "medio_humano"]}',
         'Basar en información recopilada de estudios técnicos. Incluir mapas, figuras y tablas. Citar fuentes de información.'),

        (mineria_id, 6, 'Identificación y Evaluación de Impactos',
         'Genera la evaluación de impactos ambientales incluyendo: metodología de evaluación, identificación de impactos por componente ambiental y etapa del proyecto, matriz de evaluación, descripción detallada de impactos significativos, y análisis de efectos sinérgicos.',
         '{"secciones": ["metodologia", "identificacion_impactos", "matriz_evaluacion", "impactos_significativos", "efectos_sinergicos"]}',
         'Aplicar criterios de evaluación según Guía ICSARA del SEA. Calificar magnitud, extensión, duración, reversibilidad.'),

        (mineria_id, 7, 'Medidas de Mitigación, Reparación y Compensación',
         'Genera el plan de medidas ambientales incluyendo: medidas de mitigación por impacto identificado, medidas de reparación, medidas de compensación (si aplica), fichas de medidas con descripción, objetivo, lugar aplicación, indicador de cumplimiento, momento de aplicación, y responsable.',
         '{"secciones": ["medidas_mitigacion", "medidas_reparacion", "medidas_compensacion", "fichas_medidas"]}',
         'Cada medida debe tener ficha detallada. Asegurar que cubran todos los impactos significativos identificados.'),

        (mineria_id, 8, 'Plan de Seguimiento Ambiental',
         'Genera el plan de seguimiento que incluya: objetivos del seguimiento, componentes a monitorear, indicadores de seguimiento, frecuencia y metodología de monitoreo, puntos de medición, acciones ante desvíos, y reporte de resultados.',
         '{"secciones": ["objetivos", "componentes_monitorear", "indicadores", "frecuencia_metodologia", "puntos_medicion", "acciones_desvios", "reportes"]}',
         'Alineado con medidas de mitigación. Especificar indicadores medibles y verificables.')
        ON CONFLICT (tipo_proyecto_id, capitulo_numero) DO NOTHING;
    END IF;
END $$;

COMMIT;

-- ========================================
-- VERIFICACIÓN
-- ========================================
SELECT 'Migración 007 completada exitosamente' AS status;
