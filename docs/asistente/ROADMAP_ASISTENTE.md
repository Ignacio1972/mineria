# Roadmap: Sistema de Asistente Inteligente por Proyecto

> **Versión:** 1.1 | **Fecha:** Enero 2026 | **Actualización:** Soporte multi-industria

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
│  FASE 1                FASE 2                FASE 3              FASE 4     │
│  Prefactibilidad       Estructuración        Recopilación        Generación │
│  + Multi-industria     EIA                   Guiada              EIA        │
│                                                                             │
│  ┌──────────┐         ┌──────────┐          ┌──────────┐       ┌──────────┐ │
│  │ Asistente│         │ Template │          │ Capítulo │       │ Documento│ │
│  │ + Config │────────►│ + PAS    │─────────►│ por      │──────►│ Final    │ │
│  │ Industria│         │ + Anexos │          │ Capítulo │       │ + Export │ │
│  └──────────┘         └──────────┘          └──────────┘       └──────────┘ │
│                                                                             │
│  MVP                   v1.1                  v1.2                v2.0       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Fase 1: Prefactibilidad + Multi-industria (MVP)

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

- [ ] Usuario selecciona tipo/subtipo y recibe preguntas específicas
- [ ] Sistema evalúa umbrales SEIA automáticamente
- [ ] Sistema identifica PAS aplicables según características
- [ ] Al subir ubicación, ejecuta análisis GIS
- [ ] Genera diagnóstico preliminar con justificación
- [ ] Usuario puede retomar conversación después de días
- [ ] Agregar nueva industria = solo insertar datos en BD

---

## 4. Fase 2: Estructuración EIA

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

## 5. Fase 3: Recopilación Guiada

### 5.1 Objetivo
Guiar capítulo por capítulo, validando completitud.

### 5.2 Funcionalidades

| ID | Funcionalidad |
|----|---------------|
| F3.1 | Navegación por capítulos del EIA |
| F3.2 | Validación de completitud por sección |
| F3.3 | Extracción de datos de estudios técnicos (OCR + IA) |
| F3.4 | Detección de inconsistencias entre capítulos |
| F3.5 | Sugerencias de redacción |

---

## 6. Fase 4: Generación de EIA

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
