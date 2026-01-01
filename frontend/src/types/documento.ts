/**
 * Tipos para Documento.
 */

export type CategoriaDocumento = 'legal' | 'tecnico' | 'ambiental' | 'cartografia' | 'otro'

export const CATEGORIAS_DOCUMENTO: { value: CategoriaDocumento; label: string; descripcion: string }[] = [
  { value: 'legal', label: 'Legal', descripcion: 'Permisos, contratos, escrituras' },
  { value: 'tecnico', label: 'Tecnico', descripcion: 'Estudios tecnicos, planos, informes' },
  { value: 'ambiental', label: 'Ambiental', descripcion: 'Lineas base, EIA/DIA anteriores' },
  { value: 'cartografia', label: 'Cartografia', descripcion: 'Mapas, imagenes satelitales' },
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
