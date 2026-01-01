-- ============================================================================
-- MIGRACIÓN: Sistema de Gestión de Proyectos Mineros
-- Fecha: 2025-12-27
-- Descripción: Agrega clientes, documentos, estados, auditoría
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. TIPO ENUM PARA ESTADOS
-- ----------------------------------------------------------------------------
DO $$ BEGIN
    CREATE TYPE proyectos.estado_proyecto AS ENUM (
        'borrador',
        'completo',
        'con_geometria',
        'analizado',
        'en_revision',
        'aprobado',
        'rechazado',
        'archivado'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE proyectos.categoria_documento AS ENUM (
        'legal',
        'tecnico',
        'ambiental',
        'cartografia',
        'otro'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE proyectos.tipo_analisis AS ENUM (
        'rapido',
        'completo'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- ----------------------------------------------------------------------------
-- 2. TABLA CLIENTES
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS proyectos.clientes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rut VARCHAR(12) UNIQUE,  -- Opcional, formato: 12.345.678-9
    razon_social VARCHAR(200) NOT NULL,
    nombre_fantasia VARCHAR(200),
    email VARCHAR(100),
    telefono VARCHAR(20),
    direccion TEXT,
    notas TEXT,
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_clientes_razon_social
    ON proyectos.clientes(razon_social);
CREATE INDEX IF NOT EXISTS idx_clientes_activo
    ON proyectos.clientes(activo) WHERE activo = TRUE;

COMMENT ON TABLE proyectos.clientes IS 'Empresas o personas titulares de proyectos mineros';
COMMENT ON COLUMN proyectos.clientes.rut IS 'RUT chileno, opcional, formato con puntos y guión';

-- ----------------------------------------------------------------------------
-- 3. MODIFICAR TABLA PROYECTOS
-- ----------------------------------------------------------------------------

-- 3.1 Agregar columna cliente_id
ALTER TABLE proyectos.proyectos
    ADD COLUMN IF NOT EXISTS cliente_id UUID REFERENCES proyectos.clientes(id) ON DELETE SET NULL;

-- 3.2 Agregar columna estado (usar VARCHAR para flexibilidad)
ALTER TABLE proyectos.proyectos
    ADD COLUMN IF NOT EXISTS estado VARCHAR(20) DEFAULT 'borrador';

-- 3.3 Hacer geometría opcional (si aún no lo está)
ALTER TABLE proyectos.proyectos
    ALTER COLUMN geom DROP NOT NULL;

-- 3.4 Agregar campos para triggers SEIA/LLM
ALTER TABLE proyectos.proyectos
    ADD COLUMN IF NOT EXISTS descarga_diaria_ton NUMERIC(12,2),
    ADD COLUMN IF NOT EXISTS emisiones_co2_ton_ano NUMERIC(12,2),
    ADD COLUMN IF NOT EXISTS afecta_glaciares BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS dist_area_protegida_km NUMERIC(8,2),
    ADD COLUMN IF NOT EXISTS dist_comunidad_indigena_km NUMERIC(8,2),
    ADD COLUMN IF NOT EXISTS dist_centro_poblado_km NUMERIC(8,2),
    ADD COLUMN IF NOT EXISTS requiere_reasentamiento BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS afecta_patrimonio BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS porcentaje_completado INTEGER DEFAULT 0;

-- 3.5 Índices adicionales
CREATE INDEX IF NOT EXISTS idx_proyectos_cliente
    ON proyectos.proyectos(cliente_id);
CREATE INDEX IF NOT EXISTS idx_proyectos_estado
    ON proyectos.proyectos(estado);

-- ----------------------------------------------------------------------------
-- 4. TABLA DOCUMENTOS
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS proyectos.documentos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proyecto_id INTEGER NOT NULL REFERENCES proyectos.proyectos(id) ON DELETE CASCADE,
    nombre VARCHAR(255) NOT NULL,
    nombre_original VARCHAR(255) NOT NULL,
    categoria proyectos.categoria_documento NOT NULL DEFAULT 'otro',
    descripcion TEXT,
    archivo_path VARCHAR(500) NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    tamano_bytes BIGINT NOT NULL,
    checksum_sha256 VARCHAR(64),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_documentos_proyecto
    ON proyectos.documentos(proyecto_id);
CREATE INDEX IF NOT EXISTS idx_documentos_categoria
    ON proyectos.documentos(categoria);

COMMENT ON TABLE proyectos.documentos IS 'Documentos adjuntos a proyectos (PDF, imágenes, etc.)';

-- ----------------------------------------------------------------------------
-- 5. MODIFICAR TABLA ANALISIS
-- ----------------------------------------------------------------------------
ALTER TABLE proyectos.analisis
    ADD COLUMN IF NOT EXISTS tipo_analisis VARCHAR(20) DEFAULT 'completo';

-- Índice BRIN para consultas por rango de fechas
CREATE INDEX IF NOT EXISTS idx_analisis_fecha_brin
    ON proyectos.analisis USING BRIN(fecha_analisis);

-- ----------------------------------------------------------------------------
-- 6. TABLA AUDITORÍA DE ANÁLISIS (CUMPLIMIENTO REGULATORIO)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS proyectos.auditoria_analisis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analisis_id INTEGER NOT NULL REFERENCES proyectos.analisis(id) ON DELETE CASCADE,

    -- Trazabilidad GIS
    capas_gis_usadas JSONB NOT NULL DEFAULT '[]',
    -- Ejemplo: [{"nombre": "snaspe", "fecha": "2025-12-01", "version": "v2024.2"}]

    -- Documentos referenciados en el análisis
    documentos_referenciados UUID[] DEFAULT '{}',

    -- Normativa citada por el LLM
    normativa_citada JSONB NOT NULL DEFAULT '[]',
    -- Ejemplo: [{"tipo": "Ley", "numero": "19300", "articulo": "11", "letra": "d"}]

    -- Integridad de datos
    checksum_datos_entrada VARCHAR(64) NOT NULL,  -- SHA256 de proyecto + geometría
    version_modelo_llm VARCHAR(50),               -- claude-sonnet-4-20250514
    version_sistema VARCHAR(20),                  -- v1.0.0

    -- Metadatos de ejecución
    tiempo_gis_ms INTEGER,
    tiempo_rag_ms INTEGER,
    tiempo_llm_ms INTEGER,
    tokens_usados INTEGER,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_auditoria_analisis
    ON proyectos.auditoria_analisis(analisis_id);

COMMENT ON TABLE proyectos.auditoria_analisis IS
    'Registro de auditoría para cumplimiento regulatorio SEIA. Inmutable.';

-- ----------------------------------------------------------------------------
-- 7. TABLA HISTORIAL DE ESTADOS
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS proyectos.historial_estados (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proyecto_id INTEGER NOT NULL REFERENCES proyectos.proyectos(id) ON DELETE CASCADE,
    estado_anterior VARCHAR(20),
    estado_nuevo VARCHAR(20) NOT NULL,
    motivo TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_historial_proyecto
    ON proyectos.historial_estados(proyecto_id);

-- ----------------------------------------------------------------------------
-- 8. TRIGGERS AUTOMÁTICOS
-- ----------------------------------------------------------------------------

-- 8.1 Trigger: Actualizar estado automáticamente al agregar geometría
CREATE OR REPLACE FUNCTION proyectos.fn_update_estado_geometria()
RETURNS TRIGGER AS $$
BEGIN
    -- Si se agrega geometría y estado es 'completo', pasar a 'con_geometria'
    IF NEW.geom IS NOT NULL AND OLD.geom IS NULL THEN
        IF NEW.estado = 'completo' THEN
            NEW.estado := 'con_geometria';
        END IF;
    END IF;

    -- Actualizar timestamp
    NEW.updated_at := NOW();

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_update_estado_geometria ON proyectos.proyectos;
CREATE TRIGGER trg_update_estado_geometria
    BEFORE UPDATE ON proyectos.proyectos
    FOR EACH ROW
    EXECUTE FUNCTION proyectos.fn_update_estado_geometria();

-- 8.2 Trigger: Registrar cambios de estado en historial
CREATE OR REPLACE FUNCTION proyectos.fn_log_cambio_estado()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.estado IS DISTINCT FROM NEW.estado THEN
        INSERT INTO proyectos.historial_estados (proyecto_id, estado_anterior, estado_nuevo)
        VALUES (NEW.id, OLD.estado, NEW.estado);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_log_cambio_estado ON proyectos.proyectos;
CREATE TRIGGER trg_log_cambio_estado
    AFTER UPDATE ON proyectos.proyectos
    FOR EACH ROW
    EXECUTE FUNCTION proyectos.fn_log_cambio_estado();

-- 8.3 Trigger: Actualizar porcentaje completado
CREATE OR REPLACE FUNCTION proyectos.fn_calcular_porcentaje()
RETURNS TRIGGER AS $$
DECLARE
    total_campos INTEGER := 15;
    campos_llenos INTEGER := 0;
BEGIN
    -- Contar campos obligatorios llenos
    IF NEW.nombre IS NOT NULL AND NEW.nombre != '' THEN campos_llenos := campos_llenos + 1; END IF;
    IF NEW.region IS NOT NULL THEN campos_llenos := campos_llenos + 1; END IF;
    IF NEW.comuna IS NOT NULL THEN campos_llenos := campos_llenos + 1; END IF;
    IF NEW.tipo_mineria IS NOT NULL THEN campos_llenos := campos_llenos + 1; END IF;
    IF NEW.mineral_principal IS NOT NULL THEN campos_llenos := campos_llenos + 1; END IF;
    IF NEW.fase IS NOT NULL THEN campos_llenos := campos_llenos + 1; END IF;
    IF NEW.superficie_ha IS NOT NULL THEN campos_llenos := campos_llenos + 1; END IF;
    IF NEW.vida_util_anos IS NOT NULL THEN campos_llenos := campos_llenos + 1; END IF;
    IF NEW.uso_agua_lps IS NOT NULL THEN campos_llenos := campos_llenos + 1; END IF;
    IF NEW.fuente_agua IS NOT NULL THEN campos_llenos := campos_llenos + 1; END IF;
    IF NEW.energia_mw IS NOT NULL THEN campos_llenos := campos_llenos + 1; END IF;
    IF NEW.trabajadores_construccion IS NOT NULL THEN campos_llenos := campos_llenos + 1; END IF;
    IF NEW.trabajadores_operacion IS NOT NULL THEN campos_llenos := campos_llenos + 1; END IF;
    IF NEW.inversion_musd IS NOT NULL THEN campos_llenos := campos_llenos + 1; END IF;
    IF NEW.geom IS NOT NULL THEN campos_llenos := campos_llenos + 1; END IF;

    NEW.porcentaje_completado := (campos_llenos * 100) / total_campos;

    -- Cambiar estado a 'completo' si todos los campos requeridos (menos geom) están llenos
    IF NEW.porcentaje_completado >= 93 AND NEW.geom IS NULL AND NEW.estado = 'borrador' THEN
        NEW.estado := 'completo';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_calcular_porcentaje ON proyectos.proyectos;
CREATE TRIGGER trg_calcular_porcentaje
    BEFORE INSERT OR UPDATE ON proyectos.proyectos
    FOR EACH ROW
    EXECUTE FUNCTION proyectos.fn_calcular_porcentaje();

-- 8.4 Trigger: Actualizar updated_at en clientes
CREATE OR REPLACE FUNCTION proyectos.fn_update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at := NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_clientes_updated ON proyectos.clientes;
CREATE TRIGGER trg_clientes_updated
    BEFORE UPDATE ON proyectos.clientes
    FOR EACH ROW
    EXECUTE FUNCTION proyectos.fn_update_timestamp();

-- ----------------------------------------------------------------------------
-- 9. FUNCIÓN: Pre-calcular distancias GIS al guardar geometría
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION proyectos.fn_precalcular_distancias()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.geom IS NOT NULL AND (OLD.geom IS NULL OR NOT ST_Equals(OLD.geom, NEW.geom)) THEN
        -- Distancia a área protegida más cercana
        SELECT MIN(ST_Distance(NEW.geom::geography, ap.geom::geography)) / 1000.0
        INTO NEW.dist_area_protegida_km
        FROM gis.areas_protegidas ap;

        -- Distancia a comunidad indígena más cercana
        SELECT MIN(ST_Distance(NEW.geom::geography, ci.geom::geography)) / 1000.0
        INTO NEW.dist_comunidad_indigena_km
        FROM gis.comunidades_indigenas ci;

        -- Distancia a centro poblado más cercano
        SELECT MIN(ST_Distance(NEW.geom::geography, cp.geom::geography)) / 1000.0
        INTO NEW.dist_centro_poblado_km
        FROM gis.centros_poblados cp;

        -- Verificar si afecta glaciares (intersección)
        SELECT EXISTS(
            SELECT 1 FROM gis.glaciares g
            WHERE ST_Intersects(NEW.geom, g.geom)
            OR ST_DWithin(NEW.geom::geography, g.geom::geography, 5000)  -- 5km buffer
        ) INTO NEW.afecta_glaciares;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_precalcular_distancias ON proyectos.proyectos;
CREATE TRIGGER trg_precalcular_distancias
    BEFORE INSERT OR UPDATE OF geom ON proyectos.proyectos
    FOR EACH ROW
    EXECUTE FUNCTION proyectos.fn_precalcular_distancias();

-- ----------------------------------------------------------------------------
-- 10. VISTAS ÚTILES
-- ----------------------------------------------------------------------------

-- Vista: Proyectos con info de cliente
CREATE OR REPLACE VIEW proyectos.v_proyectos_completos AS
SELECT
    p.*,
    c.razon_social AS cliente_razon_social,
    c.nombre_fantasia AS cliente_nombre_fantasia,
    c.email AS cliente_email,
    (SELECT COUNT(*) FROM proyectos.documentos d WHERE d.proyecto_id = p.id) AS total_documentos,
    (SELECT COUNT(*) FROM proyectos.analisis a WHERE a.proyecto_id = p.id) AS total_analisis,
    (SELECT MAX(fecha_analisis) FROM proyectos.analisis a WHERE a.proyecto_id = p.id) AS ultimo_analisis
FROM proyectos.proyectos p
LEFT JOIN proyectos.clientes c ON p.cliente_id = c.id;

-- Vista: Dashboard estadísticas
CREATE OR REPLACE VIEW proyectos.v_dashboard_stats AS
SELECT
    (SELECT COUNT(*) FROM proyectos.clientes WHERE activo = TRUE) AS total_clientes,
    (SELECT COUNT(*) FROM proyectos.proyectos WHERE estado != 'archivado') AS total_proyectos,
    (SELECT COUNT(*) FROM proyectos.proyectos WHERE estado = 'borrador') AS proyectos_borrador,
    (SELECT COUNT(*) FROM proyectos.proyectos WHERE estado = 'analizado') AS proyectos_analizados,
    (SELECT COUNT(*) FROM proyectos.analisis WHERE fecha_analisis > NOW() - INTERVAL '7 days') AS analisis_semana,
    (SELECT COUNT(*) FROM proyectos.analisis WHERE via_ingreso_recomendada = 'EIA') AS total_eia,
    (SELECT COUNT(*) FROM proyectos.analisis WHERE via_ingreso_recomendada = 'DIA') AS total_dia;

-- ----------------------------------------------------------------------------
-- 11. DATOS DE EJEMPLO (DESARROLLO)
-- ----------------------------------------------------------------------------

-- Cliente de ejemplo
INSERT INTO proyectos.clientes (id, rut, razon_social, nombre_fantasia, email, telefono)
VALUES (
    'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',
    '76.543.210-K',
    'Minera Andes del Norte SpA',
    'Minera Andes',
    'contacto@mineraandes.cl',
    '+56 2 2345 6789'
) ON CONFLICT (id) DO NOTHING;

-- Actualizar proyectos existentes para que tengan estado por defecto
UPDATE proyectos.proyectos SET estado = 'con_geometria' WHERE estado IS NULL AND geom IS NOT NULL;
UPDATE proyectos.proyectos SET estado = 'borrador' WHERE estado IS NULL;

COMMIT;
