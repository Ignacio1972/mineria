/**
 * Tipos para Proyecto (ACTUALIZADO para API REST).
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
  { value: 'completo', label: 'Completo', color: 'badge-info', descripcion: 'Datos listos, falta geometria' },
  { value: 'con_geometria', label: 'Con Geometria', color: 'badge-primary', descripcion: 'Listo para analisis' },
  { value: 'analizado', label: 'Analizado', color: 'badge-success', descripcion: 'Analisis ejecutado' },
  { value: 'en_revision', label: 'En Revision', color: 'badge-warning', descripcion: 'Revision por especialista' },
  { value: 'aprobado', label: 'Aprobado', color: 'badge-success', descripcion: 'Listo para ingreso SEIA' },
  { value: 'rechazado', label: 'Rechazado', color: 'badge-error', descripcion: 'Requiere correcciones' },
  { value: 'archivado', label: 'Archivado', color: 'badge-neutral', descripcion: 'Inactivo' },
]

// Geometria GeoJSON
export interface GeometriaGeoJSON {
  type: 'Polygon' | 'MultiPolygon'
  coordinates: number[][][] | number[][][][]
}

// Datos del proyecto
export interface DatosProyecto {
  nombre: string
  cliente_id?: string | null
  tipo_mineria?: 'Tajo abierto' | 'Subterranea' | 'Mixta' | null
  mineral_principal?: string | null
  fase?: 'Exploracion' | 'Explotacion' | 'Cierre' | null
  titular?: string | null
  region?: string | null
  comuna?: string | null
  superficie_ha?: number | null
  vida_util_anos?: number | null
  uso_agua_lps?: number | null
  fuente_agua?: 'Subterranea' | 'Superficial' | 'Mar' | 'Desalinizada' | null
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

// Proyecto con geometria
export interface ProyectoConGeometria extends Proyecto {
  geometria: GeometriaGeoJSON | null
}

// Para crear proyecto
export interface ProyectoCreate extends DatosProyecto {
  geometria?: GeometriaGeoJSON | null
}

// Para actualizar proyecto
export type ProyectoUpdate = Partial<DatosProyecto>

// Para actualizar geometria
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

// Resumen de analisis para listados
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
  'Tarapaca',
  'Antofagasta',
  'Atacama',
  'Coquimbo',
  'Valparaiso',
  'Metropolitana',
  "O'Higgins",
  'Maule',
  'Nuble',
  'Biobio',
  'La Araucania',
  'Los Rios',
  'Los Lagos',
  'Aysen',
  'Magallanes',
] as const

export const TIPOS_MINERIA = ['Tajo abierto', 'Subterranea', 'Mixta'] as const

export const FASES_PROYECTO = ['Exploracion', 'Explotacion', 'Cierre'] as const

export const FUENTES_AGUA = ['Subterranea', 'Superficial', 'Mar', 'Desalinizada'] as const

// Comunas por region (principales regiones mineras)
// Coordenadas centrales de cada region [longitud, latitud]
export const COORDENADAS_REGIONES: Record<string, [number, number]> = {
  'Arica y Parinacota': [-69.65, -18.48],
  'Tarapaca': [-69.65, -20.21],
  'Antofagasta': [-70.4, -23.65],
  'Atacama': [-70.05, -27.37],
  'Coquimbo': [-71.25, -29.95],
  'Valparaiso': [-71.25, -33.05],
  'Metropolitana': [-70.65, -33.45],
  "O'Higgins": [-70.75, -34.17],
  'Maule': [-71.25, -35.43],
  'Nuble': [-72.1, -36.61],
  'Biobio': [-72.35, -37.47],
  'La Araucania': [-72.6, -38.74],
  'Los Rios': [-72.6, -39.81],
  'Los Lagos': [-72.9, -41.47],
  'Aysen': [-72.07, -45.57],
  'Magallanes': [-70.91, -53.16],
}

export const COMUNAS_POR_REGION: Record<string, string[]> = {
  'Arica y Parinacota': ['Arica', 'Camarones', 'Putre', 'General Lagos'],
  'Tarapaca': ['Iquique', 'Alto Hospicio', 'Pozo Almonte', 'Camina', 'Colchane', 'Huara', 'Pica'],
  'Antofagasta': ['Antofagasta', 'Mejillones', 'Sierra Gorda', 'Taltal', 'Calama', 'Ollague', 'San Pedro de Atacama', 'Tocopilla', 'Maria Elena'],
  'Atacama': ['Copiapo', 'Caldera', 'Tierra Amarilla', 'Chanaral', 'Diego de Almagro', 'Vallenar', 'Alto del Carmen', 'Freirina', 'Huasco'],
  'Coquimbo': ['La Serena', 'Coquimbo', 'Andacollo', 'La Higuera', 'Paiguano', 'Vicuna', 'Illapel', 'Canela', 'Los Vilos', 'Salamanca', 'Ovalle', 'Combarbala', 'Monte Patria', 'Punitaqui', 'Rio Hurtado'],
  'Valparaiso': ['Valparaiso', 'Vina del Mar', 'Quintero', 'Puchuncavi', 'Casablanca', 'Los Andes', 'San Esteban', 'Calle Larga', 'Rinconada', 'San Felipe', 'Putaendo', 'Santa Maria', 'Panquehue', 'Llaillay', 'Catemu', 'Petorca', 'Cabildo', 'Zapallar', 'Papudo', 'La Ligua'],
  'Metropolitana': ['Santiago', 'Providencia', 'Las Condes', 'Vitacura', 'Lo Barnechea', 'Colina', 'Lampa', 'Tiltil', 'Pudahuel', 'Maipu', 'Cerrillos', 'Estacion Central'],
  "O'Higgins": ['Rancagua', 'Machali', 'Graneros', 'Codegua', 'Mostazal', 'Requinoa', 'Rengo', 'Malloa', 'Quinta de Tilcoco', 'San Vicente', 'Pichidegua', 'Peumo', 'Coltauco', 'Coinco', 'Olivar', 'Donihue', 'Las Cabras'],
  'Maule': ['Talca', 'Constitucion', 'Curepto', 'Empedrado', 'Maule', 'Pelarco', 'Pencahue', 'Rio Claro', 'San Clemente', 'San Rafael', 'Cauquenes', 'Chanco', 'Pelluhue', 'Curico', 'Hualane', 'Licanten', 'Molina', 'Rauco', 'Romeral', 'Sagrada Familia', 'Teno', 'Vichuquen', 'Linares', 'Colbun', 'Longavi', 'Parral', 'Retiro', 'San Javier', 'Villa Alegre', 'Yerbas Buenas'],
  'Nuble': ['Chillan', 'Chillan Viejo', 'El Carmen', 'Pemuco', 'Pinto', 'Coihueco', 'San Ignacio', 'Bulnes', 'Quillon', 'San Carlos', 'Niquen', 'San Fabian', 'San Nicolas', 'Ninhue', 'Quirihue', 'Cobquecura', 'Treguaco', 'Portezuelo', 'Coelemu', 'Ranquil', 'Yungay'],
  'Biobio': ['Concepcion', 'Talcahuano', 'Hualpen', 'Chiguayante', 'San Pedro de la Paz', 'Penco', 'Tome', 'Coronel', 'Lota', 'Arauco', 'Curanilahue', 'Los Alamos', 'Lebu', 'Canete', 'Contulmo', 'Tirua', 'Los Angeles', 'Antuco', 'Cabrero', 'Laja', 'Mulchen', 'Nacimiento', 'Negrete', 'Quilaco', 'Quilleco', 'San Rosendo', 'Santa Barbara', 'Tucapel', 'Yumbel', 'Alto Biobio'],
  'La Araucania': ['Temuco', 'Padre Las Casas', 'Carahue', 'Cholchol', 'Cunco', 'Curarrehue', 'Freire', 'Galvarino', 'Gorbea', 'Lautaro', 'Loncoche', 'Melipeuco', 'Nueva Imperial', 'Perquenco', 'Pitrufquen', 'Pucon', 'Saavedra', 'Teodoro Schmidt', 'Tolten', 'Vilcun', 'Villarrica', 'Angol', 'Collipulli', 'Curacautin', 'Ercilla', 'Lonquimay', 'Los Sauces', 'Lumaco', 'Puren', 'Renaico', 'Traiguen', 'Victoria'],
  'Los Rios': ['Valdivia', 'Corral', 'Lanco', 'Los Lagos', 'Mafil', 'Mariquina', 'Paillaco', 'Panguipulli', 'La Union', 'Futrono', 'Lago Ranco', 'Rio Bueno'],
  'Los Lagos': ['Puerto Montt', 'Calbuco', 'Cochamo', 'Fresia', 'Frutillar', 'Los Muermos', 'Llanquihue', 'Maullin', 'Puerto Varas', 'Castro', 'Ancud', 'Chonchi', 'Curaco de Velez', 'Dalcahue', 'Puqueldon', 'Queilen', 'Quellon', 'Quemchi', 'Quinchao', 'Osorno', 'Puerto Octay', 'Purranque', 'Puyehue', 'Rio Negro', 'San Juan de la Costa', 'San Pablo', 'Chaiten', 'Futaleufu', 'Hualaiue', 'Palena'],
  'Aysen': ['Coyhaique', 'Lago Verde', 'Aysen', 'Cisnes', 'Guaitecas', 'Cochrane', "O'Higgins", 'Tortel', 'Chile Chico', 'Rio Ibanez'],
  'Magallanes': ['Punta Arenas', 'Laguna Blanca', 'Rio Verde', 'San Gregorio', 'Cabo de Hornos', 'Antartica', 'Porvenir', 'Primavera', 'Timaukel', 'Natales', 'Torres del Paine'],
}
