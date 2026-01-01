<script setup lang="ts">
import { computed } from 'vue';
import { useAnalysisStore } from '@/stores/analysis';
import SeverityBadge from '@/components/common/SeverityBadge.vue';
import EmptyState from '@/components/common/EmptyState.vue';

const analysisStore = useAnalysisStore();

const triggers = computed(() =>
  [...analysisStore.triggers].sort((a, b) => b.peso - a.peso)
);

const letrasDescripcion: Record<string, string> = {
  a: 'Riesgo para la salud de la población',
  b: 'Efectos adversos sobre recursos naturales',
  c: 'Reasentamiento de comunidades o alteración de sistemas de vida',
  d: 'Localización en áreas protegidas',
  e: 'Alteración de monumentos o patrimonio',
  f: 'Alteración del valor paisajístico o turístico',
};
</script>

<template>
  <div>
    <div v-if="triggers.length === 0">
      <EmptyState
        titulo="Sin triggers detectados"
        descripcion="No se detectaron triggers del Art. 11 que requieran EIA."
        icono="search"
      />
    </div>

    <div v-else class="space-y-4">
      <div class="alert alert-warning">
        <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        <div>
          <h3 class="font-bold">Se detectaron {{ triggers.length }} trigger(s) del Art. 11</h3>
          <div class="text-sm">
            Estos efectos requieren la presentación de un Estudio de Impacto Ambiental (EIA).
          </div>
        </div>
      </div>

      <div class="space-y-3">
        <div
          v-for="trigger in triggers"
          :key="trigger.letra"
          class="card bg-base-200"
        >
          <div class="card-body p-4">
            <div class="flex items-start justify-between">
              <div class="flex items-center gap-3">
                <div class="avatar placeholder">
                  <div class="bg-warning text-warning-content rounded-full w-10">
                    <span class="text-xl font-bold">{{ trigger.letra }}</span>
                  </div>
                </div>
                <div>
                  <h4 class="font-semibold">{{ letrasDescripcion[trigger.letra] }}</h4>
                  <p class="text-sm opacity-70">Art. 11 letra {{ trigger.letra }})</p>
                </div>
              </div>
              <SeverityBadge :severidad="trigger.severidad" size="sm" />
            </div>

            <div class="mt-3 space-y-2">
              <div>
                <span class="text-xs font-semibold uppercase opacity-60">Detalle</span>
                <p class="text-sm">{{ trigger.detalle }}</p>
              </div>

              <div>
                <span class="text-xs font-semibold uppercase opacity-60">Fundamento Legal</span>
                <p class="text-sm">{{ trigger.fundamento_legal }}</p>
              </div>

              <div class="flex items-center gap-2">
                <span class="text-xs font-semibold uppercase opacity-60">Peso:</span>
                <progress
                  class="progress progress-warning w-24"
                  :value="trigger.peso"
                  max="100"
                ></progress>
                <span class="text-xs">{{ trigger.peso }}%</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
