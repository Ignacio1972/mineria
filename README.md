# Sistema de Prefactibilidad Ambiental Minera

Sistema hibrido **LLM + GIS + RAG** para analisis automatizado de prefactibilidad ambiental de proyectos mineros en Chile. Determina automaticamente si un proyecto debe ingresar al SEIA como **DIA** o **EIA** segun el Art. 11 de la Ley 19.300.

## Caracteristicas Principales

- **Analisis Espacial GIS**: Intersecciones con areas protegidas, glaciares, cuerpos de agua, comunidades indigenas, sitios patrimoniales
- **Motor de Reglas SEIA**: Evaluacion automatica de los 6 triggers del Art. 11 (letras a-f)
- **Busqueda Semantica RAG**: Corpus legal indexado con embeddings (Ley 19.300, DS 40, Guias SEA)
- **Generacion de Informes LLM**: Informes estructurados con Claude Sonnet 4
- **Exportacion Multiformato**: PDF, DOCX, TXT, HTML
- **Interfaz Interactiva**: Mapa con herramientas de dibujo, dashboard, gestion de proyectos

## Requisitos

- Docker y Docker Compose
- Node.js 18+ (para desarrollo frontend)
- API Key de Anthropic (para generacion de informes)

## Inicio Rapido

### 1. Configurar variables de entorno

```bash
cd /var/www/mineria

# Crear archivo .env
cat > docker/.env << EOF
POSTGRES_PASSWORD=mineria_dev_2024
GEOSERVER_PASSWORD=geoserver_dev_2024
ANTHROPIC_API_KEY=tu_api_key_aqui
ENVIRONMENT=development
EOF
```

### 2. Levantar servicios con Docker

```bash
cd docker
docker compose up -d

# Verificar que todos los servicios esten corriendo
docker compose ps
```

### 3. Cargar datos iniciales

```bash
cd /var/www/mineria/data/scripts

# Cargar datos GIS de ejemplo (areas protegidas, glaciares, etc.)
python cargar_datos_ejemplo.py

# Cargar corpus legal (Ley 19.300, DS 40, Guia SEA Mineria)
python cargar_corpus_legal.py

# Configurar GeoServer (publicar capas WMS/WFS)
python configurar_geoserver.py
```

### 4. Iniciar frontend (desarrollo)

```bash
cd /var/www/mineria/frontend
npm install
npm run dev
```

### 5. Acceder a los servicios

| Servicio | URL | Credenciales |
|----------|-----|--------------|
| Frontend | http://localhost:4001 | - |
| API Docs | http://localhost:9001/docs | - |
| GeoServer | http://localhost:9085/geoserver | admin / geoserver_dev_2024 |

## Stack Tecnologico

| Componente | Tecnologia |
|------------|------------|
| Backend | Python 3.11 + FastAPI |
| Frontend | Vue 3 + Vite + TypeScript |
| UI | Tailwind CSS 4 + DaisyUI 5 |
| Mapas | OpenLayers 10 |
| Base de datos | PostgreSQL 15 + PostGIS 3.4 + pgvector |
| Servidor mapas | GeoServer 2.24 |
| Cache | Redis 7 |
| LLM | Claude Sonnet 4 (claude-sonnet-4-20250514) |
| Embeddings | sentence-transformers (paraphrase-multilingual-MiniLM-L12-v2) |

## Estructura del Proyecto

```
mineria/
├── backend/             # API FastAPI
│   ├── app/
│   │   ├── api/v1/     # Endpoints REST (14 modulos)
│   │   ├── services/   # Logica de negocio (GIS, RAG, LLM, Reglas)
│   │   └── db/         # Modelos SQLAlchemy
│   └── tests/
├── frontend/            # Vue 3 SPA
│   ├── src/
│   │   ├── components/ # 32 componentes Vue
│   │   ├── stores/     # 6 stores Pinia
│   │   ├── services/   # 10 clientes API
│   │   └── views/      # 13 vistas
│   └── tests/
├── docker/              # Docker Compose + SQL init
├── data/
│   ├── gis/            # Capas GIS (SNASPE, glaciares, etc.)
│   └── legal/          # Corpus normativo (JSON)
└── docs/               # Documentacion tecnica
```

## API Endpoints Principales

### Prefactibilidad (Analisis SEIA)

```bash
# Analisis completo con generacion de informe LLM
POST /api/v1/prefactibilidad/analisis

# Analisis rapido sin LLM (2-5 segundos)
POST /api/v1/prefactibilidad/analisis-rapido

# Exportar informe
POST /api/v1/prefactibilidad/exportar/{formato}  # pdf, docx, txt, html
```

### GIS (Analisis Espacial)

```bash
# Analisis espacial de un proyecto
POST /api/v1/gis/analisis-espacial

# Listar capas disponibles
GET /api/v1/gis/capas

# Obtener capa en GeoJSON
GET /api/v1/gis/capas/{capa}/geojson
```

### Legal (RAG)

```bash
# Busqueda semantica en corpus legal
POST /api/v1/legal/buscar

# Estadisticas del corpus
GET /api/v1/legal/estadisticas
```

## Ejemplo: Analisis Espacial

```bash
curl -X POST http://localhost:9001/api/v1/gis/analisis-espacial \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Proyecto Minero Test",
    "geometria": {
      "type": "Polygon",
      "coordinates": [[
        [-68.5, -23.5],
        [-68.3, -23.5],
        [-68.3, -23.3],
        [-68.5, -23.3],
        [-68.5, -23.5]
      ]]
    },
    "tipo_mineria": "Cielo abierto",
    "mineral_principal": "Litio"
  }'
```

## Capas GIS Disponibles

| Capa | Buffer | Art. 11 |
|------|--------|---------|
| areas_protegidas | 50 km | letra d) |
| glaciares | 20 km | letra b) |
| cuerpos_agua | 10 km | letra b) |
| comunidades_indigenas | 30 km | letras c,d) |
| centros_poblados | 20 km | letra a) |
| sitios_patrimoniales | 10 km | letra e) |

## Motor de Reglas SEIA

El sistema evalua automaticamente los **6 triggers del Art. 11** de la Ley 19.300:

| Letra | Efecto | Consecuencia |
|-------|--------|--------------|
| a) | Riesgo para salud de la poblacion | EIA obligatorio |
| b) | Efectos sobre recursos naturales | EIA probable |
| c) | Reasentamiento de comunidades | EIA obligatorio |
| d) | Areas protegidas / glaciares | EIA obligatorio |
| e) | Alteracion patrimonio cultural | EIA probable |
| f) | Alteracion paisaje / turismo | Evaluar caso |

**Clasificacion automatica:**
- Trigger CRITICO → EIA obligatorio (95% confianza)
- 2+ triggers ALTOS → EIA muy probable (85%)
- Sin triggers → DIA estandar (85%)

## Tests

```bash
# Backend
cd /var/www/mineria/backend
pytest tests/ -v

# Frontend - unitarios
cd /var/www/mineria/frontend
npm run test

# Frontend - E2E
npm run test:e2e
```

## Documentacion

- `CLAUDE.md` - Documentacion tecnica completa para desarrollo
- `docs/PLAN_PROYECTO.md` - Roadmap de 6 fases
- `docs/RAG_*.md` - Arquitectura del sistema RAG
- `docs/DOCUMENTO_TECNICO_*.md` - Especificaciones backend/frontend

## Estado del Proyecto

| Fase | Estado | Completitud |
|------|--------|-------------|
| 1. Infraestructura | Completada | 100% |
| 2. RAG Legal | Completada | 100% |
| 3. Motor Analisis | Completada | 100% |
| 4. Frontend | En progreso | 95% |
| 5. Validacion | En progreso | 70% |
| 6. Produccion | Pendiente | 0% |

## Licencia

Proyecto interno - Todos los derechos reservados.
