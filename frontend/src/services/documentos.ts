/**
 * Servicio API para Documentos.
 */
import { get, del, apiClient } from './api'
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
    return get(`/proyectos/${proyectoId}/documentos`, {
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

    const response = await apiClient.post(`/proyectos/${proyectoId}/documentos`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  /**
   * Descargar documento.
   */
  async descargar(documentoId: string, nombreArchivo: string): Promise<void> {
    const response = await apiClient.get(`/documentos/${documentoId}/descargar`, {
      responseType: 'blob',
    })

    // Crear enlace temporal para descarga
    const url = window.URL.createObjectURL(new Blob([response.data]))
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
    return del(`/documentos/${documentoId}`)
  },
}
