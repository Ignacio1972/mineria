<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()
</script>

<template>
  <div class="card bg-base-100 shadow-sm">
    <div class="card-body">
      <h2 class="card-title text-lg">Acciones Rapidas</h2>
      <div class="flex flex-col gap-3 mt-4">
        <button
          class="btn btn-primary w-full"
          @click="router.push('/clientes/nuevo')"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
          Nuevo Cliente
        </button>
        <button
          class="btn btn-secondary w-full"
          @click="router.push('/proyectos/nuevo')"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
          Nuevo Proyecto
        </button>
      </div>
    </div>
  </div>
</template>
