<script setup lang="ts">
import { computed } from 'vue'
import type { PASConEstado, EstadoPAS } from '@/types'
import { ESTADO_PAS_LABELS, ESTADO_PAS_COLORS } from '@/types'

const props = defineProps<{
  pas: PASConEstado[]
  readonly?: boolean
}>()

const emit = defineEmits<{
  (e: 'actualizar', articulo: number, estado: EstadoPAS): void
}>()

const pasOrdenados = computed(() =>
  [...props.pas].sort((a, b) => a.articulo - b.articulo)
)

const estadoOpciones: EstadoPAS[] = [
  'identificado',
  'requerido',
  'en_tramite',
  'aprobado',
  'no_aplica'
]

const resumen = computed(() => ({
  total: props.pas.length,
  obligatorios: props.pas.filter(p => p.obligatoriedad === 'obligatorio').length,
  aprobados: props.pas.filter(p => p.estado === 'aprobado').length,
  enTramite: props.pas.filter(p => p.estado === 'en_tramite').length,
  pendientes: props.pas.filter(p => p.estado === 'identificado' || p.estado === 'requerido').length,
}))

function getObligatoriedadColor(ob: string): string {
  switch (ob) {
    case 'obligatorio':
      return 'badge-error'
    case 'frecuente':
      return 'badge-warning'
    default:
      return 'badge-ghost'
  }
}
</script>

<template>
  <div class="space-y-4">
    <!-- Resumen -->
    <div class="stats shadow w-full bg-base-200">
      <div class="stat place-items-center py-3">
        <div class="stat-title text-xs">Total</div>
        <div class="stat-value text-xl">{{ resumen.total }}</div>
      </div>
      <div class="stat place-items-center py-3">
        <div class="stat-title text-xs">Obligatorios</div>
        <div class="stat-value text-xl text-error">{{ resumen.obligatorios }}</div>
      </div>
      <div class="stat place-items-center py-3">
        <div class="stat-title text-xs">Aprobados</div>
        <div class="stat-value text-xl text-success">{{ resumen.aprobados }}</div>
      </div>
      <div class="stat place-items-center py-3">
        <div class="stat-title text-xs">En Tramite</div>
        <div class="stat-value text-xl text-info">{{ resumen.enTramite }}</div>
      </div>
      <div class="stat place-items-center py-3">
        <div class="stat-title text-xs">Pendientes</div>
        <div class="stat-value text-xl text-warning">{{ resumen.pendientes }}</div>
      </div>
    </div>

    <!-- Lista de PAS -->
    <div class="overflow-x-auto">
      <table class="table table-sm">
        <thead>
          <tr>
            <th>Art.</th>
            <th>Nombre</th>
            <th>Organismo</th>
            <th>Obligatoriedad</th>
            <th>Estado</th>
            <th v-if="!readonly">Cambiar</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="p in pasOrdenados"
            :key="p.articulo"
            class="hover"
          >
            <td class="font-mono font-bold">{{ p.articulo }}</td>
            <td>
              <div class="font-medium">{{ p.nombre }}</div>
              <div v-if="p.razon_aplicacion" class="text-xs opacity-60">
                {{ p.razon_aplicacion }}
              </div>
            </td>
            <td class="text-sm">{{ p.organismo }}</td>
            <td>
              <span
                class="badge badge-sm"
                :class="getObligatoriedadColor(p.obligatoriedad)"
              >
                {{ p.obligatoriedad }}
              </span>
            </td>
            <td>
              <span
                class="badge"
                :class="ESTADO_PAS_COLORS[p.estado]"
              >
                {{ ESTADO_PAS_LABELS[p.estado] }}
              </span>
            </td>
            <td v-if="!readonly">
              <select
                class="select select-bordered select-xs"
                :value="p.estado"
                @change="emit('actualizar', p.articulo, ($event.target as HTMLSelectElement).value as EstadoPAS)"
              >
                <option
                  v-for="estado in estadoOpciones"
                  :key="estado"
                  :value="estado"
                >
                  {{ ESTADO_PAS_LABELS[estado] }}
                </option>
              </select>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Mensaje si no hay PAS -->
    <div v-if="!pas.length" class="text-center py-8 opacity-60">
      No hay PAS identificados
    </div>
  </div>
</template>
