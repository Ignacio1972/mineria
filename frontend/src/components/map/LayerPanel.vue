<script setup lang="ts">
import { useMap } from '@/composables/useMap';
import { CATEGORIAS_CAPA } from '@/types/gis';

const { capasPorCategoria, toggleCapa, setOpacidad } = useMap();
</script>

<template>
  <div class="space-y-3">
    <div
      v-for="(capas, categoria) in capasPorCategoria"
      :key="categoria"
      class="space-y-1"
    >
      <h4 class="text-xs font-semibold uppercase opacity-60">
        {{ CATEGORIAS_CAPA[categoria as keyof typeof CATEGORIAS_CAPA] }}
      </h4>
      <div
        v-for="capa in capas"
        :key="capa.id"
        class="flex items-center gap-2"
      >
        <input
          type="checkbox"
          class="checkbox checkbox-xs"
          :checked="capa.visible"
          @change="toggleCapa(capa.id)"
        />
        <div class="flex-1">
          <div class="flex items-center gap-1">
            <span
              class="w-3 h-3 rounded-sm"
              :style="{
                backgroundColor: capa.estilo?.fillColor || '#888',
                border: `1px solid ${capa.estilo?.strokeColor || '#666'}`,
              }"
            ></span>
            <span class="text-xs">{{ capa.nombre }}</span>
          </div>
        </div>
        <input
          v-if="capa.visible"
          type="range"
          min="0"
          max="100"
          :value="capa.opacidad * 100"
          class="range range-xs w-12"
          @input="(e) => setOpacidad(capa.id, Number((e.target as HTMLInputElement).value) / 100)"
        />
      </div>
    </div>

    <div class="text-xs opacity-50 mt-4">
      Nota: Las capas GIS se cargan desde el servidor. Algunas capas pueden no estar disponibles en todas las regiones.
    </div>
  </div>
</template>
