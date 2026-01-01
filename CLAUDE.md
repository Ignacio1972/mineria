# CLAUDE.md - Sistema de Prefactibilidad Ambiental Minera

## IMPORTANTE: Desarrollo Frontend

> **El frontend se sirve a través de Vite (servidor de desarrollo) en el puerto 4001.**
>
> Nginx hace proxy a Vite, por lo que los cambios en el código se reflejan **instantáneamente** en el navegador gracias al hot reload.
>
> ### Requisitos para desarrollar:
> 1. **Vite debe estar corriendo**: `cd /var/www/mineria/frontend && npm run dev`
> 2. Si Vite no está corriendo, verás error 502 en el navegador
>
> ### Verificar estado de Vite:
> ```bash
> lsof -i :4001  # Debe mostrar un proceso node
> ```
>
> ### Si necesitas reiniciar Vite:
> ```bash
> # Matar proceso existente
> kill $(lsof -t -i:4001)
> # Iniciar de nuevo
> cd /var/www/mineria/frontend && npm run dev &
> ```

---

## Descripcion del Proyecto

Sistema hibrido **LLM + GIS + RAG** para analisis automatizado de prefactibilidad ambiental de proyectos mineros en Chile. El sistema evalua automaticamente si un proyecto debe ingresar al SEIA como DIA (Declaracion de Impacto Ambiental) o EIA (Estudio de Impacto Ambiental), basandose en el Art. 11 de la Ley 19.300.

### Flujo Principal

```
Usuario dibuja poligono → Analisis GIS → Evaluacion Triggers Art. 11 → Motor Reglas SEIA → Busqueda RAG → Informe LLM → Exportacion PDF/DOCX
```

## Stack Tecnologico

| Componente | Tecnologia | Version |
|------------|------------|---------|
| Backend | Python / FastAPI | 3.11+ / 0.109 |
| Frontend | Vue 3 + Vite + TypeScript | 3.5 / 7.2 / 5.9 |
| UI | Tailwind CSS + DaisyUI | 4.1 / 5.5 |
| Mapas | OpenLayers + vue3-openlayers | 10.7 / 11.6 |
| State Management | Pinia | 3.0 |
| Base de datos | PostgreSQL + PostGIS + pgvector | 15 / 3.4 / 0.2 |
| Servidor de mapas | GeoServer | 2.24 |
| Cache | Redis | 7-alpine |
| LLM | Anthropic Claude | claude-sonnet-4-20250514 |
| Embeddings | sentence-transformers | paraphrase-multilingual-MiniLM-L12-v2 |
| Testing Frontend | Vitest + Playwright | 2.1 / 1.57 |
| Testing Backend | pytest + pytest-asyncio | 7.4 / 0.23 |
| Contenedores | Docker + Docker Compose | - |

## Estructura del Proyecto

```
mineria/
├── backend/                     # API FastAPI
│   ├── app/
│   │   ├── api/v1/
│   │   │   ├── endpoints/       # 14 modulos de endpoints
│   │   │   │   ├── analisis_espacial.py   # GIS: analisis, capas, geojson
│   │   │   │   ├── buscar_normativa.py    # RAG: busqueda semantica
│   │   │   │   ├── categorias.py          # Corpus: categorias
│   │   │   │   ├── clientes.py            # CRUD clientes
│   │   │   │   ├── colecciones.py         # Corpus: colecciones
│   │   │   │   ├── corpus.py              # Corpus: documentos
│   │   │   │   ├── dashboard.py           # Estadisticas y recientes
│   │   │   │   ├── documentos.py          # Upload archivos proyecto
│   │   │   │   ├── ingestor.py            # Ingesta documentos legales
│   │   │   │   ├── llm.py                 # Gestion modelos LLM
│   │   │   │   ├── prefactibilidad.py     # Analisis principal
│   │   │   │   ├── proyectos.py           # CRUD proyectos
│   │   │   │   └── temas.py               # Corpus: temas
│   │   │   └── router.py
│   │   ├── core/
│   │   │   └── config.py        # Settings (Pydantic)
│   │   ├── db/
│   │   │   ├── models/          # 7 modelos SQLAlchemy
│   │   │   │   ├── auditoria.py # AuditoriaAnalisis
│   │   │   │   ├── cliente.py   # Cliente
│   │   │   │   ├── corpus.py    # Categoria, Tema, Coleccion
│   │   │   │   ├── documento.py # DocumentoProyecto
│   │   │   │   ├── gis.py       # Capas GIS
│   │   │   │   ├── legal.py     # Documento, Fragmento (RAG)
│   │   │   │   └── proyecto.py  # Proyecto, Analisis
│   │   │   └── session.py
│   │   ├── schemas/             # Pydantic schemas
│   │   │   ├── auditoria.py
│   │   │   ├── cliente.py
│   │   │   ├── documento.py
│   │   │   └── proyecto.py
│   │   ├── services/
│   │   │   ├── exportacion/
│   │   │   │   └── exportador.py    # PDF, DOCX, TXT, HTML
│   │   │   ├── gis/
│   │   │   │   └── analisis.py      # Analisis espacial PostGIS
│   │   │   ├── llm/
│   │   │   │   ├── clasificador.py  # Clasificacion documentos
│   │   │   │   ├── cliente.py       # Cliente Anthropic
│   │   │   │   ├── generador.py     # Generador de informes
│   │   │   │   ├── gestor.py        # Gestor de modelos
│   │   │   │   └── prompts.py       # Templates de prompts
│   │   │   ├── rag/
│   │   │   │   ├── busqueda.py      # BuscadorLegal (pgvector)
│   │   │   │   ├── embeddings.py    # EmbeddingService
│   │   │   │   └── ingestor.py      # IngestorLegal
│   │   │   ├── reglas/
│   │   │   │   ├── alertas.py       # SistemaAlertas
│   │   │   │   ├── seia.py          # MotorReglasSSEIA
│   │   │   │   └── triggers.py      # EvaluadorTriggers Art. 11
│   │   │   ├── storage/
│   │   │   │   └── archivo_service.py
│   │   │   └── startup.py
│   │   └── main.py
│   ├── tests/                   # 8 archivos de tests
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                    # Vue 3 SPA
│   ├── src/
│   │   ├── components/          # 32 componentes Vue
│   │   │   ├── analysis/        # AlertCard, AlertsPanel, AnalysisPanel, etc.
│   │   │   ├── common/          # ConfidenceBadge, LoadingSpinner, SeverityBadge
│   │   │   ├── corpus/          # CategoriaTree, CorpusManager, FragmentosViewer
│   │   │   ├── dashboard/       # DashboardStats, QuickActions, RecentAnalysis
│   │   │   ├── documentos/      # DocumentoCard, DocumentoUpload, DocumentosList
│   │   │   ├── layout/          # AppHeader, AppSidebar, AppFooter
│   │   │   ├── map/             # MapContainer, DrawTools, LayerPanel, MapControls
│   │   │   ├── proyectos/       # ProyectoFormulario, ProyectoAlertas, ProyectoProgreso
│   │   │   └── report/          # ReportViewer, ExportButtons
│   │   ├── composables/         # useAnalysis, useApi, useExport, useMap
│   │   ├── router/              # Vue Router (13 rutas)
│   │   ├── services/            # 10 servicios API
│   │   │   ├── api.ts           # Cliente Axios base
│   │   │   ├── clientes.ts
│   │   │   ├── corpus.ts        # 322 lineas, muy completo
│   │   │   ├── dashboard.ts
│   │   │   ├── documentos.ts
│   │   │   ├── gis.ts
│   │   │   ├── legal.ts
│   │   │   ├── prefactibilidad.ts
│   │   │   └── proyectos.ts
│   │   ├── stores/              # 6 stores Pinia
│   │   │   ├── analysis.ts
│   │   │   ├── clientes.ts
│   │   │   ├── corpus.ts        # 490+ lineas
│   │   │   ├── map.ts
│   │   │   ├── proyectos.ts
│   │   │   └── ui.ts
│   │   ├── types/               # TypeScript interfaces
│   │   │   ├── analysis.ts      # Triggers, Alertas, Clasificacion
│   │   │   ├── api.ts
│   │   │   ├── cliente.ts
│   │   │   ├── corpus.ts
│   │   │   ├── documento.ts
│   │   │   ├── gis.ts           # Capas, Features
│   │   │   └── project.ts       # Proyecto, Estados
│   │   ├── utils/               # format.ts, validation.ts
│   │   ├── views/               # 13 vistas
│   │   ├── App.vue
│   │   └── main.ts
│   ├── tests/                   # 21 archivos tests unitarios
│   ├── e2e/                     # 3 archivos tests E2E
│   ├── package.json
│   ├── vite.config.ts
│   └── vitest.config.ts
├── docker/
│   ├── docker-compose.yml
│   └── postgis/init/            # 5 scripts SQL
│       ├── 01_extensions.sql    # PostGIS, pgvector
│       ├── 02_schema.sql        # Esquema GIS + proyectos
│       ├── 03_clientes_documentos.sql
│       ├── 04_add_geography_indexes.sql
│       └── 05_corpus_rag_schema.sql
├── data/
│   ├── gis/
│   │   ├── catalogo.json        # Inventario de capas
│   │   ├── fuentes/             # Datos originales
│   │   └── procesados/          # Datos EPSG:4326
│   ├── legal/
│   │   └── processed/           # JSON: ley_19300, ds_40, guia_sea
│   └── scripts/
│       ├── cargar_datos_ejemplo.py
│       ├── cargar_corpus_legal.py
│       └── configurar_geoserver.py
└── docs/                        # 12 documentos tecnicos
```

## Comandos Utiles

### Docker y Servicios

```bash
# Levantar todos los servicios
cd /var/www/mineria/docker
docker compose up -d

# Ver estado de servicios
docker compose ps

# Ver logs del backend
docker compose logs -f backend

# Reiniciar backend (despues de cambios)
docker compose restart backend

# Reconstruir backend (cambios en requirements.txt)
docker compose up -d --build backend
```

### Carga de Datos

```bash
# Cargar datos GIS de ejemplo
cd /var/www/mineria/data/scripts
python cargar_datos_ejemplo.py

# Cargar corpus legal (Ley 19.300, DS 40, Guia SEA)
python cargar_corpus_legal.py

# Configurar GeoServer (publicar capas WMS/WFS)
python configurar_geoserver.py
```

### Frontend

```bash
cd /var/www/mineria/frontend

# Instalar dependencias
npm install

# Desarrollo (hot reload)
npm run dev

# Build produccion
npm run build

# Tests unitarios
npm run test

# Tests con coverage
npm run test:coverage

# Tests E2E
npm run test:e2e
```

### Backend Tests

```bash
cd /var/www/mineria/backend
pytest tests/ -v

# Tests especificos
pytest tests/test_reglas_seia.py -v
pytest tests/test_embeddings.py -v
pytest tests/test_analisis_espacial.py -v
```

## Puertos y URLs

| Servicio | Puerto Interno | Puerto Externo | URL |
|----------|---------------|----------------|-----|
| Backend API | 8000 | 9001 | http://localhost:9001/docs |
| GeoServer | 8080 | 9085 | http://localhost:9085/geoserver |
| PostgreSQL | 5432 | 5433 | localhost:5433 |
| Redis | 6379 | 6380 | localhost:6380 |
| Frontend (dev) | 4001 | 4001 | http://localhost:4001 |

### Credenciales Desarrollo

- **PostgreSQL**: `mineria` / `mineria_dev_2024`
- **GeoServer**: `admin` / `geoserver_dev_2024`

## API Endpoints Principales

### Prefactibilidad (Analisis SEIA)

| Endpoint | Metodo | Descripcion |
|----------|--------|-------------|
| `/api/v1/prefactibilidad/analisis` | POST | Analisis completo con LLM |
| `/api/v1/prefactibilidad/analisis-rapido` | POST | Analisis sin LLM (2-5 seg) |
| `/api/v1/prefactibilidad/analisis-integrado` | POST | Analisis con persistencia en BD |
| `/api/v1/prefactibilidad/exportar/{formato}` | POST | Exportar PDF/DOCX/TXT/HTML |
| `/api/v1/prefactibilidad/matriz-decision` | GET | Configuracion matriz DIA/EIA |
| `/api/v1/prefactibilidad/proyecto/{id}/historial-analisis` | GET | Historial de analisis |
| `/api/v1/prefactibilidad/analisis/{id}/auditoria` | GET | Trazabilidad del analisis |

### GIS (Analisis Espacial)

| Endpoint | Metodo | Descripcion |
|----------|--------|-------------|
| `/api/v1/gis/analisis-espacial` | POST | Analisis espacial de proyecto |
| `/api/v1/gis/capas` | GET | Listar capas disponibles |
| `/api/v1/gis/capas/{capa}/geojson` | GET | Obtener capa GeoJSON |

### Legal (RAG)

| Endpoint | Metodo | Descripcion |
|----------|--------|-------------|
| `/api/v1/legal/buscar` | POST | Busqueda semantica normativa |
| `/api/v1/legal/estadisticas` | GET | Stats del corpus |
| `/api/v1/legal/temas` | GET | Temas disponibles |

### Proyectos

| Endpoint | Metodo | Descripcion |
|----------|--------|-------------|
| `/api/v1/proyectos` | GET | Listar proyectos (paginado) |
| `/api/v1/proyectos` | POST | Crear proyecto |
| `/api/v1/proyectos/{id}` | GET | Obtener proyecto con geometria |
| `/api/v1/proyectos/{id}` | PUT | Actualizar proyecto |
| `/api/v1/proyectos/{id}/geometria` | PATCH | Actualizar geometria |
| `/api/v1/proyectos/{id}/estado` | PATCH | Cambiar estado |

### Clientes

| Endpoint | Metodo | Descripcion |
|----------|--------|-------------|
| `/api/v1/clientes` | GET/POST | Listar/Crear clientes |
| `/api/v1/clientes/{id}` | GET/PUT/DELETE | CRUD cliente |

### Corpus RAG

| Endpoint | Metodo | Descripcion |
|----------|--------|-------------|
| `/api/v1/categorias` | GET/POST | Categorias jerarquicas |
| `/api/v1/corpus` | GET/POST | Documentos legales |
| `/api/v1/corpus/{id}/fragmentos` | GET | Fragmentos del documento |
| `/api/v1/corpus/{id}/reprocesar` | POST | Regenerar embeddings |
| `/api/v1/temas` | GET/POST | Temas para clasificacion |
| `/api/v1/colecciones` | GET/POST | Colecciones de documentos |

### Dashboard

| Endpoint | Metodo | Descripcion |
|----------|--------|-------------|
| `/api/v1/dashboard/stats` | GET | Estadisticas generales |
| `/api/v1/dashboard/analisis-recientes` | GET | Ultimos analisis |

## Capas GIS Disponibles

| Capa | Descripcion | Buffer | Art. 11 | Registros |
|------|-------------|--------|---------|-----------|
| areas_protegidas | SNASPE, Santuarios, Reservas | 50 km | letra d) | 3,400 |
| glaciares | Glaciares y ambiente periglaciar | 20 km | letra b) | 450 |
| cuerpos_agua | Rios, lagos, humedales, Ramsar | 10 km | letra b) | 1,722 |
| comunidades_indigenas | Comunidades y ADIs | 30 km | letras c,d) | - |
| centros_poblados | Ciudades, pueblos, aldeas | 20 km | letra a) | - |
| sitios_patrimoniales | Arqueologico, monumentos | 10 km | letra e) | - |
| regiones | Division administrativa | - | ubicacion | 16 |
| comunas | Division administrativa | - | ubicacion | 346 |
| bienes_nacionales | Bienes Nacionales Protegidos | 10 km | letra d) | - |

## Motor de Reglas SEIA

### Clasificacion DIA vs EIA

El sistema usa una **matriz de decision ponderada**:

```
1. Trigger CRITICO detectado         → EIA obligatorio (95% confianza)
2. >= 2 triggers ALTOS               → EIA muy probable (85%)
3. Puntaje matriz >= 0.75            → EIA recomendado (80%)
4. Puntaje 0.50-0.75                 → EIA sugerido (65%)
5. Puntaje 0.30-0.50 + triggers      → DIA con medidas (60%)
6. Sin triggers significativos       → DIA estandar (85%)
```

### Triggers Art. 11 Ley 19.300

| Letra | Descripcion | Severidad si detectado |
|-------|-------------|------------------------|
| a) | Riesgo para salud de la poblacion | ALTA-CRITICA |
| b) | Efectos sobre recursos naturales renovables | MEDIA-ALTA |
| c) | Reasentamiento de comunidades humanas | CRITICA |
| d) | Areas protegidas, glaciares | CRITICA |
| e) | Alteracion patrimonio cultural | ALTA |
| f) | Alteracion paisaje/turismo | MEDIA |

### Factores de la Matriz

| Factor | Umbral | Peso |
|--------|--------|------|
| Superficie proyecto | >500 ha | 30% |
| Uso de agua | >100 L/s | 25% |
| Trabajadores construccion | >500 | 15% |
| Inversion | >100 MUSD | 15% |
| Vida util | >20 anos | 15% |

## Esquemas de Base de Datos

### Esquema `gis`

Capas GIS con geometrias PostGIS (SRID 4326):
- `areas_protegidas`, `glaciares`, `cuerpos_agua`
- `comunidades_indigenas`, `centros_poblados`, `sitios_patrimoniales`
- `regiones`, `comunas`, `bienes_nacionales_protegidos`

### Esquema `legal`

Corpus normativo con embeddings pgvector:
- `categorias` - Taxonomia jerarquica (5 niveles)
- `documentos` - Leyes, reglamentos, guias
- `fragmentos` - Articulos con embedding vector(384)
- `temas` - 20 temas predefinidos
- `colecciones` - Agrupaciones transversales
- `fragmentos_temas` - Relacion many-to-many

### Esquema `proyectos`

Proyectos mineros y analisis:
- `clientes` - Titulares de proyectos (RUT unico)
- `proyectos` - Datos del proyecto + geometria
- `documentos` - Archivos adjuntos (PDF, mapas)
- `analisis` - Resultados de prefactibilidad
- `auditoria_analisis` - Trazabilidad completa
- `historial_estados` - Log de cambios de estado

## Frontend - Stores Pinia

| Store | Estado Principal | Metodos Clave |
|-------|-----------------|---------------|
| `ui` | tema, sidebar, toasts, modales | toggleTema, mostrarToast |
| `proyectos` | proyectos[], proyectoActual, filtros | cargarProyectos, crearProyecto, cambiarEstado |
| `analysis` | resultado, historial, auditoria | analizarProyecto, exportar |
| `map` | centro, zoom, capas[], modoEdicion | toggleCapa, activarDibujo |
| `clientes` | clientes[], clienteActual | cargarClientes, crearCliente |
| `corpus` | categorias, temas, documentos | cargarDocumentos, seleccionarDocumento |

## Frontend - Vistas y Rutas

| Ruta | Vista | Descripcion |
|------|-------|-------------|
| `/` | DashboardView | Dashboard con KPIs |
| `/clientes` | ClientesView | Lista de clientes |
| `/clientes/nuevo` | ClienteFormView | Crear cliente |
| `/clientes/:id` | ClienteDetalleView | Detalle cliente |
| `/proyectos` | ProyectosView | Lista de proyectos |
| `/proyectos/nuevo` | ProyectoFormView | Crear proyecto |
| `/proyectos/:id` | ProyectoDetalleView | Detalle proyecto |
| `/proyectos/:id/mapa` | ProyectoMapaView | Dibujar geometria |
| `/proyectos/:id/analisis` | ProyectoAnalisisView | Resultados analisis |
| `/analisis` | AnalisisHistorialView | Historial global |
| `/corpus` | CorpusView | Gestion corpus RAG |

## Configuracion de Entorno

Variables principales (`.env`):

```env
# Database
POSTGRES_PASSWORD=mineria_dev_2024
DATABASE_URL=postgresql://mineria:mineria_dev_2024@localhost:5433/mineria

# Redis
REDIS_URL=redis://localhost:6380/0

# LLM
ANTHROPIC_API_KEY=sk-ant-...

# GeoServer
GEOSERVER_PASSWORD=geoserver_dev_2024

# Environment
ENVIRONMENT=development
DEBUG=true
```

### Settings Backend (core/config.py)

```python
# Buffers de analisis espacial (metros)
BUFFER_AREAS_PROTEGIDAS_M = 50000   # 50 km
BUFFER_COMUNIDADES_M = 30000        # 30 km
BUFFER_CUERPOS_AGUA_M = 10000       # 10 km
BUFFER_GLACIARES_M = 20000          # 20 km
BUFFER_CENTROS_POBLADOS_M = 20000   # 20 km

# RAG
EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
EMBEDDING_DIMENSION = 384
RAG_TOP_K = 10

# LLM
LLM_MODEL = "claude-sonnet-4-20250514"
LLM_MAX_TOKENS = 4096
```

## Tests

### Backend (pytest)

```
tests/
├── test_analisis_espacial.py   # Analisis GIS
├── test_busqueda.py            # Busqueda RAG
├── test_embeddings.py          # Generacion embeddings
├── test_generador_informes.py  # Generacion LLM
├── test_ingestor.py            # Ingesta documentos
├── test_reglas_seia.py         # Motor de reglas
├── test_triggers_eia.py        # Evaluacion triggers
└── conftest.py
```

### Frontend (vitest + playwright)

```
tests/
├── components/                  # 6 tests de componentes
├── composables/                 # 5 tests de hooks
├── services/                    # 4 tests de servicios
├── stores/                      # 4 tests de stores
└── utils/                       # 2 tests de utilidades

e2e/
├── home.spec.ts                 # Pagina inicio
├── navigation.spec.ts           # Navegacion
└── project.spec.ts              # Flujo proyecto
```

**Cobertura minima:** 55%

## Estado del Proyecto

| Fase | Descripcion | Estado | Completitud |
|------|-------------|--------|-------------|
| 1 | Infraestructura (Docker, BD) | COMPLETADA | 100% |
| 2 | RAG Legal (Corpus, Embeddings) | COMPLETADA | 100% |
| 3 | Motor de Analisis (GIS, Reglas) | COMPLETADA | 100% |
| 4 | Frontend (Vue 3, Componentes) | EN PROGRESO | 95% |
| 5 | Validacion (Tests, Expertos) | EN PROGRESO | 70% |
| 6 | Produccion (CI/CD, Deploy) | PENDIENTE | 0% |

### Pendientes Fase 5

- Validacion con consultores ambientales

## Dependencias Principales

### Backend (requirements.txt)

```
fastapi==0.109.0
uvicorn[standard]==0.27.0
sqlalchemy==2.0.25
asyncpg==0.29.0
geoalchemy2==0.14.3
sentence-transformers==2.3.1
anthropic==0.18.1
shapely==2.0.2
reportlab==4.0.8
python-docx==1.1.0
pymupdf==1.23.8
redis==5.0.1
pgvector==0.2.4
```

### Frontend (package.json)

```
vue: ^3.5.24
pinia: ^3.0.4
vue-router: ^4.6.4
axios: ^1.13.2
ol: ^10.7.0
vue3-openlayers: ^11.6.2
tailwindcss: ^4.1.18
daisyui: ^5.5.14
```

## Convenciones de Codigo

### Backend
- Python con type hints
- async/await para operaciones de BD
- Pydantic para validacion
- SQLAlchemy 2.0 con modo async

### Frontend
- Composition API con `<script setup lang="ts">`
- TypeScript estricto
- Utility-first CSS con Tailwind
- Stores Pinia para estado global

### Seguridad
- SQL injection prevenido con whitelist de tablas GIS
- CORS configurado segun ambiente
- Validacion de entrada con Pydantic
- API key de Anthropic en variables de entorno
- Checksum SHA-256 para archivos subidos

## Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                      FRONTEND (Vue 3)                        │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │
│  │Dashboard│ │Proyectos│ │  Mapa   │ │ Corpus  │           │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘           │
│       └───────────┴───────────┴───────────┘                 │
│                        │ API REST                           │
└────────────────────────┼────────────────────────────────────┘
                         ▼
┌────────────────────────────────────────────────────────────┐
│                    BACKEND (FastAPI)                        │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │   Servicios  │ │    Motor     │ │  Exportacion │        │
│  │  GIS + RAG   │ │ Reglas SEIA  │ │  PDF/DOCX    │        │
│  └──────┬───────┘ └──────┬───────┘ └──────────────┘        │
│         │                │                                  │
│  ┌──────▼───────┐ ┌──────▼───────┐                         │
│  │   PostGIS    │ │   Claude     │                         │
│  │  + pgvector  │ │   Sonnet 4   │                         │
│  └──────────────┘ └──────────────┘                         │
└────────────────────────────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
    ┌─────────┐    ┌─────────┐    ┌─────────┐
    │PostgreSQL│    │  Redis  │    │GeoServer│
    │+ PostGIS │    │  Cache  │    │ WMS/WFS │
    └─────────┘    └─────────┘    └─────────┘
```

## Notas de Desarrollo

### Performance
- Lazy loading de modelo de embeddings
- Indices espaciales GIST en PostGIS
- Indice IVFFlat para busqueda vectorial (100 lists)
- Cache de capas GIS en Redis
- Timeout LLM: 120 segundos

### Monitoreo
- Health check: `GET /health`
- API docs: `GET /docs`
- Metricas de analisis en `datos_extra` JSONB

### Fuentes de Datos GIS
- IDE Chile (https://www.ide.cl/)
- CONAF (https://www.conaf.cl/) - SNASPE
- DGA (https://dga.mop.gob.cl/) - Glaciares
- MMA (https://mma.gob.cl/) - Biodiversidad
- CMN (https://www.monumentos.gob.cl/) - Patrimonio
