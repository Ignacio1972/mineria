<script setup lang="ts">
import { useMap } from '@/composables/useMap';

const { zoomIn, zoomOut, toggleMapaBase, centrarEnChile, centrarEnAntofagasta, mapaBase } = useMap();
</script>

<template>
  <div class="flex flex-col gap-2">
    <div class="btn-group btn-group-vertical bg-base-100 rounded-lg shadow-lg">
      <button class="btn btn-sm btn-ghost" @click="zoomIn" title="Acercar">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
      </button>
      <button class="btn btn-sm btn-ghost" @click="zoomOut" title="Alejar">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 12H4" />
        </svg>
      </button>
    </div>

    <div class="btn-group btn-group-vertical bg-base-100 rounded-lg shadow-lg">
      <button
        class="btn btn-sm btn-ghost"
        @click="toggleMapaBase"
        :title="mapaBase === 'osm' ? 'Ver satélite' : 'Ver mapa'"
      >
        <svg v-if="mapaBase === 'osm'" xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
        </svg>
      </button>
    </div>

    <div class="dropdown dropdown-left">
      <div tabindex="0" role="button" class="btn btn-sm btn-ghost bg-base-100 shadow-lg rounded-lg" title="Ir a...">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
      </div>
      <ul tabindex="0" class="dropdown-content z-[1] menu p-2 shadow bg-base-100 rounded-box w-40">
        <li><a @click="centrarEnChile">Chile</a></li>
        <li><a @click="centrarEnAntofagasta">Antofagasta</a></li>
      </ul>
    </div>
  </div>
</template>
