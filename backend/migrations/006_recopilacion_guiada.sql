-- ===========================================================================
-- Migracion: Recopilacion Guiada (Fase 3)
-- Version: 1.0
-- Fecha: Enero 2026
-- Descripcion: Tablas para recopilacion de contenido EIA capitulo por capitulo
-- ===========================================================================

-- ===========================================================================
-- 1. Contenido EIA por Seccion (instancia por proyecto)
-- ===========================================================================
CREATE TABLE IF NOT EXISTS proyectos.contenido_eia (
    id SERIAL PRIMARY KEY,
    proyecto_id INTEGER NOT NULL REFERENCES proyectos.proyectos(id) ON DELETE CASCADE,
    capitulo_numero INTEGER NOT NULL,
    seccion_codigo VARCHAR(50) NOT NULL,
    seccion_nombre VARCHAR(200),
    contenido JSONB DEFAULT '{}'::jsonb,
    estado VARCHAR(20) DEFAULT 'pendiente',
    progreso INTEGER DEFAULT 0 CHECK (progreso >= 0 AND progreso <= 100),
    documentos_vinculados INTEGER[] DEFAULT '{}',
    validaciones JSONB DEFAULT '[]'::jsonb,
    inconsistencias JSONB DEFAULT '[]'::jsonb,
    sugerencias JSONB DEFAULT '[]'::jsonb,
    notas TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID,
    UNIQUE(proyecto_id, capitulo_numero, seccion_codigo)
);

CREATE INDEX IF NOT EXISTS idx_contenido_proyecto ON proyectos.contenido_eia(proyecto_id);
CREATE INDEX IF NOT EXISTS idx_contenido_capitulo ON proyectos.contenido_eia(capitulo_numero);
CREATE INDEX IF NOT EXISTS idx_contenido_estado ON proyectos.contenido_eia(estado);
CREATE INDEX IF NOT EXISTS idx_contenido_proyecto_capitulo ON proyectos.contenido_eia(proyecto_id, capitulo_numero);

COMMENT ON TABLE proyectos.contenido_eia IS 'Contenido recopilado por seccion del EIA para cada proyecto';
COMMENT ON COLUMN proyectos.contenido_eia.contenido IS 'Datos estructurados de la seccion (respuestas, valores, texto)';
COMMENT ON COLUMN proyectos.contenido_eia.documentos_vinculados IS 'IDs de documentos asociados a esta seccion';
COMMENT ON COLUMN proyectos.contenido_eia.validaciones IS 'Resultados de validacion de completitud';
COMMENT ON COLUMN proyectos.contenido_eia.inconsistencias IS 'Inconsistencias detectadas con otras secciones';

-- ===========================================================================
-- 2. Preguntas de Recopilacion por Seccion
-- ===========================================================================
CREATE TABLE IF NOT EXISTS asistente_config.preguntas_recopilacion (
    id SERIAL PRIMARY KEY,
    tipo_proyecto_id INTEGER NOT NULL REFERENCES asistente_config.tipos_proyecto(id) ON DELETE CASCADE,
    subtipo_id INTEGER REFERENCES asistente_config.subtipos_proyecto(id) ON DELETE SET NULL,
    capitulo_numero INTEGER NOT NULL,
    seccion_codigo VARCHAR(50) NOT NULL,
    seccion_nombre VARCHAR(200),
    codigo_pregunta VARCHAR(50) NOT NULL,
    pregunta TEXT NOT NULL,
    descripcion TEXT,
    tipo_respuesta VARCHAR(30) NOT NULL DEFAULT 'texto',
    opciones JSONB,
    valor_por_defecto JSONB,
    validaciones JSONB,
    es_obligatoria BOOLEAN DEFAULT true,
    condicion_activacion JSONB,
    orden INTEGER DEFAULT 0,
    activo BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(tipo_proyecto_id, capitulo_numero, seccion_codigo, codigo_pregunta)
);

CREATE INDEX IF NOT EXISTS idx_preguntas_tipo ON asistente_config.preguntas_recopilacion(tipo_proyecto_id);
CREATE INDEX IF NOT EXISTS idx_preguntas_capitulo ON asistente_config.preguntas_recopilacion(capitulo_numero);
CREATE INDEX IF NOT EXISTS idx_preguntas_seccion ON asistente_config.preguntas_recopilacion(seccion_codigo);

COMMENT ON TABLE asistente_config.preguntas_recopilacion IS 'Preguntas guiadas para recopilar informacion por seccion del EIA';
COMMENT ON COLUMN asistente_config.preguntas_recopilacion.tipo_respuesta IS 'Tipos: texto, numero, fecha, seleccion, seleccion_multiple, archivo, coordenadas, tabla';
COMMENT ON COLUMN asistente_config.preguntas_recopilacion.validaciones IS 'Reglas de validacion: {min, max, patron, requerido, etc}';
COMMENT ON COLUMN asistente_config.preguntas_recopilacion.condicion_activacion IS 'Condicion para mostrar pregunta: {campo: valor}';

-- ===========================================================================
-- 3. Reglas de Consistencia entre Capitulos
-- ===========================================================================
CREATE TABLE IF NOT EXISTS asistente_config.reglas_consistencia (
    id SERIAL PRIMARY KEY,
    tipo_proyecto_id INTEGER REFERENCES asistente_config.tipos_proyecto(id) ON DELETE CASCADE,
    codigo VARCHAR(50) NOT NULL UNIQUE,
    nombre VARCHAR(150) NOT NULL,
    descripcion TEXT,
    capitulo_origen INTEGER NOT NULL,
    seccion_origen VARCHAR(50) NOT NULL,
    campo_origen VARCHAR(100) NOT NULL,
    capitulo_destino INTEGER NOT NULL,
    seccion_destino VARCHAR(50) NOT NULL,
    campo_destino VARCHAR(100) NOT NULL,
    tipo_regla VARCHAR(30) NOT NULL DEFAULT 'igualdad',
    parametros JSONB,
    mensaje_error TEXT NOT NULL,
    severidad VARCHAR(20) DEFAULT 'warning',
    activo BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_reglas_tipo ON asistente_config.reglas_consistencia(tipo_proyecto_id);
CREATE INDEX IF NOT EXISTS idx_reglas_origen ON asistente_config.reglas_consistencia(capitulo_origen, seccion_origen);
CREATE INDEX IF NOT EXISTS idx_reglas_destino ON asistente_config.reglas_consistencia(capitulo_destino, seccion_destino);

COMMENT ON TABLE asistente_config.reglas_consistencia IS 'Reglas para detectar inconsistencias entre capitulos del EIA';
COMMENT ON COLUMN asistente_config.reglas_consistencia.tipo_regla IS 'Tipos: igualdad, contenido, rango, referencia, coherencia';
COMMENT ON COLUMN asistente_config.reglas_consistencia.severidad IS 'Niveles: error, warning, info';

-- ===========================================================================
-- 4. Historial de Extracciones de Documentos
-- ===========================================================================
CREATE TABLE IF NOT EXISTS proyectos.extracciones_documento (
    id SERIAL PRIMARY KEY,
    proyecto_id INTEGER NOT NULL REFERENCES proyectos.proyectos(id) ON DELETE CASCADE,
    documento_id INTEGER NOT NULL,
    tipo_documento VARCHAR(50),
    datos_extraidos JSONB NOT NULL DEFAULT '{}'::jsonb,
    mapeo_secciones JSONB DEFAULT '[]'::jsonb,
    confianza_extraccion NUMERIC(3,2) DEFAULT 0.00,
    estado VARCHAR(20) DEFAULT 'pendiente',
    errores JSONB DEFAULT '[]'::jsonb,
    procesado_por VARCHAR(50) DEFAULT 'claude_vision',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_extracciones_proyecto ON proyectos.extracciones_documento(proyecto_id);
CREATE INDEX IF NOT EXISTS idx_extracciones_documento ON proyectos.extracciones_documento(documento_id);

COMMENT ON TABLE proyectos.extracciones_documento IS 'Historial de extracciones de datos de documentos con IA';
COMMENT ON COLUMN proyectos.extracciones_documento.mapeo_secciones IS 'Mapeo sugerido de datos extraidos a secciones del EIA';
COMMENT ON COLUMN proyectos.extracciones_documento.confianza_extraccion IS 'Nivel de confianza de la extraccion (0-1)';

-- ===========================================================================
-- 5. Triggers para updated_at
-- ===========================================================================
CREATE OR REPLACE FUNCTION proyectos.actualizar_contenido_eia_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_contenido_eia_updated_at ON proyectos.contenido_eia;
CREATE TRIGGER trg_contenido_eia_updated_at
    BEFORE UPDATE ON proyectos.contenido_eia
    FOR EACH ROW
    EXECUTE FUNCTION proyectos.actualizar_contenido_eia_updated_at();

DROP TRIGGER IF EXISTS trg_extracciones_updated_at ON proyectos.extracciones_documento;
CREATE TRIGGER trg_extracciones_updated_at
    BEFORE UPDATE ON proyectos.extracciones_documento
    FOR EACH ROW
    EXECUTE FUNCTION proyectos.actualizar_contenido_eia_updated_at();

-- ===========================================================================
-- 6. DATOS INICIALES: Preguntas de Recopilacion para Mineria
-- ===========================================================================

DO $$
DECLARE
    v_tipo_mineria_id INTEGER;
BEGIN
    SELECT id INTO v_tipo_mineria_id FROM asistente_config.tipos_proyecto WHERE codigo = 'mineria';

    IF v_tipo_mineria_id IS NULL THEN
        RAISE NOTICE 'Tipo mineria no encontrado, saltando preguntas de recopilacion';
        RETURN;
    END IF;

    -- =========================================================================
    -- CAPITULO 1: Descripcion del Proyecto
    -- =========================================================================

    -- Seccion: Antecedentes Generales
    INSERT INTO asistente_config.preguntas_recopilacion
        (tipo_proyecto_id, capitulo_numero, seccion_codigo, seccion_nombre, codigo_pregunta, pregunta, tipo_respuesta, es_obligatoria, orden)
    VALUES
        (v_tipo_mineria_id, 1, 'antecedentes', 'Antecedentes Generales', 'nombre_proyecto',
         'Nombre oficial del proyecto minero', 'texto', true, 1),
        (v_tipo_mineria_id, 1, 'antecedentes', 'Antecedentes Generales', 'objetivo_proyecto',
         'Objetivo general del proyecto', 'texto', true, 2),
        (v_tipo_mineria_id, 1, 'antecedentes', 'Antecedentes Generales', 'justificacion',
         'Justificacion economica y estrategica del proyecto', 'texto', true, 3),
        (v_tipo_mineria_id, 1, 'antecedentes', 'Antecedentes Generales', 'antecedentes_seia',
         'Antecedentes de evaluaciones ambientales previas (si existen)', 'texto', false, 4),

        -- Seccion: Titular
        (v_tipo_mineria_id, 1, 'titular', 'Identificacion del Titular', 'razon_social',
         'Razon social del titular', 'texto', true, 1),
        (v_tipo_mineria_id, 1, 'titular', 'Identificacion del Titular', 'rut_titular',
         'RUT del titular', 'texto', true, 2),
        (v_tipo_mineria_id, 1, 'titular', 'Identificacion del Titular', 'direccion_titular',
         'Direccion del titular', 'texto', true, 3),
        (v_tipo_mineria_id, 1, 'titular', 'Identificacion del Titular', 'representante_legal',
         'Nombre del representante legal', 'texto', true, 4),
        (v_tipo_mineria_id, 1, 'titular', 'Identificacion del Titular', 'contacto_email',
         'Correo electronico de contacto', 'texto', true, 5),
        (v_tipo_mineria_id, 1, 'titular', 'Identificacion del Titular', 'contacto_telefono',
         'Telefono de contacto', 'texto', true, 6),

        -- Seccion: Localizacion
        (v_tipo_mineria_id, 1, 'localizacion', 'Localizacion', 'region',
         'Region donde se ubica el proyecto', 'seleccion', true, 1),
        (v_tipo_mineria_id, 1, 'localizacion', 'Localizacion', 'provincia',
         'Provincia donde se ubica el proyecto', 'texto', true, 2),
        (v_tipo_mineria_id, 1, 'localizacion', 'Localizacion', 'comuna',
         'Comuna donde se ubica el proyecto', 'texto', true, 3),
        (v_tipo_mineria_id, 1, 'localizacion', 'Localizacion', 'coordenadas_centroide',
         'Coordenadas del centroide del proyecto (UTM)', 'coordenadas', true, 4),
        (v_tipo_mineria_id, 1, 'localizacion', 'Localizacion', 'superficie_total',
         'Superficie total del proyecto (ha)', 'numero', true, 5),
        (v_tipo_mineria_id, 1, 'localizacion', 'Localizacion', 'altitud_media',
         'Altitud media del proyecto (m.s.n.m.)', 'numero', true, 6),
        (v_tipo_mineria_id, 1, 'localizacion', 'Localizacion', 'accesos',
         'Descripcion de vias de acceso al proyecto', 'texto', true, 7),

        -- Seccion: Partes y Obras
        (v_tipo_mineria_id, 1, 'partes_obras', 'Partes, Obras y Acciones', 'obras_permanentes',
         'Descripcion de obras permanentes (rajo, planta, depositos, etc.)', 'texto', true, 1),
        (v_tipo_mineria_id, 1, 'partes_obras', 'Partes, Obras y Acciones', 'obras_temporales',
         'Descripcion de obras temporales (campamentos, bodegas temporales)', 'texto', true, 2),
        (v_tipo_mineria_id, 1, 'partes_obras', 'Partes, Obras y Acciones', 'infraestructura_lineal',
         'Descripcion de infraestructura lineal (caminos, lineas electricas, ductos)', 'texto', false, 3),

        -- Seccion: Fases del Proyecto
        (v_tipo_mineria_id, 1, 'fases', 'Fases del Proyecto', 'fase_construccion',
         'Descripcion de la fase de construccion', 'texto', true, 1),
        (v_tipo_mineria_id, 1, 'fases', 'Fases del Proyecto', 'duracion_construccion',
         'Duracion estimada de construccion (meses)', 'numero', true, 2),
        (v_tipo_mineria_id, 1, 'fases', 'Fases del Proyecto', 'fase_operacion',
         'Descripcion de la fase de operacion', 'texto', true, 3),
        (v_tipo_mineria_id, 1, 'fases', 'Fases del Proyecto', 'vida_util',
         'Vida util del proyecto (anos)', 'numero', true, 4),
        (v_tipo_mineria_id, 1, 'fases', 'Fases del Proyecto', 'fase_cierre',
         'Descripcion de la fase de cierre', 'texto', true, 5),

        -- Seccion: Insumos
        (v_tipo_mineria_id, 1, 'insumos', 'Insumos y Servicios', 'consumo_agua',
         'Consumo de agua estimado (L/s)', 'numero', true, 1),
        (v_tipo_mineria_id, 1, 'insumos', 'Insumos y Servicios', 'fuente_agua',
         'Fuente de abastecimiento de agua', 'texto', true, 2),
        (v_tipo_mineria_id, 1, 'insumos', 'Insumos y Servicios', 'consumo_energia',
         'Consumo de energia estimado (MW)', 'numero', true, 3),
        (v_tipo_mineria_id, 1, 'insumos', 'Insumos y Servicios', 'fuente_energia',
         'Fuente de suministro electrico', 'texto', true, 4),
        (v_tipo_mineria_id, 1, 'insumos', 'Insumos y Servicios', 'combustibles',
         'Combustibles a utilizar y volumenes estimados', 'texto', true, 5),
        (v_tipo_mineria_id, 1, 'insumos', 'Insumos y Servicios', 'reactivos_quimicos',
         'Reactivos quimicos y sustancias peligrosas', 'texto', false, 6),

        -- Seccion: Emisiones y Residuos
        (v_tipo_mineria_id, 1, 'emisiones', 'Emisiones y Residuos', 'emisiones_atmosfericas',
         'Descripcion de emisiones atmosfericas (material particulado, gases)', 'texto', true, 1),
        (v_tipo_mineria_id, 1, 'emisiones', 'Emisiones y Residuos', 'efluentes_liquidos',
         'Descripcion de efluentes liquidos', 'texto', true, 2),
        (v_tipo_mineria_id, 1, 'emisiones', 'Emisiones y Residuos', 'residuos_solidos',
         'Descripcion de residuos solidos domesticos e industriales', 'texto', true, 3),
        (v_tipo_mineria_id, 1, 'emisiones', 'Emisiones y Residuos', 'residuos_peligrosos',
         'Descripcion de residuos peligrosos', 'texto', true, 4),
        (v_tipo_mineria_id, 1, 'emisiones', 'Emisiones y Residuos', 'ruido_vibraciones',
         'Fuentes de ruido y vibraciones', 'texto', true, 5),

        -- Seccion: Mano de Obra
        (v_tipo_mineria_id, 1, 'mano_obra', 'Mano de Obra', 'trabajadores_construccion',
         'Numero maximo de trabajadores en construccion', 'numero', true, 1),
        (v_tipo_mineria_id, 1, 'mano_obra', 'Mano de Obra', 'trabajadores_operacion',
         'Numero de trabajadores en operacion', 'numero', true, 2),
        (v_tipo_mineria_id, 1, 'mano_obra', 'Mano de Obra', 'sistema_turnos',
         'Sistema de turnos de trabajo', 'texto', true, 3),
        (v_tipo_mineria_id, 1, 'mano_obra', 'Mano de Obra', 'alojamiento',
         'Sistema de alojamiento de trabajadores', 'seleccion', true, 4)
    ON CONFLICT (tipo_proyecto_id, capitulo_numero, seccion_codigo, codigo_pregunta) DO UPDATE SET
        pregunta = EXCLUDED.pregunta,
        tipo_respuesta = EXCLUDED.tipo_respuesta,
        es_obligatoria = EXCLUDED.es_obligatoria,
        orden = EXCLUDED.orden;

    -- =========================================================================
    -- CAPITULO 2: Area de Influencia
    -- =========================================================================
    INSERT INTO asistente_config.preguntas_recopilacion
        (tipo_proyecto_id, capitulo_numero, seccion_codigo, seccion_nombre, codigo_pregunta, pregunta, tipo_respuesta, es_obligatoria, orden)
    VALUES
        (v_tipo_mineria_id, 2, 'criterios_ai', 'Criterios de Delimitacion', 'metodologia_ai',
         'Metodologia utilizada para delimitar el area de influencia', 'texto', true, 1),
        (v_tipo_mineria_id, 2, 'criterios_ai', 'Criterios de Delimitacion', 'criterios_generales',
         'Criterios generales de delimitacion aplicados', 'texto', true, 2),

        (v_tipo_mineria_id, 2, 'ai_fisico', 'AI Medio Fisico', 'ai_aire',
         'Delimitacion del AI para calidad del aire (descripcion y justificacion)', 'texto', true, 1),
        (v_tipo_mineria_id, 2, 'ai_fisico', 'AI Medio Fisico', 'ai_ruido',
         'Delimitacion del AI para ruido', 'texto', true, 2),
        (v_tipo_mineria_id, 2, 'ai_fisico', 'AI Medio Fisico', 'ai_agua_superficial',
         'Delimitacion del AI para aguas superficiales', 'texto', true, 3),
        (v_tipo_mineria_id, 2, 'ai_fisico', 'AI Medio Fisico', 'ai_agua_subterranea',
         'Delimitacion del AI para aguas subterraneas', 'texto', true, 4),
        (v_tipo_mineria_id, 2, 'ai_fisico', 'AI Medio Fisico', 'ai_suelos',
         'Delimitacion del AI para suelos', 'texto', true, 5),

        (v_tipo_mineria_id, 2, 'ai_biotico', 'AI Medio Biotico', 'ai_flora',
         'Delimitacion del AI para flora y vegetacion', 'texto', true, 1),
        (v_tipo_mineria_id, 2, 'ai_biotico', 'AI Medio Biotico', 'ai_fauna',
         'Delimitacion del AI para fauna terrestre', 'texto', true, 2),
        (v_tipo_mineria_id, 2, 'ai_biotico', 'AI Medio Biotico', 'ai_ecosistemas_acuaticos',
         'Delimitacion del AI para ecosistemas acuaticos (si aplica)', 'texto', false, 3),

        (v_tipo_mineria_id, 2, 'ai_humano', 'AI Medio Humano', 'ai_socioeconomico',
         'Delimitacion del AI para aspectos socioeconomicos', 'texto', true, 1),
        (v_tipo_mineria_id, 2, 'ai_humano', 'AI Medio Humano', 'ai_pueblos_indigenas',
         'Delimitacion del AI para pueblos indigenas (si aplica)', 'texto', false, 2),

        (v_tipo_mineria_id, 2, 'ai_patrimonio', 'AI Patrimonio Cultural', 'ai_arqueologia',
         'Delimitacion del AI para patrimonio arqueologico', 'texto', true, 1),

        (v_tipo_mineria_id, 2, 'ai_paisaje', 'AI Paisaje', 'ai_paisaje',
         'Delimitacion del AI para paisaje y cuencas visuales', 'texto', true, 1)
    ON CONFLICT (tipo_proyecto_id, capitulo_numero, seccion_codigo, codigo_pregunta) DO UPDATE SET
        pregunta = EXCLUDED.pregunta,
        tipo_respuesta = EXCLUDED.tipo_respuesta,
        es_obligatoria = EXCLUDED.es_obligatoria;

    -- =========================================================================
    -- CAPITULO 3: Linea de Base (preguntas clave por componente)
    -- =========================================================================
    INSERT INTO asistente_config.preguntas_recopilacion
        (tipo_proyecto_id, capitulo_numero, seccion_codigo, seccion_nombre, codigo_pregunta, pregunta, tipo_respuesta, es_obligatoria, orden)
    VALUES
        -- Clima
        (v_tipo_mineria_id, 3, 'clima', 'Clima y Meteorologia', 'fuentes_datos_clima',
         'Fuentes de datos meteorologicos utilizados', 'texto', true, 1),
        (v_tipo_mineria_id, 3, 'clima', 'Clima y Meteorologia', 'periodo_registro',
         'Periodo de registro de datos (anos)', 'numero', true, 2),
        (v_tipo_mineria_id, 3, 'clima', 'Clima y Meteorologia', 'tipo_clima',
         'Clasificacion climatica del area (Koppen)', 'texto', true, 3),
        (v_tipo_mineria_id, 3, 'clima', 'Clima y Meteorologia', 'temperatura_media',
         'Temperatura media anual (C)', 'numero', true, 4),
        (v_tipo_mineria_id, 3, 'clima', 'Clima y Meteorologia', 'precipitacion_anual',
         'Precipitacion media anual (mm)', 'numero', true, 5),

        -- Calidad del Aire
        (v_tipo_mineria_id, 3, 'calidad_aire', 'Calidad del Aire', 'campanas_realizadas',
         'Numero y periodos de campanas de monitoreo realizadas', 'texto', true, 1),
        (v_tipo_mineria_id, 3, 'calidad_aire', 'Calidad del Aire', 'estaciones_monitoreo',
         'Ubicacion de estaciones de monitoreo (coordenadas)', 'tabla', true, 2),
        (v_tipo_mineria_id, 3, 'calidad_aire', 'Calidad del Aire', 'resultados_mp10',
         'Resultados de MP10 (ug/m3)', 'texto', true, 3),
        (v_tipo_mineria_id, 3, 'calidad_aire', 'Calidad del Aire', 'resultados_mp25',
         'Resultados de MP2.5 (ug/m3)', 'texto', true, 4),

        -- Hidrogeologia
        (v_tipo_mineria_id, 3, 'hidrogeologia', 'Hidrogeologia', 'sondajes_realizados',
         'Numero y profundidad de sondajes realizados', 'texto', true, 1),
        (v_tipo_mineria_id, 3, 'hidrogeologia', 'Hidrogeologia', 'unidades_acuiferas',
         'Descripcion de unidades acuiferas identificadas', 'texto', true, 2),
        (v_tipo_mineria_id, 3, 'hidrogeologia', 'Hidrogeologia', 'niveles_freaticos',
         'Niveles freaticos medidos (m bajo superficie)', 'texto', true, 3),
        (v_tipo_mineria_id, 3, 'hidrogeologia', 'Hidrogeologia', 'calidad_agua_subterranea',
         'Caracterizacion de calidad de aguas subterraneas', 'texto', true, 4),

        -- Flora y Vegetacion
        (v_tipo_mineria_id, 3, 'flora', 'Flora y Vegetacion', 'metodologia_flora',
         'Metodologia de muestreo utilizada', 'texto', true, 1),
        (v_tipo_mineria_id, 3, 'flora', 'Flora y Vegetacion', 'formaciones_vegetacionales',
         'Formaciones vegetacionales identificadas', 'texto', true, 2),
        (v_tipo_mineria_id, 3, 'flora', 'Flora y Vegetacion', 'especies_totales',
         'Numero total de especies identificadas', 'numero', true, 3),
        (v_tipo_mineria_id, 3, 'flora', 'Flora y Vegetacion', 'especies_conservacion',
         'Especies en categoria de conservacion (listado)', 'texto', true, 4),

        -- Fauna
        (v_tipo_mineria_id, 3, 'fauna', 'Fauna Terrestre', 'metodologia_fauna',
         'Metodologia de muestreo por grupo taxonomico', 'texto', true, 1),
        (v_tipo_mineria_id, 3, 'fauna', 'Fauna Terrestre', 'mamiferos_identificados',
         'Especies de mamiferos identificadas', 'texto', true, 2),
        (v_tipo_mineria_id, 3, 'fauna', 'Fauna Terrestre', 'aves_identificadas',
         'Especies de aves identificadas', 'texto', true, 3),
        (v_tipo_mineria_id, 3, 'fauna', 'Fauna Terrestre', 'reptiles_identificados',
         'Especies de reptiles identificados', 'texto', true, 4),
        (v_tipo_mineria_id, 3, 'fauna', 'Fauna Terrestre', 'fauna_conservacion',
         'Especies de fauna en categoria de conservacion', 'texto', true, 5),

        -- Medio Humano
        (v_tipo_mineria_id, 3, 'medio_humano', 'Medio Humano', 'comunidades_identificadas',
         'Comunidades y localidades en el area de influencia', 'texto', true, 1),
        (v_tipo_mineria_id, 3, 'medio_humano', 'Medio Humano', 'poblacion_total',
         'Poblacion total en el AI', 'numero', true, 2),
        (v_tipo_mineria_id, 3, 'medio_humano', 'Medio Humano', 'actividades_economicas',
         'Principales actividades economicas', 'texto', true, 3),
        (v_tipo_mineria_id, 3, 'medio_humano', 'Medio Humano', 'servicios_basicos',
         'Cobertura de servicios basicos (agua, luz, alcantarillado)', 'texto', true, 4),

        -- Arqueologia
        (v_tipo_mineria_id, 3, 'arqueologia', 'Patrimonio Arqueologico', 'prospeccion_realizada',
         'Descripcion de prospeccion arqueologica realizada', 'texto', true, 1),
        (v_tipo_mineria_id, 3, 'arqueologia', 'Patrimonio Arqueologico', 'sitios_identificados',
         'Numero y tipo de sitios arqueologicos identificados', 'texto', true, 2),
        (v_tipo_mineria_id, 3, 'arqueologia', 'Patrimonio Arqueologico', 'autorizacion_cmn',
         'Numero de resolucion CMN autorizando trabajos', 'texto', false, 3)
    ON CONFLICT (tipo_proyecto_id, capitulo_numero, seccion_codigo, codigo_pregunta) DO UPDATE SET
        pregunta = EXCLUDED.pregunta,
        tipo_respuesta = EXCLUDED.tipo_respuesta,
        es_obligatoria = EXCLUDED.es_obligatoria;

    RAISE NOTICE 'Preguntas de recopilacion para mineria insertadas correctamente';
END $$;

-- ===========================================================================
-- 7. DATOS INICIALES: Reglas de Consistencia
-- ===========================================================================

DO $$
DECLARE
    v_tipo_mineria_id INTEGER;
BEGIN
    SELECT id INTO v_tipo_mineria_id FROM asistente_config.tipos_proyecto WHERE codigo = 'mineria';

    INSERT INTO asistente_config.reglas_consistencia
        (tipo_proyecto_id, codigo, nombre, descripcion, capitulo_origen, seccion_origen, campo_origen,
         capitulo_destino, seccion_destino, campo_destino, tipo_regla, mensaje_error, severidad)
    VALUES
        -- Consistencia de coordenadas
        (v_tipo_mineria_id, 'coord_cap1_cap2', 'Coordenadas Cap1 vs Cap2',
         'Las coordenadas del proyecto deben coincidir entre descripcion y area de influencia',
         1, 'localizacion', 'coordenadas_centroide',
         2, 'ai_fisico', 'coordenadas_referencia',
         'igualdad', 'Las coordenadas del centroide en Cap. 1 no coinciden con las de referencia en Cap. 2', 'error'),

        -- Consistencia de superficie
        (v_tipo_mineria_id, 'superficie_cap1_cap2', 'Superficie Cap1 vs AI',
         'La superficie del proyecto debe ser menor al area de influencia directa',
         1, 'localizacion', 'superficie_total',
         2, 'ai_fisico', 'superficie_ai_directa',
         'rango', 'La superficie del proyecto excede el area de influencia directa definida', 'warning'),

        -- Consistencia de comunas
        (v_tipo_mineria_id, 'comuna_cap1_cap3', 'Comuna Cap1 vs Medio Humano',
         'La comuna del proyecto debe coincidir con la caracterizada en medio humano',
         1, 'localizacion', 'comuna',
         3, 'medio_humano', 'comunas_caracterizadas',
         'contenido', 'La comuna del proyecto no esta incluida en las comunas caracterizadas en medio humano', 'error'),

        -- Consistencia de recursos hidricos
        (v_tipo_mineria_id, 'agua_cap1_cap3', 'Consumo agua vs disponibilidad',
         'El consumo de agua declarado debe ser coherente con la disponibilidad caracterizada',
         1, 'insumos', 'consumo_agua',
         3, 'hidrogeologia', 'disponibilidad_estimada',
         'rango', 'El consumo de agua declarado excede la disponibilidad caracterizada en linea base', 'warning'),

        -- Consistencia de trabajadores
        (v_tipo_mineria_id, 'trabajadores_cap1_cap5', 'Trabajadores vs medidas',
         'Las medidas del plan deben considerar el numero de trabajadores declarado',
         1, 'mano_obra', 'trabajadores_operacion',
         5, 'medidas_humano', 'trabajadores_considerados',
         'referencia', 'El numero de trabajadores en las medidas no coincide con lo declarado en Cap. 1', 'warning'),

        -- Consistencia de especies en conservacion
        (v_tipo_mineria_id, 'especies_cap3_cap5', 'Especies conservacion vs medidas',
         'Las especies en conservacion deben tener medidas especificas',
         3, 'flora', 'especies_conservacion',
         5, 'medidas_biotico', 'especies_con_medidas',
         'contenido', 'Hay especies en conservacion sin medidas de manejo asociadas', 'error'),

        -- Consistencia de sitios arqueologicos
        (v_tipo_mineria_id, 'arqueologia_cap3_cap5', 'Sitios arqueologicos vs medidas',
         'Los sitios arqueologicos identificados deben tener medidas de proteccion',
         3, 'arqueologia', 'sitios_identificados',
         5, 'medidas_patrimonio', 'sitios_con_medidas',
         'contenido', 'Hay sitios arqueologicos sin medidas de proteccion definidas', 'error')
    ON CONFLICT (codigo) DO UPDATE SET
        nombre = EXCLUDED.nombre,
        descripcion = EXCLUDED.descripcion,
        mensaje_error = EXCLUDED.mensaje_error,
        severidad = EXCLUDED.severidad;

    RAISE NOTICE 'Reglas de consistencia insertadas correctamente';
END $$;

-- ===========================================================================
-- Fin de la migracion
-- ===========================================================================
