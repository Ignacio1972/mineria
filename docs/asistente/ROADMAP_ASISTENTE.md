# Roadmap: Sistema de Asistente Inteligente por Proyecto

> **Versión:** 2.0 | **Fecha:** Enero 2026 | **Actualización:** Todas las fases completadas

---

## Estado Actual

| Fase | Estado | Fecha Completado |
|------|--------|------------------|
| **Fase 1: Prefactibilidad + Multi-industria** | ✅ Completada | Enero 2026 |
| **Fase 2: Estructuración EIA** | ✅ Completada | Enero 2026 |
| **Fase 3: Recopilación Guiada** | ✅ Completada | Enero 2026 |
| **Fase 4: Generación EIA** | ✅ Completada | Enero 2026 |

---

## 1. Visión del Proyecto

Sistema de **asistente de IA por proyecto** que guía usuarios en evaluación ambiental, desde prefactibilidad hasta generación de EIA. **Escalable a múltiples industrias**: minería, energía, inmobiliario, acuicultura, infraestructura, etc.

### 1.1 Objetivos

1. **Prefactibilidad automatizada**: Determinar ingreso al SEIA y vía (DIA/EIA)
2. **Recopilación guiada**: Preguntas adaptadas por industria/subtipo
3. **Análisis continuo**: Validación contra corpus y umbrales legales
4. **Multi-industria**: Configuración por sector sin cambios de código
5. **Generación de EIA**: Borrador basado en información recopilada

---

## 2. Fases del Proyecto

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ROADMAP DE DESARROLLO                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  FASE 1 ✅            FASE 2 ✅             FASE 3 ✅           FASE 4 ✅   │
│  Prefactibilidad       Estructuración        Recopilación        Generación │
│  + Multi-industria     EIA                   Guiada              EIA        │
│                                                                             │
│  ┌──────────┐         ┌──────────┐          ┌──────────┐       ┌──────────┐ │
│  │ Asistente│         │ Template │          │ Capítulo │       │ Documento│ │
│  │ + Config │────────►│ + PAS    │─────────►│ por      │──────►│ Final    │ │
│  │ Industria│         │ + Anexos │          │ Capítulo │       │ + Export │ │
│  └────✅────┘         └────✅────┘          └────✅────┘       └────✅────┘ │
│                                                                             │
│  MVP ✅                v1.1 ✅               v1.2 ✅             v2.0 ✅    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Fase 1: Prefactibilidad + Multi-industria (MVP) ✅ COMPLETADA

### 3.1 Objetivo
Asistente conversacional con soporte multi-industria desde el inicio. La configuración por sector está en BD, no en código.

### 3.2 Funcionalidades

| ID | Funcionalidad | Prioridad |
|----|---------------|-----------|
| F1.1 | Asistente por proyecto con contexto persistente | Alta |
| F1.2 | **Configuración por industria (tipos, subtipos, umbrales)** | Alta |
| F1.3 | **Evaluación automática de umbrales SEIA** | Alta |
| F1.4 | **Identificación automática de PAS** | Alta |
| F1.5 | Árbol de preguntas configurable por tipo/subtipo | Alta |
| F1.6 | Ficha acumulativa estructurada | Alta |
| F1.7 | Análisis GIS automático al subir ubicación | Alta |
| F1.8 | Cotejo con corpus RAG | Alta |
| F1.9 | Upload de documentos con OCR | Media |
| F1.10 | Diagnóstico Art. 11 (DIA vs EIA) | Alta |
| F1.11 | Historial persistente de conversación | Alta |

### 3.3 Entregables

**Modelo de datos:**
- Esquema `asistente_config`: tipos, subtipos, umbrales, pas, normativa, oaeca
- Esquema `proyectos` extendido: ficha, ubicaciones, documentos, conversaciones

**Backend:**
- `ConfigIndustriaService`: gestión de configuración por industria
- `AsistenteService`: orquestador de conversación
- `FichaService`: CRUD ficha acumulativa
- Endpoints de configuración y asistente

**Frontend:**
- Vista de asistente en proyecto
- Panel lateral de ficha
- Selector de tipo/subtipo
- Upload de documentos

**Datos iniciales:**
- Configuración completa para **Minería** (tipos, subtipos, PAS, umbrales)
- Configuración base para Energía, Inmobiliario (expandir después)

### 3.4 Criterios de Éxito

- [x] Usuario selecciona tipo/subtipo y recibe preguntas específicas
- [x] Sistema evalúa umbrales SEIA automáticamente
- [x] Sistema identifica PAS aplicables según características
- [x] Al subir ubicación, ejecuta análisis GIS
- [x] Genera diagnóstico preliminar con justificación
- [x] Usuario puede retomar conversación después de días
- [x] Agregar nueva industria = solo insertar datos en BD

> **Verificado:** Enero 2026 - Ver `BRIEFING_FASE1_DESARROLLADOR.md` para detalles de implementación.

---

## 4. Fase 2: Estructuración EIA ✅ COMPLETADA

### 4.1 Objetivo
Generar estructura del EIA con capítulos, anexos y PAS según tipo de proyecto.

### 4.2 Funcionalidades

| ID | Funcionalidad |
|----|---------------|
| F2.1 | Template EIA por industria (11 capítulos adaptados) |
| F2.2 | Lista de PAS requeridos con estado |
| F2.3 | Lista de anexos técnicos requeridos |
| F2.4 | Plan de línea base por componente |
| F2.5 | Estimación de alcance y complejidad |

---

## 5. Fase 3: Recopilación Guiada ✅ COMPLETADA

### 5.1 Objetivo
Sistema de recopilación inteligente capítulo por capítulo del EIA. El asistente guía al usuario a través de cada sección, extrae datos de documentos técnicos, valida completitud y detecta inconsistencias entre capítulos.

### 5.2 Funcionalidades

| ID | Funcionalidad | Prioridad |
|----|---------------|-----------|
| F3.1 | Navegación guiada por capítulos del EIA | Alta |
| F3.2 | Validación de completitud por sección con checklist | Alta |
| F3.3 | Extracción de datos de estudios técnicos (OCR + IA) | Alta |
| F3.4 | Detección de inconsistencias entre capítulos | Media |
| F3.5 | Sugerencias de redacción según corpus SEA | Media |
| F3.6 | Vinculación de documentos a secciones específicas | Alta |
| F3.7 | Progreso visual por capítulo y sección | Alta |
| F3.8 | Alertas de información faltante o incompleta | Media |

### 5.3 Arquitectura

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      FASE 3: RECOPILACIÓN GUIADA                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  FLUJO DE TRABAJO                                                           │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │ Selección│    │ Preguntas│    │ Upload   │    │ Validar  │              │
│  │ Capítulo │───►│ Guiadas  │───►│ Docs     │───►│ Completar│              │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘              │
│       │                               │                │                    │
│       │              ┌────────────────┴────────────────┘                    │
│       │              ▼                                                      │
│       │    ┌──────────────────┐                                             │
│       └───►│ Extracción IA    │ (OCR + Claude Vision)                       │
│            │ de documentos    │                                             │
│            └────────┬─────────┘                                             │
│                     ▼                                                       │
│            ┌──────────────────┐                                             │
│            │ Validación cruzada│ (Detectar inconsistencias)                 │
│            └──────────────────┘                                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.4 Entregables

**Modelo de datos:**

```sql
-- Contenido por sección del EIA (instancia por proyecto)
CREATE TABLE proyectos.contenido_eia (
    id SERIAL PRIMARY KEY,
    proyecto_id INTEGER REFERENCES proyectos.proyectos(id),
    capitulo_numero INTEGER NOT NULL,
    seccion_codigo VARCHAR(50) NOT NULL,
    contenido JSONB,                    -- Datos estructurados de la sección
    estado VARCHAR(20) DEFAULT 'pendiente',
    progreso INTEGER DEFAULT 0,
    documentos_vinculados INTEGER[],    -- IDs de documentos asociados
    validaciones JSONB,                 -- Resultados de validación
    inconsistencias JSONB,              -- Inconsistencias detectadas
    sugerencias JSONB,                  -- Sugerencias de mejora
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(proyecto_id, capitulo_numero, seccion_codigo)
);

-- Preguntas de recopilación por sección
CREATE TABLE asistente_config.preguntas_recopilacion (
    id SERIAL PRIMARY KEY,
    tipo_proyecto_id INTEGER REFERENCES asistente_config.tipos_proyecto(id),
    capitulo_numero INTEGER NOT NULL,
    seccion_codigo VARCHAR(50) NOT NULL,
    pregunta TEXT NOT NULL,
    tipo_respuesta VARCHAR(30),         -- texto, numero, fecha, seleccion, archivo
    opciones JSONB,                     -- Para tipo selección
    validaciones JSONB,                 -- Reglas de validación
    es_obligatoria BOOLEAN DEFAULT true,
    orden INTEGER
);

-- Reglas de consistencia entre capítulos
CREATE TABLE asistente_config.reglas_consistencia (
    id SERIAL PRIMARY KEY,
    tipo_proyecto_id INTEGER REFERENCES asistente_config.tipos_proyecto(id),
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT,
    capitulo_origen INTEGER,
    seccion_origen VARCHAR(50),
    capitulo_destino INTEGER,
    seccion_destino VARCHAR(50),
    regla_validacion JSONB,             -- Lógica de validación
    mensaje_error TEXT,
    severidad VARCHAR(20) DEFAULT 'warning'
);

-- Índices
CREATE INDEX idx_contenido_proyecto ON proyectos.contenido_eia(proyecto_id);
CREATE INDEX idx_contenido_capitulo ON proyectos.contenido_eia(capitulo_numero);
CREATE INDEX idx_preguntas_tipo ON asistente_config.preguntas_recopilacion(tipo_proyecto_id);
```

**Backend:**

- `RecopilacionService`: Orquestador de recopilación por capítulo
  - `iniciar_capitulo(proyecto_id, capitulo)` → Inicia flujo de recopilación
  - `get_preguntas_seccion(tipo, capitulo, seccion)` → Preguntas pendientes
  - `guardar_respuesta(proyecto_id, seccion, datos)` → Persiste contenido
  - `validar_seccion(proyecto_id, seccion)` → Valida completitud
  - `validar_consistencia(proyecto_id)` → Detecta inconsistencias

- `ExtraccionDocumentosService`: Extracción inteligente de documentos
  - `extraer_datos(documento_id, tipo_estudio)` → Extrae datos con Claude Vision
  - `mapear_a_secciones(datos, capitulo)` → Sugiere mapeo a secciones
  - `vincular_documento(doc_id, seccion_codigo)` → Vincula doc a sección

- Herramientas del Asistente:
  - `iniciar_recopilacion_capitulo` (ACCION) - Inicia recopilación de un capítulo
  - `guardar_contenido_seccion` (ACCION) - Guarda contenido de una sección
  - `consultar_progreso_capitulo` (CONSULTA) - Estado del capítulo
  - `extraer_datos_documento` (ACCION) - Extrae datos de documento subido
  - `validar_consistencia_eia` (CONSULTA) - Detecta inconsistencias
  - `sugerir_redaccion` (CONSULTA) - Sugiere texto basado en corpus

- Endpoints API:
  - `POST /recopilacion/{proyecto_id}/capitulo/{num}/iniciar`
  - `GET /recopilacion/{proyecto_id}/capitulo/{num}/preguntas`
  - `POST /recopilacion/{proyecto_id}/seccion/{codigo}`
  - `GET /recopilacion/{proyecto_id}/progreso`
  - `POST /recopilacion/{proyecto_id}/validar`
  - `POST /recopilacion/{proyecto_id}/extraer-documento`
  - `GET /recopilacion/{proyecto_id}/inconsistencias`

**Frontend:**

- `RecopilacionCapitulo.vue` - Vista principal de recopilación por capítulo
- `SeccionForm.vue` - Formulario dinámico por sección
- `ProgresoCapitulos.vue` - Navegación con progreso visual
- `DocumentoExtractor.vue` - Upload y extracción de documentos
- `InconsistenciasPanel.vue` - Panel de alertas de inconsistencias
- `SugerenciasRedaccion.vue` - Sugerencias de mejora de texto

**Datos iniciales:**
- Preguntas de recopilación para los 11 capítulos (minería)
- Reglas de consistencia entre capítulos (ej: área de influencia vs línea base)
- Templates de respuesta por sección

### 5.5 Flujo de Usuario

1. Usuario selecciona capítulo a completar
2. Asistente muestra preguntas pendientes de la primera sección
3. Usuario responde preguntas o sube documentos técnicos
4. Sistema extrae datos de documentos con IA y sugiere mapeo
5. Usuario confirma/edita datos extraídos
6. Sistema valida completitud de sección
7. Si hay inconsistencias con otros capítulos, muestra alertas
8. Al completar sección, avanza a siguiente
9. Al completar capítulo, muestra resumen y sugiere siguiente

### 5.6 Criterios de Éxito

- [ ] Usuario puede navegar entre capítulos y ver progreso visual
- [ ] Al seleccionar capítulo, asistente guía con preguntas específicas
- [ ] Sistema extrae datos de PDFs/imágenes con Claude Vision (>80% precisión)
- [ ] Datos extraídos se vinculan automáticamente a secciones correspondientes
- [ ] Sistema detecta inconsistencias entre capítulos (ej: coordenadas diferentes)
- [ ] Asistente sugiere redacción basada en corpus SEA aprobados
- [ ] Progreso se persiste y usuario puede retomar donde dejó
- [ ] Checklist de completitud visible por sección y capítulo
- [ ] Alertas claras cuando falta información obligatoria

---

## 6. Fase 4: Generación de EIA ✅ COMPLETADA

### 6.1 Objetivo
Generar documento EIA completo y exportable.

### 6.2 Funcionalidades

| ID | Funcionalidad |
|----|---------------|
| F4.1 | Compilación de documento completo |
| F4.2 | Generación de texto con LLM |
| F4.3 | Validación contra requisitos SEA |
| F4.4 | Exportación PDF/Word/e-SEIA |
| F4.5 | Versionado de documentos |

---

## 7. Estrategia Multi-industria

### 7.1 Industrias Prioritarias

| Prioridad | Industria | Letra Art.3 | Estado |
|-----------|-----------|-------------|--------|
| 1 | Minería | i) | Template listo, config en Fase 1 |
| 2 | Energía | c) | Config básica en Fase 1 |
| 3 | Inmobiliario | g) | Config básica en Fase 1 |
| 4 | Acuicultura | n) | Post-MVP |
| 5 | Infraestructura vial | e) | Post-MVP |

### 7.2 Para agregar nueva industria

1. Crear template EIA en `/docs/TEMPLATE_EIA_[SECTOR].md`
2. Insertar en `tipos_proyecto` y `subtipos_proyecto`
3. Insertar umbrales en `umbrales_seia`
4. Insertar PAS típicos en `pas_por_tipo`
5. Insertar normativa en `normativa_por_tipo`
6. Insertar preguntas en `arboles_preguntas`

**No se requiere cambio de código.**

---

## 8. Dependencias Técnicas

### Sistemas existentes a reutilizar
- Análisis GIS: `/api/v1/gis/analisis-espacial`
- RAG Legal: `/api/v1/legal/buscar`
- Ingestor documentos
- Claude Sonnet 4

### Nuevas dependencias
| Componente | Propósito | Opción |
|------------|-----------|--------|
| OCR | Documentos escaneados | Claude Vision |
| Parser XLS | Planillas | openpyxl |
| Generador PDF | Exportación | WeasyPrint |

---

## 9. Riesgos y Mitigaciones

| Riesgo | Mitigación |
|--------|------------|
| Contexto LLM crece mucho | Resúmenes automáticos |
| Configuración por industria compleja | UI de administración |
| Umbrales SEIA cambian | Tabla editable, no código |
| OCR de gráficos | Claude Vision para interpretar |

---

## 10. Métricas de Éxito

### Fase 1
- Tiempo para diagnóstico: < 30 min interacción
- % proyectos con análisis GIS: 100%
- Agregar nueva industria: < 2 horas (solo datos)

### Fases 2-4
- % campos EIA pre-llenados: > 40%
- Reducción tiempo preparación: > 30%

---

## 11. Documentación Relacionada

- **ARQUITECTURA_ASISTENTE.md**: Estructura técnica, servicios, endpoints
- **MODELO_DATOS_ASISTENTE.md**: Tablas, SQL, datos iniciales
- **METODOLOGIA_TEMPLATES_EIA.md**: Cómo crear templates por industria
- **TEMPLATE_EIA_MINERIA.md**: Template de referencia

---

*Documento actualizado: Enero 2026*
*Sistema de Prefactibilidad Ambiental*
