<script setup lang="ts">
/**
 * ChatAsistente.vue - Componente contenedor principal
 *
 * Integra ChatPanel (70%) + FichaAcumulativa (30%) en un layout side-by-side.
 * Incluye toggle para cambiar entre Chat y Búsqueda Web (Perplexity).
 * Se usa en AsistenteView y ProyectoDetalleView para mostrar el asistente
 * con la ficha acumulativa del proyecto.
 */
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAsistenteStore } from '@/stores/asistente'
import { useFichaStore } from '@/stores/ficha'
import { storeToRefs } from 'pinia'
import ChatPanel from './ChatPanel.vue'
import FichaAcumulativa from './FichaAcumulativa.vue'
import BusquedaWebPanel from './BusquedaWebPanel.vue'

interface Props {
  proyectoId?: number
  vistaActual?: string
  modoCompacto?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  vistaActual: 'asistente',
  modoCompacto: false,
})

const emit = defineEmits<{
  (e: 'navegar', ruta: string): void
  (e: 'proyecto-actualizado', proyectoId: number): void
}>()

const router = useRouter()
const asistenteStore = useAsistenteStore()
const fichaStore = useFichaStore()

const { mensajes, estado } = storeToRefs(asistenteStore)

// Estado local para colapso de paneles y modo
const chatColapsado = ref(false)
const fichaColapsada = ref(false)
const modoBusquedaWeb = ref(false)

// Computed para clases de layout
const chatClasses = computed(() => {
  if (chatColapsado.value) return 'w-12'
  if (fichaColapsada.value) return 'flex-1'
  return 'w-[70%]'
})

const fichaClasses = computed(() => {
  if (fichaColapsada.value) return 'w-12'
  if (chatColapsado.value) return 'flex-1'
  return 'w-[30%]'
})

// Observar mensajes para recargar ficha cuando el asistente guarda datos
watch(
  () => mensajes.value,
  async (nuevos, anteriores) => {
    // Si hay un nuevo mensaje del asistente, verificar si guardó datos en la ficha
    if (nuevos.length > anteriores.length && props.proyectoId) {
      const ultimoMensaje = nuevos[nuevos.length - 1]

      // Verificar si el mensaje contiene tool_calls de guardar_ficha
      if (ultimoMensaje?.rol === 'assistant' && ultimoMensaje.tool_calls) {
        const guardarFichaCall = ultimoMensaje.tool_calls.find(
          (tc: { name: string }) => tc.name === 'guardar_ficha'
        )
        if (guardarFichaCall) {
          // Recargar la ficha para reflejar los cambios
          await fichaStore.recargarFicha()
        }
      }
    }
  },
  { deep: true }
)

// Toggle handlers
function handleToggleChat() {
  chatColapsado.value = !chatColapsado.value
}

function handleToggleFicha() {
  fichaColapsada.value = !fichaColapsada.value
}

function handleNavegar(ruta: string) {
  if (ruta.startsWith('/')) {
    router.push(ruta)
  } else {
    emit('navegar', ruta)
  }
}

// Lifecycle
onMounted(async () => {
  // Establecer contexto del proyecto en el asistente
  if (props.proyectoId) {
    asistenteStore.setProyectoContexto(props.proyectoId)
  }
})

onUnmounted(() => {
  // Limpiar ficha al desmontar si no estamos en contexto de proyecto
  if (!props.proyectoId) {
    fichaStore.limpiar()
  }
})
</script>

<template>
  <div class="flex flex-col w-full h-full bg-base-100 overflow-hidden">
    <!-- Contenido principal -->
    <div
      class="flex flex-1 overflow-hidden"
      :class="{ 'gap-1': !chatColapsado && !fichaColapsada && !modoBusquedaWeb }"
    >
      <!-- Modo Busqueda Web -->
      <div v-if="modoBusquedaWeb" class="flex-1 overflow-hidden">
        <BusquedaWebPanel class="h-full" @volver-chat="modoBusquedaWeb = false" />
      </div>

      <!-- Modo Chat -->
      <template v-else>
        <!-- Panel de Chat (70%) -->
        <div
          class="transition-all duration-300 shrink-0"
          :class="chatClasses"
        >
          <ChatPanel
            :proyecto-id="proyectoId"
            :vista-actual="vistaActual"
            :colapsado="chatColapsado"
            @toggle-colapso="handleToggleChat"
            @toggle-modo-web="modoBusquedaWeb = true"
            @navegar="handleNavegar"
          />
        </div>

        <!-- Panel de Ficha Acumulativa (30%) -->
        <div
          v-if="proyectoId"
          class="transition-all duration-300 shrink-0"
          :class="fichaClasses"
        >
          <FichaAcumulativa
            :proyecto-id="proyectoId"
            :colapsado="fichaColapsada"
            @toggle-colapso="handleToggleFicha"
          />
        </div>

        <!-- Mensaje cuando no hay proyecto seleccionado -->
        <div
          v-else-if="!chatColapsado"
          class="flex-1 flex items-center justify-center bg-base-200 rounded-lg m-2"
        >
          <div class="text-center text-base-content/60 p-8">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="h-16 w-16 mx-auto mb-4 opacity-40"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            <p class="text-lg font-medium mb-2">Sin proyecto activo</p>
            <p class="text-sm mb-4">
              Selecciona o crea un proyecto para ver su ficha acumulativa
            </p>
            <button
              class="btn btn-primary btn-sm"
              @click="router.push('/proyectos')"
            >
              Ver proyectos
            </button>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>
