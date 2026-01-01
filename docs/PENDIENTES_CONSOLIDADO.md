# Pendientes Consolidado - Sistema de Prefactibilidad Ambiental Minera

**Fecha de actualizacion:** 2025-12-31
**Estado del proyecto:** Fase 4 (95% completada)
**Revision anterior:** 2025-12-31 (corregido tras auditoria de codigo)

---

## Resumen Ejecutivo

| Fase | Estado | Pendientes Reales |
|------|--------|-------------------|
| Fase 1-3 | COMPLETADAS | - |
| Fase 4: Frontend | 95% | 2 items |
| Fase 5: Validacion | 70% | 4 items |
| Fase 6: Produccion | 0% | 7 items |

**Total real:** ~13 items pendientes (anteriormente se listaban 30, pero 17 ya estaban implementados)

---

## ESTADO VERIFICADO - Lo que YA EXISTE

### Frontend (verificado en codigo)

| Componente | Ubicacion | Estado |
|------------|-----------|--------|
| Tests Corpus RAG | `frontend/tests/` | 21 archivos de tests |
| `cargarCapasDesdeAPI()` | `stores/map.ts:100-136` | Implementado completo |
| Capas WMS GeoServer | `components/map/MapContainer.vue` | TileWMS integrado |
| Tooltips en Mapa | `MapContainer.vue:141-159` | Overlay funcional |
| COMUNAS_POR_REGION | `types/project.ts:157-174` | 16 regiones completas |
| Campos dependientes | `ProyectoFormulario.vue:39-83` | computed + watch |
| Drag & Drop Upload | `DocumentoUpload.vue:48-82` | Funcional |
| Gestion Colecciones | `stores/corpus.ts` + `services/corpus.ts` | CRUD completo |
| Gestion Categorias | `CategoriaTree.vue` | Arbol jerarquico |
| Gestion Temas | `TemaSelector.vue` | Selector funcional |
| Utils format/validation | `utils/format.ts`, `utils/validation.ts` | Ambos existen |

### Backend - Auditoria (verificado en codigo)

| Componente | Ubicacion | Estado |
|------------|-----------|--------|
| Tabla auditoria_analisis | `docker/postgis/init/03_clientes_documentos.sql:142-175` | Creada |
| Indices espaciales | Distribuidos en 01-05_*.sql | 43+ indices (GIST, IVFFlat, GIN, BRIN) |
| Triggers de estados | `03_clientes_documentos.sql:196-332` | 5 triggers funcionales |
| Schema Pydantic | `backend/app/schemas/auditoria.py` | 125 lineas |
| Modelo SQLAlchemy | `backend/app/db/models/auditoria.py` | 55 lineas |
| Endpoint GET auditoria | `prefactibilidad.py:988-1031` | Funcional |
| Registro automatico | `prefactibilidad.py:924-943` | En analisis-integrado |

### Infraestructura SQL

Los archivos `07_auditoria_analisis.sql`, `08_indices_optimizacion.sql` y `09_triggers_estados.sql` mencionados anteriormente **NO son necesarios** porque sus funcionalidades fueron integradas en `03_clientes_documentos.sql` y `05_corpus_rag_schema.sql`.

---

## FASE 4: Frontend (5% restante)

### 4.1 Pendiente Real

#### [ ] Preview de PDF Inline
- **Prioridad:** Media
- **Descripcion:** Visor interactivo de PDF embebido en el panel de detalle
- **Ubicacion sugerida:** `frontend/src/components/corpus/PdfViewer.vue`
- **Opciones de implementacion:**
  - `vue-pdf-embed` - Libreria Vue para PDF
  - `iframe` con URL del archivo
  - `pdfjs-dist` - Mozilla PDF.js

```typescript
// Ejemplo con vue-pdf-embed
import VuePdfEmbed from 'vue-pdf-embed'

<VuePdfEmbed :source="pdfUrl" />
```

#### [ ] Formulario de Edicion de Documento (mejora)
- **Prioridad:** Baja
- **Descripcion:** El CorpusManager permite crear documentos, pero la edicion de metadatos podria mejorarse con un modal dedicado
- **Estado actual:** Funciona via actualizarDocumentoActual() pero sin UI dedicada

---

## FASE 5: Validacion (30% restante)

### 5.1 Componente Frontend

#### [ ] Componente de Trazabilidad de Auditoria
- **Prioridad:** Alta
- **Archivo:** `frontend/src/components/analysis/AuditoriaTrazabilidad.vue`
- **Descripcion:** Mostrar en la vista de analisis completado:
  - Capas GIS consultadas con version/fecha
  - Normativa citada (ley, articulo, letra)
  - Fragmentos RAG utilizados
  - Checksum de datos de entrada
  - Metricas de ejecucion (tiempos, tokens)

```vue
<template>
  <div class="card bg-base-100">
    <div class="card-body">
      <h3 class="card-title">Trazabilidad del Analisis</h3>

      <!-- Capas GIS -->
      <div class="collapse collapse-arrow">
        <input type="checkbox" />
        <div class="collapse-title">Capas GIS Consultadas ({{ auditoria.capas_gis_usadas.length }})</div>
        <div class="collapse-content">
          <ul>
            <li v-for="capa in auditoria.capas_gis_usadas" :key="capa.nombre">
              {{ capa.nombre }} - v{{ capa.version }}
            </li>
          </ul>
        </div>
      </div>

      <!-- Normativa -->
      <div class="collapse collapse-arrow">
        <input type="checkbox" />
        <div class="collapse-title">Normativa Citada</div>
        <div class="collapse-content">
          <ul>
            <li v-for="norma in auditoria.normativa_citada" :key="norma.tipo + norma.numero">
              {{ norma.tipo }} {{ norma.numero }}, Art. {{ norma.articulo }}
            </li>
          </ul>
        </div>
      </div>

      <!-- Metricas -->
      <div class="stats stats-vertical lg:stats-horizontal">
        <div class="stat">
          <div class="stat-title">Tiempo GIS</div>
          <div class="stat-value text-sm">{{ auditoria.tiempo_gis_ms }}ms</div>
        </div>
        <div class="stat">
          <div class="stat-title">Tiempo RAG</div>
          <div class="stat-value text-sm">{{ auditoria.tiempo_rag_ms }}ms</div>
        </div>
        <div class="stat">
          <div class="stat-title">Tokens LLM</div>
          <div class="stat-value text-sm">{{ auditoria.tokens_usados }}</div>
        </div>
      </div>
    </div>
  </div>
</template>
```

### 5.2 Tests Backend

#### [ ] Tests de Auditoria
- **Prioridad:** Alta
- **Archivo:** `backend/tests/test_auditoria.py`

```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_analisis_genera_auditoria():
    """Verificar que cada analisis genera registro de auditoria"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Crear proyecto con geometria
        proyecto_data = {
            "nombre": "Test Auditoria",
            "geometria": {"type": "Polygon", "coordinates": [[[-70.5, -23.5], [-70.4, -23.5], [-70.4, -23.4], [-70.5, -23.4], [-70.5, -23.5]]]}
        }

        # Ejecutar analisis integrado
        response = await client.post("/api/v1/prefactibilidad/analisis-integrado", json=proyecto_data)
        assert response.status_code == 200

        resultado = response.json()
        assert "auditoria_id" in resultado
        assert resultado["auditoria_id"] is not None


@pytest.mark.asyncio
async def test_auditoria_contiene_capas_gis():
    """Verificar que auditoria registra capas GIS consultadas"""
    # ... ejecutar analisis ...

    auditoria = response.json()
    assert len(auditoria["capas_gis_usadas"]) > 0
    assert all("nombre" in capa for capa in auditoria["capas_gis_usadas"])


@pytest.mark.asyncio
async def test_auditoria_inmutable():
    """Verificar que auditoria no se puede modificar via API"""
    # La API no expone endpoints de UPDATE/DELETE para auditoria
    # Verificar que no existen tales endpoints
    pass


@pytest.mark.asyncio
async def test_get_auditoria_por_analisis():
    """Verificar endpoint GET de auditoria"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(f"/api/v1/prefactibilidad/analisis/{analisis_id}/auditoria")
        assert response.status_code == 200

        auditoria = response.json()
        assert "checksum_datos_entrada" in auditoria
        assert "normativa_citada" in auditoria
```

### 5.3 Validacion con Expertos

#### [ ] Pruebas con Consultores Ambientales
- **Prioridad:** Alta (antes de produccion)
- **Actividades:**
  - Validar clasificacion DIA/EIA con 10+ casos reales
  - Recopilar feedback sobre alertas y severidades
  - Verificar que triggers Art. 11 se detectan correctamente

#### [ ] Documentacion de Limitaciones
- **Prioridad:** Media
- **Archivo:** `docs/LIMITACIONES_SISTEMA.md`
- **Contenido:**
  - Casos borde donde el sistema puede fallar
  - Disclaimer: "Este sistema es una herramienta de apoyo, no reemplaza el criterio profesional"
  - Tipos de proyectos no cubiertos
  - Limitaciones de las capas GIS (fecha de actualizacion, cobertura)

---

## FASE 6: Produccion

### 6.1 Seguridad

#### [ ] Auditoria de Seguridad
- **Prioridad:** Alta
- **Checklist OWASP Top 10:**
  - [ ] SQL Injection - Ya mitigado con whitelist de tablas GIS
  - [ ] XSS - Revisar sanitizacion en frontend
  - [ ] CSRF - Verificar tokens
  - [ ] Secrets en codigo - Mover API keys a secrets manager

#### [ ] Configuracion CORS Produccion
- **Archivo:** `backend/app/core/config.py`
- Restringir `CORS_ORIGINS` a dominios especificos

### 6.2 Infraestructura

#### [ ] Pipeline CI/CD
- **Prioridad:** Alta
- **Archivo:** `.github/workflows/ci.yml`

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test-backend:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgis/postgis:15-3.4
        env:
          POSTGRES_PASSWORD: test
        ports:
          - 5432:5432
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r backend/requirements.txt
      - run: pytest backend/tests/ -v

  test-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: cd frontend && npm ci && npm run test:run

  build:
    needs: [test-backend, test-frontend]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: docker compose -f docker/docker-compose.yml build
```

#### [ ] Sistema de Backups
- **Prioridad:** Alta
- **Script:** `scripts/backup.sh`

```bash
#!/bin/bash
BACKUP_DIR="/backups/mineria"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup PostgreSQL
docker exec mineria_postgis pg_dump -U mineria mineria | gzip > "$BACKUP_DIR/db_$DATE.sql.gz"

# Backup archivos subidos
tar -czf "$BACKUP_DIR/uploads_$DATE.tar.gz" /var/www/mineria/data/uploads/

# Retener ultimos 30 dias
find "$BACKUP_DIR" -mtime +30 -delete
```

#### [ ] Documentacion de Deployment
- **Archivo:** `docs/DEPLOYMENT.md`
- **Contenido:**
  - Requisitos del servidor
  - Variables de entorno de produccion
  - Configuracion SSL/TLS con nginx
  - Comandos de despliegue
  - Rollback procedure

### 6.3 Monitoreo

#### [ ] Health Checks Completos
- **Prioridad:** Media
- **Archivo:** `backend/app/api/v1/endpoints/health.py`

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from redis import Redis

router = APIRouter()

@router.get("/health/live")
async def liveness():
    """Kubernetes liveness probe"""
    return {"status": "alive"}

@router.get("/health/ready")
async def readiness(db: AsyncSession = Depends(get_db)):
    """Kubernetes readiness probe - verifica dependencias"""
    checks = {
        "database": await check_database(db),
        "redis": await check_redis(),
        "geoserver": await check_geoserver(),
        "embeddings": await check_embeddings_model()
    }

    all_healthy = all(c["healthy"] for c in checks.values())
    return {
        "status": "ready" if all_healthy else "not_ready",
        "checks": checks
    }
```

#### [ ] Logging Estructurado
- **Prioridad:** Media
- **Dependencia:** `structlog`
- **Archivo:** `backend/app/core/logging.py`

```python
import structlog

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
)

logger = structlog.get_logger()

# Uso:
logger.info("analisis_completado", proyecto_id=str(proyecto_id), clasificacion="EIA", duracion_ms=1234)
```

### 6.4 Documentacion

#### [ ] Manual de Usuario
- **Archivo:** `docs/MANUAL_USUARIO.md`
- **Contenido:**
  - Guia paso a paso con capturas
  - FAQ
  - Interpretacion de resultados
  - Contacto de soporte

---

## Checklist de Continuidad

### Antes de comenzar desarrollo:
- [x] Docker corriendo (`docker-compose ps`)
- [x] Frontend compila (`npm run build`)
- [x] Backend responde (`curl http://localhost:9001/docs`)
- [x] Tests pasan (`pytest tests/ -v`)

### Al completar cada item:
- [ ] Marcar como completado en este documento
- [ ] Ejecutar tests relacionados
- [ ] Actualizar documentacion si aplica

---

## Estimacion de Esfuerzo Actualizada

| Fase | Items Reales | Esfuerzo Estimado |
|------|--------------|-------------------|
| Fase 4 (restante) | 2 | 4-8 horas |
| Fase 5 (restante) | 4 | 16-24 horas |
| Fase 6 | 7 | 24-40 horas |
| **Total** | **13** | **44-72 horas** |

*Reduccion significativa respecto a estimacion anterior (90-140 horas) debido a que muchos items ya estaban implementados.*

---

## Historial de Cambios

| Fecha | Cambio |
|-------|--------|
| 2025-12-31 | Auditoria completa del codigo - 17 items marcados como YA IMPLEMENTADOS |
| 2025-12-31 | Documento inicial consolidado |

---

*Documento actualizado: 2025-12-31*
*Proxima revision sugerida: Al completar Fase 5*
