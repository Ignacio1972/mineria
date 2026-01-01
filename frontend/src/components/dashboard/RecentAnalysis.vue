<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { dashboardService, type AnalisisReciente } from '@/services/dashboard'

const router = useRouter()

const analisis = ref<AnalisisReciente[]>([])
const cargando = ref(true)
const error = ref<string | null>(null)

onMounted(async () => {
  try {
    analisis.value = await dashboardService.obtenerAnalisisRecientes(5)
  } catch (e) {
    console.error('Error cargando analisis recientes:', e)
    error.value = e instanceof Error ? e.message : 'Error al cargar analisis'
  } finally {
    cargando.value = false
  }
})

function formatearFecha(fecha: string): string {
  return new Date(fecha).toLocaleDateString('es-CL', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function irAProyecto(proyectoId: string) {
  router.push(`/proyectos/${proyectoId}/analisis`)
}
</script>

<template>
  <div class="card bg-base-100 shadow-sm">
    <div class="card-body">
      <div class="flex items-center justify-between mb-4">
        <h2 class="card-title text-lg">Analisis Recientes</h2>
        <router-link to="/analisis" class="btn btn-ghost btn-sm">
          Ver todos
        </router-link>
      </div>

      <!-- Loading -->
      <div v-if="cargando" class="flex justify-center py-8">
        <span class="loading loading-spinner loading-md"></span>
      </div>

      <!-- Error -->
      <div v-else-if="error" class="alert alert-error">
        {{ error }}
      </div>

      <!-- Lista vacia -->
      <div v-else-if="analisis.length === 0" class="text-center py-8 opacity-60">
        <p>No hay analisis recientes</p>
        <router-link to="/proyectos" class="btn btn-ghost btn-sm mt-2">
          Ir a proyectos
        </router-link>
      </div>

      <!-- Lista de analisis -->
      <div v-else class="overflow-x-auto">
        <table class="table table-sm">
          <thead>
            <tr>
              <th>Proyecto</th>
              <th>Via</th>
              <th>Confianza</th>
              <th>Alertas</th>
              <th>Fecha</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="item in analisis"
              :key="item.id"
              class="hover cursor-pointer"
              @click="irAProyecto(item.proyecto_id)"
            >
              <td class="font-medium">{{ item.proyecto_nombre }}</td>
              <td>
                <span
                  class="badge badge-sm"
                  :class="item.via_ingreso === 'EIA' ? 'badge-error' : 'badge-success'"
                >
                  {{ item.via_ingreso }}
                </span>
              </td>
              <td>{{ Math.round(item.confianza * 100) }}%</td>
              <td>
                <span
                  v-if="item.alertas_criticas > 0"
                  class="badge badge-error badge-sm"
                >
                  {{ item.alertas_criticas }}
                </span>
                <span v-else class="opacity-50">-</span>
              </td>
              <td class="text-xs opacity-60">{{ formatearFecha(item.fecha) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
