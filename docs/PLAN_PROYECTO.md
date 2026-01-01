# Plan General y Roadmap: Sistema de Prefactibilidad Ambiental Minera

## Visión del Proyecto

Sistema híbrido LLM + GIS + RAG para análisis automatizado de prefactibilidad ambiental de proyectos mineros en Chile, con capacidad de generar informes y recomendaciones basadas en normativa vigente.

---

## Arquitectura General

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND WEB                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ Mapa GIS    │  │ Formulario  │  │ Visualizador de         │  │
│  │ Interactivo │  │ de Proyecto │  │ Informes                │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      BACKEND API (FastAPI)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │ Módulo GIS   │  │ Módulo RAG   │  │ Módulo Reglas SEIA   │   │
│  │ - Análisis   │  │ - Búsqueda   │  │ - Triggers DIA/EIA   │   │
│  │   espacial   │  │   semántica  │  │ - Validaciones       │   │
│  └──────────────┘  └──────────────┘  └──────────────────────┘   │
│                              │                                   │
│  ┌───────────────────────────┴───────────────────────────────┐  │
│  │              Motor de Generación de Informes               │  │
│  │         (LLM con contexto GIS + RAG + Reglas)             │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      CAPA DE DATOS                               │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐   │
│  │ PostGIS          │  │ Vector DB        │  │ Caché/Redis  │   │
│  │ - Capas GIS      │  │ - Embeddings     │  │ - Sesiones   │   │
│  │ - Proyectos      │  │ - Corpus legal   │  │ - Resultados │   │
│  └──────────────────┘  └──────────────────┘  └──────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Componentes del Sistema

### 1. Capa GIS

**Base de datos espacial (PostGIS)**
- Áreas protegidas (SNASPE, Santuarios, Reservas)
- Glaciares y ambiente periglaciar
- Cuerpos de agua (ríos, lagos, humedales)
- Comunidades indígenas (ADI, tierras indígenas)
- Centros poblados
- Sitios arqueológicos y patrimoniales
- Zonas de riesgo (fallas geológicas, volcanes)
- Límites administrativos (regiones, comunas)

**Funcionalidades**
- Intersección de polígonos de proyecto con capas sensibles
- Cálculo de distancias a elementos críticos
- Generación de buffer zones
- Estadísticas de terreno (altitud, pendiente)

### 2. Capa RAG Legal

**Corpus normativo**
- Ley 19.300 (Bases Generales del Medio Ambiente)
- DS 40/2012 Reglamento SEIA
- Guías SEA (línea base, participación ciudadana, medio humano)
- Normativa sectorial (DGA, SERNAGEOMIN, SAG, CMN)
- Jurisprudencia ambiental relevante
- EIAs y DIAs mineros aprobados (ejemplos de referencia)

**Pipeline de procesamiento**
- Extracción de texto (PDF/HTML)
- Segmentación por artículos/secciones
- Generación de embeddings
- Indexación con metadatos (tipo, tema, vigencia)

### 3. Motor de Reglas SEIA

**Triggers automáticos para EIA (Art. 11 Ley 19.300)**
- Riesgo para salud de la población
- Efectos adversos significativos sobre recursos naturales
- Reasentamiento de comunidades
- Alteración significativa de sistemas de vida
- Localización en áreas protegidas
- Alteración de monumentos/patrimonio
- Alteración de paisaje o sitios con valor turístico

**Clasificación de proyectos**
- Probable DIA
- Probable EIA
- Requiere análisis adicional

### 4. Motor LLM

**Funciones**
- Interpretación de resultados GIS en contexto normativo
- Generación de texto técnico para informes
- Síntesis de normativa aplicable
- Recomendaciones con citas legales

**Controles**
- Siempre citar fuentes normativas
- Indicar nivel de certeza
- Marcar cuando requiere revisión humana

---

## Stack Tecnológico

| Componente | Tecnología |
|------------|------------|
| Backend API | Python 3.11+ / FastAPI |
| Base de datos espacial | PostgreSQL 15 + PostGIS 3.4 |
| Servidor de mapas | GeoServer |
| Vector DB | pgvector (integrado en PostgreSQL) |
| LLM | Claude API / Ollama (local) |
| Frontend | React + OpenLayers/Leaflet |
| Contenedores | Docker + Docker Compose |
| Caché | Redis |
| Cola de tareas | Celery (para informes largos) |

---

## Roadmap de Implementación

### Fase 1: Fundamentos (Semanas 1-4)

#### 1.1 Infraestructura Base
- [ ] Configurar entorno Docker (PostGIS + GeoServer + Redis)
- [ ] Estructura de proyecto FastAPI
- [ ] Sistema de configuración y variables de entorno
- [ ] Logging y monitoreo básico

#### 1.2 Base de Datos Espacial
- [ ] Diseño de esquema PostGIS
- [ ] Scripts de migración
- [ ] Carga inicial de capas GIS (región piloto: Antofagasta)
  - Áreas protegidas
  - Comunidades indígenas
  - Cuerpos de agua principales
  - Límites comunales

#### 1.3 API GIS Básica
- [ ] Endpoint POST `/api/v1/analisis-espacial`
  - Input: GeoJSON del polígono del proyecto
  - Output: JSON con intersecciones y distancias
- [ ] Tests unitarios y de integración

**Entregable Fase 1:** API que recibe un polígono y retorna análisis espacial básico.

---

### Fase 2: RAG Legal (Semanas 5-8)

#### 2.1 Pipeline de Ingestión
- [ ] Scraper/descargador de normativa (BCN, SEA)
- [ ] Parser de PDFs (PyMuPDF/pdfplumber)
- [ ] Segmentador de documentos legales
- [ ] Extractor de metadatos

#### 2.2 Indexación
- [ ] Configurar pgvector en PostgreSQL
- [ ] Modelo de embeddings (sentence-transformers o similar)
- [ ] Índice de búsqueda semántica
- [ ] Índice de búsqueda por metadatos

#### 2.3 Corpus Inicial
- [ ] Ley 19.300 completa
- [ ] DS 40/2012 (Reglamento SEIA)
- [ ] 3-5 guías SEA prioritarias
- [ ] 2-3 EIAs mineros de referencia

#### 2.4 API de Búsqueda
- [ ] Endpoint POST `/api/v1/buscar-normativa`
  - Input: query + filtros (tema, tipo documento)
  - Output: pasajes relevantes con metadatos y scores

**Entregable Fase 2:** Sistema RAG funcional con corpus legal básico.

---

### Fase 3: Motor de Análisis (Semanas 9-12)

#### 3.1 Reglas SEIA
- [ ] Implementar evaluador de triggers Art. 11
- [ ] Matriz de decisión DIA vs EIA
- [ ] Sistema de alertas por tipo de impacto

#### 3.2 Integración LLM
- [ ] Diseño de prompts especializados
- [ ] Templates de salida estructurada
- [ ] Sistema de citación automática
- [ ] Manejo de contexto (GIS + RAG + reglas)

#### 3.3 Generador de Informes
- [ ] Endpoint POST `/api/v1/analisis-prefactibilidad`
  - Input: polígono + parámetros del proyecto
  - Output: JSON estructurado + texto del informe
- [ ] Formato de informe estándar
- [ ] Exportación a PDF/DOCX

**Entregable Fase 3:** Sistema completo de análisis con generación de informes.

---

### Fase 4: Frontend (Semanas 13-16)

#### 4.1 Mapa Interactivo
- [ ] Componente de mapa (OpenLayers)
- [ ] Herramienta de dibujo de polígonos
- [ ] Visualización de capas GIS
- [ ] Controles de capas (on/off, opacidad)

#### 4.2 Interfaz de Usuario
- [ ] Formulario de datos del proyecto
- [ ] Panel de resultados de análisis
- [ ] Visualizador de alertas/riesgos
- [ ] Vista de informe generado

#### 4.3 Funcionalidades
- [ ] Guardar/cargar proyectos
- [ ] Historial de análisis
- [ ] Exportación de resultados

**Entregable Fase 4:** Aplicación web funcional end-to-end.

---

### Fase 5: Validación y Mejoras (Semanas 17-20)

#### 5.1 Validación con Expertos
- [ ] Pruebas con consultores ambientales
- [ ] Revisión por abogados especializados
- [ ] Ajustes a reglas y prompts
- [ ] Documentación de limitaciones

#### 5.2 Ampliación de Datos
- [ ] Más capas GIS (todas las regiones)
- [ ] Corpus legal expandido
- [ ] Más EIAs de referencia

#### 5.3 Mejoras de UX
- [ ] Optimización de tiempos de respuesta
- [ ] Mejoras de interfaz según feedback
- [ ] Tutoriales y ayuda contextual

**Entregable Fase 5:** Sistema validado y listo para uso piloto.

---

### Fase 6: Producción (Semanas 21-24)

#### 6.1 Preparación
- [ ] Auditoría de seguridad
- [ ] Optimización de rendimiento
- [ ] Sistema de backups
- [ ] Monitoreo y alertas

#### 6.2 Despliegue
- [ ] Infraestructura de producción
- [ ] CI/CD pipeline
- [ ] Documentación de API
- [ ] Manual de usuario

#### 6.3 Operación
- [ ] Sistema de actualización de normativa
- [ ] Proceso de actualización de capas GIS
- [ ] Soporte y mantenimiento

**Entregable Fase 6:** Sistema en producción.

---

## Estructura de Directorios Propuesta

```
mineria/
├── docker/
│   ├── docker-compose.yml
│   ├── postgis/
│   ├── geoserver/
│   └── redis/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── v1/
│   │   │   │   ├── endpoints/
│   │   │   │   │   ├── analisis_espacial.py
│   │   │   │   │   ├── buscar_normativa.py
│   │   │   │   │   ├── prefactibilidad.py
│   │   │   │   │   └── proyectos.py
│   │   │   │   └── router.py
│   │   │   └── deps.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   └── security.py
│   │   ├── db/
│   │   │   ├── session.py
│   │   │   └── models/
│   │   ├── services/
│   │   │   ├── gis/
│   │   │   │   ├── analisis.py
│   │   │   │   └── capas.py
│   │   │   ├── rag/
│   │   │   │   ├── embeddings.py
│   │   │   │   ├── busqueda.py
│   │   │   │   └── ingestor.py
│   │   │   ├── reglas/
│   │   │   │   ├── seia.py
│   │   │   │   └── triggers.py
│   │   │   └── llm/
│   │   │       ├── cliente.py
│   │   │       ├── prompts.py
│   │   │       └── generador.py
│   │   └── main.py
│   ├── tests/
│   ├── alembic/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Map/
│   │   │   ├── ProjectForm/
│   │   │   └── ReportViewer/
│   │   ├── services/
│   │   ├── hooks/
│   │   └── App.tsx
│   └── package.json
├── data/
│   ├── gis/
│   │   └── capas/
│   ├── legal/
│   │   ├── raw/
│   │   └── processed/
│   └── scripts/
├── docs/
│   ├── api/
│   ├── arquitectura/
│   └── usuario/
└── README.md
```

---

## Fuentes de Datos GIS

| Capa | Fuente | Formato |
|------|--------|---------|
| Áreas protegidas SNASPE | CONAF | Shapefile |
| Sitios Ramsar | MMA | Shapefile |
| Glaciares | DGA | Shapefile |
| Hidrografía | DGA/IDE Chile | Shapefile |
| Comunidades indígenas | CONADI | Shapefile |
| Sitios arqueológicos | CMN | Shapefile |
| División político-administrativa | IDE Chile | Shapefile |
| Modelo de elevación | IDE Chile | Raster |

---

## Fuentes de Corpus Legal

| Documento | Fuente | Prioridad |
|-----------|--------|-----------|
| Ley 19.300 | BCN | Alta |
| DS 40/2012 (Reglamento SEIA) | BCN | Alta |
| Guías SEA | sea.gob.cl | Alta |
| Normativa DGA | dga.cl | Media |
| Normativa SERNAGEOMIN | sernageomin.cl | Media |
| EIAs aprobados | sea.gob.cl/consultas | Media |
| Jurisprudencia Tribunal Ambiental | tribunalambiental.cl | Baja |

---

## Riesgos y Mitigaciones

| Riesgo | Impacto | Mitigación |
|--------|---------|------------|
| Datos GIS desactualizados | Alto | Establecer proceso de actualización periódica, indicar fecha de datos |
| Cambios en normativa | Alto | Sistema de alertas de cambios legales, versionamiento de corpus |
| Errores en recomendaciones | Crítico | Disclaimer claro, validación con expertos, logging de decisiones |
| Rendimiento en análisis complejos | Medio | Caché, procesamiento asíncrono, optimización de queries |
| Dependencia de API LLM externa | Medio | Soporte para modelos locales (Ollama), fallback |

---

## Indicadores de Éxito

### MVP (Fase 3)
- Análisis espacial en < 5 segundos para polígono típico
- Búsqueda RAG con precisión > 80% en queries de prueba
- Clasificación DIA/EIA correcta en > 70% de casos de prueba

### Producción (Fase 6)
- Tiempo de generación de informe < 2 minutos
- Satisfacción de usuarios piloto > 4/5
- Reducción de tiempo de análisis preliminar en > 50%

---

## Próximos Pasos Inmediatos

1. **Configurar entorno de desarrollo**
   - Docker Compose con PostGIS y servicios base
   - Estructura inicial del proyecto FastAPI

2. **Obtener datos GIS iniciales**
   - Descargar capas de IDE Chile para región de Antofagasta
   - Cargar en PostGIS y validar

3. **Prototipo de análisis espacial**
   - Implementar primer endpoint de intersección
   - Probar con polígono de ejemplo

4. **Definir esquema de datos del proyecto**
   - Campos del formulario de proyecto minero
   - Modelo de datos en PostgreSQL
