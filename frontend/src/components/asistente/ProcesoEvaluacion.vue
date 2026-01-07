<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { useProcesoEvaluacionStore } from '@/stores/procesoEvaluacion'
import { storeToRefs } from 'pinia'
import {
  PRIORIDAD_COLORS,
  TIPO_OBSERVACION_LABELS,
  OAECAS_MINERIA,
  type ObservacionICSARA,
  type ICSARA,
} from '@/types/procesoEvaluacion'

const props = defineProps<{
  proyectoId: number
}>()

const store = useProcesoEvaluacionStore()
const {
  tieneProceso,
  proceso,
  timeline,
  estadoActual,
  estadoLabel,
  porcentajePlazo,
  diasRestantes,
  diasTranscurridos,
  icsaras,
  totalIcsara,
  icsaraActual,
  totalObservaciones,
  observacionesPendientes,
  observacionesResueltas,
  porcentajeObservacionesResueltas,
  observacionesPorOAECA,
  oaecaCriticos,
  totalAdendas,
  proximaAccion,
  fechaLimite,
  alerta,
  estadoPlazo,
  tieneAlerta,
  tieneRCA,
  resultadoRCA,
  numeroRCA,
  cargando,
  guardando,
  error,
} = storeToRefs(store)

const tabActiva = ref<'timeline' | 'icsara' | 'estadisticas'>('timeline')
const icsaraSeleccionado = ref<number | null>(null)

// Cargar datos al montar
onMounted(() => {
  if (props.proyectoId) {
    store.cargarProceso(props.proyectoId)
  }
})

watch(() => props.proyectoId, (newId) => {
  if (newId) {
    store.cargarProceso(newId)
  }
})

// Seleccionar ICSARA actual por defecto
watch(icsaraActual, (actual) => {
  if (actual && !icsaraSeleccionado.value) {
    icsaraSeleccionado.value = actual.numero_icsara
  }
})

// Computed
const icsaraSeleccionadoData = computed<ICSARA | null>(() => {
  if (!icsaraSeleccionado.value) return null
  return store.obtenerICSARA(icsaraSeleccionado.value)
})

const observacionesFiltradas = computed<ObservacionICSARA[]>(() => {
  if (!icsaraSeleccionadoData.value) return []
  return icsaraSeleccionadoData.value.observaciones || []
})

// Helpers
function getEstadoColor(estado: string): string {
  const colores: Record<string, string> = {
    completado: 'step-success',
    actual: 'step-primary',
    pendiente: 'step-neutral',
  }
  return colores[estado] || 'step-neutral'
}

function getEstadoIcon(estadoId: string): string {
  const iconos: Record<string, string> = {
    no_ingresado: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z',
    ingresado: 'M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12',
    en_evaluacion: 'M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z',
    icsara_emitido: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z',
    rca_aprobada: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z',
    rca_rechazada: 'M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z',
  }
  return iconos[estadoId] || iconos.no_ingresado
}

function getPrioridadClass(prioridad: string): string {
  return PRIORIDAD_COLORS[prioridad as keyof typeof PRIORIDAD_COLORS] || 'info'
}

function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('es-CL')
}
</script>

<template>
  <div class="proceso-evaluacion h-full flex flex-col">
    <!-- Loading -->
    <div v-if="cargando" class="flex justify-center items-center py-12">
      <span class="loading loading-spinner loading-lg"></span>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="alert alert-error">
      <span>{{ error }}</span>
      <button class="btn btn-sm" @click="store.cargarProceso(proyectoId)">
        Reintentar
      </button>
    </div>

    <!-- Sin proceso - Mostrar estado inicial -->
    <div v-else-if="!tieneProceso" class="flex-1 flex flex-col items-center justify-center py-12">
      <svg
        xmlns="http://www.w3.org/2000/svg"
        class="h-16 w-16 opacity-30 mb-4"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
        />
      </svg>
      <h3 class="text-lg font-semibold mb-2">Proceso No Iniciado</h3>
      <p class="text-sm opacity-70 mb-4 text-center max-w-md">
        El proyecto aun no ha sido ingresado al SEIA.
        El proceso de evaluacion se inicia cuando el proyecto
        es presentado formalmente al Sistema de Evaluacion de Impacto Ambiental.
      </p>
      <div class="badge badge-neutral badge-lg">
        Estado: No ingresado
      </div>
    </div>

    <!-- Proceso existente -->
    <template v-else>
      <!-- Header con estado y plazos -->
      <div class="card bg-base-100 shadow-sm mb-4">
        <div class="card-body p-4">
          <div class="flex flex-wrap items-start justify-between gap-4">
            <!-- Estado actual -->
            <div>
              <div class="flex items-center gap-2 mb-1">
                <span class="text-lg font-bold">{{ estadoLabel }}</span>
                <div
                  v-if="tieneAlerta"
                  class="badge badge-warning badge-sm gap-1"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
                  </svg>
                  {{ alerta }}
                </div>
              </div>
              <p class="text-sm opacity-70">{{ proximaAccion }}</p>
              <p v-if="fechaLimite" class="text-xs opacity-50 mt-1">
                Fecha limite: {{ formatDate(fechaLimite) }}
              </p>
            </div>

            <!-- Widget de plazos -->
            <div class="stats shadow stats-vertical sm:stats-horizontal">
              <div class="stat px-4 py-2">
                <div class="stat-title text-xs">Dias transcurridos</div>
                <div class="stat-value text-xl">{{ diasTranscurridos }}</div>
              </div>
              <div class="stat px-4 py-2">
                <div class="stat-title text-xs">Dias restantes</div>
                <div
                  class="stat-value text-xl"
                  :class="{
                    'text-error': estadoPlazo === 'critico' || estadoPlazo === 'vencido',
                    'text-warning': estadoPlazo === 'alerta',
                    'text-success': estadoPlazo === 'normal',
                  }"
                >
                  {{ diasRestantes }}
                </div>
              </div>
              <div class="stat px-4 py-2">
                <div class="stat-title text-xs">ICSARA</div>
                <div class="stat-value text-xl">{{ totalIcsara }}/2</div>
              </div>
            </div>
          </div>

          <!-- Barra de progreso de plazo -->
          <div class="mt-4">
            <div class="flex justify-between text-xs mb-1">
              <span>Progreso del plazo</span>
              <span>{{ Math.round(porcentajePlazo) }}%</span>
            </div>
            <progress
              class="progress w-full"
              :class="{
                'progress-error': estadoPlazo === 'critico' || estadoPlazo === 'vencido',
                'progress-warning': estadoPlazo === 'alerta',
                'progress-success': estadoPlazo === 'normal',
              }"
              :value="porcentajePlazo"
              max="100"
            ></progress>
          </div>

          <!-- Resumen de observaciones si hay ICSARA -->
          <div v-if="totalObservaciones > 0" class="mt-4 pt-4 border-t border-base-300">
            <div class="flex flex-wrap items-center justify-between gap-2">
              <div>
                <span class="font-semibold">{{ observacionesResueltas }}</span>
                <span class="text-sm opacity-70"> / {{ totalObservaciones }} observaciones resueltas</span>
              </div>
              <div class="flex gap-1">
                <span
                  v-for="oaeca in oaecaCriticos"
                  :key="oaeca"
                  class="badge badge-sm badge-outline"
                >
                  {{ oaeca }}: {{ observacionesPorOAECA[oaeca] }}
                </span>
              </div>
            </div>
            <progress
              class="progress progress-primary w-full mt-2"
              :value="porcentajeObservacionesResueltas"
              max="100"
            ></progress>
          </div>
        </div>
      </div>

      <!-- Tabs -->
      <div class="tabs tabs-boxed mb-4">
        <button
          class="tab"
          :class="{ 'tab-active': tabActiva === 'timeline' }"
          @click="tabActiva = 'timeline'"
        >
          Timeline
        </button>
        <button
          class="tab"
          :class="{ 'tab-active': tabActiva === 'icsara' }"
          @click="tabActiva = 'icsara'"
        >
          ICSARA
          <span v-if="observacionesPendientes > 0" class="badge badge-warning badge-sm ml-1">
            {{ observacionesPendientes }}
          </span>
        </button>
        <button
          class="tab"
          :class="{ 'tab-active': tabActiva === 'estadisticas' }"
          @click="tabActiva = 'estadisticas'"
        >
          Estadisticas
        </button>
      </div>

      <!-- Tab: Timeline -->
      <div v-if="tabActiva === 'timeline'" class="flex-1 overflow-auto">
        <ul class="steps steps-vertical w-full">
          <li
            v-for="estado in timeline?.estados || []"
            :key="estado.id"
            class="step"
            :class="getEstadoColor(estado.estado)"
          >
            <div class="text-left ml-4">
              <div class="font-semibold">{{ estado.nombre }}</div>
              <div class="text-xs opacity-70">{{ estado.descripcion }}</div>
              <div v-if="estado.fecha" class="text-xs opacity-50">
                {{ formatDate(estado.fecha) }}
              </div>
            </div>
          </li>
        </ul>
      </div>

      <!-- Tab: ICSARA -->
      <div v-if="tabActiva === 'icsara'" class="flex-1 overflow-auto">
        <!-- Sin ICSARA -->
        <div v-if="totalIcsara === 0" class="text-center py-8 opacity-70">
          <p>No hay ICSARA emitidos</p>
          <p class="text-sm">Los ICSARA se emiten durante la evaluacion cuando hay observaciones de los organismos.</p>
        </div>

        <!-- Lista de ICSARA -->
        <template v-else>
          <!-- Selector de ICSARA -->
          <div class="flex gap-2 mb-4">
            <button
              v-for="icsara in icsaras"
              :key="icsara.numero_icsara"
              class="btn btn-sm"
              :class="{
                'btn-primary': icsaraSeleccionado === icsara.numero_icsara,
                'btn-outline': icsaraSeleccionado !== icsara.numero_icsara,
              }"
              @click="icsaraSeleccionado = icsara.numero_icsara"
            >
              ICSARA #{{ icsara.numero_icsara }}
              <span class="badge badge-xs ml-1">{{ icsara.total_observaciones }}</span>
            </button>
          </div>

          <!-- Detalle ICSARA seleccionado -->
          <div v-if="icsaraSeleccionadoData" class="space-y-4">
            <!-- Info del ICSARA -->
            <div class="card bg-base-200">
              <div class="card-body p-3">
                <div class="flex flex-wrap justify-between gap-2 text-sm">
                  <div>
                    <span class="opacity-70">Emitido:</span>
                    {{ formatDate(icsaraSeleccionadoData.fecha_emision) }}
                  </div>
                  <div>
                    <span class="opacity-70">Limite respuesta:</span>
                    <span :class="{ 'text-error': icsaraSeleccionadoData.esta_vencido }">
                      {{ formatDate(icsaraSeleccionadoData.fecha_limite_respuesta) }}
                    </span>
                  </div>
                  <div>
                    <span class="opacity-70">Estado:</span>
                    <span class="badge badge-sm ml-1">{{ icsaraSeleccionadoData.estado }}</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Lista de observaciones -->
            <div class="space-y-2">
              <div
                v-for="obs in observacionesFiltradas"
                :key="obs.id"
                class="card bg-base-100 shadow-sm"
              >
                <div class="card-body p-3">
                  <div class="flex items-start justify-between gap-2">
                    <div class="flex-1">
                      <div class="flex items-center gap-2 mb-1">
                        <span class="badge badge-sm">{{ obs.oaeca }}</span>
                        <span class="badge badge-sm badge-outline">Cap. {{ obs.capitulo_eia }}</span>
                        <span
                          class="badge badge-sm"
                          :class="`badge-${getPrioridadClass(obs.prioridad)}`"
                        >
                          {{ obs.prioridad }}
                        </span>
                      </div>
                      <p class="text-sm">{{ obs.texto }}</p>
                      <div class="text-xs opacity-50 mt-1">
                        {{ obs.id }} - {{ TIPO_OBSERVACION_LABELS[obs.tipo] }}
                      </div>
                    </div>
                    <div class="flex-shrink-0">
                      <span
                        class="badge"
                        :class="{
                          'badge-success': obs.estado === 'respondida',
                          'badge-warning': obs.estado === 'parcial',
                          'badge-neutral': obs.estado === 'pendiente',
                        }"
                      >
                        {{ obs.estado }}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Adendas del ICSARA -->
            <div v-if="icsaraSeleccionadoData.adendas?.length" class="mt-4">
              <h4 class="font-semibold mb-2">Adendas presentadas</h4>
              <div class="space-y-2">
                <div
                  v-for="adenda in icsaraSeleccionadoData.adendas"
                  :key="adenda.id"
                  class="card bg-base-200"
                >
                  <div class="card-body p-3">
                    <div class="flex justify-between items-center">
                      <div>
                        <span class="font-semibold">Adenda #{{ adenda.numero_adenda }}</span>
                        <span class="text-sm opacity-70 ml-2">
                          {{ formatDate(adenda.fecha_presentacion) }}
                        </span>
                      </div>
                      <div class="text-sm">
                        <span class="text-success">{{ adenda.observaciones_resueltas }}</span>
                        /
                        <span>{{ adenda.total_respuestas }}</span>
                        resueltas
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </template>
      </div>

      <!-- Tab: Estadisticas -->
      <div v-if="tabActiva === 'estadisticas'" class="flex-1 overflow-auto">
        <div v-if="totalObservaciones === 0" class="text-center py-8 opacity-70">
          <p>No hay estadisticas disponibles</p>
          <p class="text-sm">Las estadisticas se muestran cuando hay observaciones registradas.</p>
        </div>

        <div v-else class="space-y-4">
          <!-- Por organismo -->
          <div class="card bg-base-100 shadow-sm">
            <div class="card-body p-4">
              <h4 class="font-semibold mb-3">Observaciones por Organismo</h4>
              <div class="space-y-2">
                <div
                  v-for="(count, oaeca) in observacionesPorOAECA"
                  :key="oaeca"
                  class="flex items-center gap-2"
                >
                  <span class="w-24 text-sm truncate" :title="OAECAS_MINERIA[oaeca as string]?.nombre_completo || oaeca">
                    {{ oaeca }}
                  </span>
                  <progress
                    class="progress progress-primary flex-1"
                    :value="count"
                    :max="totalObservaciones"
                  ></progress>
                  <span class="text-sm font-mono w-8 text-right">{{ count }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Resumen numerico -->
          <div class="stats shadow w-full">
            <div class="stat">
              <div class="stat-title">Total</div>
              <div class="stat-value text-2xl">{{ totalObservaciones }}</div>
              <div class="stat-desc">observaciones</div>
            </div>
            <div class="stat">
              <div class="stat-title">Resueltas</div>
              <div class="stat-value text-2xl text-success">{{ observacionesResueltas }}</div>
              <div class="stat-desc">{{ porcentajeObservacionesResueltas }}%</div>
            </div>
            <div class="stat">
              <div class="stat-title">Pendientes</div>
              <div class="stat-value text-2xl text-warning">{{ observacionesPendientes }}</div>
              <div class="stat-desc">por resolver</div>
            </div>
            <div class="stat">
              <div class="stat-title">Adendas</div>
              <div class="stat-value text-2xl">{{ totalAdendas }}</div>
              <div class="stat-desc">presentadas</div>
            </div>
          </div>
        </div>
      </div>

      <!-- RCA Final -->
      <div v-if="tieneRCA" class="card bg-base-100 shadow-sm mt-4">
        <div class="card-body p-4">
          <div class="flex items-center gap-3">
            <div
              class="badge badge-lg"
              :class="{
                'badge-success': resultadoRCA === 'favorable' || resultadoRCA === 'favorable_con_condiciones',
                'badge-error': resultadoRCA === 'desfavorable',
              }"
            >
              {{ resultadoRCA === 'favorable' ? 'RCA Favorable' :
                 resultadoRCA === 'favorable_con_condiciones' ? 'RCA Favorable con Condiciones' :
                 'RCA Desfavorable' }}
            </div>
            <span class="text-sm opacity-70">{{ numeroRCA }}</span>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.steps-vertical {
  flex-direction: column;
}

.steps-vertical .step {
  display: flex;
  align-items: flex-start;
  min-height: 4rem;
}
</style>
