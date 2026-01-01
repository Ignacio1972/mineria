<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUIStore } from '@/stores/ui'

const route = useRoute()
const router = useRouter()
const uiStore = useUIStore()

const rutaActual = computed(() => route.name as string)

function esRutaActiva(rutas: string[]) {
  return rutas.some((r) => rutaActual.value?.startsWith(r))
}

interface MenuItem {
  nombre: string
  ruta: string
  icono: string
  rutas: string[]
  badge?: string
}

const menuItems: MenuItem[] = [
  {
    nombre: 'Dashboard',
    ruta: '/dashboard',
    icono: 'home',
    rutas: ['dashboard'],
  },
  {
    nombre: 'Clientes',
    ruta: '/clientes',
    icono: 'users',
    rutas: ['cliente'],
  },
  {
    nombre: 'Proyectos',
    ruta: '/proyectos',
    icono: 'building',
    rutas: ['proyecto'],
  },
  {
    nombre: 'Analisis',
    ruta: '/analisis',
    icono: 'chart',
    rutas: ['analisis'],
  },
  {
    nombre: 'Corpus Legal',
    ruta: '/corpus',
    icono: 'document',
    rutas: ['corpus'],
  },
  {
    nombre: 'Asistente IA',
    ruta: '/asistente',
    icono: 'chat',
    rutas: ['asistente'],
  },
]

function navegar(ruta: string) {
  router.push(ruta)
  // Cerrar sidebar en movil
  if (window.innerWidth < 1024) {
    uiStore.toggleSidebar()
  }
}
</script>

<template>
  <aside
    class="bg-base-200 w-64 flex flex-col transition-all duration-300 fixed lg:relative h-full z-40"
    :class="{
      '-translate-x-full lg:translate-x-0': !uiStore.sidebarAbierto,
      'translate-x-0': uiStore.sidebarAbierto,
    }"
  >
    <!-- Menu principal -->
    <div class="p-4 flex-1 overflow-y-auto">
      <ul class="menu menu-lg gap-1">
        <li v-for="item in menuItems" :key="item.ruta">
          <a
            :class="{ 'active': esRutaActiva(item.rutas) }"
            @click="navegar(item.ruta)"
          >
            <!-- Dashboard -->
            <svg v-if="item.icono === 'home'" xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
            </svg>
            <!-- Clientes -->
            <svg v-else-if="item.icono === 'users'" xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
            <!-- Proyectos -->
            <svg v-else-if="item.icono === 'building'" xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
            </svg>
            <!-- Analisis -->
            <svg v-else-if="item.icono === 'chart'" xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <!-- Corpus Legal -->
            <svg v-else-if="item.icono === 'document'" xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
            <!-- Asistente IA -->
            <svg v-else-if="item.icono === 'chat'" xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>

            {{ item.nombre }}

            <span v-if="item.badge" class="badge badge-sm">{{ item.badge }}</span>
          </a>
        </li>
      </ul>

      <!-- Acciones rapidas -->
      <div class="mt-6">
        <h3 class="px-4 text-xs font-semibold uppercase opacity-50 mb-2">Acciones rapidas</h3>
        <ul class="menu menu-sm gap-1">
          <li>
            <a @click="navegar('/clientes/nuevo')">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
              </svg>
              Nuevo cliente
            </a>
          </li>
          <li>
            <a @click="navegar('/proyectos/nuevo')">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
              </svg>
              Nuevo proyecto
            </a>
          </li>
        </ul>
      </div>

      <!-- Herramientas externas -->
      <div class="mt-6">
        <h3 class="px-4 text-xs font-semibold uppercase opacity-50 mb-2">Herramientas</h3>
        <ul class="menu menu-sm gap-1">
          <li>
            <a
              href="http://148.113.205.115:9085/geoserver/web/"
              target="_blank"
              rel="noopener noreferrer"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2" />
              </svg>
              GeoServer
              <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
              </svg>
            </a>
          </li>
          <li>
            <a
              href="http://148.113.205.115:9001/docs"
              target="_blank"
              rel="noopener noreferrer"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              API Docs
              <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
              </svg>
            </a>
          </li>
        </ul>
      </div>
    </div>

    <!-- Footer del sidebar -->
    <div class="p-4 bg-base-300">
      <div class="flex items-center gap-2 text-xs opacity-60">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span>Sistema SEIA v1.0</span>
      </div>
    </div>
  </aside>

  <!-- Overlay para movil -->
  <div
    v-if="uiStore.sidebarAbierto"
    class="fixed inset-0 bg-black/50 z-30 lg:hidden"
    @click="uiStore.toggleSidebar"
  ></div>
</template>
