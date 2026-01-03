<script setup lang="ts">
/**
 * ChatAsistente.vue - Componente contenedor del chat
 *
 * Muestra el ChatPanel con opción de alternar a Búsqueda Web (Perplexity).
 * Se usa en AsistenteView y ProyectoDetalleView.
 */
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAsistenteStore } from '@/stores/asistente'
import ChatPanel from './ChatPanel.vue'
import BusquedaWebPanel from './BusquedaWebPanel.vue'

interface Props {
  proyectoId?: number
  vistaActual?: string
}

const props = withDefaults(defineProps<Props>(), {
  vistaActual: 'asistente',
})

const emit = defineEmits<{
  (e: 'navegar', ruta: string): void
}>()

const router = useRouter()
const asistenteStore = useAsistenteStore()

// Estado local
const modoBusquedaWeb = ref(false)

function handleNavegar(ruta: string) {
  if (ruta.startsWith('/')) {
    router.push(ruta)
  } else {
    emit('navegar', ruta)
  }
}

// Lifecycle
onMounted(async () => {
  if (props.proyectoId) {
    asistenteStore.setProyectoContexto(props.proyectoId)
  }
})
</script>

<template>
  <div class="flex flex-col w-full h-full bg-base-100 overflow-hidden">
    <!-- Modo Busqueda Web -->
    <BusquedaWebPanel
      v-if="modoBusquedaWeb"
      class="h-full"
      @volver-chat="modoBusquedaWeb = false"
    />

    <!-- Modo Chat -->
    <ChatPanel
      v-else
      :proyecto-id="proyectoId"
      :vista-actual="vistaActual"
      class="h-full"
      @toggle-modo-web="modoBusquedaWeb = true"
      @navegar="handleNavegar"
    />
  </div>
</template>
