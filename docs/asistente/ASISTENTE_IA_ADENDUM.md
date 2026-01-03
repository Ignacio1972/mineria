# Adendum - Asistente IA Arquitectura

**Documento base:** ASISTENTE_IA_ARQUITECTURA.md v1.0
**Fecha:** 2025-12-31
**Proposito:** Correcciones, mejoras y extension para integracion multi-LLM

---

## 1. Correcciones al Documento Original

### 1.1 Error de Formato (Linea 80)

**Original:**
```
(Claude claude-sonnet-4-20250514)
```

**Correccion:**
```
(Claude Sonnet 4 - claude-sonnet-4-20250514)
```

### 1.2 Referencia FK Incorrecta (Linea 539)

**Original:**
```sql
user_id INTEGER REFERENCES proyectos.clientes(id)
```

**Correccion:** Verificar schema real de la tabla clientes. Segun el esquema actual del sistema, los clientes estan en schema `public` o directamente como `clientes`. Ajustar a:
```sql
user_id INTEGER REFERENCES clientes(id)
```

### 1.3 Duplicacion de Tabla RAG

La tabla `asistente.documentacion` propuesta duplica funcionalidad con `legal.fragmentos`.

**Recomendacion:** Reutilizar el sistema RAG existente agregando una columna `tipo_documento` o creando una vista unificada:

```sql
CREATE VIEW asistente.corpus_unificado AS
SELECT
    id,
    'legal' as origen,
    contenido,
    embedding,
    metadata
FROM legal.fragmentos
UNION ALL
SELECT
    id,
    'sistema' as origen,
    contenido,
    embedding,
    metadata
FROM asistente.documentacion_sistema;
```

### 1.4 Sanitizacion Problematica

El uso de `html.escape()` puede corromper queries validas con caracteres `<`, `>`, `&`.

**Recomendacion:** Usar sanitizacion especifica para el contexto:

```python
def sanitizar(self, texto: str) -> str:
    # 1. Truncar
    texto = texto[:self.MAX_LENGTH]

    # 2. Detectar inyeccion (mantener)
    for patron in self.PATRONES_BLOQUEADOS:
        if re.search(patron, texto, re.IGNORECASE):
            raise ValueError("Contenido no permitido")

    # 3. NO usar html.escape - el texto no se renderiza como HTML
    # Solo sanitizar caracteres de control
    texto = ''.join(c for c in texto if c.isprintable() or c in '\n\t')

    return texto
```

---

## 2. Mejoras Sugeridas

### 2.1 Herramienta Faltante: explicar_clasificacion

Agregar al catalogo de herramientas:

```
┌─────────────────────────────────────────────────────────────────────────┐
│ explicar_clasificacion                                                  │
│ ├── Descripcion: Genera explicacion detallada de por que un proyecto   │
│ │                fue clasificado como DIA o EIA                         │
│ ├── Input: analisis_id (int)                                           │
│ ├── Output: ExplicacionClasificacion                                   │
│ │   ├── clasificacion: str (DIA/EIA)                                   │
│ │   ├── confianza: float                                               │
│ │   ├── triggers_detectados: List[TriggerExplicado]                    │
│ │   ├── fundamento_legal: List[ArticuloRelevante]                      │
│ │   └── factores_matriz: List[FactorEvaluado]                          │
│ └── Permisos: Lectura                                                  │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Memoria Semantica

El sliding window puede perder contexto critico. Agregar memoria semantica:

```python
class MemoriaSemantica:
    """
    Almacena hechos importantes de la conversacion como embeddings.
    """

    async def extraer_hechos(self, mensaje: str) -> List[Hecho]:
        """Extrae hechos clave del mensaje usando LLM."""
        pass

    async def recuperar_contexto(self, query: str, top_k: int = 5) -> List[Hecho]:
        """Recupera hechos relevantes por similitud semantica."""
        pass

    async def comprimir_historial(self, mensajes: List[Mensaje]) -> str:
        """Genera resumen estructurado del historial."""
        pass
```

### 2.3 Priorizacion de Triggers Proactivos

Definir orden de prioridad cuando hay multiples triggers:

```python
PRIORIDAD_TRIGGERS = {
    "alertas_criticas_sin_revisar": 1,  # Maxima prioridad
    "analisis_desactualizado": 2,
    "proyecto_sin_geometria": 3,
    "normativa_actualizada": 4,         # Minima prioridad
}

def seleccionar_trigger(triggers_activos: List[str]) -> str:
    """Retorna el trigger de mayor prioridad."""
    return min(triggers_activos, key=lambda t: PRIORIDAD_TRIGGERS.get(t, 99))
```

### 2.4 WebSocket con Reconexion

```typescript
// frontend/src/composables/useAsistenteWebSocket.ts
export function useAsistenteWebSocket() {
  const HEARTBEAT_INTERVAL = 30000; // 30 segundos
  const MAX_RECONNECT_ATTEMPTS = 5;
  const RECONNECT_DELAY = 1000;

  let reconnectAttempts = 0;
  let heartbeatTimer: number | null = null;

  function connect() {
    const ws = new WebSocket(WS_URL);

    ws.onopen = () => {
      reconnectAttempts = 0;
      startHeartbeat(ws);
    };

    ws.onclose = () => {
      stopHeartbeat();
      if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
        setTimeout(() => {
          reconnectAttempts++;
          connect();
        }, RECONNECT_DELAY * Math.pow(2, reconnectAttempts));
      }
    };

    return ws;
  }

  function startHeartbeat(ws: WebSocket) {
    heartbeatTimer = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'ping' }));
      }
    }, HEARTBEAT_INTERVAL);
  }

  function stopHeartbeat() {
    if (heartbeatTimer) clearInterval(heartbeatTimer);
  }

  return { connect };
}
```

### 2.5 Rate Limiting Global

```python
class RateLimiterGlobal:
    """
    Limites globales para proteger el sistema.
    """

    LIMITES_GLOBALES = {
        "mensajes_por_minuto_global": 100,
        "llamadas_llm_por_minuto": 50,
        "busquedas_externas_por_minuto": 20,
    }

    async def verificar_limite_global(self, tipo: str) -> bool:
        key = f"rate:global:{tipo}"
        count = await redis.incr(key)
        if count == 1:
            await redis.expire(key, 60)
        return count <= self.LIMITES_GLOBALES[tipo]
```

### 2.6 Fallback a Modelo Menor

```python
class LLMClienteConFallback:
    """
    Cliente LLM con fallback automatico.
    """

    MODELOS = [
        ("claude-sonnet-4-20250514", "principal"),
        ("claude-3-5-haiku-20241022", "fallback"),
    ]

    async def generar(self, mensajes: List[dict], tools: List[dict]) -> dict:
        for modelo, tipo in self.MODELOS:
            try:
                return await self._llamar_modelo(modelo, mensajes, tools)
            except (RateLimitError, ServiceUnavailableError) as e:
                logger.warning(f"Modelo {modelo} no disponible: {e}")
                if tipo == "fallback":
                    raise
                continue
        raise ServiceUnavailableError("Todos los modelos no disponibles")
```

---

## 3. Integracion Multi-LLM: Perplexity

### 3.1 Arquitectura Multi-Proveedor

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        ARQUITECTURA MULTI-LLM                                │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                         LLM ROUTER                                      │ │
│  │                                                                         │ │
│  │   Entrada: tipo_tarea, contexto, preferencias_usuario                  │ │
│  │                                                                         │ │
│  │   Reglas de enrutamiento:                                              │ │
│  │   ├── Razonamiento complejo      → Claude Sonnet 4                     │ │
│  │   ├── Busqueda web actualizada   → Perplexity Sonar                    │ │
│  │   ├── Investigacion profunda     → Perplexity Deep Research            │ │
│  │   ├── Respuestas rapidas         → Claude Haiku (fallback)             │ │
│  │   └── Generacion de informes     → Claude Sonnet 4                     │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                    │                                         │
│           ┌────────────────────────┼────────────────────────┐               │
│           ▼                        ▼                        ▼               │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐         │
│  │    ANTHROPIC    │    │   PERPLEXITY    │    │    FALLBACK     │         │
│  │                 │    │                 │    │                 │         │
│  │ claude-sonnet-4 │    │ sonar-pro       │    │ claude-haiku    │         │
│  │                 │    │ sonar-deep      │    │                 │         │
│  │ Tool Use        │    │ sonar-reasoning │    │ Respuestas      │         │
│  │ Razonamiento    │    │                 │    │ simples         │         │
│  │ Generacion      │    │ Web Search      │    │                 │         │
│  └─────────────────┘    │ Citas           │    └─────────────────┘         │
│                         └─────────────────┘                                 │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Opcion A: MCP Server Oficial (Recomendado)

Perplexity proporciona un MCP Server oficial que se integra directamente.

**Instalacion:**

```bash
npm install -g @perplexity-ai/mcp-server
```

**Configuracion MCP (mcp.json):**

```json
{
  "mcpServers": {
    "perplexity": {
      "command": "npx",
      "args": ["-y", "@perplexity-ai/mcp-server"],
      "env": {
        "PERPLEXITY_API_KEY": "${PERPLEXITY_API_KEY}"
      }
    }
  }
}
```

**Herramientas disponibles via MCP:**

| Herramienta | Modelo | Caso de Uso |
|-------------|--------|-------------|
| `web_search` | Search API | Busqueda web directa, resultados rankeados |
| `chat` | sonar-pro | Conversacion con contexto web |
| `deep_research` | sonar-deep-research | Investigacion exhaustiva con citas |
| `reasoning` | sonar-reasoning-pro | Problemas logicos, analisis complejo |

### 3.3 Opcion B: Integracion API Directa

Si se requiere mayor control, implementar cliente directo:

```python
# backend/app/services/llm/perplexity_client.py

from typing import Optional, List, Literal
import httpx
from pydantic import BaseModel

class PerplexityResponse(BaseModel):
    contenido: str
    fuentes: List[dict]
    modelo: str
    tokens_usados: int

class PerplexityClient:
    """
    Cliente para API de Perplexity.
    """

    BASE_URL = "https://api.perplexity.ai"

    MODELOS = {
        "chat": "sonar-pro",
        "research": "sonar-deep-research",
        "reasoning": "sonar-reasoning-pro",
    }

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=120.0
        )

    async def buscar(
        self,
        query: str,
        modo: Literal["chat", "research", "reasoning"] = "chat",
        contexto_adicional: Optional[str] = None
    ) -> PerplexityResponse:
        """
        Realiza busqueda con Perplexity.

        Args:
            query: Consulta del usuario
            modo: Tipo de busqueda (chat, research, reasoning)
            contexto_adicional: Contexto del sistema de mineria
        """

        mensajes = []

        if contexto_adicional:
            mensajes.append({
                "role": "system",
                "content": f"Contexto del sistema: {contexto_adicional}"
            })

        mensajes.append({
            "role": "user",
            "content": query
        })

        response = await self.client.post(
            "/chat/completions",
            json={
                "model": self.MODELOS[modo],
                "messages": mensajes,
                "return_citations": True,
                "return_related_questions": False
            }
        )

        response.raise_for_status()
        data = response.json()

        return PerplexityResponse(
            contenido=data["choices"][0]["message"]["content"],
            fuentes=data.get("citations", []),
            modelo=data["model"],
            tokens_usados=data["usage"]["total_tokens"]
        )

    async def close(self):
        await self.client.aclose()
```

### 3.4 Nueva Herramienta: buscar_web_actualizada

Agregar al catalogo de herramientas del agente:

```
┌─────────────────────────────────────────────────────────────────────────┐
│ buscar_web_actualizada                                                  │
│ ├── Descripcion: Busqueda web con IA para informacion actualizada.     │
│ │                Usa Perplexity para consultar SEA, e-SEIA, BCN y      │
│ │                otras fuentes en tiempo real.                          │
│ ├── Input:                                                              │
│ │   ├── query (str): Consulta de busqueda                              │
│ │   ├── modo (str): "chat" | "research" | "reasoning"                  │
│ │   └── fuentes_preferidas (List[str]): URLs a priorizar               │
│ ├── Output: ResultadoBusquedaWeb                                       │
│ │   ├── respuesta: str                                                 │
│ │   ├── fuentes: List[FuenteCitada]                                    │
│ │   │   ├── titulo: str                                                │
│ │   │   ├── url: str                                                   │
│ │   │   └── fragmento: str                                             │
│ │   └── confianza: float                                               │
│ └── Casos de uso:                                                      │
│     ├── "¿Hay cambios recientes en la Ley 19.300?"                     │
│     ├── "¿Que proyectos mineros se aprobaron este mes?"                │
│     └── "¿Cuales son las ultimas guias del SEA?"                       │
└─────────────────────────────────────────────────────────────────────────┘
```

**Tool Schema JSON:**

```json
{
  "name": "buscar_web_actualizada",
  "description": "Busca informacion actualizada en la web usando Perplexity AI. Ideal para consultar normativa reciente, proyectos aprobados en e-SEIA, guias del SEA, y cualquier informacion que requiera datos actualizados. Retorna respuesta con fuentes citadas.",
  "input_schema": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "Consulta de busqueda en lenguaje natural"
      },
      "modo": {
        "type": "string",
        "enum": ["chat", "research", "reasoning"],
        "default": "chat",
        "description": "Modo de busqueda: chat (rapido), research (profundo), reasoning (analitico)"
      },
      "contexto_chile": {
        "type": "boolean",
        "default": true,
        "description": "Agregar contexto de normativa ambiental chilena"
      }
    },
    "required": ["query"]
  }
}
```

### 3.5 Configuracion de Entorno

Agregar a `.env`:

```env
# Perplexity AI
PERPLEXITY_API_KEY=pplx-xxxxxxxxxxxxxxxxxxxx
PERPLEXITY_DEFAULT_MODEL=sonar-pro
PERPLEXITY_TIMEOUT_SECONDS=120
```

Agregar a `backend/app/core/config.py`:

```python
# Perplexity
PERPLEXITY_API_KEY: str = ""
PERPLEXITY_DEFAULT_MODEL: str = "sonar-pro"
PERPLEXITY_TIMEOUT_SECONDS: int = 120
PERPLEXITY_ENABLED: bool = True
```

### 3.6 Router de LLM

```python
# backend/app/services/llm/router.py

from enum import Enum
from typing import Optional

class TipoTarea(str, Enum):
    RAZONAMIENTO = "razonamiento"
    BUSQUEDA_WEB = "busqueda_web"
    INVESTIGACION = "investigacion"
    GENERACION = "generacion"
    RESPUESTA_RAPIDA = "respuesta_rapida"

class LLMRouter:
    """
    Enruta tareas al LLM mas apropiado.
    """

    def __init__(
        self,
        anthropic_client: AnthropicClient,
        perplexity_client: Optional[PerplexityClient] = None
    ):
        self.anthropic = anthropic_client
        self.perplexity = perplexity_client

    def determinar_proveedor(self, tipo_tarea: TipoTarea) -> str:
        """
        Determina que proveedor usar segun el tipo de tarea.
        """
        if self.perplexity is None:
            return "anthropic"

        ROUTING = {
            TipoTarea.RAZONAMIENTO: "anthropic",
            TipoTarea.BUSQUEDA_WEB: "perplexity",
            TipoTarea.INVESTIGACION: "perplexity",
            TipoTarea.GENERACION: "anthropic",
            TipoTarea.RESPUESTA_RAPIDA: "anthropic",
        }

        return ROUTING.get(tipo_tarea, "anthropic")

    async def ejecutar(
        self,
        tipo_tarea: TipoTarea,
        prompt: str,
        **kwargs
    ) -> dict:
        """
        Ejecuta la tarea con el proveedor apropiado.
        """
        proveedor = self.determinar_proveedor(tipo_tarea)

        if proveedor == "perplexity":
            modo = "research" if tipo_tarea == TipoTarea.INVESTIGACION else "chat"
            return await self.perplexity.buscar(prompt, modo=modo)
        else:
            return await self.anthropic.generar(prompt, **kwargs)
```

### 3.7 Comparativa de Costos

| Proveedor | Modelo | Input (1M tokens) | Output (1M tokens) | Caso de Uso |
|-----------|--------|-------------------|--------------------| ------------|
| Anthropic | claude-sonnet-4 | $3.00 | $15.00 | Razonamiento, generacion |
| Anthropic | claude-haiku-3.5 | $0.80 | $4.00 | Fallback, tareas simples |
| Perplexity | sonar-pro | $3.00 | $15.00 | Busqueda web |
| Perplexity | sonar-deep-research | $2.00 | $8.00 | Investigacion profunda |

**Recomendacion de uso:**
- Usar Perplexity para `buscar_sea`, `buscar_eseia`, `buscar_bcn` (reemplaza scrapers)
- Usar Claude para tool use, generacion de informes, y razonamiento complejo
- Usar Haiku como fallback cuando Sonnet no este disponible

---

## 4. Referencias

- [Perplexity MCP Server - Documentacion Oficial](https://docs.perplexity.ai/guides/mcp-server)
- [GitHub - perplexityai/modelcontextprotocol](https://github.com/perplexityai/modelcontextprotocol)
- [Perplexity API Documentation](https://docs.perplexity.ai/)
- [Anthropic Tool Use](https://docs.anthropic.com/claude/docs/tool-use)

---

*Adendum v1.0 - Correcciones y Extension Multi-LLM*
