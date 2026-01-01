<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useProyectosStore } from '@/stores/proyectos'
import ProyectoFormulario from '@/components/proyectos/ProyectoFormulario.vue'
import type { DatosProyecto, ProyectoCreate } from '@/types'

const route = useRoute()
const router = useRouter()
const store = useProyectosStore()

const esEdicion = computed(() => !!route.params.id)
const titulo = computed(() => esEdicion.value ? 'Editar Proyecto' : 'Nuevo Proyecto')

const formulario = ref<DatosProyecto>({
  nombre: '',
  cliente_id: null,
})

const guardando = ref(false)
const error = ref<string | null>(null)

onMounted(async () => {
  // Si viene cliente_id en query, usarlo
  if (route.query.cliente_id) {
    formulario.value.cliente_id = route.query.cliente_id as string
  }

  if (esEdicion.value) {
    try {
      await store.cargarProyecto(route.params.id as string)
      if (store.proyectoActual) {
        formulario.value = {
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
      }
    } catch (e) {
      error.value = 'Error al cargar proyecto'
    }
  }
})

async function guardar(datos: DatosProyecto) {
  if (!datos.nombre) {
    error.value = 'El nombre es obligatorio'
    return
  }

  guardando.value = true
  error.value = null

  try {
    if (esEdicion.value) {
      await store.actualizarProyecto(route.params.id as string, datos)
      router.push(`/proyectos/${route.params.id}`)
    } else {
      const proyecto = await store.crearProyecto(datos as ProyectoCreate)
      router.push(`/proyectos/${proyecto.id}`)
    }
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Error al guardar'
  } finally {
    guardando.value = false
  }
}

function cancelar() {
  router.back()
}
</script>

<template>
  <div class="p-6 max-w-4xl mx-auto">
    <!-- Header -->
    <div class="flex items-center gap-4 mb-6">
      <button class="btn btn-ghost btn-sm" @click="cancelar">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
      </button>
      <h1 class="text-2xl font-bold">{{ titulo }}</h1>
    </div>

    <!-- Loading -->
    <div v-if="store.cargando && esEdicion" class="flex justify-center py-20">
      <span class="loading loading-spinner loading-lg"></span>
    </div>

    <!-- Formulario -->
    <div v-else class="card bg-base-100 shadow-sm">
      <div class="card-body">
        <!-- Error -->
        <div v-if="error" class="alert alert-error mb-4">
          {{ error }}
        </div>

        <ProyectoFormulario
          v-model="formulario"
          :guardando="guardando"
          @guardar="guardar"
        />

        <!-- Boton cancelar -->
        <div class="flex justify-start mt-4">
          <button type="button" class="btn btn-ghost" @click="cancelar">
            Cancelar
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
