# Workflow Integrado de Generación de EIA

**Fecha:** 2026-01-06
**Versión:** 1.0
**Estado:** Planificación

---

## Problema Actual

El sistema tiene **4 herramientas poderosas pero desconectadas**:

1. **Análisis Rápido/Completo** - Clasifica DIA vs EIA
2. **Asistente Conversacional** - Auto-llena datos básicos del proyecto
3. **Tab "Recopilación"** - Formularios estructurados por capítulos
4. **Tab "Generación"** - Genera el EIA final

**Gap Identificado:** No hay un flujo claro que conecte estas herramientas. El usuario no sabe cuál usar, cuándo, ni cómo se alimentan entre sí.

---

## Solución Propuesta

**Pipeline de 5 fases secuenciales** donde cada etapa alimenta la siguiente:

```
Identificación → Prefactibilidad → Recopilación → Generación → Refinamiento
```

Cada fase tiene un objetivo claro, herramientas específicas, y genera salidas que alimentan la siguiente fase.

---

## Workflow Completo

```
┌─────────────────────────────────────────────────────────────────┐
│  FASE 1: IDENTIFICACIÓN                                         │
│  ────────────────────────────────────────────────────────────── │
│  Herramienta: Asistente Conversacional                          │
│  Objetivo: Datos básicos del proyecto                           │
│  Duración: 5-10 min                                             │
│  Salida: 10 campos clave + geometría + ficha acumulativa        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  FASE 2: PREFACTIBILIDAD                                        │
│  ────────────────────────────────────────────────────────────── │
│  Herramienta: Análisis Completo (LLM + GIS + RAG)              │
│  Objetivo: Clasificar DIA/EIA + identificar componentes         │
│  Duración: 30-60 seg                                            │
│  Salida: Informe 10 secciones + checklist 17 componentes EIA   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  FASE 3: RECOPILACIÓN GUIADA ⭐ (NUEVA)                         │
│  ────────────────────────────────────────────────────────────── │
│  Herramienta: Tab Recopilación + Asistente Híbrido             │
│  Objetivo: Recopilar material para los 17 componentes          │
│  Duración: Variable (horas/días)                                │
│  Salida: Base de datos estructurada lista para generación      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  FASE 4: GENERACIÓN BORRADOR                                    │
│  ────────────────────────────────────────────────────────────── │
│  Herramienta: Tab Generación (usa datos de Fase 3)             │
│  Objetivo: Generar los 11 capítulos del EIA                     │
│  Duración: 3-5 min                                              │
│  Salida: Documento EIA completo con 11 capítulos                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  FASE 5: REFINAMIENTO                                           │
│  ────────────────────────────────────────────────────────────── │
│  Herramienta: Editor + Asistente (modo revisión)               │
│  Objetivo: Ajustar, validar y exportar                          │
│  Duración: Variable                                             │
│  Salida: EIA final listo para SEIA                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## Fases de Implementación

### FASE 1: Checklist de Componentes (Base del flujo)
**Objetivo:** Que el análisis completo genere un checklist de los 17 componentes EIA
**Complejidad:** Media
**Impacto:** Alto

**¿Qué se hace?**
- Modificar el análisis completo para que además de las 10 secciones actuales, genere un checklist de componentes
- Buscar en RAG material inicial para cada componente según el proyecto
- Almacenar este checklist en BD para uso en Fase 3

**Criterio de éxito:**
- Al finalizar análisis completo, el proyecto tiene un checklist de componentes con material RAG sugerido

---

### FASE 2: Dashboard de Progreso Integral
**Objetivo:** Mostrar el avance del proyecto a través de las 5 fases
**Complejidad:** Baja
**Impacto:** Medio

**¿Qué se hace?**
- Crear componente `ProgresoIntegral.vue` que muestre las 5 fases
- Indicador visual de completitud por fase
- Botones contextuales según la fase actual

**Criterio de éxito:**
- Usuario ve claramente en qué fase está y qué sigue

---

### FASE 3: Recopilación Híbrida (核心/Core)
**Objetivo:** Integrar el asistente dentro del tab "Recopilación"
**Complejidad:** Alta
**Impacto:** Muy Alto

**¿Qué se hace?**
- Modificar `RecopilacionCapitulo.vue` para tener vista dividida: formulario + asistente
- Crear herramienta del asistente `buscar_material_capitulo()` que busca en RAG
- Asistente sugiere contenido mientras el usuario llena formularios
- Usuario puede aceptar/editar/rechazar sugerencias

**Criterio de éxito:**
- Usuario puede llenar manualmente O conversar con asistente
- Asistente sugiere material del corpus RAG relevante
- Ambos métodos alimentan la misma estructura de datos

---

### FASE 4: Conexión Análisis → Recopilación
**Objetivo:** Que el checklist de Fase 1 alimente la Fase 3
**Complejidad:** Media
**Impacto:** Alto

**¿Qué se hace?**
- Al abrir tab "Recopilación", cargar el checklist del análisis
- Pre-poblar con material RAG ya identificado
- Marcar componentes como "con material" o "pendientes"

**Criterio de éxito:**
- Usuario no parte de cero en recopilación
- Tiene sugerencias basadas en el análisis

---

### FASE 5: Conexión Recopilación → Generación
**Objetivo:** Que la generación use datos estructurados de recopilación
**Complejidad:** Media
**Impacto:** Muy Alto

**¿Qué se hace?**
- Modificar servicio de generación para leer de `proyecto_caracteristicas` y respuestas de recopilación
- Validar que hay suficiente material antes de generar
- Mostrar advertencias si faltan componentes críticos

**Criterio de éxito:**
- EIA generado es sustancialmente más completo
- Usuario sabe qué falta antes de generar

---

## Plan de Implementación Sugerido

### Orden Recomendado

**Sprint 1: Base (Fases 1 + 2)**
1. Checklist de componentes en análisis completo
2. Dashboard de progreso integral
3. Testing de flujo básico

**Sprint 2: Core (Fase 3)**
4. Recopilación híbrida (formulario + asistente)
5. Herramienta `buscar_material_capitulo`
6. Testing de sugerencias RAG

**Sprint 3: Integración (Fases 4 + 5)**
7. Conectar análisis → recopilación
8. Conectar recopilación → generación
9. Testing end-to-end completo

---

## Métricas de Éxito

**Proceso:**
- ✅ Usuario completa las 5 fases sin confusión
- ✅ Cada fase muestra progreso claro
- ✅ No hay "callejones sin salida"

**Calidad:**
- ✅ EIA generado tiene >80% de componentes completos
- ✅ Material RAG es relevante (confianza >0.7)
- ✅ Usuario puede generar EIA en <2 horas (vs días manual)

**Adopción:**
- ✅ >70% de usuarios usan asistente en recopilación
- ✅ >80% completan al menos Fase 3

---

## Cambios en el Modelo de Datos

### Tabla: `proyectos.componentes_eia_checklist` (NUEVA)

```sql
CREATE TABLE proyectos.componentes_eia_checklist (
    id SERIAL PRIMARY KEY,
    proyecto_id INTEGER REFERENCES proyectos.proyectos(id),
    componente VARCHAR(100),  -- ej: "linea_base_flora_fauna"
    capitulo INTEGER,          -- 1-11
    requerido BOOLEAN,
    prioridad VARCHAR(20),     -- 'alta' | 'media' | 'baja'
    estado VARCHAR(20),        -- 'pendiente' | 'en_progreso' | 'completado'
    progreso_porcentaje INTEGER DEFAULT 0,
    material_rag JSONB,        -- Array de documentos del corpus
    sugerencias_busqueda JSONB, -- Array de strings
    fecha_analisis TIMESTAMP,
    fecha_actualizacion TIMESTAMP DEFAULT NOW()
);
```

### Modificación: `proyectos.proyectos`

```sql
ALTER TABLE proyectos.proyectos ADD COLUMN fase_actual VARCHAR(50) DEFAULT 'identificacion';
-- Valores: 'identificacion' | 'prefactibilidad' | 'recopilacion' | 'generacion' | 'refinamiento'

ALTER TABLE proyectos.proyectos ADD COLUMN progreso_global INTEGER DEFAULT 0;
-- Porcentaje 0-100
```

---

## Notas de Diseño

### Principios Clave

1. **Progresión No-Lineal:** Usuario puede saltar fases si tiene datos (ej: ya tiene un proyecto antiguo)
2. **Trazabilidad Total:** Cada dato sabe de dónde viene (manual, asistente, RAG, GIS)
3. **Flexibilidad:** No forzar el uso del asistente, siempre permitir manual
4. **Feedback Visual:** Progreso claro, advertencias útiles, celebración de hitos

### UX Crítico

- **Banner inteligente:** "Completaste el análisis. ¿Continuar con recopilación?"
- **Bloques desbloqueables:** No permitir generación sin mínimo 60% recopilación
- **Checkpoints:** Guardar automáticamente, permitir pausar/reanudar

---

## Próximos Pasos

1. **Validar este plan** con stakeholders
2. **Definir Sprint 1** con tareas específicas
3. **Prototipar** dashboard de progreso (mockup)
4. **Diseñar prompts** para búsqueda RAG contextual

---

## Anexo: Componentes EIA (17 elementos)

```
1.  Resumen Ejecutivo
2.  Descripción del Proyecto
3.  Área de Influencia
4.  Línea de Base (flora, fauna, suelo, agua, aire, patrimonio, socioeconómico)
5.  Predicción y Evaluación de Impactos
6.  Descripción de Efectos Art. 11
7.  Riesgo a la Salud
8.  Plan de Mitigación/Reparación/Compensación
9.  Plan de Prevención de Contingencias
10. Plan de Seguimiento Ambiental
11. Plan de Cumplimiento Legislación
12. Permisos Ambientales Sectoriales (PAS)
13. Compromisos Ambientales Voluntarios
14. Monitoreo Participativo
15. Fichas Resumen por Fase
16. Participación Ciudadana
17. Apéndices y Anexos
```

Cada uno de estos componentes debe tener:
- Material del corpus RAG
- Datos específicos del proyecto
- Estado de completitud
