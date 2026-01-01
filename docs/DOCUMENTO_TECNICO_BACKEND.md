# Documento Técnico: Backend - Sistema de Gestión de Proyectos Mineros

**Versión:** 1.0
**Fecha:** 2025-12-27
**Stack:** Python 3.11+ / FastAPI / PostgreSQL 15 + PostGIS 3.4 + pgvector
**Audiencia:** Desarrolladores Backend Senior

---

## 1. Resumen Ejecutivo

### Objetivo
Implementar un sistema de gestión de proyectos mineros con persistencia en PostgreSQL, reemplazando el almacenamiento actual en localStorage. El sistema debe soportar:

- CRUD de Clientes y Proyectos
- Gestión de documentos categorizados
- Análisis de prefactibilidad ambiental (GIS + LLM)
- Auditoría regulatoria para cumplimiento SEIA

### Arquitectura Actual vs. Nueva

| Aspecto | Antes | Después |
|---------|-------|---------|
| Persistencia | localStorage (frontend) | PostgreSQL |
| Geometría | Obligatoria | Opcional (progresiva) |
| Clientes | No existe | Entidad completa |
| Documentos | No existe | Con categorías + storage |
| Auditoría | No existe | Trazabilidad completa |
| Estados | Implícitos | Workflow explícito |

---

## 2. Modelo de Datos

### 2.1 Diagrama Entidad-Relación

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│    CLIENTE      │       │    PROYECTO     │       │    ANALISIS     │
├─────────────────┤       ├─────────────────┤       ├─────────────────┤
│ id (UUID PK)    │──1:N──│ id (UUID PK)    │──1:N──│ id (UUID PK)    │
│ rut (opcional)  │       │ cliente_id (FK) │       │ proyecto_id(FK) │
│ razon_social    │       │ nombre          │       │ tipo_analisis   │
│ nombre_fantasia │       │ estado          │       │ fecha           │
│ email           │       │ region/comuna   │       │ resultado_gis   │
│ telefono        │       │ datos_mineria   │       │ clasificacion   │
│ direccion       │       │ datos_calculados│       │ triggers        │
│ created_at      │       │ geom (opcional) │       │ informe_llm     │
│ updated_at      │       │ created/updated │       │ created_at      │
└─────────────────┘       └────────┬────────┘       └────────┬────────┘
                                   │                         │
                          ┌────────┴────────┐       ┌────────┴────────┐
                          │                 │       │                 │
                          ▼                 │       ▼                 │
                 ┌─────────────────┐        │  ┌─────────────────┐    │
                 │   DOCUMENTO     │        │  │    AUDITORIA    │    │
                 ├─────────────────┤        │  │    ANALISIS     │    │
                 │ id (UUID PK)    │        │  ├─────────────────┤    │
                 │ proyecto_id(FK) │        │  │ id (UUID PK)    │◄───┘
                 │ nombre          │        │  │ analisis_id(FK) │
                 │ categoria       │        │  │ capas_gis_usadas│
                 │ archivo_path    │        │  │ fechas_capas    │
                 │ mime_type       │        │  │ docs_referencia │
                 │ tamano_bytes    │        │  │ normativa_citada│
                 │ descripcion     │        │  │ checksum_datos  │
                 │ created_at      │        │  │ created_at      │
                 └─────────────────┘        │  └─────────────────┘
                                            │
                                            ▼
                                   ┌─────────────────┐
                                   │  HISTORIAL      │
                                   │  ESTADO         │
                                   ├─────────────────┤
                                   │ id (UUID PK)    │
                                   │ proyecto_id(FK) │
                                   │ estado_anterior │
                                   │ estado_nuevo    │
                                   │ motivo          │
                                   │ created_at      │
                                   └─────────────────┘
```

### 2.2 Estados del Proyecto (Workflow SEIA)

```
borrador ──► completo ──► con_geometria ──► analizado ──► en_revision ──► aprobado
    │            │              │               │              │              │
    │            │              │               │              │              ▼
    │            │              │               │              │         archivado
    │            │              │               │              │              ▲
    │            │              │               │              └──► rechazado─┘
    │            │              │               │
    └────────────┴──────────────┴───────────────┴──────────────────► archivado
```

| Estado | Descripción | Transiciones Válidas |
|--------|-------------|----------------------|
| `borrador` | Ficha recién creada, datos incompletos | → completo, archivado |
| `completo` | Datos obligatorios llenos | → con_geometria, archivado |
| `con_geometria` | Polígono dibujado | → analizado, archivado |
| `analizado` | Al menos un análisis ejecutado | → en_revision, archivado |
| `en_revision` | Revisión por especialista | → aprobado, rechazado |
| `aprobado` | Listo para ingreso SEIA | → archivado |
| `rechazado` | Requiere correcciones | → en_revision, archivado |
| `archivado` | Inactivo/histórico | (terminal) |

---

## 3. Scripts SQL de Migración

### 3.1 Crear archivo: `docker/postgis/init/03_clientes_documentos.sql`

```sql
-- ============================================================================
-- MIGRACIÓN: Sistema de Gestión de Proyectos Mineros
-- Fecha: 2025-12-27
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

-- 3.2 Agregar columna estado (usar VARCHAR temporalmente, luego migrar a ENUM)
ALTER TABLE proyectos.proyectos
    ADD COLUMN IF NOT EXISTS estado VARCHAR(20) DEFAULT 'borrador';

-- 3.3 Hacer geometría opcional
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

-- 3.5 Índices
CREATE INDEX IF NOT EXISTS idx_proyectos_cliente
    ON proyectos.proyectos(cliente_id);
CREATE INDEX IF NOT EXISTS idx_proyectos_estado
    ON proyectos.proyectos(estado);
CREATE INDEX IF NOT EXISTS idx_proyectos_region
    ON proyectos.proyectos(region);
CREATE INDEX IF NOT EXISTS idx_proyectos_geom
    ON proyectos.proyectos USING GIST(geom);

-- ----------------------------------------------------------------------------
-- 4. TABLA DOCUMENTOS
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS proyectos.documentos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proyecto_id UUID NOT NULL REFERENCES proyectos.proyectos(id) ON DELETE CASCADE,
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

-- Índice BRIN para consultas por rango de fechas (muy eficiente para series temporales)
CREATE INDEX IF NOT EXISTS idx_analisis_fecha_brin
    ON proyectos.analisis USING BRIN(fecha_analisis);

-- ----------------------------------------------------------------------------
-- 6. TABLA AUDITORÍA DE ANÁLISIS (CUMPLIMIENTO REGULATORIO)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS proyectos.auditoria_analisis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analisis_id UUID NOT NULL REFERENCES proyectos.analisis(id) ON DELETE CASCADE,

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
    proyecto_id UUID NOT NULL REFERENCES proyectos.proyectos(id) ON DELETE CASCADE,
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

COMMIT;
```

---

## 4. Modelos SQLAlchemy

### 4.1 Crear archivo: `backend/app/db/models/cliente.py`

```python
"""
Modelo SQLAlchemy para Cliente.
"""
from uuid import uuid4
from datetime import datetime
from sqlalchemy import Column, String, Text, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.session import Base


class Cliente(Base):
    """Empresa o persona titular de proyectos mineros."""

    __tablename__ = "clientes"
    __table_args__ = {"schema": "proyectos"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    rut = Column(String(12), unique=True, nullable=True, index=True)
    razon_social = Column(String(200), nullable=False, index=True)
    nombre_fantasia = Column(String(200), nullable=True)
    email = Column(String(100), nullable=True)
    telefono = Column(String(20), nullable=True)
    direccion = Column(Text, nullable=True)
    notas = Column(Text, nullable=True)
    activo = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.utcnow)

    # Relaciones
    proyectos = relationship(
        "Proyecto",
        back_populates="cliente",
        lazy="dynamic",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Cliente {self.razon_social}>"

    @property
    def cantidad_proyectos(self) -> int:
        """Retorna cantidad de proyectos del cliente."""
        return self.proyectos.count()
```

### 4.2 Crear archivo: `backend/app/db/models/documento.py`

```python
"""
Modelo SQLAlchemy para Documento.
"""
from uuid import uuid4
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, Text, BigInteger, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.orm import relationship

from app.db.session import Base


class CategoriaDocumento(str, Enum):
    """Categorías de documentos."""
    LEGAL = "legal"
    TECNICO = "tecnico"
    AMBIENTAL = "ambiental"
    CARTOGRAFIA = "cartografia"
    OTRO = "otro"


class Documento(Base):
    """Documento adjunto a un proyecto."""

    __tablename__ = "documentos"
    __table_args__ = {"schema": "proyectos"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    proyecto_id = Column(
        UUID(as_uuid=True),
        ForeignKey("proyectos.proyectos.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    nombre = Column(String(255), nullable=False)
    nombre_original = Column(String(255), nullable=False)
    categoria = Column(
        ENUM(CategoriaDocumento, name="categoria_documento", schema="proyectos"),
        nullable=False,
        default=CategoriaDocumento.OTRO,
        index=True
    )
    descripcion = Column(Text, nullable=True)
    archivo_path = Column(String(500), nullable=False)
    mime_type = Column(String(100), nullable=False)
    tamano_bytes = Column(BigInteger, nullable=False)
    checksum_sha256 = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relaciones
    proyecto = relationship("Proyecto", back_populates="documentos")

    def __repr__(self):
        return f"<Documento {self.nombre}>"

    @property
    def tamano_mb(self) -> float:
        """Retorna tamaño en MB."""
        return round(self.tamano_bytes / (1024 * 1024), 2)
```

### 4.3 Crear archivo: `backend/app/db/models/auditoria.py`

```python
"""
Modelo SQLAlchemy para Auditoría de Análisis.
"""
from uuid import uuid4
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship

from app.db.session import Base


class AuditoriaAnalisis(Base):
    """Registro de auditoría para cumplimiento regulatorio SEIA."""

    __tablename__ = "auditoria_analisis"
    __table_args__ = {"schema": "proyectos"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    analisis_id = Column(
        UUID(as_uuid=True),
        ForeignKey("proyectos.analisis.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Trazabilidad GIS
    capas_gis_usadas = Column(JSONB, nullable=False, default=list)
    # Ejemplo: [{"nombre": "snaspe", "fecha": "2025-12-01", "version": "v2024.2"}]

    # Documentos referenciados
    documentos_referenciados = Column(ARRAY(UUID(as_uuid=True)), default=list)

    # Normativa citada
    normativa_citada = Column(JSONB, nullable=False, default=list)
    # Ejemplo: [{"tipo": "Ley", "numero": "19300", "articulo": "11", "letra": "d"}]

    # Integridad
    checksum_datos_entrada = Column(String(64), nullable=False)
    version_modelo_llm = Column(String(50), nullable=True)
    version_sistema = Column(String(20), nullable=True)

    # Métricas de ejecución
    tiempo_gis_ms = Column(Integer, nullable=True)
    tiempo_rag_ms = Column(Integer, nullable=True)
    tiempo_llm_ms = Column(Integer, nullable=True)
    tokens_usados = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relaciones
    analisis = relationship("Analisis", back_populates="auditoria")

    def __repr__(self):
        return f"<AuditoriaAnalisis {self.id}>"
```

### 4.4 Modificar archivo: `backend/app/db/models/proyecto.py`

```python
"""
Modelo SQLAlchemy para Proyecto (MODIFICADO).
Agregar campos: cliente_id, estado, campos SEIA, campos pre-calculados.
"""
from uuid import uuid4
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, Text, Numeric, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry

from app.db.session import Base


class EstadoProyecto(str, Enum):
    """Estados del proyecto en workflow SEIA."""
    BORRADOR = "borrador"
    COMPLETO = "completo"
    CON_GEOMETRIA = "con_geometria"
    ANALIZADO = "analizado"
    EN_REVISION = "en_revision"
    APROBADO = "aprobado"
    RECHAZADO = "rechazado"
    ARCHIVADO = "archivado"


class Proyecto(Base):
    """Proyecto minero."""

    __tablename__ = "proyectos"
    __table_args__ = {"schema": "proyectos"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Relación con cliente (NUEVO)
    cliente_id = Column(
        UUID(as_uuid=True),
        ForeignKey("proyectos.clientes.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # Estado del proyecto (NUEVO)
    estado = Column(String(20), default="borrador", index=True)
    porcentaje_completado = Column(Integer, default=0)

    # Datos básicos
    nombre = Column(String(200), nullable=False)
    tipo_mineria = Column(String(50), nullable=True)
    mineral_principal = Column(String(100), nullable=True)
    fase = Column(String(50), nullable=True)
    titular = Column(String(200), nullable=True)  # Mantener por compatibilidad
    region = Column(String(100), nullable=True, index=True)
    comuna = Column(String(100), nullable=True)

    # Características técnicas
    superficie_ha = Column(Numeric(12, 2), nullable=True)
    produccion_estimada = Column(String(100), nullable=True)
    vida_util_anos = Column(Integer, nullable=True)

    # Recursos
    uso_agua_lps = Column(Numeric(10, 2), nullable=True)
    fuente_agua = Column(String(50), nullable=True)
    energia_mw = Column(Numeric(10, 2), nullable=True)

    # Empleo e inversión
    trabajadores_construccion = Column(Integer, nullable=True)
    trabajadores_operacion = Column(Integer, nullable=True)
    inversion_musd = Column(Numeric(12, 2), nullable=True)

    # Descripción
    descripcion = Column(Text, nullable=True)

    # Campos SEIA adicionales (NUEVO)
    descarga_diaria_ton = Column(Numeric(12, 2), nullable=True)
    emisiones_co2_ton_ano = Column(Numeric(12, 2), nullable=True)
    requiere_reasentamiento = Column(Boolean, default=False)
    afecta_patrimonio = Column(Boolean, default=False)

    # Campos pre-calculados GIS (NUEVO - actualizados por trigger)
    afecta_glaciares = Column(Boolean, default=False)
    dist_area_protegida_km = Column(Numeric(8, 2), nullable=True)
    dist_comunidad_indigena_km = Column(Numeric(8, 2), nullable=True)
    dist_centro_poblado_km = Column(Numeric(8, 2), nullable=True)

    # Metadatos
    metadata = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.utcnow)

    # Geometría (AHORA OPCIONAL)
    geom = Column(
        Geometry("MULTIPOLYGON", srid=4326),
        nullable=True  # <-- CAMBIO IMPORTANTE
    )

    # Relaciones
    cliente = relationship("Cliente", back_populates="proyectos")
    analisis = relationship(
        "Analisis",
        back_populates="proyecto",
        lazy="dynamic",
        cascade="all, delete-orphan"
    )
    documentos = relationship(
        "Documento",
        back_populates="proyecto",
        lazy="dynamic",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Proyecto {self.nombre}>"

    @property
    def tiene_geometria(self) -> bool:
        return self.geom is not None

    @property
    def puede_analizar(self) -> bool:
        """Verifica si el proyecto puede ser analizado."""
        return self.tiene_geometria and self.estado not in ['archivado']
```

### 4.5 Actualizar archivo: `backend/app/db/models/__init__.py`

```python
"""
Exportación de modelos SQLAlchemy.
"""
from app.db.models.gis import (
    AreaProtegida,
    Glaciar,
    CuerpoAgua,
    ComunidadIndigena,
    CentroPoblado,
)
from app.db.models.legal import Documento as DocumentoLegal, Fragmento
from app.db.models.proyecto import Proyecto, EstadoProyecto
from app.db.models.analisis import Analisis
from app.db.models.cliente import Cliente
from app.db.models.documento import Documento, CategoriaDocumento
from app.db.models.auditoria import AuditoriaAnalisis

__all__ = [
    # GIS
    "AreaProtegida",
    "Glaciar",
    "CuerpoAgua",
    "ComunidadIndigena",
    "CentroPoblado",
    # Legal
    "DocumentoLegal",
    "Fragmento",
    # Proyectos
    "Cliente",
    "Proyecto",
    "EstadoProyecto",
    "Analisis",
    "Documento",
    "CategoriaDocumento",
    "AuditoriaAnalisis",
]
```

---

## 5. Schemas Pydantic

### 5.1 Crear archivo: `backend/app/schemas/cliente.py`

```python
"""
Schemas Pydantic para Cliente.
"""
from uuid import UUID
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, field_validator
import re


class ClienteBase(BaseModel):
    """Campos base del cliente."""
    rut: Optional[str] = Field(None, max_length=12, description="RUT chileno (ej: 12.345.678-9)")
    razon_social: str = Field(..., min_length=2, max_length=200)
    nombre_fantasia: Optional[str] = Field(None, max_length=200)
    email: Optional[EmailStr] = None
    telefono: Optional[str] = Field(None, max_length=20)
    direccion: Optional[str] = None
    notas: Optional[str] = None

    @field_validator('rut')
    @classmethod
    def validar_rut(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        # Validar formato básico: XX.XXX.XXX-X o XXXXXXXX-X
        pattern = r'^(\d{1,2}\.?\d{3}\.?\d{3}-[\dkK])$'
        if not re.match(pattern, v.replace('.', '').replace('-', '') + '-' + v[-1] if '-' in v else v):
            # Simplificar: solo verificar que tenga estructura razonable
            clean = v.replace('.', '').replace('-', '')
            if not (7 <= len(clean) <= 9):
                raise ValueError('RUT inválido')
        return v.upper()


class ClienteCreate(ClienteBase):
    """Schema para crear cliente."""
    pass


class ClienteUpdate(BaseModel):
    """Schema para actualizar cliente (todos opcionales)."""
    rut: Optional[str] = None
    razon_social: Optional[str] = Field(None, min_length=2, max_length=200)
    nombre_fantasia: Optional[str] = None
    email: Optional[EmailStr] = None
    telefono: Optional[str] = None
    direccion: Optional[str] = None
    notas: Optional[str] = None
    activo: Optional[bool] = None


class ClienteResponse(ClienteBase):
    """Schema de respuesta del cliente."""
    id: UUID
    activo: bool
    created_at: datetime
    updated_at: Optional[datetime]
    cantidad_proyectos: int = 0

    class Config:
        from_attributes = True


class ClienteListResponse(BaseModel):
    """Lista paginada de clientes."""
    items: List[ClienteResponse]
    total: int
    page: int
    page_size: int
    pages: int
```

### 5.2 Crear archivo: `backend/app/schemas/documento.py`

```python
"""
Schemas Pydantic para Documento.
"""
from uuid import UUID
from datetime import datetime
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field


class CategoriaDocumento(str, Enum):
    """Categorías de documentos."""
    LEGAL = "legal"
    TECNICO = "tecnico"
    AMBIENTAL = "ambiental"
    CARTOGRAFIA = "cartografia"
    OTRO = "otro"


class DocumentoBase(BaseModel):
    """Campos base del documento."""
    nombre: str = Field(..., min_length=1, max_length=255)
    categoria: CategoriaDocumento = CategoriaDocumento.OTRO
    descripcion: Optional[str] = None


class DocumentoCreate(DocumentoBase):
    """Schema para crear documento (el archivo se envía como form-data)."""
    pass


class DocumentoResponse(DocumentoBase):
    """Schema de respuesta del documento."""
    id: UUID
    proyecto_id: UUID
    nombre_original: str
    archivo_path: str
    mime_type: str
    tamano_bytes: int
    tamano_mb: float
    checksum_sha256: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentoListResponse(BaseModel):
    """Lista de documentos."""
    items: List[DocumentoResponse]
    total: int
    total_bytes: int
    total_mb: float
```

### 5.3 Crear archivo: `backend/app/schemas/proyecto.py`

```python
"""
Schemas Pydantic para Proyecto (ACTUALIZADO).
"""
from uuid import UUID
from datetime import datetime
from typing import Optional, List, Any, Dict
from enum import Enum
from pydantic import BaseModel, Field


class EstadoProyecto(str, Enum):
    """Estados del proyecto."""
    BORRADOR = "borrador"
    COMPLETO = "completo"
    CON_GEOMETRIA = "con_geometria"
    ANALIZADO = "analizado"
    EN_REVISION = "en_revision"
    APROBADO = "aprobado"
    RECHAZADO = "rechazado"
    ARCHIVADO = "archivado"


class GeometriaGeoJSON(BaseModel):
    """Geometría en formato GeoJSON."""
    type: str = Field(..., pattern="^(Polygon|MultiPolygon)$")
    coordinates: Any


class ProyectoBase(BaseModel):
    """Campos base del proyecto."""
    nombre: str = Field(..., min_length=2, max_length=200)
    cliente_id: Optional[UUID] = None
    tipo_mineria: Optional[str] = None
    mineral_principal: Optional[str] = None
    fase: Optional[str] = None
    titular: Optional[str] = None
    region: Optional[str] = None
    comuna: Optional[str] = None
    superficie_ha: Optional[float] = Field(None, ge=0)
    produccion_estimada: Optional[str] = None
    vida_util_anos: Optional[int] = Field(None, ge=0)
    uso_agua_lps: Optional[float] = Field(None, ge=0)
    fuente_agua: Optional[str] = None
    energia_mw: Optional[float] = Field(None, ge=0)
    trabajadores_construccion: Optional[int] = Field(None, ge=0)
    trabajadores_operacion: Optional[int] = Field(None, ge=0)
    inversion_musd: Optional[float] = Field(None, ge=0)
    descripcion: Optional[str] = None
    # Campos SEIA adicionales
    descarga_diaria_ton: Optional[float] = Field(None, ge=0)
    emisiones_co2_ton_ano: Optional[float] = Field(None, ge=0)
    requiere_reasentamiento: bool = False
    afecta_patrimonio: bool = False


class ProyectoCreate(ProyectoBase):
    """Schema para crear proyecto."""
    geometria: Optional[GeometriaGeoJSON] = None


class ProyectoUpdate(BaseModel):
    """Schema para actualizar proyecto (todos opcionales)."""
    nombre: Optional[str] = Field(None, min_length=2, max_length=200)
    cliente_id: Optional[UUID] = None
    tipo_mineria: Optional[str] = None
    mineral_principal: Optional[str] = None
    fase: Optional[str] = None
    titular: Optional[str] = None
    region: Optional[str] = None
    comuna: Optional[str] = None
    superficie_ha: Optional[float] = None
    produccion_estimada: Optional[str] = None
    vida_util_anos: Optional[int] = None
    uso_agua_lps: Optional[float] = None
    fuente_agua: Optional[str] = None
    energia_mw: Optional[float] = None
    trabajadores_construccion: Optional[int] = None
    trabajadores_operacion: Optional[int] = None
    inversion_musd: Optional[float] = None
    descripcion: Optional[str] = None
    descarga_diaria_ton: Optional[float] = None
    emisiones_co2_ton_ano: Optional[float] = None
    requiere_reasentamiento: Optional[bool] = None
    afecta_patrimonio: Optional[bool] = None


class ProyectoGeometriaUpdate(BaseModel):
    """Schema para actualizar solo geometría."""
    geometria: GeometriaGeoJSON


class CamposPreCalculados(BaseModel):
    """Campos GIS pre-calculados."""
    afecta_glaciares: bool = False
    dist_area_protegida_km: Optional[float] = None
    dist_comunidad_indigena_km: Optional[float] = None
    dist_centro_poblado_km: Optional[float] = None


class ProyectoResponse(ProyectoBase):
    """Schema de respuesta del proyecto."""
    id: UUID
    estado: EstadoProyecto
    porcentaje_completado: int
    tiene_geometria: bool
    puede_analizar: bool
    # Campos pre-calculados
    afecta_glaciares: bool
    dist_area_protegida_km: Optional[float]
    dist_comunidad_indigena_km: Optional[float]
    dist_centro_poblado_km: Optional[float]
    # Info cliente
    cliente_razon_social: Optional[str] = None
    # Contadores
    total_documentos: int = 0
    total_analisis: int = 0
    ultimo_analisis: Optional[datetime] = None
    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class ProyectoConGeometriaResponse(ProyectoResponse):
    """Respuesta con geometría incluida."""
    geometria: Optional[GeometriaGeoJSON] = None


class ProyectoListResponse(BaseModel):
    """Lista paginada de proyectos."""
    items: List[ProyectoResponse]
    total: int
    page: int
    page_size: int
    pages: int


class FiltrosProyecto(BaseModel):
    """Filtros para listar proyectos."""
    cliente_id: Optional[UUID] = None
    estado: Optional[EstadoProyecto] = None
    region: Optional[str] = None
    busqueda: Optional[str] = None  # Busca en nombre
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
```

---

## 6. Endpoints API

### 6.1 Crear archivo: `backend/app/api/v1/endpoints/clientes.py`

```python
"""
Endpoints CRUD para Clientes.
"""
from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.session import get_db
from app.db.models import Cliente, Proyecto
from app.schemas.cliente import (
    ClienteCreate,
    ClienteUpdate,
    ClienteResponse,
    ClienteListResponse,
)

router = APIRouter(prefix="/clientes", tags=["Clientes"])


@router.get("", response_model=ClienteListResponse)
async def listar_clientes(
    busqueda: Optional[str] = Query(None, description="Buscar por razón social"),
    activo: Optional[bool] = Query(None, description="Filtrar por estado activo"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Listar clientes con paginación y filtros."""
    query = select(Cliente)

    # Filtros
    if busqueda:
        query = query.where(Cliente.razon_social.ilike(f"%{busqueda}%"))
    if activo is not None:
        query = query.where(Cliente.activo == activo)

    # Contar total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Paginación
    query = query.order_by(Cliente.razon_social)
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    clientes = result.scalars().all()

    # Agregar cantidad de proyectos
    items = []
    for cliente in clientes:
        count = await db.execute(
            select(func.count()).where(Proyecto.cliente_id == cliente.id)
        )
        cliente_dict = {
            **cliente.__dict__,
            "cantidad_proyectos": count.scalar() or 0
        }
        items.append(ClienteResponse.model_validate(cliente_dict))

    return ClienteListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.post("", response_model=ClienteResponse, status_code=201)
async def crear_cliente(
    data: ClienteCreate,
    db: AsyncSession = Depends(get_db),
):
    """Crear nuevo cliente."""
    # Verificar RUT único si se proporciona
    if data.rut:
        existe = await db.execute(
            select(Cliente).where(Cliente.rut == data.rut)
        )
        if existe.scalar():
            raise HTTPException(400, f"Ya existe un cliente con RUT {data.rut}")

    cliente = Cliente(**data.model_dump())
    db.add(cliente)
    await db.commit()
    await db.refresh(cliente)

    return ClienteResponse.model_validate({**cliente.__dict__, "cantidad_proyectos": 0})


@router.get("/{cliente_id}", response_model=ClienteResponse)
async def obtener_cliente(
    cliente_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Obtener cliente por ID."""
    result = await db.execute(select(Cliente).where(Cliente.id == cliente_id))
    cliente = result.scalar()

    if not cliente:
        raise HTTPException(404, "Cliente no encontrado")

    count = await db.execute(
        select(func.count()).where(Proyecto.cliente_id == cliente.id)
    )

    return ClienteResponse.model_validate({
        **cliente.__dict__,
        "cantidad_proyectos": count.scalar() or 0
    })


@router.put("/{cliente_id}", response_model=ClienteResponse)
async def actualizar_cliente(
    cliente_id: UUID,
    data: ClienteUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Actualizar cliente."""
    result = await db.execute(select(Cliente).where(Cliente.id == cliente_id))
    cliente = result.scalar()

    if not cliente:
        raise HTTPException(404, "Cliente no encontrado")

    # Verificar RUT único si se cambia
    if data.rut and data.rut != cliente.rut:
        existe = await db.execute(
            select(Cliente).where(Cliente.rut == data.rut, Cliente.id != cliente_id)
        )
        if existe.scalar():
            raise HTTPException(400, f"Ya existe un cliente con RUT {data.rut}")

    # Actualizar campos
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(cliente, key, value)

    await db.commit()
    await db.refresh(cliente)

    count = await db.execute(
        select(func.count()).where(Proyecto.cliente_id == cliente.id)
    )

    return ClienteResponse.model_validate({
        **cliente.__dict__,
        "cantidad_proyectos": count.scalar() or 0
    })


@router.delete("/{cliente_id}", status_code=204)
async def eliminar_cliente(
    cliente_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Eliminar cliente (soft delete: marca como inactivo)."""
    result = await db.execute(select(Cliente).where(Cliente.id == cliente_id))
    cliente = result.scalar()

    if not cliente:
        raise HTTPException(404, "Cliente no encontrado")

    # Verificar si tiene proyectos activos
    proyectos = await db.execute(
        select(func.count()).where(
            Proyecto.cliente_id == cliente_id,
            Proyecto.estado != "archivado"
        )
    )
    if proyectos.scalar() > 0:
        raise HTTPException(
            400,
            "No se puede eliminar cliente con proyectos activos. Archive los proyectos primero."
        )

    cliente.activo = False
    await db.commit()


@router.get("/{cliente_id}/proyectos")
async def listar_proyectos_cliente(
    cliente_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Listar proyectos de un cliente."""
    from app.schemas.proyecto import ProyectoResponse

    result = await db.execute(select(Cliente).where(Cliente.id == cliente_id))
    if not result.scalar():
        raise HTTPException(404, "Cliente no encontrado")

    proyectos = await db.execute(
        select(Proyecto)
        .where(Proyecto.cliente_id == cliente_id)
        .order_by(Proyecto.updated_at.desc())
    )

    return [ProyectoResponse.model_validate(p) for p in proyectos.scalars().all()]
```

### 6.2 Crear archivo: `backend/app/api/v1/endpoints/proyectos.py`

```python
"""
Endpoints CRUD para Proyectos.
"""
from uuid import UUID
from typing import Optional
import hashlib
import json
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from geoalchemy2.shape import from_shape, to_shape
from shapely.geometry import shape, mapping

from app.db.session import get_db
from app.db.models import Proyecto, Cliente, Documento, Analisis
from app.schemas.proyecto import (
    ProyectoCreate,
    ProyectoUpdate,
    ProyectoGeometriaUpdate,
    ProyectoResponse,
    ProyectoConGeometriaResponse,
    ProyectoListResponse,
    FiltrosProyecto,
    EstadoProyecto,
)

router = APIRouter(prefix="/proyectos", tags=["Proyectos"])


def proyecto_to_response(proyecto: Proyecto, cliente: Optional[Cliente] = None) -> dict:
    """Convierte modelo a diccionario para respuesta."""
    data = proyecto.__dict__.copy()
    data["tiene_geometria"] = proyecto.geom is not None
    data["puede_analizar"] = proyecto.geom is not None and proyecto.estado != "archivado"
    data["cliente_razon_social"] = cliente.razon_social if cliente else None
    return data


@router.get("", response_model=ProyectoListResponse)
async def listar_proyectos(
    cliente_id: Optional[UUID] = Query(None),
    estado: Optional[EstadoProyecto] = Query(None),
    region: Optional[str] = Query(None),
    busqueda: Optional[str] = Query(None, description="Buscar por nombre"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Listar proyectos con paginación y filtros."""
    query = select(Proyecto, Cliente).outerjoin(Cliente)

    # Filtros
    if cliente_id:
        query = query.where(Proyecto.cliente_id == cliente_id)
    if estado:
        query = query.where(Proyecto.estado == estado.value)
    if region:
        query = query.where(Proyecto.region == region)
    if busqueda:
        query = query.where(Proyecto.nombre.ilike(f"%{busqueda}%"))

    # Excluir archivados por defecto (a menos que se pida explícitamente)
    if estado != EstadoProyecto.ARCHIVADO:
        query = query.where(Proyecto.estado != "archivado")

    # Contar total
    count_subq = query.subquery()
    count_query = select(func.count()).select_from(count_subq)
    total = (await db.execute(count_query)).scalar() or 0

    # Ordenar y paginar
    query = query.order_by(Proyecto.updated_at.desc().nullsfirst())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    rows = result.all()

    items = []
    for proyecto, cliente in rows:
        # Contar documentos y análisis
        docs_count = await db.execute(
            select(func.count()).where(Documento.proyecto_id == proyecto.id)
        )
        analisis_count = await db.execute(
            select(func.count()).where(Analisis.proyecto_id == proyecto.id)
        )
        ultimo = await db.execute(
            select(Analisis.fecha_analisis)
            .where(Analisis.proyecto_id == proyecto.id)
            .order_by(Analisis.fecha_analisis.desc())
            .limit(1)
        )

        data = proyecto_to_response(proyecto, cliente)
        data["total_documentos"] = docs_count.scalar() or 0
        data["total_analisis"] = analisis_count.scalar() or 0
        data["ultimo_analisis"] = ultimo.scalar()

        items.append(ProyectoResponse.model_validate(data))

    return ProyectoListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.post("", response_model=ProyectoResponse, status_code=201)
async def crear_proyecto(
    data: ProyectoCreate,
    db: AsyncSession = Depends(get_db),
):
    """Crear nuevo proyecto."""
    # Verificar cliente si se proporciona
    if data.cliente_id:
        cliente_result = await db.execute(
            select(Cliente).where(Cliente.id == data.cliente_id, Cliente.activo == True)
        )
        if not cliente_result.scalar():
            raise HTTPException(400, "Cliente no encontrado o inactivo")

    # Preparar datos
    proyecto_data = data.model_dump(exclude={"geometria"})

    # Procesar geometría si existe
    if data.geometria:
        geom_shape = shape(data.geometria.model_dump())
        # Convertir Polygon a MultiPolygon si es necesario
        if geom_shape.geom_type == "Polygon":
            from shapely.geometry import MultiPolygon
            geom_shape = MultiPolygon([geom_shape])
        proyecto_data["geom"] = from_shape(geom_shape, srid=4326)

    proyecto = Proyecto(**proyecto_data)
    db.add(proyecto)
    await db.commit()
    await db.refresh(proyecto)

    # Obtener cliente para respuesta
    cliente = None
    if proyecto.cliente_id:
        result = await db.execute(select(Cliente).where(Cliente.id == proyecto.cliente_id))
        cliente = result.scalar()

    response_data = proyecto_to_response(proyecto, cliente)
    response_data["total_documentos"] = 0
    response_data["total_analisis"] = 0
    response_data["ultimo_analisis"] = None

    return ProyectoResponse.model_validate(response_data)


@router.get("/{proyecto_id}", response_model=ProyectoConGeometriaResponse)
async def obtener_proyecto(
    proyecto_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Obtener proyecto por ID con geometría."""
    result = await db.execute(
        select(Proyecto, Cliente)
        .outerjoin(Cliente)
        .where(Proyecto.id == proyecto_id)
    )
    row = result.first()

    if not row:
        raise HTTPException(404, "Proyecto no encontrado")

    proyecto, cliente = row

    # Contadores
    docs_count = await db.execute(
        select(func.count()).where(Documento.proyecto_id == proyecto.id)
    )
    analisis_count = await db.execute(
        select(func.count()).where(Analisis.proyecto_id == proyecto.id)
    )
    ultimo = await db.execute(
        select(Analisis.fecha_analisis)
        .where(Analisis.proyecto_id == proyecto.id)
        .order_by(Analisis.fecha_analisis.desc())
        .limit(1)
    )

    data = proyecto_to_response(proyecto, cliente)
    data["total_documentos"] = docs_count.scalar() or 0
    data["total_analisis"] = analisis_count.scalar() or 0
    data["ultimo_analisis"] = ultimo.scalar()

    # Agregar geometría
    if proyecto.geom:
        geom_shape = to_shape(proyecto.geom)
        data["geometria"] = mapping(geom_shape)
    else:
        data["geometria"] = None

    return ProyectoConGeometriaResponse.model_validate(data)


@router.put("/{proyecto_id}", response_model=ProyectoResponse)
async def actualizar_proyecto(
    proyecto_id: UUID,
    data: ProyectoUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Actualizar proyecto (sin geometría)."""
    result = await db.execute(select(Proyecto).where(Proyecto.id == proyecto_id))
    proyecto = result.scalar()

    if not proyecto:
        raise HTTPException(404, "Proyecto no encontrado")

    if proyecto.estado == "archivado":
        raise HTTPException(400, "No se puede modificar un proyecto archivado")

    # Verificar cliente si se cambia
    if data.cliente_id:
        cliente_result = await db.execute(
            select(Cliente).where(Cliente.id == data.cliente_id, Cliente.activo == True)
        )
        if not cliente_result.scalar():
            raise HTTPException(400, "Cliente no encontrado o inactivo")

    # Actualizar campos
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(proyecto, key, value)

    await db.commit()
    await db.refresh(proyecto)

    # Obtener cliente y contadores para respuesta
    cliente = None
    if proyecto.cliente_id:
        result = await db.execute(select(Cliente).where(Cliente.id == proyecto.cliente_id))
        cliente = result.scalar()

    docs_count = await db.execute(
        select(func.count()).where(Documento.proyecto_id == proyecto.id)
    )
    analisis_count = await db.execute(
        select(func.count()).where(Analisis.proyecto_id == proyecto.id)
    )

    response_data = proyecto_to_response(proyecto, cliente)
    response_data["total_documentos"] = docs_count.scalar() or 0
    response_data["total_analisis"] = analisis_count.scalar() or 0
    response_data["ultimo_analisis"] = None

    return ProyectoResponse.model_validate(response_data)


@router.patch("/{proyecto_id}/geometria", response_model=ProyectoResponse)
async def actualizar_geometria(
    proyecto_id: UUID,
    data: ProyectoGeometriaUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Actualizar solo la geometría del proyecto."""
    result = await db.execute(select(Proyecto).where(Proyecto.id == proyecto_id))
    proyecto = result.scalar()

    if not proyecto:
        raise HTTPException(404, "Proyecto no encontrado")

    if proyecto.estado == "archivado":
        raise HTTPException(400, "No se puede modificar un proyecto archivado")

    # Procesar geometría
    geom_shape = shape(data.geometria.model_dump())
    if geom_shape.geom_type == "Polygon":
        from shapely.geometry import MultiPolygon
        geom_shape = MultiPolygon([geom_shape])

    proyecto.geom = from_shape(geom_shape, srid=4326)

    await db.commit()
    await db.refresh(proyecto)

    # El trigger habrá actualizado estado y campos pre-calculados
    cliente = None
    if proyecto.cliente_id:
        result = await db.execute(select(Cliente).where(Cliente.id == proyecto.cliente_id))
        cliente = result.scalar()

    response_data = proyecto_to_response(proyecto, cliente)
    response_data["total_documentos"] = 0
    response_data["total_analisis"] = 0
    response_data["ultimo_analisis"] = None

    return ProyectoResponse.model_validate(response_data)


@router.patch("/{proyecto_id}/estado")
async def cambiar_estado(
    proyecto_id: UUID,
    nuevo_estado: EstadoProyecto,
    motivo: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Cambiar estado del proyecto."""
    result = await db.execute(select(Proyecto).where(Proyecto.id == proyecto_id))
    proyecto = result.scalar()

    if not proyecto:
        raise HTTPException(404, "Proyecto no encontrado")

    estado_actual = proyecto.estado

    # Validar transiciones permitidas
    transiciones_validas = {
        "borrador": ["completo", "archivado"],
        "completo": ["con_geometria", "archivado"],
        "con_geometria": ["analizado", "archivado"],
        "analizado": ["en_revision", "archivado"],
        "en_revision": ["aprobado", "rechazado"],
        "aprobado": ["archivado"],
        "rechazado": ["en_revision", "archivado"],
        "archivado": [],
    }

    if nuevo_estado.value not in transiciones_validas.get(estado_actual, []):
        raise HTTPException(
            400,
            f"Transición no permitida: {estado_actual} → {nuevo_estado.value}"
        )

    proyecto.estado = nuevo_estado.value
    await db.commit()

    return {"mensaje": f"Estado cambiado de {estado_actual} a {nuevo_estado.value}"}


@router.delete("/{proyecto_id}", status_code=204)
async def eliminar_proyecto(
    proyecto_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Archivar proyecto (soft delete)."""
    result = await db.execute(select(Proyecto).where(Proyecto.id == proyecto_id))
    proyecto = result.scalar()

    if not proyecto:
        raise HTTPException(404, "Proyecto no encontrado")

    proyecto.estado = "archivado"
    await db.commit()


@router.get("/{proyecto_id}/analisis")
async def historial_analisis_proyecto(
    proyecto_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Obtener historial de análisis del proyecto."""
    result = await db.execute(select(Proyecto).where(Proyecto.id == proyecto_id))
    if not result.scalar():
        raise HTTPException(404, "Proyecto no encontrado")

    analisis = await db.execute(
        select(Analisis)
        .where(Analisis.proyecto_id == proyecto_id)
        .order_by(Analisis.fecha_analisis.desc())
    )

    return analisis.scalars().all()
```

### 6.3 Crear archivo: `backend/app/api/v1/endpoints/documentos.py`

```python
"""
Endpoints para gestión de documentos.
"""
import os
import hashlib
import aiofiles
from uuid import UUID, uuid4
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.session import get_db
from app.db.models import Proyecto, Documento, CategoriaDocumento
from app.schemas.documento import (
    DocumentoResponse,
    DocumentoListResponse,
    CategoriaDocumento as CategoriaEnum,
)
from app.core.config import settings

router = APIRouter(prefix="/documentos", tags=["Documentos"])

# Configuración
UPLOAD_DIR = Path(settings.UPLOAD_DIR if hasattr(settings, 'UPLOAD_DIR') else "/var/www/mineria/uploads")
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/jpg",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/zip",
    "application/x-zip-compressed",
}


async def calcular_checksum(file_path: Path) -> str:
    """Calcula SHA256 del archivo."""
    sha256 = hashlib.sha256()
    async with aiofiles.open(file_path, 'rb') as f:
        while chunk := await f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()


@router.post("/proyectos/{proyecto_id}/documentos", response_model=DocumentoResponse, status_code=201)
async def subir_documento(
    proyecto_id: UUID,
    archivo: UploadFile = File(...),
    nombre: str = Form(...),
    categoria: CategoriaEnum = Form(CategoriaEnum.OTRO),
    descripcion: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
):
    """Subir documento a un proyecto."""
    # Verificar proyecto
    result = await db.execute(select(Proyecto).where(Proyecto.id == proyecto_id))
    proyecto = result.scalar()

    if not proyecto:
        raise HTTPException(404, "Proyecto no encontrado")

    if proyecto.estado == "archivado":
        raise HTTPException(400, "No se pueden agregar documentos a proyectos archivados")

    # Validar tipo de archivo
    if archivo.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            400,
            f"Tipo de archivo no permitido: {archivo.content_type}. "
            f"Permitidos: PDF, PNG, JPG, DOC, DOCX, XLS, XLSX, ZIP"
        )

    # Leer contenido para validar tamaño
    content = await archivo.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(400, f"Archivo demasiado grande. Máximo: {MAX_FILE_SIZE // (1024*1024)}MB")

    # Crear directorio del proyecto
    proyecto_dir = UPLOAD_DIR / str(proyecto_id)
    proyecto_dir.mkdir(parents=True, exist_ok=True)

    # Generar nombre único
    doc_id = uuid4()
    extension = Path(archivo.filename).suffix
    archivo_path = proyecto_dir / f"{doc_id}{extension}"

    # Guardar archivo
    async with aiofiles.open(archivo_path, 'wb') as f:
        await f.write(content)

    # Calcular checksum
    checksum = hashlib.sha256(content).hexdigest()

    # Crear registro en BD
    documento = Documento(
        id=doc_id,
        proyecto_id=proyecto_id,
        nombre=nombre,
        nombre_original=archivo.filename,
        categoria=CategoriaDocumento(categoria.value),
        descripcion=descripcion,
        archivo_path=str(archivo_path),
        mime_type=archivo.content_type,
        tamano_bytes=len(content),
        checksum_sha256=checksum,
    )

    db.add(documento)
    await db.commit()
    await db.refresh(documento)

    return DocumentoResponse.model_validate(documento)


@router.get("/proyectos/{proyecto_id}/documentos", response_model=DocumentoListResponse)
async def listar_documentos_proyecto(
    proyecto_id: UUID,
    categoria: Optional[CategoriaEnum] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Listar documentos de un proyecto."""
    # Verificar proyecto
    result = await db.execute(select(Proyecto).where(Proyecto.id == proyecto_id))
    if not result.scalar():
        raise HTTPException(404, "Proyecto no encontrado")

    query = select(Documento).where(Documento.proyecto_id == proyecto_id)

    if categoria:
        query = query.where(Documento.categoria == CategoriaDocumento(categoria.value))

    query = query.order_by(Documento.created_at.desc())

    result = await db.execute(query)
    documentos = result.scalars().all()

    total_bytes = sum(d.tamano_bytes for d in documentos)

    return DocumentoListResponse(
        items=[DocumentoResponse.model_validate(d) for d in documentos],
        total=len(documentos),
        total_bytes=total_bytes,
        total_mb=round(total_bytes / (1024 * 1024), 2),
    )


@router.get("/{documento_id}/descargar")
async def descargar_documento(
    documento_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Descargar documento."""
    result = await db.execute(select(Documento).where(Documento.id == documento_id))
    documento = result.scalar()

    if not documento:
        raise HTTPException(404, "Documento no encontrado")

    archivo_path = Path(documento.archivo_path)
    if not archivo_path.exists():
        raise HTTPException(404, "Archivo no encontrado en el servidor")

    return FileResponse(
        path=archivo_path,
        filename=documento.nombre_original,
        media_type=documento.mime_type,
    )


@router.delete("/{documento_id}", status_code=204)
async def eliminar_documento(
    documento_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Eliminar documento."""
    result = await db.execute(select(Documento).where(Documento.id == documento_id))
    documento = result.scalar()

    if not documento:
        raise HTTPException(404, "Documento no encontrado")

    # Verificar que proyecto no esté archivado
    proyecto_result = await db.execute(
        select(Proyecto).where(Proyecto.id == documento.proyecto_id)
    )
    proyecto = proyecto_result.scalar()

    if proyecto and proyecto.estado == "archivado":
        raise HTTPException(400, "No se pueden eliminar documentos de proyectos archivados")

    # Eliminar archivo físico
    archivo_path = Path(documento.archivo_path)
    if archivo_path.exists():
        archivo_path.unlink()

    # Eliminar registro
    await db.delete(documento)
    await db.commit()
```

### 6.4 Modificar endpoint de análisis: `backend/app/api/v1/endpoints/prefactibilidad.py`

Agregar al endpoint existente la integración LLM con auditoría:

```python
"""
AGREGAR AL ARCHIVO EXISTENTE - Integración LLM con Auditoría.
"""
import hashlib
import json
from datetime import datetime

async def crear_auditoria_analisis(
    db: AsyncSession,
    analisis_id: UUID,
    proyecto: Proyecto,
    resultado_gis: dict,
    normativa: list,
    metricas: dict,
) -> None:
    """Crear registro de auditoría para el análisis."""
    from app.db.models import AuditoriaAnalisis
    from app.core.config import settings

    # Calcular checksum de datos de entrada
    datos_entrada = {
        "proyecto_id": str(proyecto.id),
        "nombre": proyecto.nombre,
        "geometria": proyecto.geom.desc if proyecto.geom else None,
        "timestamp": datetime.utcnow().isoformat(),
    }
    checksum = hashlib.sha256(
        json.dumps(datos_entrada, sort_keys=True).encode()
    ).hexdigest()

    # Capas GIS usadas
    capas_usadas = []
    for capa in ["areas_protegidas", "glaciares", "cuerpos_agua",
                  "comunidades_indigenas", "centros_poblados"]:
        if capa in resultado_gis:
            capas_usadas.append({
                "nombre": capa,
                "fecha": datetime.utcnow().strftime("%Y-%m-%d"),
                "version": "v2024.2"
            })

    # Normativa citada (extraer de respuesta RAG)
    normativa_citada = []
    for norma in normativa:
        if "articulo" in norma or "ley" in norma:
            normativa_citada.append({
                "tipo": norma.get("tipo", "Ley"),
                "numero": norma.get("numero", ""),
                "articulo": norma.get("articulo", ""),
            })

    auditoria = AuditoriaAnalisis(
        analisis_id=analisis_id,
        capas_gis_usadas=capas_usadas,
        normativa_citada=normativa_citada,
        checksum_datos_entrada=checksum,
        version_modelo_llm=settings.LLM_MODEL if hasattr(settings, 'LLM_MODEL') else "claude-sonnet-4-20250514",
        version_sistema="1.0.0",
        tiempo_gis_ms=metricas.get("tiempo_gis_ms"),
        tiempo_rag_ms=metricas.get("tiempo_rag_ms"),
        tiempo_llm_ms=metricas.get("tiempo_llm_ms"),
        tokens_usados=metricas.get("tokens_usados"),
    )

    db.add(auditoria)
    await db.commit()


# En el endpoint de análisis principal, agregar después de guardar el análisis:
"""
# Después de crear el análisis
await crear_auditoria_analisis(
    db=db,
    analisis_id=analisis.id,
    proyecto=proyecto,
    resultado_gis=resultado_gis,
    normativa=normativa_relevante,
    metricas={
        "tiempo_gis_ms": tiempo_gis,
        "tiempo_rag_ms": tiempo_rag,
        "tiempo_llm_ms": tiempo_llm,
        "tokens_usados": tokens_usados,
    }
)
"""
```

### 6.5 Actualizar router: `backend/app/api/v1/router.py`

```python
"""
Router principal de la API v1.
"""
from fastapi import APIRouter

from app.api.v1.endpoints import (
    prefactibilidad,
    analisis_espacial,
    buscar_normativa,
    ingestor,
    clientes,      # NUEVO
    proyectos,     # NUEVO
    documentos,    # NUEVO
)

api_router = APIRouter()

# Endpoints existentes
api_router.include_router(prefactibilidad.router)
api_router.include_router(analisis_espacial.router)
api_router.include_router(buscar_normativa.router)
api_router.include_router(ingestor.router)

# Nuevos endpoints
api_router.include_router(clientes.router)
api_router.include_router(proyectos.router)
api_router.include_router(documentos.router)
```

---

## 7. Configuración Adicional

### 7.1 Actualizar: `backend/app/core/config.py`

```python
"""
AGREGAR A LA CONFIGURACIÓN EXISTENTE
"""
# Uploads
UPLOAD_DIR: str = "/var/www/mineria/uploads"
MAX_UPLOAD_SIZE_MB: int = 50

# LLM
LLM_MODEL: str = "claude-sonnet-4-20250514"
```

### 7.2 Crear directorio de uploads

```bash
mkdir -p /var/www/mineria/uploads
chmod 755 /var/www/mineria/uploads
```

---

## 8. Tests

### 8.1 Crear archivo: `backend/tests/test_clientes.py`

```python
"""
Tests para endpoints de Clientes.
"""
import pytest
from httpx import AsyncClient
from uuid import uuid4


@pytest.mark.asyncio
async def test_crear_cliente(client: AsyncClient):
    """Test crear cliente."""
    response = await client.post("/api/v1/clientes", json={
        "razon_social": "Minera Test SpA",
        "email": "test@minera.cl"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["razon_social"] == "Minera Test SpA"
    assert data["cantidad_proyectos"] == 0


@pytest.mark.asyncio
async def test_crear_cliente_con_rut(client: AsyncClient):
    """Test crear cliente con RUT."""
    response = await client.post("/api/v1/clientes", json={
        "razon_social": "Minera Con RUT SpA",
        "rut": "76.543.210-K"
    })
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_listar_clientes(client: AsyncClient):
    """Test listar clientes."""
    response = await client.get("/api/v1/clientes")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_crear_proyecto_sin_geometria(client: AsyncClient):
    """Test crear proyecto sin geometría (permitido ahora)."""
    # Primero crear cliente
    cliente = await client.post("/api/v1/clientes", json={
        "razon_social": "Cliente Test"
    })
    cliente_id = cliente.json()["id"]

    # Crear proyecto sin geometría
    response = await client.post("/api/v1/proyectos", json={
        "nombre": "Proyecto Sin Mapa",
        "cliente_id": cliente_id,
        "region": "Coquimbo"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["estado"] == "borrador"
    assert data["tiene_geometria"] == False
    assert data["puede_analizar"] == False
```

---

## 9. Resumen de Endpoints

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| **Clientes** |
| GET | `/api/v1/clientes` | Listar clientes (paginado) |
| POST | `/api/v1/clientes` | Crear cliente |
| GET | `/api/v1/clientes/{id}` | Obtener cliente |
| PUT | `/api/v1/clientes/{id}` | Actualizar cliente |
| DELETE | `/api/v1/clientes/{id}` | Desactivar cliente |
| GET | `/api/v1/clientes/{id}/proyectos` | Proyectos del cliente |
| **Proyectos** |
| GET | `/api/v1/proyectos` | Listar proyectos (filtros) |
| POST | `/api/v1/proyectos` | Crear proyecto |
| GET | `/api/v1/proyectos/{id}` | Obtener con geometría |
| PUT | `/api/v1/proyectos/{id}` | Actualizar datos |
| PATCH | `/api/v1/proyectos/{id}/geometria` | Actualizar geometría |
| PATCH | `/api/v1/proyectos/{id}/estado` | Cambiar estado |
| DELETE | `/api/v1/proyectos/{id}` | Archivar proyecto |
| GET | `/api/v1/proyectos/{id}/analisis` | Historial análisis |
| **Documentos** |
| POST | `/api/v1/proyectos/{id}/documentos` | Subir documento |
| GET | `/api/v1/proyectos/{id}/documentos` | Listar documentos |
| GET | `/api/v1/documentos/{id}/descargar` | Descargar archivo |
| DELETE | `/api/v1/documentos/{id}` | Eliminar documento |

---

## 10. Checklist de Implementación

- [ ] Ejecutar migración SQL `03_clientes_documentos.sql`
- [ ] Crear modelos: `cliente.py`, `documento.py`, `auditoria.py`
- [ ] Modificar modelo `proyecto.py`
- [ ] Actualizar `models/__init__.py`
- [ ] Crear schemas: `cliente.py`, `documento.py`, `proyecto.py` (actualizar)
- [ ] Crear endpoints: `clientes.py`, `proyectos.py`, `documentos.py`
- [ ] Actualizar `router.py`
- [ ] Actualizar `config.py`
- [ ] Crear directorio `/var/www/mineria/uploads`
- [ ] Ejecutar tests
- [ ] Verificar triggers funcionan correctamente
