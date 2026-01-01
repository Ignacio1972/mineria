# Plan de Implementación - Fase 4: Frontend

## Resumen Ejecutivo

Desarrollo del frontend web para el Sistema de Prefactibilidad Ambiental Minera utilizando Vue 3, Vite, Tailwind CSS 4 y DaisyUI 5.

---

## Stack Tecnológico

| Componente | Tecnología | Versión |
|------------|------------|---------|
| Framework | Vue 3 + Composition API | 3.4+ |
| Build Tool | Vite | 5.x |
| Lenguaje | TypeScript | 5.x |
| CSS | Tailwind CSS | 4.x |
| Componentes UI | DaisyUI | 5.x |
| Mapas | OpenLayers + vue3-openlayers | 9.x |
| State Management | Pinia | 2.x |
| HTTP Client | Axios | 1.x |
| Utilidades | VueUse | 10.x |

---

## Estructura del Proyecto

```
frontend/
├── index.html
├── package.json
├── vite.config.ts
├── tsconfig.json
├── env.d.ts
├── .env.example
│
├── public/
│   └── favicon.ico
│
└── src/
    ├── main.ts                    # Entry point
    ├── App.vue                    # Root component
    │
    ├── assets/
    │   └── main.css               # Tailwind + DaisyUI imports
    │
    ├── components/
    │   ├── layout/
    │   │   ├── AppHeader.vue      # Header con logo y navegación
    │   │   ├── AppSidebar.vue     # Sidebar con controles
    │   │   └── AppFooter.vue      # Footer informativo
    │   │
    │   ├── map/
    │   │   ├── MapContainer.vue   # Contenedor principal del mapa
    │   │   ├── MapControls.vue    # Controles de zoom/capas
    │   │   ├── MapLayers.vue      # Gestión de capas GIS
    │   │   ├── DrawTools.vue      # Herramientas de dibujo
    │   │   └── LayerPanel.vue     # Panel de control de capas
    │   │
    │   ├── project/
    │   │   ├── ProjectForm.vue    # Formulario de datos del proyecto
    │   │   ├── ProjectCard.vue    # Tarjeta resumen del proyecto
    │   │   └── ProjectHistory.vue # Historial de proyectos
    │   │
    │   ├── analysis/
    │   │   ├── AnalysisPanel.vue  # Panel principal de resultados
    │   │   ├── GisResults.vue     # Resultados del análisis GIS
    │   │   ├── SeiaClassification.vue  # Clasificación DIA/EIA
    │   │   ├── TriggersList.vue   # Lista de triggers Art. 11
    │   │   ├── AlertsPanel.vue    # Panel de alertas por severidad
    │   │   └── AlertCard.vue      # Tarjeta individual de alerta
    │   │
    │   ├── report/
    │   │   ├── ReportViewer.vue   # Visualizador del informe
    │   │   ├── ReportSection.vue  # Sección individual del informe
    │   │   └── ExportButtons.vue  # Botones de exportación
    │   │
    │   └── common/
    │       ├── LoadingSpinner.vue # Indicador de carga
    │       ├── ConfidenceBadge.vue # Badge de nivel de confianza
    │       ├── SeverityBadge.vue  # Badge de severidad
    │       └── EmptyState.vue     # Estado vacío
    │
    ├── composables/
    │   ├── useApi.ts              # Wrapper de Axios
    │   ├── useAnalysis.ts         # Lógica de análisis
    │   ├── useProject.ts          # Gestión de proyecto
    │   ├── useMap.ts              # Estado del mapa
    │   └── useExport.ts           # Exportación de informes
    │
    ├── services/
    │   ├── api.ts                 # Cliente API base
    │   ├── prefactibilidad.ts     # Endpoints de prefactibilidad
    │   ├── gis.ts                 # Endpoints GIS
    │   └── legal.ts               # Endpoints legales
    │
    ├── stores/
    │   ├── project.ts             # Estado del proyecto actual
    │   ├── analysis.ts            # Estado del análisis
    │   ├── map.ts                 # Estado del mapa
    │   └── ui.ts                  # Estado de UI (modales, etc.)
    │
    ├── types/
    │   ├── project.ts             # Tipos del proyecto
    │   ├── analysis.ts            # Tipos del análisis
    │   ├── gis.ts                 # Tipos GIS
    │   └── api.ts                 # Tipos de respuestas API
    │
    └── utils/
        ├── format.ts              # Formateo de datos
        ├── validation.ts          # Validaciones
        └── geoJson.ts             # Utilidades GeoJSON
```

---

## Diseño de Interfaz

### Layout Principal

```
┌─────────────────────────────────────────────────────────────────┐
│  HEADER: Logo + "Sistema de Prefactibilidad Ambiental Minera"   │
├──────────────┬──────────────────────────────────────────────────┤
│              │                                                  │
│   SIDEBAR    │              MAPA INTERACTIVO                    │
│   200-280px  │              (OpenLayers)                        │
│              │                                                  │
│  ┌─────────┐ │  ┌──────────────────────────────────────────┐   │
│  │ Capas   │ │  │                                          │   │
│  │ GIS     │ │  │     Polígono dibujado por usuario        │   │
│  ├─────────┤ │  │                                          │   │
│  │ Datos   │ │  │     + Capas GIS superpuestas             │   │
│  │Proyecto │ │  │                                          │   │
│  ├─────────┤ │  └──────────────────────────────────────────┘   │
│  │ Acciones│ │                                                  │
│  │ Análisis│ │  [Herramientas de dibujo]  [Controles de mapa]  │
│  └─────────┘ │                                                  │
│              │                                                  │
├──────────────┴──────────────────────────────────────────────────┤
│  PANEL INFERIOR: Resultados / Alertas / Informe (colapsable)    │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐               │
│  │Resumen  │ │Triggers │ │Alertas  │ │Informe  │               │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘               │
└─────────────────────────────────────────────────────────────────┘
```

### Tema DaisyUI

```css
/* main.css */
@import "tailwindcss";
@plugin "daisyui" {
  themes: corporate --default, dark --prefersdark;
}
```

### Paleta de Colores para Alertas

| Severidad | Color DaisyUI | Uso |
|-----------|---------------|-----|
| CRITICA | `error` (rojo) | Alertas críticas, triggers bloqueantes |
| ALTA | `warning` (naranja) | Alertas importantes |
| MEDIA | `info` (azul) | Alertas moderadas |
| BAJA | `success` (verde) | Alertas informativas |

---

## Componentes Principales

### 1. MapContainer.vue

**Responsabilidades:**
- Renderizar mapa base (OpenStreetMap/Satellite)
- Cargar capas GIS desde GeoServer/API
- Permitir dibujo de polígonos
- Mostrar resultado de intersecciones
- Zoom a geometría del proyecto

**Capas GIS a mostrar:**
- Áreas protegidas (SNASPE)
- Glaciares
- Cuerpos de agua
- Comunidades indígenas
- Centros poblados
- Sitios patrimoniales
- Límites regionales/comunales

**Interacciones:**
- Click: Seleccionar features
- Draw: Dibujar polígono del proyecto
- Hover: Tooltip con información

### 2. ProjectForm.vue

**Campos del formulario (agrupados):**

```
Información Básica:
├── nombre* (text, min 3)
├── titular (text)
└── descripcion (textarea)

Ubicación:
├── region (select)
└── comuna (select, dependiente de región)

Características del Proyecto:
├── tipo_mineria (select: Tajo abierto, Subterránea, Mixta)
├── mineral_principal (text)
├── fase (select: Exploración, Explotación, Cierre)
├── superficie_ha (number)
├── vida_util_anos (number)
└── produccion_estimada (text)

Recursos:
├── uso_agua_lps (number)
├── fuente_agua (select: Subterránea, Superficial, Mar, Desalinizada)
└── energia_mw (number)

Empleo e Inversión:
├── trabajadores_construccion (number)
├── trabajadores_operacion (number)
└── inversion_musd (number)
```

### 3. AnalysisPanel.vue

**Tabs/Secciones:**
1. **Resumen**: Clasificación DIA/EIA + indicadores clave
2. **Análisis GIS**: Tabla con intersecciones por capa
3. **Triggers Art. 11**: Lista de triggers detectados
4. **Alertas**: Alertas agrupadas por severidad
5. **Informe**: Visualización del informe generado

### 4. AlertsPanel.vue

**Visualización por severidad:**
```
┌─ CRÍTICAS (2) ─────────────────────────────────┐
│ [!] Intersección con Área Protegida            │
│ [!] Afectación Directa de Glaciares            │
└────────────────────────────────────────────────┘

┌─ ALTAS (3) ─────────────────────────────────────┐
│ [△] Proximidad a Comunidades Indígenas         │
│ [△] Alto Consumo de Agua                       │
│ [△] Proximidad a Centros Poblados              │
└────────────────────────────────────────────────┘

┌─ MEDIAS (1) ────────────────────────────────────┐
│ [i] Potencial Impacto por Emisiones            │
└────────────────────────────────────────────────┘
```

---

## Flujos de Usuario

### Flujo Principal: Nuevo Análisis

```
1. Usuario abre la aplicación
   └─> Vista inicial con mapa centrado en Chile

2. Usuario dibuja polígono en el mapa
   └─> Herramienta de dibujo activa
   └─> Polígono se muestra en el mapa

3. Usuario completa formulario del proyecto
   └─> Campos obligatorios: nombre
   └─> Campos recomendados: tipo, superficie, agua

4. Usuario hace clic en "Analizar"
   └─> Opción: Análisis rápido (sin LLM) / Completo (con LLM)
   └─> Loading spinner mientras procesa

5. Sistema muestra resultados
   └─> Clasificación DIA/EIA prominente
   └─> Panel de triggers y alertas
   └─> Mapa actualizado con intersecciones

6. Usuario puede exportar
   └─> PDF, DOCX, TXT, HTML
```

### Flujo Secundario: Modificar y Re-analizar

```
1. Usuario modifica polígono (mover vértices)
2. Usuario modifica datos del proyecto
3. Clic en "Re-analizar"
4. Nuevos resultados
```

---

## Integración con API Backend

### Endpoints a Consumir

| Endpoint | Método | Uso en Frontend |
|----------|--------|-----------------|
| `/api/v1/prefactibilidad/analisis` | POST | Análisis completo |
| `/api/v1/prefactibilidad/analisis-rapido` | POST | Análisis sin LLM |
| `/api/v1/prefactibilidad/exportar/{formato}` | POST | Exportar informe |
| `/api/v1/gis/capas` | GET | Listar capas disponibles |
| `/api/v1/gis/analisis-espacial` | POST | Análisis GIS puro |
| `/api/v1/legal/buscar` | POST | Búsqueda de normativa |

### Tipos TypeScript

```typescript
// types/project.ts
interface DatosProyecto {
  nombre: string;
  tipo_mineria?: string;
  mineral_principal?: string;
  fase?: string;
  titular?: string;
  region?: string;
  comuna?: string;
  superficie_ha?: number;
  vida_util_anos?: number;
  uso_agua_lps?: number;
  fuente_agua?: string;
  energia_mw?: number;
  trabajadores_construccion?: number;
  trabajadores_operacion?: number;
  inversion_musd?: number;
  produccion_estimada?: string;
  descripcion?: string;
}

interface GeometriaGeoJSON {
  type: 'Polygon' | 'MultiPolygon';
  coordinates: number[][][];
}

// types/analysis.ts
type Severidad = 'CRITICA' | 'ALTA' | 'MEDIA' | 'BAJA' | 'INFO';
type NivelConfianza = 'MUY_ALTA' | 'ALTA' | 'MEDIA' | 'BAJA';
type ViaIngreso = 'EIA' | 'DIA';
type LetraTrigger = 'a' | 'b' | 'c' | 'd' | 'e' | 'f';

interface Trigger {
  letra: LetraTrigger;
  descripcion: string;
  detalle: string;
  severidad: Severidad;
  fundamento_legal: string;
  peso: number;
}

interface Alerta {
  id: string;
  nivel: Severidad;
  categoria: string;
  titulo: string;
  descripcion: string;
  acciones_requeridas: string[];
}

interface ClasificacionSEIA {
  via_ingreso_recomendada: ViaIngreso;
  confianza: number;
  nivel_confianza: NivelConfianza;
  justificacion: string;
  puntaje_matriz: number;
}

interface ResultadoAnalisis {
  id: string;
  fecha_analisis: string;
  proyecto: DatosProyecto;
  resultado_gis: ResultadoGIS;
  clasificacion_seia: ClasificacionSEIA;
  triggers: Trigger[];
  alertas: Alerta[];
  normativa_citada: NormativaCitada[];
  informe?: Informe;
  metricas: Metricas;
}
```

---

## Tareas de Implementación

### Etapa 1: Setup Inicial
- [ ] Crear proyecto Vue 3 + Vite + TypeScript
- [ ] Configurar Tailwind CSS 4 + DaisyUI 5
- [ ] Configurar estructura de carpetas
- [ ] Definir tipos TypeScript
- [ ] Configurar Pinia stores
- [ ] Configurar cliente API (Axios)

### Etapa 2: Layout y Navegación
- [ ] Implementar AppHeader
- [ ] Implementar AppSidebar
- [ ] Implementar layout responsivo
- [ ] Configurar tema DaisyUI (corporate)

### Etapa 3: Mapa Interactivo
- [ ] Integrar vue3-openlayers
- [ ] Configurar mapa base
- [ ] Implementar herramientas de dibujo
- [ ] Cargar capas GIS
- [ ] Implementar controles de capas
- [ ] Implementar tooltips/popups

### Etapa 4: Formulario de Proyecto
- [ ] Implementar ProjectForm
- [ ] Validaciones de campos
- [ ] Campos dependientes (región/comuna)
- [ ] Guardar en store

### Etapa 5: Análisis y Resultados
- [ ] Implementar llamada a API de análisis
- [ ] Implementar AnalysisPanel
- [ ] Implementar SeiaClassification (prominente)
- [ ] Implementar TriggersList
- [ ] Implementar AlertsPanel
- [ ] Implementar GisResults

### Etapa 6: Informe y Exportación
- [ ] Implementar ReportViewer
- [ ] Implementar ExportButtons
- [ ] Descargar archivos (PDF, DOCX, etc.)

### Etapa 7: Persistencia
- [ ] Guardar proyectos en localStorage
- [ ] Historial de análisis
- [ ] Cargar proyecto existente

### Etapa 8: Testing y Pulido
- [ ] Tests de componentes
- [ ] Manejo de errores
- [ ] Estados de loading
- [ ] Estados vacíos
- [ ] Responsive design

---

## Configuración de Desarrollo

### package.json (dependencias principales)

```json
{
  "dependencies": {
    "vue": "^3.4",
    "vue-router": "^4.2",
    "pinia": "^2.1",
    "axios": "^1.6",
    "@vueuse/core": "^10.7",
    "ol": "^9.0",
    "vue3-openlayers": "^9.0"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.0",
    "typescript": "^5.3",
    "vite": "^5.0",
    "tailwindcss": "^4.0",
    "daisyui": "^5.0",
    "@types/node": "^20"
  }
}
```

### Comandos

```bash
# Desarrollo
npm run dev

# Build
npm run build

# Preview
npm run preview
```

---

## Consideraciones Técnicas

### Performance
- Lazy loading de componentes pesados (mapa)
- Debounce en búsquedas
- Caché de capas GIS
- Virtualización de listas largas (alertas)

### Accesibilidad
- Labels en todos los inputs
- Contraste de colores WCAG AA
- Navegación por teclado
- ARIA labels en componentes interactivos

### Responsividad
- Mobile-first approach
- Sidebar colapsable en mobile
- Mapa fullscreen en mobile
- Panel de resultados como bottom sheet en mobile

### Manejo de Errores
- Toast notifications para errores de API
- Estados de error en componentes
- Retry automático en fallos de red
- Validación client-side antes de enviar

---

## Entregable Final

> **Entregable Fase 4:** Aplicación web funcional end-to-end que permite:
> 1. Dibujar polígonos de proyectos mineros en mapa interactivo
> 2. Ingresar datos técnicos del proyecto
> 3. Ejecutar análisis de prefactibilidad ambiental
> 4. Visualizar clasificación SEIA, triggers y alertas
> 5. Generar y exportar informes en múltiples formatos

---

*Documento creado: 2024-12-26*
*Versión: 1.0*
