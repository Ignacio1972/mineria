# Asistente IA - Documento de Arquitectura

**Sistema de Prefactibilidad Ambiental Minera**
**Version:** 1.0
**Fecha:** 2025-12-31
**Estado:** Especificacion Tecnica

---

## 1. Vision General

### 1.1 Proposito

El Asistente IA es un componente central del Sistema de Prefactibilidad Ambiental Minera que actua como interfaz conversacional inteligente entre el usuario y el sistema. Su objetivo es democratizar el acceso a la informacion ambiental y normativa, guiando a los usuarios en la evaluacion de proyectos mineros.

### 1.2 Objetivos del Sistema

| Objetivo | Descripcion |
|----------|-------------|
| **Asistencia contextual** | Responder preguntas sobre el sistema, proyectos y normativa ambiental |
| **Explicacion de resultados** | Justificar clasificaciones DIA/EIA con fundamento legal |
| **Proactividad** | Detectar estados incompletos y sugerir acciones |
| **Autonomia controlada** | Ejecutar acciones en el sistema con confirmacion del usuario |
| **Propuestas tecnicas** | Sugerir mejoras y nuevas funcionalidades al sistema |
| **Acceso a fuentes externas** | Consultar SEA, e-SEIA y normativa actualizada |

### 1.3 Casos de Uso Principales

```
┌─────────────────────────────────────────────────────────────────┐
│                     CASOS DE USO                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  CONSULTA           EXPLICACION         ACCION                  │
│  ┌──────────┐       ┌──────────┐       ┌──────────┐            │
│  │ "¿Como   │       │ "¿Por que│       │ "Crea un │            │
│  │ funciona │       │ este     │       │ proyecto │            │
│  │ el Art.  │       │ proyecto │       │ en       │            │
│  │ 11?"     │       │ es EIA?" │       │ Atacama" │            │
│  └──────────┘       └──────────┘       └──────────┘            │
│                                                                  │
│  PROACTIVO          NORMATIVA          PROPUESTA                │
│  ┌──────────┐       ┌──────────┐       ┌──────────┐            │
│  │ "Falta   │       │ "¿Que    │       │ "Quiero  │            │
│  │ definir  │       │ dice la  │       │ evaluar  │            │
│  │ la       │       │ ley sobre│       │ fauna    │            │
│  │ geometria│       │ glaciares│       │ silvestre│            │
│  │ ¿dibujar?│       │ ?"       │       │ "        │            │
│  └──────────┘       └──────────┘       └──────────┘            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Arquitectura del Sistema

### 2.1 Arquitectura de Alto Nivel

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND                                        │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                        AsistenteView.vue                               │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │  │
│  │  │  ChatPanel  │  │ MessageList │  │ InputArea   │  │ ActionPanel │  │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                    │                                         │
│                                    ▼ WebSocket / REST                        │
└────────────────────────────────────┼─────────────────────────────────────────┘
                                     │
┌────────────────────────────────────┼─────────────────────────────────────────┐
│                              BACKEND                                          │
│                                    ▼                                          │
│  ┌───────────────────────────────────────────────────────────────────────┐   │
│  │                         AsistenteService                               │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │   │
│  │  │                      AGENTE PRINCIPAL                            │  │   │
│  │  │                    (Claude claude-sonnet-4-20250514)                        │  │   │
│  │  │  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐       │  │   │
│  │  │  │  Contexto │ │  Memoria  │ │   Tools   │ │ Ejecutor  │       │  │   │
│  │  │  │  Manager  │ │  Manager  │ │  Registry │ │  Actions  │       │  │   │
│  │  │  └───────────┘ └───────────┘ └───────────┘ └───────────┘       │  │   │
│  │  └─────────────────────────────────────────────────────────────────┘  │   │
│  └───────────────────────────────────────────────────────────────────────┘   │
│                                    │                                          │
│           ┌────────────────────────┼────────────────────────┐                │
│           ▼                        ▼                        ▼                │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐          │
│  │   HERRAMIENTAS  │    │   HERRAMIENTAS  │    │   HERRAMIENTAS  │          │
│  │   INTERNAS      │    │   RAG           │    │   EXTERNAS      │          │
│  │                 │    │                 │    │                 │          │
│  │ • consultar_    │    │ • buscar_       │    │ • buscar_sea    │          │
│  │   proyecto      │    │   normativa     │    │ • buscar_eseia  │          │
│  │ • consultar_    │    │ • buscar_       │    │ • buscar_bcn    │          │
│  │   analisis      │    │   documentacion │    │                 │          │
│  │ • crear_        │    │                 │    │                 │          │
│  │   proyecto      │    │                 │    │                 │          │
│  │ • ejecutar_     │    │                 │    │                 │          │
│  │   analisis      │    │                 │    │                 │          │
│  └────────┬────────┘    └────────┬────────┘    └────────┬────────┘          │
│           │                      │                      │                    │
│           ▼                      ▼                      ▼                    │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐          │
│  │   PostgreSQL    │    │    pgvector     │    │   HTTP Client   │          │
│  │   + PostGIS     │    │   Embeddings    │    │   (httpx)       │          │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘          │
│                                                          │                   │
└──────────────────────────────────────────────────────────┼───────────────────┘
                                                           │
                              ┌─────────────────────────────┼─────────────────┐
                              │        FUENTES EXTERNAS     │                 │
                              │                             ▼                 │
                              │  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
                              │  │   SEA    │  │  e-SEIA  │  │   BCN    │    │
                              │  │ sea.gob  │  │ proyectos│  │ leychile │    │
                              │  │ .cl      │  │ aprobados│  │ .cl      │    │
                              │  └──────────┘  └──────────┘  └──────────┘    │
                              └───────────────────────────────────────────────┘
```

### 2.2 Componentes Principales

#### 2.2.1 Agente Principal

El agente es el nucleo del asistente. Utiliza el modelo Claude de Anthropic con capacidad de tool use (function calling).

```
┌─────────────────────────────────────────────────────────────────┐
│                      AGENTE PRINCIPAL                            │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    SYSTEM PROMPT                         │    │
│  │                                                          │    │
│  │  • Rol: Asistente experto en evaluacion ambiental       │    │
│  │  • Contexto: Sistema de prefactibilidad minera Chile    │    │
│  │  • Capacidades: Consultar, explicar, ejecutar, proponer │    │
│  │  • Restricciones: Confirmar acciones, citar fuentes     │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                   │
│                              ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                   CONTEXTO DINAMICO                      │    │
│  │                                                          │    │
│  │  • Usuario actual y permisos                            │    │
│  │  • Proyecto activo (si existe)                          │    │
│  │  • Ultimo analisis realizado                            │    │
│  │  • Historial de conversacion                            │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                   │
│                              ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    TOOL REGISTRY                         │    │
│  │                                                          │    │
│  │  tools = [                                              │    │
│  │    buscar_normativa,        # RAG legal                 │    │
│  │    buscar_documentacion,    # RAG sistema               │    │
│  │    consultar_proyecto,      # BD proyectos              │    │
│  │    consultar_analisis,      # BD analisis               │    │
│  │    listar_proyectos,        # BD proyectos              │    │
│  │    crear_proyecto,          # Accion + confirmacion     │    │
│  │    ejecutar_analisis,       # Accion + confirmacion     │    │
│  │    buscar_sea,              # Web SEA                   │    │
│  │    buscar_eseia,            # Web e-SEIA                │    │
│  │    buscar_bcn,              # Web BCN                   │    │
│  │    proponer_implementacion, # Arquitectura              │    │
│  │  ]                                                      │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### 2.2.2 Gestor de Contexto

Mantiene el estado de la conversacion y el contexto del usuario.

```
┌─────────────────────────────────────────────────────────────────┐
│                     CONTEXT MANAGER                              │
│                                                                  │
│  ContextoConversacion:                                          │
│  ├── session_id: UUID                                           │
│  ├── user_id: Optional[int]                                     │
│  ├── proyecto_activo: Optional[Proyecto]                        │
│  ├── analisis_activo: Optional[Analisis]                        │
│  ├── cliente_activo: Optional[Cliente]                          │
│  ├── vista_actual: str  # "dashboard", "proyecto", "mapa"       │
│  ├── acciones_pendientes: List[AccionPendiente]                 │
│  └── metadata: dict                                             │
│                                                                  │
│  Funciones:                                                      │
│  ├── actualizar_contexto(evento: EventoUI)                      │
│  ├── obtener_contexto_para_prompt() -> str                      │
│  ├── registrar_accion_pendiente(accion: Accion)                 │
│  └── limpiar_contexto()                                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### 2.2.3 Gestor de Memoria

Maneja el historial de conversaciones y memoria a largo plazo.

```
┌─────────────────────────────────────────────────────────────────┐
│                      MEMORY MANAGER                              │
│                                                                  │
│  Memoria Corto Plazo (Sesion):                                  │
│  ├── mensajes: List[Mensaje]  # Ultimos N mensajes              │
│  ├── resumen_conversacion: str  # Resumen automatico            │
│  └── tokens_usados: int                                         │
│                                                                  │
│  Memoria Largo Plazo (Persistente):                             │
│  ├── preferencias_usuario: dict                                 │
│  ├── proyectos_frecuentes: List[int]                            │
│  ├── consultas_anteriores: List[ConsultaResumen]                │
│  └── feedback_recibido: List[Feedback]                          │
│                                                                  │
│  Estrategias:                                                    │
│  ├── sliding_window: Mantener ultimos N mensajes                │
│  ├── summarization: Resumir conversaciones largas               │
│  └── retrieval: Buscar contexto relevante de memoria            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### 2.2.4 Ejecutor de Acciones

Maneja la ejecucion de acciones con confirmacion del usuario.

```
┌─────────────────────────────────────────────────────────────────┐
│                     ACTION EXECUTOR                              │
│                                                                  │
│  Flujo de Accion con Confirmacion:                              │
│                                                                  │
│  1. Usuario: "Crea un proyecto llamado Mina Norte en Atacama"   │
│                              │                                   │
│                              ▼                                   │
│  2. Agente detecta intencion de accion                          │
│                              │                                   │
│                              ▼                                   │
│  3. Genera AccionPendiente:                                     │
│     {                                                           │
│       "tipo": "crear_proyecto",                                 │
│       "parametros": {                                           │
│         "nombre": "Mina Norte",                                 │
│         "region": "Atacama"                                     │
│       },                                                        │
│       "descripcion": "Crear proyecto 'Mina Norte' en Atacama",  │
│       "requiere_confirmacion": true                             │
│     }                                                           │
│                              │                                   │
│                              ▼                                   │
│  4. Frontend muestra dialogo de confirmacion                    │
│     ┌─────────────────────────────────────┐                     │
│     │  ¿Confirmar accion?                 │                     │
│     │                                     │                     │
│     │  Crear proyecto "Mina Norte"        │                     │
│     │  Region: Atacama                    │                     │
│     │                                     │                     │
│     │  [Cancelar]  [Confirmar]            │                     │
│     └─────────────────────────────────────┘                     │
│                              │                                   │
│                              ▼                                   │
│  5. Si confirma: Ejecutar accion y reportar resultado           │
│     Si cancela: Informar al agente para respuesta alternativa   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Herramientas del Agente

### 3.1 Catalogo de Herramientas

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                          CATALOGO DE HERRAMIENTAS                             │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  CATEGORIA: RAG (Retrieval Augmented Generation)                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │ buscar_normativa                                                        │ │
│  │ ├── Descripcion: Busca en corpus legal (Ley 19300, DS 40, Guias SEA)   │ │
│  │ ├── Input: query (str), top_k (int), temas (List[str])                 │ │
│  │ ├── Output: List[FragmentoLegal]                                       │ │
│  │ └── Fuente: pgvector (tabla legal.fragmentos)                          │ │
│  │                                                                         │ │
│  │ buscar_documentacion                                                    │ │
│  │ ├── Descripcion: Busca en documentacion del sistema                    │ │
│  │ ├── Input: query (str), top_k (int)                                    │ │
│  │ ├── Output: List[FragmentoDocumentacion]                               │ │
│  │ └── Fuente: pgvector (tabla sistema.documentacion)                     │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                               │
│  CATEGORIA: Consultas Internas                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │ consultar_proyecto                                                      │ │
│  │ ├── Descripcion: Obtiene datos completos de un proyecto                │ │
│  │ ├── Input: proyecto_id (int)                                           │ │
│  │ ├── Output: ProyectoCompleto (datos + geometria + documentos)          │ │
│  │ └── Permisos: Lectura                                                  │ │
│  │                                                                         │ │
│  │ consultar_analisis                                                      │ │
│  │ ├── Descripcion: Obtiene resultados de un analisis                     │ │
│  │ ├── Input: analisis_id (int) o proyecto_id (int)                       │ │
│  │ ├── Output: AnalisisCompleto (clasificacion + triggers + alertas)      │ │
│  │ └── Permisos: Lectura                                                  │ │
│  │                                                                         │ │
│  │ listar_proyectos                                                        │ │
│  │ ├── Descripcion: Lista proyectos con filtros                           │ │
│  │ ├── Input: filtros (estado, region, cliente, fecha)                    │ │
│  │ ├── Output: List[ProyectoResumen]                                      │ │
│  │ └── Permisos: Lectura                                                  │ │
│  │                                                                         │ │
│  │ obtener_estadisticas                                                    │ │
│  │ ├── Descripcion: Obtiene KPIs del dashboard                            │ │
│  │ ├── Input: periodo (str)                                               │ │
│  │ ├── Output: EstadisticasDashboard                                      │ │
│  │ └── Permisos: Lectura                                                  │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                               │
│  CATEGORIA: Acciones (requieren confirmacion)                                │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │ crear_proyecto                                                          │ │
│  │ ├── Descripcion: Crea un nuevo proyecto                                │ │
│  │ ├── Input: nombre, region, comuna, tipo_mineria, cliente_id            │ │
│  │ ├── Output: Proyecto creado                                            │ │
│  │ ├── Confirmacion: REQUERIDA                                            │ │
│  │ └── Permisos: Escritura                                                │ │
│  │                                                                         │ │
│  │ ejecutar_analisis                                                       │ │
│  │ ├── Descripcion: Ejecuta analisis de prefactibilidad                   │ │
│  │ ├── Input: proyecto_id, tipo (rapido/completo)                         │ │
│  │ ├── Output: ResultadoAnalisis                                          │ │
│  │ ├── Confirmacion: REQUERIDA                                            │ │
│  │ └── Permisos: Escritura                                                │ │
│  │                                                                         │ │
│  │ actualizar_proyecto                                                     │ │
│  │ ├── Descripcion: Actualiza datos de un proyecto                        │ │
│  │ ├── Input: proyecto_id, campos_a_actualizar                            │ │
│  │ ├── Output: Proyecto actualizado                                       │ │
│  │ ├── Confirmacion: REQUERIDA                                            │ │
│  │ └── Permisos: Escritura                                                │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                               │
│  CATEGORIA: Fuentes Externas                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │ buscar_sea                                                              │ │
│  │ ├── Descripcion: Busca informacion en sitio del SEA                    │ │
│  │ ├── Input: query (str), seccion (str)                                  │ │
│  │ ├── Output: List[ResultadoSEA]                                         │ │
│  │ ├── URL Base: https://www.sea.gob.cl                                   │ │
│  │ └── Metodo: Web scraping + cache                                       │ │
│  │                                                                         │ │
│  │ buscar_eseia                                                            │ │
│  │ ├── Descripcion: Busca proyectos aprobados en e-SEIA                   │ │
│  │ ├── Input: nombre, region, tipo, anio                                  │ │
│  │ ├── Output: List[ProyectoESEIA]                                        │ │
│  │ ├── URL Base: https://seia.sea.gob.cl                                  │ │
│  │ └── Metodo: API/scraping + cache                                       │ │
│  │                                                                         │ │
│  │ buscar_bcn                                                              │ │
│  │ ├── Descripcion: Busca normativa en Biblioteca del Congreso            │ │
│  │ ├── Input: tipo_norma, numero, articulo                                │ │
│  │ ├── Output: TextoNormativo                                             │ │
│  │ ├── URL Base: https://www.bcn.cl/leychile                              │ │
│  │ └── Metodo: API BCN + cache                                            │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                               │
│  CATEGORIA: Meta/Sistema                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │ proponer_implementacion                                                 │ │
│  │ ├── Descripcion: Genera propuesta tecnica para nueva funcionalidad     │ │
│  │ ├── Input: objetivo (str), contexto (str)                              │ │
│  │ ├── Output: PropuestaTecnica (arquitectura, archivos, estimacion)      │ │
│  │ └── Nota: Usa conocimiento del sistema via RAG documentacion           │ │
│  │                                                                         │ │
│  │ explicar_sistema                                                        │ │
│  │ ├── Descripcion: Explica componentes del sistema                       │ │
│  │ ├── Input: componente (str)                                            │ │
│  │ ├── Output: Explicacion detallada                                      │ │
│  │ └── Fuente: RAG documentacion + CLAUDE.md                              │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                               │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Esquema de Herramienta (Tool Schema)

Cada herramienta sigue el formato de Anthropic Tool Use:

```json
{
  "name": "buscar_normativa",
  "description": "Busca fragmentos relevantes en el corpus legal del sistema (Ley 19.300, DS 40, Guias SEA). Usa esta herramienta cuando el usuario pregunte sobre normativa ambiental, requisitos legales, o fundamentos de clasificacion DIA/EIA.",
  "input_schema": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "Consulta de busqueda semantica"
      },
      "top_k": {
        "type": "integer",
        "description": "Numero de resultados a retornar",
        "default": 5
      },
      "temas": {
        "type": "array",
        "items": {"type": "string"},
        "description": "Filtrar por temas especificos (ej: 'areas_protegidas', 'glaciares')"
      }
    },
    "required": ["query"]
  }
}
```

---

## 4. Flujos de Datos

### 4.1 Flujo de Consulta Simple

```
Usuario                    Frontend                   Backend                    LLM
   │                          │                          │                         │
   │  "¿Que es el Art. 11?"   │                          │                         │
   │ ─────────────────────────>│                          │                         │
   │                          │   POST /asistente/chat   │                         │
   │                          │ ─────────────────────────>│                         │
   │                          │                          │  Construir prompt       │
   │                          │                          │  + contexto + tools     │
   │                          │                          │ ─────────────────────────>
   │                          │                          │                         │
   │                          │                          │   Tool: buscar_normativa│
   │                          │                          │ <─────────────────────────
   │                          │                          │                         │
   │                          │                          │   [Ejecutar busqueda    │
   │                          │                          │    en pgvector]         │
   │                          │                          │                         │
   │                          │                          │   Resultado + contexto  │
   │                          │                          │ ─────────────────────────>
   │                          │                          │                         │
   │                          │                          │   Respuesta final       │
   │                          │                          │ <─────────────────────────
   │                          │   Respuesta + fuentes    │                         │
   │                          │ <─────────────────────────│                         │
   │  Respuesta formateada    │                          │                         │
   │ <─────────────────────────│                          │                         │
   │                          │                          │                         │
```

### 4.2 Flujo de Accion con Confirmacion

```
Usuario                    Frontend                   Backend                    LLM
   │                          │                          │                         │
   │ "Crea proyecto Mina X"   │                          │                         │
   │ ─────────────────────────>│                          │                         │
   │                          │   POST /asistente/chat   │                         │
   │                          │ ─────────────────────────>│                         │
   │                          │                          │ ─────────────────────────>
   │                          │                          │                         │
   │                          │                          │  Tool: crear_proyecto   │
   │                          │                          │  (requiere_confirm=true)│
   │                          │                          │ <─────────────────────────
   │                          │                          │                         │
   │                          │  Accion pendiente        │                         │
   │                          │ <─────────────────────────│                         │
   │                          │                          │                         │
   │  Dialogo confirmacion    │                          │                         │
   │ <─────────────────────────│                          │                         │
   │                          │                          │                         │
   │  [Confirmar]             │                          │                         │
   │ ─────────────────────────>│                          │                         │
   │                          │ POST /asistente/confirm  │                         │
   │                          │ ─────────────────────────>│                         │
   │                          │                          │                         │
   │                          │                          │  [Ejecutar accion]      │
   │                          │                          │  [Crear proyecto en BD] │
   │                          │                          │                         │
   │                          │                          │  Resultado a LLM        │
   │                          │                          │ ─────────────────────────>
   │                          │                          │                         │
   │                          │                          │  Respuesta confirmacion │
   │                          │                          │ <─────────────────────────
   │                          │  "Proyecto creado: #123" │                         │
   │                          │ <─────────────────────────│                         │
   │  Mensaje exito           │                          │                         │
   │ <─────────────────────────│                          │                         │
```

### 4.3 Flujo Proactivo

```
Sistema                    Backend                   Frontend                  Usuario
   │                          │                          │                         │
   │  Evento: proyecto sin    │                          │                         │
   │  geometria abierto       │                          │                         │
   │ ─────────────────────────>│                          │                         │
   │                          │                          │                         │
   │                          │  Evaluar condiciones     │                         │
   │                          │  proactivas              │                         │
   │                          │                          │                         │
   │                          │  Generar sugerencia      │                         │
   │                          │                          │                         │
   │                          │  WebSocket: sugerencia   │                         │
   │                          │ ─────────────────────────>│                         │
   │                          │                          │                         │
   │                          │                          │  Notificacion chat      │
   │                          │                          │ ─────────────────────────>
   │                          │                          │                         │
   │                          │                          │  "Este proyecto no      │
   │                          │                          │   tiene geometria.      │
   │                          │                          │   ¿Desea dibujarla?"    │
   │                          │                          │                         │
   │                          │                          │  [Ir al mapa]           │
```

---

## 5. Modelo de Datos

### 5.1 Esquema de Base de Datos

```sql
-- Nuevo schema para el asistente
CREATE SCHEMA IF NOT EXISTS asistente;

-- Conversaciones
CREATE TABLE asistente.conversaciones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL,
    user_id INTEGER REFERENCES proyectos.clientes(id),
    titulo VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Mensajes
CREATE TABLE asistente.mensajes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversacion_id UUID REFERENCES asistente.conversaciones(id) ON DELETE CASCADE,
    rol VARCHAR(20) NOT NULL CHECK (rol IN ('user', 'assistant', 'system', 'tool')),
    contenido TEXT NOT NULL,
    tool_calls JSONB,  -- Para mensajes del asistente con tool calls
    tool_call_id VARCHAR(100),  -- Para mensajes de tipo tool
    tokens_input INTEGER,
    tokens_output INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Acciones pendientes de confirmacion
CREATE TABLE asistente.acciones_pendientes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversacion_id UUID REFERENCES asistente.conversaciones(id) ON DELETE CASCADE,
    tipo VARCHAR(50) NOT NULL,
    parametros JSONB NOT NULL,
    descripcion TEXT NOT NULL,
    estado VARCHAR(20) DEFAULT 'pendiente' CHECK (estado IN ('pendiente', 'confirmada', 'cancelada', 'expirada')),
    resultado JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() + INTERVAL '5 minutes'
);

-- Memoria a largo plazo
CREATE TABLE asistente.memoria_usuario (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER REFERENCES proyectos.clientes(id),
    tipo VARCHAR(50) NOT NULL,  -- 'preferencia', 'consulta_frecuente', 'feedback'
    clave VARCHAR(100),
    valor JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Documentacion del sistema (para RAG)
CREATE TABLE asistente.documentacion (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tipo VARCHAR(50) NOT NULL,  -- 'archivo', 'docstring', 'comentario'
    ruta VARCHAR(500),
    titulo VARCHAR(255),
    contenido TEXT NOT NULL,
    embedding vector(384),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indice para busqueda vectorial
CREATE INDEX idx_documentacion_embedding ON asistente.documentacion
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Indices adicionales
CREATE INDEX idx_conversaciones_session ON asistente.conversaciones(session_id);
CREATE INDEX idx_conversaciones_user ON asistente.conversaciones(user_id);
CREATE INDEX idx_mensajes_conversacion ON asistente.mensajes(conversacion_id);
CREATE INDEX idx_acciones_estado ON asistente.acciones_pendientes(estado);
CREATE INDEX idx_memoria_user ON asistente.memoria_usuario(user_id);
```

### 5.2 Modelos Pydantic

```python
# Mensaje
class MensajeBase(BaseModel):
    rol: Literal["user", "assistant", "system", "tool"]
    contenido: str

class MensajeUsuario(MensajeBase):
    rol: Literal["user"] = "user"
    proyecto_contexto_id: Optional[int] = None

class MensajeAsistente(MensajeBase):
    rol: Literal["assistant"] = "assistant"
    tool_calls: Optional[List[ToolCall]] = None
    fuentes: Optional[List[Fuente]] = None

class MensajeTool(MensajeBase):
    rol: Literal["tool"] = "tool"
    tool_call_id: str
    tool_name: str

# Acciones
class AccionPendiente(BaseModel):
    id: UUID
    tipo: str
    parametros: dict
    descripcion: str
    requiere_confirmacion: bool = True
    expires_at: datetime

class ConfirmacionAccion(BaseModel):
    accion_id: UUID
    confirmada: bool
    comentario: Optional[str] = None

# Respuesta del chat
class RespuestaChat(BaseModel):
    mensaje: MensajeAsistente
    accion_pendiente: Optional[AccionPendiente] = None
    sugerencias: List[str] = []
    contexto_actualizado: bool = False
```

---

## 6. Integraciones Externas

### 6.1 SEA (Servicio de Evaluacion Ambiental)

```
┌─────────────────────────────────────────────────────────────────┐
│                    INTEGRACION SEA                               │
│                                                                  │
│  URL Base: https://www.sea.gob.cl                               │
│                                                                  │
│  Secciones a indexar:                                           │
│  ├── /evaluacion-ambiental/guias-y-criterios/                   │
│  │   └── Guias de evaluacion por sector                         │
│  ├── /evaluacion-ambiental/participacion-ciudadana/             │
│  │   └── Procedimientos PAC                                     │
│  ├── /documentos/                                               │
│  │   └── Documentos tecnicos y manuales                         │
│  └── /noticias/                                                 │
│      └── Actualizaciones normativas                             │
│                                                                  │
│  Estrategia:                                                    │
│  1. Scraping periodico (1x/semana)                              │
│  2. Cache en Redis (TTL: 24h)                                   │
│  3. Indexacion en pgvector para RAG                             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 e-SEIA (Sistema Electronico de Evaluacion)

```
┌─────────────────────────────────────────────────────────────────┐
│                    INTEGRACION e-SEIA                            │
│                                                                  │
│  URL Base: https://seia.sea.gob.cl                              │
│                                                                  │
│  Datos a consultar:                                             │
│  ├── Proyectos por region y tipo                                │
│  ├── Resoluciones de Calificacion Ambiental (RCA)               │
│  ├── Addendums y respuestas ICSARA                              │
│  └── Estadisticas de evaluacion                                 │
│                                                                  │
│  Casos de uso:                                                  │
│  ├── "¿Hay proyectos similares aprobados en esta zona?"         │
│  ├── "¿Que medidas de mitigacion usaron proyectos similares?"   │
│  └── "¿Cual es el tiempo promedio de evaluacion para DIA?"      │
│                                                                  │
│  Estrategia:                                                    │
│  1. API publica si disponible                                   │
│  2. Scraping con Playwright si no hay API                       │
│  3. Cache por proyecto (TTL: 7 dias)                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 6.3 BCN (Biblioteca del Congreso Nacional)

```
┌─────────────────────────────────────────────────────────────────┐
│                    INTEGRACION BCN                               │
│                                                                  │
│  URL Base: https://www.bcn.cl/leychile                          │
│  API: https://www.leychile.cl/servicios                         │
│                                                                  │
│  Normativa relevante:                                           │
│  ├── Ley 19.300 - Bases Generales del Medio Ambiente            │
│  ├── DS 40/2012 - Reglamento SEIA                               │
│  ├── Ley 20.417 - Superintendencia del Medio Ambiente           │
│  ├── Ley 20.600 - Tribunales Ambientales                        │
│  └── Normativa sectorial (mineria, aguas, etc.)                 │
│                                                                  │
│  Estrategia:                                                    │
│  1. API BCN para texto consolidado                              │
│  2. Deteccion de modificaciones                                 │
│  3. Actualizacion automatica del corpus                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 7. Modo Proactivo

### 7.1 Triggers Proactivos

El asistente puede iniciar conversaciones basado en eventos del sistema:

```
┌─────────────────────────────────────────────────────────────────┐
│                   TRIGGERS PROACTIVOS                            │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ TRIGGER: proyecto_sin_geometria                          │    │
│  │ Condicion: proyecto.estado == 'borrador' AND             │    │
│  │            proyecto.geometria IS NULL AND                │    │
│  │            dias_desde_creacion > 1                       │    │
│  │ Mensaje: "El proyecto {nombre} no tiene geometria        │    │
│  │          definida. ¿Desea ir al mapa para dibujarla?"    │    │
│  │ Accion sugerida: navegar_a('/proyectos/{id}/mapa')       │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ TRIGGER: analisis_desactualizado                         │    │
│  │ Condicion: proyecto.geometria_modificada_at >            │    │
│  │            ultimo_analisis.fecha                         │    │
│  │ Mensaje: "La geometria del proyecto fue modificada       │    │
│  │          despues del ultimo analisis. ¿Desea             │    │
│  │          ejecutar un nuevo analisis?"                    │    │
│  │ Accion sugerida: ejecutar_analisis(proyecto_id)          │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ TRIGGER: alertas_criticas_sin_revisar                    │    │
│  │ Condicion: analisis.alertas_criticas > 0 AND             │    │
│  │            NOT analisis.alertas_revisadas                │    │
│  │ Mensaje: "El analisis tiene {n} alertas criticas que     │    │
│  │          requieren atencion. ¿Desea revisarlas?"         │    │
│  │ Accion sugerida: navegar_a('/proyectos/{id}/analisis')   │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ TRIGGER: normativa_actualizada                           │    │
│  │ Condicion: nueva_version_normativa_detectada             │    │
│  │ Mensaje: "Se ha actualizado la normativa {nombre}.       │    │
│  │          Esto podria afectar proyectos en evaluacion."   │    │
│  │ Accion sugerida: ver_cambios_normativa()                 │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 7.2 Configuracion de Proactividad

```python
class ConfiguracionProactividad(BaseModel):
    habilitado: bool = True
    triggers_activos: List[str] = [
        "proyecto_sin_geometria",
        "analisis_desactualizado",
        "alertas_criticas_sin_revisar",
        "normativa_actualizada"
    ]
    frecuencia_verificacion_minutos: int = 5
    max_notificaciones_por_hora: int = 3
    horario_activo: Tuple[int, int] = (8, 20)  # 8am - 8pm
```

---

## 8. Seguridad y Permisos

### 8.1 Modelo de Permisos

```
┌─────────────────────────────────────────────────────────────────┐
│                    MODELO DE PERMISOS                            │
│                                                                  │
│  Niveles de acceso por herramienta:                             │
│                                                                  │
│  ┌──────────────────────┬───────────┬───────────┬───────────┐   │
│  │ Herramienta          │ Lectura   │ Escritura │ Admin     │   │
│  ├──────────────────────┼───────────┼───────────┼───────────┤   │
│  │ buscar_normativa     │    ✓      │     ✓     │     ✓     │   │
│  │ buscar_documentacion │    ✓      │     ✓     │     ✓     │   │
│  │ consultar_proyecto   │    ✓      │     ✓     │     ✓     │   │
│  │ consultar_analisis   │    ✓      │     ✓     │     ✓     │   │
│  │ listar_proyectos     │    ✓      │     ✓     │     ✓     │   │
│  │ crear_proyecto       │    ✗      │     ✓     │     ✓     │   │
│  │ ejecutar_analisis    │    ✗      │     ✓     │     ✓     │   │
│  │ actualizar_proyecto  │    ✗      │     ✓     │     ✓     │   │
│  │ buscar_sea           │    ✓      │     ✓     │     ✓     │   │
│  │ buscar_eseia         │    ✓      │     ✓     │     ✓     │   │
│  │ buscar_bcn           │    ✓      │     ✓     │     ✓     │   │
│  │ proponer_implementa  │    ✗      │     ✗     │     ✓     │   │
│  └──────────────────────┴───────────┴───────────┴───────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 8.2 Sanitizacion de Entradas

```python
class SanitizadorEntrada:
    """
    Sanitiza entradas del usuario antes de pasarlas al agente.
    """

    # Patrones a bloquear (prompt injection)
    PATRONES_BLOQUEADOS = [
        r"ignore previous instructions",
        r"ignore all previous",
        r"disregard your instructions",
        r"you are now",
        r"new instructions:",
        r"system prompt:",
    ]

    # Longitud maxima de mensaje
    MAX_LENGTH = 4000

    def sanitizar(self, texto: str) -> str:
        # 1. Truncar si excede limite
        texto = texto[:self.MAX_LENGTH]

        # 2. Detectar intentos de inyeccion
        for patron in self.PATRONES_BLOQUEADOS:
            if re.search(patron, texto, re.IGNORECASE):
                raise ValueError("Contenido no permitido detectado")

        # 3. Escapar caracteres especiales
        texto = html.escape(texto)

        return texto
```

---

## 9. Metricas y Observabilidad

### 9.1 Metricas a Capturar

```
┌─────────────────────────────────────────────────────────────────┐
│                    METRICAS DEL ASISTENTE                        │
│                                                                  │
│  Uso:                                                           │
│  ├── total_conversaciones                                       │
│  ├── total_mensajes                                             │
│  ├── mensajes_por_conversacion (promedio)                       │
│  ├── usuarios_activos (diario/semanal/mensual)                  │
│  └── tasa_uso_herramientas (por tipo)                           │
│                                                                  │
│  Rendimiento:                                                   │
│  ├── latencia_respuesta_p50                                     │
│  ├── latencia_respuesta_p95                                     │
│  ├── tokens_por_mensaje (input/output)                          │
│  ├── costo_por_conversacion                                     │
│  └── tasa_error (por tipo)                                      │
│                                                                  │
│  Calidad:                                                       │
│  ├── tasa_confirmacion_acciones                                 │
│  ├── tasa_cancelacion_acciones                                  │
│  ├── feedback_positivo/negativo                                 │
│  └── consultas_sin_respuesta                                    │
│                                                                  │
│  Herramientas:                                                  │
│  ├── llamadas_por_herramienta                                   │
│  ├── tasa_exito_por_herramienta                                 │
│  ├── latencia_por_herramienta                                   │
│  └── cache_hit_rate (fuentes externas)                          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 9.2 Logging Estructurado

```python
# Ejemplo de log estructurado
logger.info(
    "asistente_respuesta",
    conversation_id=str(conversation_id),
    user_id=user_id,
    message_length=len(mensaje),
    tools_called=["buscar_normativa", "consultar_proyecto"],
    latency_ms=latency,
    tokens_input=tokens_in,
    tokens_output=tokens_out,
    has_action=True,
    action_type="crear_proyecto"
)
```

---

## 10. Consideraciones de Escalabilidad

### 10.1 Estrategias de Cache

```
┌─────────────────────────────────────────────────────────────────┐
│                    ESTRATEGIA DE CACHE                           │
│                                                                  │
│  Redis Cache Layers:                                            │
│                                                                  │
│  L1: Respuestas frecuentes                                      │
│  ├── Key: hash(query_normalizada)                               │
│  ├── TTL: 1 hora                                                │
│  └── Uso: Preguntas FAQ (Art. 11, procedimientos)               │
│                                                                  │
│  L2: Resultados de herramientas                                 │
│  ├── Key: tool:{nombre}:{hash(params)}                          │
│  ├── TTL: Variable por herramienta                              │
│  │   ├── buscar_normativa: 24h                                  │
│  │   ├── buscar_sea: 6h                                         │
│  │   ├── buscar_eseia: 24h                                      │
│  │   └── consultar_proyecto: 5min                               │
│  └── Invalidacion: Por evento (update proyecto)                 │
│                                                                  │
│  L3: Embeddings                                                 │
│  ├── Key: emb:{hash(texto)}                                     │
│  ├── TTL: 7 dias                                                │
│  └── Uso: Evitar recalcular embeddings                          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 10.2 Rate Limiting

```python
class RateLimiter:
    """
    Limites de tasa para el asistente.
    """

    LIMITES = {
        "mensajes_por_minuto": 10,
        "mensajes_por_hora": 100,
        "acciones_por_hora": 20,
        "busquedas_externas_por_hora": 30,
    }

    async def verificar_limite(
        self,
        user_id: int,
        tipo: str
    ) -> bool:
        key = f"rate:{user_id}:{tipo}"
        count = await redis.incr(key)
        if count == 1:
            await redis.expire(key, self._ttl_for_tipo(tipo))
        return count <= self.LIMITES[tipo]
```

---

## 11. Plan de Contingencia

### 11.1 Fallbacks

```
┌─────────────────────────────────────────────────────────────────┐
│                    PLAN DE FALLBACKS                             │
│                                                                  │
│  Si LLM no disponible:                                          │
│  ├── Mostrar mensaje: "Servicio temporalmente no disponible"    │
│  ├── Ofrecer busqueda basica en FAQ                             │
│  └── Log para alertar a operaciones                             │
│                                                                  │
│  Si fuente externa falla:                                       │
│  ├── Usar cache si disponible (aunque expirado)                 │
│  ├── Informar al usuario: "No se pudo consultar [fuente]"       │
│  └── Continuar con informacion local                            │
│                                                                  │
│  Si base de datos lenta:                                        │
│  ├── Timeout de consultas: 10s                                  │
│  ├── Respuesta parcial si posible                               │
│  └── Cache agresivo de consultas frecuentes                     │
│                                                                  │
│  Si accion falla:                                               │
│  ├── Rollback automatico si aplica                              │
│  ├── Informar al usuario con detalle del error                  │
│  └── Ofrecer alternativas o reintentos                          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 12. Glosario

| Termino | Definicion |
|---------|------------|
| **Agente** | Sistema de IA que puede usar herramientas para completar tareas |
| **Tool Use** | Capacidad del LLM de llamar funciones externas |
| **RAG** | Retrieval Augmented Generation - busqueda + generacion |
| **Proactivo** | Iniciado por el sistema, no por el usuario |
| **Confirmacion** | Aprobacion explicita del usuario para ejecutar accion |
| **Contexto** | Informacion del estado actual (proyecto, usuario, vista) |
| **Memoria** | Historial de conversacion y preferencias persistentes |

---

## 13. Referencias

- [Anthropic Tool Use Documentation](https://docs.anthropic.com/claude/docs/tool-use)
- [SEA - Servicio de Evaluacion Ambiental](https://www.sea.gob.cl)
- [e-SEIA](https://seia.sea.gob.cl)
- [Biblioteca del Congreso Nacional](https://www.bcn.cl/leychile)
- [Ley 19.300](https://www.bcn.cl/leychile/navegar?idNorma=30667)
- [DS 40/2012 - Reglamento SEIA](https://www.bcn.cl/leychile/navegar?idNorma=1053563)

---

*Documento de Arquitectura v1.0 - Sistema de Prefactibilidad Ambiental Minera*
