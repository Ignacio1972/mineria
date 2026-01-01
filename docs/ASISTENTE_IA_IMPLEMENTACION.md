# Asistente IA - Guia de Implementacion

**Version:** 1.0 | **Fecha:** 2025-12-31

---

## 1. Stack Tecnologico

| Componente | Tecnologia | Justificacion |
|------------|------------|---------------|
| LLM | Anthropic Claude (claude-sonnet-4-20250514) | Ya integrado en el sistema |
| Embeddings | sentence-transformers | Ya existe para RAG legal |
| Vector DB | pgvector | Ya configurado |
| Cache | Redis | Ya disponible |
| WebSocket | FastAPI WebSockets | Tiempo real |
| HTTP Client | httpx | Async para fuentes externas |

---

## 2. Estructura de Archivos

```
backend/app/
├── api/v1/endpoints/
│   └── asistente.py              # Endpoints REST + WebSocket
├── services/
│   └── asistente/
│       ├── __init__.py
│       ├── agente.py             # Agente principal (orquestador)
│       ├── contexto.py           # Gestor de contexto
│       ├── memoria.py            # Gestor de memoria
│       ├── ejecutor.py           # Ejecutor de acciones
│       └── tools/
│           ├── __init__.py
│           ├── registry.py       # Registro de herramientas
│           ├── internas.py       # consultar_proyecto, ejecutar_analisis
│           ├── rag.py            # buscar_normativa, buscar_documentacion
│           └── externas.py       # buscar_sea, buscar_eseia, buscar_bcn
├── schemas/
│   └── asistente.py              # Pydantic schemas
└── db/models/
    └── asistente.py              # SQLAlchemy models

frontend/src/
├── views/
│   └── AsistenteView.vue         # Vista principal
├── components/asistente/
│   ├── ChatPanel.vue             # Panel de chat
│   ├── MessageList.vue           # Lista de mensajes
│   ├── MessageBubble.vue         # Burbuja individual
│   ├── InputArea.vue             # Area de entrada
│   ├── ActionConfirmDialog.vue   # Dialogo confirmacion
│   └── SourcesPanel.vue          # Panel de fuentes
├── stores/
│   └── asistente.ts              # Pinia store
├── services/
│   └── asistente.ts              # API client
└── types/
    └── asistente.ts              # TypeScript types
```

---

## 3. Backend - Codigo Base

### 3.1 Schemas (`schemas/asistente.py`)

```python
from pydantic import BaseModel
from typing import Optional, List, Literal
from uuid import UUID
from datetime import datetime

class MensajeInput(BaseModel):
    contenido: str
    proyecto_contexto_id: Optional[int] = None

class ToolCall(BaseModel):
    id: str
    name: str
    arguments: dict

class Fuente(BaseModel):
    tipo: str  # "normativa", "documentacion", "sea", "eseia"
    titulo: str
    referencia: str
    url: Optional[str] = None

class MensajeResponse(BaseModel):
    id: UUID
    rol: Literal["assistant"]
    contenido: str
    fuentes: List[Fuente] = []
    created_at: datetime

class AccionPendiente(BaseModel):
    id: UUID
    tipo: str
    descripcion: str
    parametros: dict

class ChatResponse(BaseModel):
    mensaje: MensajeResponse
    accion_pendiente: Optional[AccionPendiente] = None
    sugerencias: List[str] = []

class ConfirmacionInput(BaseModel):
    accion_id: UUID
    confirmada: bool
```

### 3.2 Agente Principal (`services/asistente/agente.py`)

```python
from anthropic import Anthropic
from typing import List, Optional
from .tools.registry import TOOLS, ejecutar_tool
from .contexto import ContextoManager
from .memoria import MemoriaManager

class AgenteAsistente:
    def __init__(self):
        self.client = Anthropic()
        self.model = "claude-sonnet-4-20250514"
        self.contexto = ContextoManager()
        self.memoria = MemoriaManager()

    async def procesar_mensaje(
        self,
        mensaje: str,
        session_id: str,
        proyecto_id: Optional[int] = None
    ) -> dict:
        # 1. Construir contexto
        contexto = await self.contexto.obtener(session_id, proyecto_id)
        historial = await self.memoria.obtener_historial(session_id)

        # 2. Construir mensajes
        messages = self._construir_mensajes(historial, mensaje, contexto)

        # 3. Llamar al modelo con tools
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=self._system_prompt(contexto),
            tools=TOOLS,
            messages=messages
        )

        # 4. Procesar respuesta (puede incluir tool calls)
        resultado = await self._procesar_respuesta(response, session_id)

        # 5. Guardar en memoria
        await self.memoria.guardar(session_id, mensaje, resultado)

        return resultado

    async def _procesar_respuesta(self, response, session_id) -> dict:
        contenido = ""
        fuentes = []
        accion_pendiente = None

        for block in response.content:
            if block.type == "text":
                contenido = block.text
            elif block.type == "tool_use":
                # Ejecutar herramienta
                tool_result = await ejecutar_tool(
                    block.name,
                    block.input,
                    session_id
                )

                # Si es accion que requiere confirmacion
                if tool_result.get("requiere_confirmacion"):
                    accion_pendiente = AccionPendiente(
                        id=uuid4(),
                        tipo=block.name,
                        descripcion=tool_result["descripcion"],
                        parametros=block.input
                    )
                else:
                    # Continuar conversacion con resultado
                    fuentes.extend(tool_result.get("fuentes", []))

        return {
            "mensaje": contenido,
            "fuentes": fuentes,
            "accion_pendiente": accion_pendiente
        }

    def _system_prompt(self, contexto: dict) -> str:
        return f"""Eres el asistente del Sistema de Prefactibilidad Ambiental Minera de Chile.

Tu rol es ayudar a usuarios a evaluar proyectos mineros segun la Ley 19.300 y el SEIA.

CAPACIDADES:
- Responder preguntas sobre normativa ambiental (usa buscar_normativa)
- Explicar el funcionamiento del sistema (usa buscar_documentacion)
- Consultar datos de proyectos (usa consultar_proyecto)
- Ejecutar acciones con confirmacion del usuario
- Buscar informacion en fuentes externas (SEA, e-SEIA, BCN)

CONTEXTO ACTUAL:
{contexto}

REGLAS:
1. Siempre cita las fuentes cuando uses informacion de herramientas
2. Para acciones (crear, modificar, ejecutar), solicita confirmacion
3. Se conciso pero completo en las respuestas
4. Si no sabes algo, dilo honestamente
"""
```

### 3.3 Registro de Herramientas (`services/asistente/tools/registry.py`)

```python
TOOLS = [
    {
        "name": "buscar_normativa",
        "description": "Busca en el corpus legal (Ley 19.300, DS 40, Guias SEA)",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Consulta de busqueda"},
                "top_k": {"type": "integer", "default": 5}
            },
            "required": ["query"]
        }
    },
    {
        "name": "consultar_proyecto",
        "description": "Obtiene datos de un proyecto especifico",
        "input_schema": {
            "type": "object",
            "properties": {
                "proyecto_id": {"type": "integer"}
            },
            "required": ["proyecto_id"]
        }
    },
    {
        "name": "crear_proyecto",
        "description": "Crea un nuevo proyecto. REQUIERE CONFIRMACION.",
        "input_schema": {
            "type": "object",
            "properties": {
                "nombre": {"type": "string"},
                "region": {"type": "string"},
                "tipo_mineria": {"type": "string"}
            },
            "required": ["nombre", "region"]
        }
    },
    {
        "name": "ejecutar_analisis",
        "description": "Ejecuta analisis de prefactibilidad. REQUIERE CONFIRMACION.",
        "input_schema": {
            "type": "object",
            "properties": {
                "proyecto_id": {"type": "integer"},
                "tipo": {"type": "string", "enum": ["rapido", "completo"]}
            },
            "required": ["proyecto_id"]
        }
    },
    {
        "name": "buscar_sea",
        "description": "Busca informacion en el sitio del SEA",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "buscar_eseia",
        "description": "Busca proyectos aprobados en e-SEIA",
        "input_schema": {
            "type": "object",
            "properties": {
                "nombre": {"type": "string"},
                "region": {"type": "string"},
                "tipo": {"type": "string"}
            }
        }
    }
]

# Herramientas que requieren confirmacion
TOOLS_CON_CONFIRMACION = ["crear_proyecto", "ejecutar_analisis", "actualizar_proyecto"]

async def ejecutar_tool(name: str, params: dict, session_id: str) -> dict:
    if name in TOOLS_CON_CONFIRMACION:
        return {
            "requiere_confirmacion": True,
            "descripcion": f"Ejecutar {name} con parametros: {params}"
        }

    # Importar y ejecutar la herramienta correspondiente
    if name == "buscar_normativa":
        from .rag import buscar_normativa
        return await buscar_normativa(**params)
    elif name == "consultar_proyecto":
        from .internas import consultar_proyecto
        return await consultar_proyecto(**params)
    # ... etc
```

### 3.4 Endpoints (`api/v1/endpoints/asistente.py`)

```python
from fastapi import APIRouter, Depends, WebSocket
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services.asistente.agente import AgenteAsistente
from app.schemas.asistente import MensajeInput, ChatResponse, ConfirmacionInput

router = APIRouter(prefix="/asistente", tags=["asistente"])
agente = AgenteAsistente()

@router.post("/chat", response_model=ChatResponse)
async def enviar_mensaje(
    input: MensajeInput,
    session_id: str = Header(...),
    db: AsyncSession = Depends(get_db)
):
    resultado = await agente.procesar_mensaje(
        mensaje=input.contenido,
        session_id=session_id,
        proyecto_id=input.proyecto_contexto_id
    )
    return ChatResponse(**resultado)

@router.post("/confirmar")
async def confirmar_accion(
    input: ConfirmacionInput,
    session_id: str = Header(...),
    db: AsyncSession = Depends(get_db)
):
    if input.confirmada:
        resultado = await agente.ejecutar_accion_pendiente(input.accion_id)
        return {"exito": True, "resultado": resultado}
    else:
        return {"exito": False, "mensaje": "Accion cancelada"}

@router.get("/historial")
async def obtener_historial(
    session_id: str = Header(...),
    limit: int = 50
):
    return await agente.memoria.obtener_historial(session_id, limit)

@router.websocket("/ws/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: str):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            resultado = await agente.procesar_mensaje(
                mensaje=data["contenido"],
                session_id=session_id,
                proyecto_id=data.get("proyecto_id")
            )
            await websocket.send_json(resultado)
    except Exception:
        await websocket.close()
```

---

## 4. Frontend - Codigo Base

### 4.1 Store Pinia (`stores/asistente.ts`)

```typescript
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { asistenteService } from '@/services/asistente'

export interface Mensaje {
  id: string
  rol: 'user' | 'assistant'
  contenido: string
  fuentes?: Fuente[]
  createdAt: Date
}

export interface AccionPendiente {
  id: string
  tipo: string
  descripcion: string
  parametros: Record<string, any>
}

export const useAsistenteStore = defineStore('asistente', () => {
  const mensajes = ref<Mensaje[]>([])
  const cargando = ref(false)
  const accionPendiente = ref<AccionPendiente | null>(null)
  const sessionId = ref(crypto.randomUUID())

  async function enviarMensaje(contenido: string, proyectoId?: number) {
    // Agregar mensaje del usuario
    mensajes.value.push({
      id: crypto.randomUUID(),
      rol: 'user',
      contenido,
      createdAt: new Date()
    })

    cargando.value = true
    try {
      const response = await asistenteService.enviarMensaje({
        contenido,
        proyecto_contexto_id: proyectoId
      }, sessionId.value)

      // Agregar respuesta del asistente
      mensajes.value.push({
        id: response.mensaje.id,
        rol: 'assistant',
        contenido: response.mensaje.contenido,
        fuentes: response.mensaje.fuentes,
        createdAt: new Date(response.mensaje.created_at)
      })

      // Manejar accion pendiente
      if (response.accion_pendiente) {
        accionPendiente.value = response.accion_pendiente
      }
    } finally {
      cargando.value = false
    }
  }

  async function confirmarAccion(confirmada: boolean) {
    if (!accionPendiente.value) return

    const resultado = await asistenteService.confirmarAccion({
      accion_id: accionPendiente.value.id,
      confirmada
    }, sessionId.value)

    accionPendiente.value = null
    return resultado
  }

  return {
    mensajes,
    cargando,
    accionPendiente,
    sessionId,
    enviarMensaje,
    confirmarAccion
  }
})
```

### 4.2 Vista Principal (`views/AsistenteView.vue`)

```vue
<template>
  <div class="h-screen flex flex-col">
    <!-- Header -->
    <div class="navbar bg-base-200">
      <div class="flex-1">
        <span class="text-xl font-bold">Asistente IA</span>
      </div>
    </div>

    <!-- Chat Area -->
    <div class="flex-1 overflow-hidden flex">
      <!-- Messages -->
      <div class="flex-1 overflow-y-auto p-4 space-y-4">
        <MessageBubble
          v-for="msg in mensajes"
          :key="msg.id"
          :mensaje="msg"
        />
        <div v-if="cargando" class="flex justify-start">
          <span class="loading loading-dots loading-md"></span>
        </div>
      </div>

      <!-- Sources Panel (optional) -->
      <SourcesPanel
        v-if="mensajeSeleccionado?.fuentes?.length"
        :fuentes="mensajeSeleccionado.fuentes"
        class="w-80 border-l"
      />
    </div>

    <!-- Input Area -->
    <div class="p-4 border-t bg-base-100">
      <div class="flex gap-2">
        <input
          v-model="inputMensaje"
          @keyup.enter="enviar"
          type="text"
          placeholder="Escribe tu mensaje..."
          class="input input-bordered flex-1"
          :disabled="cargando"
        />
        <button
          @click="enviar"
          class="btn btn-primary"
          :disabled="cargando || !inputMensaje.trim()"
        >
          Enviar
        </button>
      </div>
    </div>

    <!-- Action Confirmation Dialog -->
    <ActionConfirmDialog
      v-if="accionPendiente"
      :accion="accionPendiente"
      @confirmar="onConfirmar"
      @cancelar="onCancelar"
    />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { storeToRefs } from 'pinia'
import { useAsistenteStore } from '@/stores/asistente'
import MessageBubble from '@/components/asistente/MessageBubble.vue'
import SourcesPanel from '@/components/asistente/SourcesPanel.vue'
import ActionConfirmDialog from '@/components/asistente/ActionConfirmDialog.vue'

const store = useAsistenteStore()
const { mensajes, cargando, accionPendiente } = storeToRefs(store)

const inputMensaje = ref('')
const mensajeSeleccionado = ref(null)

async function enviar() {
  if (!inputMensaje.value.trim()) return
  const msg = inputMensaje.value
  inputMensaje.value = ''
  await store.enviarMensaje(msg)
}

async function onConfirmar() {
  await store.confirmarAccion(true)
}

async function onCancelar() {
  await store.confirmarAccion(false)
}
</script>
```

### 4.3 Ruta (`router/index.ts`)

```typescript
// Agregar a las rutas existentes
{
  path: '/asistente',
  name: 'asistente',
  component: () => import('@/views/AsistenteView.vue'),
  meta: { title: 'Asistente IA' }
}
```

---

## 5. SQL - Migracion

```sql
-- Ejecutar en PostgreSQL
CREATE SCHEMA IF NOT EXISTS asistente;

CREATE TABLE asistente.conversaciones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL,
    user_id INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE asistente.mensajes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversacion_id UUID REFERENCES asistente.conversaciones(id),
    rol VARCHAR(20) NOT NULL,
    contenido TEXT NOT NULL,
    tool_calls JSONB,
    fuentes JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE asistente.acciones_pendientes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversacion_id UUID REFERENCES asistente.conversaciones(id),
    tipo VARCHAR(50) NOT NULL,
    parametros JSONB NOT NULL,
    estado VARCHAR(20) DEFAULT 'pendiente',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ DEFAULT NOW() + INTERVAL '5 minutes'
);

CREATE TABLE asistente.documentacion (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tipo VARCHAR(50) NOT NULL,
    ruta VARCHAR(500),
    contenido TEXT NOT NULL,
    embedding vector(384),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_doc_embedding ON asistente.documentacion
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

---

## 6. Plan de Implementacion

| Fase | Tareas | Estimacion |
|------|--------|------------|
| **1. Base** | Schemas, modelos, endpoint basico | 1-2 dias |
| **2. Agente** | Integracion Claude, tool registry | 2-3 dias |
| **3. Tools internas** | consultar_proyecto, ejecutar_analisis | 1-2 dias |
| **4. RAG sistema** | Indexar documentacion, buscar_documentacion | 1-2 dias |
| **5. Fuentes externas** | SEA, e-SEIA, BCN scrapers | 2-3 dias |
| **6. Frontend** | Vista, componentes, store | 2-3 dias |
| **7. Acciones** | Confirmacion, ejecucion | 1-2 dias |
| **8. Proactividad** | Triggers, notificaciones | 1-2 dias |
| **9. Testing** | Unit, integration, E2E | 2-3 dias |

**Total estimado: 2-3 semanas**

---

## 7. Dependencias a Agregar

### Backend (`requirements.txt`)
```
httpx==0.27.0  # Ya existe, verificar version
playwright==1.40.0  # Para scraping e-SEIA (opcional)
```

### Frontend (`package.json`)
```json
{
  "dependencies": {
    "marked": "^12.0.0"  // Para renderizar markdown en respuestas
  }
}
```

---

## 8. Variables de Entorno

```env
# Ya existentes (verificar)
ANTHROPIC_API_KEY=sk-ant-...

# Nuevas
ASISTENTE_MAX_TOKENS=4096
ASISTENTE_CACHE_TTL_SEGUNDOS=3600
ASISTENTE_RATE_LIMIT_POR_MINUTO=10
```

---

*Documento de Implementacion v1.0*
