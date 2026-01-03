<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useGeneracionEiaStore } from '@/stores/generacionEia'
import { storeToRefs } from 'pinia'

const props = defineProps<{
  proyectoId: number
}>()

const store = useGeneracionEiaStore()
const {
  versiones,
  documento,
  guardando,
} = storeToRefs(store)

const mostrarModalCrear = ref(false)
const mostrarModalRestaurar = ref(false)
const versionARestaurar = ref<number | null>(null)
const descripcionCambios = ref('')

// Versiones ordenadas por mas reciente
const versionesOrdenadas = computed(() => {
  return [...versiones.value].sort((a, b) => b.version - a.version)
})

// Version actual del documento
const versionActual = computed(() => documento.value?.version ?? 0)

// Acciones
async function crearVersion() {
  if (!descripcionCambios.value.trim()) return

  mostrarModalCrear.value = false
  try {
    await store.crearVersion(descripcionCambios.value)
    descripcionCambios.value = ''
  } catch (e) {
    console.error('Error creando version:', e)
  }
}

async function restaurarVersion() {
  if (versionARestaurar.value === null) return

  mostrarModalRestaurar.value = false
  try {
    await store.restaurarVersion(versionARestaurar.value)
    versionARestaurar.value = null
  } catch (e) {
    console.error('Error restaurando version:', e)
  }
}

function abrirModalCrear() {
  descripcionCambios.value = ''
  mostrarModalCrear.value = true
}

function abrirModalRestaurar(version: number) {
  versionARestaurar.value = version
  mostrarModalRestaurar.value = true
}

function formatearFecha(fecha: string): string {
  const d = new Date(fecha)
  return d.toLocaleDateString('es-CL', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

onMounted(() => {
  store.cargarVersiones()
})
</script>

<template>
  <div class="versiones-panel p-4">
    <!-- Header -->
    <div class="flex items-center justify-between mb-4">
      <div>
        <h3 class="font-bold text-lg">Historial de Versiones</h3>
        <p class="text-sm opacity-60">
          Version actual: {{ versionActual }}
        </p>
      </div>
      <button
        class="btn btn-primary btn-sm"
        @click="abrirModalCrear"
      >
        Crear Version
      </button>
    </div>

    <!-- Lista de versiones -->
    <div v-if="versionesOrdenadas.length === 0" class="text-center py-8 opacity-60">
      <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 mx-auto mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <p>No hay versiones guardadas</p>
      <p class="text-xs mt-1">Crea una version para guardar el estado actual del documento</p>
    </div>

    <div v-else class="relative">
      <!-- Linea del timeline -->
      <div class="absolute left-4 top-0 bottom-0 w-0.5 bg-base-300"></div>

      <!-- Versiones -->
      <div class="space-y-4">
        <div
          v-for="version in versionesOrdenadas"
          :key="version.id"
          class="relative pl-10"
        >
          <!-- Punto del timeline -->
          <div
            class="absolute left-2 w-5 h-5 rounded-full border-2 bg-base-100"
            :class="{
              'border-primary bg-primary': version.version === versionActual,
              'border-base-300': version.version !== versionActual,
            }"
          ></div>

          <!-- Card de version -->
          <div
            class="card bg-base-100 shadow-sm"
            :class="{ 'ring-2 ring-primary': version.version === versionActual }"
          >
            <div class="card-body p-3">
              <div class="flex items-start justify-between gap-2">
                <div class="flex-1">
                  <div class="flex items-center gap-2">
                    <span class="font-bold">Version {{ version.version }}</span>
                    <span
                      v-if="version.version === versionActual"
                      class="badge badge-primary badge-sm"
                    >
                      Actual
                    </span>
                  </div>
                  <p class="text-sm mt-1">{{ version.cambios }}</p>
                  <div class="text-xs opacity-60 mt-2">
                    {{ formatearFecha(version.created_at) }}
                    <span v-if="version.creado_por"> - {{ version.creado_por }}</span>
                  </div>
                </div>

                <!-- Boton restaurar -->
                <button
                  v-if="version.version !== versionActual"
                  class="btn btn-ghost btn-xs"
                  title="Restaurar esta version"
                  @click="abrirModalRestaurar(version.version)"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal Crear Version -->
    <dialog
      class="modal"
      :class="{ 'modal-open': mostrarModalCrear }"
    >
      <div class="modal-box">
        <h3 class="font-bold text-lg mb-4">Crear Nueva Version</h3>

        <p class="text-sm opacity-70 mb-4">
          Esto guardara el estado actual del documento como una nueva version.
          Podras restaurar esta version mas adelante si es necesario.
        </p>

        <div class="form-control mb-4">
          <label class="label">
            <span class="label-text">Descripcion de los cambios</span>
          </label>
          <textarea
            v-model="descripcionCambios"
            class="textarea textarea-bordered"
            rows="3"
            placeholder="Ej: Completado capitulo 3 de descripcion del proyecto..."
            required
          ></textarea>
        </div>

        <div class="modal-action">
          <button class="btn btn-ghost" @click="mostrarModalCrear = false">
            Cancelar
          </button>
          <button
            class="btn btn-primary"
            :disabled="guardando || !descripcionCambios.trim()"
            @click="crearVersion"
          >
            <span v-if="guardando" class="loading loading-spinner loading-sm"></span>
            <span v-else>Crear Version</span>
          </button>
        </div>
      </div>
      <form method="dialog" class="modal-backdrop">
        <button @click="mostrarModalCrear = false">close</button>
      </form>
    </dialog>

    <!-- Modal Restaurar -->
    <dialog
      class="modal"
      :class="{ 'modal-open': mostrarModalRestaurar }"
    >
      <div class="modal-box">
        <h3 class="font-bold text-lg mb-4">Restaurar Version</h3>

        <div class="alert alert-warning mb-4">
          <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-5 w-5" fill="none" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <span>Esto reemplazara el contenido actual del documento con la version {{ versionARestaurar }}.</span>
        </div>

        <p class="text-sm opacity-70">
          Se recomienda crear una nueva version antes de restaurar para no perder cambios.
        </p>

        <div class="modal-action">
          <button class="btn btn-ghost" @click="mostrarModalRestaurar = false">
            Cancelar
          </button>
          <button
            class="btn btn-warning"
            :disabled="guardando"
            @click="restaurarVersion"
          >
            <span v-if="guardando" class="loading loading-spinner loading-sm"></span>
            <span v-else>Restaurar</span>
          </button>
        </div>
      </div>
      <form method="dialog" class="modal-backdrop">
        <button @click="mostrarModalRestaurar = false">close</button>
      </form>
    </dialog>
  </div>
</template>

<style scoped>
.versiones-panel {
  max-height: 100%;
}
</style>
