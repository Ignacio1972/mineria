<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useUIStore } from '@/stores/ui'

const route = useRoute()
const uiStore = useUIStore()

const herramientasMenu = ref<HTMLDetailsElement | null>(null)
const proyectosMenu = ref<HTMLDetailsElement | null>(null)

const rutaActual = computed(() => route.name as string)

function esRutaActiva(rutas: string[]) {
  return rutas.some((r) => rutaActual.value?.startsWith(r))
}

function cerrarMenu(menu: 'herramientas' | 'proyectos') {
  if (menu === 'herramientas' && herramientasMenu.value) {
    herramientasMenu.value.open = false
  }
  if (menu === 'proyectos' && proyectosMenu.value) {
    proyectosMenu.value.open = false
  }
}
</script>

<template>
  <header class="navbar bg-primary text-primary-content shadow-lg app-header">
    <div class="flex-none lg:hidden">
      <button
        class="btn btn-square btn-ghost"
        @click="uiStore.toggleSidebar"
        aria-label="Toggle sidebar"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>
    </div>

    <div class="flex-1">
      <router-link :to="{ name: 'dashboard' }" class="flex items-center gap-3 hover:opacity-90 transition-opacity">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
        </svg>
        <div>
          <h1 class="text-lg font-bold leading-tight">
            Sistema de Prefactibilidad Ambiental Minera
          </h1>
          <p class="text-xs opacity-80">Analisis SEIA - Chile</p>
        </div>
      </router-link>
    </div>

    <div class="flex-none hidden md:flex">
      <ul class="menu menu-horizontal px-1">
        <li>
          <router-link
            :to="{ name: 'dashboard' }"
            class="text-primary-content"
            :class="{ 'bg-primary-focus': rutaActual === 'dashboard' }"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
            </svg>
            Dashboard
          </router-link>
        </li>
        <li>
          <details ref="proyectosMenu">
            <summary class="text-primary-content" :class="{ 'bg-primary-focus': esRutaActiva(['proyecto', 'cliente']) }">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
              </svg>
              Proyectos
            </summary>
            <ul class="bg-base-100 text-base-content rounded-box z-50 w-48">
              <li>
                <router-link :to="{ name: 'proyectos' }" @click="cerrarMenu('proyectos')">
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                  </svg>
                  Proyectos
                </router-link>
              </li>
              <li>
                <router-link :to="{ name: 'clientes' }" @click="cerrarMenu('proyectos')">
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                  </svg>
                  Clientes
                </router-link>
              </li>
            </ul>
          </details>
        </li>
        <li>
          <router-link
            :to="{ name: 'analisis-historial' }"
            class="text-primary-content"
            :class="{ 'bg-primary-focus': rutaActual === 'analisis-historial' }"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            Analisis
          </router-link>
        </li>
        <li>
          <router-link
            :to="{ name: 'corpus' }"
            class="text-primary-content"
            :class="{ 'bg-primary-focus': rutaActual === 'corpus' }"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
            Corpus
          </router-link>
        </li>
        <li>
          <router-link
            :to="{ name: 'asistente' }"
            class="text-primary-content"
            :class="{ 'bg-primary-focus': rutaActual === 'asistente' }"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
            Asistente
          </router-link>
        </li>
        <li>
          <details ref="herramientasMenu">
            <summary class="text-primary-content">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
              </svg>
              Herramientas
            </summary>
            <ul class="bg-base-100 text-base-content rounded-box z-50 w-56">
              <li class="menu-title">Mapas SEA</li>
              <li>
                <router-link :to="{ name: 'seia-proyectos' }" @click="cerrarMenu('herramientas')">
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
                  </svg>
                  Proyectos SEIA
                </router-link>
              </li>
              <li>
                <router-link :to="{ name: 'seia-lineas-base' }" @click="cerrarMenu('herramientas')">
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  Lineas de Base EIA
                </router-link>
              </li>
              <li class="menu-title">Desarrollo</li>
              <li>
                <a
                  href="http://148.113.205.115:9085/geoserver/web/"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  GeoServer
                </a>
              </li>
              <li>
                <a
                  href="http://148.113.205.115:9001/docs"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  API Docs
                </a>
              </li>
            </ul>
          </details>
        </li>
      </ul>
    </div>

    <div class="flex-none gap-2">
      <button
        class="btn btn-ghost btn-circle"
        @click="uiStore.toggleTema"
        :aria-label="uiStore.tema === 'dark' ? 'Cambiar a modo claro' : 'Cambiar a modo oscuro'"
      >
        <svg v-if="uiStore.tema === 'dark'" xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
        </svg>
        <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
        </svg>
      </button>

      <div class="dropdown dropdown-end">
        <div tabindex="0" role="button" class="btn btn-ghost btn-circle">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <ul tabindex="0" class="dropdown-content z-[1] menu p-2 shadow bg-base-100 text-base-content rounded-box w-64">
          <li class="menu-title">Acerca de</li>
          <li><a class="pointer-events-none">Sistema de Prefactibilidad Ambiental</a></li>
          <li><a class="pointer-events-none opacity-60">Version 1.0.0</a></li>
          <li class="menu-title mt-2">Leyenda</li>
          <li><span class="flex items-center gap-2"><span class="badge badge-error badge-xs"></span> Alerta Critica</span></li>
          <li><span class="flex items-center gap-2"><span class="badge badge-warning badge-xs"></span> Alerta Alta</span></li>
          <li><span class="flex items-center gap-2"><span class="badge badge-info badge-xs"></span> Alerta Media</span></li>
          <li><span class="flex items-center gap-2"><span class="badge badge-success badge-xs"></span> Alerta Baja</span></li>
        </ul>
      </div>
    </div>
  </header>
</template>
