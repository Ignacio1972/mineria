<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useProyectosStore } from '@/stores/proyectos'
import { useMapStore } from '@/stores/map'
import MapContainer from '@/components/map/MapContainer.vue'
import type { GeometriaGeoJSON } from '@/types'

const route = useRoute()
const router = useRouter()
const store = useProyectosStore()
const mapStore = useMapStore()

const guardando = ref(false)
const geometriaLocal = ref<GeometriaGeoJSON | null>(null)

const proyecto = computed(() => store.proyectoActual)

onMounted(async () => {
  const id = route.params.id as string
  if (id) {
    await store.cargarProyecto(id)
    if (store.proyectoActual?.geometria) {
      geometriaLocal.value = store.proyectoActual.geometria
    } else if (store.proyectoActual?.region) {
      // Si no tiene geometria, centrar en la region del proyecto
      mapStore.centrarEnRegion(store.proyectoActual.region)
    }
  }
})

function onGeometriaChange(geom: GeometriaGeoJSON | null) {
  geometriaLocal.value = geom
}

async function guardar() {
  if (!proyecto.value || !geometriaLocal.value) return

  guardando.value = true
  try {
    await store.actualizarGeometria(proyecto.value.id, {
      geometria: geometriaLocal.value,
    })
    router.push(`/proyectos/${proyecto.value.id}`)
  } catch (e) {
    console.error('Error guardando geometria:', e)
  } finally {
    guardando.value = false
  }
}

function cancelar() {
  router.back()
}
</script>

<template>
  <div class="h-screen flex flex-col">
    <!-- Header -->
    <div class="navbar bg-base-100 border-b px-4">
      <div class="flex-1 gap-4">
        <button class="btn btn-ghost btn-sm" @click="cancelar">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
          </svg>
          Volver
        </button>
        <div>
          <h1 class="font-bold">{{ proyecto?.nombre || 'Cargando...' }}</h1>
          <p class="text-xs opacity-60">Editar ubicacion del proyecto</p>
        </div>
      </div>
      <div class="flex-none gap-2">
        <button class="btn btn-ghost" @click="cancelar">
          Cancelar
        </button>
        <button
          class="btn btn-primary"
          :disabled="!geometriaLocal || guardando"
          @click="guardar"
        >
          <span v-if="guardando" class="loading loading-spinner loading-sm"></span>
          <span v-else>Guardar Ubicacion</span>
        </button>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="store.cargando" class="flex-1 flex items-center justify-center">
      <span class="loading loading-spinner loading-lg"></span>
    </div>

    <!-- Mapa -->
    <div v-else class="flex-1 relative">
      <MapContainer
        :geometria="geometriaLocal"
        :readonly="false"
        @update:geometria="onGeometriaChange"
      />

      <!-- Instrucciones (posicionado arriba de DrawTools en móvil, z-40 para estar debajo de controles z-50) -->
      <div class="absolute bottom-20 left-4 right-4 md:bottom-4 md:left-auto md:right-4 md:w-80 z-40">
        <div class="card bg-base-100 shadow-lg">
          <div class="card-body p-4">
            <h3 class="font-semibold text-sm mb-2">Instrucciones</h3>
            <ul class="text-xs space-y-1 opacity-80">
              <li>1. Usa la herramienta de dibujo para trazar el poligono</li>
              <li>2. Haz clic para agregar vertices</li>
              <li>3. Doble clic para terminar el poligono</li>
              <li>4. Guarda cuando estes satisfecho</li>
            </ul>
            <div v-if="geometriaLocal" class="mt-2 pt-2 border-t">
              <span class="badge badge-success badge-sm">Poligono dibujado</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
