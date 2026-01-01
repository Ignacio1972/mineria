<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useClientesStore } from '@/stores/clientes'
import type { DatosProyecto } from '@/types'
import { REGIONES_CHILE, TIPOS_MINERIA, FASES_PROYECTO, FUENTES_AGUA, COMUNAS_POR_REGION } from '@/types'

const props = defineProps<{
  modelValue?: DatosProyecto
  guardando?: boolean
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: DatosProyecto): void
  (e: 'guardar', value: DatosProyecto): void
}>()

const clientesStore = useClientesStore()

const formulario = ref<DatosProyecto>({
  nombre: '',
  cliente_id: null,
  tipo_mineria: null,
  mineral_principal: null,
  fase: null,
  titular: null,
  region: null,
  comuna: null,
  superficie_ha: null,
  vida_util_anos: null,
  uso_agua_lps: null,
  fuente_agua: null,
  energia_mw: null,
  trabajadores_construccion: null,
  trabajadores_operacion: null,
  inversion_musd: null,
  descripcion: null,
})

// Comunas disponibles segun region
const comunasDisponibles = computed(() => {
  if (!formulario.value.region) return []
  return COMUNAS_POR_REGION[formulario.value.region] || []
})

// Flag para evitar ciclo de actualizaciones
const actualizandoDesdeProps = ref(false)

// Inicializar con modelValue
watch(
  () => props.modelValue,
  (val) => {
    if (val) {
      actualizandoDesdeProps.value = true
      formulario.value = { ...val }
      // Reset flag en siguiente tick
      setTimeout(() => {
        actualizandoDesdeProps.value = false
      }, 0)
    }
  },
  { immediate: true }
)

// Emitir cambios (solo si no vienen del prop)
watch(
  formulario,
  (val) => {
    if (!actualizandoDesdeProps.value) {
      emit('update:modelValue', { ...val })
    }
  },
  { deep: true }
)

// Reset comuna si cambia region
watch(
  () => formulario.value.region,
  () => {
    if (!comunasDisponibles.value.includes(formulario.value.comuna || '')) {
      formulario.value.comuna = null
    }
  }
)

onMounted(() => {
  clientesStore.cargarClientes({ page_size: 100 })
})

function guardar() {
  emit('guardar', { ...formulario.value })
}
</script>

<template>
  <form class="space-y-6" @submit.prevent="guardar">
    <!-- Seccion: Identificacion -->
    <div>
      <h3 class="font-semibold mb-4">Identificacion del Proyecto</h3>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <!-- Nombre -->
        <div class="form-control md:col-span-2">
          <label class="label">
            <span class="label-text">Nombre del Proyecto *</span>
          </label>
          <input
            v-model="formulario.nombre"
            type="text"
            class="input input-bordered"
            placeholder="Nombre del proyecto minero"
            required
          />
        </div>

        <!-- Cliente -->
        <div class="form-control">
          <label class="label">
            <span class="label-text">Cliente</span>
          </label>
          <select v-model="formulario.cliente_id" class="select select-bordered">
            <option :value="null">Sin cliente asignado</option>
            <option
              v-for="cliente in clientesStore.clientes"
              :key="cliente.id"
              :value="cliente.id"
            >
              {{ cliente.razon_social }}
            </option>
          </select>
        </div>

        <!-- Titular -->
        <div class="form-control">
          <label class="label">
            <span class="label-text">Titular</span>
          </label>
          <input
            v-model="formulario.titular"
            type="text"
            class="input input-bordered"
            placeholder="Nombre del titular"
          />
        </div>
      </div>
    </div>

    <!-- Seccion: Ubicacion -->
    <div>
      <h3 class="font-semibold mb-4">Ubicacion</h3>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div class="form-control">
          <label class="label">
            <span class="label-text">Region</span>
          </label>
          <select v-model="formulario.region" class="select select-bordered">
            <option :value="null">Seleccionar region</option>
            <option v-for="region in REGIONES_CHILE" :key="region" :value="region">
              {{ region }}
            </option>
          </select>
        </div>

        <div class="form-control">
          <label class="label">
            <span class="label-text">Comuna</span>
          </label>
          <select
            v-model="formulario.comuna"
            class="select select-bordered"
            :disabled="!formulario.region"
          >
            <option :value="null">Seleccionar comuna</option>
            <option v-for="comuna in comunasDisponibles" :key="comuna" :value="comuna">
              {{ comuna }}
            </option>
          </select>
        </div>
      </div>
    </div>

    <!-- Seccion: Caracteristicas Tecnicas -->
    <div>
      <h3 class="font-semibold mb-4">Caracteristicas Tecnicas</h3>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div class="form-control">
          <label class="label">
            <span class="label-text">Tipo de Mineria</span>
          </label>
          <select v-model="formulario.tipo_mineria" class="select select-bordered">
            <option :value="null">Seleccionar</option>
            <option v-for="tipo in TIPOS_MINERIA" :key="tipo" :value="tipo">
              {{ tipo }}
            </option>
          </select>
        </div>

        <div class="form-control">
          <label class="label">
            <span class="label-text">Mineral Principal</span>
          </label>
          <input
            v-model="formulario.mineral_principal"
            type="text"
            class="input input-bordered"
            placeholder="Ej: Cobre, Litio"
          />
        </div>

        <div class="form-control">
          <label class="label">
            <span class="label-text">Fase</span>
          </label>
          <select v-model="formulario.fase" class="select select-bordered">
            <option :value="null">Seleccionar</option>
            <option v-for="fase in FASES_PROYECTO" :key="fase" :value="fase">
              {{ fase }}
            </option>
          </select>
        </div>

        <div class="form-control">
          <label class="label">
            <span class="label-text">Superficie (ha)</span>
          </label>
          <input
            v-model.number="formulario.superficie_ha"
            type="number"
            class="input input-bordered"
            min="0"
            step="0.1"
          />
        </div>

        <div class="form-control">
          <label class="label">
            <span class="label-text">Vida Util (anos)</span>
          </label>
          <input
            v-model.number="formulario.vida_util_anos"
            type="number"
            class="input input-bordered"
            min="0"
          />
        </div>

        <div class="form-control">
          <label class="label">
            <span class="label-text">Inversion (MUSD)</span>
          </label>
          <input
            v-model.number="formulario.inversion_musd"
            type="number"
            class="input input-bordered"
            min="0"
            step="0.1"
          />
        </div>
      </div>
    </div>

    <!-- Seccion: Recursos -->
    <div>
      <h3 class="font-semibold mb-4">Recursos</h3>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div class="form-control">
          <label class="label">
            <span class="label-text">Uso de Agua (L/s)</span>
          </label>
          <input
            v-model.number="formulario.uso_agua_lps"
            type="number"
            class="input input-bordered"
            min="0"
            step="0.1"
          />
        </div>

        <div class="form-control">
          <label class="label">
            <span class="label-text">Fuente de Agua</span>
          </label>
          <select v-model="formulario.fuente_agua" class="select select-bordered">
            <option :value="null">Seleccionar</option>
            <option v-for="fuente in FUENTES_AGUA" :key="fuente" :value="fuente">
              {{ fuente }}
            </option>
          </select>
        </div>

        <div class="form-control">
          <label class="label">
            <span class="label-text">Energia (MW)</span>
          </label>
          <input
            v-model.number="formulario.energia_mw"
            type="number"
            class="input input-bordered"
            min="0"
            step="0.1"
          />
        </div>
      </div>
    </div>

    <!-- Seccion: Personal -->
    <div>
      <h3 class="font-semibold mb-4">Personal</h3>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div class="form-control">
          <label class="label">
            <span class="label-text">Trabajadores Construccion</span>
          </label>
          <input
            v-model.number="formulario.trabajadores_construccion"
            type="number"
            class="input input-bordered"
            min="0"
          />
        </div>

        <div class="form-control">
          <label class="label">
            <span class="label-text">Trabajadores Operacion</span>
          </label>
          <input
            v-model.number="formulario.trabajadores_operacion"
            type="number"
            class="input input-bordered"
            min="0"
          />
        </div>
      </div>
    </div>

    <!-- Descripcion -->
    <div class="form-control">
      <label class="label">
        <span class="label-text">Descripcion</span>
      </label>
      <textarea
        v-model="formulario.descripcion"
        class="textarea textarea-bordered"
        rows="3"
        placeholder="Descripcion general del proyecto..."
      ></textarea>
    </div>

    <!-- Boton guardar -->
    <div class="flex justify-end">
      <button type="submit" class="btn btn-primary" :disabled="guardando">
        <span v-if="guardando" class="loading loading-spinner loading-sm"></span>
        <span v-else>Guardar</span>
      </button>
    </div>
  </form>
</template>
