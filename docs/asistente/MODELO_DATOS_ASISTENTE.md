# Modelo de Datos: Sistema de Asistente por Proyecto

> **Versión:** 1.1 | **Fecha:** Enero 2026 | **Actualización:** Soporte multi-industria

---

## 1. Diagrama de Relaciones

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        CONFIGURACIÓN POR INDUSTRIA                          │
│  ┌─────────────────┐                                                        │
│  │ tipos_proyecto  │◄─────────────────────────────────────────────┐         │
│  └────────┬────────┘                                              │         │
│           │                                                       │         │
│           ▼                                                       │         │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐│         │
│  │subtipos_proyecto│    │  pas_por_tipo   │    │umbrales_seia    ││         │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘│         │
│                                                                   │         │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐│         │
│  │normativa_por_tip│    │ oaeca_por_tipo  │    │impactos_por_tipo││         │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘│         │
│                                                                   │         │
│  ┌─────────────────┐    ┌─────────────────┐                       │         │
│  │anexos_por_tipo  │    │arboles_preguntas│                       │         │
│  └─────────────────┘    └─────────────────┘                       │         │
├───────────────────────────────────────────────────────────────────┼─────────┤
│                           PROYECTOS                               │         │
│                    ┌────────────────┐                             │         │
│                    │   proyectos    │◄────────────────────────────┘         │
│                    └───────┬────────┘                                       │
│           ┌────────────────┼────────────────┬─────────────────┐             │
│           ▼                ▼                ▼                 ▼             │
│  ┌─────────────────┐ ┌───────────────┐ ┌────────────┐ ┌───────────────┐     │
│  │proyecto_        │ │proyecto_      │ │proyecto_   │ │proyecto_      │     │
│  │ubicaciones      │ │caracteristicas│ │documentos  │ │conversaciones │     │
│  └─────────────────┘ └───────┬───────┘ └────────────┘ └───────┬───────┘     │
│                              │                                │             │
│                              ▼                                ▼             │
│                    ┌─────────────────┐              ┌─────────────────┐     │
│                    │proyecto_        │              │conversacion_    │     │
│                    │analisis_art11   │              │mensajes         │     │
│                    └────────┬────────┘              └─────────────────┘     │
│                             │                                               │
│                             ▼                                               │
│                    ┌─────────────────┐    ┌─────────────────┐               │
│                    │proyecto_        │    │proyecto_pas     │               │
│                    │diagnosticos     │    │(instancia)      │               │
│                    └─────────────────┘    └─────────────────┘               │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Esquema: asistente_config (Configuración por Industria)

### tipos_proyecto
```sql
CREATE TABLE asistente_config.tipos_proyecto (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(50) UNIQUE NOT NULL,  -- 'mineria', 'energia', 'inmobiliario'
    nombre VARCHAR(100) NOT NULL,
    letra_art3 VARCHAR(5),               -- 'i)', 'c)', 'g)' según DS 40
    descripcion TEXT,
    activo BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### subtipos_proyecto (NUEVO)
```sql
CREATE TABLE asistente_config.subtipos_proyecto (
    id SERIAL PRIMARY KEY,
    tipo_proyecto_id INTEGER NOT NULL REFERENCES asistente_config.tipos_proyecto(id),
    codigo VARCHAR(50) NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT,
    activo BOOLEAN DEFAULT true,
    UNIQUE(tipo_proyecto_id, codigo)
);

-- Ejemplos:
-- (energia, 'solar', 'Central Solar Fotovoltaica')
-- (energia, 'eolica', 'Parque Eólico')
-- (energia, 'hidro_embalse', 'Central Hidroeléctrica de Embalse')
-- (mineria, 'extraccion_rajo', 'Extracción a Rajo Abierto')
-- (mineria, 'extraccion_subterranea', 'Extracción Subterránea')
-- (inmobiliario, 'habitacional', 'Conjunto Habitacional')
```

### umbrales_seia (NUEVO) - Determina ingreso al SEIA
```sql
CREATE TABLE asistente_config.umbrales_seia (
    id SERIAL PRIMARY KEY,
    tipo_proyecto_id INTEGER REFERENCES asistente_config.tipos_proyecto(id),
    subtipo_id INTEGER REFERENCES asistente_config.subtipos_proyecto(id),
    parametro VARCHAR(100) NOT NULL,      -- 'tonelaje_mensual', 'potencia_mw', 'superficie_ha'
    operador VARCHAR(10) NOT NULL,        -- '>=', '>', '<', '<=', '='
    valor NUMERIC NOT NULL,
    unidad VARCHAR(50),                   -- 'ton/mes', 'MW', 'ha'
    resultado VARCHAR(50) NOT NULL,       -- 'ingresa_seia', 'no_ingresa', 'requiere_eia'
    descripcion TEXT,
    norma_referencia VARCHAR(100)         -- 'Art. 3 letra i.1) DS 40'
);

-- Ejemplos:
-- (mineria, NULL, 'tonelaje_mensual', '>=', 5000, 'ton/mes', 'ingresa_seia', 'Art. 3 i.1)')
-- (energia, solar, 'potencia_mw', '>=', 3, 'MW', 'ingresa_seia', 'Art. 3 c)')
```

### pas_por_tipo (NUEVO) - PAS típicos por industria
```sql
CREATE TABLE asistente_config.pas_por_tipo (
    id SERIAL PRIMARY KEY,
    tipo_proyecto_id INTEGER REFERENCES asistente_config.tipos_proyecto(id),
    subtipo_id INTEGER REFERENCES asistente_config.subtipos_proyecto(id),
    articulo INTEGER NOT NULL,            -- 111, 120, 135, etc.
    nombre VARCHAR(200) NOT NULL,
    organismo VARCHAR(100) NOT NULL,      -- 'DGA', 'CMN', 'SERNAGEOMIN'
    obligatoriedad VARCHAR(20) NOT NULL,  -- 'obligatorio', 'frecuente', 'caso_a_caso'
    condicion_activacion JSONB,           -- {"campo": "tiene_relaves", "valor": true}
    descripcion TEXT
);

-- Ejemplos:
-- (mineria, NULL, 135, 'Depósito de relaves', 'SERNAGEOMIN', 'obligatorio', {"tiene_relaves": true})
-- (mineria, NULL, 137, 'Plan de cierre', 'SERNAGEOMIN', 'obligatorio', NULL)
-- (energia, hidro, 111, 'Alteración de cauce', 'DGA', 'obligatorio', NULL)
```

### normativa_por_tipo (NUEVO)
```sql
CREATE TABLE asistente_config.normativa_por_tipo (
    id SERIAL PRIMARY KEY,
    tipo_proyecto_id INTEGER REFERENCES asistente_config.tipos_proyecto(id),
    norma VARCHAR(100) NOT NULL,          -- 'D.S. 90/2000', 'Ley 20.551'
    nombre VARCHAR(200) NOT NULL,
    componente VARCHAR(100),              -- 'agua', 'aire', 'residuos'
    tipo_norma VARCHAR(50),               -- 'calidad', 'emision', 'sectorial'
    aplica_siempre BOOLEAN DEFAULT false,
    descripcion TEXT
);
```

### oaeca_por_tipo (NUEVO)
```sql
CREATE TABLE asistente_config.oaeca_por_tipo (
    id SERIAL PRIMARY KEY,
    tipo_proyecto_id INTEGER REFERENCES asistente_config.tipos_proyecto(id),
    organismo VARCHAR(100) NOT NULL,      -- 'DGA', 'SAG', 'SERNAGEOMIN'
    competencias TEXT[],                  -- ['recursos hídricos', 'derechos de agua']
    relevancia VARCHAR(20) NOT NULL       -- 'principal', 'secundario'
);
```

### impactos_por_tipo (NUEVO)
```sql
CREATE TABLE asistente_config.impactos_por_tipo (
    id SERIAL PRIMARY KEY,
    tipo_proyecto_id INTEGER REFERENCES asistente_config.tipos_proyecto(id),
    subtipo_id INTEGER REFERENCES asistente_config.subtipos_proyecto(id),
    componente VARCHAR(100) NOT NULL,     -- 'aire', 'agua', 'fauna', 'medio_humano'
    impacto TEXT NOT NULL,
    fase VARCHAR(50),                     -- 'construccion', 'operacion', 'cierre'
    frecuencia VARCHAR(20)                -- 'muy_comun', 'frecuente', 'ocasional'
);
```

### anexos_por_tipo (NUEVO)
```sql
CREATE TABLE asistente_config.anexos_por_tipo (
    id SERIAL PRIMARY KEY,
    tipo_proyecto_id INTEGER REFERENCES asistente_config.tipos_proyecto(id),
    subtipo_id INTEGER REFERENCES asistente_config.subtipos_proyecto(id),
    codigo VARCHAR(10) NOT NULL,          -- 'A1', 'A13', 'A20'
    nombre VARCHAR(200) NOT NULL,
    profesional_responsable VARCHAR(100),
    obligatorio BOOLEAN DEFAULT false,
    condicion_activacion JSONB
);

-- Ejemplos:
-- (mineria, NULL, 'A20', 'Diseño depósito de relaves', 'Ing. Civil', true, {"tiene_relaves": true})
-- (mineria, NULL, 'A13', 'Estudio arqueológico', 'Arqueólogo', true, NULL)
```

### arboles_preguntas (actualizado)
```sql
CREATE TABLE asistente_config.arboles_preguntas (
    id SERIAL PRIMARY KEY,
    tipo_proyecto_id INTEGER REFERENCES asistente_config.tipos_proyecto(id),
    subtipo_id INTEGER REFERENCES asistente_config.subtipos_proyecto(id),  -- NUEVO
    codigo VARCHAR(50) NOT NULL,
    pregunta_texto TEXT NOT NULL,
    tipo_respuesta VARCHAR(20) NOT NULL,  -- 'texto', 'numero', 'opcion', 'archivo', 'ubicacion'
    opciones JSONB,
    orden INTEGER DEFAULT 0,
    es_obligatoria BOOLEAN DEFAULT false,
    campo_destino VARCHAR(100),
    condicion_activacion JSONB,
    valida_umbral BOOLEAN DEFAULT false,  -- NUEVO: Si activa validación de umbral
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 3. Esquema: proyectos (Datos del Proyecto)

### proyecto_ubicaciones
```sql
CREATE TABLE proyectos.proyecto_ubicaciones (
    id SERIAL PRIMARY KEY,
    proyecto_id INTEGER NOT NULL REFERENCES proyectos.proyectos(id) ON DELETE CASCADE,
    geometria GEOMETRY(GEOMETRY, 4326) NOT NULL,
    regiones TEXT[],
    comunas TEXT[],
    provincias TEXT[],                    -- NUEVO
    alcance VARCHAR(20),                  -- 'regional', 'bi_regional', 'nacional'
    superficie_ha NUMERIC,                -- NUEVO: calculado de geometría
    analisis_gis_cache JSONB,
    version INTEGER DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_ubicaciones_geom ON proyectos.proyecto_ubicaciones USING GIST(geometria);
```

### proyecto_caracteristicas
```sql
CREATE TABLE proyectos.proyecto_caracteristicas (
    id SERIAL PRIMARY KEY,
    proyecto_id INTEGER NOT NULL REFERENCES proyectos.proyectos(id) ON DELETE CASCADE,
    categoria VARCHAR(50) NOT NULL,
    clave VARCHAR(100) NOT NULL,
    valor TEXT,
    valor_numerico NUMERIC,               -- NUEVO: para comparaciones de umbral
    unidad VARCHAR(50),                   -- NUEVO
    fuente VARCHAR(20) DEFAULT 'manual',
    documento_id INTEGER,
    validado BOOLEAN DEFAULT false,       -- NUEVO
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(proyecto_id, categoria, clave)
);
```

### proyecto_pas (NUEVO) - Instancia de PAS por proyecto
```sql
CREATE TABLE proyectos.proyecto_pas (
    id SERIAL PRIMARY KEY,
    proyecto_id INTEGER NOT NULL REFERENCES proyectos.proyectos(id) ON DELETE CASCADE,
    articulo INTEGER NOT NULL,
    nombre VARCHAR(200) NOT NULL,
    organismo VARCHAR(100) NOT NULL,
    estado VARCHAR(30) DEFAULT 'identificado',  -- 'identificado', 'requerido', 'en_tramite', 'aprobado', 'rechazado'
    obligatorio BOOLEAN DEFAULT false,
    justificacion TEXT,                   -- Por qué aplica o no aplica
    documento_id INTEGER,                 -- Resolución si existe
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(proyecto_id, articulo)
);
```

### proyecto_analisis_art11
```sql
CREATE TABLE proyectos.proyecto_analisis_art11 (
    id SERIAL PRIMARY KEY,
    proyecto_id INTEGER NOT NULL REFERENCES proyectos.proyectos(id) ON DELETE CASCADE,
    literal CHAR(1) NOT NULL,
    estado VARCHAR(20) DEFAULT 'pendiente',
    justificacion TEXT,
    evidencias JSONB,
    fuente_gis BOOLEAN DEFAULT false,     -- NUEVO: si viene del análisis GIS
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(proyecto_id, literal)
);
```

### proyecto_diagnosticos
```sql
CREATE TABLE proyectos.proyecto_diagnosticos (
    id SERIAL PRIMARY KEY,
    proyecto_id INTEGER NOT NULL REFERENCES proyectos.proyectos(id) ON DELETE CASCADE,
    version INTEGER DEFAULT 1,
    via_sugerida VARCHAR(10),             -- 'DIA', 'EIA', 'NO_SEIA'
    confianza INTEGER,
    literales_gatillados CHAR(1)[],
    permisos_identificados JSONB,
    alertas JSONB,
    recomendaciones JSONB,
    cumple_umbral_seia BOOLEAN,           -- NUEVO
    umbral_evaluado JSONB,                -- NUEVO: detalle del umbral
    ubicacion_version_id INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### proyecto_documentos
```sql
CREATE TABLE proyectos.proyecto_documentos (
    id SERIAL PRIMARY KEY,
    proyecto_id INTEGER NOT NULL REFERENCES proyectos.proyectos(id) ON DELETE CASCADE,
    nombre VARCHAR(255) NOT NULL,
    tipo VARCHAR(20) NOT NULL,
    tipo_anexo VARCHAR(10),               -- NUEVO: 'A1', 'A13', etc. si es anexo EIA
    ruta_archivo TEXT NOT NULL,
    tamano_bytes BIGINT,
    ocr_completado BOOLEAN DEFAULT false,
    texto_extraido TEXT,                  -- NUEVO: resultado OCR
    vectorizado BOOLEAN DEFAULT false,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 4. Esquema: conversaciones

### proyecto_conversaciones
```sql
CREATE TABLE proyectos.proyecto_conversaciones (
    id SERIAL PRIMARY KEY,
    proyecto_id INTEGER NOT NULL REFERENCES proyectos.proyectos(id) ON DELETE CASCADE,
    estado VARCHAR(20) DEFAULT 'activa',
    fase VARCHAR(50) DEFAULT 'prefactibilidad',  -- NUEVO: 'prefactibilidad', 'estructuracion', 'recopilacion'
    resumen_actual TEXT,
    ultima_pregunta_codigo VARCHAR(50),
    progreso_porcentaje INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### conversacion_mensajes
```sql
CREATE TABLE proyectos.conversacion_mensajes (
    id SERIAL PRIMARY KEY,
    conversacion_id INTEGER NOT NULL REFERENCES proyectos.proyecto_conversaciones(id) ON DELETE CASCADE,
    rol VARCHAR(20) NOT NULL,
    contenido TEXT NOT NULL,
    documento_adjunto_id INTEGER REFERENCES proyectos.proyecto_documentos(id),
    acciones_ejecutadas JSONB,
    tokens_usados INTEGER,                -- NUEVO: para tracking
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_mensajes_conversacion ON proyectos.conversacion_mensajes(conversacion_id);
```

---

## 5. Mapeo: Capítulos EIA → Tablas

| Capítulo EIA | Tabla(s) | Campo/Categoría |
|--------------|----------|-----------------|
| **Cap 1.1** Antecedentes | proyecto_caracteristicas | categoria='identificacion' |
| **Cap 1.2** Localización | proyecto_ubicaciones | geometria, regiones, comunas |
| **Cap 1.3** Obras | proyecto_caracteristicas | categoria='obras' |
| **Cap 1.4** Fases | proyecto_caracteristicas | categoria='fases' |
| **Cap 1.5** Insumos | proyecto_caracteristicas | categoria='insumos' |
| **Cap 1.6** Emisiones | proyecto_caracteristicas | categoria='emisiones' |
| **Cap 2** Área Influencia | proyecto_ubicaciones | analisis_gis_cache |
| **Cap 3** Línea Base | proyecto_documentos | tipo_anexo='A3' a 'A15' |
| **Cap 4** Impactos | proyecto_analisis_art11 | literal, estado |
| **Cap 9** PAS | proyecto_pas | todos los registros |
| **Anexos** | proyecto_documentos | tipo_anexo |

---

## 6. Datos Iniciales por Industria

### Tipos y Subtipos
```sql
-- Tipos principales
INSERT INTO asistente_config.tipos_proyecto (codigo, nombre, letra_art3) VALUES
('mineria', 'Minería', 'i)'),
('energia', 'Energía', 'c)'),
('inmobiliario', 'Inmobiliario/Urbano', 'g)'),
('acuicultura', 'Acuicultura/Pesca', 'n)'),
('infraestructura', 'Infraestructura Vial', 'e)'),
('portuario', 'Portuario', 'f)'),
('forestal', 'Forestal', 'm)'),
('agroindustria', 'Agroindustria', 'l)');

-- Subtipos energía
INSERT INTO asistente_config.subtipos_proyecto (tipo_proyecto_id, codigo, nombre) VALUES
(2, 'solar', 'Central Solar Fotovoltaica'),
(2, 'eolica', 'Parque Eólico'),
(2, 'hidro_pasada', 'Central Hidroeléctrica de Pasada'),
(2, 'hidro_embalse', 'Central Hidroeléctrica de Embalse'),
(2, 'termoelectrica', 'Central Termoeléctrica'),
(2, 'geotermica', 'Central Geotérmica');

-- Subtipos minería
INSERT INTO asistente_config.subtipos_proyecto (tipo_proyecto_id, codigo, nombre) VALUES
(1, 'extraccion_rajo', 'Extracción a Rajo Abierto'),
(1, 'extraccion_subterranea', 'Extracción Subterránea'),
(1, 'planta_beneficio', 'Planta de Beneficio'),
(1, 'deposito_relaves', 'Depósito de Relaves'),
(1, 'botadero', 'Botadero de Estériles');
```

### Umbrales SEIA
```sql
INSERT INTO asistente_config.umbrales_seia
(tipo_proyecto_id, parametro, operador, valor, unidad, resultado, norma_referencia) VALUES
(1, 'tonelaje_mensual', '>=', 5000, 'ton/mes', 'ingresa_seia', 'Art. 3 i.1) DS 40'),
(2, 'potencia_mw', '>=', 3, 'MW', 'ingresa_seia', 'Art. 3 c) DS 40'),
(3, 'superficie_ha', '>=', 7, 'ha', 'ingresa_seia', 'Art. 3 g) DS 40'),
(3, 'viviendas', '>=', 300, 'unidades', 'ingresa_seia', 'Art. 3 g) DS 40');
```

### PAS típicos minería
```sql
INSERT INTO asistente_config.pas_por_tipo
(tipo_proyecto_id, articulo, nombre, organismo, obligatoriedad, condicion_activacion) VALUES
(1, 135, 'Depósito de relaves', 'SERNAGEOMIN', 'obligatorio', '{"tiene_relaves": true}'),
(1, 136, 'Botadero de estériles', 'SERNAGEOMIN', 'obligatorio', '{"tiene_botadero": true}'),
(1, 137, 'Plan de cierre faena minera', 'SERNAGEOMIN', 'obligatorio', NULL),
(1, 111, 'Obras alteración de cauce', 'DGA', 'frecuente', '{"interviene_cauce": true}'),
(1, 120, 'Intervención monumentos arqueológicos', 'CMN', 'frecuente', NULL),
(1, 132, 'Tratamiento aguas servidas', 'SEREMI Salud', 'obligatorio', NULL),
(1, 133, 'Manejo residuos peligrosos', 'SEREMI Salud', 'obligatorio', NULL);
```

---

## 7. Script de Migración

```sql
-- 1. Crear esquema
CREATE SCHEMA IF NOT EXISTS asistente_config;

-- 2. Ejecutar en orden:
-- a) tipos_proyecto
-- b) subtipos_proyecto
-- c) umbrales_seia
-- d) pas_por_tipo
-- e) normativa_por_tipo
-- f) oaeca_por_tipo
-- g) impactos_por_tipo
-- h) anexos_por_tipo
-- i) arboles_preguntas
-- j) proyecto_ubicaciones
-- k) proyecto_caracteristicas
-- l) proyecto_pas
-- m) proyecto_documentos
-- n) proyecto_analisis_art11
-- o) proyecto_diagnosticos
-- p) proyecto_conversaciones
-- q) conversacion_mensajes

-- 3. Insertar datos iniciales
```

---

*Ver ROADMAP_ASISTENTE.md para fases del proyecto*
*Ver ARQUITECTURA_ASISTENTE.md para estructura de código*
