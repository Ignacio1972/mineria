<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useCorpusStore } from '@/stores/corpus'
import CategoriaTree from './CategoriaTree.vue'
import FragmentosViewer from './FragmentosViewer.vue'
import PdfViewer from './PdfViewer.vue'
import DocumentoEditarModal from './DocumentoEditarModal.vue'
import { ESTADOS_DOCUMENTO, TIPOS_DOCUMENTO } from '@/types'
import type { DocumentoUpdateData } from '@/types'

// Props para navegación directa desde URL
const props = defineProps<{
  documentoIdInicial?: number
}>()

const router = useRouter()
const store = useCorpusStore()

// UI State
const vistaActiva = ref<'lista' | 'detalle'>('lista')
const tabActiva = ref<'info' | 'fragmentos' | 'relaciones' | 'pdf'>('info')
const mostrarFiltros = ref(false)
const mostrarFormulario = ref(false)
const mostrarEditar = ref(false)

// Formulario nuevo documento
const nuevoDocumento = ref({
  titulo: '',
  tipo: 'Ley',
  numero: '',
  categoria_id: 0,
  contenido: '',
})
const archivoSeleccionado = ref<File | null>(null)

// Computed
const documentoSeleccionado = computed(() => store.documentoActual)
const cargando = computed(() => store.cargandoDocumentos || store.cargandoDocumento)

// Watch para cambiar vista
watch(
  () => store.documentoActual,
  (doc) => {
    if (doc) {
      vistaActiva.value = 'detalle'
    }
  }
)

// Handlers
function seleccionarCategoria(id: number | null) {
  store.aplicarFiltro({ categoria_id: id ?? undefined })
}

function seleccionarDocumento(id: number) {
  store.seleccionarDocumento(id)
  // Actualizar URL para compartir enlace directo
  router.replace({ query: { doc: id.toString() } })
}

function volverALista() {
  vistaActiva.value = 'lista'
  store.limpiarDocumentoActual()
  // Limpiar query param de la URL
  router.replace({ query: {} })
}

function cambiarPagina(pagina: number) {
  store.irAPagina(pagina)
}

async function crearDocumento() {
  if (!nuevoDocumento.value.titulo || !nuevoDocumento.value.categoria_id) return

  const resultado = await store.crearNuevoDocumento(
    {
      titulo: nuevoDocumento.value.titulo,
      tipo: nuevoDocumento.value.tipo,
      numero: nuevoDocumento.value.numero || undefined,
      categoria_id: nuevoDocumento.value.categoria_id,
      contenido: nuevoDocumento.value.contenido || undefined,
    },
    archivoSeleccionado.value ?? undefined
  )

  if (resultado) {
    mostrarFormulario.value = false
    nuevoDocumento.value = { titulo: '', tipo: 'Ley', numero: '', categoria_id: 0, contenido: '' }
    archivoSeleccionado.value = null
  }
}

async function eliminarDocumento() {
  if (!confirm('¿Eliminar este documento? Esta accion no se puede deshacer.')) return
  const exito = await store.eliminarDocumentoActual()
  if (exito) volverALista()
}

function onFileChange(event: Event) {
  const target = event.target as HTMLInputElement
  if (target.files && target.files[0]) {
    archivoSeleccionado.value = target.files[0]
  }
}

function getEstadoBadgeClass(estado: string): string {
  const config = ESTADOS_DOCUMENTO.find((e) => e.value === estado)
  return config ? `badge-${config.color}` : 'badge-neutral'
}

// Edición de documento
async function guardarEdicion(data: DocumentoUpdateData) {
  const exito = await store.actualizarDocumentoActual(data)
  if (exito) {
    mostrarEditar.value = false
  }
}

// Inicializar
onMounted(async () => {
  await store.inicializar()

  // Si hay documento inicial (navegación directa), cargarlo
  if (props.documentoIdInicial) {
    store.seleccionarDocumento(props.documentoIdInicial)
  }
})
</script>

<template>
  <div class="corpus-manager h-full flex flex-col">
    <!-- Header -->
    <div class="navbar bg-base-200 px-4 gap-2">
      <div class="flex-1">
        <h2 class="text-lg font-bold">Corpus Legal RAG</h2>
        <span class="badge badge-ghost ml-2">{{ store.totalDocumentos }} documentos</span>
      </div>

      <div class="flex items-center gap-2">
        <!-- Busqueda -->
        <input
          type="text"
          placeholder="Buscar por titulo..."
          class="input input-bordered input-sm w-64"
          :value="store.filtrosActivos.q"
          @input="store.aplicarFiltro({ q: ($event.target as HTMLInputElement).value })"
        />

        <!-- Toggle filtros -->
        <button
          class="btn btn-ghost btn-sm"
          :class="mostrarFiltros ? 'btn-active' : ''"
          @click="mostrarFiltros = !mostrarFiltros"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
          </svg>
          Filtros
        </button>

        <!-- Boton nuevo documento -->
        <button class="btn btn-primary btn-sm" @click="mostrarFormulario = true">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
          Nuevo
        </button>
      </div>
    </div>

    <!-- Error global -->
    <div v-if="store.error" class="alert alert-error mx-4 mt-2">
      <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
      </svg>
      <span>{{ store.error }}</span>
      <button class="btn btn-ghost btn-sm" @click="store.limpiarError()">Cerrar</button>
    </div>

    <!-- Contenido principal -->
    <div class="flex-1 flex overflow-hidden">
      <!-- Sidebar: Categorias -->
      <aside class="w-64 border-r border-base-300 p-4 overflow-y-auto bg-base-100">
        <h3 class="font-semibold mb-3 flex items-center gap-2">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
          </svg>
          Categorias
        </h3>

        <div v-if="store.cargandoCategorias" class="flex justify-center py-4">
          <span class="loading loading-spinner loading-sm"></span>
        </div>

        <CategoriaTree
          v-else
          :categorias="store.categoriasArbol"
          :seleccionada="store.filtrosActivos.categoria_id"
          @seleccionar="seleccionarCategoria"
        />
      </aside>

      <!-- Panel principal -->
      <main class="flex-1 flex flex-col overflow-hidden">
        <!-- Filtros expandidos -->
        <div v-if="mostrarFiltros" class="p-4 bg-base-200 border-b border-base-300">
          <div class="flex flex-wrap gap-4">
            <!-- Tipo -->
            <div class="form-control">
              <label class="label label-text text-xs">Tipo</label>
              <select
                class="select select-bordered select-sm"
                :value="store.filtrosActivos.tipo"
                @change="store.aplicarFiltro({ tipo: ($event.target as HTMLSelectElement).value || undefined })"
              >
                <option value="">Todos</option>
                <option v-for="tipo in TIPOS_DOCUMENTO" :key="tipo.value" :value="tipo.value">
                  {{ tipo.label }}
                </option>
              </select>
            </div>

            <!-- Estado -->
            <div class="form-control">
              <label class="label label-text text-xs">Estado</label>
              <select
                class="select select-bordered select-sm"
                :value="store.filtrosActivos.estado"
                @change="store.aplicarFiltro({ estado: ($event.target as HTMLSelectElement).value as any || undefined })"
              >
                <option value="">Todos</option>
                <option v-for="estado in ESTADOS_DOCUMENTO" :key="estado.value" :value="estado.value">
                  {{ estado.label }}
                </option>
              </select>
            </div>

            <!-- Ordenamiento -->
            <div class="form-control">
              <label class="label label-text text-xs">Ordenar por</label>
              <select
                class="select select-bordered select-sm"
                :value="store.filtrosActivos.orden"
                @change="store.aplicarFiltro({ orden: ($event.target as HTMLSelectElement).value as any })"
              >
                <option value="fecha_desc">Mas recientes</option>
                <option value="fecha_asc">Mas antiguos</option>
                <option value="titulo_asc">Titulo A-Z</option>
                <option value="titulo_desc">Titulo Z-A</option>
              </select>
            </div>

            <!-- Limpiar -->
            <div class="form-control justify-end">
              <button class="btn btn-ghost btn-sm" @click="store.limpiarFiltros()">
                Limpiar filtros
              </button>
            </div>
          </div>
        </div>

        <!-- Vista Lista -->
        <div v-if="vistaActiva === 'lista'" class="flex-1 overflow-y-auto p-4">
          <!-- Loading -->
          <div v-if="cargando" class="flex justify-center py-12">
            <span class="loading loading-spinner loading-lg"></span>
          </div>

          <!-- Lista de documentos -->
          <div v-else-if="store.documentos.length > 0" class="space-y-2">
            <div
              v-for="doc in store.documentos"
              :key="doc.id"
              class="card bg-base-100 shadow-sm hover:shadow-md transition-shadow cursor-pointer"
              @click="seleccionarDocumento(doc.id)"
            >
              <div class="card-body p-4">
                <div class="flex items-start gap-3">
                  <!-- Icono tipo -->
                  <div class="avatar placeholder">
                    <div class="bg-base-300 text-base-content rounded-lg w-10 h-10">
                      <span class="text-xs font-bold">{{ doc.tipo.substring(0, 2).toUpperCase() }}</span>
                    </div>
                  </div>

                  <!-- Info -->
                  <div class="flex-1 min-w-0">
                    <h4 class="font-medium truncate">{{ doc.titulo }}</h4>
                    <div class="flex items-center gap-2 mt-1 text-xs opacity-60">
                      <span>{{ doc.tipo }}</span>
                      <span v-if="doc.numero">| {{ doc.numero }}</span>
                      <span v-if="doc.fecha_publicacion">| {{ doc.fecha_publicacion }}</span>
                    </div>
                  </div>

                  <!-- Badges -->
                  <div class="flex items-center gap-2">
                    <span :class="['badge badge-sm', getEstadoBadgeClass(doc.estado)]">
                      {{ doc.estado }}
                    </span>
                    <span v-if="doc.tiene_archivo" class="badge badge-sm badge-outline">
                      PDF
                    </span>
                    <span class="badge badge-sm badge-ghost">
                      {{ doc.fragmentos_count }} frag.
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Paginacion -->
            <div v-if="store.totalPaginas > 1" class="flex justify-center pt-4">
              <div class="join">
                <button
                  class="join-item btn btn-sm"
                  :disabled="store.paginaActual <= 1"
                  @click="cambiarPagina(store.paginaActual - 1)"
                >
                  Anterior
                </button>
                <button class="join-item btn btn-sm btn-disabled">
                  Pagina {{ store.paginaActual }} de {{ store.totalPaginas }}
                </button>
                <button
                  class="join-item btn btn-sm"
                  :disabled="store.paginaActual >= store.totalPaginas"
                  @click="cambiarPagina(store.paginaActual + 1)"
                >
                  Siguiente
                </button>
              </div>
            </div>
          </div>

          <!-- Estado vacio -->
          <div v-else class="text-center py-12">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-16 w-16 mx-auto opacity-20" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <p class="mt-4 text-lg opacity-60">Sin documentos</p>
            <p class="text-sm opacity-40">Agrega documentos al corpus para comenzar</p>
            <button class="btn btn-primary mt-4" @click="mostrarFormulario = true">
              Agregar documento
            </button>
          </div>
        </div>

        <!-- Vista Detalle -->
        <div v-else-if="vistaActiva === 'detalle' && documentoSeleccionado" class="flex-1 overflow-y-auto">
          <!-- Header detalle -->
          <div class="p-4 bg-base-200 border-b border-base-300">
            <div class="flex items-start gap-4">
              <button class="btn btn-ghost btn-sm" @click="volverALista">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                </svg>
                Volver
              </button>

              <div class="flex-1">
                <h2 class="text-xl font-bold">{{ documentoSeleccionado.titulo }}</h2>
                <div class="flex items-center gap-2 mt-1">
                  <span :class="['badge', getEstadoBadgeClass(documentoSeleccionado.estado)]">
                    {{ documentoSeleccionado.estado }}
                  </span>
                  <span class="badge badge-outline">{{ documentoSeleccionado.tipo }}</span>
                  <span v-if="documentoSeleccionado.numero" class="text-sm opacity-60">
                    {{ documentoSeleccionado.numero }}
                  </span>
                </div>
              </div>

              <!-- Acciones -->
              <div class="flex gap-2">
                <button
                  class="btn btn-ghost btn-sm"
                  @click="mostrarEditar = true"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                  Editar
                </button>
                <button
                  v-if="documentoSeleccionado.tiene_archivo"
                  class="btn btn-ghost btn-sm"
                  @click="store.descargarArchivoDocumento()"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                  Descargar
                </button>
                <button class="btn btn-error btn-sm" @click="eliminarDocumento">
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </div>
            </div>
          </div>

          <!-- Tabs -->
          <div class="tabs tabs-bordered px-4 pt-2">
            <button
              class="tab"
              :class="tabActiva === 'info' ? 'tab-active' : ''"
              @click="tabActiva = 'info'"
            >
              Informacion
            </button>
            <button
              v-if="documentoSeleccionado.tiene_archivo"
              class="tab"
              :class="tabActiva === 'pdf' ? 'tab-active' : ''"
              @click="tabActiva = 'pdf'"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
              </svg>
              PDF
            </button>
            <button
              class="tab"
              :class="tabActiva === 'fragmentos' ? 'tab-active' : ''"
              @click="tabActiva = 'fragmentos'"
            >
              Fragmentos ({{ documentoSeleccionado.fragmentos_count }})
            </button>
            <button
              class="tab"
              :class="tabActiva === 'relaciones' ? 'tab-active' : ''"
              @click="tabActiva = 'relaciones'"
            >
              Relaciones
            </button>
          </div>

          <!-- Tab content -->
          <div class="p-4 flex-1 overflow-hidden">
            <!-- Tab PDF -->
            <div v-if="tabActiva === 'pdf' && documentoSeleccionado.tiene_archivo" class="h-full min-h-[500px]">
              <PdfViewer
                :documento-id="documentoSeleccionado.id"
                :nombre-archivo="documentoSeleccionado.archivo_nombre || 'documento.pdf'"
                :tipo-archivo="documentoSeleccionado.archivo_tipo || undefined"
                @cerrar="tabActiva = 'info'"
                @descargar="store.descargarArchivoDocumento()"
              />
            </div>

            <!-- Tab Info -->
            <div v-else-if="tabActiva === 'info'" class="space-y-4">
              <!-- Metadatos -->
              <div class="grid grid-cols-2 gap-4">
                <div v-if="documentoSeleccionado.categoria_nombre" class="form-control">
                  <label class="label label-text text-xs opacity-60">Categoria</label>
                  <p class="font-medium">{{ documentoSeleccionado.categoria_nombre }}</p>
                </div>
                <div v-if="documentoSeleccionado.organismo" class="form-control">
                  <label class="label label-text text-xs opacity-60">Organismo</label>
                  <p class="font-medium">{{ documentoSeleccionado.organismo }}</p>
                </div>
                <div v-if="documentoSeleccionado.fecha_publicacion" class="form-control">
                  <label class="label label-text text-xs opacity-60">Fecha publicacion</label>
                  <p class="font-medium">{{ documentoSeleccionado.fecha_publicacion }}</p>
                </div>
                <div v-if="documentoSeleccionado.fecha_vigencia" class="form-control">
                  <label class="label label-text text-xs opacity-60">Fecha vigencia</label>
                  <p class="font-medium">{{ documentoSeleccionado.fecha_vigencia }}</p>
                </div>
              </div>

              <!-- Resumen -->
              <div v-if="documentoSeleccionado.resumen" class="form-control">
                <label class="label label-text text-xs opacity-60">Resumen</label>
                <p class="text-sm">{{ documentoSeleccionado.resumen }}</p>
              </div>

              <!-- Archivo -->
              <div v-if="documentoSeleccionado.tiene_archivo" class="card bg-base-200">
                <div class="card-body p-4">
                  <h4 class="font-medium text-sm">Archivo original</h4>
                  <div class="flex items-center gap-4 text-sm">
                    <span>{{ documentoSeleccionado.archivo_nombre }}</span>
                    <span class="opacity-60">{{ documentoSeleccionado.archivo_tipo }}</span>
                    <span class="opacity-60">{{ documentoSeleccionado.archivo_tamano_mb }} MB</span>
                  </div>
                </div>
              </div>

              <!-- Temas/Componentes -->
              <div v-if="documentoSeleccionado.componentes_ambientales?.length" class="form-control">
                <label class="label label-text text-xs opacity-60">Componentes ambientales</label>
                <div class="flex flex-wrap gap-1">
                  <span
                    v-for="comp in documentoSeleccionado.componentes_ambientales"
                    :key="comp"
                    class="badge badge-info badge-outline"
                  >
                    {{ comp }}
                  </span>
                </div>
              </div>

              <div v-if="documentoSeleccionado.triggers_art11?.length" class="form-control">
                <label class="label label-text text-xs opacity-60">Triggers Art. 11</label>
                <div class="flex flex-wrap gap-1">
                  <span
                    v-for="trigger in documentoSeleccionado.triggers_art11"
                    :key="trigger"
                    class="badge badge-error badge-outline"
                  >
                    Letra {{ trigger }}
                  </span>
                </div>
              </div>

              <!-- Colecciones -->
              <div v-if="documentoSeleccionado.colecciones?.length" class="form-control">
                <label class="label label-text text-xs opacity-60">Colecciones</label>
                <div class="flex flex-wrap gap-1">
                  <span
                    v-for="col in documentoSeleccionado.colecciones"
                    :key="col.id"
                    class="badge badge-outline"
                  >
                    {{ col.nombre }}
                  </span>
                </div>
              </div>
            </div>

            <!-- Tab Fragmentos -->
            <div v-else-if="tabActiva === 'fragmentos'">
              <FragmentosViewer
                :fragmentos="store.fragmentos"
                :total="store.totalFragmentos"
                :cargando="store.cargandoFragmentos"
                :documento-titulo="documentoSeleccionado.titulo"
                @cargar-mas="store.cargarFragmentosDocumento(100, store.fragmentos.length)"
                @reprocesar="store.reprocesarDocumentoActual()"
              />
            </div>

            <!-- Tab Relaciones -->
            <div v-else-if="tabActiva === 'relaciones'">
              <div v-if="documentoSeleccionado.documentos_relacionados?.length" class="space-y-2">
                <div
                  v-for="rel in documentoSeleccionado.documentos_relacionados"
                  :key="rel.id"
                  class="card bg-base-200"
                >
                  <div class="card-body p-3 flex-row items-center gap-3">
                    <span class="badge badge-sm">{{ rel.relacion }}</span>
                    <span class="flex-1 truncate">{{ rel.titulo }}</span>
                    <button class="btn btn-ghost btn-xs" @click="seleccionarDocumento(rel.id)">
                      Ver
                    </button>
                  </div>
                </div>
              </div>
              <div v-else class="text-center py-8 opacity-50">
                Sin documentos relacionados
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>

    <!-- Modal nuevo documento -->
    <dialog :class="{ 'modal modal-open': mostrarFormulario }">
      <div class="modal-box max-w-2xl">
        <h3 class="font-bold text-lg mb-4">Nuevo documento</h3>

        <form @submit.prevent="crearDocumento" class="space-y-4">
          <!-- Titulo -->
          <div class="form-control">
            <label class="label">
              <span class="label-text">Titulo *</span>
            </label>
            <input
              v-model="nuevoDocumento.titulo"
              type="text"
              class="input input-bordered"
              placeholder="Titulo del documento"
              required
            />
          </div>

          <!-- Tipo y Numero -->
          <div class="grid grid-cols-2 gap-4">
            <div class="form-control">
              <label class="label">
                <span class="label-text">Tipo *</span>
              </label>
              <select v-model="nuevoDocumento.tipo" class="select select-bordered" required>
                <option v-for="tipo in TIPOS_DOCUMENTO" :key="tipo.value" :value="tipo.value">
                  {{ tipo.label }}
                </option>
              </select>
            </div>

            <div class="form-control">
              <label class="label">
                <span class="label-text">Numero</span>
              </label>
              <input
                v-model="nuevoDocumento.numero"
                type="text"
                class="input input-bordered"
                placeholder="Ej: 19.300"
              />
            </div>
          </div>

          <!-- Categoria -->
          <div class="form-control">
            <label class="label">
              <span class="label-text">Categoria *</span>
            </label>
            <select v-model="nuevoDocumento.categoria_id" class="select select-bordered" required>
              <option :value="0" disabled>Seleccionar categoria</option>
              <option v-for="cat in store.categorias" :key="cat.id" :value="cat.id">
                {{ cat.nombre }}
              </option>
            </select>
          </div>

          <!-- Archivo o contenido -->
          <div class="form-control">
            <label class="label">
              <span class="label-text">Archivo PDF/DOCX</span>
            </label>
            <input
              type="file"
              class="file-input file-input-bordered"
              accept=".pdf,.docx"
              @change="onFileChange"
            />
          </div>

          <div class="form-control">
            <label class="label">
              <span class="label-text">O contenido de texto</span>
            </label>
            <textarea
              v-model="nuevoDocumento.contenido"
              class="textarea textarea-bordered h-32"
              placeholder="Pegar contenido del documento..."
            ></textarea>
          </div>

          <!-- Acciones -->
          <div class="modal-action">
            <button type="button" class="btn btn-ghost" @click="mostrarFormulario = false">
              Cancelar
            </button>
            <button
              type="submit"
              class="btn btn-primary"
              :disabled="store.procesando || !nuevoDocumento.titulo || !nuevoDocumento.categoria_id"
            >
              <span v-if="store.procesando" class="loading loading-spinner loading-sm"></span>
              Crear documento
            </button>
          </div>
        </form>
      </div>
      <form method="dialog" class="modal-backdrop">
        <button @click="mostrarFormulario = false">close</button>
      </form>
    </dialog>

    <!-- Modal editar documento -->
    <DocumentoEditarModal
      :documento="mostrarEditar ? documentoSeleccionado : null"
      :categorias="store.categorias"
      :procesando="store.procesando"
      @guardar="guardarEdicion"
      @cerrar="mostrarEditar = false"
    />
  </div>
</template>

<style scoped>
.corpus-manager {
  min-height: 0;
}
</style>
