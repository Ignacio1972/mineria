<script setup lang="ts">
import type { Alerta, Severidad } from '@/types';

defineProps<{
  alerta: Alerta;
}>();

const coloresBorde: Record<Severidad, string> = {
  CRITICA: 'border-l-error',
  ALTA: 'border-l-warning',
  MEDIA: 'border-l-info',
  BAJA: 'border-l-success',
  INFO: 'border-l-neutral',
};

const iconos: Record<Severidad, string> = {
  CRITICA: '!',
  ALTA: '!',
  MEDIA: 'i',
  BAJA: '',
  INFO: 'i',
};
</script>

<template>
  <div
    class="card bg-base-200 border-l-4"
    :class="coloresBorde[alerta.nivel]"
  >
    <div class="card-body p-3">
      <div class="flex items-start gap-3">
        <div
          class="flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold"
          :class="{
            'bg-error text-error-content': alerta.nivel === 'CRITICA',
            'bg-warning text-warning-content': alerta.nivel === 'ALTA',
            'bg-info text-info-content': alerta.nivel === 'MEDIA',
            'bg-success text-success-content': alerta.nivel === 'BAJA',
            'bg-neutral text-neutral-content': alerta.nivel === 'INFO',
          }"
        >
          {{ iconos[alerta.nivel] }}
        </div>

        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2 flex-wrap">
            <h4 class="font-semibold text-sm">{{ alerta.titulo }}</h4>
            <span class="badge badge-ghost badge-xs">{{ alerta.categoria }}</span>
          </div>

          <p class="text-sm opacity-70 mt-1">{{ alerta.descripcion }}</p>

          <div v-if="alerta.acciones_requeridas.length > 0" class="mt-2">
            <span class="text-xs font-semibold uppercase opacity-60">Acciones requeridas:</span>
            <ul class="list-disc list-inside text-xs mt-1 space-y-0.5">
              <li v-for="(accion, idx) in alerta.acciones_requeridas" :key="idx">
                {{ accion }}
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
