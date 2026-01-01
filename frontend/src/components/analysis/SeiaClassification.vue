<script setup lang="ts">
import { computed } from 'vue';
import { useAnalysisStore } from '@/stores/analysis';
import ConfidenceBadge from '@/components/common/ConfidenceBadge.vue';
import ExportButtons from '@/components/report/ExportButtons.vue';

const analysisStore = useAnalysisStore();

const clasificacion = computed(() => analysisStore.clasificacion);
const resultado = computed(() => analysisStore.resultado);
</script>

<template>
  <div v-if="clasificacion" class="space-y-6">
    <!-- Clasificación principal -->
    <div class="flex flex-col md:flex-row gap-6">
      <!-- Card de clasificación -->
      <div
        class="card flex-1"
        :class="clasificacion.via_ingreso_recomendada === 'EIA' ? 'bg-warning/10 border-warning' : 'bg-success/10 border-success'"
      >
        <div class="card-body items-center text-center">
          <h2 class="text-4xl font-bold" :class="clasificacion.via_ingreso_recomendada === 'EIA' ? 'text-warning' : 'text-success'">
            {{ clasificacion.via_ingreso_recomendada }}
          </h2>
          <p class="text-sm opacity-70">
            {{ clasificacion.via_ingreso_recomendada === 'EIA' ? 'Estudio de Impacto Ambiental' : 'Declaración de Impacto Ambiental' }}
          </p>
          <div class="mt-2">
            <ConfidenceBadge
              :nivel="clasificacion.nivel_confianza"
              :porcentaje="clasificacion.confianza"
            />
          </div>
        </div>
      </div>

      <!-- Métricas -->
      <div class="flex-1 space-y-4">
        <div class="stats stats-vertical lg:stats-horizontal shadow w-full">
          <div class="stat">
            <div class="stat-title">Puntaje Matriz</div>
            <div class="stat-value text-2xl">{{ clasificacion.puntaje_matriz.toFixed(1) }}</div>
            <div class="stat-desc">de 100 puntos</div>
          </div>
          <div class="stat">
            <div class="stat-title">Triggers</div>
            <div class="stat-value text-2xl">{{ analysisStore.triggers.length }}</div>
            <div class="stat-desc">Art. 11 Ley 19.300</div>
          </div>
          <div class="stat">
            <div class="stat-title">Alertas</div>
            <div class="stat-value text-2xl">{{ analysisStore.alertas.length }}</div>
            <div class="stat-desc">detectadas</div>
          </div>
        </div>

        <!-- Exportar -->
        <ExportButtons />
      </div>
    </div>

    <!-- Justificación -->
    <div class="card bg-base-200">
      <div class="card-body">
        <h3 class="card-title text-sm">Justificación de la Clasificación</h3>
        <p class="text-sm">{{ clasificacion.justificacion }}</p>
      </div>
    </div>

    <!-- Información del análisis -->
    <div v-if="resultado" class="text-xs opacity-60 flex flex-wrap gap-4">
      <span>ID: {{ resultado.id }}</span>
      <span>Fecha: {{ new Date(resultado.fecha_analisis).toLocaleString('es-CL') }}</span>
      <span>Modo: {{ analysisStore.modoAnalisis === 'completo' ? 'Completo (LLM)' : 'Rápido' }}</span>
    </div>
  </div>
</template>
