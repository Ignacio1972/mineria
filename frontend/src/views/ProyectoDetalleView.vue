<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useProyectosStore } from '@/stores/proyectos'
import { useAnalysisStore } from '@/stores/analysis'
import { useAnalysis } from '@/composables/useAnalysis'
import ProyectoProgreso from '@/components/proyectos/ProyectoProgreso.vue'
import ProyectoAlertas from '@/components/proyectos/ProyectoAlertas.vue'
import ProyectoFormulario from '@/components/proyectos/ProyectoFormulario.vue'
import MapContainer from '@/components/map/MapContainer.vue'
import AnalysisPanel from '@/components/analysis/AnalysisPanel.vue'
import { ESTADOS_PROYECTO } from '@/types'
import type { DatosProyecto } from '@/types'

const route = useRoute()
const router = useRouter()
const store = useProyectosStore()
const analysisStore = useAnalysisStore()
const { ejecutarAnalisisRapido, ejecutarAnalisisCompleto, cargando: analizando } = useAnalysis()

const tabActivo = ref<'info' | 'mapa' | 'analisis' | 'documentos'>('info')
const guardando = ref(false)
const formularioDatos = ref<DatosProyecto>({ nombre: '' })

const proyecto = computed(() => store.proyectoActual)
const estadoInfo = computed(() =>
  ESTADOS_PROYECTO.find((e) => e.value === proyecto.value?.estado)
)

// Cargar proyecto y su último análisis
onMounted(async () => {
  const id = route.params.id as string
  if (id) {
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
</script>

<template>
  <div class="p-6 max-w-7xl mx-auto">
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
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Sidebar izquierdo -->
        <div class="lg:col-span-1 space-y-4">
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
            </div>
          </div>
        </div>

        <!-- Contenido principal con tabs -->
        <div class="lg:col-span-2">
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
                <button class="btn btn-primary btn-sm" @click="irAMapa">
                  {{ proyecto.tiene_geometria ? 'Editar poligono' : 'Dibujar poligono' }}
                </button>
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
        </div>
      </div>
    </template>
  </div>
</template>
