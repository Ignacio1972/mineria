<script setup lang="ts">
import { computed } from 'vue'
import type { CategoriaConHijos } from '@/types'

const props = defineProps<{
  categorias: CategoriaConHijos[]
  seleccionada?: number | null
  colapsado?: boolean
}>()

const emit = defineEmits<{
  seleccionar: [id: number | null]
}>()

const tieneSeleccion = computed(() => props.seleccionada !== null && props.seleccionada !== undefined)

function seleccionar(id: number | null) {
  emit('seleccionar', id)
}

function estaSeleccionada(id: number): boolean {
  return props.seleccionada === id
}

function debeEstarAbierto(categoria: CategoriaConHijos): boolean {
  if (props.colapsado) return false
  return estaSeleccionada(categoria.id) || categoria.hijos.some(h => estaSeleccionada(h.id))
}
</script>

<template>
  <div class="categoria-tree">
    <!-- Opcion: Todas las categorias -->
    <button
      class="btn btn-sm btn-block justify-start gap-2 mb-1"
      :class="!tieneSeleccion ? 'btn-primary' : 'btn-ghost'"
      @click="seleccionar(null)"
    >
      <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
      </svg>
      <span class="flex-1 text-left">Todas las categorias</span>
    </button>

    <!-- Categorias nivel 1 -->
    <template v-for="categoria in categorias" :key="categoria.id">
      <details
        class="collapse bg-base-100 rounded-box mb-1"
        :open="debeEstarAbierto(categoria)"
      >
        <!-- Header de categoria -->
        <summary class="collapse-title p-2 min-h-0 flex items-center gap-2 cursor-pointer">
          <button
            class="btn btn-xs btn-circle"
            :class="estaSeleccionada(categoria.id) ? 'btn-primary' : 'btn-ghost'"
            @click.stop="seleccionar(categoria.id)"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
            </svg>
          </button>
          <span class="font-medium text-sm flex-1">{{ categoria.nombre }}</span>
          <span class="badge-count">{{ categoria.cantidad_documentos }}</span>
        </summary>

        <!-- Subcategorias -->
        <div v-if="categoria.hijos.length > 0" class="collapse-content px-2 pb-2">
          <div class="pl-4 border-l-2 border-base-300 space-y-1">
            <template v-for="sub in categoria.hijos" :key="sub.id">
              <button
                class="btn btn-xs btn-block justify-start gap-2"
                :class="estaSeleccionada(sub.id) ? 'btn-primary' : 'btn-ghost'"
                @click="seleccionar(sub.id)"
              >
                <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <span class="flex-1 text-left truncate">{{ sub.nombre }}</span>
                <span class="badge-count">{{ sub.cantidad_documentos }}</span>
              </button>

              <!-- Nivel 3 (si existe) -->
              <button
                v-for="sub2 in sub.hijos"
                :key="sub2.id"
                class="btn btn-xs btn-block justify-start gap-2 ml-4"
                :class="estaSeleccionada(sub2.id) ? 'btn-primary' : 'btn-ghost'"
                @click="seleccionar(sub2.id)"
              >
                <span class="w-3 h-3 border-l border-b border-base-300"></span>
                <span class="flex-1 text-left truncate text-xs">{{ sub2.nombre }}</span>
                <span class="badge-count">{{ sub2.cantidad_documentos }}</span>
              </button>
            </template>
          </div>
        </div>
      </details>
    </template>

    <!-- Estado vacio -->
    <div v-if="categorias.length === 0" class="text-center py-4 opacity-50">
      <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 mx-auto mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
      </svg>
      <p class="text-sm">Sin categorias</p>
    </div>
  </div>
</template>

<style scoped>
/* Ocultar flecha/marcador del details/summary */
.collapse-title {
  list-style: none;
}

.collapse-title::-webkit-details-marker {
  display: none;
}

.collapse-title::marker {
  display: none;
  content: '';
}

/* Ocultar pseudo-elemento ::after del collapse-title */
.collapse-title::after {
  display: none !important;
  content: none !important;
}

/* Estilos del badge de conteo - aislado de cualquier herencia */
.badge-count {
  display: inline-block;
  font-family: system-ui, -apple-system, sans-serif;
  font-size: 0.75rem;
  font-weight: normal;
  line-height: 1;
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
  background-color: var(--color-base-200, #e5e7eb);
  color: var(--color-base-content, #374151);
  opacity: 0.7;
  text-decoration: none !important;
  border: none !important;
  box-shadow: none !important;
}
</style>
