<script setup lang="ts">
import { computed, watch } from 'vue';
import { useAnalysisStore } from '@/stores/analysis';
import EmptyState from '@/components/common/EmptyState.vue';
import LoadingSpinner from '@/components/common/LoadingSpinner.vue';

const analysisStore = useAnalysisStore();

const auditoria = computed(() => analysisStore.auditoria);
const cargando = computed(() => analysisStore.cargandoAuditoria);

// Cargar auditoría cuando cambia el resultado
watch(
  () => analysisStore.resultado?.id,
  (nuevoId) => {
    if (nuevoId) {
      const analisisId = parseInt(nuevoId, 10);
      if (!isNaN(analisisId)) {
        analysisStore.cargarAuditoria(analisisId);
      }
    }
  },
  { immediate: true }
);

// Formatear fecha
function formatearFecha(fecha: string): string {
  return new Date(fecha).toLocaleString('es-CL', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

// Formatear milisegundos a texto legible
function formatearTiempo(ms?: number): string {
  if (!ms) return '-';
  if (ms < 1000) return `${ms} ms`;
  return `${(ms / 1000).toFixed(2)} s`;
}

// Formatear tokens
function formatearTokens(tokens?: number): string {
  if (!tokens) return '-';
  if (tokens >= 1000) return `${(tokens / 1000).toFixed(1)}k`;
  return tokens.toString();
}
</script>

<template>
  <div>
    <!-- Loading -->
    <div v-if="cargando" class="flex justify-center p-8">
      <LoadingSpinner size="md" text="Cargando trazabilidad..." />
    </div>

    <!-- Sin auditoría -->
    <div v-else-if="!auditoria">
      <EmptyState
        titulo="Sin trazabilidad"
        descripcion="No hay registro de auditoría disponible para este análisis."
        icono="document"
      />
    </div>

    <!-- Contenido de auditoría -->
    <div v-else class="space-y-4">
      <!-- Header con checksum y fecha -->
      <div class="alert alert-info">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="stroke-current shrink-0 w-6 h-6">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
        </svg>
        <div>
          <div class="font-semibold">Registro de Trazabilidad</div>
          <div class="text-xs opacity-80">
            Checksum: <code class="bg-base-300 px-1 rounded">{{ auditoria.checksum_datos_entrada }}</code>
          </div>
          <div class="text-xs opacity-80">
            Generado: {{ formatearFecha(auditoria.created_at) }}
          </div>
        </div>
      </div>

      <!-- Métricas de ejecución -->
      <div class="stats stats-vertical lg:stats-horizontal shadow w-full">
        <div class="stat">
          <div class="stat-title">Tiempo GIS</div>
          <div class="stat-value text-lg">{{ formatearTiempo(auditoria.tiempo_gis_ms) }}</div>
          <div class="stat-desc">Análisis espacial</div>
        </div>
        <div class="stat">
          <div class="stat-title">Tiempo RAG</div>
          <div class="stat-value text-lg">{{ formatearTiempo(auditoria.tiempo_rag_ms) }}</div>
          <div class="stat-desc">Búsqueda normativa</div>
        </div>
        <div class="stat">
          <div class="stat-title">Tiempo LLM</div>
          <div class="stat-value text-lg">{{ formatearTiempo(auditoria.tiempo_llm_ms) }}</div>
          <div class="stat-desc">Generación informe</div>
        </div>
        <div class="stat">
          <div class="stat-title">Tokens</div>
          <div class="stat-value text-lg">{{ formatearTokens(auditoria.tokens_usados) }}</div>
          <div class="stat-desc">Consumidos</div>
        </div>
      </div>

      <!-- Capas GIS consultadas -->
      <div class="collapse collapse-arrow bg-base-200">
        <input type="checkbox" checked />
        <div class="collapse-title font-medium">
          Capas GIS Consultadas
          <span class="badge badge-sm badge-neutral ml-2">{{ auditoria.capas_gis_usadas.length }}</span>
        </div>
        <div class="collapse-content">
          <div v-if="auditoria.capas_gis_usadas.length === 0" class="text-sm opacity-60">
            No se consultaron capas GIS
          </div>
          <div v-else class="overflow-x-auto">
            <table class="table table-sm">
              <thead>
                <tr>
                  <th>Capa</th>
                  <th>Fecha datos</th>
                  <th>Versión</th>
                  <th>Elementos</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="capa in auditoria.capas_gis_usadas" :key="capa.nombre">
                  <td class="font-medium">{{ capa.nombre }}</td>
                  <td>{{ capa.fecha }}</td>
                  <td>
                    <span v-if="capa.version" class="badge badge-sm badge-ghost">v{{ capa.version }}</span>
                    <span v-else class="opacity-50">-</span>
                  </td>
                  <td>
                    <span class="badge badge-sm" :class="capa.elementos_encontrados > 0 ? 'badge-warning' : 'badge-success'">
                      {{ capa.elementos_encontrados }}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- Normativa citada -->
      <div class="collapse collapse-arrow bg-base-200">
        <input type="checkbox" checked />
        <div class="collapse-title font-medium">
          Normativa Citada
          <span class="badge badge-sm badge-neutral ml-2">{{ auditoria.normativa_citada.length }}</span>
        </div>
        <div class="collapse-content">
          <div v-if="auditoria.normativa_citada.length === 0" class="text-sm opacity-60">
            No se citó normativa específica
          </div>
          <div v-else class="space-y-2">
            <div
              v-for="(norma, idx) in auditoria.normativa_citada"
              :key="idx"
              class="flex items-start gap-2 p-2 bg-base-100 rounded-lg"
            >
              <span class="badge badge-primary badge-sm shrink-0">
                {{ norma.tipo }} {{ norma.numero }}
              </span>
              <div class="flex-1 min-w-0">
                <div class="text-sm">
                  <span v-if="norma.articulo">Art. {{ norma.articulo }}</span>
                  <span v-if="norma.letra" class="ml-1">letra {{ norma.letra }})</span>
                </div>
                <div v-if="norma.descripcion" class="text-xs opacity-70 truncate">
                  {{ norma.descripcion }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Documentos referenciados -->
      <div v-if="auditoria.documentos_referenciados.length > 0" class="collapse collapse-arrow bg-base-200">
        <input type="checkbox" />
        <div class="collapse-title font-medium">
          Documentos RAG Utilizados
          <span class="badge badge-sm badge-neutral ml-2">{{ auditoria.documentos_referenciados.length }}</span>
        </div>
        <div class="collapse-content">
          <ul class="list-disc list-inside text-sm space-y-1">
            <li v-for="docId in auditoria.documentos_referenciados" :key="docId" class="font-mono text-xs">
              {{ docId }}
            </li>
          </ul>
        </div>
      </div>

      <!-- Información del sistema -->
      <div class="collapse collapse-arrow bg-base-200">
        <input type="checkbox" />
        <div class="collapse-title font-medium">
          Información del Sistema
        </div>
        <div class="collapse-content">
          <div class="grid grid-cols-2 gap-2 text-sm">
            <div class="opacity-70">Versión Sistema:</div>
            <div class="font-mono">{{ auditoria.version_sistema || '-' }}</div>
            <div class="opacity-70">Modelo LLM:</div>
            <div class="font-mono">{{ auditoria.version_modelo_llm || 'No utilizado' }}</div>
            <div class="opacity-70">ID Análisis:</div>
            <div class="font-mono">{{ auditoria.analisis_id }}</div>
            <div class="opacity-70">ID Auditoría:</div>
            <div class="font-mono text-xs">{{ auditoria.id }}</div>
          </div>
        </div>
      </div>

      <!-- Disclaimer -->
      <div class="text-xs text-center opacity-50 pt-4">
        Este registro es inmutable y garantiza la trazabilidad del análisis
      </div>
    </div>
  </div>
</template>
