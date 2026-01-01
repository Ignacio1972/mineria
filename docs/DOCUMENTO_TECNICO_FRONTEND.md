# Documento Técnico: Frontend - Sistema de Gestión de Proyectos Mineros

**Versión:** 1.0
**Fecha:** 2025-12-27
**Stack:** Vue 3 + Vite + TypeScript + Pinia + Tailwind CSS 4 + DaisyUI 5 + OpenLayers 10
**Audiencia:** Desarrolladores Frontend Senior

---

## 1. Resumen Ejecutivo

### Objetivo
Rediseñar el frontend para soportar un sistema de gestión de proyectos completo, migrando de localStorage a una API REST, e implementando nuevas vistas para Clientes, Proyectos y Dashboard.

### Cambios Principales

| Antes | Después |
|-------|---------|
| localStorage | API REST (PostgreSQL) |
| Vista única (ProyectoView) | Dashboard + CRUD Clientes + CRUD Proyectos |
| Geometría obligatoria para guardar | Guardado progresivo sin geometría |
| Sin concepto de cliente | Clientes como entidad principal |
| Sin documentos | Upload de documentos categorizados |
| Sin progreso visual | Barra de progreso + validación visual |

---

## 2. Arquitectura de Rutas

### 2.1 Nuevas Rutas

```typescript
// frontend/src/router/index.ts

const routes = [
  // Dashboard
  {
    path: '/',
    name: 'dashboard',
    component: () => import('@/views/DashboardView.vue'),
    meta: { title: 'Dashboard' }
  },

  // Clientes
  {
    path: '/clientes',
    name: 'clientes',
    component: () => import('@/views/ClientesView.vue'),
    meta: { title: 'Clientes' }
  },
  {
    path: '/clientes/nuevo',
    name: 'cliente-nuevo',
    component: () => import('@/views/ClienteFormView.vue'),
    meta: { title: 'Nuevo Cliente' }
  },
  {
    path: '/clientes/:id',
    name: 'cliente-detalle',
    component: () => import('@/views/ClienteDetalleView.vue'),
    meta: { title: 'Detalle Cliente' }
  },
  {
    path: '/clientes/:id/editar',
    name: 'cliente-editar',
    component: () => import('@/views/ClienteFormView.vue'),
    meta: { title: 'Editar Cliente' }
  },

  // Proyectos
  {
    path: '/proyectos',
    name: 'proyectos',
    component: () => import('@/views/ProyectosView.vue'),
    meta: { title: 'Proyectos' }
  },
  {
    path: '/proyectos/nuevo',
    name: 'proyecto-nuevo',
    component: () => import('@/views/ProyectoFormView.vue'),
    meta: { title: 'Nuevo Proyecto' }
  },
  {
    path: '/proyectos/:id',
    name: 'proyecto-detalle',
    component: () => import('@/views/ProyectoDetalleView.vue'),
    meta: { title: 'Detalle Proyecto' }
  },
  {
    path: '/proyectos/:id/editar',
    name: 'proyecto-editar',
    component: () => import('@/views/ProyectoFormView.vue'),
    meta: { title: 'Editar Proyecto' }
  },
  {
    path: '/proyectos/:id/mapa',
    name: 'proyecto-mapa',
    component: () => import('@/views/ProyectoMapaView.vue'),
    meta: { title: 'Editar Ubicación' }
  },
  {
    path: '/proyectos/:id/analisis',
    name: 'proyecto-analisis',
    component: () => import('@/views/ProyectoAnalisisView.vue'),
    meta: { title: 'Análisis' }
  },

  // Análisis global
  {
    path: '/analisis',
    name: 'analisis-historial',
    component: () => import('@/views/AnalisisHistorialView.vue'),
    meta: { title: 'Historial de Análisis' }
  },

  // Legacy (mantener compatibilidad temporal)
  {
    path: '/proyecto-legacy/:id?',
    name: 'proyecto-legacy',
    component: () => import('@/views/ProyectoView.vue'),
    meta: { title: 'Proyecto (Legacy)' }
  },

  // 404
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: () => import('@/views/NotFoundView.vue'),
  },
]
```

### 2.2 Diagrama de Navegación

```
┌─────────────────────────────────────────────────────────────────┐
│                         DASHBOARD (/)                           │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐                         │
│  │Clientes │  │Proyectos│  │Análisis │                         │
│  │   12    │  │   47    │  │   23    │                         │
│  └────┬────┘  └────┬────┘  └────┬────┘                         │
│       │            │            │                               │
│  [+Nuevo]     [+Nuevo]     [Ver todos]                         │
└───────┼────────────┼────────────┼───────────────────────────────┘
        │            │            │
        ▼            │            ▼
┌───────────────┐    │    ┌───────────────┐
│  /clientes    │    │    │  /analisis    │
│   (listado)   │    │    │ (historial)   │
└───────┬───────┘    │    └───────────────┘
        │            │
        ▼            ▼
┌───────────────┐  ┌───────────────┐
│/clientes/:id  │  │  /proyectos   │
│  (detalle)    │  │   (listado)   │
│               │  │               │
│ ┌───────────┐ │  └───────┬───────┘
│ │Proyectos  │ │          │
│ │del cliente│ │          ▼
│ └───────────┘ │  ┌───────────────────────────────────────────┐
└───────────────┘  │           /proyectos/:id                  │
                   │              (detalle)                    │
                   │                                           │
                   │  TABS: [Info] [Mapa] [Análisis] [Docs]    │
                   │                                           │
                   │  ┌─────────────────────────────────────┐  │
                   │  │  PROGRESO: ████████░░ 80%           │  │
                   │  │  ✓ Cliente    ✓ Datos básicos       │  │
                   │  │  ○ Geometría  ○ Análisis            │  │
                   │  └─────────────────────────────────────┘  │
                   │                                           │
                   │  [Guardar] [Análisis Rápido] [Completo]   │
                   └───────────────────────────────────────────┘
```

---

## 3. Tipos TypeScript

### 3.1 Crear archivo: `frontend/src/types/cliente.ts`

```typescript
/**
 * Tipos para Cliente.
 */

export interface Cliente {
  id: string
  rut: string | null
  razon_social: string
  nombre_fantasia: string | null
  email: string | null
  telefono: string | null
  direccion: string | null
  notas: string | null
  activo: boolean
  created_at: string
  updated_at: string | null
  cantidad_proyectos: number
}

export interface ClienteCreate {
  rut?: string | null
  razon_social: string
  nombre_fantasia?: string | null
  email?: string | null
  telefono?: string | null
  direccion?: string | null
  notas?: string | null
}

export interface ClienteUpdate extends Partial<ClienteCreate> {
  activo?: boolean
}

export interface ClienteListResponse {
  items: Cliente[]
  total: number
  page: number
  page_size: number
  pages: number
}
```

### 3.2 Crear archivo: `frontend/src/types/documento.ts`

```typescript
/**
 * Tipos para Documento.
 */

export type CategoriaDocumento = 'legal' | 'tecnico' | 'ambiental' | 'cartografia' | 'otro'

export const CATEGORIAS_DOCUMENTO: { value: CategoriaDocumento; label: string; descripcion: string }[] = [
  { value: 'legal', label: 'Legal', descripcion: 'Permisos, contratos, escrituras' },
  { value: 'tecnico', label: 'Técnico', descripcion: 'Estudios técnicos, planos, informes' },
  { value: 'ambiental', label: 'Ambiental', descripcion: 'Líneas base, EIA/DIA anteriores' },
  { value: 'cartografia', label: 'Cartografía', descripcion: 'Mapas, imágenes satelitales' },
  { value: 'otro', label: 'Otro', descripcion: 'Documentos varios' },
]

export interface Documento {
  id: string
  proyecto_id: string
  nombre: string
  nombre_original: string
  categoria: CategoriaDocumento
  descripcion: string | null
  archivo_path: string
  mime_type: string
  tamano_bytes: number
  tamano_mb: number
  checksum_sha256: string | null
  created_at: string
}

export interface DocumentoCreate {
  nombre: string
  categoria: CategoriaDocumento
  descripcion?: string | null
}

export interface DocumentoListResponse {
  items: Documento[]
  total: number
  total_bytes: number
  total_mb: number
}
```

### 3.3 Actualizar archivo: `frontend/src/types/project.ts`

```typescript
/**
 * Tipos para Proyecto (ACTUALIZADO).
 */

// Estados del proyecto
export type EstadoProyecto =
  | 'borrador'
  | 'completo'
  | 'con_geometria'
  | 'analizado'
  | 'en_revision'
  | 'aprobado'
  | 'rechazado'
  | 'archivado'

export const ESTADOS_PROYECTO: { value: EstadoProyecto; label: string; color: string; descripcion: string }[] = [
  { value: 'borrador', label: 'Borrador', color: 'badge-ghost', descripcion: 'Datos incompletos' },
  { value: 'completo', label: 'Completo', color: 'badge-info', descripcion: 'Datos listos, falta geometría' },
  { value: 'con_geometria', label: 'Con Geometría', color: 'badge-primary', descripcion: 'Listo para análisis' },
  { value: 'analizado', label: 'Analizado', color: 'badge-success', descripcion: 'Análisis ejecutado' },
  { value: 'en_revision', label: 'En Revisión', color: 'badge-warning', descripcion: 'Revisión por especialista' },
  { value: 'aprobado', label: 'Aprobado', color: 'badge-success', descripcion: 'Listo para ingreso SEIA' },
  { value: 'rechazado', label: 'Rechazado', color: 'badge-error', descripcion: 'Requiere correcciones' },
  { value: 'archivado', label: 'Archivado', color: 'badge-neutral', descripcion: 'Inactivo' },
]

// Geometría GeoJSON
export interface GeometriaGeoJSON {
  type: 'Polygon' | 'MultiPolygon'
  coordinates: number[][][] | number[][][][]
}

// Datos del proyecto
export interface DatosProyecto {
  nombre: string
  cliente_id?: string | null
  tipo_mineria?: 'Tajo abierto' | 'Subterránea' | 'Mixta' | null
  mineral_principal?: string | null
  fase?: 'Exploración' | 'Explotación' | 'Cierre' | null
  titular?: string | null
  region?: string | null
  comuna?: string | null
  superficie_ha?: number | null
  vida_util_anos?: number | null
  uso_agua_lps?: number | null
  fuente_agua?: 'Subterránea' | 'Superficial' | 'Mar' | 'Desalinizada' | null
  energia_mw?: number | null
  trabajadores_construccion?: number | null
  trabajadores_operacion?: number | null
  inversion_musd?: number | null
  descripcion?: string | null
  // Campos SEIA adicionales
  descarga_diaria_ton?: number | null
  emisiones_co2_ton_ano?: number | null
  requiere_reasentamiento?: boolean
  afecta_patrimonio?: boolean
}

// Campos pre-calculados GIS
export interface CamposPreCalculados {
  afecta_glaciares: boolean
  dist_area_protegida_km: number | null
  dist_comunidad_indigena_km: number | null
  dist_centro_poblado_km: number | null
}

// Proyecto completo
export interface Proyecto extends DatosProyecto, CamposPreCalculados {
  id: string
  estado: EstadoProyecto
  porcentaje_completado: number
  tiene_geometria: boolean
  puede_analizar: boolean
  cliente_razon_social: string | null
  total_documentos: number
  total_analisis: number
  ultimo_analisis: string | null
  created_at: string
  updated_at: string | null
}

// Proyecto con geometría
export interface ProyectoConGeometria extends Proyecto {
  geometria: GeometriaGeoJSON | null
}

// Para crear proyecto
export interface ProyectoCreate extends DatosProyecto {
  geometria?: GeometriaGeoJSON | null
}

// Para actualizar proyecto
export type ProyectoUpdate = Partial<DatosProyecto>

// Para actualizar geometría
export interface ProyectoGeometriaUpdate {
  geometria: GeometriaGeoJSON
}

// Respuesta paginada
export interface ProyectoListResponse {
  items: Proyecto[]
  total: number
  page: number
  page_size: number
  pages: number
}

// Filtros
export interface FiltrosProyecto {
  cliente_id?: string
  estado?: EstadoProyecto
  region?: string
  busqueda?: string
  page?: number
  page_size?: number
}

// Resumen de análisis para listados
export interface AnalisisResumen {
  id: string
  proyecto_id: string
  via_ingreso: 'EIA' | 'DIA'
  confianza: number
  alertas_criticas: number
  alertas_altas: number
  created_at: string
}

// Constantes
export const REGIONES_CHILE = [
  'Arica y Parinacota',
  'Tarapacá',
  'Antofagasta',
  'Atacama',
  'Coquimbo',
  'Valparaíso',
  'Metropolitana',
  'O\'Higgins',
  'Maule',
  'Ñuble',
  'Biobío',
  'La Araucanía',
  'Los Ríos',
  'Los Lagos',
  'Aysén',
  'Magallanes',
] as const

export const TIPOS_MINERIA = ['Tajo abierto', 'Subterránea', 'Mixta'] as const

export const FASES_PROYECTO = ['Exploración', 'Explotación', 'Cierre'] as const

export const FUENTES_AGUA = ['Subterránea', 'Superficial', 'Mar', 'Desalinizada'] as const

// Comunas por región (principales regiones mineras)
export const COMUNAS_POR_REGION: Record<string, string[]> = {
  'Arica y Parinacota': ['Arica', 'Camarones', 'Putre', 'General Lagos'],
  'Tarapacá': ['Iquique', 'Alto Hospicio', 'Pozo Almonte', 'Camiña', 'Colchane', 'Huara', 'Pica'],
  'Antofagasta': ['Antofagasta', 'Mejillones', 'Sierra Gorda', 'Taltal', 'Calama', 'Ollagüe', 'San Pedro de Atacama', 'Tocopilla', 'María Elena'],
  'Atacama': ['Copiapó', 'Caldera', 'Tierra Amarilla', 'Chañaral', 'Diego de Almagro', 'Vallenar', 'Alto del Carmen', 'Freirina', 'Huasco'],
  'Coquimbo': ['La Serena', 'Coquimbo', 'Andacollo', 'La Higuera', 'Paiguano', 'Vicuña', 'Illapel', 'Canela', 'Los Vilos', 'Salamanca', 'Ovalle', 'Combarbalá', 'Monte Patria', 'Punitaqui', 'Río Hurtado'],
  'Valparaíso': ['Valparaíso', 'Viña del Mar', 'Quintero', 'Puchuncaví', 'Casablanca', 'Los Andes', 'San Esteban', 'Calle Larga', 'Rinconada', 'San Felipe', 'Putaendo', 'Santa María', 'Panquehue', 'Llaillay', 'Catemu', 'Petorca', 'Cabildo', 'Zapallar', 'Papudo', 'La Ligua'],
  'Metropolitana': ['Santiago', 'Providencia', 'Las Condes', 'Vitacura', 'Lo Barnechea', 'Colina', 'Lampa', 'Tiltil', 'Pudahuel', 'Maipú', 'Cerrillos', 'Estación Central'],
  "O'Higgins": ['Rancagua', 'Machalí', 'Graneros', 'Codegua', 'Mostazal', 'Requínoa', 'Rengo', 'Malloa', 'Quinta de Tilcoco', 'San Vicente', 'Pichidegua', 'Peumo', 'Coltauco', 'Coinco', 'Olivar', 'Doñihue', 'Las Cabras'],
  'Maule': ['Talca', 'Constitución', 'Curepto', 'Empedrado', 'Maule', 'Pelarco', 'Pencahue', 'Río Claro', 'San Clemente', 'San Rafael', 'Cauquenes', 'Chanco', 'Pelluhue', 'Curicó', 'Hualañé', 'Licantén', 'Molina', 'Rauco', 'Romeral', 'Sagrada Familia', 'Teno', 'Vichuquén', 'Linares', 'Colbún', 'Longaví', 'Parral', 'Retiro', 'San Javier', 'Villa Alegre', 'Yerbas Buenas'],
  'Ñuble': ['Chillán', 'Chillán Viejo', 'El Carmen', 'Pemuco', 'Pinto', 'Coihueco', 'San Ignacio', 'Bulnes', 'Quillón', 'San Carlos', 'Ñiquén', 'San Fabián', 'San Nicolás', 'Ninhue', 'Quirihue', 'Cobquecura', 'Treguaco', 'Portezuelo', 'Coelemu', 'Ránquil', 'Yungay'],
  'Biobío': ['Concepción', 'Talcahuano', 'Hualpén', 'Chiguayante', 'San Pedro de la Paz', 'Penco', 'Tomé', 'Coronel', 'Lota', 'Arauco', 'Curanilahue', 'Los Álamos', 'Lebu', 'Cañete', 'Contulmo', 'Tirúa', 'Los Ángeles', 'Antuco', 'Cabrero', 'Laja', 'Mulchén', 'Nacimiento', 'Negrete', 'Quilaco', 'Quilleco', 'San Rosendo', 'Santa Bárbara', 'Tucapel', 'Yumbel', 'Alto Biobío'],
  'La Araucanía': ['Temuco', 'Padre Las Casas', 'Carahue', 'Cholchol', 'Cunco', 'Curarrehue', 'Freire', 'Galvarino', 'Gorbea', 'Lautaro', 'Loncoche', 'Melipeuco', 'Nueva Imperial', 'Perquenco', 'Pitrufquén', 'Pucón', 'Saavedra', 'Teodoro Schmidt', 'Toltén', 'Vilcún', 'Villarrica', 'Angol', 'Collipulli', 'Curacautín', 'Ercilla', 'Lonquimay', 'Los Sauces', 'Lumaco', 'Purén', 'Renaico', 'Traiguén', 'Victoria'],
  'Los Ríos': ['Valdivia', 'Corral', 'Lanco', 'Los Lagos', 'Máfil', 'Mariquina', 'Paillaco', 'Panguipulli', 'La Unión', 'Futrono', 'Lago Ranco', 'Río Bueno'],
  'Los Lagos': ['Puerto Montt', 'Calbuco', 'Cochamó', 'Fresia', 'Frutillar', 'Los Muermos', 'Llanquihue', 'Maullín', 'Puerto Varas', 'Castro', 'Ancud', 'Chonchi', 'Curaco de Vélez', 'Dalcahue', 'Puqueldón', 'Queilén', 'Quellón', 'Quemchi', 'Quinchao', 'Osorno', 'Puerto Octay', 'Purranque', 'Puyehue', 'Río Negro', 'San Juan de la Costa', 'San Pablo', 'Chaitén', 'Futaleufú', 'Hualaihué', 'Palena'],
  'Aysén': ['Coyhaique', 'Lago Verde', 'Aysén', 'Cisnes', 'Guaitecas', 'Cochrane', 'O'Higgins', 'Tortel', 'Chile Chico', 'Río Ibáñez'],
  'Magallanes': ['Punta Arenas', 'Laguna Blanca', 'Río Verde', 'San Gregorio', 'Cabo de Hornos', 'Antártica', 'Porvenir', 'Primavera', 'Timaukel', 'Natales', 'Torres del Paine'],
}
```

### 3.4 Actualizar archivo: `frontend/src/types/index.ts`

```typescript
export * from './project'
export * from './analysis'
export * from './gis'
export * from './api'
export * from './cliente'    // NUEVO
export * from './documento'  // NUEVO
```

---

## 4. Servicios API

### 4.1 Crear archivo: `frontend/src/services/clientes.ts`

```typescript
/**
 * Servicio API para Clientes.
 */
import { api } from './api'
import type {
  Cliente,
  ClienteCreate,
  ClienteUpdate,
  ClienteListResponse,
  Proyecto,
} from '@/types'

const BASE_URL = '/clientes'

export const clientesService = {
  /**
   * Listar clientes con paginación y filtros.
   */
  async listar(params?: {
    busqueda?: string
    activo?: boolean
    page?: number
    page_size?: number
  }): Promise<ClienteListResponse> {
    return api.get(BASE_URL, { params })
  },

  /**
   * Obtener cliente por ID.
   */
  async obtener(id: string): Promise<Cliente> {
    return api.get(`${BASE_URL}/${id}`)
  },

  /**
   * Crear nuevo cliente.
   */
  async crear(data: ClienteCreate): Promise<Cliente> {
    return api.post(BASE_URL, data)
  },

  /**
   * Actualizar cliente.
   */
  async actualizar(id: string, data: ClienteUpdate): Promise<Cliente> {
    return api.put(`${BASE_URL}/${id}`, data)
  },

  /**
   * Eliminar (desactivar) cliente.
   */
  async eliminar(id: string): Promise<void> {
    return api.delete(`${BASE_URL}/${id}`)
  },

  /**
   * Obtener proyectos del cliente.
   */
  async obtenerProyectos(id: string): Promise<Proyecto[]> {
    return api.get(`${BASE_URL}/${id}/proyectos`)
  },
}
```

### 4.2 Crear archivo: `frontend/src/services/proyectos.ts`

```typescript
/**
 * Servicio API para Proyectos.
 */
import { api } from './api'
import type {
  Proyecto,
  ProyectoConGeometria,
  ProyectoCreate,
  ProyectoUpdate,
  ProyectoGeometriaUpdate,
  ProyectoListResponse,
  FiltrosProyecto,
  EstadoProyecto,
  AnalisisResumen,
} from '@/types'

const BASE_URL = '/proyectos'

export const proyectosService = {
  /**
   * Listar proyectos con paginación y filtros.
   */
  async listar(filtros?: FiltrosProyecto): Promise<ProyectoListResponse> {
    return api.get(BASE_URL, { params: filtros })
  },

  /**
   * Obtener proyecto por ID (con geometría).
   */
  async obtener(id: string): Promise<ProyectoConGeometria> {
    return api.get(`${BASE_URL}/${id}`)
  },

  /**
   * Crear nuevo proyecto.
   */
  async crear(data: ProyectoCreate): Promise<Proyecto> {
    return api.post(BASE_URL, data)
  },

  /**
   * Actualizar proyecto (sin geometría).
   */
  async actualizar(id: string, data: ProyectoUpdate): Promise<Proyecto> {
    return api.put(`${BASE_URL}/${id}`, data)
  },

  /**
   * Actualizar solo geometría.
   */
  async actualizarGeometria(id: string, data: ProyectoGeometriaUpdate): Promise<Proyecto> {
    return api.patch(`${BASE_URL}/${id}/geometria`, data)
  },

  /**
   * Cambiar estado del proyecto.
   */
  async cambiarEstado(id: string, nuevoEstado: EstadoProyecto, motivo?: string): Promise<void> {
    return api.patch(`${BASE_URL}/${id}/estado`, {
      nuevo_estado: nuevoEstado,
      motivo,
    })
  },

  /**
   * Archivar proyecto.
   */
  async archivar(id: string): Promise<void> {
    return api.delete(`${BASE_URL}/${id}`)
  },

  /**
   * Obtener historial de análisis.
   */
  async obtenerAnalisis(id: string): Promise<AnalisisResumen[]> {
    return api.get(`${BASE_URL}/${id}/analisis`)
  },
}
```

### 4.3 Crear archivo: `frontend/src/services/documentos.ts`

```typescript
/**
 * Servicio API para Documentos.
 */
import { api } from './api'
import type {
  Documento,
  DocumentoListResponse,
  CategoriaDocumento,
} from '@/types'

export const documentosService = {
  /**
   * Listar documentos de un proyecto.
   */
  async listar(proyectoId: string, categoria?: CategoriaDocumento): Promise<DocumentoListResponse> {
    return api.get(`/proyectos/${proyectoId}/documentos`, {
      params: categoria ? { categoria } : undefined,
    })
  },

  /**
   * Subir documento.
   */
  async subir(
    proyectoId: string,
    archivo: File,
    datos: {
      nombre: string
      categoria: CategoriaDocumento
      descripcion?: string
    }
  ): Promise<Documento> {
    const formData = new FormData()
    formData.append('archivo', archivo)
    formData.append('nombre', datos.nombre)
    formData.append('categoria', datos.categoria)
    if (datos.descripcion) {
      formData.append('descripcion', datos.descripcion)
    }

    return api.post(`/proyectos/${proyectoId}/documentos`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
  },

  /**
   * Descargar documento.
   */
  async descargar(documentoId: string, nombreArchivo: string): Promise<void> {
    const response = await api.get(`/documentos/${documentoId}/descargar`, {
      responseType: 'blob',
    })

    // Crear enlace temporal para descarga
    const url = window.URL.createObjectURL(new Blob([response]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', nombreArchivo)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  },

  /**
   * Eliminar documento.
   */
  async eliminar(documentoId: string): Promise<void> {
    return api.delete(`/documentos/${documentoId}`)
  },
}
```

### 4.4 Crear archivo: `frontend/src/services/dashboard.ts`

```typescript
/**
 * Servicio API para Dashboard.
 *
 * NOTA: Requiere crear endpoint GET /api/v1/dashboard/stats en el backend.
 */
import { api } from './api'

export interface DashboardStats {
  total_clientes: number
  total_proyectos: number
  proyectos_borrador: number
  proyectos_analizados: number
  analisis_semana: number
  total_eia: number
  total_dia: number
}

export interface AnalisisReciente {
  id: string
  proyecto_id: string
  proyecto_nombre: string
  via_ingreso: 'EIA' | 'DIA'
  confianza: number
  fecha: string
  alertas_criticas: number
}

export const dashboardService = {
  /**
   * Obtener estadísticas del dashboard.
   * Requiere endpoint: GET /api/v1/dashboard/stats
   */
  async obtenerEstadisticas(): Promise<DashboardStats> {
    return api.get('/dashboard/stats')
  },

  /**
   * Obtener análisis recientes.
   * Requiere endpoint: GET /api/v1/dashboard/analisis-recientes
   */
  async obtenerAnalisisRecientes(limite = 5): Promise<AnalisisReciente[]> {
    return api.get('/dashboard/analisis-recientes', { params: { limite } })
  },
}
```

> **IMPORTANTE**: Estos endpoints deben crearse en el backend. Ver sección de Backend Requerido al final del documento.

---

## 5. Stores Pinia

### 5.1 Crear archivo: `frontend/src/stores/clientes.ts`

```typescript
/**
 * Store Pinia para Clientes.
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { clientesService } from '@/services/clientes'
import type { Cliente, ClienteCreate, ClienteUpdate } from '@/types'

export const useClientesStore = defineStore('clientes', () => {
  // Estado
  const clientes = ref<Cliente[]>([])
  const clienteActual = ref<Cliente | null>(null)
  const cargando = ref(false)
  const error = ref<string | null>(null)
  const paginacion = ref({
    total: 0,
    page: 1,
    page_size: 20,
    pages: 0,
  })

  // Computed
  const clientesActivos = computed(() =>
    clientes.value.filter((c) => c.activo)
  )

  const tieneClientes = computed(() => clientes.value.length > 0)

  // Acciones
  async function cargarClientes(params?: {
    busqueda?: string
    page?: number
    page_size?: number
  }) {
    cargando.value = true
    error.value = null

    try {
      const response = await clientesService.listar({
        activo: true,
        ...params,
      })
      clientes.value = response.items
      paginacion.value = {
        total: response.total,
        page: response.page,
        page_size: response.page_size,
        pages: response.pages,
      }
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error al cargar clientes'
      throw e
    } finally {
      cargando.value = false
    }
  }

  async function cargarCliente(id: string) {
    cargando.value = true
    error.value = null

    try {
      clienteActual.value = await clientesService.obtener(id)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error al cargar cliente'
      throw e
    } finally {
      cargando.value = false
    }
  }

  async function crearCliente(data: ClienteCreate): Promise<Cliente> {
    cargando.value = true
    error.value = null

    try {
      const cliente = await clientesService.crear(data)
      clientes.value.unshift(cliente)
      return cliente
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error al crear cliente'
      throw e
    } finally {
      cargando.value = false
    }
  }

  async function actualizarCliente(id: string, data: ClienteUpdate): Promise<Cliente> {
    cargando.value = true
    error.value = null

    try {
      const cliente = await clientesService.actualizar(id, data)

      // Actualizar en lista (creando nuevo array para reactividad)
      const idx = clientes.value.findIndex((c) => c.id === id)
      if (idx >= 0) {
        clientes.value = [
          ...clientes.value.slice(0, idx),
          cliente,
          ...clientes.value.slice(idx + 1),
        ]
      }

      // Actualizar actual si corresponde
      if (clienteActual.value?.id === id) {
        clienteActual.value = cliente
      }

      return cliente
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error al actualizar cliente'
      throw e
    } finally {
      cargando.value = false
    }
  }

  async function eliminarCliente(id: string) {
    cargando.value = true
    error.value = null

    try {
      await clientesService.eliminar(id)

      // Quitar de lista
      clientes.value = clientes.value.filter((c) => c.id !== id)

      // Limpiar actual si corresponde
      if (clienteActual.value?.id === id) {
        clienteActual.value = null
      }
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error al eliminar cliente'
      throw e
    } finally {
      cargando.value = false
    }
  }

  function limpiarActual() {
    clienteActual.value = null
  }

  return {
    // Estado
    clientes,
    clienteActual,
    cargando,
    error,
    paginacion,
    // Computed
    clientesActivos,
    tieneClientes,
    // Acciones
    cargarClientes,
    cargarCliente,
    crearCliente,
    actualizarCliente,
    eliminarCliente,
    limpiarActual,
  }
})
```

### 5.2 Crear archivo: `frontend/src/stores/proyectos.ts`

```typescript
/**
 * Store Pinia para Proyectos (REEMPLAZA project.ts).
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { proyectosService } from '@/services/proyectos'
import type {
  Proyecto,
  ProyectoConGeometria,
  ProyectoCreate,
  ProyectoUpdate,
  ProyectoGeometriaUpdate,
  FiltrosProyecto,
  EstadoProyecto,
} from '@/types'

export const useProyectosStore = defineStore('proyectos', () => {
  // Estado
  const proyectos = ref<Proyecto[]>([])
  const proyectoActual = ref<ProyectoConGeometria | null>(null)
  const cargando = ref(false)
  const guardando = ref(false)
  const error = ref<string | null>(null)
  const filtros = ref<FiltrosProyecto>({
    page: 1,
    page_size: 20,
  })
  const paginacion = ref({
    total: 0,
    page: 1,
    page_size: 20,
    pages: 0,
  })

  // Computed
  const tieneProyectos = computed(() => proyectos.value.length > 0)

  const proyectosPorEstado = computed(() => {
    const grupos: Record<EstadoProyecto, Proyecto[]> = {
      borrador: [],
      completo: [],
      con_geometria: [],
      analizado: [],
      en_revision: [],
      aprobado: [],
      rechazado: [],
      archivado: [],
    }

    proyectos.value.forEach((p) => {
      grupos[p.estado].push(p)
    })

    return grupos
  })

  const puedeAnalizar = computed(() =>
    proyectoActual.value?.puede_analizar ?? false
  )

  const tieneGeometria = computed(() =>
    proyectoActual.value?.tiene_geometria ?? false
  )

  // Acciones
  async function cargarProyectos(nuevosFiltros?: Partial<FiltrosProyecto>) {
    if (nuevosFiltros) {
      filtros.value = { ...filtros.value, ...nuevosFiltros }
    }

    cargando.value = true
    error.value = null

    try {
      const response = await proyectosService.listar(filtros.value)
      proyectos.value = response.items
      paginacion.value = {
        total: response.total,
        page: response.page,
        page_size: response.page_size,
        pages: response.pages,
      }
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error al cargar proyectos'
      throw e
    } finally {
      cargando.value = false
    }
  }

  async function cargarProyecto(id: string) {
    cargando.value = true
    error.value = null

    try {
      proyectoActual.value = await proyectosService.obtener(id)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error al cargar proyecto'
      throw e
    } finally {
      cargando.value = false
    }
  }

  async function crearProyecto(data: ProyectoCreate): Promise<Proyecto> {
    guardando.value = true
    error.value = null

    try {
      const proyecto = await proyectosService.crear(data)
      proyectos.value.unshift(proyecto)
      return proyecto
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error al crear proyecto'
      throw e
    } finally {
      guardando.value = false
    }
  }

  async function actualizarProyecto(id: string, data: ProyectoUpdate): Promise<Proyecto> {
    guardando.value = true
    error.value = null

    try {
      const proyecto = await proyectosService.actualizar(id, data)

      // Actualizar en lista (creando nuevo array para reactividad)
      const idx = proyectos.value.findIndex((p) => p.id === id)
      if (idx >= 0) {
        proyectos.value = [
          ...proyectos.value.slice(0, idx),
          proyecto,
          ...proyectos.value.slice(idx + 1),
        ]
      }

      // Actualizar actual
      if (proyectoActual.value?.id === id) {
        proyectoActual.value = { ...proyectoActual.value, ...proyecto }
      }

      return proyecto
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error al actualizar proyecto'
      throw e
    } finally {
      guardando.value = false
    }
  }

  async function actualizarGeometria(id: string, data: ProyectoGeometriaUpdate): Promise<Proyecto> {
    guardando.value = true
    error.value = null

    try {
      const proyecto = await proyectosService.actualizarGeometria(id, data)

      // Actualizar actual
      if (proyectoActual.value?.id === id) {
        proyectoActual.value = {
          ...proyectoActual.value,
          ...proyecto,
          geometria: data.geometria,
        }
      }

      return proyecto
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error al actualizar geometría'
      throw e
    } finally {
      guardando.value = false
    }
  }

  async function cambiarEstado(id: string, nuevoEstado: EstadoProyecto, motivo?: string) {
    guardando.value = true
    error.value = null

    try {
      await proyectosService.cambiarEstado(id, nuevoEstado, motivo)

      // Actualizar en lista (creando nuevo objeto para reactividad)
      const idx = proyectos.value.findIndex((p) => p.id === id)
      if (idx >= 0) {
        proyectos.value = [
          ...proyectos.value.slice(0, idx),
          { ...proyectos.value[idx], estado: nuevoEstado },
          ...proyectos.value.slice(idx + 1),
        ]
      }

      // Actualizar actual
      if (proyectoActual.value?.id === id) {
        proyectoActual.value = { ...proyectoActual.value, estado: nuevoEstado }
      }
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error al cambiar estado'
      throw e
    } finally {
      guardando.value = false
    }
  }

  async function archivarProyecto(id: string) {
    guardando.value = true
    error.value = null

    try {
      await proyectosService.archivar(id)

      // Quitar de lista (o marcar como archivado)
      proyectos.value = proyectos.value.filter((p) => p.id !== id)

      // Limpiar actual
      if (proyectoActual.value?.id === id) {
        proyectoActual.value = null
      }
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error al archivar proyecto'
      throw e
    } finally {
      guardando.value = false
    }
  }

  function limpiarActual() {
    proyectoActual.value = null
  }

  function limpiarFiltros() {
    filtros.value = { page: 1, page_size: 20 }
  }

  return {
    // Estado
    proyectos,
    proyectoActual,
    cargando,
    guardando,
    error,
    filtros,
    paginacion,
    // Computed
    tieneProyectos,
    proyectosPorEstado,
    puedeAnalizar,
    tieneGeometria,
    // Acciones
    cargarProyectos,
    cargarProyecto,
    crearProyecto,
    actualizarProyecto,
    actualizarGeometria,
    cambiarEstado,
    archivarProyecto,
    limpiarActual,
    limpiarFiltros,
  }
})
```

---

## 6. Componentes Vue

### 6.1 Dashboard

#### `frontend/src/views/DashboardView.vue`

```vue
<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import DashboardStats from '@/components/dashboard/DashboardStats.vue'
import RecentAnalysis from '@/components/dashboard/RecentAnalysis.vue'
import QuickActions from '@/components/dashboard/QuickActions.vue'

const router = useRouter()
</script>

<template>
  <div class="p-6 max-w-7xl mx-auto">
    <h1 class="text-2xl font-bold mb-6">Dashboard</h1>

    <!-- Estadísticas -->
    <DashboardStats class="mb-8" />

    <!-- Grid principal -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Acciones rápidas -->
      <div class="lg:col-span-1">
        <QuickActions />
      </div>

      <!-- Análisis recientes -->
      <div class="lg:col-span-2">
        <RecentAnalysis />
      </div>
    </div>
  </div>
</template>
```

#### `frontend/src/components/dashboard/DashboardStats.vue`

```vue
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { dashboardService } from '@/services/dashboard'

const router = useRouter()

const stats = ref({
  clientes: 0,
  proyectos: 0,
  analisis: 0,
  cargando: true,
  error: null as string | null,
})

onMounted(async () => {
  try {
    const dashboardStats = await dashboardService.obtenerEstadisticas()
    stats.value.clientes = dashboardStats.total_clientes
    stats.value.proyectos = dashboardStats.total_proyectos
    stats.value.analisis = dashboardStats.analisis_semana
  } catch (e) {
    console.error('Error cargando stats:', e)
    stats.value.error = e instanceof Error ? e.message : 'Error al cargar estadísticas'
  } finally {
    stats.value.cargando = false
  }
})
</script>

<template>
  <!-- Error -->
  <div v-if="stats.error" class="alert alert-error mb-4">
    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
    </svg>
    <span>{{ stats.error }}</span>
  </div>

  <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
    <!-- Clientes -->
    <div
      class="card bg-base-100 shadow-sm cursor-pointer hover:shadow-md transition-shadow"
      @click="router.push('/clientes')"
    >
      <div class="card-body">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm opacity-60">Clientes</p>
            <p class="text-3xl font-bold">
              <span v-if="stats.cargando" class="loading loading-dots loading-sm"></span>
              <span v-else>{{ stats.clientes }}</span>
            </p>
          </div>
          <div class="text-4xl opacity-20">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </div>
        </div>
        <p class="text-xs opacity-60 mt-2">Ver todos →</p>
      </div>
    </div>

    <!-- Proyectos -->
    <div
      class="card bg-base-100 shadow-sm cursor-pointer hover:shadow-md transition-shadow"
      @click="router.push('/proyectos')"
    >
      <div class="card-body">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm opacity-60">Proyectos</p>
            <p class="text-3xl font-bold">
              <span v-if="stats.cargando" class="loading loading-dots loading-sm"></span>
              <span v-else>{{ stats.proyectos }}</span>
            </p>
          </div>
          <div class="text-4xl opacity-20">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
            </svg>
          </div>
        </div>
        <p class="text-xs opacity-60 mt-2">Ver todos →</p>
      </div>
    </div>

    <!-- Análisis -->
    <div
      class="card bg-base-100 shadow-sm cursor-pointer hover:shadow-md transition-shadow"
      @click="router.push('/analisis')"
    >
      <div class="card-body">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm opacity-60">Análisis</p>
            <p class="text-3xl font-bold">
              <span v-if="stats.cargando" class="loading loading-dots loading-sm"></span>
              <span v-else>{{ stats.analisis }}</span>
            </p>
          </div>
          <div class="text-4xl opacity-20">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
        </div>
        <p class="text-xs opacity-60 mt-2">Ver historial →</p>
      </div>
    </div>
  </div>
</template>
```

#### `frontend/src/components/dashboard/QuickActions.vue`

```vue
<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()
</script>

<template>
  <div class="card bg-base-100 shadow-sm">
    <div class="card-body">
      <h2 class="card-title text-lg">Acciones Rápidas</h2>
      <div class="flex flex-col gap-3 mt-4">
        <button
          class="btn btn-primary w-full"
          @click="router.push('/clientes/nuevo')"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
          Nuevo Cliente
        </button>
        <button
          class="btn btn-secondary w-full"
          @click="router.push('/proyectos/nuevo')"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
          Nuevo Proyecto
        </button>
      </div>
    </div>
  </div>
</template>
```

#### `frontend/src/components/dashboard/RecentAnalysis.vue`

```vue
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { dashboardService, type AnalisisReciente } from '@/services/dashboard'

const router = useRouter()

const analisis = ref<AnalisisReciente[]>([])
const cargando = ref(true)
const error = ref<string | null>(null)

onMounted(async () => {
  try {
    analisis.value = await dashboardService.obtenerAnalisisRecientes(5)
  } catch (e) {
    console.error('Error cargando análisis recientes:', e)
    error.value = e instanceof Error ? e.message : 'Error al cargar análisis'
  } finally {
    cargando.value = false
  }
})

function formatearFecha(fecha: string): string {
  return new Date(fecha).toLocaleDateString('es-CL', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function irAProyecto(proyectoId: string) {
  router.push(`/proyectos/${proyectoId}/analisis`)
}
</script>

<template>
  <div class="card bg-base-100 shadow-sm">
    <div class="card-body">
      <div class="flex items-center justify-between mb-4">
        <h2 class="card-title text-lg">Análisis Recientes</h2>
        <router-link to="/analisis" class="btn btn-ghost btn-sm">
          Ver todos →
        </router-link>
      </div>

      <!-- Loading -->
      <div v-if="cargando" class="flex justify-center py-8">
        <span class="loading loading-spinner loading-md"></span>
      </div>

      <!-- Error -->
      <div v-else-if="error" class="alert alert-error">
        {{ error }}
      </div>

      <!-- Lista vacía -->
      <div v-else-if="analisis.length === 0" class="text-center py-8 opacity-60">
        <p>No hay análisis recientes</p>
        <router-link to="/proyectos" class="btn btn-ghost btn-sm mt-2">
          Ir a proyectos →
        </router-link>
      </div>

      <!-- Lista de análisis -->
      <div v-else class="overflow-x-auto">
        <table class="table table-sm">
          <thead>
            <tr>
              <th>Proyecto</th>
              <th>Vía</th>
              <th>Confianza</th>
              <th>Alertas</th>
              <th>Fecha</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="item in analisis"
              :key="item.id"
              class="hover cursor-pointer"
              @click="irAProyecto(item.proyecto_id)"
            >
              <td class="font-medium">{{ item.proyecto_nombre }}</td>
              <td>
                <span
                  class="badge badge-sm"
                  :class="item.via_ingreso === 'EIA' ? 'badge-error' : 'badge-success'"
                >
                  {{ item.via_ingreso }}
                </span>
              </td>
              <td>{{ Math.round(item.confianza * 100) }}%</td>
              <td>
                <span
                  v-if="item.alertas_criticas > 0"
                  class="badge badge-error badge-sm"
                >
                  {{ item.alertas_criticas }}
                </span>
                <span v-else class="opacity-50">-</span>
              </td>
              <td class="text-xs opacity-60">{{ formatearFecha(item.fecha) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
```

### 6.2 Componente de Progreso del Proyecto

#### `frontend/src/components/proyectos/ProyectoProgreso.vue`

```vue
<script setup lang="ts">
import { computed } from 'vue'
import type { Proyecto } from '@/types'

const props = defineProps<{
  proyecto: Proyecto
}>()

const pasos = computed(() => [
  {
    nombre: 'Cliente',
    completado: !!props.proyecto.cliente_id,
    icono: 'user',
  },
  {
    nombre: 'Datos básicos',
    completado: props.proyecto.porcentaje_completado >= 50,
    icono: 'document',
  },
  {
    nombre: 'Geometría',
    completado: props.proyecto.tiene_geometria,
    icono: 'map',
    accion: props.proyecto.tiene_geometria ? null : 'Dibujar en Mapa →',
  },
  {
    nombre: 'Análisis',
    completado: props.proyecto.estado === 'analizado' || props.proyecto.total_analisis > 0,
    icono: 'chart',
    deshabilitado: !props.proyecto.puede_analizar,
  },
])
</script>

<template>
  <div class="card bg-base-100 shadow-sm">
    <div class="card-body">
      <div class="flex items-center justify-between mb-4">
        <h3 class="font-semibold">Estado del Proyecto</h3>
        <div class="badge" :class="proyecto.estado === 'borrador' ? 'badge-ghost' : 'badge-primary'">
          {{ proyecto.porcentaje_completado }}% completo
        </div>
      </div>

      <!-- Barra de progreso -->
      <progress
        class="progress progress-primary w-full mb-4"
        :value="proyecto.porcentaje_completado"
        max="100"
      ></progress>

      <!-- Lista de pasos -->
      <ul class="space-y-2">
        <li
          v-for="paso in pasos"
          :key="paso.nombre"
          class="flex items-center gap-3"
          :class="{ 'opacity-50': paso.deshabilitado }"
        >
          <!-- Icono de estado -->
          <div
            class="w-6 h-6 rounded-full flex items-center justify-center"
            :class="paso.completado ? 'bg-success text-success-content' : 'bg-base-300'"
          >
            <svg v-if="paso.completado" xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
            </svg>
            <span v-else class="w-2 h-2 rounded-full bg-base-content opacity-30"></span>
          </div>

          <!-- Nombre -->
          <span class="flex-1">{{ paso.nombre }}</span>

          <!-- Acción (si aplica) -->
          <span v-if="paso.accion" class="text-xs text-primary cursor-pointer hover:underline">
            {{ paso.accion }}
          </span>
        </li>
      </ul>
    </div>
  </div>
</template>
```

### 6.3 Componente de Alertas GIS

#### `frontend/src/components/proyectos/ProyectoAlertas.vue`

```vue
<script setup lang="ts">
import { computed } from 'vue'
import type { Proyecto } from '@/types'

const props = defineProps<{
  proyecto: Proyecto
}>()

const alertas = computed(() => {
  const items = []

  if (props.proyecto.afecta_glaciares) {
    items.push({
      tipo: 'error',
      mensaje: 'Afecta glaciares (< 5km)',
      detalle: 'Trigger EIA Art. 11 letra b)',
    })
  }

  if (props.proyecto.dist_area_protegida_km !== null && props.proyecto.dist_area_protegida_km < 10) {
    items.push({
      tipo: 'warning',
      mensaje: `Área protegida a ${props.proyecto.dist_area_protegida_km?.toFixed(1)} km`,
      detalle: 'Verificar afectación según Art. 11 letra d)',
    })
  }

  if (props.proyecto.dist_comunidad_indigena_km !== null && props.proyecto.dist_comunidad_indigena_km < 5) {
    items.push({
      tipo: 'warning',
      mensaje: `Comunidad indígena a ${props.proyecto.dist_comunidad_indigena_km?.toFixed(1)} km`,
      detalle: 'Posible consulta indígena según Convenio 169',
    })
  }

  if (props.proyecto.dist_centro_poblado_km !== null && props.proyecto.dist_centro_poblado_km < 2) {
    items.push({
      tipo: 'info',
      mensaje: `Centro poblado a ${props.proyecto.dist_centro_poblado_km?.toFixed(1)} km`,
      detalle: 'Considerar impacto en población',
    })
  }

  return items
})
</script>

<template>
  <div v-if="alertas.length > 0" class="space-y-2">
    <div
      v-for="(alerta, idx) in alertas"
      :key="idx"
      class="alert"
      :class="{
        'alert-error': alerta.tipo === 'error',
        'alert-warning': alerta.tipo === 'warning',
        'alert-info': alerta.tipo === 'info',
      }"
    >
      <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
      </svg>
      <div>
        <p class="font-medium">{{ alerta.mensaje }}</p>
        <p class="text-xs opacity-80">{{ alerta.detalle }}</p>
      </div>
    </div>
  </div>

  <div v-else class="alert alert-success">
    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
    </svg>
    <span>Sin alertas GIS detectadas</span>
  </div>
</template>
```

### 6.4 Componente de Documentos

#### `frontend/src/components/documentos/DocumentosList.vue`

```vue
<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { documentosService } from '@/services/documentos'
import DocumentoUpload from './DocumentoUpload.vue'
import DocumentoCard from './DocumentoCard.vue'
import type { Documento, DocumentoListResponse, CategoriaDocumento } from '@/types'
import { CATEGORIAS_DOCUMENTO } from '@/types'

const props = defineProps<{
  proyectoId: string
  readonly?: boolean
}>()

const emit = defineEmits<{
  (e: 'actualizado'): void
}>()

const documentos = ref<Documento[]>([])
const cargando = ref(false)
const filtroCategoria = ref<CategoriaDocumento | null>(null)
const mostrarUpload = ref(false)
const totalMb = ref(0)

const documentosFiltrados = computed(() => {
  if (!filtroCategoria.value) return documentos.value
  return documentos.value.filter((d) => d.categoria === filtroCategoria.value)
})

const documentosPorCategoria = computed(() => {
  const grupos: Record<CategoriaDocumento, Documento[]> = {
    legal: [],
    tecnico: [],
    ambiental: [],
    cartografia: [],
    otro: [],
  }

  documentos.value.forEach((d) => {
    grupos[d.categoria].push(d)
  })

  return grupos
})

async function cargarDocumentos() {
  cargando.value = true
  try {
    const response = await documentosService.listar(props.proyectoId)
    documentos.value = response.items
    totalMb.value = response.total_mb
  } catch (e) {
    console.error('Error cargando documentos:', e)
  } finally {
    cargando.value = false
  }
}

async function handleSubido(doc: Documento) {
  documentos.value.unshift(doc)
  mostrarUpload.value = false
  emit('actualizado')
}

async function handleEliminado(id: string) {
  documentos.value = documentos.value.filter((d) => d.id !== id)
  emit('actualizado')
}

onMounted(cargarDocumentos)
</script>

<template>
  <div class="space-y-4">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h3 class="font-semibold">Documentos</h3>
        <p class="text-xs opacity-60">
          {{ documentos.length }} archivos ({{ totalMb.toFixed(1) }} MB)
        </p>
      </div>
      <button
        v-if="!readonly"
        class="btn btn-primary btn-sm"
        @click="mostrarUpload = true"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        Subir
      </button>
    </div>

    <!-- Filtro por categoría -->
    <div class="tabs tabs-boxed">
      <button
        class="tab"
        :class="{ 'tab-active': !filtroCategoria }"
        @click="filtroCategoria = null"
      >
        Todos
      </button>
      <button
        v-for="cat in CATEGORIAS_DOCUMENTO"
        :key="cat.value"
        class="tab"
        :class="{ 'tab-active': filtroCategoria === cat.value }"
        @click="filtroCategoria = cat.value"
      >
        {{ cat.label }}
        <span class="badge badge-sm ml-1">{{ documentosPorCategoria[cat.value].length }}</span>
      </button>
    </div>

    <!-- Loading -->
    <div v-if="cargando" class="flex justify-center py-8">
      <span class="loading loading-spinner loading-lg"></span>
    </div>

    <!-- Lista de documentos -->
    <div v-else-if="documentosFiltrados.length > 0" class="grid gap-3">
      <DocumentoCard
        v-for="doc in documentosFiltrados"
        :key="doc.id"
        :documento="doc"
        :readonly="readonly"
        @eliminado="handleEliminado"
      />
    </div>

    <!-- Vacío -->
    <div v-else class="text-center py-8 opacity-60">
      <p>No hay documentos</p>
      <button
        v-if="!readonly"
        class="btn btn-ghost btn-sm mt-2"
        @click="mostrarUpload = true"
      >
        Subir el primero
      </button>
    </div>

    <!-- Modal Upload -->
    <dialog class="modal" :class="{ 'modal-open': mostrarUpload }">
      <div class="modal-box">
        <h3 class="font-bold text-lg mb-4">Subir Documento</h3>
        <DocumentoUpload
          :proyecto-id="proyectoId"
          @subido="handleSubido"
          @cancelar="mostrarUpload = false"
        />
      </div>
      <form method="dialog" class="modal-backdrop">
        <button @click="mostrarUpload = false">close</button>
      </form>
    </dialog>
  </div>
</template>
```

#### `frontend/src/components/documentos/DocumentoCard.vue`

```vue
<script setup lang="ts">
import { ref } from 'vue'
import { documentosService } from '@/services/documentos'
import type { Documento } from '@/types'
import { CATEGORIAS_DOCUMENTO } from '@/types'

const props = defineProps<{
  documento: Documento
  readonly?: boolean
}>()

const emit = defineEmits<{
  (e: 'eliminado', id: string): void
}>()

const descargando = ref(false)
const eliminando = ref(false)
const confirmarEliminar = ref(false)

const categoriaInfo = CATEGORIAS_DOCUMENTO.find((c) => c.value === props.documento.categoria)

function formatearTamano(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function formatearFecha(fecha: string): string {
  return new Date(fecha).toLocaleDateString('es-CL', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  })
}

async function descargar() {
  descargando.value = true
  try {
    await documentosService.descargar(props.documento.id, props.documento.nombre_original)
  } catch (e) {
    console.error('Error descargando:', e)
  } finally {
    descargando.value = false
  }
}

async function eliminar() {
  eliminando.value = true
  try {
    await documentosService.eliminar(props.documento.id)
    emit('eliminado', props.documento.id)
  } catch (e) {
    console.error('Error eliminando:', e)
  } finally {
    eliminando.value = false
    confirmarEliminar.value = false
  }
}
</script>

<template>
  <div class="card card-compact bg-base-200">
    <div class="card-body flex-row items-center gap-4">
      <!-- Icono según tipo -->
      <div class="text-2xl opacity-50">
        <span v-if="documento.mime_type.includes('pdf')">📄</span>
        <span v-else-if="documento.mime_type.includes('image')">🖼️</span>
        <span v-else-if="documento.mime_type.includes('zip')">📦</span>
        <span v-else>📎</span>
      </div>

      <!-- Info -->
      <div class="flex-1 min-w-0">
        <p class="font-medium truncate">{{ documento.nombre }}</p>
        <p class="text-xs opacity-60">
          <span class="badge badge-ghost badge-xs mr-2">{{ categoriaInfo?.label }}</span>
          {{ formatearTamano(documento.tamano_bytes) }} · {{ formatearFecha(documento.created_at) }}
        </p>
        <p v-if="documento.descripcion" class="text-xs opacity-50 truncate mt-1">
          {{ documento.descripcion }}
        </p>
      </div>

      <!-- Acciones -->
      <div class="flex gap-1">
        <button
          class="btn btn-ghost btn-sm btn-square"
          :disabled="descargando"
          title="Descargar"
          @click="descargar"
        >
          <span v-if="descargando" class="loading loading-spinner loading-xs"></span>
          <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
        </button>

        <button
          v-if="!readonly"
          class="btn btn-ghost btn-sm btn-square text-error"
          :disabled="eliminando"
          title="Eliminar"
          @click="confirmarEliminar = true"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
        </button>
      </div>
    </div>

    <!-- Modal confirmar eliminación -->
    <dialog class="modal" :class="{ 'modal-open': confirmarEliminar }">
      <div class="modal-box">
        <h3 class="font-bold text-lg">Eliminar documento</h3>
        <p class="py-4">
          ¿Estás seguro de eliminar "<strong>{{ documento.nombre }}</strong>"?
          Esta acción no se puede deshacer.
        </p>
        <div class="modal-action">
          <button class="btn btn-ghost" @click="confirmarEliminar = false">Cancelar</button>
          <button
            class="btn btn-error"
            :disabled="eliminando"
            @click="eliminar"
          >
            <span v-if="eliminando" class="loading loading-spinner loading-sm"></span>
            <span v-else>Eliminar</span>
          </button>
        </div>
      </div>
      <form method="dialog" class="modal-backdrop">
        <button @click="confirmarEliminar = false">close</button>
      </form>
    </dialog>
  </div>
</template>
```

#### `frontend/src/components/documentos/DocumentoUpload.vue`

```vue
<script setup lang="ts">
import { ref } from 'vue'
import { documentosService } from '@/services/documentos'
import type { CategoriaDocumento, Documento } from '@/types'
import { CATEGORIAS_DOCUMENTO } from '@/types'

const props = defineProps<{
  proyectoId: string
}>()

const emit = defineEmits<{
  (e: 'subido', doc: Documento): void
  (e: 'cancelar'): void
}>()

const archivo = ref<File | null>(null)
const nombre = ref('')
const categoria = ref<CategoriaDocumento>('otro')
const descripcion = ref('')
const subiendo = ref(false)
const error = ref('')

const MAX_SIZE_MB = 50

function handleFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]

  if (file) {
    if (file.size > MAX_SIZE_MB * 1024 * 1024) {
      error.value = `Archivo muy grande. Máximo ${MAX_SIZE_MB}MB`
      return
    }
    archivo.value = file
    if (!nombre.value) {
      nombre.value = file.name.replace(/\.[^/.]+$/, '')
    }
    error.value = ''
  }
}

async function subir() {
  if (!archivo.value || !nombre.value) {
    error.value = 'Selecciona un archivo y nombre'
    return
  }

  subiendo.value = true
  error.value = ''

  try {
    const doc = await documentosService.subir(props.proyectoId, archivo.value, {
      nombre: nombre.value,
      categoria: categoria.value,
      descripcion: descripcion.value || undefined,
    })
    emit('subido', doc)
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Error al subir archivo'
  } finally {
    subiendo.value = false
  }
}
</script>

<template>
  <div class="space-y-4">
    <!-- Archivo -->
    <div class="form-control">
      <label class="label">
        <span class="label-text">Archivo *</span>
      </label>
      <input
        type="file"
        class="file-input file-input-bordered w-full"
        accept=".pdf,.png,.jpg,.jpeg,.doc,.docx,.xls,.xlsx,.zip"
        @change="handleFileChange"
      />
      <label class="label">
        <span class="label-text-alt">PDF, imágenes, Office, ZIP. Máx {{ MAX_SIZE_MB }}MB</span>
      </label>
    </div>

    <!-- Nombre -->
    <div class="form-control">
      <label class="label">
        <span class="label-text">Nombre *</span>
      </label>
      <input
        v-model="nombre"
        type="text"
        class="input input-bordered w-full"
        placeholder="Nombre del documento"
      />
    </div>

    <!-- Categoría -->
    <div class="form-control">
      <label class="label">
        <span class="label-text">Categoría</span>
      </label>
      <select v-model="categoria" class="select select-bordered w-full">
        <option v-for="cat in CATEGORIAS_DOCUMENTO" :key="cat.value" :value="cat.value">
          {{ cat.label }} - {{ cat.descripcion }}
        </option>
      </select>
    </div>

    <!-- Descripción -->
    <div class="form-control">
      <label class="label">
        <span class="label-text">Descripción (opcional)</span>
      </label>
      <textarea
        v-model="descripcion"
        class="textarea textarea-bordered"
        rows="2"
        placeholder="Breve descripción..."
      ></textarea>
    </div>

    <!-- Error -->
    <div v-if="error" class="alert alert-error">
      {{ error }}
    </div>

    <!-- Botones -->
    <div class="flex justify-end gap-2">
      <button class="btn btn-ghost" @click="emit('cancelar')">Cancelar</button>
      <button
        class="btn btn-primary"
        :disabled="!archivo || !nombre || subiendo"
        @click="subir"
      >
        <span v-if="subiendo" class="loading loading-spinner loading-sm"></span>
        <span v-else>Subir</span>
      </button>
    </div>
  </div>
</template>
```

---

```
