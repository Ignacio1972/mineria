-- ===========================================================================
-- Migracion: Estructura EIA (Fase 2)
-- Version: 1.0
-- Fecha: Enero 2026
-- Descripcion: Tablas para estructura del EIA por tipo de proyecto
-- ===========================================================================

-- ===========================================================================
-- 1. Capitulos del EIA por tipo de proyecto
-- ===========================================================================
CREATE TABLE IF NOT EXISTS asistente_config.capitulos_eia (
    id SERIAL PRIMARY KEY,
    tipo_proyecto_id INTEGER NOT NULL REFERENCES asistente_config.tipos_proyecto(id) ON DELETE CASCADE,
    numero INTEGER NOT NULL,
    titulo VARCHAR(200) NOT NULL,
    descripcion TEXT,
    contenido_requerido JSONB DEFAULT '[]'::jsonb,
    es_obligatorio BOOLEAN DEFAULT true,
    orden INTEGER NOT NULL,
    activo BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(tipo_proyecto_id, numero)
);

CREATE INDEX IF NOT EXISTS idx_capitulos_tipo
    ON asistente_config.capitulos_eia(tipo_proyecto_id);
CREATE INDEX IF NOT EXISTS idx_capitulos_orden
    ON asistente_config.capitulos_eia(tipo_proyecto_id, orden);

COMMENT ON TABLE asistente_config.capitulos_eia IS 'Capitulos del EIA segun Art. 18 DS 40, adaptados por tipo de proyecto';
COMMENT ON COLUMN asistente_config.capitulos_eia.numero IS 'Numero del capitulo (1-11)';
COMMENT ON COLUMN asistente_config.capitulos_eia.contenido_requerido IS 'Lista JSON de secciones/subsecciones requeridas';

-- ===========================================================================
-- 2. Componentes de Linea Base
-- ===========================================================================
CREATE TABLE IF NOT EXISTS asistente_config.componentes_linea_base (
    id SERIAL PRIMARY KEY,
    tipo_proyecto_id INTEGER NOT NULL REFERENCES asistente_config.tipos_proyecto(id) ON DELETE CASCADE,
    subtipo_id INTEGER REFERENCES asistente_config.subtipos_proyecto(id) ON DELETE SET NULL,
    capitulo_numero INTEGER DEFAULT 3,
    nombre VARCHAR(150) NOT NULL,
    codigo VARCHAR(50) NOT NULL,
    descripcion TEXT,
    metodologia TEXT,
    variables_monitorear JSONB DEFAULT '[]'::jsonb,
    estudios_requeridos JSONB DEFAULT '[]'::jsonb,
    duracion_estimada_dias INTEGER DEFAULT 30,
    es_obligatorio BOOLEAN DEFAULT true,
    condicion_activacion JSONB,
    orden INTEGER DEFAULT 0,
    activo BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(tipo_proyecto_id, codigo)
);

CREATE INDEX IF NOT EXISTS idx_componentes_tipo
    ON asistente_config.componentes_linea_base(tipo_proyecto_id);
CREATE INDEX IF NOT EXISTS idx_componentes_capitulo
    ON asistente_config.componentes_linea_base(capitulo_numero);

COMMENT ON TABLE asistente_config.componentes_linea_base IS 'Componentes ambientales a caracterizar en linea de base';
COMMENT ON COLUMN asistente_config.componentes_linea_base.variables_monitorear IS 'Variables a medir en campanas de monitoreo';
COMMENT ON COLUMN asistente_config.componentes_linea_base.estudios_requeridos IS 'Estudios tecnicos especificos requeridos';

-- ===========================================================================
-- 3. Estructura EIA por Proyecto (instancia generada)
-- ===========================================================================
CREATE TABLE IF NOT EXISTS proyectos.estructura_eia (
    id SERIAL PRIMARY KEY,
    proyecto_id INTEGER NOT NULL REFERENCES proyectos.proyectos(id) ON DELETE CASCADE,
    version INTEGER DEFAULT 1,
    capitulos JSONB NOT NULL DEFAULT '[]'::jsonb,
    pas_requeridos JSONB NOT NULL DEFAULT '[]'::jsonb,
    anexos_requeridos JSONB NOT NULL DEFAULT '[]'::jsonb,
    plan_linea_base JSONB DEFAULT '[]'::jsonb,
    estimacion_complejidad JSONB,
    notas TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID,
    UNIQUE(proyecto_id, version)
);

CREATE INDEX IF NOT EXISTS idx_estructura_proyecto
    ON proyectos.estructura_eia(proyecto_id);
CREATE INDEX IF NOT EXISTS idx_estructura_version
    ON proyectos.estructura_eia(proyecto_id, version DESC);

COMMENT ON TABLE proyectos.estructura_eia IS 'Estructura EIA generada para cada proyecto';
COMMENT ON COLUMN proyectos.estructura_eia.capitulos IS 'Lista de capitulos con estado y progreso';
COMMENT ON COLUMN proyectos.estructura_eia.pas_requeridos IS 'PAS identificados con estado de tramitacion';
COMMENT ON COLUMN proyectos.estructura_eia.anexos_requeridos IS 'Anexos tecnicos requeridos con estado';
COMMENT ON COLUMN proyectos.estructura_eia.estimacion_complejidad IS 'Estimacion de nivel, tiempo y recursos';

-- ===========================================================================
-- 4. DATOS INICIALES: Capitulos EIA para Mineria
-- ===========================================================================

-- Obtener ID del tipo mineria
DO $$
DECLARE
    v_tipo_mineria_id INTEGER;
BEGIN
    SELECT id INTO v_tipo_mineria_id FROM asistente_config.tipos_proyecto WHERE codigo = 'mineria';

    IF v_tipo_mineria_id IS NULL THEN
        RAISE NOTICE 'Tipo mineria no encontrado, saltando datos iniciales de capitulos';
        RETURN;
    END IF;

    -- Insertar los 11 capitulos del EIA para mineria
    INSERT INTO asistente_config.capitulos_eia
        (tipo_proyecto_id, numero, titulo, descripcion, contenido_requerido, es_obligatorio, orden)
    VALUES
        (v_tipo_mineria_id, 1, 'Descripcion del Proyecto',
         'Antecedentes generales, localizacion, partes, obras y acciones del proyecto',
         '["Antecedentes generales", "Identificacion del titular", "Objetivo del proyecto", "Tipologia segun Art. 3", "Localizacion", "Descripcion de partes y obras", "Descripcion de fases", "Insumos y servicios", "Emisiones y residuos", "Mano de obra", "Cronograma"]',
         true, 1),

        (v_tipo_mineria_id, 2, 'Area de Influencia',
         'Determinacion del area de influencia para cada elemento ambiental afectado',
         '["Criterios de delimitacion por componente", "AI medio fisico", "AI medio biotico", "AI medio humano", "AI patrimonio cultural", "AI paisaje", "Cartografia del AI"]',
         true, 2),

        (v_tipo_mineria_id, 3, 'Linea de Base',
         'Descripcion del estado actual del medio ambiente antes del proyecto',
         '["Medio fisico (clima, aire, ruido, geologia, hidrogeologia, hidrologia, suelos)", "Medio biotico (flora, vegetacion, fauna terrestre, ecosistemas acuaticos)", "Medio humano (geografico, demografico, antropologico, socioeconomico)", "Patrimonio cultural (arqueologico, paleontologico, historico)", "Paisaje", "Areas protegidas y sitios prioritarios", "Uso del territorio"]',
         true, 3),

        (v_tipo_mineria_id, 4, 'Prediccion y Evaluacion de Impactos',
         'Metodologia de evaluacion y prediccion de impactos ambientales',
         '["Metodologia de evaluacion (matriz Leopold u otra)", "Identificacion de impactos por fase y componente", "Evaluacion de efectos Art. 11", "Impactos significativos", "Impactos residuales"]',
         true, 4),

        (v_tipo_mineria_id, 5, 'Plan de Medidas',
         'Medidas de mitigacion, reparacion y compensacion ambiental',
         '["Jerarquia de mitigacion (prevenir, minimizar, restaurar, compensar)", "Medidas por componente ambiental", "Formato estandar por medida", "Indicadores de cumplimiento", "Responsables"]',
         true, 5),

        (v_tipo_mineria_id, 6, 'Plan de Prevencion de Contingencias y Emergencias',
         'Identificacion de riesgos y respuesta a contingencias',
         '["Identificacion de riesgos (HAZOP, What-If)", "Matriz de riesgos", "Contingencias tipicas (derrames, fallas estructurales, incendios, sismos)", "Medidas preventivas", "Medidas de respuesta", "Organizacion para emergencias", "Capacitacion y simulacros"]',
         true, 6),

        (v_tipo_mineria_id, 7, 'Plan de Seguimiento Ambiental',
         'Monitoreo de variables ambientales comprometidas',
         '["Variables a monitorear por componente", "Puntos de control con coordenadas", "Metodologia de medicion", "Frecuencia de monitoreo", "Limites y metas", "Acciones ante desviaciones", "Informes de seguimiento"]',
         true, 7),

        (v_tipo_mineria_id, 8, 'Normativa Ambiental Aplicable',
         'Normas de calidad ambiental y emision aplicables al proyecto',
         '["Normas de calidad ambiental (DS 59, DS 12, DS 113, DS 114, NCh 1333)", "Normas de emision (DS 138, DS 90, DS 46)", "Otras normativas (DS 38 ruido, DS 148 RESPEL)", "Cumplimiento normativo"]',
         true, 8),

        (v_tipo_mineria_id, 9, 'Permisos Ambientales Sectoriales',
         'PAS aplicables al proyecto segun Titulo VII RSEIA',
         '["Identificacion de PAS aplicables", "Requisitos por PAS", "Antecedentes tecnicos", "Contenidos minimos por permiso"]',
         true, 9),

        (v_tipo_mineria_id, 10, 'Relacion con Politicas, Planes y Programas',
         'Compatibilidad con instrumentos de planificacion territorial',
         '["Politica Nacional de Desarrollo Regional", "Estrategia Regional de Desarrollo", "Plan Regional de Ordenamiento Territorial", "Plan Regulador Comunal", "Plan de Desarrollo Comunal", "Analisis de compatibilidad"]',
         true, 10),

        (v_tipo_mineria_id, 11, 'Compromisos Ambientales Voluntarios',
         'Compromisos adicionales que el titular asume voluntariamente',
         '["Programas de desarrollo local", "Fondos comunitarios", "Capacitacion laboral", "Proyectos de conservacion", "Investigacion cientifica"]',
         false, 11)
    ON CONFLICT (tipo_proyecto_id, numero) DO UPDATE SET
        titulo = EXCLUDED.titulo,
        descripcion = EXCLUDED.descripcion,
        contenido_requerido = EXCLUDED.contenido_requerido,
        es_obligatorio = EXCLUDED.es_obligatorio;

    RAISE NOTICE 'Capitulos EIA para mineria insertados correctamente';
END $$;

-- ===========================================================================
-- 5. DATOS INICIALES: Componentes de Linea Base para Mineria
-- ===========================================================================

DO $$
DECLARE
    v_tipo_mineria_id INTEGER;
BEGIN
    SELECT id INTO v_tipo_mineria_id FROM asistente_config.tipos_proyecto WHERE codigo = 'mineria';

    IF v_tipo_mineria_id IS NULL THEN
        RAISE NOTICE 'Tipo mineria no encontrado, saltando componentes de linea base';
        RETURN;
    END IF;

    -- Insertar componentes de linea base para mineria
    INSERT INTO asistente_config.componentes_linea_base
        (tipo_proyecto_id, capitulo_numero, codigo, nombre, descripcion, metodologia,
         variables_monitorear, estudios_requeridos, duracion_estimada_dias, es_obligatorio, orden)
    VALUES
        -- Medio Fisico
        (v_tipo_mineria_id, 3, 'clima', 'Clima y Meteorologia',
         'Caracterizacion climatica del area de estudio',
         'Analisis de datos DGA/DMC (minimo 10 anos) + estacion meteorologica propia si se requiere',
         '["Temperatura (media, max, min)", "Precipitacion (media anual, estacionalidad)", "Viento (rosa de vientos, velocidad)", "Humedad relativa", "Evaporacion"]',
         '["Informe climatologico", "Rosa de vientos"]',
         30, true, 1),

        (v_tipo_mineria_id, 3, 'calidad_aire', 'Calidad del Aire',
         'Caracterizacion de la calidad del aire en el area de influencia',
         'Campanas de monitoreo segun D.S. 61/2008, minimo una campana representativa',
         '["MP10", "MP2.5", "SO2", "NOx", "CO"]',
         '["Informe de calidad del aire", "Modelacion de dispersion de contaminantes"]',
         90, true, 2),

        (v_tipo_mineria_id, 3, 'ruido', 'Ruido y Vibraciones',
         'Caracterizacion de niveles basales de ruido',
         'Mediciones segun D.S. 38/2011, identificando receptores sensibles',
         '["NPS Leq dia", "NPS Leq noche", "Vibraciones (si aplica)"]',
         '["Informe de ruido basal", "Modelacion acustica"]',
         30, true, 3),

        (v_tipo_mineria_id, 3, 'geologia', 'Geologia y Geomorfologia',
         'Contexto geologico regional y local del proyecto',
         'Revision de cartografia geologica SERNAGEOMIN + trabajo de campo',
         '["Unidades litologicas", "Estructuras (fallas, plegamientos)", "Procesos geomorfologicos"]',
         '["Informe geologico", "Mapa geologico local"]',
         60, true, 4),

        (v_tipo_mineria_id, 3, 'geotecnia', 'Geotecnia',
         'Caracterizacion geotecnica del terreno',
         'Ensayos de laboratorio y terreno, clasificacion geomecanica',
         '["Parametros geotecnicos", "Estabilidad de taludes", "Parametros sismicos"]',
         '["Informe geotecnico", "Analisis de estabilidad"]',
         60, true, 5),

        (v_tipo_mineria_id, 3, 'peligros_geologicos', 'Peligros Geologicos',
         'Evaluacion de peligros geologicos en el area',
         'Analisis de sismicidad, volcanismo, remociones en masa, inundaciones',
         '["Zona sismica", "Aceleracion de diseno", "Susceptibilidad a remociones"]',
         '["Informe de peligros geologicos"]',
         45, true, 6),

        (v_tipo_mineria_id, 3, 'hidrogeologia', 'Hidrogeologia',
         'Caracterizacion de aguas subterraneas',
         'Modelo hidrogeologico conceptual basado en sondajes y pruebas de bombeo',
         '["Niveles freaticos", "Direcciones de flujo", "Calidad aguas subterraneas", "Parametros hidraulicos"]',
         '["Informe hidrogeologico", "Modelo conceptual", "Balance hidrico"]',
         120, true, 7),

        (v_tipo_mineria_id, 3, 'hidrologia', 'Hidrologia',
         'Caracterizacion de aguas superficiales',
         'Analisis de cuencas, aforos, muestreo de calidad',
         '["Caudales (medio, max, min)", "Calidad de agua superficial", "Derechos de agua"]',
         '["Informe hidrologico", "Analisis de crecidas"]',
         90, true, 8),

        (v_tipo_mineria_id, 3, 'suelos', 'Suelos',
         'Caracterizacion de suelos del area',
         'Calicatas y analisis de laboratorio',
         '["Clasificacion capacidad de uso", "Caracteristicas fisico-quimicas"]',
         '["Informe edafologico"]',
         45, true, 9),

        -- Medio Biotico
        (v_tipo_mineria_id, 3, 'flora_vegetacion', 'Flora y Vegetacion',
         'Inventario floristico y caracterizacion de vegetacion',
         'Transectos, parcelas y puntos de muestreo, considerar estacionalidad',
         '["Formaciones vegetacionales", "Riqueza de especies", "Cobertura", "Especies en categoria de conservacion"]',
         '["Informe de flora y vegetacion", "Cartografia de formaciones"]',
         90, true, 10),

        (v_tipo_mineria_id, 3, 'fauna_terrestre', 'Fauna Terrestre',
         'Inventario de fauna terrestre por grupo taxonomico',
         'Transectos, trampas, avistamiento, camaras trampa, considerar estacionalidad',
         '["Mamiferos", "Aves", "Reptiles", "Anfibios", "Especies en categoria de conservacion"]',
         '["Informe de fauna", "Mapas de habitat"]',
         120, true, 11),

        (v_tipo_mineria_id, 3, 'ecosistemas_acuaticos', 'Ecosistemas Acuaticos Continentales',
         'Caracterizacion de biota acuatica',
         'Muestreo de macroinvertebrados, peces, vegetacion riberana',
         '["Macroinvertebrados", "Peces", "Vegetacion riberana", "Estado trofico"]',
         '["Informe limnologico"]',
         60, false, 12),

        -- Medio Humano
        (v_tipo_mineria_id, 3, 'medio_humano', 'Medio Humano',
         'Caracterizacion del medio humano en sus dimensiones',
         'Levantamiento de informacion primaria y secundaria',
         '["Dimension geografica", "Dimension demografica", "Dimension antropologica", "Dimension socioeconomica", "Bienestar social basico"]',
         '["Informe de medio humano", "Cartografia social"]',
         90, true, 13),

        (v_tipo_mineria_id, 3, 'pueblos_indigenas', 'Pueblos Indigenas',
         'Identificacion y caracterizacion de pueblos indigenas',
         'Consulta a CONADI, trabajo de campo con comunidades',
         '["Comunidades identificadas", "Uso del territorio", "Practicas culturales", "Sitios de significacion"]',
         '["Informe de pueblos indigenas"]',
         90, false, 14),

        -- Patrimonio Cultural
        (v_tipo_mineria_id, 3, 'arqueologia', 'Patrimonio Arqueologico',
         'Prospeccion arqueologica superficial y sondeos',
         'Prospeccion sistematica, autorizacion CMN para sondeos',
         '["Sitios registrados", "Cronologia", "Estado de conservacion"]',
         '["Informe arqueologico", "Autorizacion CMN"]',
         90, true, 15),

        (v_tipo_mineria_id, 3, 'paleontologia', 'Patrimonio Paleontologico',
         'Evaluacion del potencial paleontologico',
         'Revision de formaciones geologicas y prospeccion',
         '["Potencial paleontologico", "Hallazgos"]',
         '["Informe paleontologico"]',
         45, false, 16),

        -- Paisaje
        (v_tipo_mineria_id, 3, 'paisaje', 'Paisaje',
         'Caracterizacion de unidades de paisaje',
         'Analisis de cuencas visuales, calidad y fragilidad visual',
         '["Unidades de paisaje", "Calidad visual", "Fragilidad visual", "Puntos de observacion"]',
         '["Informe de paisaje", "Fotomontajes"]',
         45, true, 17),

        -- Areas Protegidas
        (v_tipo_mineria_id, 3, 'areas_protegidas', 'Areas Protegidas y Sitios Prioritarios',
         'Identificacion de areas bajo proteccion oficial',
         'Revision de SNASPE, sitios Ramsar, sitios prioritarios, humedales urbanos',
         '["SNASPE", "Santuarios de la Naturaleza", "Sitios Ramsar", "Sitios prioritarios", "Humedales urbanos"]',
         '["Informe de areas protegidas"]',
         30, true, 18),

        -- Uso del Territorio
        (v_tipo_mineria_id, 3, 'uso_territorio', 'Uso del Territorio',
         'Analisis de instrumentos de planificacion territorial',
         'Revision de IPT (PRC, PRI, PROT), uso actual del suelo',
         '["Zonificacion IPT", "Uso actual del suelo"]',
         '["Informe de uso del territorio"]',
         30, true, 19)
    ON CONFLICT (tipo_proyecto_id, codigo) DO UPDATE SET
        nombre = EXCLUDED.nombre,
        descripcion = EXCLUDED.descripcion,
        metodologia = EXCLUDED.metodologia,
        variables_monitorear = EXCLUDED.variables_monitorear,
        estudios_requeridos = EXCLUDED.estudios_requeridos,
        duracion_estimada_dias = EXCLUDED.duracion_estimada_dias,
        es_obligatorio = EXCLUDED.es_obligatorio,
        orden = EXCLUDED.orden;

    RAISE NOTICE 'Componentes de linea base para mineria insertados correctamente';
END $$;

-- ===========================================================================
-- 6. Trigger para actualizar updated_at
-- ===========================================================================
CREATE OR REPLACE FUNCTION proyectos.actualizar_estructura_eia_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_estructura_eia_updated_at ON proyectos.estructura_eia;
CREATE TRIGGER trg_estructura_eia_updated_at
    BEFORE UPDATE ON proyectos.estructura_eia
    FOR EACH ROW
    EXECUTE FUNCTION proyectos.actualizar_estructura_eia_updated_at();

-- ===========================================================================
-- Fin de la migracion
-- ===========================================================================
