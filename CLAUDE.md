# CLAUDE.md - Sistema de Prefactibilidad Ambiental Minera

Sistema **LLM + GIS + RAG** para análisis de prefactibilidad ambiental de proyectos mineros en Chile (DIA vs EIA según Art. 11 Ley 19.300).

---

## IMPORTANTE: Ingesta de Documentos al Corpus RAG

> **Para ingestar documentos legales usar los scripts en `/var/www/mineria/data/scripts/`**
>
> **NO usar el endpoint HTTP `/api/v1/ingestor/pdf`** - es lento y puede fallar por timeout.
>
> ### Script principal:
> ```bash
> docker exec mineria_backend python /app/data/scripts/ingestar_instructivos_sea_2025.py
> ```
>
> ### Para agregar nuevos documentos:
> 1. Editar `data/scripts/ingestar_instructivos_sea_2025.py`
> 2. Agregar entrada al diccionario `INSTRUCTIVOS_2025`
> 3. Ejecutar el script
>
> ### Scripts disponibles:
> - `ingestar_instructivos_sea_2025.py` - Instructivos SEA
> - `ingestar_guias_sea.py` - Guías metodológicas
> - `cargar_corpus_legal.py` - Corpus base (Ley 19.300, DS 40)
>
> ### Verificar documentos:
> ```bash
> docker exec mineria_postgis psql -U mineria -d mineria -c "SELECT id, titulo, numero FROM legal.documentos ORDER BY id DESC LIMIT 10;"
> ```

---

## IMPORTANTE: Desarrollo Frontend

> **Vite sirve el frontend en puerto 4001** - Nginx hace proxy, hot reload automático.
>
> ### Verificar/reiniciar Vite:
> ```bash
> lsof -i :4001                          # Verificar si corre
> kill $(lsof -t -i:4001)                # Matar si es necesario
> cd /var/www/mineria/frontend && npm run dev &  # Iniciar
> ```
> Si Vite no corre, verás error 502.

---

## Comandos Esenciales

### Docker
```bash
cd /var/www/mineria/docker
docker compose up -d              # Levantar servicios
docker compose logs -f backend    # Ver logs
docker compose restart backend    # Reiniciar backend
```

### Frontend
```bash
cd /var/www/mineria/frontend
npm run dev          # Desarrollo
npm run build        # Producción
npm run test         # Tests
```

### Backend Tests
```bash
docker exec mineria_backend pytest tests/ -v
```

---

## Puertos y URLs

| Servicio | Puerto | URL |
|----------|--------|-----|
| Frontend | 4001 | http://localhost:4001 |
| Backend API | 9001 | http://localhost:9001/docs |
| GeoServer | 9085 | http://localhost:9085/geoserver |
| PostgreSQL | 5433 | - |
| Redis | 6380 | - |

**Credenciales dev:** PostgreSQL `mineria/mineria_dev_2024`, GeoServer `admin/geoserver_dev_2024`

---

## Stack Principal

- **Backend:** FastAPI + SQLAlchemy async + Pydantic
- **Frontend:** Vue 3 + TypeScript + Pinia + Tailwind/DaisyUI
- **Mapas:** OpenLayers + vue3-openlayers
- **BD:** PostgreSQL + PostGIS + pgvector
- **LLM:** Claude Sonnet 4 + sentence-transformers (embeddings)

---

## Convenciones de Código

### Backend
- Python con type hints, async/await para BD
- Pydantic para validación, SQLAlchemy 2.0 async

### Frontend
- Composition API con `<script setup lang="ts">`
- TypeScript estricto, Tailwind utility-first
- Stores Pinia para estado global

---

## Endpoints Clave

- `POST /api/v1/prefactibilidad/analisis` - Análisis completo con LLM
- `POST /api/v1/prefactibilidad/analisis-rapido` - Sin LLM (2-5 seg)
- `POST /api/v1/gis/analisis-espacial` - Análisis GIS
- `POST /api/v1/legal/buscar` - Búsqueda RAG normativa
