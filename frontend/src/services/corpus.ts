/**
 * Servicio de API para gestión del corpus RAG.
 */

import { get, post, put, del, apiClient } from './api'
import type {
  Categoria,
  Tema,
  Coleccion,
  DocumentoResumen,
  DocumentoDetalle,
  DocumentoCreateData,
  DocumentoUpdateData,
  DocumentoFiltros,
  ListaDocumentosResponse,
  TiposDocumentoResponse,
  FragmentosResponse,
  ReprocesarResponse,
  RelacionResponse,
} from '@/types'

// ============================================================================
// CATEGORIAS
// ============================================================================

export async function listarCategorias(): Promise<Categoria[]> {
  return get<Categoria[]>('/categorias/')
}

export async function obtenerCategoria(id: number): Promise<Categoria> {
  return get<Categoria>(`/categorias/${id}`)
}

export async function crearCategoria(data: {
  codigo: string
  nombre: string
  descripcion?: string
  parent_id?: number
  orden?: number
}): Promise<Categoria> {
  return post<Categoria>('/categorias/', data)
}

export async function actualizarCategoria(
  id: number,
  data: Partial<{
    codigo: string
    nombre: string
    descripcion: string
    orden: number
    activo: boolean
  }>
): Promise<Categoria> {
  return put<Categoria>(`/categorias/${id}`, data)
}

export async function eliminarCategoria(id: number): Promise<void> {
  return del(`/categorias/${id}`)
}

// ============================================================================
// TEMAS
// ============================================================================

export async function listarTemas(grupo?: string): Promise<Tema[]> {
  const params = grupo ? `?grupo=${grupo}` : ''
  return get<Tema[]>(`/temas/${params}`)
}

export async function obtenerTema(id: number): Promise<Tema> {
  return get<Tema>(`/temas/${id}`)
}

export async function crearTema(data: {
  codigo: string
  nombre: string
  grupo: string
  descripcion?: string
  keywords?: string[]
  color?: string
}): Promise<Tema> {
  return post<Tema>('/temas/', data)
}

export async function actualizarTema(
  id: number,
  data: Partial<{
    codigo: string
    nombre: string
    grupo: string
    descripcion: string
    keywords: string[]
    color: string
    activo: boolean
  }>
): Promise<Tema> {
  return put<Tema>(`/temas/${id}`, data)
}

export async function eliminarTema(id: number): Promise<void> {
  return del(`/temas/${id}`)
}

// ============================================================================
// COLECCIONES
// ============================================================================

export async function listarColecciones(): Promise<Coleccion[]> {
  return get<Coleccion[]>('/colecciones/')
}

export async function obtenerColeccion(id: number): Promise<Coleccion> {
  return get<Coleccion>(`/colecciones/${id}`)
}

export async function crearColeccion(data: {
  codigo: string
  nombre: string
  descripcion?: string
  es_publica?: boolean
  color?: string
}): Promise<Coleccion> {
  return post<Coleccion>('/colecciones/', data)
}

export async function actualizarColeccion(
  id: number,
  data: Partial<{
    codigo: string
    nombre: string
    descripcion: string
    es_publica: boolean
    color: string
    orden: number
  }>
): Promise<Coleccion> {
  return put<Coleccion>(`/colecciones/${id}`, data)
}

export async function eliminarColeccion(id: number): Promise<void> {
  return del(`/colecciones/${id}`)
}

// ============================================================================
// DOCUMENTOS
// ============================================================================

export async function listarDocumentos(
  filtros?: DocumentoFiltros
): Promise<ListaDocumentosResponse> {
  const params = new URLSearchParams()

  if (filtros) {
    Object.entries(filtros).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        params.append(key, String(value))
      }
    })
  }

  const query = params.toString() ? `?${params.toString()}` : ''
  return get<ListaDocumentosResponse>(`/corpus/${query}`)
}

export async function obtenerDocumento(id: number): Promise<DocumentoDetalle> {
  return get<DocumentoDetalle>(`/corpus/${id}`)
}

export async function crearDocumento(
  data: DocumentoCreateData,
  archivo?: File,
  procesarAutomaticamente = true
): Promise<DocumentoResumen> {
  const formData = new FormData()
  formData.append('datos', JSON.stringify(data))
  formData.append('procesar_automaticamente', String(procesarAutomaticamente))

  if (archivo) {
    formData.append('archivo', archivo)
  }

  const response = await apiClient.post<DocumentoResumen>('/corpus/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return response.data
}

export async function actualizarDocumento(
  id: number,
  data: DocumentoUpdateData
): Promise<DocumentoResumen> {
  return put<DocumentoResumen>(`/corpus/${id}`, data)
}

export async function eliminarDocumento(
  id: number,
  eliminarArchivo = true
): Promise<void> {
  return del(`/corpus/${id}?eliminar_archivo=${eliminarArchivo}`)
}

export async function listarTiposDocumento(): Promise<TiposDocumentoResponse> {
  return get<TiposDocumentoResponse>('/corpus/tipos')
}

// ============================================================================
// FRAGMENTOS
// ============================================================================

export async function obtenerFragmentos(
  documentoId: number,
  limite = 100,
  offset = 0
): Promise<FragmentosResponse> {
  return get<FragmentosResponse>(
    `/corpus/${documentoId}/fragmentos?limite=${limite}&offset=${offset}`
  )
}

export async function reprocesarDocumento(
  documentoId: number,
  regenerarEmbeddings = true
): Promise<ReprocesarResponse> {
  return post<ReprocesarResponse>(
    `/corpus/${documentoId}/reprocesar?regenerar_embeddings=${regenerarEmbeddings}`
  )
}

// ============================================================================
// ARCHIVOS
// ============================================================================

export async function descargarArchivo(
  documentoId: number,
  nombreArchivo: string
): Promise<void> {
  const response = await apiClient.get(`/corpus/${documentoId}/archivo`, {
    responseType: 'blob',
  })

  const blob = new Blob([response.data])
  const link = document.createElement('a')
  link.href = window.URL.createObjectURL(blob)
  link.download = nombreArchivo
  link.click()
  window.URL.revokeObjectURL(link.href)
}

// ============================================================================
// RELACIONES
// ============================================================================

export async function crearRelacion(
  documentoOrigenId: number,
  documentoDestinoId: number,
  tipoRelacion: string,
  descripcion?: string
): Promise<RelacionResponse> {
  const params = new URLSearchParams({
    documento_destino_id: String(documentoDestinoId),
    tipo_relacion: tipoRelacion,
  })

  if (descripcion) {
    params.append('descripcion', descripcion)
  }

  return post<RelacionResponse>(`/corpus/${documentoOrigenId}/relacion?${params.toString()}`)
}

// ============================================================================
// EXPORT AGRUPADO
// ============================================================================

export const corpusService = {
  // Categorias
  categorias: {
    listar: listarCategorias,
    obtener: obtenerCategoria,
    crear: crearCategoria,
    actualizar: actualizarCategoria,
    eliminar: eliminarCategoria,
  },
  // Temas
  temas: {
    listar: listarTemas,
    obtener: obtenerTema,
    crear: crearTema,
    actualizar: actualizarTema,
    eliminar: eliminarTema,
  },
  // Colecciones
  colecciones: {
    listar: listarColecciones,
    obtener: obtenerColeccion,
    crear: crearColeccion,
    actualizar: actualizarColeccion,
    eliminar: eliminarColeccion,
  },
  // Documentos
  documentos: {
    listar: listarDocumentos,
    obtener: obtenerDocumento,
    crear: crearDocumento,
    actualizar: actualizarDocumento,
    eliminar: eliminarDocumento,
    listarTipos: listarTiposDocumento,
  },
  // Fragmentos
  fragmentos: {
    obtener: obtenerFragmentos,
    reprocesar: reprocesarDocumento,
  },
  // Archivos
  archivos: {
    descargar: descargarArchivo,
  },
  // Relaciones
  relaciones: {
    crear: crearRelacion,
  },
}
