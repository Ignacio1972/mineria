-- ===========================================================================
-- Migración: Configuración por Industria (asistente_config)
-- Versión: 1.1
-- Fecha: Enero 2026
-- ===========================================================================

-- Crear esquema si no existe
CREATE SCHEMA IF NOT EXISTS asistente_config;

-- ===========================================================================
-- 1. Tipos de Proyecto (Industrias)
-- ===========================================================================
CREATE TABLE IF NOT EXISTS asistente_config.tipos_proyecto (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(50) UNIQUE NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    letra_art3 VARCHAR(5),
    descripcion TEXT,
    activo BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tipos_proyecto_codigo
    ON asistente_config.tipos_proyecto(codigo);
CREATE INDEX IF NOT EXISTS idx_tipos_proyecto_activo
    ON asistente_config.tipos_proyecto(activo);

-- ===========================================================================
-- 2. Subtipos de Proyecto
-- ===========================================================================
CREATE TABLE IF NOT EXISTS asistente_config.subtipos_proyecto (
    id SERIAL PRIMARY KEY,
    tipo_proyecto_id INTEGER NOT NULL REFERENCES asistente_config.tipos_proyecto(id) ON DELETE CASCADE,
    codigo VARCHAR(50) NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT,
    activo BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(tipo_proyecto_id, codigo)
);

CREATE INDEX IF NOT EXISTS idx_subtipos_tipo
    ON asistente_config.subtipos_proyecto(tipo_proyecto_id);

-- ===========================================================================
-- 3. Umbrales SEIA
-- ===========================================================================
CREATE TABLE IF NOT EXISTS asistente_config.umbrales_seia (
    id SERIAL PRIMARY KEY,
    tipo_proyecto_id INTEGER NOT NULL REFERENCES asistente_config.tipos_proyecto(id) ON DELETE CASCADE,
    subtipo_id INTEGER REFERENCES asistente_config.subtipos_proyecto(id) ON DELETE SET NULL,
    parametro VARCHAR(100) NOT NULL,
    operador VARCHAR(10) NOT NULL,
    valor NUMERIC NOT NULL,
    unidad VARCHAR(50),
    resultado VARCHAR(50) NOT NULL,
    descripcion TEXT,
    norma_referencia VARCHAR(100),
    activo BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_umbrales_tipo
    ON asistente_config.umbrales_seia(tipo_proyecto_id);
CREATE INDEX IF NOT EXISTS idx_umbrales_subtipo
    ON asistente_config.umbrales_seia(subtipo_id);

-- ===========================================================================
-- 4. PAS por Tipo
-- ===========================================================================
CREATE TABLE IF NOT EXISTS asistente_config.pas_por_tipo (
    id SERIAL PRIMARY KEY,
    tipo_proyecto_id INTEGER NOT NULL REFERENCES asistente_config.tipos_proyecto(id) ON DELETE CASCADE,
    subtipo_id INTEGER REFERENCES asistente_config.subtipos_proyecto(id) ON DELETE SET NULL,
    articulo INTEGER NOT NULL,
    nombre VARCHAR(200) NOT NULL,
    organismo VARCHAR(100) NOT NULL,
    obligatoriedad VARCHAR(20) NOT NULL,
    condicion_activacion JSONB,
    descripcion TEXT,
    activo BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_pas_tipo
    ON asistente_config.pas_por_tipo(tipo_proyecto_id);
CREATE INDEX IF NOT EXISTS idx_pas_articulo
    ON asistente_config.pas_por_tipo(articulo);

-- ===========================================================================
-- 5. Normativa por Tipo
-- ===========================================================================
CREATE TABLE IF NOT EXISTS asistente_config.normativa_por_tipo (
    id SERIAL PRIMARY KEY,
    tipo_proyecto_id INTEGER NOT NULL REFERENCES asistente_config.tipos_proyecto(id) ON DELETE CASCADE,
    norma VARCHAR(100) NOT NULL,
    nombre VARCHAR(200) NOT NULL,
    componente VARCHAR(100),
    tipo_norma VARCHAR(50),
    aplica_siempre BOOLEAN DEFAULT false,
    descripcion TEXT,
    activo BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_normativa_tipo
    ON asistente_config.normativa_por_tipo(tipo_proyecto_id);

-- ===========================================================================
-- 6. OAECA por Tipo
-- ===========================================================================
CREATE TABLE IF NOT EXISTS asistente_config.oaeca_por_tipo (
    id SERIAL PRIMARY KEY,
    tipo_proyecto_id INTEGER NOT NULL REFERENCES asistente_config.tipos_proyecto(id) ON DELETE CASCADE,
    organismo VARCHAR(100) NOT NULL,
    competencias TEXT[],
    relevancia VARCHAR(20) NOT NULL,
    activo BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_oaeca_tipo
    ON asistente_config.oaeca_por_tipo(tipo_proyecto_id);

-- ===========================================================================
-- 7. Impactos por Tipo
-- ===========================================================================
CREATE TABLE IF NOT EXISTS asistente_config.impactos_por_tipo (
    id SERIAL PRIMARY KEY,
    tipo_proyecto_id INTEGER NOT NULL REFERENCES asistente_config.tipos_proyecto(id) ON DELETE CASCADE,
    subtipo_id INTEGER REFERENCES asistente_config.subtipos_proyecto(id) ON DELETE SET NULL,
    componente VARCHAR(100) NOT NULL,
    impacto TEXT NOT NULL,
    fase VARCHAR(50),
    frecuencia VARCHAR(20),
    activo BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_impactos_tipo
    ON asistente_config.impactos_por_tipo(tipo_proyecto_id);

-- ===========================================================================
-- 8. Anexos por Tipo
-- ===========================================================================
CREATE TABLE IF NOT EXISTS asistente_config.anexos_por_tipo (
    id SERIAL PRIMARY KEY,
    tipo_proyecto_id INTEGER NOT NULL REFERENCES asistente_config.tipos_proyecto(id) ON DELETE CASCADE,
    subtipo_id INTEGER REFERENCES asistente_config.subtipos_proyecto(id) ON DELETE SET NULL,
    codigo VARCHAR(10) NOT NULL,
    nombre VARCHAR(200) NOT NULL,
    profesional_responsable VARCHAR(100),
    obligatorio BOOLEAN DEFAULT false,
    condicion_activacion JSONB,
    descripcion TEXT,
    activo BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_anexos_tipo
    ON asistente_config.anexos_por_tipo(tipo_proyecto_id);

-- ===========================================================================
-- 9. Árbol de Preguntas
-- ===========================================================================
CREATE TABLE IF NOT EXISTS asistente_config.arboles_preguntas (
    id SERIAL PRIMARY KEY,
    tipo_proyecto_id INTEGER NOT NULL REFERENCES asistente_config.tipos_proyecto(id) ON DELETE CASCADE,
    subtipo_id INTEGER REFERENCES asistente_config.subtipos_proyecto(id) ON DELETE SET NULL,
    codigo VARCHAR(50) NOT NULL,
    pregunta_texto TEXT NOT NULL,
    tipo_respuesta VARCHAR(20) NOT NULL,
    opciones JSONB,
    orden INTEGER DEFAULT 0,
    es_obligatoria BOOLEAN DEFAULT false,
    campo_destino VARCHAR(100),
    categoria_destino VARCHAR(50),
    condicion_activacion JSONB,
    valida_umbral BOOLEAN DEFAULT false,
    ayuda TEXT,
    activo BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(tipo_proyecto_id, codigo)
);

CREATE INDEX IF NOT EXISTS idx_arboles_tipo
    ON asistente_config.arboles_preguntas(tipo_proyecto_id);
CREATE INDEX IF NOT EXISTS idx_arboles_orden
    ON asistente_config.arboles_preguntas(tipo_proyecto_id, orden);

-- ===========================================================================
-- DATOS INICIALES
-- ===========================================================================

-- Tipos de proyecto
INSERT INTO asistente_config.tipos_proyecto (codigo, nombre, letra_art3, descripcion) VALUES
('mineria', 'Minería', 'i)', 'Proyectos de extracción y procesamiento de minerales'),
('energia', 'Energía', 'c)', 'Centrales generadoras de energía eléctrica'),
('inmobiliario', 'Inmobiliario/Urbano', 'g)', 'Proyectos inmobiliarios y de urbanización'),
('acuicultura', 'Acuicultura/Pesca', 'n)', 'Proyectos de acuicultura y pesca'),
('infraestructura', 'Infraestructura Vial', 'e)', 'Autopistas, carreteras y caminos'),
('portuario', 'Portuario', 'f)', 'Puertos, terminales y muelles'),
('forestal', 'Forestal', 'm)', 'Proyectos de explotación forestal'),
('agroindustria', 'Agroindustria', 'l)', 'Agroindustria y plantas de procesamiento')
ON CONFLICT (codigo) DO NOTHING;

-- Subtipos minería
INSERT INTO asistente_config.subtipos_proyecto (tipo_proyecto_id, codigo, nombre, descripcion)
SELECT id, 'extraccion_rajo', 'Extracción a Rajo Abierto', 'Minería superficial a cielo abierto'
FROM asistente_config.tipos_proyecto WHERE codigo = 'mineria'
ON CONFLICT (tipo_proyecto_id, codigo) DO NOTHING;

INSERT INTO asistente_config.subtipos_proyecto (tipo_proyecto_id, codigo, nombre, descripcion)
SELECT id, 'extraccion_subterranea', 'Extracción Subterránea', 'Minería subterránea con túneles'
FROM asistente_config.tipos_proyecto WHERE codigo = 'mineria'
ON CONFLICT (tipo_proyecto_id, codigo) DO NOTHING;

INSERT INTO asistente_config.subtipos_proyecto (tipo_proyecto_id, codigo, nombre, descripcion)
SELECT id, 'planta_beneficio', 'Planta de Beneficio', 'Procesamiento de minerales'
FROM asistente_config.tipos_proyecto WHERE codigo = 'mineria'
ON CONFLICT (tipo_proyecto_id, codigo) DO NOTHING;

INSERT INTO asistente_config.subtipos_proyecto (tipo_proyecto_id, codigo, nombre, descripcion)
SELECT id, 'deposito_relaves', 'Depósito de Relaves', 'Almacenamiento de relaves mineros'
FROM asistente_config.tipos_proyecto WHERE codigo = 'mineria'
ON CONFLICT (tipo_proyecto_id, codigo) DO NOTHING;

INSERT INTO asistente_config.subtipos_proyecto (tipo_proyecto_id, codigo, nombre, descripcion)
SELECT id, 'botadero', 'Botadero de Estériles', 'Disposición de material estéril'
FROM asistente_config.tipos_proyecto WHERE codigo = 'mineria'
ON CONFLICT (tipo_proyecto_id, codigo) DO NOTHING;

-- Subtipos energía
INSERT INTO asistente_config.subtipos_proyecto (tipo_proyecto_id, codigo, nombre, descripcion)
SELECT id, 'solar', 'Central Solar Fotovoltaica', 'Generación de energía solar'
FROM asistente_config.tipos_proyecto WHERE codigo = 'energia'
ON CONFLICT (tipo_proyecto_id, codigo) DO NOTHING;

INSERT INTO asistente_config.subtipos_proyecto (tipo_proyecto_id, codigo, nombre, descripcion)
SELECT id, 'eolica', 'Parque Eólico', 'Generación de energía eólica'
FROM asistente_config.tipos_proyecto WHERE codigo = 'energia'
ON CONFLICT (tipo_proyecto_id, codigo) DO NOTHING;

INSERT INTO asistente_config.subtipos_proyecto (tipo_proyecto_id, codigo, nombre, descripcion)
SELECT id, 'hidro_pasada', 'Central Hidroeléctrica de Pasada', 'Generación hidroeléctrica sin embalse'
FROM asistente_config.tipos_proyecto WHERE codigo = 'energia'
ON CONFLICT (tipo_proyecto_id, codigo) DO NOTHING;

INSERT INTO asistente_config.subtipos_proyecto (tipo_proyecto_id, codigo, nombre, descripcion)
SELECT id, 'hidro_embalse', 'Central Hidroeléctrica de Embalse', 'Generación hidroeléctrica con embalse'
FROM asistente_config.tipos_proyecto WHERE codigo = 'energia'
ON CONFLICT (tipo_proyecto_id, codigo) DO NOTHING;

INSERT INTO asistente_config.subtipos_proyecto (tipo_proyecto_id, codigo, nombre, descripcion)
SELECT id, 'termoelectrica', 'Central Termoeléctrica', 'Generación termoeléctrica'
FROM asistente_config.tipos_proyecto WHERE codigo = 'energia'
ON CONFLICT (tipo_proyecto_id, codigo) DO NOTHING;

-- Umbrales SEIA minería
INSERT INTO asistente_config.umbrales_seia
(tipo_proyecto_id, parametro, operador, valor, unidad, resultado, norma_referencia)
SELECT id, 'tonelaje_mensual', '>=', 5000, 'ton/mes', 'ingresa_seia', 'Art. 3 i.1) DS 40'
FROM asistente_config.tipos_proyecto WHERE codigo = 'mineria'
ON CONFLICT DO NOTHING;

INSERT INTO asistente_config.umbrales_seia
(tipo_proyecto_id, parametro, operador, valor, unidad, resultado, norma_referencia)
SELECT id, 'superficie_rajo', '>=', 20, 'ha', 'ingresa_seia', 'Art. 3 i.2) DS 40'
FROM asistente_config.tipos_proyecto WHERE codigo = 'mineria'
ON CONFLICT DO NOTHING;

INSERT INTO asistente_config.umbrales_seia
(tipo_proyecto_id, parametro, operador, valor, unidad, resultado, norma_referencia)
SELECT id, 'capacidad_relaves', '>=', 1000000, 'm3', 'ingresa_seia', 'Art. 3 i.3) DS 40'
FROM asistente_config.tipos_proyecto WHERE codigo = 'mineria'
ON CONFLICT DO NOTHING;

-- Umbrales SEIA energía
INSERT INTO asistente_config.umbrales_seia
(tipo_proyecto_id, parametro, operador, valor, unidad, resultado, norma_referencia)
SELECT id, 'potencia_mw', '>=', 3, 'MW', 'ingresa_seia', 'Art. 3 c) DS 40'
FROM asistente_config.tipos_proyecto WHERE codigo = 'energia'
ON CONFLICT DO NOTHING;

INSERT INTO asistente_config.umbrales_seia
(tipo_proyecto_id, parametro, operador, valor, unidad, resultado, norma_referencia)
SELECT id, 'linea_transmision_kv', '>=', 23, 'kV', 'ingresa_seia', 'Art. 3 c) DS 40'
FROM asistente_config.tipos_proyecto WHERE codigo = 'energia'
ON CONFLICT DO NOTHING;

-- Umbrales SEIA inmobiliario
INSERT INTO asistente_config.umbrales_seia
(tipo_proyecto_id, parametro, operador, valor, unidad, resultado, norma_referencia)
SELECT id, 'superficie_ha', '>=', 7, 'ha', 'ingresa_seia', 'Art. 3 g) DS 40'
FROM asistente_config.tipos_proyecto WHERE codigo = 'inmobiliario'
ON CONFLICT DO NOTHING;

INSERT INTO asistente_config.umbrales_seia
(tipo_proyecto_id, parametro, operador, valor, unidad, resultado, norma_referencia)
SELECT id, 'viviendas', '>=', 300, 'unidades', 'ingresa_seia', 'Art. 3 g) DS 40'
FROM asistente_config.tipos_proyecto WHERE codigo = 'inmobiliario'
ON CONFLICT DO NOTHING;

-- PAS típicos minería
INSERT INTO asistente_config.pas_por_tipo
(tipo_proyecto_id, articulo, nombre, organismo, obligatoriedad, condicion_activacion)
SELECT id, 135, 'Aprobación de proyecto de depósito de relaves', 'SERNAGEOMIN', 'obligatorio', '{"tiene_relaves": true}'::jsonb
FROM asistente_config.tipos_proyecto WHERE codigo = 'mineria'
ON CONFLICT DO NOTHING;

INSERT INTO asistente_config.pas_por_tipo
(tipo_proyecto_id, articulo, nombre, organismo, obligatoriedad, condicion_activacion)
SELECT id, 136, 'Aprobación de proyecto de botadero de estériles', 'SERNAGEOMIN', 'obligatorio', '{"tiene_botadero": true}'::jsonb
FROM asistente_config.tipos_proyecto WHERE codigo = 'mineria'
ON CONFLICT DO NOTHING;

INSERT INTO asistente_config.pas_por_tipo
(tipo_proyecto_id, articulo, nombre, organismo, obligatoriedad)
SELECT id, 137, 'Aprobación de plan de cierre de faena minera', 'SERNAGEOMIN', 'obligatorio'
FROM asistente_config.tipos_proyecto WHERE codigo = 'mineria'
ON CONFLICT DO NOTHING;

INSERT INTO asistente_config.pas_por_tipo
(tipo_proyecto_id, articulo, nombre, organismo, obligatoriedad)
SELECT id, 138, 'Aprobación de método de explotación minera', 'SERNAGEOMIN', 'obligatorio'
FROM asistente_config.tipos_proyecto WHERE codigo = 'mineria'
ON CONFLICT DO NOTHING;

INSERT INTO asistente_config.pas_por_tipo
(tipo_proyecto_id, articulo, nombre, organismo, obligatoriedad, condicion_activacion)
SELECT id, 111, 'Obras de regularización y defensa de cauces naturales', 'DGA', 'frecuente', '{"interviene_cauce": true}'::jsonb
FROM asistente_config.tipos_proyecto WHERE codigo = 'mineria'
ON CONFLICT DO NOTHING;

INSERT INTO asistente_config.pas_por_tipo
(tipo_proyecto_id, articulo, nombre, organismo, obligatoriedad)
SELECT id, 120, 'Permiso para realizar trabajos de conservación', 'CMN', 'frecuente'
FROM asistente_config.tipos_proyecto WHERE codigo = 'mineria'
ON CONFLICT DO NOTHING;

INSERT INTO asistente_config.pas_por_tipo
(tipo_proyecto_id, articulo, nombre, organismo, obligatoriedad)
SELECT id, 132, 'Instalación de sistema de tratamiento de aguas servidas', 'SEREMI Salud', 'obligatorio'
FROM asistente_config.tipos_proyecto WHERE codigo = 'mineria'
ON CONFLICT DO NOTHING;

INSERT INTO asistente_config.pas_por_tipo
(tipo_proyecto_id, articulo, nombre, organismo, obligatoriedad)
SELECT id, 133, 'Permiso para manejo de residuos peligrosos', 'SEREMI Salud', 'obligatorio'
FROM asistente_config.tipos_proyecto WHERE codigo = 'mineria'
ON CONFLICT DO NOTHING;

-- Normativa minería
INSERT INTO asistente_config.normativa_por_tipo
(tipo_proyecto_id, norma, nombre, componente, tipo_norma, aplica_siempre)
SELECT id, 'D.S. 40/2012', 'Reglamento SEIA', NULL, 'general', true
FROM asistente_config.tipos_proyecto WHERE codigo = 'mineria'
ON CONFLICT DO NOTHING;

INSERT INTO asistente_config.normativa_por_tipo
(tipo_proyecto_id, norma, nombre, componente, tipo_norma, aplica_siempre)
SELECT id, 'D.S. 90/2000', 'Norma de Emisión para Descarga de Residuos Líquidos', 'agua', 'emision', true
FROM asistente_config.tipos_proyecto WHERE codigo = 'mineria'
ON CONFLICT DO NOTHING;

INSERT INTO asistente_config.normativa_por_tipo
(tipo_proyecto_id, norma, nombre, componente, tipo_norma, aplica_siempre)
SELECT id, 'D.S. 248/2007', 'Reglamento de Depósitos de Relaves', 'residuos', 'sectorial', false
FROM asistente_config.tipos_proyecto WHERE codigo = 'mineria'
ON CONFLICT DO NOTHING;

INSERT INTO asistente_config.normativa_por_tipo
(tipo_proyecto_id, norma, nombre, componente, tipo_norma, aplica_siempre)
SELECT id, 'Ley 20.551', 'Ley de Cierre de Faenas Mineras', NULL, 'sectorial', true
FROM asistente_config.tipos_proyecto WHERE codigo = 'mineria'
ON CONFLICT DO NOTHING;

-- OAECA minería
INSERT INTO asistente_config.oaeca_por_tipo
(tipo_proyecto_id, organismo, competencias, relevancia)
SELECT id, 'SERNAGEOMIN', ARRAY['seguridad minera', 'relaves', 'cierre de faenas', 'método de explotación'], 'principal'
FROM asistente_config.tipos_proyecto WHERE codigo = 'mineria'
ON CONFLICT DO NOTHING;

INSERT INTO asistente_config.oaeca_por_tipo
(tipo_proyecto_id, organismo, competencias, relevancia)
SELECT id, 'DGA', ARRAY['recursos hídricos', 'derechos de agua', 'cauces naturales'], 'principal'
FROM asistente_config.tipos_proyecto WHERE codigo = 'mineria'
ON CONFLICT DO NOTHING;

INSERT INTO asistente_config.oaeca_por_tipo
(tipo_proyecto_id, organismo, competencias, relevancia)
SELECT id, 'SAG', ARRAY['suelo', 'flora', 'fauna silvestre'], 'secundario'
FROM asistente_config.tipos_proyecto WHERE codigo = 'mineria'
ON CONFLICT DO NOTHING;

INSERT INTO asistente_config.oaeca_por_tipo
(tipo_proyecto_id, organismo, competencias, relevancia)
SELECT id, 'CMN', ARRAY['patrimonio arqueológico', 'monumentos nacionales'], 'secundario'
FROM asistente_config.tipos_proyecto WHERE codigo = 'mineria'
ON CONFLICT DO NOTHING;

-- Árbol de preguntas minería
INSERT INTO asistente_config.arboles_preguntas
(tipo_proyecto_id, codigo, pregunta_texto, tipo_respuesta, orden, es_obligatoria, campo_destino, categoria_destino)
SELECT id, 'nombre_proyecto', '¿Cuál es el nombre del proyecto?', 'texto', 1, true, 'nombre', 'identificacion'
FROM asistente_config.tipos_proyecto WHERE codigo = 'mineria'
ON CONFLICT (tipo_proyecto_id, codigo) DO NOTHING;

INSERT INTO asistente_config.arboles_preguntas
(tipo_proyecto_id, codigo, pregunta_texto, tipo_respuesta, orden, es_obligatoria, campo_destino, categoria_destino, opciones)
SELECT id, 'tipo_extraccion', '¿Qué tipo de extracción realizará el proyecto?', 'opcion', 2, true, 'tipo_extraccion', 'tecnico',
'{"opciones": ["Rajo abierto", "Subterránea", "Mixta"]}'::jsonb
FROM asistente_config.tipos_proyecto WHERE codigo = 'mineria'
ON CONFLICT (tipo_proyecto_id, codigo) DO NOTHING;

INSERT INTO asistente_config.arboles_preguntas
(tipo_proyecto_id, codigo, pregunta_texto, tipo_respuesta, orden, es_obligatoria, campo_destino, categoria_destino, valida_umbral)
SELECT id, 'tonelaje_mensual', '¿Cuál será el tonelaje mensual de extracción (en toneladas)?', 'numero', 3, true, 'tonelaje_mensual', 'tecnico', true
FROM asistente_config.tipos_proyecto WHERE codigo = 'mineria'
ON CONFLICT (tipo_proyecto_id, codigo) DO NOTHING;

INSERT INTO asistente_config.arboles_preguntas
(tipo_proyecto_id, codigo, pregunta_texto, tipo_respuesta, orden, es_obligatoria, campo_destino, categoria_destino)
SELECT id, 'mineral_principal', '¿Cuál es el mineral principal a extraer?', 'texto', 4, true, 'mineral_principal', 'tecnico'
FROM asistente_config.tipos_proyecto WHERE codigo = 'mineria'
ON CONFLICT (tipo_proyecto_id, codigo) DO NOTHING;

INSERT INTO asistente_config.arboles_preguntas
(tipo_proyecto_id, codigo, pregunta_texto, tipo_respuesta, orden, es_obligatoria, campo_destino, categoria_destino)
SELECT id, 'tiene_relaves', '¿El proyecto contempla un depósito de relaves?', 'boolean', 5, true, 'tiene_relaves', 'obras'
FROM asistente_config.tipos_proyecto WHERE codigo = 'mineria'
ON CONFLICT (tipo_proyecto_id, codigo) DO NOTHING;

INSERT INTO asistente_config.arboles_preguntas
(tipo_proyecto_id, codigo, pregunta_texto, tipo_respuesta, orden, es_obligatoria, campo_destino, categoria_destino)
SELECT id, 'tiene_botadero', '¿El proyecto contempla un botadero de estériles?', 'boolean', 6, true, 'tiene_botadero', 'obras'
FROM asistente_config.tipos_proyecto WHERE codigo = 'mineria'
ON CONFLICT (tipo_proyecto_id, codigo) DO NOTHING;

INSERT INTO asistente_config.arboles_preguntas
(tipo_proyecto_id, codigo, pregunta_texto, tipo_respuesta, orden, es_obligatoria, campo_destino, categoria_destino)
SELECT id, 'uso_agua_lps', '¿Cuál será el consumo de agua en litros por segundo?', 'numero', 7, true, 'uso_agua_lps', 'insumos'
FROM asistente_config.tipos_proyecto WHERE codigo = 'mineria'
ON CONFLICT (tipo_proyecto_id, codigo) DO NOTHING;

INSERT INTO asistente_config.arboles_preguntas
(tipo_proyecto_id, codigo, pregunta_texto, tipo_respuesta, orden, es_obligatoria, campo_destino, categoria_destino, opciones)
SELECT id, 'fuente_agua', '¿Cuál será la fuente de agua?', 'opcion', 8, true, 'fuente_agua', 'insumos',
'{"opciones": ["Subterránea", "Superficial", "Mar desalinizada", "Otra"]}'::jsonb
FROM asistente_config.tipos_proyecto WHERE codigo = 'mineria'
ON CONFLICT (tipo_proyecto_id, codigo) DO NOTHING;

COMMIT;
