<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useClientesStore } from '@/stores/clientes'
import type { ClienteCreate, ClienteUpdate } from '@/types'

const route = useRoute()
const router = useRouter()
const store = useClientesStore()

const esEdicion = computed(() => !!route.params.id)
const titulo = computed(() => esEdicion.value ? 'Editar Cliente' : 'Nuevo Cliente')

const formulario = ref<ClienteCreate>({
  razon_social: '',
  rut: null,
  nombre_fantasia: null,
  email: null,
  telefono: null,
  direccion: null,
  notas: null,
})

const guardando = ref(false)
const error = ref<string | null>(null)

onMounted(async () => {
  if (esEdicion.value) {
    try {
      await store.cargarCliente(route.params.id as string)
      if (store.clienteActual) {
        formulario.value = {
          razon_social: store.clienteActual.razon_social,
          rut: store.clienteActual.rut,
          nombre_fantasia: store.clienteActual.nombre_fantasia,
          email: store.clienteActual.email,
          telefono: store.clienteActual.telefono,
          direccion: store.clienteActual.direccion,
          notas: store.clienteActual.notas,
        }
      }
    } catch (e) {
      error.value = 'Error al cargar cliente'
    }
  }
})

async function guardar() {
  if (!formulario.value.razon_social) {
    error.value = 'La razon social es obligatoria'
    return
  }

  guardando.value = true
  error.value = null

  try {
    if (esEdicion.value) {
      await store.actualizarCliente(route.params.id as string, formulario.value as ClienteUpdate)
    } else {
      await store.crearCliente(formulario.value)
    }
    router.push('/clientes')
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
  <div class="p-6 max-w-2xl mx-auto">
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
    <form v-else class="card bg-base-100 shadow-sm" @submit.prevent="guardar">
      <div class="card-body space-y-4">
        <!-- Error -->
        <div v-if="error" class="alert alert-error">
          {{ error }}
        </div>

        <!-- Razon Social -->
        <div class="form-control">
          <label class="label">
            <span class="label-text">Razon Social *</span>
          </label>
          <input
            v-model="formulario.razon_social"
            type="text"
            class="input input-bordered"
            placeholder="Nombre de la empresa"
            required
          />
        </div>

        <!-- RUT -->
        <div class="form-control">
          <label class="label">
            <span class="label-text">RUT</span>
          </label>
          <input
            v-model="formulario.rut"
            type="text"
            class="input input-bordered"
            placeholder="12.345.678-9"
          />
        </div>

        <!-- Nombre Fantasia -->
        <div class="form-control">
          <label class="label">
            <span class="label-text">Nombre Fantasia</span>
          </label>
          <input
            v-model="formulario.nombre_fantasia"
            type="text"
            class="input input-bordered"
            placeholder="Nombre comercial"
          />
        </div>

        <!-- Email -->
        <div class="form-control">
          <label class="label">
            <span class="label-text">Email</span>
          </label>
          <input
            v-model="formulario.email"
            type="email"
            class="input input-bordered"
            placeholder="contacto@empresa.cl"
          />
        </div>

        <!-- Telefono -->
        <div class="form-control">
          <label class="label">
            <span class="label-text">Telefono</span>
          </label>
          <input
            v-model="formulario.telefono"
            type="tel"
            class="input input-bordered"
            placeholder="+56 9 1234 5678"
          />
        </div>

        <!-- Direccion -->
        <div class="form-control">
          <label class="label">
            <span class="label-text">Direccion</span>
          </label>
          <input
            v-model="formulario.direccion"
            type="text"
            class="input input-bordered"
            placeholder="Direccion de la empresa"
          />
        </div>

        <!-- Notas -->
        <div class="form-control">
          <label class="label">
            <span class="label-text">Notas</span>
          </label>
          <textarea
            v-model="formulario.notas"
            class="textarea textarea-bordered"
            rows="3"
            placeholder="Notas adicionales..."
          ></textarea>
        </div>

        <!-- Botones -->
        <div class="flex justify-end gap-2 pt-4">
          <button type="button" class="btn btn-ghost" @click="cancelar">
            Cancelar
          </button>
          <button type="submit" class="btn btn-primary" :disabled="guardando">
            <span v-if="guardando" class="loading loading-spinner loading-sm"></span>
            <span v-else>{{ esEdicion ? 'Guardar Cambios' : 'Crear Cliente' }}</span>
          </button>
        </div>
      </div>
    </form>
  </div>
</template>
