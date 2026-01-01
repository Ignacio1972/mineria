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
