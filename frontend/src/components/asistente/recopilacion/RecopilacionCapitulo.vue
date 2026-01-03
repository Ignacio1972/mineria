<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useRecopilacionStore } from '@/stores/recopilacion'
import ProgresoCapitulos from './ProgresoCapitulos.vue'
import SeccionForm from './SeccionForm.vue'
import InconsistenciasPanel from './InconsistenciasPanel.vue'

const props = defineProps<{
  proyectoId: number
}>()

const store = useRecopilacionStore()
const {
  capituloActual,
  seccionActual,
  secciones,
  inconsistencias,
  respuestasLocales,
  capitulos,
  progresoTotal,
  totalInconsistencias,
  cargando,
  guardando,
  validando,
  error,
} = storeToRefs(store)

const capituloSeleccionado = ref<number>(1)
const mostrarInconsistencias = ref(false)

// Cargar progreso al montar
onMounted(async () => {
  await store.cargarProgreso(props.proyectoId)

  // Si hay capitulos, iniciar el primero
  const primerCapitulo = capitulos.value[0]
  if (primerCapitulo) {
    await seleccionarCapitulo(primerCapitulo.numero)
  }
})

// Recargar si cambia el proyecto
watch(
  () => props.proyectoId,
  async (newId) => {
    if (newId) {
      store.limpiar()
      await store.cargarProgreso(newId)
      const primerCapitulo = capitulos.value[0]
      if (primerCapitulo) {
        await seleccionarCapitulo(primerCapitulo.numero)
      }
    }
  }
)

async function seleccionarCapitulo(numero: number) {
  capituloSeleccionado.value = numero
  await store.iniciarCapitulo(props.proyectoId, numero)
}

async function seleccionarSeccion(codigo: string) {
  await store.seleccionarSeccion(codigo)
}

function actualizarRespuesta(codigo: string, valor: unknown) {
  store.actualizarRespuestaLocal(codigo, valor)
}

async function guardarRespuestas() {
  await store.guardarRespuestas()
}

async function siguienteSeccion() {
  const avanzado = await store.siguienteSeccion()
  if (!avanzado && capituloActual.value) {
    // Fin del capitulo, preguntar si ir al siguiente
    const idx = capitulos.value.findIndex(
      (c) => c.numero === capituloActual.value?.capitulo_numero
    )
    const siguienteCapitulo = capitulos.value[idx + 1]
    if (idx >= 0 && idx < capitulos.value.length - 1 && siguienteCapitulo) {
      await seleccionarCapitulo(siguienteCapitulo.numero)
    }
  }
}

async function seccionAnterior() {
  const retrocedio = await store.seccionAnterior()
  if (!retrocedio && capituloActual.value) {
    // Inicio del capitulo, ir al anterior
    const idx = capitulos.value.findIndex(
      (c) => c.numero === capituloActual.value?.capitulo_numero
    )
    const capituloAnterior = capitulos.value[idx - 1]
    if (idx > 0 && capituloAnterior) {
      await seleccionarCapitulo(capituloAnterior.numero)
    }
  }
}

async function validarConsistencia() {
  await store.validarConsistencia()
  mostrarInconsistencias.value = true
}

async function irASeccion(capitulo: number, seccion: string) {
  await seleccionarCapitulo(capitulo)
  await seleccionarSeccion(seccion)
  mostrarInconsistencias.value = false
}
</script>

<template>
  <div class="recopilacion-capitulo h-full flex flex-col">
    <!-- Loading inicial -->
    <div v-if="cargando && !capituloActual" class="flex justify-center items-center py-12">
      <span class="loading loading-spinner loading-lg"></span>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="alert alert-error">
      <span>{{ error }}</span>
      <button class="btn btn-sm" @click="store.cargarProgreso(proyectoId)">
        Reintentar
      </button>
    </div>

    <!-- Sin capitulos configurados -->
    <div
      v-else-if="capitulos.length === 0"
      class="flex-1 flex flex-col items-center justify-center py-12"
    >
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
          d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
        />
      </svg>
      <h3 class="text-lg font-semibold mb-2">Sin estructura EIA</h3>
      <p class="text-sm opacity-70 text-center max-w-md">
        Primero debes generar la estructura del EIA en la pestana "Estructura EIA"
        para poder iniciar la recopilacion de informacion.
      </p>
    </div>

    <!-- Contenido principal -->
    <template v-else>
      <!-- Header con progreso general -->
      <div class="card bg-base-100 shadow-sm mb-4">
        <div class="card-body p-4">
          <div class="flex flex-wrap items-center justify-between gap-4">
            <div>
              <h2 class="text-lg font-bold">Recopilacion del EIA</h2>
              <p class="text-sm opacity-60">
                Completa la informacion capitulo por capitulo
              </p>
            </div>

            <div class="flex items-center gap-4">
              <!-- Progreso general -->
              <div class="text-center">
                <div
                  class="radial-progress text-primary"
                  :style="`--value:${progresoTotal}; --size:3.5rem;`"
                  role="progressbar"
                >
                  {{ progresoTotal }}%
                </div>
                <div class="text-xs opacity-60 mt-1">Progreso</div>
              </div>

              <!-- Inconsistencias -->
              <button
                class="btn btn-outline btn-sm"
                :class="{ 'btn-warning': totalInconsistencias > 0 }"
                @click="mostrarInconsistencias = !mostrarInconsistencias"
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
                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                  />
                </svg>
                <span v-if="totalInconsistencias > 0">{{ totalInconsistencias }}</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Layout de dos columnas -->
      <div class="flex-1 grid grid-cols-1 lg:grid-cols-4 gap-4 min-h-0">
        <!-- Sidebar: Navegacion de capitulos -->
        <div class="lg:col-span-1 overflow-y-auto">
          <div class="card bg-base-100 shadow-sm h-full">
            <div class="card-body p-3">
              <ProgresoCapitulos
                :capitulos="capitulos"
                :capitulo-actual="capituloActual?.capitulo_numero"
                :seccion-actual="seccionActual?.seccion_codigo"
                :secciones="secciones"
                @seleccionar-capitulo="seleccionarCapitulo"
                @seleccionar-seccion="seleccionarSeccion"
              />
            </div>
          </div>
        </div>

        <!-- Contenido principal -->
        <div class="lg:col-span-3 overflow-y-auto">
          <!-- Panel de inconsistencias (colapsable) -->
          <div
            v-if="mostrarInconsistencias"
            class="card bg-base-100 shadow-sm mb-4"
          >
            <div class="card-body p-4">
              <InconsistenciasPanel
                :inconsistencias="inconsistencias"
                :validando="validando"
                @validar="validarConsistencia"
                @ir-a-seccion="irASeccion"
              />
            </div>
          </div>

          <!-- Mensaje de bienvenida del capitulo -->
          <div
            v-if="capituloActual?.mensaje_bienvenida"
            class="alert alert-info mb-4"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="h-5 w-5 flex-shrink-0"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <span class="text-sm" v-html="capituloActual.mensaje_bienvenida.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')"></span>
          </div>

          <!-- Formulario de seccion -->
          <div class="card bg-base-100 shadow-sm">
            <div class="card-body">
              <div v-if="cargando" class="flex justify-center py-8">
                <span class="loading loading-spinner loading-md"></span>
              </div>

              <SeccionForm
                v-else-if="seccionActual"
                :seccion="seccionActual"
                :respuestas-locales="respuestasLocales"
                :guardando="guardando"
                @actualizar-respuesta="actualizarRespuesta"
                @guardar="guardarRespuestas"
                @siguiente="siguienteSeccion"
                @anterior="seccionAnterior"
              />

              <div v-else class="text-center py-8 opacity-60">
                Selecciona un capitulo y seccion para comenzar
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.recopilacion-capitulo {
  max-height: calc(100vh - 200px);
}
</style>
