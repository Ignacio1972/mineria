<script setup lang="ts">
import { useUIStore } from '@/stores/ui';
import { useAnalysisStore } from '@/stores/analysis';
import { computed } from 'vue';
import SeiaClassification from './SeiaClassification.vue';
import TriggersList from './TriggersList.vue';
import AlertsPanel from './AlertsPanel.vue';
import GisResults from './GisResults.vue';
import AuditoriaTrazabilidad from './AuditoriaTrazabilidad.vue';
import ReportViewer from '@/components/report/ReportViewer.vue';
import EmptyState from '@/components/common/EmptyState.vue';
import LoadingSpinner from '@/components/common/LoadingSpinner.vue';

const uiStore = useUIStore();
const analysisStore = useAnalysisStore();

const tabs = [
  { id: 'resumen', label: 'Resumen', icon: 'chart' },
  { id: 'gis', label: 'Análisis GIS', icon: 'map' },
  { id: 'triggers', label: 'Triggers Art. 11', icon: 'alert' },
  { id: 'alertas', label: 'Alertas', icon: 'warning' },
  { id: 'informe', label: 'Informe', icon: 'document' },
  { id: 'auditoria', label: 'Trazabilidad', icon: 'shield' },
] as const;

const conteoAlertas = computed(() => analysisStore.conteoAlertas);
</script>

<template>
  <div
    class="results-panel bg-base-100 border-t border-base-300 transition-all duration-300"
    :class="uiStore.panelResultadosExpandido ? 'expanded' : 'collapsed'"
  >
    <!-- Header del panel -->
    <div
      class="flex items-center justify-between px-4 py-2 bg-base-200 cursor-pointer"
      @click="uiStore.togglePanelResultados"
    >
      <div class="flex items-center gap-4">
        <h3 class="font-semibold text-sm">Resultados del Análisis</h3>
        <div v-if="analysisStore.resultado" class="flex gap-2">
          <span
            class="badge"
            :class="analysisStore.clasificacion?.via_ingreso_recomendada === 'EIA' ? 'badge-warning' : 'badge-success'"
          >
            {{ analysisStore.clasificacion?.via_ingreso_recomendada || '-' }}
          </span>
          <span v-if="conteoAlertas.CRITICA > 0" class="badge badge-error badge-sm">
            {{ conteoAlertas.CRITICA }} críticas
          </span>
          <span v-if="conteoAlertas.ALTA > 0" class="badge badge-warning badge-sm">
            {{ conteoAlertas.ALTA }} altas
          </span>
        </div>
      </div>
      <button class="btn btn-ghost btn-sm btn-circle">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          class="h-5 w-5 transition-transform"
          :class="uiStore.panelResultadosExpandido ? 'rotate-180' : ''"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7" />
        </svg>
      </button>
    </div>

    <!-- Contenido -->
    <div v-if="uiStore.panelResultadosExpandido" class="overflow-hidden">
      <!-- Loading -->
      <div v-if="analysisStore.cargando" class="p-8">
        <LoadingSpinner size="lg" text="Ejecutando análisis..." />
      </div>

      <!-- Error -->
      <div v-else-if="analysisStore.error" class="p-4">
        <div class="alert alert-error">
          <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>{{ analysisStore.error }}</span>
        </div>
      </div>

      <!-- Sin resultados -->
      <div v-else-if="!analysisStore.resultado" class="p-4">
        <EmptyState
          titulo="Sin resultados"
          descripcion="Dibuje el polígono del proyecto y ejecute el análisis para ver los resultados."
          icono="chart"
        />
      </div>

      <!-- Resultados -->
      <div v-else>
        <!-- Tabs -->
        <div class="tabs tabs-bordered px-4 bg-base-100">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            class="tab"
            :class="uiStore.tabResultadosActivo === tab.id ? 'tab-active' : ''"
            @click="uiStore.setTabResultados(tab.id)"
          >
            {{ tab.label }}
            <span
              v-if="tab.id === 'alertas' && conteoAlertas.total > 0"
              class="badge badge-sm ml-1"
              :class="{
                'badge-error': conteoAlertas.CRITICA > 0,
                'badge-warning': conteoAlertas.CRITICA === 0 && conteoAlertas.ALTA > 0,
                'badge-info': conteoAlertas.CRITICA === 0 && conteoAlertas.ALTA === 0,
              }"
            >
              {{ conteoAlertas.total }}
            </span>
            <span
              v-if="tab.id === 'triggers' && analysisStore.triggers.length > 0"
              class="badge badge-sm badge-warning ml-1"
            >
              {{ analysisStore.triggers.length }}
            </span>
          </button>
        </div>

        <!-- Tab content -->
        <div class="p-4 overflow-y-auto" style="max-height: calc(80vh - 120px); min-height: 400px">
          <SeiaClassification v-if="uiStore.tabResultadosActivo === 'resumen'" />
          <GisResults v-else-if="uiStore.tabResultadosActivo === 'gis'" />
          <TriggersList v-else-if="uiStore.tabResultadosActivo === 'triggers'" />
          <AlertsPanel v-else-if="uiStore.tabResultadosActivo === 'alertas'" />
          <ReportViewer v-else-if="uiStore.tabResultadosActivo === 'informe'" />
          <AuditoriaTrazabilidad v-else-if="uiStore.tabResultadosActivo === 'auditoria'" />
        </div>
      </div>
    </div>
  </div>
</template>
