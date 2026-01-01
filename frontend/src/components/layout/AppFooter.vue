<script setup lang="ts">
import { useAnalysisStore } from '@/stores/analysis';
import { computed } from 'vue';

const analysisStore = useAnalysisStore();

const metricas = computed(() => {
  if (!analysisStore.resultado?.metricas) return null;
  return analysisStore.resultado.metricas;
});
</script>

<template>
  <footer class="bg-base-200 text-base-content p-2 text-xs app-footer">
    <div class="flex justify-between items-center">
      <div class="flex items-center gap-4">
        <span class="opacity-60">Sistema de Prefactibilidad Ambiental Minera - Chile</span>
        <span v-if="metricas" class="flex items-center gap-2">
          <span v-if="metricas.tiempo_gis_ms != null" class="badge badge-ghost badge-sm">
            GIS: {{ metricas.tiempo_gis_ms }}ms
          </span>
          <span v-if="metricas.tiempo_llm_ms != null" class="badge badge-ghost badge-sm">
            LLM: {{ (metricas.tiempo_llm_ms / 1000).toFixed(1) }}s
          </span>
          <span v-if="metricas.tiempo_analisis_segundos != null" class="badge badge-ghost badge-sm">
            Total: {{ metricas.tiempo_analisis_segundos.toFixed(1) }}s
          </span>
        </span>
      </div>
      <div class="flex items-center gap-2 opacity-60">
        <span>Normativa SEIA vigente</span>
        <span>|</span>
        <span>Datos GIS actualizados</span>
      </div>
    </div>
  </footer>
</template>
