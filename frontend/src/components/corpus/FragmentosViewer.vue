<script setup lang="ts">
import { ref, computed } from 'vue'
import type { Fragmento } from '@/types'

const props = defineProps<{
  fragmentos: Fragmento[]
  total: number
  cargando?: boolean
  documentoTitulo?: string
}>()

const emit = defineEmits<{
  cargarMas: []
  reprocesar: []
}>()

const fragmentoExpandido = ref<number | null>(null)
const filtroTema = ref<string>('')

const temasUnicos = computed(() => {
  const temas = new Set<string>()
  props.fragmentos.forEach((f) => f.temas.forEach((t) => temas.add(t)))
  return Array.from(temas).sort()
})

const fragmentosFiltrados = computed(() => {
  if (!filtroTema.value) return props.fragmentos
  return props.fragmentos.filter((f) => f.temas.includes(filtroTema.value))
})

const hayMasFragmentos = computed(() => props.fragmentos.length < props.total)

function toggleExpansion(id: number) {
  fragmentoExpandido.value = fragmentoExpandido.value === id ? null : id
}

function copiarContenido(contenido: string) {
  navigator.clipboard.writeText(contenido)
}
</script>

<template>
  <div class="fragmentos-viewer">
    <!-- Header -->
    <div class="flex items-center justify-between mb-4">
      <div>
        <h3 class="font-semibold">Fragmentos indexados</h3>
        <p class="text-xs opacity-60">
          {{ fragmentosFiltrados.length }} de {{ total }} fragmentos
        </p>
      </div>

      <div class="flex items-center gap-2">
        <!-- Filtro por tema -->
        <select
          v-if="temasUnicos.length > 0"
          v-model="filtroTema"
          class="select select-bordered select-xs"
        >
          <option value="">Todos los temas</option>
          <option v-for="tema in temasUnicos" :key="tema" :value="tema">
            {{ tema }}
          </option>
        </select>

        <!-- Boton reprocesar -->
        <button class="btn btn-ghost btn-xs" @click="emit('reprocesar')">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Reprocesar
        </button>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="cargando" class="flex justify-center py-8">
      <span class="loading loading-spinner loading-md"></span>
    </div>

    <!-- Lista de fragmentos -->
    <div v-else-if="fragmentosFiltrados.length > 0" class="space-y-2">
      <div
        v-for="fragmento in fragmentosFiltrados"
        :key="fragmento.id"
        class="card bg-base-200 card-compact"
      >
        <div class="card-body">
          <!-- Header del fragmento -->
          <div class="flex items-start justify-between gap-2">
            <div class="flex items-center gap-2 min-w-0">
              <!-- Indicador de embedding -->
              <div
                class="tooltip"
                :data-tip="fragmento.tiene_embedding ? 'Con embedding' : 'Sin embedding'"
              >
                <span
                  class="w-2 h-2 rounded-full inline-block"
                  :class="fragmento.tiene_embedding ? 'bg-success' : 'bg-warning'"
                ></span>
              </div>

              <!-- Seccion -->
              <span v-if="fragmento.seccion" class="font-medium text-sm truncate">
                {{ fragmento.seccion }}
              </span>
              <span v-else class="text-xs opacity-50">Fragmento #{{ fragmento.id }}</span>
            </div>

            <!-- Acciones -->
            <div class="flex items-center gap-1">
              <button
                class="btn btn-ghost btn-xs"
                @click="copiarContenido(fragmento.contenido)"
              >
                <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
              </button>
              <button
                class="btn btn-ghost btn-xs"
                @click="toggleExpansion(fragmento.id)"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  class="h-3 w-3 transition-transform"
                  :class="fragmentoExpandido === fragmento.id ? 'rotate-180' : ''"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                </svg>
              </button>
            </div>
          </div>

          <!-- Contenido (preview o completo) -->
          <p
            class="text-sm whitespace-pre-wrap"
            :class="fragmentoExpandido !== fragmento.id ? 'line-clamp-2' : ''"
          >
            {{ fragmento.contenido }}
          </p>

          <!-- Indicador de truncado -->
          <p v-if="fragmento.contenido_truncado" class="text-xs text-warning">
            Contenido truncado en vista previa
          </p>

          <!-- Temas -->
          <div v-if="fragmento.temas.length > 0" class="flex flex-wrap gap-1 mt-1">
            <span
              v-for="tema in fragmento.temas"
              :key="tema"
              class="badge badge-xs"
              :class="filtroTema === tema ? 'badge-primary' : 'badge-outline'"
            >
              {{ tema }}
            </span>
          </div>
        </div>
      </div>

      <!-- Cargar mas -->
      <div v-if="hayMasFragmentos" class="text-center pt-2">
        <button class="btn btn-ghost btn-sm" @click="emit('cargarMas')">
          Cargar mas fragmentos
        </button>
      </div>
    </div>

    <!-- Estado vacio -->
    <div v-else class="text-center py-8">
      <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 mx-auto opacity-20" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
      <p class="mt-2 opacity-60">Sin fragmentos</p>
      <p class="text-xs opacity-40">
        El documento aun no ha sido procesado
      </p>
      <button class="btn btn-primary btn-sm mt-4" @click="emit('reprocesar')">
        Procesar documento
      </button>
    </div>
  </div>
</template>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
