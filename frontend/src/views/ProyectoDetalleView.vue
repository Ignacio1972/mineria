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
import ProgresoIntegral from '@/components/proyectos/ProgresoIntegral.vue'
import MapContainer from '@/components/map/MapContainer.vue'
import AnalysisPanel from '@/components/analysis/AnalysisPanel.vue'
import ChatAsistente from '@/components/asistente/ChatAsistente.vue'
import FichaAcumulativa from '@/components/asistente/FichaAcumulativa.vue'
import EstructuraEIA from '@/components/asistente/EstructuraEIA.vue'
import RecopilacionCapitulo from '@/components/asistente/recopilacion/RecopilacionCapitulo.vue'
import GeneracionEIA from '@/components/generacion/GeneracionEIA.vue'
import ChecklistComponentes from '@/components/componentes/ChecklistComponentes.vue'
import type { DatosProyecto, GeometriaGeoJSON } from '@/types'

const route = useRoute()
const router = useRouter()
const store = useProyectosStore()
const analysisStore = useAnalysisStore()
const asistenteStore = useAsistenteStore()
const { ejecutarAnalisisRapido, ejecutarAnalisisCompleto, cargando: analizando } = useAnalysis()
const { centrarEnGeometria } = useMap()

const tabActivo = ref<'info' | 'mapa' | 'analisis' | 'documentos' | 'asistente' | 'ficha' | 'estructura' | 'recopilacion' | 'generacion' | 'checklist'>('info')

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

// Descripción geográfica
const generandoDescripcion = ref(false)
const errorDescripcion = ref<string | null>(null)

const proyecto = computed(() => store.proyectoActual)

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

      // Cargar el último análisis solo si el proyecto tiene análisis previos
      const proyectoId = parseInt(id, 10)
      if (!isNaN(proyectoId) && store.proyectoActual.total_analisis > 0) {
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

// Generar descripción geográfica
async function generarDescripcionGeografica() {
  if (!proyecto.value) return

  generandoDescripcion.value = true
  errorDescripcion.value = null

  try {
    const response = await fetch(
      `/api/v1/proyectos/${proyecto.value.id}/generar-descripcion-geografica?forzar=${!!proyecto.value.descripcion_geografica}`,
      { method: 'POST' }
    )

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Error generando descripción')
    }

    const resultado = await response.json()

    // Recargar proyecto para obtener la descripción actualizada
    await store.cargarProyecto(proyecto.value.id.toString())

    console.log('Descripción geográfica generada:', resultado)
  } catch (e) {
    console.error('Error generando descripción geográfica:', e)
    errorDescripcion.value = e instanceof Error ? e.message : 'Error generando descripción'
    setTimeout(() => errorDescripcion.value = null, 5000)
  } finally {
    generandoDescripcion.value = false
  }
}
</script>

<template>
  <div class="mx-auto p-6 max-w-7xl">
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
      <div class="mb-3">
        <h1 class="text-2xl font-bold">{{ proyecto.nombre }}</h1>
      </div>

      <!-- Dashboard de progreso del workflow EIA -->
      <div class="mb-6">
        <ProgresoIntegral
          :proyecto-id="Number(proyecto.id)"
          @ir-a-fase="(fase) => {
            if (fase === 'identificacion') tabActivo = 'mapa'
            else if (fase === 'prefactibilidad') tabActivo = 'analisis'
            else if (fase === 'recopilacion') tabActivo = 'checklist'
            else if (fase === 'generacion') tabActivo = 'generacion'
            else tabActivo = 'info'
          }"
        />
      </div>

      <!-- Contenedor principal -->
      <div>
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
            <button
              class="tab"
              :class="{ 'tab-active': tabActivo === 'estructura' }"
              @click="tabActivo = 'estructura'"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
              </svg>
              Estructura EIA
            </button>
            <button
              class="tab"
              :class="{ 'tab-active': tabActivo === 'recopilacion' }"
              @click="tabActivo = 'recopilacion'"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
              </svg>
              Recopilacion
            </button>
            <button
              class="tab"
              :class="{ 'tab-active': tabActivo === 'checklist' }"
              @click="tabActivo = 'checklist'"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Checklist
            </button>
            <button
              class="tab"
              :class="{ 'tab-active': tabActivo === 'generacion' }"
              @click="tabActivo = 'generacion'"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              Generacion EIA
            </button>
          </div>

          <!-- Tab: Informacion -->
          <div v-if="tabActivo === 'info'" class="space-y-6">
            <!-- Grid superior con progreso, alertas y acciones -->
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
              <!-- Progreso -->
              <ProyectoProgreso :proyecto="proyecto" @ir-a-mapa="irAMapa" />

              <!-- Alertas GIS (si tiene geometria) -->
              <div v-if="proyecto.tiene_geometria" class="card bg-base-100 shadow-sm">
                <div class="card-body">
                  <h3 class="font-semibold mb-2">Alertas GIS</h3>
                  <ProyectoAlertas :proyecto="proyecto" />
                </div>
              </div>

              <!-- Placeholder si no tiene geometria -->
              <div v-else class="card bg-base-100 shadow-sm">
                <div class="card-body">
                  <h3 class="font-semibold mb-2">Alertas GIS</h3>
                  <div class="alert alert-info">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <span class="text-sm">Dibuja el polígono para ver alertas GIS</span>
                  </div>
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

            <!-- Formulario de datos del proyecto -->
            <div class="card bg-base-100 shadow-sm">
              <div class="card-body">
                <ProyectoFormulario
                  v-model="formularioDatos"
                  :guardando="guardando"
                  @guardar="guardar"
                />
              </div>
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

              <!-- Descripción geográfica -->
              <div v-if="proyecto.tiene_geometria" class="mt-6">
                <div class="flex justify-between items-center mb-3">
                  <h4 class="font-semibold flex items-center gap-2">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
                    </svg>
                    Descripción Geográfica
                  </h4>
                  <button
                    class="btn btn-ghost btn-sm gap-2"
                    :disabled="generandoDescripcion"
                    @click="generarDescripcionGeografica"
                  >
                    <span v-if="generandoDescripcion" class="loading loading-spinner loading-xs"></span>
                    <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                    {{ proyecto.descripcion_geografica ? 'Regenerar' : 'Generar' }}
                  </button>
                </div>

                <!-- Mensaje si no hay descripción -->
                <div v-if="!proyecto.descripcion_geografica && !generandoDescripcion" class="alert alert-info py-3">
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="stroke-current shrink-0 w-5 h-5">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                  </svg>
                  <span class="text-sm">
                    Genera una descripción automática del lugar geográfico donde se emplaza el proyecto
                  </span>
                </div>

                <!-- Descripción existente -->
                <div v-else-if="proyecto.descripcion_geografica" class="bg-base-200 rounded-lg p-4">
                  <p class="text-sm leading-relaxed whitespace-pre-line">{{ proyecto.descripcion_geografica }}</p>

                  <!-- Metadatos -->
                  <div class="mt-3 pt-3 border-t border-base-300 flex items-center gap-4 text-xs opacity-60">
                    <span v-if="proyecto.descripcion_geografica_fecha">
                      Generada: {{ new Date(proyecto.descripcion_geografica_fecha).toLocaleString('es-CL') }}
                    </span>
                    <span v-if="proyecto.descripcion_geografica_fuente === 'auto'" class="badge badge-sm badge-ghost">
                      Automática (LLM + GIS)
                    </span>
                  </div>
                </div>

                <!-- Loading state -->
                <div v-if="generandoDescripcion" class="flex flex-col items-center justify-center py-8 gap-3">
                  <span class="loading loading-spinner loading-lg"></span>
                  <p class="text-sm opacity-60">Generando descripción geográfica...</p>
                </div>

                <!-- Error -->
                <div v-if="errorDescripcion" class="alert alert-error mt-3 py-2">
                  <span class="text-sm">{{ errorDescripcion }}</span>
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

          <!-- Tab: Asistente -->
          <div v-else-if="tabActivo === 'asistente'" class="card bg-base-100 shadow-sm">
            <div class="card-body p-0 h-[600px]">
              <ChatAsistente
                :proyecto-id="Number(proyecto.id)"
                vista-actual="proyecto-detalle"
              />
            </div>
          </div>

          <!-- Tab: Ficha (full-width, altura adaptable) -->
          <div v-else-if="tabActivo === 'ficha'" class="w-full min-h-[60vh]">
            <div class="card bg-base-100 shadow-sm h-full w-full">
              <FichaAcumulativa
                :proyecto-id="Number(proyecto.id)"
                :colapsado="false"
                class="h-full w-full"
              />
            </div>
          </div>

          <!-- Tab: Estructura EIA -->
          <div v-else-if="tabActivo === 'estructura'">
            <EstructuraEIA :proyecto-id="Number(proyecto.id)" />
          </div>

          <!-- Tab: Recopilacion EIA -->
          <div v-else-if="tabActivo === 'recopilacion'" class="h-[70vh]">
            <RecopilacionCapitulo :proyecto-id="Number(proyecto.id)" />
          </div>

          <!-- Tab: Checklist EIA -->
          <div v-else-if="tabActivo === 'checklist'" class="card bg-base-100 shadow-sm">
            <div class="card-body">
              <ChecklistComponentes :proyecto-id="Number(proyecto.id)" />
            </div>
          </div>

          <!-- Tab: Generacion EIA -->
          <div v-else-if="tabActivo === 'generacion'" class="h-[70vh]">
            <div class="card bg-base-100 shadow-sm h-full">
              <div class="card-body p-4">
                <GeneracionEIA :proyecto-id="Number(proyecto.id)" />
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
