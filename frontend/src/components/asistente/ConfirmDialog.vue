<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { AccionPendiente } from '@/types'

interface Props {
  accion: AccionPendiente | null
  visible: boolean
  procesando?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  procesando: false,
})

const emit = defineEmits<{
  (e: 'confirmar', comentario?: string): void
  (e: 'cancelar'): void
  (e: 'cerrar'): void
}>()

const comentario = ref('')

const tipoIcono = computed(() => {
  if (!props.accion) return 'question'

  const iconos: Record<string, string> = {
    crear_proyecto: 'document-add',
    actualizar_proyecto: 'pencil',
    ejecutar_analisis: 'chart-bar',
    exportar_informe: 'download',
    navegar: 'arrow-right',
  }
  return iconos[props.accion.tipo] || 'question'
})

const tipoTexto = computed(() => {
  if (!props.accion) return ''

  const textos: Record<string, string> = {
    crear_proyecto: 'Crear proyecto',
    actualizar_proyecto: 'Actualizar proyecto',
    ejecutar_analisis: 'Ejecutar analisis',
    exportar_informe: 'Exportar informe',
    navegar: 'Navegar',
  }
  return textos[props.accion.tipo] || props.accion.tipo
})

function confirmar() {
  emit('confirmar', comentario.value || undefined)
}

function cancelar() {
  emit('cancelar')
}

watch(
  () => props.visible,
  (val) => {
    if (!val) {
      comentario.value = ''
    }
  }
)
</script>

<template>
  <dialog
    class="modal"
    :class="{ 'modal-open': visible }"
  >
    <div class="modal-box">
      <!-- Header -->
      <div class="flex items-start gap-4 mb-4">
        <!-- Icono -->
        <div class="bg-warning/20 rounded-full p-3 shrink-0">
          <svg v-if="tipoIcono === 'document-add'" xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-warning" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 13h6m-3-3v6m5 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <svg v-else-if="tipoIcono === 'pencil'" xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-warning" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
          </svg>
          <svg v-else-if="tipoIcono === 'chart-bar'" xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-warning" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <svg v-else-if="tipoIcono === 'download'" xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-warning" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
          <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-warning" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>

        <div>
          <h3 class="font-bold text-lg">Confirmar accion</h3>
          <p class="text-sm text-base-content/70">{{ tipoTexto }}</p>
        </div>

        <!-- Boton cerrar -->
        <button
          class="btn btn-sm btn-circle btn-ghost ml-auto"
          @click="emit('cerrar')"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <!-- Contenido -->
      <div v-if="accion" class="space-y-4">
        <!-- Descripcion -->
        <div class="alert alert-warning">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <span>{{ accion.descripcion }}</span>
        </div>

        <!-- Parametros -->
        <div v-if="Object.keys(accion.parametros).length > 0">
          <h4 class="font-medium text-sm mb-2">Parametros:</h4>
          <div class="bg-base-200 rounded-lg p-3">
            <dl class="space-y-2">
              <div
                v-for="(valor, clave) in accion.parametros"
                :key="clave"
                class="flex justify-between text-sm"
              >
                <dt class="text-base-content/70">{{ clave }}:</dt>
                <dd class="font-medium">
                  {{ typeof valor === 'object' ? JSON.stringify(valor) : valor }}
                </dd>
              </div>
            </dl>
          </div>
        </div>

        <!-- Comentario opcional -->
        <div class="form-control">
          <label class="label">
            <span class="label-text">Comentario (opcional)</span>
          </label>
          <textarea
            v-model="comentario"
            class="textarea textarea-bordered h-20"
            placeholder="Agrega un comentario si lo deseas..."
            :disabled="procesando"
          ></textarea>
        </div>
      </div>

      <!-- Acciones -->
      <div class="modal-action">
        <button
          class="btn btn-ghost"
          :disabled="procesando"
          @click="cancelar"
        >
          Cancelar
        </button>
        <button
          class="btn btn-primary"
          :class="{ 'loading': procesando }"
          :disabled="procesando"
          @click="confirmar"
        >
          <svg v-if="!procesando" xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
          </svg>
          Confirmar
        </button>
      </div>
    </div>

    <!-- Backdrop -->
    <form method="dialog" class="modal-backdrop">
      <button @click="emit('cerrar')">close</button>
    </form>
  </dialog>
</template>
