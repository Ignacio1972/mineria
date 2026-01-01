<script setup lang="ts">
import { computed } from 'vue';
import { useAnalysisStore } from '@/stores/analysis';
import AlertCard from './AlertCard.vue';
import EmptyState from '@/components/common/EmptyState.vue';
import type { Severidad } from '@/types';

const analysisStore = useAnalysisStore();

const alertasPorSeveridad = computed(() => analysisStore.alertasPorSeveridad);
const conteo = computed(() => analysisStore.conteoAlertas);

const severidades: Array<{ key: Severidad; label: string; color: string }> = [
  { key: 'CRITICA', label: 'Críticas', color: 'error' },
  { key: 'ALTA', label: 'Altas', color: 'warning' },
  { key: 'MEDIA', label: 'Medias', color: 'info' },
  { key: 'BAJA', label: 'Bajas', color: 'success' },
  { key: 'INFO', label: 'Informativas', color: 'neutral' },
];
</script>

<template>
  <div>
    <div v-if="conteo.total === 0">
      <EmptyState
        titulo="Sin alertas"
        descripcion="No se detectaron alertas para este proyecto."
        icono="search"
      />
    </div>

    <div v-else class="space-y-6">
      <!-- Resumen de alertas -->
      <div class="flex flex-wrap gap-2">
        <div
          v-for="sev in severidades"
          :key="sev.key"
          v-show="conteo[sev.key] > 0"
          class="badge gap-1"
          :class="`badge-${sev.color}`"
        >
          <span class="font-bold">{{ conteo[sev.key] }}</span>
          {{ sev.label }}
        </div>
      </div>

      <!-- Alertas por severidad -->
      <div
        v-for="sev in severidades"
        :key="sev.key"
        v-show="alertasPorSeveridad[sev.key].length > 0"
      >
        <div class="flex items-center gap-2 mb-2">
          <div class="badge" :class="`badge-${sev.color}`">
            {{ sev.label }} ({{ alertasPorSeveridad[sev.key].length }})
          </div>
        </div>

        <div class="space-y-2">
          <AlertCard
            v-for="alerta in alertasPorSeveridad[sev.key]"
            :key="alerta.id"
            :alerta="alerta"
          />
        </div>
      </div>
    </div>
  </div>
</template>
