<script setup lang="ts">
import { computed } from 'vue';
import { useAnalysisStore } from '@/stores/analysis';
import EmptyState from '@/components/common/EmptyState.vue';
import ExportButtons from './ExportButtons.vue';

const analysisStore = useAnalysisStore();

const informe = computed(() => analysisStore.informe);
const secciones = computed(() => informe.value?.secciones || []);
</script>

<template>
  <div>
    <div v-if="!informe">
      <EmptyState
        titulo="Sin informe generado"
        descripcion="Ejecute el análisis completo (con LLM) para generar un informe detallado."
        icono="document"
      />
    </div>

    <div v-else class="space-y-4">
      <!-- Header del informe -->
      <div class="flex items-center justify-between">
        <div>
          <h3 class="font-bold text-lg">Informe de Prefactibilidad Ambiental</h3>
          <p class="text-sm opacity-60">
            Generado: {{ new Date(informe.fecha_generacion).toLocaleString('es-CL') }}
          </p>
        </div>
        <ExportButtons />
      </div>

      <!-- Secciones del informe -->
      <div class="space-y-4">
        <div
          v-for="seccion in secciones"
          :key="seccion.orden"
          class="card bg-base-200"
        >
          <div class="card-body p-4">
            <h4 class="card-title text-sm">
              {{ seccion.orden }}. {{ seccion.titulo }}
            </h4>
            <div class="prose prose-sm max-w-none">
              <p class="whitespace-pre-wrap">{{ seccion.contenido }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Texto completo (colapsable) -->
      <div class="collapse collapse-arrow bg-base-200">
        <input type="checkbox" />
        <div class="collapse-title font-medium">
          Ver texto completo del informe
        </div>
        <div class="collapse-content">
          <pre class="text-xs whitespace-pre-wrap bg-base-300 p-4 rounded-lg overflow-x-auto">{{ informe.texto_completo }}</pre>
        </div>
      </div>
    </div>
  </div>
</template>
