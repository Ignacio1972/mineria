<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useClientesStore } from '@/stores/clientes'
import { clientesService } from '@/services/clientes'
import type { Proyecto } from '@/types'

const route = useRoute()
const router = useRouter()
const store = useClientesStore()

const proyectos = ref<Proyecto[]>([])
const cargandoProyectos = ref(false)
const confirmarEliminar = ref(false)
const eliminando = ref(false)

const cliente = computed(() => store.clienteActual)

onMounted(async () => {
  const id = route.params.id as string
  await store.cargarCliente(id)
  await cargarProyectos(id)
})

async function cargarProyectos(clienteId: string) {
  cargandoProyectos.value = true
  try {
    proyectos.value = await clientesService.obtenerProyectos(clienteId)
  } catch (e) {
    console.error('Error cargando proyectos:', e)
  } finally {
    cargandoProyectos.value = false
  }
}

function irAEditar() {
  router.push(`/clientes/${route.params.id}/editar`)
}

function irAProyecto(id: string) {
  router.push(`/proyectos/${id}`)
}

function irANuevoProyecto() {
  router.push(`/proyectos/nuevo?cliente_id=${route.params.id}`)
}

async function eliminar() {
  eliminando.value = true
  try {
    await store.eliminarCliente(route.params.id as string)
    router.push('/clientes')
  } catch (e) {
    console.error('Error eliminando cliente:', e)
  } finally {
    eliminando.value = false
    confirmarEliminar.value = false
  }
}

function formatearFecha(fecha: string): string {
  return new Date(fecha).toLocaleDateString('es-CL', {
    day: '2-digit',
    month: 'long',
    year: 'numeric',
  })
}
</script>

<template>
  <div class="p-6 max-w-4xl mx-auto">
    <!-- Loading -->
    <div v-if="store.cargando" class="flex justify-center py-20">
      <span class="loading loading-spinner loading-lg"></span>
    </div>

    <!-- No encontrado -->
    <div v-else-if="!cliente" class="text-center py-20">
      <h2 class="text-xl font-bold">Cliente no encontrado</h2>
      <button class="btn btn-primary mt-4" @click="router.push('/clientes')">
        Volver a clientes
      </button>
    </div>

    <!-- Contenido -->
    <template v-else>
      <!-- Header -->
      <div class="flex items-start justify-between mb-6">
        <div>
          <div class="flex items-center gap-2 mb-2">
            <button class="btn btn-ghost btn-sm" @click="router.push('/clientes')">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
              </svg>
              Clientes
            </button>
          </div>
          <h1 class="text-2xl font-bold">{{ cliente.razon_social }}</h1>
          <p v-if="cliente.nombre_fantasia" class="text-sm opacity-60">
            {{ cliente.nombre_fantasia }}
          </p>
        </div>
        <div class="flex items-center gap-2">
          <button class="btn btn-ghost" @click="irAEditar">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
            Editar
          </button>
          <button class="btn btn-error btn-outline" @click="confirmarEliminar = true">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Info del cliente -->
        <div class="lg:col-span-1">
          <div class="card bg-base-100 shadow-sm">
            <div class="card-body space-y-4">
              <h3 class="font-semibold">Informacion</h3>

              <div v-if="cliente.rut">
                <p class="text-xs opacity-60">RUT</p>
                <p>{{ cliente.rut }}</p>
              </div>

              <div v-if="cliente.email">
                <p class="text-xs opacity-60">Email</p>
                <a :href="`mailto:${cliente.email}`" class="link link-primary">
                  {{ cliente.email }}
                </a>
              </div>

              <div v-if="cliente.telefono">
                <p class="text-xs opacity-60">Telefono</p>
                <a :href="`tel:${cliente.telefono}`" class="link">
                  {{ cliente.telefono }}
                </a>
              </div>

              <div v-if="cliente.direccion">
                <p class="text-xs opacity-60">Direccion</p>
                <p>{{ cliente.direccion }}</p>
              </div>

              <div v-if="cliente.notas">
                <p class="text-xs opacity-60">Notas</p>
                <p class="text-sm">{{ cliente.notas }}</p>
              </div>

              <div class="divider"></div>

              <div>
                <p class="text-xs opacity-60">Creado</p>
                <p class="text-sm">{{ formatearFecha(cliente.created_at) }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Proyectos -->
        <div class="lg:col-span-2">
          <div class="card bg-base-100 shadow-sm">
            <div class="card-body">
              <div class="flex items-center justify-between mb-4">
                <h3 class="font-semibold">Proyectos ({{ proyectos.length }})</h3>
                <button class="btn btn-primary btn-sm" @click="irANuevoProyecto">
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
                  </svg>
                  Nuevo Proyecto
                </button>
              </div>

              <!-- Loading proyectos -->
              <div v-if="cargandoProyectos" class="flex justify-center py-8">
                <span class="loading loading-spinner loading-md"></span>
              </div>

              <!-- Lista vacia -->
              <div v-else-if="proyectos.length === 0" class="text-center py-8 opacity-60">
                <p>Este cliente no tiene proyectos</p>
                <button class="btn btn-ghost btn-sm mt-2" @click="irANuevoProyecto">
                  Crear el primero
                </button>
              </div>

              <!-- Lista de proyectos -->
              <div v-else class="space-y-3">
                <div
                  v-for="proyecto in proyectos"
                  :key="proyecto.id"
                  class="flex items-center justify-between p-3 bg-base-200 rounded-lg cursor-pointer hover:bg-base-300 transition-colors"
                  @click="irAProyecto(proyecto.id)"
                >
                  <div class="flex-1 min-w-0">
                    <p class="font-medium truncate">{{ proyecto.nombre }}</p>
                    <p class="text-xs opacity-60">
                      {{ proyecto.region || 'Sin region' }} - {{ proyecto.tipo_mineria || 'Sin tipo' }}
                    </p>
                  </div>
                  <div class="flex items-center gap-2">
                    <span
                      class="badge badge-sm"
                      :class="{
                        'badge-ghost': proyecto.estado === 'borrador',
                        'badge-info': proyecto.estado === 'completo',
                        'badge-primary': proyecto.estado === 'con_geometria',
                        'badge-success': proyecto.estado === 'analizado',
                      }"
                    >
                      {{ proyecto.estado }}
                    </span>
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                    </svg>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- Modal confirmar eliminacion -->
    <dialog class="modal" :class="{ 'modal-open': confirmarEliminar }">
      <div class="modal-box">
        <h3 class="font-bold text-lg">Eliminar cliente</h3>
        <p class="py-4">
          Estas seguro de eliminar a "<strong>{{ cliente?.razon_social }}</strong>"?
          Esta accion desactivara el cliente pero conservara sus proyectos.
        </p>
        <div class="modal-action">
          <button class="btn btn-ghost" @click="confirmarEliminar = false">Cancelar</button>
          <button
            class="btn btn-error"
            :disabled="eliminando"
            @click="eliminar"
          >
            <span v-if="eliminando" class="loading loading-spinner loading-sm"></span>
            <span v-else>Eliminar</span>
          </button>
        </div>
      </div>
      <form method="dialog" class="modal-backdrop">
        <button @click="confirmarEliminar = false">close</button>
      </form>
    </dialog>
  </div>
</template>
