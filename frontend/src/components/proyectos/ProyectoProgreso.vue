<script setup lang="ts">
import { computed } from 'vue'
import type { Proyecto } from '@/types'

const props = defineProps<{
  proyecto: Proyecto
}>()

const emit = defineEmits<{
  (e: 'irAMapa'): void
}>()

const pasos = computed(() => [
  {
    nombre: 'Cliente',
    completado: !!props.proyecto.cliente_id,
    icono: 'user',
  },
  {
    nombre: 'Datos basicos',
    completado: props.proyecto.porcentaje_completado >= 50,
    icono: 'document',
  },
  {
    nombre: 'Geometria',
    completado: props.proyecto.tiene_geometria,
    icono: 'map',
    accion: props.proyecto.tiene_geometria ? null : 'Dibujar en Mapa',
  },
  {
    nombre: 'Analisis',
    completado: props.proyecto.estado === 'analizado' || props.proyecto.total_analisis > 0,
    icono: 'chart',
    deshabilitado: !props.proyecto.puede_analizar,
  },
])
</script>

<template>
  <div class="card bg-base-100 shadow-sm">
    <div class="card-body">
      <div class="flex items-center justify-between mb-4">
        <h3 class="font-semibold">Estado del Proyecto</h3>
        <div class="badge" :class="proyecto.estado === 'borrador' ? 'badge-ghost' : 'badge-primary'">
          {{ proyecto.porcentaje_completado }}% completo
        </div>
      </div>

      <!-- Barra de progreso -->
      <progress
        class="progress progress-primary w-full mb-4"
        :value="proyecto.porcentaje_completado"
        max="100"
      ></progress>

      <!-- Lista de pasos -->
      <ul class="space-y-2">
        <li
          v-for="paso in pasos"
          :key="paso.nombre"
          class="flex items-center gap-3"
          :class="{ 'opacity-50': paso.deshabilitado }"
        >
          <!-- Icono de estado -->
          <div
            class="w-6 h-6 rounded-full flex items-center justify-center"
            :class="paso.completado ? 'bg-success text-success-content' : 'bg-base-300'"
          >
            <svg v-if="paso.completado" xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
            </svg>
            <span v-else class="w-2 h-2 rounded-full bg-base-content opacity-30"></span>
          </div>

          <!-- Nombre -->
          <span class="flex-1">{{ paso.nombre }}</span>

          <!-- Accion (si aplica) -->
          <span
            v-if="paso.accion"
            class="text-xs text-primary cursor-pointer hover:underline"
            @click="emit('irAMapa')"
          >
            {{ paso.accion }}
          </span>
        </li>
      </ul>
    </div>
  </div>
</template>
