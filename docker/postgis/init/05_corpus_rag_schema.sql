-- =====================================================
-- Schema para Sistema de Gestion Documental RAG
-- Proyecto: Mineria Ambiental
-- Version: 1.0
-- =====================================================

-- Asegurar que el schema legal existe
CREATE SCHEMA IF NOT EXISTS legal;

-- =====================================================
-- TABLA: legal.categorias
-- Taxonomia jerarquica de documentos (arbol con auto-referencia)
-- =====================================================
CREATE TABLE IF NOT EXISTS legal.categorias (
    id SERIAL PRIMARY KEY,

    -- Jerarquia
    parent_id INTEGER REFERENCES legal.categorias(id) ON DELETE CASCADE,
    nivel INTEGER NOT NULL DEFAULT 1,
    orden INTEGER NOT NULL DEFAULT 0,

    -- Identificacion
    codigo VARCHAR(100) UNIQUE NOT NULL,
    nombre VARCHAR(255) NOT NULL,
    descripcion TEXT,

    -- Configuracion
    tipo_documentos_permitidos VARCHAR(100)[] DEFAULT '{}',
    icono VARCHAR(50),
    color VARCHAR(7),

    -- Estado
    activo BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT nivel_valido CHECK (nivel >= 1 AND nivel <= 5)
);

CREATE INDEX IF NOT EXISTS idx_categorias_parent ON legal.categorias(parent_id);
CREATE INDEX IF NOT EXISTS idx_categorias_codigo ON legal.categorias(codigo);
CREATE INDEX IF NOT EXISTS idx_categorias_activo ON legal.categorias(activo);

-- Funcion para obtener path completo de categoria
CREATE OR REPLACE FUNCTION legal.get_categoria_path(categoria_id INTEGER)
RETURNS TEXT AS $$
    WITH RECURSIVE path AS (
        SELECT id, nombre, parent_id, nombre::TEXT as full_path
        FROM legal.categorias WHERE id = categoria_id
        UNION ALL
        SELECT c.id, c.nombre, c.parent_id, c.nombre || ' > ' || p.full_path
        FROM legal.categorias c
        JOIN path p ON c.id = p.parent_id
    )
    SELECT full_path FROM path WHERE parent_id IS NULL;
$$ LANGUAGE SQL;

-- =====================================================
-- TABLA: legal.archivos_originales
-- Almacena referencias a archivos fisicos (PDF/DOCX)
-- =====================================================
CREATE TABLE IF NOT EXISTS legal.archivos_originales (
    id SERIAL PRIMARY KEY,

    -- Archivo fisico
    nombre_original VARCHAR(500) NOT NULL,
    nombre_storage VARCHAR(255) NOT NULL,
    ruta_storage VARCHAR(1000) NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    tamano_bytes BIGINT NOT NULL,

    -- Integridad
    hash_sha256 VARCHAR(64) NOT NULL,

    -- Procesamiento
    texto_extraido TEXT,
    paginas INTEGER,
    procesado_at TIMESTAMP,

    -- Auditoria
    subido_por VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT archivo_hash_unico UNIQUE (hash_sha256)
);

CREATE INDEX IF NOT EXISTS idx_archivos_hash ON legal.archivos_originales(hash_sha256);

-- =====================================================
-- TABLA: legal.temas
-- Catalogo de temas para clasificacion consistente
-- =====================================================
CREATE TABLE IF NOT EXISTS legal.temas (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(50) UNIQUE NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT,

    -- Agrupacion
    grupo VARCHAR(50),

    -- Keywords para deteccion automatica
    keywords TEXT[] DEFAULT '{}',

    -- UI
    color VARCHAR(7),
    icono VARCHAR(50),

    activo BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insertar temas predefinidos
INSERT INTO legal.temas (codigo, nombre, grupo, keywords, color) VALUES
    ('agua', 'Recursos Hidricos', 'componente_ambiental',
     ARRAY['agua', 'hidrico', 'rio', 'lago', 'humedal', 'acuifero', 'caudal', 'DGA', 'cuenca'], '#3B82F6'),
    ('aire', 'Calidad del Aire', 'componente_ambiental',
     ARRAY['aire', 'emision', 'atmosferico', 'material particulado', 'MP10', 'MP2.5', 'contaminacion atmosferica'], '#94A3B8'),
    ('suelo', 'Suelo', 'componente_ambiental',
     ARRAY['suelo', 'erosion', 'contaminacion del suelo', 'edafico'], '#92400E'),
    ('flora_fauna', 'Flora y Fauna', 'componente_ambiental',
     ARRAY['flora', 'fauna', 'especie', 'biodiversidad', 'habitat', 'SAG', 'vegetacion', 'animal'], '#22C55E'),
    ('glaciares', 'Glaciares y Criosfera', 'componente_ambiental',
     ARRAY['glaciar', 'criosfera', 'permafrost', 'periglaciar', 'nieve', 'hielo'], '#06B6D4'),
    ('ruido', 'Ruido', 'componente_ambiental',
     ARRAY['ruido', 'acustico', 'decibeles', 'sonido', 'vibracion'], '#F59E0B'),
    ('patrimonio_arqueologico', 'Patrimonio Arqueologico', 'patrimonio',
     ARRAY['arqueologico', 'arqueologia', 'sitio arqueologico', 'CMN'], '#7C3AED'),
    ('patrimonio_paleontologico', 'Patrimonio Paleontologico', 'patrimonio',
     ARRAY['paleontologico', 'fosil', 'paleontologia'], '#A855F7'),
    ('comunidades_indigenas', 'Pueblos Indigenas', 'social',
     ARRAY['indigena', 'pueblo originario', 'consulta', 'CONADI', 'ADI', 'Convenio 169', 'etnia'], '#EC4899'),
    ('participacion_ciudadana', 'Participacion Ciudadana', 'procedimiento',
     ARRAY['participacion ciudadana', 'PAC', 'observacion ciudadana', 'consulta publica'], '#F97316'),
    ('areas_protegidas', 'Areas Protegidas', 'territorio',
     ARRAY['area protegida', 'SNASPE', 'parque nacional', 'reserva', 'santuario', 'CONAF', 'Ramsar'], '#10B981'),
    ('eia', 'Estudio de Impacto Ambiental', 'instrumento',
     ARRAY['EIA', 'estudio de impacto', 'articulo 11'], '#DC2626'),
    ('dia', 'Declaracion de Impacto Ambiental', 'instrumento',
     ARRAY['DIA', 'declaracion de impacto'], '#16A34A'),
    ('rca', 'Resolucion de Calificacion Ambiental', 'instrumento',
     ARRAY['RCA', 'resolucion de calificacion', 'calificacion ambiental'], '#2563EB'),
    ('mineria', 'Mineria', 'sector',
     ARRAY['mineria', 'minero', 'faena minera', 'SERNAGEOMIN', 'relaves', 'botadero', 'yacimiento'], '#854D0E'),
    ('energia', 'Energia', 'sector',
     ARRAY['energia', 'electrico', 'generacion', 'transmision', 'renovable', 'solar', 'eolico'], '#EAB308'),
    ('impactos_acumulativos', 'Impactos Acumulativos', 'metodologia',
     ARRAY['acumulativo', 'sinergico', 'impacto acumulativo', 'efecto sinergico'], '#6366F1'),
    ('linea_base', 'Linea Base', 'metodologia',
     ARRAY['linea base', 'linea de base', 'caracterizacion', 'diagnostico'], '#8B5CF6'),
    ('medidas_mitigacion', 'Medidas de Mitigacion', 'metodologia',
     ARRAY['mitigacion', 'compensacion', 'reparacion', 'medida ambiental'], '#14B8A6'),
    ('seguimiento', 'Seguimiento Ambiental', 'procedimiento',
     ARRAY['seguimiento', 'monitoreo', 'fiscalizacion', 'SMA', 'cumplimiento'], '#0EA5E9')
ON CONFLICT (codigo) DO NOTHING;

-- =====================================================
-- TABLA: legal.colecciones
-- Agrupaciones tematicas transversales de documentos
-- =====================================================
CREATE TABLE IF NOT EXISTS legal.colecciones (
    id SERIAL PRIMARY KEY,

    codigo VARCHAR(50) UNIQUE NOT NULL,
    nombre VARCHAR(255) NOT NULL,
    descripcion TEXT,

    -- Configuracion
    es_publica BOOLEAN DEFAULT true,
    orden INTEGER DEFAULT 0,

    -- UI
    color VARCHAR(7),
    icono VARCHAR(50),

    -- Auditoria
    creado_por VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insertar colecciones sugeridas
INSERT INTO legal.colecciones (codigo, nombre, descripcion, color) VALUES
    ('art11_triggers', 'Triggers Articulo 11', 'Documentacion sobre las 6 letras del Art. 11 Ley 19.300', '#DC2626'),
    ('normativa_aguas', 'Normativa de Aguas', 'Todo sobre recursos hidricos y DGA', '#3B82F6'),
    ('consulta_indigena', 'Consulta Indigena', 'Convenio 169 OIT y procedimientos de consulta', '#EC4899'),
    ('mineria_altura', 'Mineria de Altura', 'Glaciares, criosfera, proyectos cordilleranos', '#06B6D4'),
    ('patrimonio', 'Patrimonio Cultural', 'Arqueologico, paleontologico, historico', '#7C3AED'),
    ('nuevas_tecnologias', 'Nuevas Tecnologias', 'Hidrogeno verde, almacenamiento energia, desalinizacion', '#F59E0B'),
    ('guias_descripcion', 'Guias de Descripcion', 'Guias SEA para descripcion de proyectos por sector', '#22C55E'),
    ('criterios_evaluacion', 'Criterios de Evaluacion', 'Criterios tecnicos del SEA para evaluacion', '#8B5CF6')
ON CONFLICT (codigo) DO NOTHING;

-- =====================================================
-- Modificar tabla legal.documentos existente
-- Agregar nuevas columnas para el sistema mejorado
-- =====================================================
DO $$
BEGIN
    -- Categoria
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_schema = 'legal' AND table_name = 'documentos' AND column_name = 'categoria_id') THEN
        ALTER TABLE legal.documentos ADD COLUMN categoria_id INTEGER REFERENCES legal.categorias(id);
    END IF;

    -- Archivo original
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_schema = 'legal' AND table_name = 'documentos' AND column_name = 'archivo_id') THEN
        ALTER TABLE legal.documentos ADD COLUMN archivo_id INTEGER REFERENCES legal.archivos_originales(id);
    END IF;

    -- Versionado
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_schema = 'legal' AND table_name = 'documentos' AND column_name = 'version') THEN
        ALTER TABLE legal.documentos ADD COLUMN version INTEGER DEFAULT 1;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_schema = 'legal' AND table_name = 'documentos' AND column_name = 'version_anterior_id') THEN
        ALTER TABLE legal.documentos ADD COLUMN version_anterior_id INTEGER REFERENCES legal.documentos(id);
    END IF;

    -- Metadatos enriquecidos
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_schema = 'legal' AND table_name = 'documentos' AND column_name = 'resolucion_aprobatoria') THEN
        ALTER TABLE legal.documentos ADD COLUMN resolucion_aprobatoria VARCHAR(100);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_schema = 'legal' AND table_name = 'documentos' AND column_name = 'fecha_vigencia_fin') THEN
        ALTER TABLE legal.documentos ADD COLUMN fecha_vigencia_fin DATE;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_schema = 'legal' AND table_name = 'documentos' AND column_name = 'sectores') THEN
        ALTER TABLE legal.documentos ADD COLUMN sectores VARCHAR(100)[] DEFAULT '{}';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_schema = 'legal' AND table_name = 'documentos' AND column_name = 'tipologias_art3') THEN
        ALTER TABLE legal.documentos ADD COLUMN tipologias_art3 VARCHAR(20)[] DEFAULT '{}';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_schema = 'legal' AND table_name = 'documentos' AND column_name = 'triggers_art11') THEN
        ALTER TABLE legal.documentos ADD COLUMN triggers_art11 CHAR(1)[] DEFAULT '{}';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_schema = 'legal' AND table_name = 'documentos' AND column_name = 'componentes_ambientales') THEN
        ALTER TABLE legal.documentos ADD COLUMN componentes_ambientales VARCHAR(50)[] DEFAULT '{}';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_schema = 'legal' AND table_name = 'documentos' AND column_name = 'regiones_aplicables') THEN
        ALTER TABLE legal.documentos ADD COLUMN regiones_aplicables VARCHAR(50)[] DEFAULT '{}';
    END IF;

    -- Etapa del proceso SEIA (nuevo, basado en screenshots)
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_schema = 'legal' AND table_name = 'documentos' AND column_name = 'etapa_proceso') THEN
        ALTER TABLE legal.documentos ADD COLUMN etapa_proceso VARCHAR(50);
    END IF;

    -- Actor principal (SEA, OAECA, Titular, etc.)
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_schema = 'legal' AND table_name = 'documentos' AND column_name = 'actor_principal') THEN
        ALTER TABLE legal.documentos ADD COLUMN actor_principal VARCHAR(50);
    END IF;

    -- Busqueda
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_schema = 'legal' AND table_name = 'documentos' AND column_name = 'palabras_clave') THEN
        ALTER TABLE legal.documentos ADD COLUMN palabras_clave VARCHAR(100)[] DEFAULT '{}';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_schema = 'legal' AND table_name = 'documentos' AND column_name = 'resumen') THEN
        ALTER TABLE legal.documentos ADD COLUMN resumen TEXT;
    END IF;

    -- Auditoria mejorada
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_schema = 'legal' AND table_name = 'documentos' AND column_name = 'creado_por') THEN
        ALTER TABLE legal.documentos ADD COLUMN creado_por VARCHAR(255);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_schema = 'legal' AND table_name = 'documentos' AND column_name = 'modificado_por') THEN
        ALTER TABLE legal.documentos ADD COLUMN modificado_por VARCHAR(255);
    END IF;
END $$;

-- Indices para nuevas columnas
CREATE INDEX IF NOT EXISTS idx_documentos_categoria ON legal.documentos(categoria_id);
CREATE INDEX IF NOT EXISTS idx_documentos_tipo ON legal.documentos(tipo);
CREATE INDEX IF NOT EXISTS idx_documentos_estado ON legal.documentos(estado);
CREATE INDEX IF NOT EXISTS idx_documentos_etapa ON legal.documentos(etapa_proceso);
CREATE INDEX IF NOT EXISTS idx_documentos_actor ON legal.documentos(actor_principal);
CREATE INDEX IF NOT EXISTS idx_documentos_sectores ON legal.documentos USING GIN(sectores);
CREATE INDEX IF NOT EXISTS idx_documentos_triggers ON legal.documentos USING GIN(triggers_art11);
CREATE INDEX IF NOT EXISTS idx_documentos_componentes ON legal.documentos USING GIN(componentes_ambientales);

-- Busqueda full-text en titulo y resumen
CREATE INDEX IF NOT EXISTS idx_documentos_fts ON legal.documentos
    USING GIN(to_tsvector('spanish', coalesce(titulo, '') || ' ' || coalesce(resumen, '')));

-- =====================================================
-- TABLA: legal.fragmentos_temas (junction)
-- Relacion many-to-many entre fragmentos y temas
-- =====================================================
CREATE TABLE IF NOT EXISTS legal.fragmentos_temas (
    fragmento_id INTEGER REFERENCES legal.fragmentos(id) ON DELETE CASCADE,
    tema_id INTEGER REFERENCES legal.temas(id) ON DELETE CASCADE,

    -- Metadatos de la relacion
    confianza FLOAT DEFAULT 1.0,
    detectado_por VARCHAR(20) DEFAULT 'manual',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (fragmento_id, tema_id)
);

CREATE INDEX IF NOT EXISTS idx_fragmentos_temas_tema ON legal.fragmentos_temas(tema_id);

-- =====================================================
-- TABLA: legal.documentos_colecciones (junction)
-- Relacion many-to-many entre documentos y colecciones
-- =====================================================
CREATE TABLE IF NOT EXISTS legal.documentos_colecciones (
    documento_id INTEGER REFERENCES legal.documentos(id) ON DELETE CASCADE,
    coleccion_id INTEGER REFERENCES legal.colecciones(id) ON DELETE CASCADE,

    orden INTEGER DEFAULT 0,
    notas TEXT,
    agregado_por VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (documento_id, coleccion_id)
);

-- =====================================================
-- TABLA: legal.relaciones_documentos
-- Relaciones entre documentos
-- =====================================================
CREATE TABLE IF NOT EXISTS legal.relaciones_documentos (
    id SERIAL PRIMARY KEY,

    documento_origen_id INTEGER REFERENCES legal.documentos(id) ON DELETE CASCADE,
    documento_destino_id INTEGER REFERENCES legal.documentos(id) ON DELETE CASCADE,

    -- Tipos: reglamenta, interpreta, reemplaza, complementa, cita, modifica
    tipo_relacion VARCHAR(50) NOT NULL,

    descripcion TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT relacion_unica UNIQUE (documento_origen_id, documento_destino_id, tipo_relacion),
    CONSTRAINT no_auto_relacion CHECK (documento_origen_id != documento_destino_id)
);

CREATE INDEX IF NOT EXISTS idx_relaciones_origen ON legal.relaciones_documentos(documento_origen_id);
CREATE INDEX IF NOT EXISTS idx_relaciones_destino ON legal.relaciones_documentos(documento_destino_id);
CREATE INDEX IF NOT EXISTS idx_relaciones_tipo ON legal.relaciones_documentos(tipo_relacion);

-- =====================================================
-- TABLA: legal.historial_versiones
-- Auditoria de cambios en documentos
-- =====================================================
CREATE TABLE IF NOT EXISTS legal.historial_versiones (
    id SERIAL PRIMARY KEY,

    documento_id INTEGER REFERENCES legal.documentos(id) ON DELETE CASCADE,
    version INTEGER NOT NULL,

    -- Snapshot del documento en esa version
    datos_documento JSONB NOT NULL,

    -- Cambio
    tipo_cambio VARCHAR(50) NOT NULL,
    descripcion_cambio TEXT,

    -- Auditoria
    realizado_por VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_historial_documento ON legal.historial_versiones(documento_id);

-- =====================================================
-- INSERTAR CATEGORIAS BASE (Taxonomia del Doc 2)
-- =====================================================
INSERT INTO legal.categorias (codigo, nombre, descripcion, nivel, orden) VALUES
    -- Nivel 1: Categorias principales
    ('normativa_legal', 'Normativa Legal', 'Documentos con fuerza de ley que establecen obligaciones', 1, 1),
    ('guias_sea', 'Guias SEA', 'Documentos orientadores del SEA para evaluacion ambiental', 1, 2),
    ('instructivos_sea', 'Instructivos SEA', 'Directrices operativas del SEA (Ordinarios)', 1, 3),
    ('criterios_evaluacion', 'Criterios de Evaluacion', 'Documentos tecnicos con estandares de evaluacion', 1, 4),
    ('jurisprudencia', 'Jurisprudencia', 'Sentencias y dictamenes que interpretan normativa', 1, 5),
    ('documentos_proceso', 'Documentos de Proceso', 'Modelos y ejemplos de documentos del SEIA', 1, 6),
    ('recursos_adicionales', 'Recursos Adicionales', 'Normas de calidad, estadisticas y publicaciones', 1, 7)
ON CONFLICT (codigo) DO NOTHING;

-- Nivel 2: Subcategorias de Normativa Legal
INSERT INTO legal.categorias (codigo, nombre, descripcion, nivel, orden, parent_id) VALUES
    ('leyes', 'Leyes', 'Aprobadas por el Congreso Nacional', 2, 1,
     (SELECT id FROM legal.categorias WHERE codigo = 'normativa_legal')),
    ('reglamentos', 'Reglamentos', 'Decretos Supremos que detallan las leyes', 2, 2,
     (SELECT id FROM legal.categorias WHERE codigo = 'normativa_legal')),
    ('decretos_resoluciones', 'Decretos y Resoluciones', 'Normas especificas de aplicacion', 2, 3,
     (SELECT id FROM legal.categorias WHERE codigo = 'normativa_legal'))
ON CONFLICT (codigo) DO NOTHING;

-- Nivel 2: Subcategorias de Guias SEA
INSERT INTO legal.categorias (codigo, nombre, descripcion, nivel, orden, parent_id) VALUES
    ('guias_descripcion', 'Guias de Descripcion de Proyectos', 'Como describir proyectos por sector', 2, 1,
     (SELECT id FROM legal.categorias WHERE codigo = 'guias_sea')),
    ('guias_art11', 'Guias Articulo 11', 'Evaluacion de triggers EIA', 2, 2,
     (SELECT id FROM legal.categorias WHERE codigo = 'guias_sea')),
    ('guias_area_influencia', 'Guias de Area de Influencia', 'Metodologias para delimitar area de estudio', 2, 3,
     (SELECT id FROM legal.categorias WHERE codigo = 'guias_sea')),
    ('guias_pac', 'Guias de Participacion Ciudadana', 'Procesos de participacion ciudadana', 2, 4,
     (SELECT id FROM legal.categorias WHERE codigo = 'guias_sea')),
    ('guias_metodologias', 'Guias de Metodologias y Modelos', 'Modelacion y evaluacion tecnica', 2, 5,
     (SELECT id FROM legal.categorias WHERE codigo = 'guias_sea')),
    ('guias_pas', 'Guias de Permisos Ambientales Sectoriales', 'PAS tramitados en el SEIA', 2, 6,
     (SELECT id FROM legal.categorias WHERE codigo = 'guias_sea')),
    ('guias_normas', 'Guias de Aplicacion de Normas', 'Orientaciones para aplicar normativa', 2, 7,
     (SELECT id FROM legal.categorias WHERE codigo = 'guias_sea')),
    ('guias_no_vigentes', 'Guias No Vigentes', 'Guias reemplazadas (historico)', 2, 8,
     (SELECT id FROM legal.categorias WHERE codigo = 'guias_sea'))
ON CONFLICT (codigo) DO NOTHING;

-- Nivel 2: Subcategorias de Instructivos
INSERT INTO legal.categorias (codigo, nombre, descripcion, nivel, orden, parent_id) VALUES
    ('instructivos_consulta_indigena', 'Consulta a Pueblos Indigenas', 'Convenio 169 OIT', 2, 1,
     (SELECT id FROM legal.categorias WHERE codigo = 'instructivos_sea')),
    ('instructivos_procedimientos', 'Procedimientos Administrativos', 'e-SEIA, firma electronica, expedientes', 2, 2,
     (SELECT id FROM legal.categorias WHERE codigo = 'instructivos_sea')),
    ('instructivos_pertinencia', 'Pertinencia de Ingreso', 'Determinar ingreso al SEIA', 2, 3,
     (SELECT id FROM legal.categorias WHERE codigo = 'instructivos_sea')),
    ('instructivos_areas_protegidas', 'Areas Protegidas', 'Instructivos sobre areas bajo proteccion', 2, 4,
     (SELECT id FROM legal.categorias WHERE codigo = 'instructivos_sea')),
    ('instructivos_seguimiento', 'Seguimiento Ambiental', 'Seguimiento de RCA y auditorias', 2, 5,
     (SELECT id FROM legal.categorias WHERE codigo = 'instructivos_sea')),
    ('instructivos_pac', 'Participacion Ciudadana', 'Documentacion y admisibilidad PAC', 2, 6,
     (SELECT id FROM legal.categorias WHERE codigo = 'instructivos_sea'))
ON CONFLICT (codigo) DO NOTHING;

-- Nivel 2: Subcategorias de Criterios de Evaluacion
INSERT INTO legal.categorias (codigo, nombre, descripcion, nivel, orden, parent_id) VALUES
    ('criterios_componentes', 'Componentes Ambientales', 'Agua, aire, suelo, fauna, flora', 2, 1,
     (SELECT id FROM legal.categorias WHERE codigo = 'criterios_evaluacion')),
    ('criterios_patrimonio', 'Patrimonio Cultural', 'Arqueologico, paleontologico, historico', 2, 2,
     (SELECT id FROM legal.categorias WHERE codigo = 'criterios_evaluacion')),
    ('criterios_impactos', 'Impactos Especiales', 'Acumulativos, sinergicos, sombra', 2, 3,
     (SELECT id FROM legal.categorias WHERE codigo = 'criterios_evaluacion')),
    ('criterios_proyectos', 'Proyectos Especificos', 'Hidrogeno, energia, salmonicultura', 2, 4,
     (SELECT id FROM legal.categorias WHERE codigo = 'criterios_evaluacion'))
ON CONFLICT (codigo) DO NOTHING;

-- Nivel 2: Subcategorias de Jurisprudencia
INSERT INTO legal.categorias (codigo, nombre, descripcion, nivel, orden, parent_id) VALUES
    ('jurisprudencia_ta', 'Tribunales Ambientales', 'Sentencias de los 3 tribunales ambientales', 2, 1,
     (SELECT id FROM legal.categorias WHERE codigo = 'jurisprudencia')),
    ('jurisprudencia_cs', 'Corte Suprema', 'Recursos de casacion en materia ambiental', 2, 2,
     (SELECT id FROM legal.categorias WHERE codigo = 'jurisprudencia')),
    ('jurisprudencia_cgr', 'Contraloria General', 'Dictamenes sobre interpretacion normativa', 2, 3,
     (SELECT id FROM legal.categorias WHERE codigo = 'jurisprudencia'))
ON CONFLICT (codigo) DO NOTHING;

-- Nivel 2: Subcategorias de Documentos de Proceso
INSERT INTO legal.categorias (codigo, nombre, descripcion, nivel, orden, parent_id) VALUES
    ('modelos_templates', 'Modelos y Templates', 'Estructura tipo de DIA, EIA, Adendas', 2, 1,
     (SELECT id FROM legal.categorias WHERE codigo = 'documentos_proceso')),
    ('ejemplos_rca', 'Ejemplos de RCA', 'RCAs de proyectos como referencia', 2, 2,
     (SELECT id FROM legal.categorias WHERE codigo = 'documentos_proceso')),
    ('ejemplos_icsara', 'Ejemplos de ICSARA', 'Para entender observaciones tipicas', 2, 3,
     (SELECT id FROM legal.categorias WHERE codigo = 'documentos_proceso')),
    ('casos_estudio', 'Casos de Estudio', 'Analisis de proyectos por sector y trigger', 2, 4,
     (SELECT id FROM legal.categorias WHERE codigo = 'documentos_proceso'))
ON CONFLICT (codigo) DO NOTHING;

-- Nivel 3: Sub-subcategorias de Guias Art. 11
INSERT INTO legal.categorias (codigo, nombre, descripcion, nivel, orden, parent_id) VALUES
    ('guias_art11_letra_a', 'Letra a) Riesgo Salud', 'Riesgo para salud de la poblacion', 3, 1,
     (SELECT id FROM legal.categorias WHERE codigo = 'guias_art11')),
    ('guias_art11_letra_b', 'Letra b) Recursos Naturales', 'Efectos adversos sobre recursos naturales', 3, 2,
     (SELECT id FROM legal.categorias WHERE codigo = 'guias_art11')),
    ('guias_art11_letra_c', 'Letra c) Reasentamiento', 'Reasentamiento de comunidades humanas', 3, 3,
     (SELECT id FROM legal.categorias WHERE codigo = 'guias_art11')),
    ('guias_art11_letra_d', 'Letra d) Areas Protegidas', 'Localizacion en o proxima a areas protegidas', 3, 4,
     (SELECT id FROM legal.categorias WHERE codigo = 'guias_art11')),
    ('guias_art11_letra_e', 'Letra e) Patrimonio', 'Alteracion del patrimonio cultural', 3, 5,
     (SELECT id FROM legal.categorias WHERE codigo = 'guias_art11')),
    ('guias_art11_letra_f', 'Letra f) Paisaje', 'Alteracion de paisaje o sitios turisticos', 3, 6,
     (SELECT id FROM legal.categorias WHERE codigo = 'guias_art11'))
ON CONFLICT (codigo) DO NOTHING;

-- Nivel 3: Subcategorias de Guias de Descripcion por sector
INSERT INTO legal.categorias (codigo, nombre, descripcion, nivel, orden, parent_id) VALUES
    ('guias_desc_mineria', 'Mineria', 'Cobre, metales preciosos, litio', 3, 1,
     (SELECT id FROM legal.categorias WHERE codigo = 'guias_descripcion')),
    ('guias_desc_energia', 'Energia', 'Solar, eolico, hidro, geotermia', 3, 2,
     (SELECT id FROM legal.categorias WHERE codigo = 'guias_descripcion')),
    ('guias_desc_infraestructura', 'Infraestructura', 'Transporte, inmobiliario', 3, 3,
     (SELECT id FROM legal.categorias WHERE codigo = 'guias_descripcion')),
    ('guias_desc_acuicultura', 'Acuicultura', 'Salmonicultura, cultivos marinos', 3, 4,
     (SELECT id FROM legal.categorias WHERE codigo = 'guias_descripcion')),
    ('guias_desc_otros', 'Otros Sectores', 'Petroleo, gas, agroindustria', 3, 5,
     (SELECT id FROM legal.categorias WHERE codigo = 'guias_descripcion'))
ON CONFLICT (codigo) DO NOTHING;

-- =====================================================
-- TABLA: legal.plazos_proceso
-- Plazos legales del proceso SEIA (de los screenshots)
-- =====================================================
CREATE TABLE IF NOT EXISTS legal.plazos_proceso (
    id SERIAL PRIMARY KEY,
    instrumento VARCHAR(10) NOT NULL, -- 'DIA' o 'EIA'
    etapa VARCHAR(100) NOT NULL,
    plazo_dias INTEGER NOT NULL,
    descripcion TEXT,
    normativa_referencia VARCHAR(255),
    orden INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insertar plazos de DIA (del screenshot 3)
INSERT INTO legal.plazos_proceso (instrumento, etapa, plazo_dias, descripcion, orden) VALUES
    ('DIA', 'test_admisibilidad', 5, 'SEA realiza test de admisibilidad', 1),
    ('DIA', 'evaluacion_oaeca', 15, 'OAECA evaluan y emiten informes', 2),
    ('DIA', 'solicitud_adenda', 10, 'SEA solicita a OAECA informar Adenda', 3),
    ('DIA', 'icsara_complementario', 15, 'SEA elabora ICSARA Complementario', 4),
    ('DIA', 'elaboracion_ice', 10, 'SEA elabora y publica ICE', 5),
    ('DIA', 'calificacion', 5, 'Califica comision de Evaluacion o Director Ejecutivo', 6)
ON CONFLICT DO NOTHING;

-- Insertar plazos de EIA (del screenshot 2)
INSERT INTO legal.plazos_proceso (instrumento, etapa, plazo_dias, descripcion, orden) VALUES
    ('EIA', 'test_admisibilidad', 5, 'SEA realiza test de admisibilidad', 1),
    ('EIA', 'evaluacion_oaeca', 30, 'OAECA evaluan y emiten informes', 2),
    ('EIA', 'solicitud_adenda', 15, 'SEA solicita a OAECA informar Adenda', 3),
    ('EIA', 'icsara_complementario', 15, 'SEA elabora ICSARA Complementario', 4),
    ('EIA', 'elaboracion_ice', 15, 'SEA elabora y publica ICE', 5),
    ('EIA', 'visa_oaeca', 5, 'OAECA visa ICE', 6),
    ('EIA', 'calificacion', 4, 'Califica comision de Evaluacion o Director Ejecutivo', 7)
ON CONFLICT DO NOTHING;

-- =====================================================
-- TABLA: legal.actores_seia
-- Actores del proceso SEIA
-- =====================================================
CREATE TABLE IF NOT EXISTS legal.actores_seia (
    id SERIAL PRIMARY KEY,
    sigla VARCHAR(20) UNIQUE NOT NULL,
    nombre_completo VARCHAR(255) NOT NULL,
    descripcion TEXT,
    rol VARCHAR(100),
    url_sitio VARCHAR(500),
    activo BOOLEAN DEFAULT true
);

INSERT INTO legal.actores_seia (sigla, nombre_completo, descripcion, rol) VALUES
    ('SEA', 'Servicio de Evaluacion Ambiental', 'Administra el SEIA, coordina evaluacion, elabora informes consolidados', 'Administrador'),
    ('OAECA', 'Organos de la Administracion del Estado con Competencia Ambiental', 'Evaluan tecnicamente segun su especialidad', 'Evaluador'),
    ('SAG', 'Servicio Agricola y Ganadero', 'Fauna, flora, suelo agricola', 'Evaluador'),
    ('DGA', 'Direccion General de Aguas', 'Recursos hidricos, derechos de agua', 'Evaluador'),
    ('CONAF', 'Corporacion Nacional Forestal', 'Bosques, SNASPE', 'Evaluador'),
    ('CMN', 'Consejo de Monumentos Nacionales', 'Patrimonio arqueologico, paleontologico, historico', 'Evaluador'),
    ('SERNAGEOMIN', 'Servicio Nacional de Geologia y Mineria', 'Aspectos geologicos, seguridad minera', 'Evaluador'),
    ('CONADI', 'Corporacion Nacional de Desarrollo Indigena', 'Pueblos originarios, ADI', 'Evaluador'),
    ('SMA', 'Superintendencia del Medio Ambiente', 'Fiscalizacion post-RCA', 'Fiscalizador'),
    ('TITULAR', 'Titular del Proyecto', 'Empresa o persona que presenta proyecto', 'Proponente'),
    ('COMISION', 'Comision de Evaluacion Regional', 'Califica proyectos regionales', 'Calificador'),
    ('DE', 'Director Ejecutivo SEA', 'Califica proyectos interregionales', 'Calificador')
ON CONFLICT (sigla) DO NOTHING;

-- =====================================================
-- Actualizar trigger para updated_at
-- =====================================================
CREATE OR REPLACE FUNCTION legal.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Aplicar trigger a tablas con updated_at
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_categorias_updated_at') THEN
        CREATE TRIGGER update_categorias_updated_at
            BEFORE UPDATE ON legal.categorias
            FOR EACH ROW EXECUTE FUNCTION legal.update_updated_at_column();
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_colecciones_updated_at') THEN
        CREATE TRIGGER update_colecciones_updated_at
            BEFORE UPDATE ON legal.colecciones
            FOR EACH ROW EXECUTE FUNCTION legal.update_updated_at_column();
    END IF;
END $$;

-- =====================================================
-- Vistas utiles
-- =====================================================

-- Vista: Documentos con info de categoria
CREATE OR REPLACE VIEW legal.v_documentos_completos AS
SELECT
    d.*,
    c.nombre as categoria_nombre,
    c.codigo as categoria_codigo,
    legal.get_categoria_path(d.categoria_id) as categoria_path,
    a.nombre_original as archivo_nombre,
    a.mime_type as archivo_tipo,
    (SELECT COUNT(*) FROM legal.fragmentos f WHERE f.documento_id = d.id) as fragmentos_count
FROM legal.documentos d
LEFT JOIN legal.categorias c ON d.categoria_id = c.id
LEFT JOIN legal.archivos_originales a ON d.archivo_id = a.id;

-- Vista: Estadisticas del corpus
CREATE OR REPLACE VIEW legal.v_estadisticas_corpus AS
SELECT
    (SELECT COUNT(*) FROM legal.documentos) as total_documentos,
    (SELECT COUNT(*) FROM legal.fragmentos) as total_fragmentos,
    (SELECT COUNT(*) FROM legal.categorias WHERE activo = true) as total_categorias,
    (SELECT COUNT(*) FROM legal.archivos_originales) as total_archivos,
    (SELECT COUNT(DISTINCT tipo) FROM legal.documentos) as tipos_distintos,
    (SELECT COUNT(*) FROM legal.documentos WHERE estado = 'vigente') as documentos_vigentes;

COMMENT ON TABLE legal.categorias IS 'Taxonomia jerarquica de documentos del corpus RAG';
COMMENT ON TABLE legal.archivos_originales IS 'Referencias a archivos PDF/DOCX con hash de integridad';
COMMENT ON TABLE legal.temas IS 'Catalogo de temas para clasificacion de fragmentos';
COMMENT ON TABLE legal.colecciones IS 'Agrupaciones tematicas transversales de documentos';
COMMENT ON TABLE legal.plazos_proceso IS 'Plazos legales del proceso SEIA para DIA y EIA';
COMMENT ON TABLE legal.actores_seia IS 'Actores del Sistema de Evaluacion de Impacto Ambiental';
