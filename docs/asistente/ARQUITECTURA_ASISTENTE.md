# Arquitectura: Sistema de Asistente por Proyecto

> **Versión:** 1.1 | **Fecha:** Enero 2026 | **Actualización:** Soporte multi-industria

---

## 1. Diagrama General

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND                                    │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  ProyectoDetalleView                                            │    │
│  │  ┌─────────────────────────────┬───────────────────────────┐    │    │
│  │  │     ChatAsistente.vue       │    FichaAcumulativa.vue   │    │    │
│  │  │     (70% ancho)             │    (30% ancho)            │    │    │
│  │  └─────────────────────────────┴───────────────────────────┘    │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                              BACKEND                                     │
│                                                                          │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐       │
│  │ AsistenteRouter  │  │ FichaService     │  │ ArbolService     │       │
│  │ /proyecto/{id}/  │  │ CRUD ficha       │  │ Preguntas config │       │
│  │ asistente        │  │ acumulativa      │  │ por tipo proy    │       │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘       │
│           │                     │                     │                  │
│           └─────────────────────┼─────────────────────┘                  │
│                                 ▼                                        │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    AsistenteService                               │   │
│  │  - Orquesta conversación                                          │   │
│  │  - Llama a Claude con contexto (ficha + historial + corpus)       │   │
│  │  - Ejecuta acciones (guardar en ficha, análisis GIS, etc)         │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│           │                     │                     │                  │
│           ▼                     ▼                     ▼                  │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐           │
│  │ GIS Service  │      │ RAG Service  │      │ Doc Service  │           │
│  │ (existente)  │      │ (existente)  │      │ OCR + parse  │           │
│  └──────────────┘      └──────────────┘      └──────────────┘           │
│           │                     │                     │                  │
│           └─────────────────────┼─────────────────────┘                  │
│                                 ▼                                        │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │              ConfigIndustriaService (NUEVO)                       │   │
│  │  - Carga configuración por tipo/subtipo                           │   │
│  │  - Evalúa umbrales SEIA                                           │   │
│  │  - Identifica PAS aplicables                                      │   │
│  │  - Retorna normativa y OAECA relevantes                           │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                            BASE DE DATOS                                 │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐             │
│  │ proyectos.*    │  │asistente_config│  │ legal.*        │             │
│  │ (ficha)        │  │ (industrias)   │  │ (corpus)       │             │
│  └────────────────┘  └────────────────┘  └────────────────┘             │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Estructura Backend

```
backend/app/
├── api/v1/endpoints/
│   ├── asistente_proyecto.py       # Endpoint asistente
│   └── config_industria.py         # NUEVO: CRUD configuración
│
├── services/
│   ├── asistente/
│   │   ├── service.py              # Orquestador principal
│   │   ├── ficha.py                # CRUD ficha acumulativa
│   │   ├── arboles.py              # Gestión árboles preguntas
│   │   ├── contexto.py             # Constructor contexto LLM
│   │   └── documentos.py           # OCR y extracción
│   │
│   └── config_industria/           # NUEVO
│       ├── service.py              # Servicio principal
│       ├── umbrales.py             # Evaluador de umbrales SEIA
│       ├── pas.py                  # Identificador de PAS
│       └── normativa.py            # Normativa por tipo
│
├── models/
│   ├── proyecto.py                 # Extendido
│   ├── ficha.py
│   ├── conversacion.py
│   ├── config_industria.py         # NUEVO: tipos, subtipos, pas, etc.
│   └── arbol_preguntas.py
│
└── schemas/
    ├── ficha.py
    ├── asistente_proyecto.py
    └── config_industria.py         # NUEVO
```

---

## 3. Estructura Frontend

```
frontend/src/
├── views/
│   └── ProyectoDetalleView.vue     # Agregar tab "Asistente"
│
├── components/asistente/
│   ├── ChatAsistente.vue           # Conversación
│   ├── FichaAcumulativa.vue        # Panel lateral
│   ├── MensajeChat.vue             # Burbuja de mensaje
│   ├── UploadDocumento.vue         # Subida de archivos
│   └── SelectorTipoProyecto.vue    # NUEVO: selector tipo/subtipo
│
├── stores/
│   ├── asistenteProyecto.ts        # Estado del asistente
│   └── configIndustria.ts          # NUEVO: cache de config
│
└── services/
    ├── asistenteProyecto.ts        # API calls
    └── configIndustria.ts          # NUEVO
```

---

## 4. Workflow del Asistente

```
ESTADO 1: INICIO
    └─► "¿Tienes la ubicación del proyecto?"
        ├─► Sube KML ──► ESTADO 2
        └─► "No tengo" ──► Continúa sin ubicación

ESTADO 2: UBICACIÓN PROCESADA
    └─► Ejecuta análisis GIS automático
    └─► Calcula regiones/comunas/alcance
    └─► Muestra alertas detectadas
    └─► "¿Qué tipo de proyecto es?"

ESTADO 3: TIPO DEFINIDO
    └─► Carga configuración de la industria:
        ├─► Subtipos disponibles
        ├─► Umbrales SEIA
        ├─► PAS típicos
        └─► Preguntas específicas
    └─► "¿Qué subtipo específico es?" (si aplica)

ESTADO 4: SUBTIPO DEFINIDO
    └─► Refina configuración con subtipo
    └─► Carga árbol de preguntas específico
    └─► Inicia recopilación

ESTADO 5: RECOPILACIÓN
    └─► Por cada respuesta:
        ├─► Guarda en ficha acumulativa
        ├─► Evalúa umbrales SEIA si aplica
        ├─► Coteja con corpus (RAG)
        ├─► Si hay alerta ──► Informa
        └─► Siguiente pregunta

ESTADO 6: DIAGNÓSTICO
    └─► Evalúa ingreso SEIA (umbrales)
    └─► Evalúa Art. 11 (DIA vs EIA)
    └─► Identifica PAS requeridos
    └─► Genera diagnóstico completo
```

---

## 5. Endpoints API

### Asistente
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/v1/proyectos/{id}/asistente` | Estado del asistente |
| POST | `/api/v1/proyectos/{id}/asistente/mensaje` | Enviar mensaje |
| GET | `/api/v1/proyectos/{id}/ficha` | Ficha acumulativa |
| PATCH | `/api/v1/proyectos/{id}/ficha` | Actualizar campo |
| POST | `/api/v1/proyectos/{id}/documentos` | Subir documento |

### Configuración por Industria (NUEVO)
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/v1/config/tipos` | Lista tipos de proyecto |
| GET | `/api/v1/config/tipos/{tipo}/subtipos` | Subtipos de un tipo |
| GET | `/api/v1/config/tipos/{tipo}/umbrales` | Umbrales SEIA |
| GET | `/api/v1/config/tipos/{tipo}/pas` | PAS típicos |
| GET | `/api/v1/config/tipos/{tipo}/normativa` | Normativa aplicable |
| GET | `/api/v1/config/tipos/{tipo}/oaeca` | OAECA principales |
| GET | `/api/v1/config/arboles/{tipo}` | Árbol de preguntas |
| POST | `/api/v1/config/evaluar-umbral` | Evaluar si cumple umbral |

---

## 6. Contexto del LLM

```python
CONTEXTO = {
    # Datos del proyecto
    "ficha_actual": { ... },
    "alertas_gis": [ ... ],

    # Configuración de la industria (NUEVO)
    "tipo_proyecto": "mineria",
    "subtipo": "extraccion_subterranea",
    "umbrales_aplicables": [ ... ],
    "pas_tipicos": [ ... ],
    "normativa_relevante": [ ... ],

    # Conversación
    "historial_resumido": "...",
    "ultimos_mensajes": [ ... ],

    # Preguntas pendientes
    "arbol_preguntas": { ... },

    # Corpus
    "corpus_relevante": [ ... ]
}
```

---

## 7. Servicios Clave

### ConfigIndustriaService (NUEVO)

```python
class ConfigIndustriaService:
    async def get_config_completa(tipo: str, subtipo: str = None) -> ConfigIndustria:
        """Retorna toda la configuración para un tipo/subtipo"""

    async def evaluar_umbral(tipo: str, parametros: dict) -> UmbralResult:
        """Evalúa si un proyecto cumple umbral de ingreso SEIA"""

    async def get_pas_aplicables(tipo: str, caracteristicas: dict) -> list[PAS]:
        """Retorna PAS que aplican según características"""

    async def get_normativa(tipo: str) -> list[Normativa]:
        """Retorna normativa aplicable al tipo"""
```

### Flujo de evaluación de umbral

```
Usuario dice: "Procesaremos 4,500 toneladas mensuales"
                    │
                    ▼
┌─────────────────────────────────────────┐
│ 1. Guardar en ficha:                    │
│    categoria='tecnico'                  │
│    clave='tonelaje_mensual'             │
│    valor_numerico=4500                  │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│ 2. Buscar umbral aplicable:             │
│    tipo='mineria'                       │
│    parametro='tonelaje_mensual'         │
│    operador='>='                        │
│    valor=5000                           │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│ 3. Evaluar: 4500 >= 5000?               │
│    Resultado: NO CUMPLE                 │
│    → No ingresa al SEIA por este umbral │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│ 4. Asistente informa:                   │
│    "Con 4,500 ton/mes no alcanzas el    │
│    umbral de 5,000 ton/mes del Art. 3   │
│    i.1) del DS 40. Sin embargo, podrías │
│    ingresar por otras causales..."      │
└─────────────────────────────────────────┘
```

---

## 8. Integraciones

| Sistema | Cuándo se usa | Cómo se integra |
|---------|---------------|-----------------|
| **GIS** | Al subir/cambiar ubicación | `analisis-espacial` existente |
| **RAG** | En cada respuesta del usuario | Búsqueda con filtro por industria |
| **OCR** | Al subir documento imagen/PDF | Claude Vision / Tesseract |
| **LLM** | En cada interacción | Claude Sonnet 4 |
| **ConfigIndustria** | Al definir tipo/subtipo | Servicio nuevo |

---

## 9. Consideraciones de Escalabilidad

### Multi-industria
- Toda la lógica específica de industria está en tablas configurables
- Agregar nueva industria = insertar datos, no código
- Templates EIA por industria en `/docs/TEMPLATE_EIA_*.md`

### Performance
- Cache de configuración por industria en Redis
- Vectorización asíncrona de documentos
- Resúmenes automáticos de conversación

### Mantenibilidad
- Separación clara: config vs datos de proyecto
- Servicios modulares por responsabilidad
- UI de administración para editar configuración

---

*Ver ROADMAP_ASISTENTE.md para fases del proyecto*
*Ver MODELO_DATOS_ASISTENTE.md para estructura de tablas*
