<script setup lang="ts">
import { useMap } from '@/composables/useMap';
import { computed } from 'vue';

const props = defineProps<{
  tieneGeometria?: boolean
}>()

const {
  modoEdicion,
  herramientaActiva,
  activarDibujo,
  activarModificar,
  activarEliminar,
  desactivarEdicion,
} = useMap();

const geometriaPresente = computed(() => props.tieneGeometria ?? false);
</script>

<template>
  <div class="bg-base-100 rounded-lg shadow-lg p-2">
    <div class="flex gap-2">
      <div class="tooltip" data-tip="Dibujar polígono">
        <button
          class="btn btn-sm"
          :class="herramientaActiva === 'polygon' ? 'btn-primary' : 'btn-ghost'"
          @click="activarDibujo"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6z" />
          </svg>
        </button>
      </div>

      <div class="tooltip" data-tip="Modificar polígono">
        <button
          class="btn btn-sm"
          :class="herramientaActiva === 'modify' ? 'btn-secondary' : 'btn-ghost'"
          :disabled="!geometriaPresente"
          @click="activarModificar"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
          </svg>
        </button>
      </div>

      <div class="tooltip" data-tip="Eliminar polígono">
        <button
          class="btn btn-sm btn-ghost"
          :disabled="!geometriaPresente"
          @click="activarEliminar"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
        </button>
      </div>

      <div v-if="modoEdicion" class="divider divider-horizontal mx-0"></div>

      <button
        v-if="modoEdicion"
        class="btn btn-sm btn-ghost"
        @click="desactivarEdicion"
      >
        Cancelar
      </button>
    </div>

    <div v-if="modoEdicion" class="mt-2 text-xs opacity-70">
      <span v-if="herramientaActiva === 'polygon'">
        Haga clic en el mapa para dibujar el polígono. Doble clic para finalizar.
      </span>
      <span v-else-if="herramientaActiva === 'modify'">
        Arrastre los vértices para modificar el polígono.
      </span>
    </div>
  </div>
</template>
