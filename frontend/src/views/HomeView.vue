<script setup lang="ts">
import { useRouter } from 'vue-router';

const router = useRouter();

function nuevoProyecto() {
  router.push({ name: 'proyecto' });
}
</script>

<template>
  <div class="hero min-h-[60vh] bg-base-200 rounded-box">
    <div class="hero-content text-center">
      <div class="max-w-md">
        <h1 class="text-4xl font-bold">
          Sistema de Prefactibilidad Ambiental Minera
        </h1>
        <p class="py-6 text-base-content/70">
          Analiza la prefactibilidad ambiental de proyectos mineros en Chile.
          Evalua automaticamente si tu proyecto debe ingresar al SEIA como DIA o EIA.
        </p>
        <div class="flex gap-4 justify-center">
          <button
            class="btn btn-primary"
            @click="nuevoProyecto"
          >
            Nuevo Proyecto
          </button>
          <router-link
            :to="{ name: 'historial' }"
            class="btn btn-outline"
          >
            Ver Historial
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>
