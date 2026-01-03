<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useProyectosStore } from '@/stores/proyectos'
import { useAnalysisStore } from '@/stores/analysis'
import { useAsistenteStore } from '@/stores/asistente'
import { useAnalysis } from '@/composables/useAnalysis'
import { useMap } from '@/composables/useMap'
import ProyectoProgreso from '@/components/proyectos/ProyectoProgreso.vue'
import ProyectoAlertas from '@/components/proyectos/ProyectoAlertas.vue'
import ProyectoFormulario from '@/components/proyectos/ProyectoFormulario.vue'
import MapContainer from '@/components/map/MapContainer.vue'
import AnalysisPanel from '@/components/analysis/AnalysisPanel.vue'
import ChatAsistente from '@/components/asistente/ChatAsistente.vue'
import FichaAcumulativa from '@/components/asistente/FichaAcumulativa.vue'
import { ESTADOS_PROYECTO } from '@/types'
import type { DatosProyecto, GeometriaGeoJSON } from '@/types'

const route = useRoute()
const router = useRouter()
const store = useProyectosStore()
const analysisStore = useAnalysisStore()
const asistenteStore = useAsistenteStore()
const { ejecutarAnalisisRapido, ejecutarAnalisisCompleto, cargando: analizando } = useAnalysis()
const { centrarEnGeometria } = useMap()

const tabActivo = ref<'info' | 'mapa' | 'analisis' | 'documentos' | 'asistente' | 'ficha'>('info')

// Computed para determinar si el layout debe ser full-width (sin sidebar)
const layoutFullWidth = computed(() => tabActivo.value === 'asistente' || tabActivo.value === 'ficha')
const guardando = ref(false)
const formularioDatos = ref<DatosProyecto>({ nombre: '' })

// Modal de confirmación para eliminar
const mostrarModalEliminar = ref(false)
const eliminando = ref(false)
const tipoEliminacion = ref<'archivar' | 'eliminar'>('archivar')

// Importación KML
const kmlFileInput = ref<HTMLInputElement | null>(null)
const importandoKml = ref(false)
const errorKml = ref<string | null>(null)

const proyecto = computed(() => store.proyectoActual)
const estadoInfo = computed(() =>
  ESTADOS_PROYECTO.find((e) => e.value === proyecto.value?.estado)
)

// Cargar proyecto y su último análisis
onMounted(async () => {
  const id = route.params.id as string
  if (id) {
    // Establecer contexto del proyecto para el asistente
    const proyectoId = parseInt(id, 10)
    if (!isNaN(proyectoId)) {
      asistenteStore.setProyectoContexto(proyectoId)
    }

    await store.cargarProyecto(id)
    if (store.proyectoActual) {
      formularioDatos.value = {
        nombre: store.proyectoActual.nombre,
        cliente_id: store.proyectoActual.cliente_id || null,
        tipo_mineria: store.proyectoActual.tipo_mineria || null,
        mineral_principal: store.proyectoActual.mineral_principal || null,
        fase: store.proyectoActual.fase || null,
        titular: store.proyectoActual.titular || null,
        region: store.proyectoActual.region || null,
        comuna: store.proyectoActual.comuna || null,
        superficie_ha: store.proyectoActual.superficie_ha || null,
        vida_util_anos: store.proyectoActual.vida_util_anos || null,
        uso_agua_lps: store.proyectoActual.uso_agua_lps || null,
        fuente_agua: store.proyectoActual.fuente_agua || null,
        energia_mw: store.proyectoActual.energia_mw || null,
        trabajadores_construccion: store.proyectoActual.trabajadores_construccion || null,
        trabajadores_operacion: store.proyectoActual.trabajadores_operacion || null,
        inversion_musd: store.proyectoActual.inversion_musd || null,
        descripcion: store.proyectoActual.descripcion || null,
      }

      // Cargar el último análisis del proyecto desde la BD
      const proyectoId = parseInt(id, 10)
      if (!isNaN(proyectoId)) {
        await analysisStore.cargarUltimoAnalisis(proyectoId)
      }

      // Centrar el mapa en la geometría si existe
      if (store.proyectoActual.geometria) {
        centrarEnGeometria(store.proyectoActual.geometria)
      }
    }
  }
})

// Navegacion a editar mapa
function irAMapa() {
  router.push(`/proyectos/${proyecto.value?.id}/mapa`)
}

// Guardar cambios
async function guardar(datos: DatosProyecto) {
  if (!proyecto.value) return
  guardando.value = true
  try {
    await store.actualizarProyecto(proyecto.value.id, datos)
  } catch (e) {
    console.error('Error guardando:', e)
  } finally {
    guardando.value = false
  }
}

// Analisis
async function analizar(tipo: 'rapido' | 'completo') {
  if (!proyecto.value) return
  if (tipo === 'rapido') {
    await ejecutarAnalisisRapido()
  } else {
    await ejecutarAnalisisCompleto()
  }
  tabActivo.value = 'analisis'
}

// Eliminar proyecto
function confirmarEliminacion(tipo: 'archivar' | 'eliminar') {
  tipoEliminacion.value = tipo
  mostrarModalEliminar.value = true
}

async function ejecutarEliminacion() {
  if (!proyecto.value) return
  eliminando.value = true

  try {
    if (tipoEliminacion.value === 'eliminar') {
      await store.eliminarProyecto(proyecto.value.id.toString())
    } else {
      await store.archivarProyecto(proyecto.value.id.toString())
    }
    mostrarModalEliminar.value = false
    router.push('/proyectos')
  } catch (e) {
    console.error('Error eliminando:', e)
  } finally {
    eliminando.value = false
  }
}

// Computed para saber si puede eliminar permanentemente
const puedeEliminarPermanente = computed(() =>
  proyecto.value?.estado === 'borrador' && proyecto.value?.total_analisis === 0
)

// Importación KML
function abrirSelectorKml() {
  kmlFileInput.value?.click()
}

// Función recursiva para eliminar la dimensión Z de las coordenadas
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function eliminarDimensionZ(coords: any): any {
  if (!Array.isArray(coords)) return coords
  if (typeof coords[0] === 'number') {
    return [coords[0], coords[1]]
  }
  return coords.map(eliminarDimensionZ)
}

async function onKmlSeleccionado(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file || !proyecto.value) return

  const extension = file.name.toLowerCase().split('.').pop()
  if (extension !== 'kml' && extension !== 'kmz') {
    errorKml.value = 'Solo se permiten archivos KML o KMZ'
    setTimeout(() => errorKml.value = null, 3000)
    input.value = ''
    return
  }

  importandoKml.value = true
  errorKml.value = null

  try {
    const contenido = await file.text()

    const KML = (await import('ol/format/KML')).default
    const kmlFormat = new KML({ extractStyles: false })

    const features = kmlFormat.readFeatures(contenido, {
      dataProjection: 'EPSG:4326',
      featureProjection: 'EPSG:4326',
    })

    if (features.length === 0) {
      throw new Error('No se encontraron geometrías en el archivo')
    }

    let geometria: GeometriaGeoJSON | null = null

    for (const feature of features) {
      const geom = feature.getGeometry()
      if (!geom) continue

      const type = geom.getType()
      if (type === 'Polygon' || type === 'MultiPolygon') {
        const GeoJSON = (await import('ol/format/GeoJSON')).default
        const geojsonFormat = new GeoJSON()
        geometria = geojsonFormat.writeGeometryObject(geom, {
          dataProjection: 'EPSG:4326',
          featureProjection: 'EPSG:4326',
        }) as GeometriaGeoJSON

        if (geometria && geometria.coordinates) {
          geometria.coordinates = eliminarDimensionZ(geometria.coordinates)
        }
        break
      }
    }

    if (!geometria) {
      throw new Error('El archivo no contiene polígonos válidos')
    }

    // Guardar la geometría en el backend
    await store.actualizarGeometria(proyecto.value.id.toString(), {
      geometria: geometria,
    })

    // Recargar el proyecto para ver los cambios
    await store.cargarProyecto(proyecto.value.id.toString())

    // Centrar el mapa en la geometría importada
    centrarEnGeometria(geometria)

  } catch (e) {
    console.error('Error importando KML:', e)
    errorKml.value = e instanceof Error ? e.message : 'Error al importar archivo'
    setTimeout(() => errorKml.value = null, 4000)
  } finally {
    importandoKml.value = false
    input.value = ''
  }
}
</script>

<template>
  <div
    class="mx-auto"
    :class="layoutFullWidth ? 'w-full p-2' : 'p-6 max-w-7xl'"
  >
    <!-- Loading -->
    <div v-if="store.cargando" class="flex justify-center py-20">
      <span class="loading loading-spinner loading-lg"></span>
    </div>

    <!-- No encontrado -->
    <div v-else-if="!proyecto" class="text-center py-20">
      <h2 class="text-xl font-bold">Proyecto no encontrado</h2>
      <button class="btn btn-primary mt-4" @click="router.push('/proyectos')">
        Volver a proyectos
      </button>
    </div>

    <!-- Contenido -->
    <template v-else>
      <!-- Header -->
      <div class="flex items-start justify-between mb-6">
        <div>
          <div class="flex items-center gap-2 mb-2">
            <button class="btn btn-ghost btn-sm" @click="router.push('/proyectos')">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
              </svg>
              Proyectos
            </button>
          </div>
          <h1 class="text-2xl font-bold">{{ proyecto.nombre }}</h1>
          <p class="text-sm opacity-60">
            {{ proyecto.cliente_razon_social || 'Sin cliente asignado' }}
          </p>
        </div>
        <div class="flex items-center gap-2">
          <div class="badge" :class="estadoInfo?.color">
            {{ estadoInfo?.label }}
          </div>
        </div>
      </div>

      <!-- Grid principal -->
      <div
        class="grid gap-6"
        :class="layoutFullWidth ? 'grid-cols-1' : 'grid-cols-1 lg:grid-cols-3'"
      >
        <!-- Sidebar izquierdo (oculto en modo full-width) -->
        <div v-if="!layoutFullWidth" class="lg:col-span-1 space-y-4">
          <!-- Progreso -->
          <ProyectoProgreso :proyecto="proyecto" @ir-a-mapa="irAMapa" />

          <!-- Alertas GIS (si tiene geometria) -->
          <div v-if="proyecto.tiene_geometria" class="card bg-base-100 shadow-sm">
            <div class="card-body">
              <h3 class="font-semibold mb-2">Alertas GIS</h3>
              <ProyectoAlertas :proyecto="proyecto" />
            </div>
          </div>

          <!-- Acciones -->
          <div class="card bg-base-100 shadow-sm">
            <div class="card-body space-y-2">
              <h3 class="font-semibold mb-2">Acciones</h3>

              <button
                class="btn btn-primary w-full"
                :disabled="!proyecto.puede_analizar || analizando"
                @click="analizar('rapido')"
              >
                <span v-if="analizando" class="loading loading-spinner loading-sm"></span>
                <span v-else>Analisis Rapido</span>
              </button>

              <button
                class="btn btn-secondary w-full"
                :disabled="!proyecto.puede_analizar || analizando"
                @click="analizar('completo')"
              >
                <span v-if="analizando" class="loading loading-spinner loading-sm"></span>
                <span v-else>Analisis Completo (LLM)</span>
              </button>

              <div v-if="!proyecto.tiene_geometria" class="text-xs text-warning text-center">
                Dibuja el poligono para habilitar analisis
              </div>

              <div class="divider my-2"></div>

              <!-- Botón eliminar con dropdown -->
              <div class="dropdown dropdown-end w-full">
                <label tabindex="0" class="btn btn-outline btn-error w-full">
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                  Eliminar
                </label>
                <ul tabindex="0" class="dropdown-content z-[1] menu p-2 shadow bg-base-100 rounded-box w-64 mt-1">
                  <li>
                    <button @click="confirmarEliminacion('archivar')" class="text-warning">
                      <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
                      </svg>
                      Archivar
                      <span class="text-xs opacity-60">(recuperable)</span>
                    </button>
                  </li>
                  <li v-if="puedeEliminarPermanente">
                    <button @click="confirmarEliminacion('eliminar')" class="text-error">
                      <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                      Eliminar permanente
                    </button>
                  </li>
                  <li v-else class="disabled">
                    <span class="text-xs opacity-50 cursor-not-allowed">
                      Eliminar permanente solo disponible para borradores sin analisis
                    </span>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        <!-- Contenido principal con tabs -->
        <div :class="layoutFullWidth ? '' : 'lg:col-span-2'">
          <!-- Tabs -->
          <div class="tabs tabs-boxed mb-4">
            <button
              class="tab"
              :class="{ 'tab-active': tabActivo === 'info' }"
              @click="tabActivo = 'info'"
            >
              Informacion
            </button>
            <button
              class="tab"
              :class="{ 'tab-active': tabActivo === 'mapa' }"
              @click="tabActivo = 'mapa'"
            >
              Ubicacion
              <span v-if="!proyecto.tiene_geometria" class="badge badge-warning badge-xs ml-1">!</span>
            </button>
            <button
              class="tab"
              :class="{ 'tab-active': tabActivo === 'analisis' }"
              @click="tabActivo = 'analisis'"
            >
              Analisis
              <span v-if="proyecto.total_analisis > 0" class="badge badge-sm ml-1">
                {{ proyecto.total_analisis }}
              </span>
            </button>
            <button
              class="tab"
              :class="{ 'tab-active': tabActivo === 'documentos' }"
              @click="tabActivo = 'documentos'"
            >
              Documentos
              <span v-if="proyecto.total_documentos > 0" class="badge badge-sm ml-1">
                {{ proyecto.total_documentos }}
              </span>
            </button>
            <div class="divider divider-horizontal mx-1"></div>
            <button
              class="tab"
              :class="{ 'tab-active': tabActivo === 'asistente' }"
              @click="tabActivo = 'asistente'"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
              Asistente
            </button>
            <button
              class="tab"
              :class="{ 'tab-active': tabActivo === 'ficha' }"
              @click="tabActivo = 'ficha'"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              Ficha
            </button>
          </div>

          <!-- Tab: Informacion -->
          <div v-if="tabActivo === 'info'" class="card bg-base-100 shadow-sm">
            <div class="card-body">
              <ProyectoFormulario
                v-model="formularioDatos"
                :guardando="guardando"
                @guardar="guardar"
              />
            </div>
          </div>

          <!-- Tab: Mapa -->
          <div v-else-if="tabActivo === 'mapa'" class="card bg-base-100 shadow-sm">
            <div class="card-body">
              <div class="flex justify-between items-center mb-4">
                <h3 class="font-semibold">Ubicacion del Proyecto</h3>
                <div class="flex gap-2">
                  <button
                    class="btn btn-ghost btn-sm"
                    :disabled="importandoKml"
                    @click="abrirSelectorKml"
                  >
                    <span v-if="importandoKml" class="loading loading-spinner loading-xs"></span>
                    <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                    </svg>
                    Importar KML
                  </button>
                  <input
                    ref="kmlFileInput"
                    type="file"
                    accept=".kml,.kmz"
                    class="hidden"
                    @change="onKmlSeleccionado"
                  />
                  <button class="btn btn-primary btn-sm" @click="irAMapa">
                    {{ proyecto.tiene_geometria ? 'Editar poligono' : 'Dibujar poligono' }}
                  </button>
                </div>
              </div>

              <!-- Error de importación -->
              <div v-if="errorKml" class="alert alert-error mb-4 py-2">
                <span class="text-sm">{{ errorKml }}</span>
              </div>

              <!-- Mini mapa de vista previa -->
              <div class="h-96 rounded-lg overflow-hidden bg-base-300 relative">
                <MapContainer
                  :geometria="proyecto.geometria"
                  :readonly="true"
                />
                <!-- Overlay si no tiene geometria -->
                <div
                  v-if="!proyecto.geometria"
                  class="absolute inset-0 bg-base-300/80 flex items-center justify-center z-10"
                >
                  <div class="text-center">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 mx-auto mb-2 opacity-40" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
                    </svg>
                    <p class="font-medium mb-2">Sin ubicacion definida</p>
                    <button class="btn btn-primary btn-sm" @click="irAMapa">
                      Dibujar poligono
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Tab: Analisis -->
          <div v-else-if="tabActivo === 'analisis'">
            <AnalysisPanel />
          </div>

          <!-- Tab: Documentos -->
          <div v-else-if="tabActivo === 'documentos'" class="card bg-base-100 shadow-sm">
            <div class="card-body">
              <p class="text-center opacity-60 py-8">
                Gestion de documentos en desarrollo
              </p>
            </div>
          </div>

          <!-- Tab: Asistente (full-width, altura fija) -->
          <div v-else-if="tabActivo === 'asistente'" class="w-full h-[calc(100vh-16rem)]">
            <ChatAsistente
              :proyecto-id="proyecto.id"
              vista-actual="proyecto-detalle"
            />
          </div>

          <!-- Tab: Ficha (full-width, altura adaptable) -->
          <div v-else-if="tabActivo === 'ficha'" class="w-full min-h-[60vh]">
            <div class="card bg-base-100 shadow-sm h-full w-full">
              <FichaAcumulativa
                :proyecto-id="proyecto.id"
                :colapsado="false"
                class="h-full w-full"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- Modal de confirmación de eliminación -->
      <dialog :class="{ 'modal modal-open': mostrarModalEliminar, 'modal': !mostrarModalEliminar }">
        <div class="modal-box">
          <h3 class="font-bold text-lg">
            {{ tipoEliminacion === 'eliminar' ? 'Eliminar permanentemente' : 'Archivar proyecto' }}
          </h3>
          <p class="py-4">
            <template v-if="tipoEliminacion === 'eliminar'">
              Esta accion <strong>no se puede deshacer</strong>. El proyecto y todos sus documentos seran eliminados permanentemente.
            </template>
            <template v-else>
              El proyecto sera archivado y no aparecera en la lista principal. Podras restaurarlo mas adelante si lo necesitas.
            </template>
          </p>
          <p class="text-sm opacity-70 mb-4">
            Proyecto: <strong>{{ proyecto.nombre }}</strong>
          </p>
          <div class="modal-action">
            <button
              class="btn"
              :disabled="eliminando"
              @click="mostrarModalEliminar = false"
            >
              Cancelar
            </button>
            <button
              class="btn"
              :class="tipoEliminacion === 'eliminar' ? 'btn-error' : 'btn-warning'"
              :disabled="eliminando"
              @click="ejecutarEliminacion"
            >
              <span v-if="eliminando" class="loading loading-spinner loading-sm"></span>
              {{ tipoEliminacion === 'eliminar' ? 'Eliminar permanentemente' : 'Archivar' }}
            </button>
          </div>
        </div>
        <form method="dialog" class="modal-backdrop">
          <button @click="mostrarModalEliminar = false">close</button>
        </form>
      </dialog>
    </template>
  </div>
</template>
