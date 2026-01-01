<script setup lang="ts">
import { useRouter } from 'vue-router';

const router = useRouter();

function irInicio() {
  router.push({ name: 'home' });
}
</script>

<template>
  <div class="hero min-h-[60vh]">
    <div class="hero-content text-center">
      <div class="max-w-md">
        <h1 class="text-6xl font-bold text-error">404</h1>
        <h2 class="text-2xl font-semibold mt-4">Pagina no encontrada</h2>
        <p class="py-6 text-base-content/70">
          La pagina que buscas no existe o ha sido movida.
        </p>
        <button class="btn btn-primary" @click="irInicio">
          Volver al Inicio
        </button>
      </div>
    </div>
  </div>
</template>
