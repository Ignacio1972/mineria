# Análisis de Cobertura EIA en el Sistema de Prefactibilidad

**Fecha:** 2026-01-06
**Autor:** Claude Code
**Propósito:** Comparar la estructura completa del EIA (Art. 18 DS 40) con lo que actualmente cubre el sistema.

---

## Resumen Ejecutivo

El sistema actual tiene **DOS SUBSISTEMAS SEPARADOS**:

1. **Análisis de Prefactibilidad** (Análisis Rápido/Completo) → Determina DIA vs EIA
2. **Generación de EIA** (Tab "Generación") → Genera el documento EIA completo

**Conclusión:** El análisis rápido/completo **NO** está tomando en cuenta la estructura completa del EIA de 17 componentes. Solo genera 10 secciones de prefactibilidad.

---

## 1. Estructura Actual del Análisis de Prefactibilidad

### Secciones que genera actualmente (10 secciones):

```python
# Ubicación: backend/app/services/llm/generador.py:23-35

class SeccionInforme(str, Enum):
    RESUMEN_EJECUTIVO = "resumen_ejecutivo"
    DESCRIPCION_PROYECTO = "descripcion_proyecto"
    ANALISIS_TERRITORIAL = "analisis_territorial"
    EVALUACION_SEIA = "evaluacion_seia"
    NORMATIVA_APLICABLE = "normativa_aplicable"
    ALERTAS_AMBIENTALES = "alertas_ambientales"
    PERMISOS_REQUERIDOS = "permisos_requeridos"
    LINEA_BASE_SUGERIDA = "linea_base_sugerida"
    RECOMENDACIONES = "recomendaciones"
    CONCLUSION = "conclusion"
```

### Diferencia: Análisis Rápido vs Completo

- **Análisis Rápido**: Solo ejecuta GIS + Motor de Reglas (2-5 seg, sin LLM)
- **Análisis Completo**: GIS + Motor de Reglas + RAG + **Genera las 10 secciones con LLM** (30-60 seg)

**Problema identificado:** Ninguno de los dos considera los 17 componentes del EIA completo.

---

## 2. Estructura Completa del EIA según Art. 18 DS 40

### Componentes del EIA (17 elementos principales):

| # | Componente | ¿Cubierto en Análisis? | ¿Cubierto en Generación? |
|---|-----------|------------------------|--------------------------|
| 1 | Índice y Resumen | ✅ Parcial (RESUMEN_EJECUTIVO) | ✅ Sí |
| 2 | Descripción del Proyecto | ✅ Parcial (DESCRIPCION_PROYECTO) | ✅ Sí (Cap. 1) |
| 3 | Área de Influencia | ❌ No | ✅ Sí (Cap. 2) |
| 4 | Línea de Base | ⚠️ Solo "sugerida" | ✅ Sí (Cap. 3) |
| 5 | Predicción y Evaluación de Impactos | ❌ No | ✅ Sí (Cap. 4) |
| 6 | Descripción de Efectos Art. 11 | ✅ Parcial (EVALUACION_SEIA) | ❌ No explícito |
| 7 | Capítulo de Riesgo a la Salud | ❌ No | ❌ No explícito |
| 8 | Plan de Mitigación/Reparación/Compensación | ❌ No | ✅ Sí (Cap. 5) |
| 9 | Plan de Prevención de Contingencias | ❌ No | ✅ Sí (Cap. 6) |
| 10 | Plan de Seguimiento Ambiental | ❌ No | ✅ Sí (Cap. 7) |
| 11 | Plan de Cumplimiento Legislación | ✅ Parcial (NORMATIVA_APLICABLE) | ❌ No explícito |
| 12 | Permisos Ambientales Sectoriales (PAS) | ✅ Parcial (PERMISOS_REQUERIDOS) | ❌ No explícito |
| 13 | Compromisos Ambientales Voluntarios | ❌ No | ✅ Sí (Cap. 10) |
| 14 | Monitoreo Participativo | ❌ No | ❌ No explícito |
| 15 | Fichas Resumen por Fase | ❌ No | ✅ Sí (Cap. 11) |
| 16 | Acciones Previas de Consulta Ciudadana | ❌ No | ✅ Parcial (Cap. 8) |
| 17 | Apéndices y Anexos | ❌ No | ⚠️ Parcial (modelo Anexo existe) |

---

## 3. Sistema de Generación de EIA (Tab "Generación")

### Capítulos del EIA generados (11 capítulos):

```python
# Ubicación: backend/app/services/generacion_eia/service.py:52-64

CAPITULOS_EIA = {
    1: "Descripción del Proyecto",
    2: "Determinación y Justificación del Área de Influencia",
    3: "Línea de Base",
    4: "Predicción y Evaluación de Impactos Ambientales",
    5: "Plan de Medidas de Mitigación, Reparación y Compensación",
    6: "Plan de Prevención de Contingencias y Emergencias",
    7: "Plan de Seguimiento Ambiental",
    8: "Descripción de la Participación Ciudadana",
    9: "Relación con Políticas, Planes y Programas",
    10: "Compromisos Ambientales Voluntarios",
    11: "Ficha Resumen del EIA"
}
```

**Este sistema SÍ cubre la estructura completa del EIA**, pero está **separado** del análisis de prefactibilidad.

---

## 4. Flujo Actual del Sistema

```
Usuario aprieta "Análisis Rápido"
    ↓
1. Análisis GIS (intersecciones con capas)
2. Motor de Reglas SEIA (triggers Art. 11)
3. Sistema de Alertas
4. NO genera informe con LLM
    ↓
Resultado: Clasificación DIA/EIA + Alertas
```

```
Usuario aprieta "Análisis Completo"
    ↓
1. Análisis GIS
2. Motor de Reglas SEIA
3. Sistema de Alertas
4. Búsqueda RAG (normativa)
5. Generación de 10 secciones con LLM
    ↓
Resultado: Informe de prefactibilidad (10 secciones)
```

**LUEGO, en otro tab:**

```
Usuario va a tab "Generación"
    ↓
Sistema de Generación de EIA
    ↓
Genera los 11 capítulos del EIA completo
```

---

## 5. Gap Identificado

### ❌ Problema Principal:

El **análisis de prefactibilidad NO está recopilando material** para todos los componentes del EIA completo.

### Qué falta en el análisis:

1. **Área de Influencia** - No se delimita por componente ambiental
2. **Línea de Base Completa** - Solo se "sugiere", no se recopila material
3. **Predicción de Impactos** - No se hace modelación ni predicción cuantitativa
4. **Planes de Manejo** - No se recopila info para mitigación, contingencias, seguimiento
5. **Participación Ciudadana** - No se documenta
6. **Fichas por Fase** - No se generan

### ⚠️ Consecuencia:

Cuando el usuario va a "Generación" (tab aparte), el sistema **no tiene suficiente información recopilada** para generar los 11 capítulos del EIA de manera robusta.

---

## 6. Recomendaciones

### Opción 1: Integrar análisis profundo con recopilación EIA

Hacer que el **"Análisis Completo"** además de clasificar DIA/EIA:

1. Identifique qué componentes de línea de base necesita el proyecto
2. Recopile información del corpus RAG para cada componente
3. Genere fichas de datos por componente ambiental
4. Almacene esta información en la BD para uso posterior en "Generación"

**Archivos a modificar:**
- `backend/app/services/prefactibilidad/service.py` - Añadir recopilación de componentes
- `backend/app/services/llm/generador.py` - Expandir secciones a generar
- `backend/app/db/models/proyecto.py` - Añadir campo para material recopilado

### Opción 2: Sistema de recopilación intermedio (ya existe parcialmente)

El tab "Recopilación" parece diseñado para esto. Fortalecerlo como:

```
Análisis Completo → Recopilación → Generación
       ↓               ↓              ↓
   Clasifica      Recopila        Genera
   DIA/EIA        Material        EIA Final
```

**Archivos a revisar:**
- `frontend/src/components/asistente/recopilacion/RecopilacionCapitulo.vue`
- `backend/app/services/asistente/` - Tools de recopilación

### Opción 3: Checklist de componentes en el análisis

Añadir al análisis completo un **checklist de 17 componentes** que:

1. Identifique qué componentes necesita el proyecto
2. Busque en el corpus RAG material relevante para cada uno
3. Marque como "con material" o "sin material"
4. Permita al usuario revisar qué le falta

---

## 7. Próximos Pasos Sugeridos

1. ✅ **Entender la funcionalidad actual del tab "Recopilación"**
   - Leer `RecopilacionCapitulo.vue`
   - Ver qué herramientas del asistente usa

2. **Decidir la estrategia:**
   - ¿Integrar en análisis completo?
   - ¿Fortalecer tab recopilación?
   - ¿Crear flujo híbrido?

3. **Implementar recopilación por componente:**
   - Crear servicio `RecopilacionComponentesService`
   - Integrar con RAG para buscar material por componente
   - Almacenar en BD para uso en Generación

4. **Testing:**
   - Probar flujo completo: Análisis → Recopilación → Generación
   - Verificar que cada capítulo del EIA tiene material suficiente

---

## Conclusión

**Respuesta a tu pregunta:**

> "¿En el análisis rápido o el análisis profundo, se están tomando en cuenta los siguientes ítems [17 componentes del EIA]?"

**NO**, el análisis actual (rápido ni completo) NO está tomando en cuenta todos los 17 componentes del EIA. Solo cubre aproximadamente **6-7 de los 17 componentes**, y de forma parcial.

El sistema **SÍ tiene** la capacidad de generar los 11 capítulos del EIA (en el tab "Generación"), pero **NO está recopilando material** de forma sistemática durante el análisis para alimentar esa generación.

**Recomendación:** Fortalecer el flujo de recopilación intermedio entre el análisis y la generación, posiblemente expandiendo el tab "Recopilación" para que sea el puente que busque y almacene material del corpus RAG para cada uno de los 17 componentes del EIA.
