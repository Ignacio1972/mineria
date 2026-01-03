# Auditoría del Asistente IA - Enero 2026

**Fecha:** 2026-01-02
**Auditor:** Claude Code
**Versión del Sistema:** 1.0.0 (commit 6b4a753)

---

## Resumen Ejecutivo

| Severidad | Total | Resueltos | Pendientes |
|-----------|-------|-----------|------------|
| Crítico   | 3     | 3         | 0          |
| Importante | 5    | 3         | 2          |
| Menor     | 3     | 1         | 2          |

**Bugs resueltos:** BUG-001, BUG-002, BUG-003, BUG-004, BUG-005, BUG-008, BUG-010

---

## Bugs Pendientes

### BUG-006: AccionPendiente sin referencia a proyecto [IMPORTANTE]

**Ubicación:** `backend/app/db/models/asistente.py`

La tabla `asistente.acciones_pendientes` no tiene FK a `proyectos.proyectos`.

**Solución:** Agregar columna `proyecto_id` con FK y crear migración Alembic.

---

### BUG-007: Session ID sin protección [MENOR]

**Ubicación:** `frontend/src/stores/asistente.ts:22-30`

El `session_id` se almacena en localStorage sin protección ni expiración.

---

### BUG-009: Patrones de prompt injection muy básicos [MENOR]

**Ubicación:** `backend/app/services/asistente/service.py:91-98`

Los patrones regex de sanitización son fáciles de evadir.

---

### BUG-011: Proyecto no se asocia automáticamente a conversación [IMPORTANTE]

**Ubicación:** `backend/app/services/asistente/tools/consultas.py`

**Problema:**
Cuando el usuario menciona un proyecto por nombre (ej: "qué sabes del proyecto Colico"), el asistente usa las herramientas `listar_proyectos` o `consultar_proyecto` para buscarlo, pero **no actualiza** el `proyecto_activo_id` de la conversación.

**Comportamiento actual:**
- `proyecto_activo_id` solo se establece si el usuario navega desde la vista de un proyecto o pasa `?proyecto=ID` en la URL
- Las herramientas de consulta no modifican el contexto de la conversación

**Comportamiento esperado:**
Cuando el asistente consulta un proyecto específico, debería asociarlo automáticamente a la conversación para que:
1. La conversación aparezca vinculada al proyecto en el historial
2. El contexto se mantenga para preguntas de seguimiento

**Solución propuesta:**
Modificar las herramientas `consultar_proyecto` y `listar_proyectos` para que retornen el `proyecto_id` en metadata, y que el servicio del asistente actualice `conversacion.proyecto_activo_id` cuando detecte que se consultó un proyecto específico.

---

## Estado de Herramientas

| Herramienta | Estado |
|-------------|--------|
| buscar_normativa | ✅ OK |
| consultar_proyecto | ✅ OK |
| crear_proyecto | ✅ OK |
| ejecutar_analisis | ✅ OK |
| actualizar_proyecto | ✅ OK |

---

---

## Bugs Resueltos (Detalle)

### BUG-010: Asistente responde sin consultar corpus RAG [CRÍTICO] ✅ RESUELTO

**Fecha detección:** 2026-01-02
**Fecha resolución:** 2026-01-02

**Problema:**
El asistente respondía preguntas sobre normativa (ej: "¿cuáles son los requisitos mínimos de tonelaje para ingresar al SEIA?") usando su conocimiento general en lugar de consultar el corpus legal. Esto causó respuestas erróneas como afirmar que "NO existen umbrales mínimos de toneladas" cuando el corpus claramente establece el umbral de **5,000 toneladas mensuales**.

**Evidencia:**
- Fragmento #1945 del documento 25 (Guía para proyectos de cobre y oro-plata) contiene: *"capacidad de extracción de mineral sea superior a cinco mil toneladas mensuales (5.000 t/mes)"*
- El asistente no usó la herramienta `buscar_normativa` antes de responder

**Causa raíz:**
El `SYSTEM_PROMPT_BASE` en `service.py` no obligaba al asistente a usar la herramienta `buscar_normativa` ANTES de responder preguntas sobre normativa.

**Solución implementada:**
Se agregó la sección "VERIFICACIÓN OBLIGATORIA - REGLA CRÍTICA" al system prompt que:
1. Lista explícitamente los temas que requieren consulta al corpus (14 categorías)
2. Prohíbe responder desde conocimiento general sobre normativa chilena
3. Establece protocolo cuando no se encuentra información

**Refuerzo adicional - Guías, Instructivos y Criterios:**
Se agregó sección "IMPORTANCIA DE LAS GUÍAS, INSTRUCTIVOS Y CRITERIOS SEA" que enfatiza:
- El corpus tiene 125+ Guías SEA, 28+ Criterios SEA, 12+ Instructivos
- Estos documentos contienen la interpretación OFICIAL del SEA
- Incluyen datos específicos (umbrales, plazos, metodologías) que NO están en las leyes base
- Ejemplo explícito: "El umbral de 5.000 t/mes para proyectos mineros está en la Guía SEA, no en la Ley 19.300"

**Archivo modificado:** `backend/app/services/asistente/service.py:74-106`

---

### MEJORA-001: Búsqueda RAG en dos pasos [IMPLEMENTADO]

**Fecha:** 2026-01-02

**Motivación:**
Las Guías SEA, Criterios e Instructivos son más importantes que las leyes base porque contienen la interpretación oficial del SEA con datos específicos (umbrales, plazos, metodologías).

**Implementación:**
Se modificó la herramienta `buscar_normativa` para usar búsqueda en dos pasos:

1. **Paso 1 (70% resultados):** Busca primero en tipos prioritarios:
   - Guía SEA, Criterio SEA, Instructivo, Instructivo SEA, Criterio, Manual

2. **Paso 2 (30% resultados):** Complementa con tipos base:
   - Ley, Reglamento

**Resultados verificados:**
```
Query: "requisitos minimos tonelaje proyectos mineros SEIA"

Paso 1 (Prioritarios):
- Fragmento 1945 (Guía SEA) - Similitud 0.796 - "5.000 t/mes" ✓
- Fragmento 5639 (Guía SEA) - Similitud 0.636
- Fragmento 5640 (Guía SEA) - Similitud 0.581

Paso 2 (Base):
- Fragmento 26 (Reglamento) - Similitud 0.396
- Fragmento 23 (Ley) - Similitud 0.298
```

**Nuevos parámetros de la herramienta:**
- `top_k`: Ahora default 8 (antes 5)
- `solo_prioritarios`: Boolean para buscar solo en Guías/Criterios/Instructivos
- Respuesta incluye `es_prioritario` por fragmento y `metodo_busqueda`

**Archivo modificado:** `backend/app/services/asistente/tools/rag.py:23-252`

---

*Actualizado: 2026-01-02*
