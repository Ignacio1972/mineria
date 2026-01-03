<script setup lang="ts">
import type { InconsistenciaDetectada } from '@/types/recopilacion'
import { SEVERIDAD_COLORS } from '@/types/recopilacion'

defineProps<{
  inconsistencias: InconsistenciaDetectada[]
  validando?: boolean
}>()

const emit = defineEmits<{
  (e: 'validar'): void
  (e: 'ir-a-seccion', capitulo: number, seccion: string): void
}>()
</script>

<template>
  <div class="inconsistencias-panel">
    <!-- Header -->
    <div class="flex items-center justify-between mb-4">
      <h3 class="font-semibold">
        Inconsistencias
        <span v-if="inconsistencias.length > 0" class="badge badge-warning ml-2">
          {{ inconsistencias.length }}
        </span>
      </h3>
      <button
        class="btn btn-sm btn-outline"
        :disabled="validando"
        @click="emit('validar')"
      >
        <span v-if="validando" class="loading loading-spinner loading-xs"></span>
        <svg
          v-else
          xmlns="http://www.w3.org/2000/svg"
          class="h-4 w-4"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
        Validar
      </button>
    </div>

    <!-- Sin inconsistencias -->
    <div
      v-if="inconsistencias.length === 0"
      class="text-center py-8 opacity-60"
    >
      <svg
        xmlns="http://www.w3.org/2000/svg"
        class="h-12 w-12 mx-auto mb-2 text-success"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
      <p>Sin inconsistencias detectadas</p>
    </div>

    <!-- Lista de inconsistencias -->
    <div v-else class="space-y-3">
      <div
        v-for="(inc, idx) in inconsistencias"
        :key="idx"
        class="alert"
        :class="SEVERIDAD_COLORS[inc.severidad]"
      >
        <div class="flex-1">
          <div class="font-medium text-sm">{{ inc.regla_nombre }}</div>
          <p class="text-sm opacity-80">{{ inc.mensaje }}</p>
          <div class="flex gap-4 mt-2 text-xs opacity-70">
            <button
              class="link"
              @click="emit('ir-a-seccion', inc.capitulo_origen, inc.seccion_origen)"
            >
              Cap. {{ inc.capitulo_origen }} - {{ inc.seccion_origen }}
            </button>
            <span>vs</span>
            <button
              class="link"
              @click="emit('ir-a-seccion', inc.capitulo_destino, inc.seccion_destino)"
            >
              Cap. {{ inc.capitulo_destino }} - {{ inc.seccion_destino }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
