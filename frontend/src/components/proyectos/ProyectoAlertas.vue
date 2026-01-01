<script setup lang="ts">
import { computed } from 'vue'
import type { Proyecto } from '@/types'

const props = defineProps<{
  proyecto: Proyecto
}>()

const alertas = computed(() => {
  const items = []

  if (props.proyecto.afecta_glaciares) {
    items.push({
      tipo: 'error',
      mensaje: 'Afecta glaciares (< 5km)',
      detalle: 'Trigger EIA Art. 11 letra b)',
    })
  }

  if (props.proyecto.dist_area_protegida_km !== null && props.proyecto.dist_area_protegida_km < 10) {
    items.push({
      tipo: 'warning',
      mensaje: `Area protegida a ${props.proyecto.dist_area_protegida_km?.toFixed(1)} km`,
      detalle: 'Verificar afectacion segun Art. 11 letra d)',
    })
  }

  if (props.proyecto.dist_comunidad_indigena_km !== null && props.proyecto.dist_comunidad_indigena_km < 5) {
    items.push({
      tipo: 'warning',
      mensaje: `Comunidad indigena a ${props.proyecto.dist_comunidad_indigena_km?.toFixed(1)} km`,
      detalle: 'Posible consulta indigena segun Convenio 169',
    })
  }

  if (props.proyecto.dist_centro_poblado_km !== null && props.proyecto.dist_centro_poblado_km < 2) {
    items.push({
      tipo: 'info',
      mensaje: `Centro poblado a ${props.proyecto.dist_centro_poblado_km?.toFixed(1)} km`,
      detalle: 'Considerar impacto en poblacion',
    })
  }

  return items
})
</script>

<template>
  <div v-if="alertas.length > 0" class="space-y-2">
    <div
      v-for="(alerta, idx) in alertas"
      :key="idx"
      class="alert"
      :class="{
        'alert-error': alerta.tipo === 'error',
        'alert-warning': alerta.tipo === 'warning',
        'alert-info': alerta.tipo === 'info',
      }"
    >
      <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
      </svg>
      <div>
        <p class="font-medium">{{ alerta.mensaje }}</p>
        <p class="text-xs opacity-80">{{ alerta.detalle }}</p>
      </div>
    </div>
  </div>

  <div v-else class="alert alert-success">
    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
    </svg>
    <span>Sin alertas GIS detectadas</span>
  </div>
</template>
