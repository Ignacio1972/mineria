<script setup lang="ts">
import { onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useProyectosStore } from '@/stores/proyectos'
import { useAnalysisStore } from '@/stores/analysis'
import AnalysisPanel from '@/components/analysis/AnalysisPanel.vue'

const route = useRoute()
const router = useRouter()
const store = useProyectosStore()
const analysisStore = useAnalysisStore()

onMounted(async () => {
  const id = route.params.id as string
  console.log('[ProyectoAnalisisView] onMounted, id:', id)
  if (id) {
    // Cargar el proyecto
    await store.cargarProyecto(id)

    // Cargar el último análisis del proyecto desde la BD
    const proyectoId = parseInt(id, 10)
    console.log('[ProyectoAnalisisView] proyectoId parsed:', proyectoId)
    if (!isNaN(proyectoId)) {
      console.log('[ProyectoAnalisisView] Llamando cargarUltimoAnalisis...')
      await analysisStore.cargarUltimoAnalisis(proyectoId)
      console.log('[ProyectoAnalisisView] cargarUltimoAnalisis completado')
    }
  }
})
</script>

<template>
  <div class="p-6 max-w-6xl mx-auto">
    <!-- Header -->
    <div class="flex items-center gap-4 mb-6">
      <button class="btn btn-ghost btn-sm" @click="router.push(`/proyectos/${route.params.id}`)">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
      </button>
      <div>
        <h1 class="text-2xl font-bold">Analisis</h1>
        <p class="text-sm opacity-60">{{ store.proyectoActual?.nombre || 'Cargando...' }}</p>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="store.cargando" class="flex justify-center py-20">
      <span class="loading loading-spinner loading-lg"></span>
    </div>

    <!-- Panel de analisis -->
    <AnalysisPanel v-else />
  </div>
</template>
