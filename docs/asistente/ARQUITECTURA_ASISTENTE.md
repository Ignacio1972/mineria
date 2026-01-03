# Arquitectura: Sistema de Asistentes IA

> **Versión:** 2.0 | **Fecha:** Enero 2026 | **Cambio principal:** Separación Asistente Global/Proyecto

---

## 1. Visión General

El sistema implementa **dos asistentes diferenciados** según el contexto de uso:

| Asistente | Propósito | Dónde |
|-----------|-----------|-------|
| **Asistente Global** | Hub de información: normativa, comparaciones, crear proyectos | Vista `/asistente` sin proyecto |
| **Asistente de Proyecto** | Guiar elaboración EIA/DIA, completar ficha acumulativa | Vista `/proyectos/{id}` o con proyecto en contexto |

---

## 2. Diagrama de Arquitectura

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                     Rutas y Vistas                                   │    │
│  │  ┌─────────────────────┐         ┌────────────────────────────┐    │    │
│  │  │   AsistenteView     │         │   ProyectoDetalleView      │    │    │
│  │  │ vista_actual:       │         │ vista_actual:              │    │    │
│  │  │ "asistente-global"  │         │ "proyecto-detalle"         │    │    │
│  │  └──────────┬──────────┘         └─────────────┬──────────────┘    │    │
│  │             │                                  │                    │    │
│  │             └──────────────┬───────────────────┘                    │    │
│  │                            ▼                                        │    │
│  │  ┌──────────────────────────────────────────────────────────────┐  │    │
│  │  │                    ChatAsistente.vue                          │  │    │
│  │  │  - Panel de chat (70%)                                        │  │    │
│  │  │  - Ficha acumulativa (30%) [solo en proyecto]                 │  │    │
│  │  └──────────────────────────────────────────────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└───────────────────────────────┬─────────────────────────────────────────────┘
                                │ POST /api/v1/asistente/chat
                                │ { vista_actual, proyecto_contexto_id }
                                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              BACKEND                                         │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                       AsistenteService                                │   │
│  │                                                                       │   │
│  │   ┌─────────────────────────────────────────────────────────────┐    │   │
│  │   │              SELECTOR DE CONTEXTO                            │    │   │
│  │   │                                                              │    │   │
│  │   │   if "proyecto" in vista_actual OR proyecto_id:              │    │   │
│  │   │       → SYSTEM_PROMPT_PROYECTO                               │    │   │
│  │   │       → Herramientas: PROYECTO + AMBOS                       │    │   │
│  │   │   else:                                                      │    │   │
│  │   │       → SYSTEM_PROMPT_GLOBAL                                 │    │   │
│  │   │       → Herramientas: GLOBAL + AMBOS                         │    │   │
│  │   └─────────────────────────────────────────────────────────────┘    │   │
│  │                              │                                        │   │
│  │           ┌──────────────────┴──────────────────┐                    │   │
│  │           ▼                                     ▼                    │   │
│  │   ┌─────────────────┐               ┌─────────────────┐              │   │
│  │   │ CONTEXTO GLOBAL │               │CONTEXTO PROYECTO│              │   │
│  │   │                 │               │                 │              │   │
│  │   │ Herramientas:   │               │ Herramientas:   │              │   │
│  │   │ • crear_proyecto│               │ • consultar_*   │              │   │
│  │   │ • listar_proyec │               │ • guardar_ficha │              │   │
│  │   │ • obtener_stats │               │ • ejecutar_anal │              │   │
│  │   │ + buscar_norma  │               │ • evaluar_umbral│              │   │
│  │   │ + buscar_doc    │               │ • obtener_config│              │   │
│  │   │ + buscar_web    │               │ + buscar_norma  │              │   │
│  │   └─────────────────┘               │ + buscar_doc    │              │   │
│  │                                     │ + buscar_web    │              │   │
│  │                                     └─────────────────┘              │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│           ┌────────────────────────┼────────────────────────┐               │
│           ▼                        ▼                        ▼               │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐         │
│  │   GIS Service   │    │   RAG Service   │    │ ConfigIndustria │         │
│  │   (existente)   │    │   (existente)   │    │   Service       │         │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘         │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            BASE DE DATOS                                     │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐                 │
│  │ proyectos.*    │  │asistente_config│  │ legal.*        │                 │
│  │ (ficha)        │  │ (industrias)   │  │ (corpus RAG)   │                 │
│  └────────────────┘  └────────────────┘  └────────────────┘                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Los Dos Asistentes

### 3.1 Asistente Global (Hub de Información)

**Cuándo se activa:** Vista `/asistente` sin proyecto seleccionado

**Propósito:**
- Consultas generales sobre normativa ambiental chilena
- Crear nuevos proyectos
- Listar y buscar proyectos existentes
- Estadísticas del sistema
- Búsquedas web de información actualizada

**System Prompt:**
```
Eres el Asistente General del Sistema de Prefactibilidad Ambiental.

Tu rol es ser un HUB DE INFORMACIÓN para usuarios que:
1. Buscan información sobre normativa ambiental chilena
2. Quieren crear nuevos proyectos
3. Necesitan consultas generales sobre el SEIA
4. Quieren comparar proyectos o ver estadísticas

CAPACIDADES EN ESTE MODO:
- Buscar en corpus legal (Ley 19.300, DS 40, guías SEA)
- Crear nuevos proyectos (requiere confirmación)
- Listar proyectos existentes
- Mostrar estadísticas del sistema
- Buscar información actualizada en la web

LIMITACIONES:
- NO tienes acceso a un proyecto específico
- NO puedes ejecutar análisis ni guardar en fichas
- Para trabajo detallado en un proyecto, sugiere ir a la vista del proyecto
```

**Herramientas disponibles:**
| Herramienta | Descripción |
|-------------|-------------|
| `crear_proyecto` | Crear nuevo proyecto (con confirmación) |
| `listar_proyectos` | Listar proyectos con filtros |
| `obtener_estadisticas` | KPIs del sistema |
| `buscar_normativa` | Búsqueda RAG en corpus legal |
| `buscar_documentacion` | Documentación del sistema |
| `buscar_web_actualizada` | Búsqueda web (Perplexity) |
| `obtener_estadisticas_corpus` | Info del corpus RAG |

---

### 3.2 Asistente de Proyecto (Guía EIA/DIA)

**Cuándo se activa:**
- Vista `/proyectos/{id}`
- Cualquier vista con `proyecto_contexto_id` definido

**Propósito:**
- Guiar la elaboración del EIA/DIA paso a paso
- Completar la ficha acumulativa del proyecto
- Evaluar umbrales SEIA automáticamente
- Ejecutar análisis de prefactibilidad
- Identificar PAS aplicables

**System Prompt:**
```
Eres el Asistente Especializado para el proyecto "{proyecto_nombre}".

Tu objetivo es GUIAR al usuario para completar la evaluación ambiental (DIA o EIA).

FLUJO DE TRABAJO:

1. IDENTIFICAR TIPO DE PROYECTO
   - Si no está definido, pregunta qué tipo de proyecto es
   - Usa 'obtener_config_industria' para cargar configuración del sector
   - Muestra subtipos disponibles si aplica

2. RECOPILAR INFORMACIÓN GUIADA
   - Usa 'obtener_siguiente_pregunta' para seguir el árbol de preguntas
   - Guarda cada respuesta con 'guardar_ficha'
   - Si el usuario da un valor numérico (tonelaje, potencia, superficie):
     a) Guárdalo con guardar_ficha
     b) Evalúa con 'evaluar_umbral_seia' si cumple umbrales SEIA
     c) Informa el resultado al usuario

3. EVALUAR UMBRALES AUTOMÁTICAMENTE
   - Cuando detectes valores como tonelaje, MW, hectáreas, viviendas
   - Evalúa contra umbrales SEIA configurados
   - Informa si el proyecto ingresaría al SEIA por ese parámetro

4. ANÁLISIS Y DIAGNÓSTICO
   - Cuando tengas suficiente información, sugiere ejecutar análisis
   - Explica la clasificación (DIA/EIA) con fundamento legal

CONTEXTO DEL PROYECTO:
- Proyecto ID: {proyecto_id}
- Estado: {proyecto_estado}
- Tiene geometría: {tiene_geometria}
- Tiene análisis: {tiene_analisis}
```

**Herramientas disponibles:**
| Herramienta | Descripción |
|-------------|-------------|
| `consultar_proyecto` | Datos completos del proyecto |
| `consultar_analisis` | Resultados de análisis |
| `ejecutar_analisis` | Ejecutar prefactibilidad (con confirmación) |
| `actualizar_proyecto` | Modificar datos (con confirmación) |
| `guardar_ficha` | Guardar en ficha acumulativa (con confirmación) |
| `obtener_config_industria` | Config por tipo de proyecto |
| `evaluar_umbral_seia` | Evaluar si cumple umbral SEIA |
| `obtener_siguiente_pregunta` | Siguiente pregunta del árbol |
| `explicar_clasificacion` | Explicar DIA/EIA del análisis |
| `buscar_normativa` | Búsqueda RAG en corpus legal |
| `buscar_documentacion` | Documentación del sistema |
| `buscar_web_actualizada` | Búsqueda web (Perplexity) |
| `obtener_estadisticas_corpus` | Info del corpus RAG |

---

## 4. Clasificación de Herramientas por Contexto

```python
class ContextoHerramienta(str, Enum):
    GLOBAL = "global"      # Solo en asistente global
    PROYECTO = "proyecto"  # Solo con proyecto en contexto
    AMBOS = "ambos"        # Disponible en ambos contextos
```

### Tabla completa de clasificación

| Herramienta | Contexto | Categoría | Confirmación |
|-------------|----------|-----------|--------------|
| `crear_proyecto` | GLOBAL | accion | Sí |
| `listar_proyectos` | GLOBAL | consulta | No |
| `obtener_estadisticas` | GLOBAL | consulta | No |
| `consultar_proyecto` | PROYECTO | consulta | No |
| `consultar_analisis` | PROYECTO | consulta | No |
| `ejecutar_analisis` | PROYECTO | accion | Sí |
| `actualizar_proyecto` | PROYECTO | accion | Sí |
| `guardar_ficha` | PROYECTO | accion | Sí |
| `obtener_config_industria` | PROYECTO | consulta | No |
| `evaluar_umbral_seia` | PROYECTO | consulta | No |
| `obtener_siguiente_pregunta` | PROYECTO | consulta | No |
| `buscar_normativa` | AMBOS | rag | No |
| `buscar_documentacion` | AMBOS | rag | No |
| `explicar_clasificacion` | AMBOS | rag | No |
| `obtener_estadisticas_corpus` | AMBOS | rag | No |
| `buscar_web_actualizada` | AMBOS | externa | No |

---

## 5. Estructura de Código

### Backend

```
backend/app/
├── api/v1/endpoints/
│   ├── asistente.py              # Endpoints del asistente
│   └── config_industria.py       # CRUD configuración
│
├── services/
│   ├── asistente/
│   │   ├── service.py            # Orquestador principal
│   │   │   ├── SYSTEM_PROMPT_GLOBAL
│   │   │   ├── SYSTEM_PROMPT_PROYECTO
│   │   │   └── Selector de contexto
│   │   │
│   │   ├── tools/
│   │   │   ├── base.py           # ContextoHerramienta, RegistroHerramientas
│   │   │   ├── consultas.py      # Consultas (GLOBAL/PROYECTO)
│   │   │   ├── rag.py            # RAG (AMBOS)
│   │   │   ├── externa.py        # APIs externas (AMBOS)
│   │   │   ├── config_industria.py  # Config industria (PROYECTO)
│   │   │   └── acciones/
│   │   │       ├── crear_proyecto.py      # GLOBAL
│   │   │       ├── ejecutar_analisis.py   # PROYECTO
│   │   │       ├── actualizar_proyecto.py # PROYECTO
│   │   │       └── guardar_ficha.py       # PROYECTO
│   │   │
│   │   ├── memoria.py            # Gestión historial
│   │   └── contexto.py           # Constructor contexto LLM
│   │
│   └── config_industria/
│       ├── service.py            # ConfigIndustriaService
│       ├── umbrales.py           # Evaluador de umbrales
│       └── pas.py                # Identificador de PAS
│
├── db/models/
│   └── asistente.py              # Modelos BD
│
└── schemas/
    └── asistente.py              # Schemas Pydantic
```

### Frontend

```
frontend/src/
├── views/
│   ├── AsistenteView.vue         # Asistente global
│   └── ProyectoDetalleView.vue   # Incluye asistente de proyecto
│
├── components/asistente/
│   ├── ChatAsistente.vue         # Componente principal
│   ├── MensajeChat.vue           # Burbuja de mensaje
│   ├── FichaAcumulativa.vue      # Panel lateral (solo proyecto)
│   └── SelectorTipoProyecto.vue  # Selector industria
│
├── stores/
│   ├── asistente.ts              # Estado del asistente
│   └── configIndustria.ts        # Cache de config
│
└── services/
    ├── asistente.ts              # API calls
    └── configIndustria.ts        # API config industria
```

---

## 6. Flujos de Trabajo

### 6.1 Flujo Asistente Global

```
Usuario entra a /asistente (sin proyecto)
              │
              ▼
┌─────────────────────────────────────────────┐
│ Frontend envía:                             │
│   vista_actual: "asistente-global"          │
│   proyecto_contexto_id: null                │
└─────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────┐
│ Backend detecta: contexto GLOBAL            │
│   → Usa SYSTEM_PROMPT_GLOBAL                │
│   → Filtra herramientas: GLOBAL + AMBOS     │
└─────────────────────────────────────────────┘
              │
              ▼
Usuario: "¿Cuáles son los requisitos para ingresar al SEIA?"
              │
              ▼
Asistente: [usa buscar_normativa]
           "Según el Art. 10 de la Ley 19.300..."
              │
              ▼
Usuario: "Quiero crear un proyecto minero"
              │
              ▼
Asistente: [usa crear_proyecto con confirmación]
           "Perfecto. ¿Cómo se llama el proyecto?..."
```

### 6.2 Flujo Asistente de Proyecto

```
Usuario entra a /proyectos/123
              │
              ▼
┌─────────────────────────────────────────────┐
│ Frontend envía:                             │
│   vista_actual: "proyecto-detalle"          │
│   proyecto_contexto_id: 123                 │
└─────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────┐
│ Backend detecta: contexto PROYECTO          │
│   → Usa SYSTEM_PROMPT_PROYECTO              │
│   → Filtra herramientas: PROYECTO + AMBOS   │
│   → Carga contexto del proyecto             │
└─────────────────────────────────────────────┘
              │
              ▼
Usuario: "Quiero evaluar este proyecto minero"
              │
              ▼
Asistente: [usa obtener_config_industria(mineria)]
           "Entendido. Para proyectos mineros hay varios subtipos:
            • Extracción a rajo abierto
            • Extracción subterránea
            ¿Cuál corresponde?"
              │
              ▼
Usuario: "Es extracción a rajo abierto, 6,000 toneladas al mes"
              │
              ▼
Asistente: [usa guardar_ficha(tonelaje_mensual=6000)]
           [usa evaluar_umbral_seia(mineria, {tonelaje_mensual: 6000})]

           "He registrado 6,000 ton/mes.

            ✅ Este valor SUPERA el umbral de 5,000 ton/mes establecido
            en el Art. 3 letra i.1) del DS 40, por lo que tu proyecto
            SÍ debe ingresar al SEIA.

            ¿Cuál es la superficie del proyecto?"
```

---

## 7. Filtrado de Herramientas

### Implementación en `base.py`

```python
class RegistroHerramientas:
    def listar(
        self,
        contexto: Optional[ContextoHerramienta] = None,
        ...
    ) -> List[DefinicionHerramienta]:
        resultado = []

        for nombre, herramienta_class in self._herramientas.items():
            definicion = herramienta_class.get_definicion()

            # Filtrar por contexto
            if contexto:
                # AMBOS siempre se incluye
                if definicion.contexto_requerido == ContextoHerramienta.AMBOS:
                    pass
                # Si no coincide, excluir
                elif definicion.contexto_requerido != contexto:
                    continue

            resultado.append(definicion)

        return resultado

    def obtener_tools_anthropic(
        self,
        contexto: Optional[ContextoHerramienta] = None,
        ...
    ) -> List[Dict[str, Any]]:
        definiciones = self.listar(contexto=contexto, ...)
        return [d.to_anthropic_format() for d in definiciones]
```

### Uso en `service.py`

```python
async def chat(self, request: ChatRequest) -> ChatResponse:
    # Determinar contexto
    es_contexto_proyecto = (
        request.proyecto_contexto_id is not None or
        "proyecto" in (request.vista_actual or "").lower()
    )

    # Seleccionar prompt y herramientas
    if es_contexto_proyecto and contexto.proyecto_id:
        system_prompt = SYSTEM_PROMPT_PROYECTO.format(...)
        contexto_herramientas = ContextoHerramienta.PROYECTO
    else:
        system_prompt = SYSTEM_PROMPT_GLOBAL
        contexto_herramientas = ContextoHerramienta.GLOBAL

    # Obtener herramientas filtradas
    tools = registro_herramientas.obtener_tools_anthropic(
        contexto=contexto_herramientas
    )
```

---

## 8. Configuración por Industria

El sistema es multi-industria desde el diseño. Agregar nueva industria = insertar datos en BD.

### Tipos disponibles

| Código | Nombre | Letra Art.3 DS 40 |
|--------|--------|-------------------|
| `mineria` | Minería | i) |
| `energia` | Energía | c) |
| `inmobiliario` | Inmobiliario/Urbano | g) |
| `acuicultura` | Acuicultura/Pesca | n) |
| `infraestructura` | Infraestructura Vial | e) |
| `portuario` | Portuario | f) |
| `forestal` | Forestal | m) |
| `agroindustria` | Agroindustria | l) |

### Servicios de configuración

```python
class ConfigIndustriaService:
    async def get_config_completa(tipo: str, subtipo: str = None):
        """Retorna configuración completa para un tipo/subtipo."""

    async def evaluar_umbral(tipo: str, parametros: dict) -> UmbralResult:
        """Evalúa si un proyecto cumple umbral de ingreso SEIA."""

    async def get_pas_aplicables(tipo: str, caracteristicas: dict) -> list[PAS]:
        """Retorna PAS que aplican según características."""

    async def get_siguiente_pregunta(
        tipo: str,
        respuestas_previas: dict
    ) -> Pregunta:
        """Retorna siguiente pregunta del árbol."""
```

---

## 9. Endpoints API

### Asistente

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/v1/asistente/chat` | Enviar mensaje (incluye `vista_actual`, `proyecto_contexto_id`) |
| GET | `/api/v1/asistente/conversacion/{id}` | Historial de conversación |
| POST | `/api/v1/asistente/confirmar` | Confirmar acción pendiente |
| GET | `/api/v1/asistente/herramientas` | Lista de herramientas disponibles |

### Proyecto con Asistente

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/v1/proyectos/{id}/asistente` | Estado del asistente del proyecto |
| GET | `/api/v1/proyectos/{id}/ficha` | Ficha acumulativa |
| PATCH | `/api/v1/proyectos/{id}/ficha` | Actualizar campo de ficha |

### Configuración por Industria

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/v1/config/tipos` | Lista tipos de proyecto |
| GET | `/api/v1/config/tipos/{tipo}/subtipos` | Subtipos de un tipo |
| GET | `/api/v1/config/tipos/{tipo}/umbrales` | Umbrales SEIA |
| POST | `/api/v1/config/evaluar-umbral` | Evaluar umbral |
| GET | `/api/v1/config/arboles/{tipo}` | Árbol de preguntas |

---

## 10. Consideraciones Técnicas

### Performance
- Cache de configuración por industria en Redis
- Resúmenes automáticos de conversación para contexto largo
- Filtrado de herramientas en memoria (no BD)

### Seguridad
- Sanitización de entrada para prevenir prompt injection
- Confirmación obligatoria para acciones que modifican datos
- Permisos por herramienta

### Mantenibilidad
- Separación clara: config industria vs datos proyecto
- Herramientas modulares con registro automático
- Contexto declarativo en cada herramienta

---

## 11. Documentación Relacionada

| Documento | Contenido |
|-----------|-----------|
| `MODELO_DATOS_ASISTENTE.md` | Esquema BD, tablas, SQL |
| `ROADMAP_ASISTENTE.md` | Fases del proyecto |
| `BRIEFING_FASE1_DESARROLLADOR.md` | Detalles de implementación |
| `ASISTENTE_IA_ADENDUM.md` | Integración multi-LLM (Perplexity) |
| `METODOLOGIA_TEMPLATES_EIA.md` | Cómo crear templates por industria |

---

*Versión 2.0 - Enero 2026 - Separación Asistente Global/Proyecto*
