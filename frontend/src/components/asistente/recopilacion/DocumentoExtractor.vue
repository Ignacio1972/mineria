<script setup lang="ts">
import { ref, computed } from 'vue'
import { post } from '@/services/api'
import type {
  ExtraccionDocumento,
  MapeoSeccionSugerido,
  EstadoExtraccion,
} from '@/types/recopilacion'

const props = defineProps<{
  proyectoId: number
  capituloNumero?: number
  seccionCodigo?: string
}>()

const emit = defineEmits<{
  (e: 'extraccion-completada', extraccion: ExtraccionDocumento): void
  (e: 'aplicar-mapeo', mapeo: MapeoSeccionSugerido): void
  (e: 'cerrar'): void
}>()

// Estado
const documentoId = ref<number | null>(null)
const tipoDocumento = ref<string>('')
const extraccion = ref<ExtraccionDocumento | null>(null)
const procesando = ref(false)
const error = ref<string | null>(null)
const mapeosSeleccionados = ref<Set<number>>(new Set())

// Tipos de documento disponibles
const tiposDocumento = [
  { valor: '', etiqueta: 'Detectar automaticamente' },
  { valor: 'informe_climatologico', etiqueta: 'Informe Climatologico' },
  { valor: 'informe_calidad_aire', etiqueta: 'Informe Calidad del Aire' },
  { valor: 'informe_hidrogeologico', etiqueta: 'Informe Hidrogeologico' },
  { valor: 'informe_flora', etiqueta: 'Informe Flora y Vegetacion' },
  { valor: 'informe_fauna', etiqueta: 'Informe Fauna' },
  { valor: 'informe_arqueologico', etiqueta: 'Informe Arqueologico' },
  { valor: 'informe_medio_humano', etiqueta: 'Informe Medio Humano' },
  { valor: 'ficha_proyecto', etiqueta: 'Ficha de Proyecto' },
]

const estadoColors: Record<EstadoExtraccion, string> = {
  pendiente: 'badge-ghost',
  procesando: 'badge-warning',
  completado: 'badge-success',
  error: 'badge-error',
}

const estadoLabels: Record<EstadoExtraccion, string> = {
  pendiente: 'Pendiente',
  procesando: 'Procesando...',
  completado: 'Completado',
  error: 'Error',
}

const hayMapeos = computed(() =>
  extraccion.value && extraccion.value.mapeo_secciones.length > 0
)

const confianzaPromedio = computed(() => {
  if (!extraccion.value || extraccion.value.mapeo_secciones.length === 0) return 0
  const suma = extraccion.value.mapeo_secciones.reduce((acc, m) => acc + m.confianza, 0)
  return Math.round((suma / extraccion.value.mapeo_secciones.length) * 100)
})

async function extraerDatos() {
  if (!documentoId.value) {
    error.value = 'Selecciona un documento'
    return
  }

  procesando.value = true
  error.value = null

  try {
    extraccion.value = await post<ExtraccionDocumento>(
      `/recopilacion/${props.proyectoId}/extraer-documento`,
      {
        documento_id: documentoId.value,
        tipo_documento: tipoDocumento.value || undefined,
        forzar_reprocesar: false,
      }
    )

    // Seleccionar todos los mapeos por defecto
    mapeosSeleccionados.value = new Set(
      extraccion.value.mapeo_secciones.map((_, i) => i)
    )

    emit('extraccion-completada', extraccion.value)
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Error al extraer datos'
  } finally {
    procesando.value = false
  }
}

function toggleMapeo(index: number) {
  if (mapeosSeleccionados.value.has(index)) {
    mapeosSeleccionados.value.delete(index)
  } else {
    mapeosSeleccionados.value.add(index)
  }
  // Forzar reactividad
  mapeosSeleccionados.value = new Set(mapeosSeleccionados.value)
}

function aplicarMapeosSeleccionados() {
  if (!extraccion.value) return

  for (const index of mapeosSeleccionados.value) {
    const mapeo = extraccion.value.mapeo_secciones[index]
    if (mapeo) {
      emit('aplicar-mapeo', mapeo)
    }
  }
}

function formatearValor(valor: unknown): string {
  if (valor === null || valor === undefined) return '-'
  if (typeof valor === 'object') return JSON.stringify(valor, null, 2)
  return String(valor)
}

function getConfianzaColor(confianza: number): string {
  if (confianza >= 0.8) return 'text-success'
  if (confianza >= 0.5) return 'text-warning'
  return 'text-error'
}
</script>

<template>
  <div class="documento-extractor">
    <!-- Header -->
    <div class="flex items-center justify-between mb-4">
      <h3 class="font-semibold text-lg">Extractor de Documentos</h3>
      <button class="btn btn-sm btn-ghost btn-circle" @click="emit('cerrar')">
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
            d="M6 18L18 6M6 6l12 12"
          />
        </svg>
      </button>
    </div>

    <!-- Formulario de extraccion -->
    <div v-if="!extraccion" class="space-y-4">
      <p class="text-sm opacity-70">
        Extrae datos de documentos tecnicos usando IA. El sistema identificara
        automaticamente el tipo de documento y extraera la informacion relevante
        para el EIA.
      </p>

      <!-- ID Documento -->
      <div class="form-control">
        <label class="label">
          <span class="label-text">ID del Documento</span>
        </label>
        <input
          v-model.number="documentoId"
          type="number"
          class="input input-bordered w-full"
          placeholder="Ingresa el ID del documento"
          :disabled="procesando"
        />
      </div>

      <!-- Tipo documento -->
      <div class="form-control">
        <label class="label">
          <span class="label-text">Tipo de Documento</span>
        </label>
        <select
          v-model="tipoDocumento"
          class="select select-bordered w-full"
          :disabled="procesando"
        >
          <option
            v-for="tipo in tiposDocumento"
            :key="tipo.valor"
            :value="tipo.valor"
          >
            {{ tipo.etiqueta }}
          </option>
        </select>
        <label class="label">
          <span class="label-text-alt opacity-60">
            Deja vacio para deteccion automatica
          </span>
        </label>
      </div>

      <!-- Error -->
      <div v-if="error" class="alert alert-error">
        <span>{{ error }}</span>
      </div>

      <!-- Boton extraer -->
      <button
        class="btn btn-primary w-full"
        :disabled="procesando || !documentoId"
        @click="extraerDatos"
      >
        <span v-if="procesando" class="loading loading-spinner loading-sm"></span>
        <svg
          v-else
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
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
          />
        </svg>
        {{ procesando ? 'Extrayendo...' : 'Extraer Datos' }}
      </button>
    </div>

    <!-- Resultados de extraccion -->
    <div v-else class="space-y-4">
      <!-- Estado y confianza -->
      <div class="flex items-center justify-between">
        <span class="badge" :class="estadoColors[extraccion.estado]">
          {{ estadoLabels[extraccion.estado] }}
        </span>
        <div class="flex items-center gap-2">
          <span class="text-sm opacity-70">Confianza:</span>
          <span class="font-semibold" :class="getConfianzaColor(confianzaPromedio / 100)">
            {{ confianzaPromedio }}%
          </span>
        </div>
      </div>

      <!-- Tipo detectado -->
      <div v-if="extraccion.tipo_documento" class="text-sm">
        <span class="opacity-70">Tipo detectado:</span>
        <span class="ml-2 font-medium">{{ extraccion.tipo_documento }}</span>
      </div>

      <!-- Datos extraidos -->
      <div class="collapse collapse-arrow bg-base-200">
        <input type="checkbox" />
        <div class="collapse-title font-medium">
          Datos Extraidos ({{ Object.keys(extraccion.datos_extraidos).length }})
        </div>
        <div class="collapse-content">
          <div class="overflow-x-auto">
            <table class="table table-xs">
              <thead>
                <tr>
                  <th>Campo</th>
                  <th>Valor</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="(valor, campo) in extraccion.datos_extraidos"
                  :key="String(campo)"
                >
                  <td class="font-medium">{{ campo }}</td>
                  <td class="text-sm">
                    <pre class="whitespace-pre-wrap">{{ formatearValor(valor) }}</pre>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- Mapeos sugeridos -->
      <div v-if="hayMapeos">
        <h4 class="font-medium mb-2">Mapeo a Secciones del EIA</h4>
        <p class="text-sm opacity-70 mb-3">
          Selecciona los campos que deseas aplicar a las secciones correspondientes.
        </p>

        <div class="space-y-2 max-h-64 overflow-y-auto">
          <label
            v-for="(mapeo, idx) in extraccion.mapeo_secciones"
            :key="idx"
            class="flex items-start gap-3 p-2 rounded hover:bg-base-200 cursor-pointer"
          >
            <input
              type="checkbox"
              class="checkbox checkbox-sm mt-1"
              :checked="mapeosSeleccionados.has(idx)"
              @change="toggleMapeo(idx)"
            />
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2">
                <span class="font-medium text-sm">{{ mapeo.campo }}</span>
                <span
                  class="text-xs"
                  :class="getConfianzaColor(mapeo.confianza)"
                >
                  {{ Math.round(mapeo.confianza * 100) }}%
                </span>
              </div>
              <div class="text-xs opacity-60">
                Cap. {{ mapeo.capitulo_numero }} - {{ mapeo.seccion_codigo }}
              </div>
              <div class="text-sm truncate">{{ formatearValor(mapeo.valor) }}</div>
            </div>
          </label>
        </div>

        <!-- Acciones -->
        <div class="flex gap-2 mt-4">
          <button
            class="btn btn-primary flex-1"
            :disabled="mapeosSeleccionados.size === 0"
            @click="aplicarMapeosSeleccionados"
          >
            Aplicar Seleccionados ({{ mapeosSeleccionados.size }})
          </button>
          <button
            class="btn btn-ghost"
            @click="extraccion = null"
          >
            Nueva Extraccion
          </button>
        </div>
      </div>

      <!-- Sin mapeos -->
      <div v-else class="text-center py-4 opacity-60">
        <p>No se generaron mapeos automaticos</p>
        <button class="btn btn-sm btn-ghost mt-2" @click="extraccion = null">
          Intentar de nuevo
        </button>
      </div>

      <!-- Errores de extraccion -->
      <div v-if="extraccion.errores && extraccion.errores.length > 0">
        <div
          v-for="(err, idx) in extraccion.errores"
          :key="idx"
          class="alert alert-warning text-sm"
        >
          {{ err }}
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.documento-extractor {
  max-height: 80vh;
  overflow-y: auto;
}
</style>
