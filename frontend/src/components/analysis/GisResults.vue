<script setup lang="ts">
import { computed } from 'vue';
import { useAnalysisStore } from '@/stores/analysis';
import EmptyState from '@/components/common/EmptyState.vue';

const analysisStore = useAnalysisStore();

const resultadoGis = computed(() => analysisStore.resultado?.resultado_gis);
const intersecciones = computed(() => resultadoGis.value?.intersecciones || []);
</script>

<template>
  <div>
    <div v-if="!resultadoGis">
      <EmptyState
        titulo="Sin resultados GIS"
        descripcion="No hay resultados de análisis espacial disponibles."
        icono="map"
      />
    </div>

    <div v-else class="space-y-4">
      <!-- Resumen del proyecto -->
      <div class="stats shadow w-full">
        <div class="stat">
          <div class="stat-title">Área del proyecto</div>
          <div class="stat-value text-xl">{{ resultadoGis.area_proyecto_ha?.toFixed(2) || '-' }}</div>
          <div class="stat-desc">hectáreas</div>
        </div>
        <div class="stat">
          <div class="stat-title">Centroide</div>
          <div class="stat-value text-sm">
            {{ resultadoGis.centroide?.[1]?.toFixed(4) || '-' }},
            {{ resultadoGis.centroide?.[0]?.toFixed(4) || '-' }}
          </div>
          <div class="stat-desc">lat, lon</div>
        </div>
        <div class="stat">
          <div class="stat-title">Intersecciones</div>
          <div class="stat-value text-xl">{{ intersecciones.length }}</div>
          <div class="stat-desc">capas afectadas</div>
        </div>
      </div>

      <!-- Tabla de intersecciones -->
      <div v-if="intersecciones.length > 0" class="overflow-x-auto">
        <table class="table table-sm">
          <thead>
            <tr>
              <th>Capa</th>
              <th>Elemento</th>
              <th>Estado</th>
              <th>Área afectada</th>
              <th>Distancia</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(int, idx) in intersecciones" :key="idx">
              <td class="font-medium">{{ int.capa }}</td>
              <td>{{ int.nombre_elemento || '-' }}</td>
              <td>
                <span
                  class="badge badge-sm"
                  :class="int.dentro ? 'badge-error' : 'badge-warning'"
                >
                  {{ int.dentro ? 'Dentro' : 'Cercano' }}
                </span>
              </td>
              <td>
                <span v-if="int.area_afectada_ha">
                  {{ int.area_afectada_ha.toFixed(2) }} ha
                  <span v-if="int.porcentaje_interseccion" class="opacity-60">
                    ({{ (int.porcentaje_interseccion * 100).toFixed(1) }}%)
                  </span>
                </span>
                <span v-else class="opacity-50">-</span>
              </td>
              <td>
                <span v-if="int.distancia_metros !== undefined">
                  {{ int.distancia_metros < 1000
                    ? `${int.distancia_metros.toFixed(0)} m`
                    : `${(int.distancia_metros / 1000).toFixed(1)} km`
                  }}
                </span>
                <span v-else class="opacity-50">-</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Alertas GIS -->
      <div v-if="resultadoGis.alertas_gis?.length > 0" class="space-y-2">
        <h4 class="font-semibold text-sm">Alertas del Análisis Espacial</h4>
        <div class="space-y-1">
          <div
            v-for="(alerta, idx) in resultadoGis.alertas_gis"
            :key="idx"
            class="alert alert-warning py-2"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-5 w-5" fill="none" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <span class="text-sm">{{ alerta }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
