<script setup lang="ts">
import { computed } from 'vue'
import type { CapituloProgreso, SeccionConPreguntas } from '@/types/recopilacion'
import { ESTADO_SECCION_COLORS } from '@/types/recopilacion'

const props = defineProps<{
  capitulos: CapituloProgreso[]
  capituloActual?: number
  seccionActual?: string
  secciones?: SeccionConPreguntas[]
}>()

const emit = defineEmits<{
  (e: 'seleccionar-capitulo', numero: number): void
  (e: 'seleccionar-seccion', codigo: string): void
}>()

const capituloSeleccionado = computed(() =>
  props.capitulos.find((c) => c.numero === props.capituloActual)
)

function getEstadoIcon(estado: string): string {
  switch (estado) {
    case 'completado':
      return 'M5 13l4 4L19 7'
    case 'en_progreso':
      return 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z'
    case 'validado':
      return 'M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z'
    default:
      return 'M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z'
  }
}

function getEstadoColor(estado: string): string {
  switch (estado) {
    case 'completado':
      return 'text-success'
    case 'en_progreso':
      return 'text-warning'
    case 'validado':
      return 'text-info'
    default:
      return 'text-base-content/40'
  }
}
</script>

<template>
  <div class="progreso-capitulos">
    <!-- Lista de capitulos -->
    <div class="space-y-2">
      <div
        v-for="capitulo in capitulos"
        :key="capitulo.numero"
        class="collapse collapse-arrow bg-base-200 rounded-lg"
        :class="{ 'ring-2 ring-primary': capitulo.numero === capituloActual }"
      >
        <input
          type="radio"
          name="capitulo-accordion"
          :checked="capitulo.numero === capituloActual"
          @change="emit('seleccionar-capitulo', capitulo.numero)"
        />

        <!-- Header del capitulo -->
        <div class="collapse-title pr-8">
          <div class="flex items-center gap-3">
            <!-- Icono estado -->
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="h-5 w-5 flex-shrink-0"
              :class="getEstadoColor(capitulo.estado)"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                :d="getEstadoIcon(capitulo.estado)"
              />
            </svg>

            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2">
                <span class="font-medium">Cap. {{ capitulo.numero }}</span>
                <span class="text-sm opacity-70 truncate">{{ capitulo.titulo }}</span>
              </div>
              <div class="flex items-center gap-2 mt-1">
                <progress
                  class="progress progress-primary w-20 h-1"
                  :value="capitulo.progreso"
                  max="100"
                ></progress>
                <span class="text-xs opacity-60">{{ capitulo.progreso }}%</span>
              </div>
            </div>

            <!-- Badge inconsistencias -->
            <span
              v-if="capitulo.tiene_inconsistencias"
              class="badge badge-warning badge-sm"
              title="Tiene inconsistencias"
            >
              !
            </span>
          </div>
        </div>

        <!-- Secciones del capitulo -->
        <div class="collapse-content">
          <ul class="menu menu-sm bg-base-100 rounded-lg mt-2">
            <li
              v-for="seccion in capitulo.numero === capituloActual && secciones
                ? secciones
                : capitulo.secciones"
              :key="seccion.seccion_codigo"
            >
              <a
                :class="{
                  active: seccion.seccion_codigo === seccionActual,
                  'opacity-60': seccion.estado === 'pendiente',
                }"
                @click="emit('seleccionar-seccion', seccion.seccion_codigo)"
              >
                <span
                  class="badge badge-xs"
                  :class="ESTADO_SECCION_COLORS[seccion.estado]"
                ></span>
                <span class="flex-1 truncate">{{ seccion.seccion_nombre || seccion.seccion_codigo }}</span>
                <span class="text-xs opacity-60">{{ seccion.progreso }}%</span>
              </a>
            </li>
          </ul>
        </div>
      </div>
    </div>

    <!-- Resumen si hay capitulo seleccionado -->
    <div
      v-if="capituloSeleccionado"
      class="mt-4 p-3 bg-base-200 rounded-lg text-sm"
    >
      <div class="flex justify-between mb-2">
        <span>Secciones completadas</span>
        <span class="font-medium">
          {{ capituloSeleccionado.secciones_completadas }}/{{
            capituloSeleccionado.total_secciones
          }}
        </span>
      </div>
      <div class="flex justify-between">
        <span>Progreso capitulo</span>
        <span class="font-medium">{{ capituloSeleccionado.progreso }}%</span>
      </div>
    </div>
  </div>
</template>
