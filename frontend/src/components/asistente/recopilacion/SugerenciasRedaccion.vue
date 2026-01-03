<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { post } from '@/services/api'

interface SugerenciaRedaccion {
  seccion_codigo: string
  campo: string
  texto_sugerido: string
  fuente: string
  confianza: number
}

interface SugerenciasResponse {
  sugerencias: SugerenciaRedaccion[]
  total: number
}

const props = defineProps<{
  proyectoId: number
  capituloNumero: number
  seccionCodigo: string
  campo?: string
}>()

const emit = defineEmits<{
  (e: 'aplicar-sugerencia', campo: string, texto: string): void
  (e: 'cerrar'): void
}>()

// Estado
const sugerencias = ref<SugerenciaRedaccion[]>([])
const cargando = ref(false)
const error = ref<string | null>(null)
const contextoAdicional = ref('')

const haySugerencias = computed(() => sugerencias.value.length > 0)

const fuenteLabels: Record<string, string> = {
  corpus_sea: 'Corpus SEA',
  eia_aprobado: 'EIA Aprobados',
  normativa: 'Normativa',
  template: 'Template',
}

const fuenteColors: Record<string, string> = {
  corpus_sea: 'badge-primary',
  eia_aprobado: 'badge-secondary',
  normativa: 'badge-accent',
  template: 'badge-ghost',
}

// Cargar sugerencias al montar o cuando cambian props
watch(
  [() => props.capituloNumero, () => props.seccionCodigo, () => props.campo],
  () => {
    cargarSugerencias()
  },
  { immediate: true }
)

async function cargarSugerencias() {
  cargando.value = true
  error.value = null

  try {
    // El endpoint de sugerencias se maneja via el asistente
    // Por ahora usamos templates basicos
    sugerencias.value = generarSugerenciasLocales()
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Error al cargar sugerencias'
  } finally {
    cargando.value = false
  }
}

async function solicitarSugerenciasIA() {
  cargando.value = true
  error.value = null

  try {
    const response = await post<SugerenciasResponse>(
      `/recopilacion/${props.proyectoId}/sugerencias`,
      {
        capitulo_numero: props.capituloNumero,
        seccion_codigo: props.seccionCodigo,
        campo: props.campo,
        contexto_adicional: contextoAdicional.value || undefined,
      }
    )
    sugerencias.value = response.sugerencias
  } catch (e) {
    // Si el endpoint no existe, usar sugerencias locales
    error.value = 'Sugerencias IA no disponibles. Mostrando templates.'
    sugerencias.value = generarSugerenciasLocales()
  } finally {
    cargando.value = false
  }
}

function generarSugerenciasLocales(): SugerenciaRedaccion[] {
  // Templates basicos por seccion
  const templates: Record<string, SugerenciaRedaccion[]> = {
    antecedentes: [
      {
        seccion_codigo: 'antecedentes',
        campo: 'descripcion_general',
        texto_sugerido:
          'El presente Estudio de Impacto Ambiental (EIA) tiene por objeto describir y evaluar los impactos ambientales asociados al proyecto [NOMBRE], ubicado en [UBICACION], Region de [REGION].',
        fuente: 'template',
        confianza: 0.7,
      },
    ],
    titular: [
      {
        seccion_codigo: 'titular',
        campo: 'representante_legal',
        texto_sugerido:
          'El representante legal de [EMPRESA], con RUT [RUT], sera el responsable de todas las gestiones relacionadas con el presente proyecto ante el Sistema de Evaluacion de Impacto Ambiental.',
        fuente: 'template',
        confianza: 0.7,
      },
    ],
    localizacion: [
      {
        seccion_codigo: 'localizacion',
        campo: 'descripcion_accesos',
        texto_sugerido:
          'El acceso al area del proyecto se realiza a traves de [RUTA], desde la ciudad de [CIUDAD], recorriendo aproximadamente [X] km por camino [TIPO_CAMINO].',
        fuente: 'template',
        confianza: 0.7,
      },
    ],
    clima: [
      {
        seccion_codigo: 'clima',
        campo: 'caracterizacion',
        texto_sugerido:
          'Segun la clasificacion climatica de Koppen, el area de estudio presenta un clima [TIPO_CLIMA], caracterizado por [CARACTERISTICAS]. La temperatura media anual es de [X] grados C, con precipitaciones anuales de [X] mm.',
        fuente: 'corpus_sea',
        confianza: 0.8,
      },
    ],
    flora: [
      {
        seccion_codigo: 'flora',
        campo: 'metodologia',
        texto_sugerido:
          'La caracterizacion de la flora y vegetacion se realizo mediante censos floristicos en transectos de [X] metros, siguiendo la metodologia propuesta por [AUTOR]. Se identificaron las formaciones vegetacionales presentes y se determino el estado de conservacion de las especies segun DS 68/2009 MMA.',
        fuente: 'corpus_sea',
        confianza: 0.85,
      },
    ],
    fauna: [
      {
        seccion_codigo: 'fauna',
        campo: 'metodologia',
        texto_sugerido:
          'La caracterizacion de la fauna terrestre se realizo mediante campanas estacionales, utilizando transectos lineales para aves, trampas Sherman para micromamiferos, y busqueda activa para reptiles. El esfuerzo de muestreo fue de [X] dias/persona.',
        fuente: 'corpus_sea',
        confianza: 0.85,
      },
    ],
    medio_humano: [
      {
        seccion_codigo: 'medio_humano',
        campo: 'caracterizacion',
        texto_sugerido:
          'El area de influencia del proyecto corresponde a la comuna de [COMUNA], con una poblacion de [X] habitantes segun el Censo 2017. Las principales actividades economicas son [ACTIVIDADES].',
        fuente: 'corpus_sea',
        confianza: 0.75,
      },
    ],
  }

  return templates[props.seccionCodigo] || [
    {
      seccion_codigo: props.seccionCodigo,
      campo: 'general',
      texto_sugerido:
        'Ingrese una descripcion detallada de esta seccion, incluyendo metodologia utilizada, resultados obtenidos y fuentes de informacion consultadas.',
      fuente: 'template',
      confianza: 0.5,
    },
  ]
}

function aplicarSugerencia(sugerencia: SugerenciaRedaccion) {
  emit('aplicar-sugerencia', sugerencia.campo, sugerencia.texto_sugerido)
}

function copiarAlPortapapeles(texto: string) {
  navigator.clipboard.writeText(texto)
}

function getConfianzaColor(confianza: number): string {
  if (confianza >= 0.8) return 'text-success'
  if (confianza >= 0.5) return 'text-warning'
  return 'text-error'
}
</script>

<template>
  <div class="sugerencias-redaccion">
    <!-- Header -->
    <div class="flex items-center justify-between mb-4">
      <h3 class="font-semibold text-lg">Sugerencias de Redaccion</h3>
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

    <!-- Info de contexto -->
    <div class="bg-base-200 rounded-lg p-3 mb-4">
      <div class="text-sm">
        <span class="opacity-70">Seccion:</span>
        <span class="ml-2 font-medium">{{ seccionCodigo }}</span>
      </div>
      <div v-if="campo" class="text-sm">
        <span class="opacity-70">Campo:</span>
        <span class="ml-2 font-medium">{{ campo }}</span>
      </div>
    </div>

    <!-- Contexto adicional para IA -->
    <div class="form-control mb-4">
      <label class="label">
        <span class="label-text">Contexto adicional (opcional)</span>
      </label>
      <textarea
        v-model="contextoAdicional"
        class="textarea textarea-bordered h-20"
        placeholder="Describe el contexto del proyecto para sugerencias mas precisas..."
        :disabled="cargando"
      ></textarea>
    </div>

    <!-- Boton solicitar IA -->
    <button
      class="btn btn-outline btn-sm w-full mb-4"
      :disabled="cargando"
      @click="solicitarSugerenciasIA"
    >
      <span v-if="cargando" class="loading loading-spinner loading-xs"></span>
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
          d="M13 10V3L4 14h7v7l9-11h-7z"
        />
      </svg>
      Obtener Sugerencias con IA
    </button>

    <!-- Error -->
    <div v-if="error" class="alert alert-warning mb-4 text-sm">
      {{ error }}
    </div>

    <!-- Loading -->
    <div v-if="cargando" class="flex justify-center py-8">
      <span class="loading loading-spinner loading-lg"></span>
    </div>

    <!-- Sin sugerencias -->
    <div
      v-else-if="!haySugerencias"
      class="text-center py-8 opacity-60"
    >
      <svg
        xmlns="http://www.w3.org/2000/svg"
        class="h-12 w-12 mx-auto mb-2"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
        />
      </svg>
      <p>No hay sugerencias disponibles para esta seccion</p>
    </div>

    <!-- Lista de sugerencias -->
    <div v-else class="space-y-4">
      <div
        v-for="(sug, idx) in sugerencias"
        :key="idx"
        class="card bg-base-200"
      >
        <div class="card-body p-4">
          <!-- Header de sugerencia -->
          <div class="flex items-center justify-between mb-2">
            <div class="flex items-center gap-2">
              <span class="badge badge-sm" :class="fuenteColors[sug.fuente] || 'badge-ghost'">
                {{ fuenteLabels[sug.fuente] || sug.fuente }}
              </span>
              <span class="text-xs" :class="getConfianzaColor(sug.confianza)">
                {{ Math.round(sug.confianza * 100) }}% confianza
              </span>
            </div>
            <span class="text-xs opacity-60">{{ sug.campo }}</span>
          </div>

          <!-- Texto sugerido -->
          <p class="text-sm whitespace-pre-wrap mb-3">
            {{ sug.texto_sugerido }}
          </p>

          <!-- Acciones -->
          <div class="flex gap-2">
            <button
              class="btn btn-primary btn-sm flex-1"
              @click="aplicarSugerencia(sug)"
            >
              <svg
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
                  d="M5 13l4 4L19 7"
                />
              </svg>
              Aplicar
            </button>
            <button
              class="btn btn-ghost btn-sm"
              @click="copiarAlPortapapeles(sug.texto_sugerido)"
            >
              <svg
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
                  d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"
                />
              </svg>
              Copiar
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Nota informativa -->
    <div class="mt-4 text-xs opacity-60 text-center">
      Las sugerencias son orientativas. Adapta el texto a las caracteristicas
      especificas de tu proyecto.
    </div>
  </div>
</template>

<style scoped>
.sugerencias-redaccion {
  max-height: 80vh;
  overflow-y: auto;
}
</style>
