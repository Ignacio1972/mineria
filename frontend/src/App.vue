<script setup lang="ts">
import { onMounted, computed } from 'vue';
import { useRoute } from 'vue-router';
import { useUIStore } from '@/stores/ui';
import { AppHeader, AppFooter } from '@/components/layout';

const route = useRoute();
const uiStore = useUIStore();

const isLoginPage = computed(() => route.name === 'login');

onMounted(() => {
  uiStore.cargarTema();
});
</script>

<template>
  <div class="min-h-screen bg-base-100" :class="{ 'app-layout': !isLoginPage }" :data-theme="uiStore.tema">
    <AppHeader v-if="!isLoginPage" class="app-header" />

    <router-view class="app-main" />

    <AppFooter v-if="!isLoginPage" class="app-footer" />

    <!-- Toast notifications -->
    <div class="toast toast-end toast-bottom z-50">
      <div
        v-for="toast in uiStore.toasts"
        :key="toast.id"
        class="alert"
        :class="{
          'alert-success': toast.tipo === 'success',
          'alert-error': toast.tipo === 'error',
          'alert-warning': toast.tipo === 'warning',
          'alert-info': toast.tipo === 'info',
        }"
      >
        <span>{{ toast.mensaje }}</span>
        <button class="btn btn-ghost btn-xs" @click="uiStore.eliminarToast(toast.id)">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>

<style>
.app-layout {
  display: grid;
  grid-template-rows: auto 1fr auto;
  grid-template-areas:
    "header"
    "main"
    "footer";
  min-height: 100vh;
}

.app-header {
  grid-area: header;
}

.app-main {
  grid-area: main;
  overflow: hidden;
}

.app-footer {
  grid-area: footer;
}
</style>
