<script setup lang="ts">
import type { Severidad } from '@/types';

defineProps<{
  severidad: Severidad;
  size?: 'xs' | 'sm' | 'md' | 'lg';
}>();

const colores: Record<Severidad, string> = {
  CRITICA: 'badge-error',
  ALTA: 'badge-warning',
  MEDIA: 'badge-info',
  BAJA: 'badge-success',
  INFO: 'badge-neutral',
};

const etiquetas: Record<Severidad, string> = {
  CRITICA: 'Crítica',
  ALTA: 'Alta',
  MEDIA: 'Media',
  BAJA: 'Baja',
  INFO: 'Info',
};
</script>

<template>
  <span
    class="badge"
    :class="[
      colores[severidad],
      {
        'badge-xs': size === 'xs',
        'badge-sm': size === 'sm',
        'badge-md': size === 'md' || !size,
        'badge-lg': size === 'lg',
      },
    ]"
  >
    {{ etiquetas[severidad] }}
  </span>
</template>
