<script setup lang="ts">
import { ref, computed } from 'vue'
import { CATEGORIAS_DOCUMENTO, type CategoriaDocumento } from '@/types'

const emit = defineEmits<{
  subir: [data: { archivo: File; nombre: string; categoria: CategoriaDocumento; descripcion?: string }]
  cancelar: []
}>()

const archivo = ref<File | null>(null)
const nombre = ref('')
const categoria = ref<CategoriaDocumento>('tecnico')
const descripcion = ref('')
const arrastrando = ref(false)
const inputRef = ref<HTMLInputElement | null>(null)

const nombreArchivo = computed(() => archivo.value?.name || '')
const tamanoArchivo = computed(() => {
  if (!archivo.value) return ''
  const bytes = archivo.value.size
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`
})

const esValido = computed(() => archivo.value !== null && nombre.value.trim().length > 0)

function seleccionarArchivo() {
  inputRef.value?.click()
}

function onArchivoSeleccionado(event: Event) {
  const target = event.target as HTMLInputElement
  if (target.files && target.files[0]) {
    setArchivo(target.files[0])
  }
}

function setArchivo(file: File) {
  archivo.value = file
  if (!nombre.value) {
    // Auto-completar nombre sin extension
    const nombreSinExt = file.name.replace(/\.[^/.]+$/, '')
    nombre.value = nombreSinExt
  }
}

function onDrop(event: DragEvent) {
  arrastrando.value = false
  if (event.dataTransfer?.files && event.dataTransfer.files[0]) {
    setArchivo(event.dataTransfer.files[0])
  }
}

function onDragOver(event: DragEvent) {
  event.preventDefault()
  arrastrando.value = true
}

function onDragLeave() {
  arrastrando.value = false
}

function limpiar() {
  archivo.value = null
  nombre.value = ''
  descripcion.value = ''
  categoria.value = 'tecnico'
}

function enviar() {
  if (!archivo.value || !nombre.value.trim()) return

  emit('subir', {
    archivo: archivo.value,
    nombre: nombre.value.trim(),
    categoria: categoria.value,
    descripcion: descripcion.value.trim() || undefined,
  })

  limpiar()
}
</script>

<template>
  <div class="space-y-4">
    <!-- Zona de drop -->
    <div
      class="border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors"
      :class="{
        'border-primary bg-primary/5': arrastrando,
        'border-base-300 hover:border-primary/50': !arrastrando,
      }"
      @click="seleccionarArchivo"
      @drop.prevent="onDrop"
      @dragover="onDragOver"
      @dragleave="onDragLeave"
    >
      <input
        ref="inputRef"
        type="file"
        class="hidden"
        @change="onArchivoSeleccionado"
      />

      <div v-if="!archivo">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 mx-auto opacity-40" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
        </svg>
        <p class="mt-2 font-medium">Arrastra un archivo aqui</p>
        <p class="text-sm opacity-60">o haz clic para seleccionar</p>
      </div>

      <div v-else class="flex items-center justify-center gap-3">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 text-success" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <div class="text-left">
          <p class="font-medium">{{ nombreArchivo }}</p>
          <p class="text-sm opacity-60">{{ tamanoArchivo }}</p>
        </div>
        <button
          type="button"
          class="btn btn-ghost btn-sm btn-circle"
          @click.stop="limpiar"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>

    <!-- Formulario -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div class="form-control">
        <label class="label">
          <span class="label-text">Nombre del documento *</span>
        </label>
        <input
          v-model="nombre"
          type="text"
          class="input input-bordered"
          placeholder="Ej: Estudio de impacto 2024"
        />
      </div>

      <div class="form-control">
        <label class="label">
          <span class="label-text">Categoria *</span>
        </label>
        <select v-model="categoria" class="select select-bordered">
          <option v-for="cat in CATEGORIAS_DOCUMENTO" :key="cat.value" :value="cat.value">
            {{ cat.label }} - {{ cat.descripcion }}
          </option>
        </select>
      </div>
    </div>

    <div class="form-control">
      <label class="label">
        <span class="label-text">Descripcion (opcional)</span>
      </label>
      <textarea
        v-model="descripcion"
        class="textarea textarea-bordered"
        rows="2"
        placeholder="Breve descripcion del contenido..."
      ></textarea>
    </div>

    <!-- Acciones -->
    <div class="flex justify-end gap-2">
      <button
        type="button"
        class="btn btn-ghost"
        @click="emit('cancelar')"
      >
        Cancelar
      </button>
      <button
        type="button"
        class="btn btn-primary"
        :disabled="!esValido"
        @click="enviar"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
        </svg>
        Subir documento
      </button>
    </div>
  </div>
</template>
