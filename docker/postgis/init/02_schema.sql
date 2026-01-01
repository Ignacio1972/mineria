-- ============================================
-- ESQUEMA BASE DE DATOS: MINERIA PREFACTIBILIDAD
-- ============================================

-- Esquema para capas GIS
CREATE SCHEMA IF NOT EXISTS gis;

-- Esquema para datos legales/RAG
CREATE SCHEMA IF NOT EXISTS legal;

-- Esquema para proyectos
CREATE SCHEMA IF NOT EXISTS proyectos;

-- ============================================
-- TABLAS GIS
-- ============================================

-- Áreas protegidas (SNASPE, Santuarios, etc.)
CREATE TABLE gis.areas_protegidas (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    tipo VARCHAR(100) NOT NULL, -- 'Parque Nacional', 'Reserva Nacional', 'Monumento Natural', 'Santuario', etc.
    categoria VARCHAR(100), -- Categoría SNASPE
    region VARCHAR(100),
    comuna VARCHAR(100),
    superficie_ha NUMERIC(12, 2),
    fecha_creacion DATE,
    decreto VARCHAR(100),
    fuente VARCHAR(255),
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    geom GEOMETRY(MultiPolygon, 4326) NOT NULL
);

CREATE INDEX idx_areas_protegidas_geom ON gis.areas_protegidas USING GIST(geom);
CREATE INDEX idx_areas_protegidas_geog ON gis.areas_protegidas USING GIST((geom::geography));
CREATE INDEX idx_areas_protegidas_tipo ON gis.areas_protegidas(tipo);
CREATE INDEX idx_areas_protegidas_region ON gis.areas_protegidas(region);

-- Glaciares
CREATE TABLE gis.glaciares (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255),
    tipo VARCHAR(100), -- 'Glaciar descubierto', 'Glaciar cubierto', 'Glaciarete', 'Campo de nieve'
    cuenca VARCHAR(255),
    subcuenca VARCHAR(255),
    region VARCHAR(100),
    superficie_km2 NUMERIC(10, 4),
    altitud_min_m INTEGER,
    altitud_max_m INTEGER,
    fuente VARCHAR(255),
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    geom GEOMETRY(MultiPolygon, 4326) NOT NULL
);

CREATE INDEX idx_glaciares_geom ON gis.glaciares USING GIST(geom);
CREATE INDEX idx_glaciares_geog ON gis.glaciares USING GIST((geom::geography));
CREATE INDEX idx_glaciares_region ON gis.glaciares(region);

-- Cuerpos de agua (ríos, lagos, humedales)
CREATE TABLE gis.cuerpos_agua (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255),
    tipo VARCHAR(100) NOT NULL, -- 'Río', 'Lago', 'Laguna', 'Humedal', 'Embalse'
    cuenca VARCHAR(255),
    subcuenca VARCHAR(255),
    region VARCHAR(100),
    es_sitio_ramsar BOOLEAN DEFAULT FALSE,
    fuente VARCHAR(255),
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    geom GEOMETRY(Geometry, 4326) NOT NULL -- Puede ser línea o polígono
);

CREATE INDEX idx_cuerpos_agua_geom ON gis.cuerpos_agua USING GIST(geom);
CREATE INDEX idx_cuerpos_agua_geog ON gis.cuerpos_agua USING GIST((geom::geography));
CREATE INDEX idx_cuerpos_agua_tipo ON gis.cuerpos_agua(tipo);

-- Comunidades indígenas
CREATE TABLE gis.comunidades_indigenas (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    pueblo VARCHAR(100), -- 'Mapuche', 'Aymara', 'Atacameño', 'Diaguita', 'Rapa Nui', etc.
    tipo VARCHAR(100), -- 'Comunidad', 'Asociación', 'ADI'
    region VARCHAR(100),
    comuna VARCHAR(100),
    es_adi BOOLEAN DEFAULT FALSE, -- Área de Desarrollo Indígena
    nombre_adi VARCHAR(255),
    fuente VARCHAR(255),
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    geom GEOMETRY(Geometry, 4326) NOT NULL -- Punto o polígono
);

CREATE INDEX idx_comunidades_indigenas_geom ON gis.comunidades_indigenas USING GIST(geom);
CREATE INDEX idx_comunidades_indigenas_geog ON gis.comunidades_indigenas USING GIST((geom::geography));
CREATE INDEX idx_comunidades_indigenas_pueblo ON gis.comunidades_indigenas(pueblo);

-- Centros poblados
CREATE TABLE gis.centros_poblados (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    tipo VARCHAR(100), -- 'Ciudad', 'Pueblo', 'Aldea', 'Caserío'
    region VARCHAR(100),
    comuna VARCHAR(100),
    poblacion INTEGER,
    fuente VARCHAR(255),
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    geom GEOMETRY(Point, 4326) NOT NULL
);

CREATE INDEX idx_centros_poblados_geom ON gis.centros_poblados USING GIST(geom);
CREATE INDEX idx_centros_poblados_geog ON gis.centros_poblados USING GIST((geom::geography));

-- Sitios arqueológicos y patrimoniales
CREATE TABLE gis.sitios_patrimoniales (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    tipo VARCHAR(100), -- 'Sitio arqueológico', 'Monumento histórico', 'Zona típica'
    categoria VARCHAR(100),
    decreto VARCHAR(100),
    region VARCHAR(100),
    comuna VARCHAR(100),
    descripcion TEXT,
    fuente VARCHAR(255),
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    geom GEOMETRY(Geometry, 4326) NOT NULL
);

CREATE INDEX idx_sitios_patrimoniales_geom ON gis.sitios_patrimoniales USING GIST(geom);
CREATE INDEX idx_sitios_patrimoniales_geog ON gis.sitios_patrimoniales USING GIST((geom::geography));

-- División político-administrativa
CREATE TABLE gis.regiones (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(10) NOT NULL UNIQUE,
    nombre VARCHAR(255) NOT NULL,
    geom GEOMETRY(MultiPolygon, 4326) NOT NULL
);

CREATE INDEX idx_regiones_geom ON gis.regiones USING GIST(geom);

CREATE TABLE gis.comunas (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(10) NOT NULL UNIQUE,
    nombre VARCHAR(255) NOT NULL,
    region_codigo VARCHAR(10) REFERENCES gis.regiones(codigo),
    provincia VARCHAR(255),
    geom GEOMETRY(MultiPolygon, 4326) NOT NULL
);

CREATE INDEX idx_comunas_geom ON gis.comunas USING GIST(geom);

-- ============================================
-- TABLAS LEGALES / RAG
-- ============================================

-- Documentos legales
CREATE TABLE legal.documentos (
    id SERIAL PRIMARY KEY,
    titulo VARCHAR(500) NOT NULL,
    tipo VARCHAR(100) NOT NULL, -- 'Ley', 'Reglamento', 'Decreto', 'Guía SEA', 'EIA', 'DIA', 'RCA'
    numero VARCHAR(100),
    fecha_publicacion DATE,
    fecha_vigencia DATE,
    organismo VARCHAR(255), -- 'Congreso', 'MINSEGPRES', 'MMA', 'SEA', etc.
    url_fuente VARCHAR(500),
    contenido_completo TEXT,
    estado VARCHAR(50) DEFAULT 'vigente', -- 'vigente', 'derogado', 'modificado'
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_documentos_tipo ON legal.documentos(tipo);
CREATE INDEX idx_documentos_estado ON legal.documentos(estado);

-- Fragmentos de documentos (para RAG)
CREATE TABLE legal.fragmentos (
    id SERIAL PRIMARY KEY,
    documento_id INTEGER REFERENCES legal.documentos(id) ON DELETE CASCADE,
    seccion VARCHAR(255), -- 'Título I', 'Artículo 11', 'Capítulo 3', etc.
    numero_seccion VARCHAR(50),
    contenido TEXT NOT NULL,
    temas VARCHAR(255)[], -- ['agua', 'aire', 'fauna', 'comunidades_indigenas']
    embedding vector(384), -- Vector de embeddings para búsqueda semántica (paraphrase-multilingual-MiniLM-L12-v2)
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_fragmentos_documento ON legal.fragmentos(documento_id);
CREATE INDEX idx_fragmentos_embedding ON legal.fragmentos USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX idx_fragmentos_temas ON legal.fragmentos USING GIN(temas);

-- ============================================
-- TABLAS DE PROYECTOS
-- ============================================

-- Proyectos mineros a evaluar
CREATE TABLE proyectos.proyectos (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    tipo_mineria VARCHAR(100), -- 'Cielo abierto', 'Subterránea', 'Mixta'
    mineral_principal VARCHAR(100), -- 'Cobre', 'Litio', 'Oro', 'Hierro', etc.
    fase VARCHAR(100), -- 'Exploración', 'Construcción', 'Operación', 'Cierre'
    titular VARCHAR(255),
    region VARCHAR(100),
    comuna VARCHAR(100),
    superficie_ha NUMERIC(12, 2),
    produccion_estimada VARCHAR(255),
    vida_util_anos INTEGER,
    uso_agua_lps NUMERIC(10, 2), -- Litros por segundo
    fuente_agua VARCHAR(255), -- 'Agua de mar', 'Agua superficial', 'Agua subterránea'
    energia_mw NUMERIC(10, 2),
    trabajadores_construccion INTEGER,
    trabajadores_operacion INTEGER,
    inversion_musd NUMERIC(12, 2),
    descripcion TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    geom GEOMETRY(MultiPolygon, 4326) NOT NULL
);

CREATE INDEX idx_proyectos_geom ON proyectos.proyectos USING GIST(geom);
CREATE INDEX idx_proyectos_region ON proyectos.proyectos(region);
CREATE INDEX idx_proyectos_tipo ON proyectos.proyectos(tipo_mineria);

-- Análisis de prefactibilidad
CREATE TABLE proyectos.analisis (
    id SERIAL PRIMARY KEY,
    proyecto_id INTEGER REFERENCES proyectos.proyectos(id) ON DELETE CASCADE,
    fecha_analisis TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Resultados GIS
    resultado_gis JSONB, -- Intersecciones, distancias, alertas espaciales

    -- Clasificación SEIA
    via_ingreso_recomendada VARCHAR(50), -- 'DIA', 'EIA', 'No requiere'
    confianza_clasificacion NUMERIC(3, 2), -- 0.00 a 1.00
    triggers_eia JSONB, -- Lista de triggers del Art. 11 detectados

    -- Normativa aplicable
    normativa_relevante JSONB, -- Referencias a fragmentos legales

    -- Informe generado
    informe_texto TEXT,
    informe_json JSONB,

    -- Metadata
    version_modelo VARCHAR(50),
    tiempo_procesamiento_ms INTEGER,
    metadata JSONB
);

CREATE INDEX idx_analisis_proyecto ON proyectos.analisis(proyecto_id);
CREATE INDEX idx_analisis_fecha ON proyectos.analisis(fecha_analisis);

-- ============================================
-- FUNCIONES ÚTILES
-- ============================================

-- Función para obtener análisis espacial de un proyecto
CREATE OR REPLACE FUNCTION gis.analizar_proyecto(proyecto_geom GEOMETRY)
RETURNS JSONB AS $$
DECLARE
    resultado JSONB;
BEGIN
    SELECT jsonb_build_object(
        'areas_protegidas', (
            SELECT jsonb_agg(jsonb_build_object(
                'id', id,
                'nombre', nombre,
                'tipo', tipo,
                'intersecta', ST_Intersects(geom, proyecto_geom),
                'distancia_m', ST_Distance(geom::geography, proyecto_geom::geography)
            ))
            FROM gis.areas_protegidas
            WHERE ST_DWithin(geom::geography, proyecto_geom::geography, 50000) -- 50km buffer
        ),
        'glaciares', (
            SELECT jsonb_agg(jsonb_build_object(
                'id', id,
                'nombre', nombre,
                'tipo', tipo,
                'intersecta', ST_Intersects(geom, proyecto_geom),
                'distancia_m', ST_Distance(geom::geography, proyecto_geom::geography)
            ))
            FROM gis.glaciares
            WHERE ST_DWithin(geom::geography, proyecto_geom::geography, 20000)
        ),
        'cuerpos_agua', (
            SELECT jsonb_agg(jsonb_build_object(
                'id', id,
                'nombre', nombre,
                'tipo', tipo,
                'intersecta', ST_Intersects(geom, proyecto_geom),
                'distancia_m', ST_Distance(geom::geography, proyecto_geom::geography)
            ))
            FROM gis.cuerpos_agua
            WHERE ST_DWithin(geom::geography, proyecto_geom::geography, 10000)
        ),
        'comunidades_indigenas', (
            SELECT jsonb_agg(jsonb_build_object(
                'id', id,
                'nombre', nombre,
                'pueblo', pueblo,
                'es_adi', es_adi,
                'distancia_m', ST_Distance(geom::geography, proyecto_geom::geography)
            ))
            FROM gis.comunidades_indigenas
            WHERE ST_DWithin(geom::geography, proyecto_geom::geography, 30000)
        ),
        'centros_poblados', (
            SELECT jsonb_agg(jsonb_build_object(
                'id', id,
                'nombre', nombre,
                'tipo', tipo,
                'poblacion', poblacion,
                'distancia_m', ST_Distance(geom::geography, proyecto_geom::geography)
            ))
            FROM gis.centros_poblados
            WHERE ST_DWithin(geom::geography, proyecto_geom::geography, 20000)
        ),
        'sitios_patrimoniales', (
            SELECT jsonb_agg(jsonb_build_object(
                'id', id,
                'nombre', nombre,
                'tipo', tipo,
                'intersecta', ST_Intersects(geom, proyecto_geom),
                'distancia_m', ST_Distance(geom::geography, proyecto_geom::geography)
            ))
            FROM gis.sitios_patrimoniales
            WHERE ST_DWithin(geom::geography, proyecto_geom::geography, 10000)
        ),
        'ubicacion', (
            SELECT jsonb_build_object(
                'region', r.nombre,
                'comuna', c.nombre
            )
            FROM gis.comunas c
            JOIN gis.regiones r ON c.region_codigo = r.codigo
            WHERE ST_Intersects(c.geom, ST_Centroid(proyecto_geom))
            LIMIT 1
        )
    ) INTO resultado;

    RETURN resultado;
END;
$$ LANGUAGE plpgsql;

-- Función para buscar fragmentos por similitud semántica
CREATE OR REPLACE FUNCTION legal.buscar_similares(
    query_embedding vector(384),
    limite INTEGER DEFAULT 10,
    filtro_temas TEXT[] DEFAULT NULL
)
RETURNS TABLE(
    id INTEGER,
    documento_id INTEGER,
    seccion VARCHAR,
    contenido TEXT,
    similitud FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        f.id,
        f.documento_id,
        f.seccion,
        f.contenido,
        1 - (f.embedding <=> query_embedding) as similitud
    FROM legal.fragmentos f
    WHERE (filtro_temas IS NULL OR f.temas && filtro_temas)
    ORDER BY f.embedding <=> query_embedding
    LIMIT limite;
END;
$$ LANGUAGE plpgsql;
