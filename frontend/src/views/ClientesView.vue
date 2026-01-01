<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useClientesStore } from '@/stores/clientes'
import { useDebounceFn } from '@vueuse/core'

const router = useRouter()
const store = useClientesStore()

const busqueda = ref('')

// Debounce de busqueda
const buscarDebounced = useDebounceFn(() => {
  store.cargarClientes({ busqueda: busqueda.value, page: 1 })
}, 300)

watch(busqueda, () => {
  buscarDebounced()
})

onMounted(() => {
  store.cargarClientes()
})

function irANuevo() {
  router.push('/clientes/nuevo')
}

function irADetalle(id: string) {
  router.push(`/clientes/${id}`)
}

function cambiarPagina(page: number) {
  store.cargarClientes({ page })
}
</script>

<template>
  <div class="p-6 max-w-7xl mx-auto">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold">Clientes</h1>
        <p class="text-sm opacity-60">{{ store.paginacion.total }} clientes registrados</p>
      </div>
      <button class="btn btn-primary" @click="irANuevo">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        Nuevo Cliente
      </button>
    </div>

    <!-- Barra de busqueda -->
    <div class="mb-6">
      <input
        v-model="busqueda"
        type="text"
        placeholder="Buscar por nombre, RUT o email..."
        class="input input-bordered w-full max-w-md"
      />
    </div>

    <!-- Loading -->
    <div v-if="store.cargando" class="flex justify-center py-20">
      <span class="loading loading-spinner loading-lg"></span>
    </div>

    <!-- Error -->
    <div v-else-if="store.error" class="alert alert-error">
      {{ store.error }}
    </div>

    <!-- Lista vacia -->
    <div v-else-if="!store.tieneClientes" class="text-center py-20">
      <div class="text-6xl opacity-20 mb-4">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-24 w-24 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
      </div>
      <h2 class="text-xl font-bold mb-2">No hay clientes</h2>
      <p class="opacity-60 mb-4">Comienza creando tu primer cliente</p>
      <button class="btn btn-primary" @click="irANuevo">
        Crear Cliente
      </button>
    </div>

    <!-- Tabla de clientes -->
    <div v-else class="overflow-x-auto">
      <table class="table">
        <thead>
          <tr>
            <th>Razon Social</th>
            <th>RUT</th>
            <th>Email</th>
            <th>Proyectos</th>
            <th>Estado</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="cliente in store.clientes"
            :key="cliente.id"
            class="hover cursor-pointer"
            @click="irADetalle(cliente.id)"
          >
            <td>
              <div class="font-medium">{{ cliente.razon_social }}</div>
              <div v-if="cliente.nombre_fantasia" class="text-xs opacity-60">
                {{ cliente.nombre_fantasia }}
              </div>
            </td>
            <td class="text-sm">{{ cliente.rut || '-' }}</td>
            <td class="text-sm">{{ cliente.email || '-' }}</td>
            <td>
              <span class="badge badge-ghost">{{ cliente.cantidad_proyectos }}</span>
            </td>
            <td>
              <span
                class="badge badge-sm"
                :class="cliente.activo ? 'badge-success' : 'badge-ghost'"
              >
                {{ cliente.activo ? 'Activo' : 'Inactivo' }}
              </span>
            </td>
            <td>
              <button class="btn btn-ghost btn-sm btn-square">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                </svg>
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Paginacion -->
    <div v-if="store.paginacion.pages > 1" class="flex justify-center mt-6">
      <div class="join">
        <button
          class="join-item btn btn-sm"
          :disabled="store.paginacion.page <= 1"
          @click="cambiarPagina(store.paginacion.page - 1)"
        >
          Anterior
        </button>
        <button class="join-item btn btn-sm btn-disabled">
          Pagina {{ store.paginacion.page }} de {{ store.paginacion.pages }}
        </button>
        <button
          class="join-item btn btn-sm"
          :disabled="store.paginacion.page >= store.paginacion.pages"
          @click="cambiarPagina(store.paginacion.page + 1)"
        >
          Siguiente
        </button>
      </div>
    </div>
  </div>
</template>
