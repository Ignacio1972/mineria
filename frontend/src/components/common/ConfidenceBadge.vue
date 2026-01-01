<script setup lang="ts">
import type { NivelConfianza } from '@/types';

defineProps<{
  nivel: NivelConfianza;
  porcentaje?: number;
}>();

const colores: Record<NivelConfianza, string> = {
  MUY_ALTA: 'badge-success',
  ALTA: 'badge-info',
  MEDIA: 'badge-warning',
  BAJA: 'badge-error',
};

const etiquetas: Record<NivelConfianza, string> = {
  MUY_ALTA: 'Muy Alta',
  ALTA: 'Alta',
  MEDIA: 'Media',
  BAJA: 'Baja',
};
</script>

<template>
  <span class="badge gap-1" :class="colores[nivel]">
    <span>{{ etiquetas[nivel] }}</span>
    <span v-if="porcentaje !== undefined">({{ Math.round(porcentaje * 100) }}%)</span>
  </span>
</template>
