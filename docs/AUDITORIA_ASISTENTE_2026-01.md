# Auditoría del Asistente IA - Enero 2026

**Fecha:** 2026-01-02
**Auditor:** Claude Code
**Versión del Sistema:** 1.0.0 (commit a11d7bb)

---

## Resumen Ejecutivo

Se realizó una auditoría completa del módulo Asistente IA (`/asistente`) con foco en:
- Funcionamiento general del chat con tool use
- **Conexión con proyectos e informes del sistema**
- Flujo de confirmación de acciones
- Gestión de contexto entre vistas

### Resultados

| Severidad | Cantidad | Estado |
|-----------|----------|--------|
| Crítico   | 2        | Pendiente |
| Importante | 4       | Pendiente |
| Menor     | 3        | Pendiente |

---

## Arquitectura Actual

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (Vue 3)                         │
│  AsistenteView.vue → useAsistenteStore → asistenteService   │
│                           ↓                                 │
│              proyectoContextoId (ref)                       │
└─────────────────────────────────────────────────────────────┘
                            │
                   POST /api/v1/asistente/chat
                   { proyecto_contexto_id: number }
                            │
┌─────────────────────────────────────────────────────────────┐
│                    BACKEND (FastAPI)                        │
│  AsistenteService → GestorContexto → Claude API             │
│                           ↓                                 │
│  Herramientas: CrearProyecto, EjecutarAnalisis, etc.        │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                    BASE DE DATOS                            │
│  asistente.conversaciones ←→ proyectos.proyectos            │
│  asistente.acciones_pendientes                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Bugs Identificados

### BUG-001: EjecutarAnalisis no ejecuta el análisis [CRÍTICO]

**Ubicación:** `backend/app/services/asistente/tools/acciones.py:477-496`

**Descripción:**
La herramienta `EjecutarAnalisis` está implementada como placeholder. Cuando el usuario confirma la acción, el análisis de prefactibilidad **nunca se ejecuta realmente**.

**Código actual:**
```python
async def ejecutar(self, proyecto_id: int, tipo_analisis: str = "completo", ...):
    # ... validaciones ...

    # Aqui se llamaria al servicio de prefactibilidad
    # Por ahora retornamos un placeholder indicando que la accion fue aceptada
    # La ejecucion real se hara cuando se implemente el AsistenteService

    return ResultadoHerramienta(
        exito=True,
        contenido={
            "proyecto_id": proyecto_id,
            "estado": "pendiente_ejecucion",  # ← NUNCA CAMBIA
            "mensaje": f"Analisis '{tipo_analisis}' programado...",
            "nota": "El analisis se ejecutara al confirmar la accion",
        },
    )
```

**Impacto:**
- El usuario confirma "Ejecutar análisis" pero nada sucede
- El proyecto no cambia de estado
- No se genera ningún informe de prefactibilidad
- La funcionalidad principal del asistente está rota

**Flujo afectado:**
```
Usuario: "Analiza mi proyecto"
   ↓
Claude: tool_use(ejecutar_analisis, {proyecto_id: 123})
   ↓
Sistema: Muestra panel de confirmación
   ↓
Usuario: Confirma ✓
   ↓
Sistema: Retorna "pendiente_ejecucion" ← NUNCA EJECUTA
   ↓
Usuario: Espera resultados que nunca llegan
```

---

### BUG-002: Contexto no se actualiza después de acciones [CRÍTICO]

**Ubicación:** `backend/app/services/asistente/service.py:973-993`

**Descripción:**
Las sugerencias se generan con el contexto obtenido al **inicio** del request. Si durante la conversación se crea un proyecto o se ejecuta un análisis, las sugerencias no reflejan el nuevo estado.

**Código actual:**
```python
async def chat(self, request: ChatRequest) -> ChatResponse:
    # Contexto se obtiene UNA VEZ al inicio
    contexto = await self.gestor_contexto.obtener_contexto(...)

    # ... se ejecutan herramientas que pueden modificar el proyecto ...

    # Sugerencias usan contexto OBSOLETO
    return ChatResponse(
        sugerencias=self._generar_sugerencias(contexto, respuesta_final),
    )

def _generar_sugerencias(self, contexto, respuesta):
    if contexto.proyecto_id:
        if not contexto.proyecto_tiene_analisis:  # ← Valor obsoleto
            sugerencias.append("Ejecutar analisis de prefactibilidad")
```

**Impacto:**
- Usuario crea proyecto → Sugerencia sigue siendo "Crear nuevo proyecto"
- Usuario ejecuta análisis → Sugerencia sigue siendo "Ejecutar análisis"
- Confunde al usuario sobre el estado real del sistema

---

### BUG-003: Contexto de proyecto se pierde al navegar [IMPORTANTE]

**Ubicación:** `frontend/src/views/AsistenteView.vue:140-147`

**Descripción:**
Cuando el usuario navega desde `/proyectos/123` a `/asistente`, el contexto del proyecto no se preserva. El `proyectoContextoId` solo se establece si existe un composable `useAsistente` activo.

**Código actual:**
```typescript
// AsistenteView.vue
onMounted(async () => {
  store.setVistaActual('asistente')
  // ← NO sincroniza proyectoContextoId desde la ruta anterior
  await Promise.all([
    store.cargarConversaciones(),
    store.cargarNotificaciones(),
    store.cargarHerramientas(),
  ])
})
```

**Impacto:**
- El asistente "olvida" en qué proyecto estaba trabajando el usuario
- Las respuestas no tienen contexto del proyecto
- El usuario debe mencionar explícitamente el proyecto cada vez

**Flujo afectado:**
```
Usuario en /proyectos/123/detalle
   ↓
Navega a /asistente
   ↓
proyectoContextoId = null ← Se perdió el contexto
   ↓
Usuario: "Ejecuta el análisis"
   ↓
Asistente: "¿De qué proyecto?" ← No sabe cuál
```

---

### BUG-004: Descripción de acciones no muestra nombre del proyecto [IMPORTANTE]

**Ubicación:** `backend/app/services/asistente/tools/acciones.py:506-510`

**Descripción:**
El método `generar_descripcion_confirmacion()` solo muestra el ID del proyecto, no su nombre. El usuario ve "Ejecutar análisis para proyecto ID 123" en lugar de "Ejecutar análisis para 'Proyecto Minero Atacama'".

**Código actual:**
```python
def generar_descripcion_confirmacion(self, **kwargs) -> str:
    proyecto_id = kwargs.get("proyecto_id", "?")
    tipo = kwargs.get("tipo_analisis", "completo")
    return f"Ejecutar analisis {tipo} para proyecto ID {proyecto_id}"
    # ← Solo muestra ID, no nombre
```

**Impacto:**
- Usuario no sabe a qué proyecto se refiere la acción
- Riesgo de confirmar acción sobre proyecto equivocado
- Mala experiencia de usuario

---

### BUG-005: Conversaciones no muestran proyecto asociado [IMPORTANTE]

**Ubicación:** `frontend/src/stores/asistente.ts:138-150`

**Descripción:**
El historial de conversaciones no indica a qué proyecto pertenece cada conversación, aunque el backend sí almacena `proyecto_activo_id`.

**Código actual:**
```typescript
// Al crear conversación local
conversacionActual.value = {
  id: respuesta.conversacion_id,
  session_id: sessionId.value,
  titulo: contenido.substring(0, 50),
  // ← No incluye proyecto_activo_id ni proyecto_nombre
}
```

**Impacto:**
- Lista de conversaciones no indica contexto
- Usuario no puede filtrar conversaciones por proyecto
- Difícil encontrar conversaciones anteriores sobre un proyecto específico

---

### BUG-006: AccionPendiente sin referencia a proyecto [IMPORTANTE]

**Ubicación:** `backend/app/db/models/asistente.py` (modelo AccionPendiente)

**Descripción:**
La tabla `asistente.acciones_pendientes` no tiene FK a `proyectos.proyectos`. No hay forma de auditar qué acciones se ejecutaron sobre qué proyecto.

**Estructura actual:**
```python
class AccionPendiente(Base):
    __tablename__ = "acciones_pendientes"

    id = Column(UUID)
    conversacion_id = Column(UUID, ForeignKey("asistente.conversaciones.id"))
    tipo = Column(String)
    parametros = Column(JSON)  # ← proyecto_id está aquí, enterrado en JSON
    # ← Falta: proyecto_id = Column(Integer, ForeignKey("proyectos.proyectos.id"))
```

**Impacto:**
- No se puede consultar "acciones pendientes del proyecto X"
- No hay auditoría de acciones por proyecto
- Difícil rastrear qué cambios se hicieron a un proyecto vía asistente

---

### BUG-007: Session ID sin protección [MENOR]

**Ubicación:** `frontend/src/stores/asistente.ts:22-30`

**Descripción:**
El `session_id` se almacena en localStorage sin ninguna protección. Un atacante podría extraerlo y suplantar la sesión.

**Código actual:**
```typescript
const getSessionId = (): string => {
  const stored = localStorage.getItem('asistente_session_id')
  if (stored) return stored
  const newId = uuidv4()
  localStorage.setItem('asistente_session_id', newId)  // ← Texto plano
  return newId
}
```

**Impacto:**
- Riesgo de suplantación de sesión (bajo en entorno interno)
- No hay expiración de sesión

---

### BUG-008: Límite de iteraciones sin aviso [MENOR]

**Ubicación:** `backend/app/services/asistente/service.py:86, 891-893`

**Descripción:**
Si Claude necesita más de 10 iteraciones de tool use, el loop se corta silenciosamente y la respuesta puede estar incompleta.

**Código actual:**
```python
MAX_TOOL_ITERATIONS = 10

# En _ejecutar_loop_tool_use:
while iteracion < MAX_TOOL_ITERATIONS:
    iteracion += 1
    # ...

# Limite de iteraciones alcanzado
logger.warning("Limite de iteraciones de tool use alcanzado")
return texto_respuesta, tool_calls_realizados, fuentes, accion_pendiente
# ← No avisa al usuario
```

**Impacto:**
- Usuario recibe respuesta incompleta sin saber por qué
- Puede parecer que el asistente "se confundió"

---

### BUG-009: Patrones de prompt injection muy básicos [MENOR]

**Ubicación:** `backend/app/services/asistente/service.py:91-98`

**Descripción:**
La sanitización de entrada usa patrones regex muy simples que pueden ser evadidos fácilmente.

**Código actual:**
```python
PATRONES_BLOQUEADOS = [
    r"ignore\s+(previous|all|your)\s+instructions?",
    r"disregard\s+(your|all)\s+instructions?",
    r"you\s+are\s+now",
    # ...
]
```

**Impacto:**
- Variaciones con caracteres especiales pueden evadir detección
- Riesgo bajo dado que es sistema interno

---

## Estado de la Conexión Asistente ↔ Proyectos

| Funcionalidad | Estado | Notas |
|---------------|--------|-------|
| Enviar `proyecto_contexto_id` en chat | ✅ OK | Funciona correctamente |
| Backend recibe contexto del proyecto | ✅ OK | Se incluye en system prompt |
| Herramienta `ConsultarProyecto` | ✅ OK | Retorna datos completos |
| Herramienta `ListarProyectos` | ✅ OK | Funciona con filtros |
| Herramienta `ConsultarAnalisis` | ✅ OK | Retorna análisis existentes |
| Herramienta `CrearProyecto` | ✅ OK | Crea proyectos correctamente |
| Herramienta `ActualizarProyecto` | ✅ OK | Actualiza campos |
| Herramienta `EjecutarAnalisis` | ❌ BUG-001 | No ejecuta realmente |
| Sincronizar contexto entre vistas | ⚠️ BUG-003 | Se pierde al navegar |
| Mostrar nombre proyecto en acciones | ❌ BUG-004 | Solo muestra ID |
| Vincular conversación a proyecto (BD) | ✅ OK | Campo existe |
| Vincular conversación a proyecto (UI) | ⚠️ BUG-005 | No se muestra |
| Auditoría de acciones por proyecto | ❌ BUG-006 | Sin FK |

---

## Plan de Corrección

### Fase 1: Bugs Críticos (Prioridad Alta)

#### 1.1 Implementar EjecutarAnalisis real

**Archivos a modificar:**
- `backend/app/services/asistente/tools/acciones.py`

**Cambios:**
```python
async def ejecutar(self, proyecto_id: int, tipo_analisis: str = "completo", ...):
    # ... validaciones existentes ...

    # NUEVO: Importar y usar servicio de prefactibilidad
    from app.services.prefactibilidad import PrefactibilidadService

    prefact_service = PrefactibilidadService(db)

    if tipo_analisis == "rapido":
        resultado = await prefact_service.analisis_rapido(proyecto_id)
    else:
        resultado = await prefact_service.analisis_completo(proyecto_id)

    # Actualizar estado del proyecto
    proyecto.estado = "analizado"
    await db.flush()

    return ResultadoHerramienta(
        exito=True,
        contenido={
            "proyecto_id": proyecto_id,
            "analisis_id": resultado.id,
            "clasificacion": resultado.clasificacion,
            "via_ingreso": resultado.via_ingreso_recomendada,
            "mensaje": f"Análisis completado: {resultado.via_ingreso_recomendada}",
        },
    )
```

**Esfuerzo estimado:** 2-3 horas

---

#### 1.2 Actualizar contexto después de acciones

**Archivos a modificar:**
- `backend/app/services/asistente/service.py`

**Cambios:**
```python
async def chat(self, request: ChatRequest) -> ChatResponse:
    # ... código existente ...

    # Después de ejecutar herramientas, recargar contexto
    if accion_pendiente or any(tc.name in ['crear_proyecto', 'ejecutar_analisis'] for tc in tool_calls_realizados):
        contexto = await self.gestor_contexto.obtener_contexto(
            session_id=request.session_id,
            user_id=request.user_id,
            proyecto_id=request.proyecto_contexto_id,
            vista_actual=request.vista_actual or "dashboard",
        )

    return ChatResponse(
        sugerencias=self._generar_sugerencias(contexto, respuesta_final),
    )
```

**Esfuerzo estimado:** 1 hora

---

### Fase 2: Bugs Importantes (Prioridad Media)

#### 2.1 Preservar contexto de proyecto al navegar

**Archivos a modificar:**
- `frontend/src/views/AsistenteView.vue`
- `frontend/src/composables/useAsistente.ts` (crear si no existe)

**Cambios:**
```typescript
// AsistenteView.vue
import { useRoute } from 'vue-router'

onMounted(async () => {
  const route = useRoute()

  // Verificar si hay proyecto en query params o localStorage
  const proyectoId = route.query.proyecto
    || localStorage.getItem('ultimo_proyecto_contexto')

  if (proyectoId) {
    store.setProyectoContexto(Number(proyectoId))
  }

  store.setVistaActual('asistente')
  // ...
})
```

**Esfuerzo estimado:** 2 horas

---

#### 2.2 Mejorar descripción de acciones con nombre del proyecto

**Archivos a modificar:**
- `backend/app/services/asistente/tools/acciones.py`
- `backend/app/services/asistente/service.py`

**Cambios:**
```python
# En EjecutarHerramientas.ejecutar_tool()
async def ejecutar_tool(self, tool_name, tool_input, conversacion_id):
    # Si la herramienta usa proyecto_id, obtener nombre
    proyecto_nombre = None
    if "proyecto_id" in tool_input:
        result = await self.db.execute(
            select(Proyecto.nombre).where(Proyecto.id == tool_input["proyecto_id"])
        )
        proyecto_nombre = result.scalar()

    # Pasar nombre a generar_descripcion_confirmacion
    if hasattr(herramienta, 'generar_descripcion_confirmacion'):
        descripcion = herramienta.generar_descripcion_confirmacion(
            **tool_input,
            _proyecto_nombre=proyecto_nombre  # Parámetro interno
        )

# En EjecutarAnalisis
def generar_descripcion_confirmacion(self, **kwargs) -> str:
    proyecto_id = kwargs.get("proyecto_id", "?")
    proyecto_nombre = kwargs.get("_proyecto_nombre", f"ID {proyecto_id}")
    tipo = kwargs.get("tipo_analisis", "completo")
    return f"Ejecutar análisis {tipo} para '{proyecto_nombre}'"
```

**Esfuerzo estimado:** 2 horas

---

#### 2.3 Mostrar proyecto asociado en conversaciones

**Archivos a modificar:**
- `frontend/src/types/asistente.ts`
- `frontend/src/stores/asistente.ts`
- `frontend/src/views/AsistenteView.vue`
- `backend/app/schemas/asistente.py`

**Cambios:**
```typescript
// types/asistente.ts
interface Conversacion {
  id: string
  titulo: string
  proyecto_activo_id?: number
  proyecto_nombre?: string  // NUEVO
  // ...
}

// AsistenteView.vue - En lista de conversaciones
<p v-if="conv.proyecto_nombre" class="text-xs text-primary">
  {{ conv.proyecto_nombre }}
</p>
```

**Esfuerzo estimado:** 3 horas

---

#### 2.4 Agregar FK proyecto a AccionPendiente

**Archivos a modificar:**
- `backend/app/db/models/asistente.py`
- Nueva migración Alembic

**Cambios:**
```python
class AccionPendiente(Base):
    # ... campos existentes ...

    # NUEVO
    proyecto_id = Column(
        Integer,
        ForeignKey("proyectos.proyectos.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    proyecto = relationship("Proyecto")
```

**Migración:**
```bash
alembic revision --autogenerate -m "add_proyecto_id_to_acciones_pendientes"
alembic upgrade head
```

**Esfuerzo estimado:** 1 hora

---

### Fase 3: Bugs Menores (Prioridad Baja)

#### 3.1 Usar sessionStorage en lugar de localStorage

**Esfuerzo:** 30 min

#### 3.2 Avisar al usuario cuando se alcanza límite de iteraciones

**Esfuerzo:** 30 min

#### 3.3 Mejorar patrones de sanitización

**Esfuerzo:** 2 horas (requiere investigación)

---

## Cronograma Sugerido

| Fase | Descripción | Esfuerzo | Prioridad |
|------|-------------|----------|-----------|
| 1.1 | Implementar EjecutarAnalisis | 3h | Alta |
| 1.2 | Actualizar contexto post-acciones | 1h | Alta |
| 2.1 | Preservar contexto al navegar | 2h | Media |
| 2.2 | Nombre proyecto en acciones | 2h | Media |
| 2.3 | Proyecto en lista conversaciones | 3h | Media |
| 2.4 | FK proyecto en AccionPendiente | 1h | Media |
| 3.x | Bugs menores | 3h | Baja |
| **Total** | | **15h** | |

---

## Verificación Post-Corrección

### Tests a ejecutar:

1. **Test EjecutarAnalisis:**
   - Crear proyecto con geometría
   - Pedir al asistente "ejecuta el análisis"
   - Confirmar acción
   - Verificar que el análisis se creó en BD
   - Verificar que proyecto.estado = "analizado"

2. **Test Contexto Proyecto:**
   - Navegar a /proyectos/123
   - Ir a /asistente
   - Verificar que proyectoContextoId = 123
   - Enviar mensaje "¿qué sabes de este proyecto?"
   - Verificar que responde con datos del proyecto 123

3. **Test Descripción Acciones:**
   - Pedir "crea un proyecto llamado 'Test ABC'"
   - Verificar que la confirmación dice "Crear proyecto 'Test ABC'" no "proyecto ID X"

4. **Test Conversaciones:**
   - Crear conversación mientras estás en /proyectos/123
   - Ir al historial de conversaciones
   - Verificar que muestra "Proyecto: Test ABC" junto a la conversación

---

## Anexos

### A. Archivos Relevantes

```
backend/
├── app/
│   ├── services/
│   │   └── asistente/
│   │       ├── service.py          # Servicio principal
│   │       └── tools/
│   │           ├── acciones.py     # CrearProyecto, EjecutarAnalisis
│   │           ├── consultas.py    # ConsultarProyecto, etc.
│   │           └── rag.py          # BuscarNormativa, etc.
│   ├── schemas/
│   │   └── asistente.py            # Pydantic schemas
│   └── db/
│       └── models/
│           └── asistente.py        # Modelos SQLAlchemy

frontend/
├── src/
│   ├── views/
│   │   └── AsistenteView.vue       # Vista principal
│   ├── components/
│   │   └── asistente/
│   │       ├── MessageList.vue
│   │       ├── ActionPanel.vue
│   │       ├── InputArea.vue
│   │       └── ConfirmDialog.vue
│   ├── stores/
│   │   └── asistente.ts            # Pinia store
│   └── types/
│       └── asistente.ts            # TypeScript types
```

### B. Herramientas del Asistente

| Herramienta | Categoría | Confirmación | Estado |
|-------------|-----------|--------------|--------|
| buscar_normativa | RAG | No | ✅ OK |
| buscar_documentacion | RAG | No | ✅ OK |
| explicar_clasificacion | RAG | No | ✅ OK |
| consultar_proyecto | Consulta | No | ✅ OK |
| consultar_analisis | Consulta | No | ✅ OK |
| listar_proyectos | Consulta | No | ✅ OK |
| obtener_estadisticas | Consulta | No | ✅ OK |
| crear_proyecto | Acción | Sí | ✅ OK |
| actualizar_proyecto | Acción | Sí | ✅ OK |
| ejecutar_analisis | Acción | Sí | ❌ BUG |
| buscar_web_actualizada | Externa | No | ✅ OK |

---

*Documento generado automáticamente por Claude Code*
