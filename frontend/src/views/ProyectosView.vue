<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useProyectosStore } from '@/stores/proyectos'
import { useClientesStore } from '@/stores/clientes'
import { useDebounceFn } from '@vueuse/core'
import { ESTADOS_PROYECTO, REGIONES_CHILE, type EstadoProyecto } from '@/types'

const router = useRouter()
const store = useProyectosStore()
const clientesStore = useClientesStore()

const busqueda = ref('')
const filtroEstado = ref<EstadoProyecto | ''>('')
const filtroRegion = ref('')
const filtroCliente = ref('')

// Debounce de busqueda
const buscarDebounced = useDebounceFn(() => {
  aplicarFiltros()
}, 300)

watch(busqueda, () => {
  buscarDebounced()
})

watch([filtroEstado, filtroRegion, filtroCliente], () => {
  aplicarFiltros()
})

function aplicarFiltros() {
  store.cargarProyectos({
    busqueda: busqueda.value || undefined,
    estado: filtroEstado.value || undefined,
    region: filtroRegion.value || undefined,
    cliente_id: filtroCliente.value || undefined,
    page: 1,
  })
}

onMounted(async () => {
  await Promise.all([
    store.cargarProyectos(),
    clientesStore.cargarClientes({ page_size: 100 }),
  ])
})

function irANuevo() {
  router.push('/proyectos/nuevo')
}

function irADetalle(id: string) {
  router.push(`/proyectos/${id}`)
}

function cambiarPagina(page: number) {
  store.cargarProyectos({ page })
}

function getEstadoInfo(estado: EstadoProyecto) {
  return ESTADOS_PROYECTO.find((e) => e.value === estado)
}
</script>

<template>
  <div class="p-6 max-w-7xl mx-auto">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold">Proyectos</h1>
        <p class="text-sm opacity-60">{{ store.paginacion.total }} proyectos registrados</p>
      </div>
      <button class="btn btn-primary" @click="irANuevo">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        Nuevo Proyecto
      </button>
    </div>

    <!-- Filtros -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
      <input
        v-model="busqueda"
        type="text"
        placeholder="Buscar por nombre..."
        class="input input-bordered w-full"
      />
      <select v-model="filtroEstado" class="select select-bordered w-full">
        <option value="">Todos los estados</option>
        <option v-for="estado in ESTADOS_PROYECTO" :key="estado.value" :value="estado.value">
          {{ estado.label }}
        </option>
      </select>
      <select v-model="filtroRegion" class="select select-bordered w-full">
        <option value="">Todas las regiones</option>
        <option v-for="region in REGIONES_CHILE" :key="region" :value="region">
          {{ region }}
        </option>
      </select>
      <select v-model="filtroCliente" class="select select-bordered w-full">
        <option value="">Todos los clientes</option>
        <option v-for="cliente in clientesStore.clientes" :key="cliente.id" :value="cliente.id">
          {{ cliente.razon_social }}
        </option>
      </select>
    </div>

    <!-- Loading -->
    <div v-if="store.cargando" class="flex justify-center py-20">
      <span class="loading loading-spinner loading-lg"></span>
    </div>

    <!-- Error -->
    <div v-else-if="store.error" class="alert alert-error">
      {{ store.error }}
    </div>

    <!-- Lista vacia -->
    <div v-else-if="!store.tieneProyectos" class="text-center py-20">
      <div class="text-6xl opacity-20 mb-4">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-24 w-24 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
        </svg>
      </div>
      <h2 class="text-xl font-bold mb-2">No hay proyectos</h2>
      <p class="opacity-60 mb-4">Comienza creando tu primer proyecto</p>
      <button class="btn btn-primary" @click="irANuevo">
        Crear Proyecto
      </button>
    </div>

    <!-- Grid de proyectos -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div
        v-for="proyecto in store.proyectos"
        :key="proyecto.id"
        class="card bg-base-100 shadow-sm hover:shadow-md transition-shadow cursor-pointer"
        @click="irADetalle(proyecto.id)"
      >
        <div class="card-body">
          <div class="flex items-start justify-between">
            <div class="flex-1 min-w-0">
              <h3 class="font-bold truncate">{{ proyecto.nombre }}</h3>
              <p class="text-sm opacity-60 truncate">
                {{ proyecto.cliente_razon_social || 'Sin cliente' }}
              </p>
            </div>
            <span
              class="badge badge-sm ml-2"
              :class="getEstadoInfo(proyecto.estado)?.color"
            >
              {{ getEstadoInfo(proyecto.estado)?.label }}
            </span>
          </div>

          <div class="mt-4 space-y-2">
            <!-- Progreso -->
            <div class="flex items-center gap-2">
              <progress
                class="progress progress-primary flex-1"
                :value="proyecto.porcentaje_completado"
                max="100"
              ></progress>
              <span class="text-xs opacity-60">{{ proyecto.porcentaje_completado }}%</span>
            </div>

            <!-- Info -->
            <div class="flex items-center gap-4 text-xs opacity-60">
              <span v-if="proyecto.region">{{ proyecto.region }}</span>
              <span v-if="proyecto.tipo_mineria">{{ proyecto.tipo_mineria }}</span>
            </div>

            <!-- Badges -->
            <div class="flex items-center gap-2">
              <span
                v-if="proyecto.tiene_geometria"
                class="badge badge-ghost badge-xs"
                title="Tiene geometria"
              >
                Mapa
              </span>
              <span
                v-if="proyecto.total_analisis > 0"
                class="badge badge-ghost badge-xs"
              >
                {{ proyecto.total_analisis }} analisis
              </span>
              <span
                v-if="proyecto.afecta_glaciares"
                class="badge badge-error badge-xs"
                title="Afecta glaciares"
              >
                Glaciares
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Paginacion -->
    <div v-if="store.paginacion.pages > 1" class="flex justify-center mt-6">
      <div class="join">
        <button
          class="join-item btn btn-sm"
          :disabled="store.paginacion.page <= 1"
          @click="cambiarPagina(store.paginacion.page - 1)"
        >
          Anterior
        </button>
        <button class="join-item btn btn-sm btn-disabled">
          Pagina {{ store.paginacion.page }} de {{ store.paginacion.pages }}
        </button>
        <button
          class="join-item btn btn-sm"
          :disabled="store.paginacion.page >= store.paginacion.pages"
          @click="cambiarPagina(store.paginacion.page + 1)"
        >
          Siguiente
        </button>
      </div>
    </div>
  </div>
</template>
