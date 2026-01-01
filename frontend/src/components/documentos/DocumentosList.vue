<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { documentosService } from '@/services/documentos'
import { CATEGORIAS_DOCUMENTO, type Documento, type CategoriaDocumento } from '@/types'
import DocumentoCard from './DocumentoCard.vue'
import DocumentoUpload from './DocumentoUpload.vue'

const props = defineProps<{
  proyectoId: string
  readonly?: boolean
}>()

const documentos = ref<Documento[]>([])
const cargando = ref(false)
const error = ref<string | null>(null)
const subiendo = ref(false)
const mostrarFormulario = ref(false)
const filtroCategoria = ref<CategoriaDocumento | ''>('')
const documentoAEliminar = ref<Documento | null>(null)

const totalBytes = ref(0)
const totalMb = computed(() => (totalBytes.value / (1024 * 1024)).toFixed(2))

const documentosFiltrados = computed(() => {
  if (!filtroCategoria.value) return documentos.value
  return documentos.value.filter((d) => d.categoria === filtroCategoria.value)
})

async function cargarDocumentos() {
  cargando.value = true
  error.value = null
  try {
    const response = await documentosService.listar(props.proyectoId)
    documentos.value = response.items
    totalBytes.value = response.total_bytes
  } catch (e: any) {
    error.value = e.message || 'Error al cargar documentos'
  } finally {
    cargando.value = false
  }
}

async function subirDocumento(data: {
  archivo: File
  nombre: string
  categoria: CategoriaDocumento
  descripcion?: string
}) {
  subiendo.value = true
  error.value = null
  try {
    const nuevoDoc = await documentosService.subir(props.proyectoId, data.archivo, {
      nombre: data.nombre,
      categoria: data.categoria,
      descripcion: data.descripcion,
    })
    documentos.value.unshift(nuevoDoc)
    totalBytes.value += nuevoDoc.tamano_bytes
    mostrarFormulario.value = false
  } catch (e: any) {
    error.value = e.message || 'Error al subir documento'
  } finally {
    subiendo.value = false
  }
}

async function descargarDocumento(documento: Documento) {
  try {
    await documentosService.descargar(documento.id, documento.nombre_original)
  } catch (e: any) {
    error.value = e.message || 'Error al descargar documento'
  }
}

function confirmarEliminar(documento: Documento) {
  documentoAEliminar.value = documento
}

async function eliminarDocumento() {
  if (!documentoAEliminar.value) return

  try {
    await documentosService.eliminar(documentoAEliminar.value.id)
    const index = documentos.value.findIndex((d) => d.id === documentoAEliminar.value?.id)
    if (index !== -1) {
      const doc = documentos.value[index]
      if (doc) {
        totalBytes.value -= doc.tamano_bytes
      }
      documentos.value.splice(index, 1)
    }
    documentoAEliminar.value = null
  } catch (e: any) {
    error.value = e.message || 'Error al eliminar documento'
  }
}

onMounted(() => {
  cargarDocumentos()
})
</script>

<template>
  <div class="space-y-4">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h3 class="font-semibold">Documentos</h3>
        <p class="text-xs opacity-60">
          {{ documentos.length }} documentos ({{ totalMb }} MB)
        </p>
      </div>
      <button
        v-if="!readonly && !mostrarFormulario"
        class="btn btn-primary btn-sm"
        @click="mostrarFormulario = true"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        Subir
      </button>
    </div>

    <!-- Error -->
    <div v-if="error" class="alert alert-error alert-sm">
      <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
      </svg>
      <span>{{ error }}</span>
      <button class="btn btn-ghost btn-xs" @click="error = null">Cerrar</button>
    </div>

    <!-- Formulario de subida -->
    <div v-if="mostrarFormulario" class="card bg-base-200">
      <div class="card-body">
        <h4 class="font-medium mb-2">Subir nuevo documento</h4>
        <DocumentoUpload
          @subir="subirDocumento"
          @cancelar="mostrarFormulario = false"
        />
        <div v-if="subiendo" class="flex items-center gap-2 mt-2">
          <span class="loading loading-spinner loading-sm"></span>
          <span class="text-sm">Subiendo...</span>
        </div>
      </div>
    </div>

    <!-- Filtro por categoria -->
    <div v-if="documentos.length > 0" class="flex gap-2 flex-wrap">
      <button
        class="btn btn-xs"
        :class="!filtroCategoria ? 'btn-primary' : 'btn-ghost'"
        @click="filtroCategoria = ''"
      >
        Todos ({{ documentos.length }})
      </button>
      <button
        v-for="cat in CATEGORIAS_DOCUMENTO"
        :key="cat.value"
        class="btn btn-xs"
        :class="filtroCategoria === cat.value ? 'btn-primary' : 'btn-ghost'"
        @click="filtroCategoria = cat.value"
      >
        {{ cat.label }} ({{ documentos.filter((d) => d.categoria === cat.value).length }})
      </button>
    </div>

    <!-- Loading -->
    <div v-if="cargando" class="flex justify-center py-8">
      <span class="loading loading-spinner loading-md"></span>
    </div>

    <!-- Lista vacia -->
    <div v-else-if="documentos.length === 0" class="text-center py-8">
      <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 mx-auto opacity-20" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
      </svg>
      <p class="mt-2 opacity-60">Sin documentos</p>
      <button
        v-if="!readonly"
        class="btn btn-ghost btn-sm mt-2"
        @click="mostrarFormulario = true"
      >
        Subir primer documento
      </button>
    </div>

    <!-- Lista de documentos -->
    <div v-else class="space-y-2">
      <DocumentoCard
        v-for="doc in documentosFiltrados"
        :key="doc.id"
        :documento="doc"
        :readonly="readonly"
        @descargar="descargarDocumento"
        @eliminar="confirmarEliminar"
      />
    </div>

    <!-- Modal de confirmacion -->
    <dialog :class="{ 'modal modal-open': documentoAEliminar }">
      <div class="modal-box">
        <h3 class="font-bold text-lg">Eliminar documento</h3>
        <p class="py-4">
          ¿Estas seguro de eliminar
          <strong>{{ documentoAEliminar?.nombre }}</strong>?
          Esta accion no se puede deshacer.
        </p>
        <div class="modal-action">
          <button class="btn btn-ghost" @click="documentoAEliminar = null">
            Cancelar
          </button>
          <button class="btn btn-error" @click="eliminarDocumento">
            Eliminar
          </button>
        </div>
      </div>
      <form method="dialog" class="modal-backdrop">
        <button @click="documentoAEliminar = null">close</button>
      </form>
    </dialog>
  </div>
</template>
