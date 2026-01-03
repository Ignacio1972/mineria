<script setup lang="ts">
/**
 * Panel lateral que muestra la ficha acumulativa del proyecto.
 * Se actualiza en tiempo real cuando el asistente guarda datos.
 */
import { ref, computed, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useFichaStore } from '@/stores/ficha'
import type { CategoriaCaracteristica } from '@/types'
import { CATEGORIA_LABELS, VIA_SUGERIDA_LABELS } from '@/types/ficha'

interface Props {
  proyectoId: number
  colapsado?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  colapsado: false,
})

const emit = defineEmits<{
  (e: 'toggle-colapso'): void
}>()

const store = useFichaStore()
const {
  ficha,
  caracteristicasPorCategoria,
  analisisArt11,
  cargando,
  error,
  porcentajeProgreso,
  viaSugerida,
  literalesGatillados,
  totalPAS,
  pasRequeridos,
} = storeToRefs(store)

// Categoria activa en el acordeon
const categoriaActiva = ref<CategoriaCaracteristica | null>(null)

// Cargar ficha cuando cambia el proyecto
watch(
  () => props.proyectoId,
  async (newId) => {
    if (newId) {
      await store.cargarFicha(newId)
      await store.cargarProgreso()
    }
  },
  { immediate: true }
)

// Categorias ordenadas
const categorias: CategoriaCaracteristica[] = [
  'identificacion',
  'tecnico',
  'obras',
  'fases',
  'insumos',
  'emisiones',
  'social',
  'ambiental',
]

// Obtener items de una categoria
function getCategoriaDatos(categoria: CategoriaCaracteristica): Record<string, unknown> | null {
  if (!caracteristicasPorCategoria.value) return null
  return caracteristicasPorCategoria.value[categoria] || null
}

// Contar items de una categoria
function getCategoriaCount(categoria: CategoriaCaracteristica): number {
  const datos = getCategoriaDatos(categoria)
  return datos ? Object.keys(datos).length : 0
}

// Toggle categoria
function toggleCategoria(categoria: CategoriaCaracteristica): void {
  if (categoriaActiva.value === categoria) {
    categoriaActiva.value = null
  } else {
    categoriaActiva.value = categoria
  }
}

// Formatear valor para mostrar
function formatearValor(valor: unknown): string {
  if (valor === null || valor === undefined) return '-'
  if (typeof valor === 'boolean') return valor ? 'Si' : 'No'
  if (typeof valor === 'number') return valor.toLocaleString('es-CL')
  return String(valor)
}

// Clase de color para via sugerida
const viaSugeridaClass = computed(() => {
  switch (viaSugerida.value) {
    case 'DIA':
      return 'badge-success'
    case 'EIA':
      return 'badge-warning'
    case 'NO_SEIA':
      return 'badge-info'
    default:
      return 'badge-ghost'
  }
})

// Clase de color para literal Art. 11
function getLiteralClass(estado: string): string {
  switch (estado) {
    case 'confirmado':
      return 'text-error'
    case 'probable':
      return 'text-warning'
    case 'no_aplica':
      return 'text-success'
    default:
      return 'text-base-content/50'
  }
}

// Descripcion de literales Art. 11
const literalDescripciones: Record<string, string> = {
  a: 'Riesgo salud poblacion',
  b: 'Efectos adversos recursos naturales',
  c: 'Reasentamiento comunidades',
  d: 'Areas protegidas / glaciares',
  e: 'Alteracion patrimonio cultural',
  f: 'Alteracion paisaje/turismo',
}
</script>

<template>
  <div
    class="flex flex-col h-full bg-base-100 border-l border-base-300 overflow-hidden transition-all duration-300"
    :class="colapsado ? 'w-12' : 'w-full'"
  >
    <!-- Header -->
    <div class="bg-secondary text-secondary-content p-3 flex items-center justify-between shrink-0">
      <div v-if="!colapsado" class="flex items-center gap-2">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <span class="font-semibold text-sm">Ficha del Proyecto</span>
      </div>

      <button
        class="btn btn-ghost btn-sm btn-circle text-secondary-content"
        :title="colapsado ? 'Expandir' : 'Colapsar'"
        @click="emit('toggle-colapso')"
      >
        <svg v-if="!colapsado" xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
        </svg>
        <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 5l7 7-7 7M5 5l7 7-7 7" />
        </svg>
      </button>
    </div>

    <!-- Contenido cuando esta expandido -->
    <template v-if="!colapsado">
      <!-- Cargando -->
      <div v-if="cargando" class="flex-1 flex items-center justify-center">
        <span class="loading loading-spinner loading-md"></span>
      </div>

      <!-- Error -->
      <div v-else-if="error" class="p-4">
        <div class="alert alert-error text-sm">
          <span>{{ error }}</span>
        </div>
      </div>

      <!-- Sin ficha -->
      <div v-else-if="!ficha" class="flex-1 flex items-center justify-center p-4 text-center">
        <div class="text-base-content/50">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 mx-auto mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <p class="text-sm">Selecciona un proyecto para ver su ficha</p>
        </div>
      </div>

      <!-- Ficha -->
      <div v-else class="flex-1 overflow-y-auto">
        <!-- Diagnostico rapido -->
        <div class="p-3 bg-base-200 border-b border-base-300">
          <div class="flex items-center justify-between mb-2">
            <span class="text-xs font-medium text-base-content/70">Diagnostico</span>
            <span
              class="badge badge-sm"
              :class="viaSugeridaClass"
            >
              {{ viaSugerida ? VIA_SUGERIDA_LABELS[viaSugerida] : 'Pendiente' }}
            </span>
          </div>

          <!-- Barra de progreso -->
          <div class="mb-2">
            <div class="flex items-center justify-between text-xs mb-1">
              <span>Completitud</span>
              <span>{{ Math.round(porcentajeProgreso) }}%</span>
            </div>
            <progress
              class="progress progress-primary w-full h-2"
              :value="porcentajeProgreso"
              max="100"
            ></progress>
          </div>

          <!-- Literales gatillados -->
          <div v-if="literalesGatillados.length > 0" class="flex items-center gap-1 text-xs">
            <span class="text-base-content/70">Art. 11:</span>
            <span
              v-for="lit in literalesGatillados"
              :key="lit"
              class="badge badge-error badge-xs"
            >
              {{ lit }}
            </span>
          </div>
        </div>

        <!-- Art. 11 - Resumen compacto -->
        <div class="p-3 border-b border-base-300">
          <div class="text-xs font-medium text-base-content/70 mb-2">
            Literales Art. 11
          </div>
          <div class="grid grid-cols-6 gap-1">
            <div
              v-for="lit in ['a', 'b', 'c', 'd', 'e', 'f']"
              :key="lit"
              class="tooltip tooltip-bottom"
              :data-tip="literalDescripciones[lit]"
            >
              <div
                class="text-center text-xs font-mono p-1 rounded"
                :class="[
                  getLiteralClass(analisisArt11.find(a => a.literal === lit)?.estado || 'pendiente'),
                  'bg-base-200'
                ]"
              >
                {{ lit.toUpperCase() }}
              </div>
            </div>
          </div>
        </div>

        <!-- PAS resumen -->
        <div class="p-3 border-b border-base-300">
          <div class="flex items-center justify-between">
            <span class="text-xs font-medium text-base-content/70">PAS Identificados</span>
            <span class="badge badge-sm badge-outline">{{ totalPAS }}</span>
          </div>
          <div v-if="pasRequeridos.length > 0" class="mt-2 flex flex-wrap gap-1">
            <span
              v-for="p in pasRequeridos.slice(0, 5)"
              :key="p.articulo"
              class="badge badge-warning badge-xs"
            >
              Art. {{ p.articulo }}
            </span>
            <span v-if="pasRequeridos.length > 5" class="badge badge-ghost badge-xs">
              +{{ pasRequeridos.length - 5 }}
            </span>
          </div>
        </div>

        <!-- Categorias - Acordeon -->
        <div class="divide-y divide-base-200">
          <div
            v-for="cat in categorias"
            :key="cat"
            class="group"
          >
            <!-- Header categoria -->
            <button
              class="w-full px-3 py-2 flex items-center justify-between text-sm hover:bg-base-200 transition-colors"
              @click="toggleCategoria(cat)"
            >
              <div class="flex items-center gap-2">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  class="h-4 w-4 transition-transform"
                  :class="{ 'rotate-90': categoriaActiva === cat }"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                </svg>
                <span>{{ CATEGORIA_LABELS[cat] }}</span>
              </div>
              <span class="badge badge-ghost badge-sm">
                {{ getCategoriaCount(cat) }}
              </span>
            </button>

            <!-- Contenido categoria -->
            <div
              v-if="categoriaActiva === cat && getCategoriaCount(cat) > 0"
              class="px-3 pb-3 bg-base-50"
            >
              <div class="space-y-1">
                <div
                  v-for="(valor, clave) in getCategoriaDatos(cat)"
                  :key="String(clave)"
                  class="flex items-center justify-between text-xs py-1 border-b border-base-200 last:border-0"
                >
                  <span class="text-base-content/70 truncate mr-2" :title="String(clave)">
                    {{ String(clave).replace(/_/g, ' ') }}
                  </span>
                  <span class="font-medium truncate text-right" :title="formatearValor(valor)">
                    {{ formatearValor(valor) }}
                  </span>
                </div>
              </div>
            </div>

            <!-- Sin datos -->
            <div
              v-else-if="categoriaActiva === cat && getCategoriaCount(cat) === 0"
              class="px-3 pb-3 text-xs text-base-content/50 italic"
            >
              Sin datos registrados
            </div>
          </div>
        </div>
      </div>

      <!-- Footer con info de ubicacion -->
      <div v-if="ficha?.ubicacion" class="p-2 bg-base-200 border-t border-base-300 text-xs">
        <div class="flex items-center gap-1 text-base-content/70">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
          <span class="truncate">
            {{ ficha.ubicacion.comunas?.join(', ') || ficha.ubicacion.regiones?.join(', ') || 'Sin ubicacion' }}
          </span>
        </div>
      </div>
    </template>

    <!-- Contenido cuando esta colapsado -->
    <div v-else class="flex-1 flex flex-col items-center py-4 gap-3">
      <!-- Icono de ficha -->
      <button
        class="btn btn-ghost btn-circle"
        title="Abrir ficha"
        @click="emit('toggle-colapso')"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      </button>

      <!-- Indicador de progreso circular -->
      <div
        v-if="ficha"
        class="radial-progress text-primary text-xs"
        :style="`--value:${porcentajeProgreso}; --size:2.5rem; --thickness:3px;`"
        role="progressbar"
      >
        {{ Math.round(porcentajeProgreso) }}
      </div>

      <!-- Via sugerida badge -->
      <div
        v-if="viaSugerida && viaSugerida !== 'INDEFINIDO'"
        class="badge badge-sm"
        :class="viaSugeridaClass"
        style="writing-mode: vertical-rl; text-orientation: mixed;"
      >
        {{ viaSugerida }}
      </div>
    </div>
  </div>
</template>
