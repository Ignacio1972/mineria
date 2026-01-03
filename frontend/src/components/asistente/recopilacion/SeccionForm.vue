<script setup lang="ts">
import { computed } from 'vue'
import PreguntaDinamica from './PreguntaDinamica.vue'
import type { SeccionConPreguntas } from '@/types/recopilacion'
import { ESTADO_SECCION_LABELS, ESTADO_SECCION_COLORS } from '@/types/recopilacion'

const props = defineProps<{
  seccion: SeccionConPreguntas
  respuestasLocales: Record<string, unknown>
  guardando?: boolean
}>()

const emit = defineEmits<{
  (e: 'actualizar-respuesta', codigo: string, valor: unknown): void
  (e: 'guardar'): void
  (e: 'siguiente'): void
  (e: 'anterior'): void
}>()

const preguntasVisibles = computed(() =>
  props.seccion.preguntas.filter((p) => {
    if (!p.condicion_activacion) return true
    // Evaluar condicion
    for (const [campo, valorEsperado] of Object.entries(p.condicion_activacion)) {
      const valorActual =
        props.respuestasLocales[campo] ??
        props.seccion.preguntas.find((pr) => pr.codigo_pregunta === campo)
          ?.respuesta_actual
      if (valorActual !== valorEsperado) return false
    }
    return true
  })
)

const progresoLocal = computed(() => {
  const obligatorias = preguntasVisibles.value.filter((p) => p.es_obligatoria)
  if (obligatorias.length === 0) return 100

  const respondidas = obligatorias.filter((p) => {
    const valor =
      props.respuestasLocales[p.codigo_pregunta] ?? p.respuesta_actual
    return valor !== null && valor !== undefined && valor !== ''
  }).length

  return Math.round((respondidas / obligatorias.length) * 100)
})

function obtenerValor(codigoPregunta: string): unknown {
  return props.respuestasLocales[codigoPregunta] ?? undefined
}
</script>

<template>
  <div class="seccion-form">
    <!-- Header -->
    <div class="flex items-center justify-between mb-4">
      <div>
        <h3 class="font-semibold text-lg">{{ seccion.seccion_nombre }}</h3>
        <p class="text-sm opacity-60">
          {{ preguntasVisibles.length }} preguntas
          <span v-if="seccion.preguntas_obligatorias > 0">
            ({{ seccion.preguntas_obligatorias }} obligatorias)
          </span>
        </p>
      </div>
      <div class="flex items-center gap-2">
        <span
          class="badge"
          :class="ESTADO_SECCION_COLORS[seccion.estado]"
        >
          {{ ESTADO_SECCION_LABELS[seccion.estado] }}
        </span>
        <div
          class="radial-progress text-primary text-xs"
          :style="`--value:${progresoLocal}; --size:2.5rem;`"
          role="progressbar"
        >
          {{ progresoLocal }}%
        </div>
      </div>
    </div>

    <!-- Progreso bar -->
    <progress
      class="progress progress-primary w-full mb-4"
      :value="progresoLocal"
      max="100"
    ></progress>

    <!-- Preguntas -->
    <div class="space-y-4">
      <PreguntaDinamica
        v-for="pregunta in preguntasVisibles"
        :key="pregunta.codigo_pregunta"
        :pregunta="pregunta"
        :model-value="obtenerValor(pregunta.codigo_pregunta)"
        :disabled="guardando"
        @update:model-value="
          (v) => emit('actualizar-respuesta', pregunta.codigo_pregunta, v)
        "
      />
    </div>

    <!-- Acciones -->
    <div class="flex justify-between mt-6 pt-4 border-t border-base-300">
      <button class="btn btn-ghost" @click="emit('anterior')">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          class="h-5 w-5"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M15 19l-7-7 7-7"
          />
        </svg>
        Anterior
      </button>

      <div class="flex gap-2">
        <button
          class="btn btn-primary"
          :disabled="guardando"
          @click="emit('guardar')"
        >
          <span v-if="guardando" class="loading loading-spinner loading-sm"></span>
          <span v-else>Guardar</span>
        </button>

        <button class="btn btn-secondary" @click="emit('siguiente')">
          Siguiente
          <svg
            xmlns="http://www.w3.org/2000/svg"
            class="h-5 w-5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M9 5l7 7-7 7"
            />
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>
