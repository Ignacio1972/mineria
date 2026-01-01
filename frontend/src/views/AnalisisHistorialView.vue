<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useDebounceFn } from '@vueuse/core'
import { dashboardService, type AnalisisReciente } from '@/services/dashboard'

const router = useRouter()

const analisis = ref<AnalisisReciente[]>([])
const cargando = ref(false)
const error = ref<string | null>(null)

// Estado para el modal de eliminación
const modalEliminar = ref(false)
const analisisAEliminar = ref<AnalisisReciente | null>(null)
const eliminando = ref(false)

const busqueda = ref('')
const filtroVia = ref<'EIA' | 'DIA' | ''>('')
const filtroFecha = ref<'hoy' | 'semana' | 'mes' | ''>('')

// Paginacion simple
const paginaActual = ref(1)
const porPagina = 12
const totalItems = ref(0)

const analisisFiltrados = computed(() => {
  let resultado = [...analisis.value]

  if (busqueda.value) {
    const query = busqueda.value.toLowerCase()
    resultado = resultado.filter((a) =>
      a.proyecto_nombre.toLowerCase().includes(query)
    )
  }

  if (filtroVia.value) {
    resultado = resultado.filter((a) => a.via_ingreso === filtroVia.value)
  }

  if (filtroFecha.value) {
    const ahora = new Date()
    resultado = resultado.filter((a) => {
      const fecha = new Date(a.fecha)
      if (filtroFecha.value === 'hoy') {
        return fecha.toDateString() === ahora.toDateString()
      } else if (filtroFecha.value === 'semana') {
        const hace7Dias = new Date(ahora.getTime() - 7 * 24 * 60 * 60 * 1000)
        return fecha >= hace7Dias
      } else if (filtroFecha.value === 'mes') {
        const hace30Dias = new Date(ahora.getTime() - 30 * 24 * 60 * 60 * 1000)
        return fecha >= hace30Dias
      }
      return true
    })
  }

  totalItems.value = resultado.length
  return resultado
})

const analisisPaginados = computed(() => {
  const inicio = (paginaActual.value - 1) * porPagina
  return analisisFiltrados.value.slice(inicio, inicio + porPagina)
})

const totalPaginas = computed(() => Math.ceil(totalItems.value / porPagina))

async function cargarAnalisis() {
  cargando.value = true
  error.value = null
  try {
    // Cargamos el máximo permitido por el backend (20)
    analisis.value = await dashboardService.obtenerAnalisisRecientes(20)
  } catch (e: any) {
    error.value = e.message || 'Error al cargar analisis'
  } finally {
    cargando.value = false
  }
}

const buscarDebounced = useDebounceFn(() => {
  paginaActual.value = 1
}, 300)

watch(busqueda, () => {
  buscarDebounced()
})

watch([filtroVia, filtroFecha], () => {
  paginaActual.value = 1
})

onMounted(() => {
  cargarAnalisis()
})

function irAProyecto(proyectoId: string) {
  router.push(`/proyectos/${proyectoId}/analisis`)
}

function formatearFecha(fecha: string) {
  return new Date(fecha).toLocaleDateString('es-CL', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function getConfianzaColor(confianza: number) {
  if (confianza >= 0.85) return 'text-success'
  if (confianza >= 0.65) return 'text-warning'
  return 'text-error'
}

function getConfianzaLabel(confianza: number) {
  if (confianza >= 0.85) return 'Alta'
  if (confianza >= 0.65) return 'Media'
  return 'Baja'
}

function limpiarFiltros() {
  busqueda.value = ''
  filtroVia.value = ''
  filtroFecha.value = ''
  paginaActual.value = 1
}

function abrirModalEliminar(item: AnalisisReciente, event: Event) {
  event.stopPropagation()
  analisisAEliminar.value = item
  modalEliminar.value = true
}

function cerrarModalEliminar() {
  modalEliminar.value = false
  analisisAEliminar.value = null
}

async function confirmarEliminar() {
  if (!analisisAEliminar.value) return

  eliminando.value = true
  try {
    const resultado = await dashboardService.eliminarAnalisis(
      parseInt(analisisAEliminar.value.id)
    )

    // Remover de la lista local
    analisis.value = analisis.value.filter(
      (a) => a.id !== analisisAEliminar.value?.id
    )

    cerrarModalEliminar()

    // Mostrar mensaje si era el último análisis
    if (resultado.era_ultimo_analisis) {
      console.log(`Proyecto cambiado a estado: ${resultado.nuevo_estado_proyecto}`)
    }
  } catch (e: any) {
    error.value = e.detail || 'Error al eliminar el análisis'
  } finally {
    eliminando.value = false
  }
}
</script>

<template>
  <div class="p-6 max-w-7xl mx-auto">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold">Historial de Analisis</h1>
        <p class="text-sm opacity-60">{{ totalItems }} analisis encontrados</p>
      </div>
      <button class="btn btn-ghost btn-sm" @click="cargarAnalisis" :disabled="cargando">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" :class="{ 'animate-spin': cargando }" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
        Actualizar
      </button>
    </div>

    <!-- Filtros -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
      <input
        v-model="busqueda"
        type="text"
        placeholder="Buscar por proyecto..."
        class="input input-bordered w-full"
      />
      <select v-model="filtroVia" class="select select-bordered w-full">
        <option value="">Todas las vias</option>
        <option value="EIA">EIA - Estudio de Impacto</option>
        <option value="DIA">DIA - Declaracion de Impacto</option>
      </select>
      <select v-model="filtroFecha" class="select select-bordered w-full">
        <option value="">Todas las fechas</option>
        <option value="hoy">Hoy</option>
        <option value="semana">Ultima semana</option>
        <option value="mes">Ultimo mes</option>
      </select>
      <button
        v-if="busqueda || filtroVia || filtroFecha"
        class="btn btn-ghost"
        @click="limpiarFiltros"
      >
        Limpiar filtros
      </button>
    </div>

    <!-- Estadisticas rapidas -->
    <div class="stats stats-vertical lg:stats-horizontal shadow mb-6 w-full">
      <div class="stat">
        <div class="stat-title">Total Analisis</div>
        <div class="stat-value text-primary">{{ analisis.length }}</div>
      </div>
      <div class="stat">
        <div class="stat-title">EIA</div>
        <div class="stat-value text-error">
          {{ analisis.filter((a) => a.via_ingreso === 'EIA').length }}
        </div>
        <div class="stat-desc">Estudios de Impacto</div>
      </div>
      <div class="stat">
        <div class="stat-title">DIA</div>
        <div class="stat-value text-success">
          {{ analisis.filter((a) => a.via_ingreso === 'DIA').length }}
        </div>
        <div class="stat-desc">Declaraciones de Impacto</div>
      </div>
      <div class="stat">
        <div class="stat-title">Alertas Criticas</div>
        <div class="stat-value text-warning">
          {{ analisis.reduce((sum, a) => sum + a.alertas_criticas, 0) }}
        </div>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="cargando" class="flex justify-center py-20">
      <span class="loading loading-spinner loading-lg"></span>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="alert alert-error">
      <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
      </svg>
      <span>{{ error }}</span>
      <button class="btn btn-sm" @click="cargarAnalisis">Reintentar</button>
    </div>

    <!-- Lista vacia -->
    <div v-else-if="analisisFiltrados.length === 0" class="text-center py-20">
      <div class="text-6xl opacity-20 mb-4">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-24 w-24 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      </div>
      <h2 class="text-xl font-bold mb-2">No hay analisis</h2>
      <p class="opacity-60 mb-4">
        {{ busqueda || filtroVia || filtroFecha ? 'No se encontraron resultados con los filtros aplicados' : 'Aun no se han realizado analisis' }}
      </p>
      <button v-if="busqueda || filtroVia || filtroFecha" class="btn btn-ghost" @click="limpiarFiltros">
        Limpiar filtros
      </button>
      <router-link v-else to="/proyectos" class="btn btn-primary">
        Ver proyectos
      </router-link>
    </div>

    <!-- Tabla de analisis -->
    <div v-else class="overflow-x-auto">
      <table class="table table-zebra">
        <thead>
          <tr>
            <th>Proyecto</th>
            <th>Via de Ingreso</th>
            <th>Confianza</th>
            <th>Alertas Criticas</th>
            <th>Fecha</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="item in analisisPaginados"
            :key="item.id"
            class="hover cursor-pointer"
            @click="irAProyecto(item.proyecto_id)"
          >
            <td>
              <div class="font-medium">{{ item.proyecto_nombre }}</div>
            </td>
            <td>
              <span
                class="badge"
                :class="item.via_ingreso === 'EIA' ? 'badge-error' : 'badge-success'"
              >
                {{ item.via_ingreso }}
              </span>
            </td>
            <td>
              <div class="flex items-center gap-2">
                <div class="radial-progress text-xs" :class="getConfianzaColor(item.confianza)" style="--value: 100; --size: 2rem;">
                  {{ Math.round(item.confianza * 100) }}%
                </div>
                <span class="text-xs opacity-60">{{ getConfianzaLabel(item.confianza) }}</span>
              </div>
            </td>
            <td>
              <span v-if="item.alertas_criticas > 0" class="badge badge-warning badge-sm">
                {{ item.alertas_criticas }}
              </span>
              <span v-else class="text-xs opacity-40">-</span>
            </td>
            <td class="text-sm opacity-60">
              {{ formatearFecha(item.fecha) }}
            </td>
            <td>
              <div class="flex gap-1">
                <button class="btn btn-ghost btn-sm">
                  Ver
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                  </svg>
                </button>
                <button
                  class="btn btn-ghost btn-sm text-error"
                  @click="abrirModalEliminar(item, $event)"
                  title="Eliminar análisis"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Paginacion -->
    <div v-if="totalPaginas > 1" class="flex justify-center mt-6">
      <div class="join">
        <button
          class="join-item btn btn-sm"
          :disabled="paginaActual <= 1"
          @click="paginaActual--"
        >
          Anterior
        </button>
        <button class="join-item btn btn-sm btn-disabled">
          Pagina {{ paginaActual }} de {{ totalPaginas }}
        </button>
        <button
          class="join-item btn btn-sm"
          :disabled="paginaActual >= totalPaginas"
          @click="paginaActual++"
        >
          Siguiente
        </button>
      </div>
    </div>

    <!-- Modal de confirmación de eliminación -->
    <dialog class="modal" :class="{ 'modal-open': modalEliminar }">
      <div class="modal-box">
        <h3 class="font-bold text-lg text-error">Eliminar Análisis</h3>

        <div v-if="analisisAEliminar" class="py-4">
          <p class="mb-4">
            ¿Estás seguro de eliminar este análisis?
          </p>

          <div class="bg-base-200 p-4 rounded-lg space-y-2">
            <div class="flex justify-between">
              <span class="opacity-60">Proyecto:</span>
              <span class="font-medium">{{ analisisAEliminar.proyecto_nombre }}</span>
            </div>
            <div class="flex justify-between">
              <span class="opacity-60">Via de ingreso:</span>
              <span
                class="badge"
                :class="analisisAEliminar.via_ingreso === 'EIA' ? 'badge-error' : 'badge-success'"
              >
                {{ analisisAEliminar.via_ingreso }}
              </span>
            </div>
            <div class="flex justify-between">
              <span class="opacity-60">Fecha:</span>
              <span>{{ formatearFecha(analisisAEliminar.fecha) }}</span>
            </div>
          </div>

          <div class="alert alert-warning mt-4">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <span class="text-sm">Esta accion eliminara el analisis y su auditoria. Es irreversible.</span>
          </div>
        </div>

        <div class="modal-action">
          <button class="btn" @click="cerrarModalEliminar" :disabled="eliminando">
            Cancelar
          </button>
          <button
            class="btn btn-error"
            @click="confirmarEliminar"
            :disabled="eliminando"
          >
            <span v-if="eliminando" class="loading loading-spinner loading-sm"></span>
            {{ eliminando ? 'Eliminando...' : 'Eliminar' }}
          </button>
        </div>
      </div>
      <form method="dialog" class="modal-backdrop">
        <button @click="cerrarModalEliminar">close</button>
      </form>
    </dialog>
  </div>
</template>
