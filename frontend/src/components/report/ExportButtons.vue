<script setup lang="ts">
import { useExport } from '@/composables/useExport';

const { puedeExportar, exportando, exportar, formatos } = useExport();
</script>

<template>
  <div class="flex flex-wrap gap-2">
    <div class="dropdown dropdown-end">
      <div
        tabindex="0"
        role="button"
        class="btn btn-sm btn-outline"
        :class="{ 'btn-disabled': !puedeExportar || exportando }"
      >
        <span v-if="exportando" class="loading loading-spinner loading-xs"></span>
        <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
        </svg>
        Exportar
      </div>
      <ul tabindex="0" class="dropdown-content z-[1] menu p-2 shadow bg-base-100 rounded-box w-40">
        <li v-for="formato in formatos" :key="formato.valor">
          <a @click="exportar(formato.valor)">
            {{ formato.nombre }}
          </a>
        </li>
      </ul>
    </div>
  </div>
</template>
