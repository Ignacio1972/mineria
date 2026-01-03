<script setup lang="ts">
import { computed } from 'vue'
import type { AnexoRequerido, EstadoAnexo } from '@/types'
import { ESTADO_ANEXO_LABELS, ESTADO_ANEXO_COLORS } from '@/types'

const props = defineProps<{
  anexos: AnexoRequerido[]
  readonly?: boolean
}>()

const emit = defineEmits<{
  (e: 'actualizar', codigo: string, estado: EstadoAnexo): void
}>()

const anexosOrdenados = computed(() =>
  [...props.anexos].sort((a, b) => a.codigo.localeCompare(b.codigo))
)

const estadoOpciones: EstadoAnexo[] = ['pendiente', 'en_elaboracion', 'completado']

const resumen = computed(() => ({
  total: props.anexos.length,
  obligatorios: props.anexos.filter(a => a.obligatorio).length,
  completados: props.anexos.filter(a => a.estado === 'completado').length,
  enElaboracion: props.anexos.filter(a => a.estado === 'en_elaboracion').length,
  pendientes: props.anexos.filter(a => a.estado === 'pendiente').length,
}))
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
        <div class="stat-title text-xs">Completados</div>
        <div class="stat-value text-xl text-success">{{ resumen.completados }}</div>
      </div>
      <div class="stat place-items-center py-3">
        <div class="stat-title text-xs">En Elaboracion</div>
        <div class="stat-value text-xl text-warning">{{ resumen.enElaboracion }}</div>
      </div>
      <div class="stat place-items-center py-3">
        <div class="stat-title text-xs">Pendientes</div>
        <div class="stat-value text-xl text-base-content/50">{{ resumen.pendientes }}</div>
      </div>
    </div>

    <!-- Lista de anexos -->
    <div class="grid gap-3 grid-cols-1 md:grid-cols-2">
      <div
        v-for="anexo in anexosOrdenados"
        :key="anexo.codigo"
        class="card bg-base-200 shadow-sm"
      >
        <div class="card-body p-4">
          <div class="flex items-start justify-between gap-3">
            <div class="flex-1">
              <div class="flex items-center gap-2 mb-1">
                <span class="font-mono font-bold text-sm">{{ anexo.codigo }}</span>
                <span
                  v-if="anexo.obligatorio"
                  class="badge badge-error badge-xs"
                >
                  Obligatorio
                </span>
              </div>
              <h4 class="font-medium text-sm">{{ anexo.nombre }}</h4>
              <p v-if="anexo.descripcion" class="text-xs opacity-70 mt-1">
                {{ anexo.descripcion }}
              </p>
              <p v-if="anexo.profesional_responsable" class="text-xs opacity-60 mt-1">
                Responsable: {{ anexo.profesional_responsable }}
              </p>
            </div>

            <div class="flex flex-col items-end gap-2">
              <span
                class="badge badge-sm"
                :class="ESTADO_ANEXO_COLORS[anexo.estado]"
              >
                {{ ESTADO_ANEXO_LABELS[anexo.estado] }}
              </span>

              <select
                v-if="!readonly"
                class="select select-bordered select-xs"
                :value="anexo.estado"
                @change="emit('actualizar', anexo.codigo, ($event.target as HTMLSelectElement).value as EstadoAnexo)"
              >
                <option
                  v-for="estado in estadoOpciones"
                  :key="estado"
                  :value="estado"
                >
                  {{ ESTADO_ANEXO_LABELS[estado] }}
                </option>
              </select>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Mensaje si no hay anexos -->
    <div v-if="!anexos.length" class="text-center py-8 opacity-60">
      No hay anexos identificados
    </div>
  </div>
</template>
