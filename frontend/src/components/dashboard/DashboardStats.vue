<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { dashboardService } from '@/services/dashboard'

const router = useRouter()

const stats = ref({
  clientes: 0,
  proyectos: 0,
  analisis: 0,
  cargando: true,
  error: null as string | null,
})

onMounted(async () => {
  try {
    const dashboardStats = await dashboardService.obtenerEstadisticas()
    stats.value.clientes = dashboardStats.total_clientes
    stats.value.proyectos = dashboardStats.total_proyectos
    stats.value.analisis = dashboardStats.analisis_semana
  } catch (e) {
    console.error('Error cargando stats:', e)
    stats.value.error = e instanceof Error ? e.message : 'Error al cargar estadisticas'
  } finally {
    stats.value.cargando = false
  }
})
</script>

<template>
  <div>
    <!-- Error -->
    <div v-if="stats.error" class="alert alert-error mb-4">
    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
    </svg>
    <span>{{ stats.error }}</span>
  </div>

  <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
    <!-- Clientes -->
    <div
      class="card bg-base-100 shadow-sm cursor-pointer hover:shadow-md transition-shadow"
      @click="router.push('/clientes')"
    >
      <div class="card-body">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm opacity-60">Clientes</p>
            <p class="text-3xl font-bold">
              <span v-if="stats.cargando" class="loading loading-dots loading-sm"></span>
              <span v-else>{{ stats.clientes }}</span>
            </p>
          </div>
          <div class="text-4xl opacity-20">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </div>
        </div>
        <p class="text-xs opacity-60 mt-2">Ver todos</p>
      </div>
    </div>

    <!-- Proyectos -->
    <div
      class="card bg-base-100 shadow-sm cursor-pointer hover:shadow-md transition-shadow"
      @click="router.push('/proyectos')"
    >
      <div class="card-body">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm opacity-60">Proyectos</p>
            <p class="text-3xl font-bold">
              <span v-if="stats.cargando" class="loading loading-dots loading-sm"></span>
              <span v-else>{{ stats.proyectos }}</span>
            </p>
          </div>
          <div class="text-4xl opacity-20">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
            </svg>
          </div>
        </div>
        <p class="text-xs opacity-60 mt-2">Ver todos</p>
      </div>
    </div>

    <!-- Analisis -->
    <div
      class="card bg-base-100 shadow-sm cursor-pointer hover:shadow-md transition-shadow"
      @click="router.push('/analisis')"
    >
      <div class="card-body">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm opacity-60">Analisis esta semana</p>
            <p class="text-3xl font-bold">
              <span v-if="stats.cargando" class="loading loading-dots loading-sm"></span>
              <span v-else>{{ stats.analisis }}</span>
            </p>
          </div>
          <div class="text-4xl opacity-20">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
        </div>
        <p class="text-xs opacity-60 mt-2">Ver historial</p>
      </div>
    </div>
  </div>
  </div>
</template>
