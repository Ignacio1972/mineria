export interface CapaGISInfo {
  nombre: string;
  registros: number;
  url_geojson?: string;
  url_wms?: string;
  error?: string;
}

export interface CapasGISResponse {
  capas: Record<string, CapaGISInfo>;
}

export interface Feature {
  type: 'Feature';
  geometry: GeoJSON.Geometry;
  properties: Record<string, unknown>;
}

export interface FeatureCollection {
  type: 'FeatureCollection';
  name?: string;
  crs?: {
    type: string;
    properties: { name: string };
  };
  features: Feature[];
  totalFeatures?: number;
}

export interface CapaGIS {
  id: string;
  nombre: string;
  descripcion: string;
  tipo: 'vector' | 'raster';
  categoria: CategoriaCapaGIS;
  visible: boolean;
  opacidad: number;
  url?: string;
  estilo?: EstiloCapa;
  // Campos para capas WMS externas (no GeoServer local)
  wmsExterno?: {
    url: string;      // URL base del servicio WMS
    layers: string;   // Nombre de la capa en el WMS
    attribution?: string; // Atribución/créditos
  };
}

export type CategoriaCapaGIS =
  | 'areas_protegidas'
  | 'recursos_hidricos'
  | 'comunidades'
  | 'patrimonio'
  | 'limites_admin'
  | 'riesgos'
  | 'uso_suelo'
  | 'base';

export interface EstiloCapa {
  fillColor?: string;
  strokeColor?: string;
  strokeWidth?: number;
  fillOpacity?: number;
}

export interface FeatureInfo {
  id: string;
  capa: string;
  propiedades: Record<string, unknown>;
  geometria: GeoJSON.Geometry;
}

export interface EstadoMapa {
  centro: [number, number];
  zoom: number;
  capasVisibles: string[];
  modoEdicion: boolean;
  geometriaProyecto: GeoJSON.Polygon | GeoJSON.MultiPolygon | null;
}

export const CAPAS_DISPONIBLES: CapaGIS[] = [
  {
    id: 'areas_protegidas',
    nombre: 'Áreas Protegidas SNASPE',
    descripcion: 'Sistema Nacional de Áreas Silvestres Protegidas del Estado',
    tipo: 'vector',
    categoria: 'areas_protegidas',
    visible: false,
    opacidad: 0.7,
    estilo: { fillColor: '#22c55e', strokeColor: '#15803d', fillOpacity: 0.3 },
  },
  {
    id: 'glaciares',
    nombre: 'Glaciares',
    descripcion: 'Inventario nacional de glaciares',
    tipo: 'vector',
    categoria: 'recursos_hidricos',
    visible: false,
    opacidad: 0.7,
    estilo: { fillColor: '#06b6d4', strokeColor: '#0891b2', fillOpacity: 0.4 },
  },
  {
    id: 'cuerpos_agua',
    nombre: 'Cuerpos de Agua',
    descripcion: 'Ríos, lagos y humedales',
    tipo: 'vector',
    categoria: 'recursos_hidricos',
    visible: false,
    opacidad: 0.7,
    estilo: { fillColor: '#3b82f6', strokeColor: '#1d4ed8', fillOpacity: 0.3 },
  },
  {
    id: 'comunidades_indigenas',
    nombre: 'Comunidades Indígenas',
    descripcion: 'Tierras y ADI indígenas',
    tipo: 'vector',
    categoria: 'comunidades',
    visible: false,
    opacidad: 0.7,
    estilo: { fillColor: '#f59e0b', strokeColor: '#d97706', fillOpacity: 0.3 },
  },
  {
    id: 'sitios_patrimoniales',
    nombre: 'Sitios Patrimoniales',
    descripcion: 'Monumentos y sitios arqueológicos',
    tipo: 'vector',
    categoria: 'patrimonio',
    visible: false,
    opacidad: 0.7,
    estilo: { fillColor: '#8b5cf6', strokeColor: '#7c3aed', fillOpacity: 0.3 },
  },
  {
    id: 'centros_poblados',
    nombre: 'Centros Poblados',
    descripcion: 'Ciudades y poblaciones',
    tipo: 'vector',
    categoria: 'comunidades',
    visible: false,
    opacidad: 0.7,
    estilo: { fillColor: '#ef4444', strokeColor: '#dc2626', fillOpacity: 0.2 },
  },
  {
    id: 'regiones',
    nombre: 'Regiones',
    descripcion: 'División regional de Chile (16 regiones)',
    tipo: 'vector',
    categoria: 'limites_admin',
    visible: false,
    opacidad: 0.5,
    estilo: { strokeColor: '#6b7280', strokeWidth: 2 },
  },
  {
    id: 'provincias',
    nombre: 'Provincias',
    descripcion: 'División provincial de Chile (56 provincias)',
    tipo: 'vector',
    categoria: 'limites_admin',
    visible: false,
    opacidad: 0.5,
    estilo: { strokeColor: '#8b5cf6', strokeWidth: 1.5 },
  },
  {
    id: 'comunas',
    nombre: 'Comunas',
    descripcion: 'División comunal de Chile (345 comunas)',
    tipo: 'vector',
    categoria: 'limites_admin',
    visible: false,
    opacidad: 0.5,
    estilo: { strokeColor: '#9ca3af', strokeWidth: 1 },
  },
  {
    id: 'bienes_nacionales_protegidos',
    nombre: 'Bienes Nacionales Protegidos',
    descripcion: 'Terrenos fiscales con protección ambiental (MBN)',
    tipo: 'vector',
    categoria: 'areas_protegidas',
    visible: false,
    opacidad: 0.7,
    estilo: { fillColor: '#10b981', strokeColor: '#059669', fillOpacity: 0.4 },
  },
  // Capas externas (WMS de terceros)
  {
    id: 'ciren_industria_forestal',
    nombre: 'Industria Forestal (INFOR)',
    descripcion: 'Catastro de la Industria Forestal Primaria 2025 - CIREN/INFOR',
    tipo: 'vector',
    categoria: 'uso_suelo',
    visible: false,
    opacidad: 0.7,
    wmsExterno: {
      url: 'https://esri.ciren.cl/server/services/IDEMINAGRI/INDUSTRIA_FORESTAL_INFOR/MapServer/WMSServer',
      layers: '0',
      attribution: 'CIREN - INFOR',
    },
  },
];

export const CATEGORIAS_CAPA: Record<CategoriaCapaGIS, string> = {
  areas_protegidas: 'Áreas Protegidas',
  recursos_hidricos: 'Recursos Hídricos',
  comunidades: 'Comunidades y Poblados',
  patrimonio: 'Patrimonio Cultural',
  limites_admin: 'Límites Administrativos',
  riesgos: 'Riesgos Naturales',
  uso_suelo: 'Uso de Suelo',
  base: 'Mapas Base',
};
