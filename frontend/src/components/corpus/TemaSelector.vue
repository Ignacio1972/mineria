<script setup lang="ts">
import { computed } from 'vue'
import type { Tema, GrupoTema } from '@/types'
import { GRUPOS_TEMA } from '@/types'

const props = defineProps<{
  temas: Tema[]
  seleccionados: string[]
  agrupados?: Record<GrupoTema, Tema[]>
  multiselect?: boolean
  mostrarCantidad?: boolean
}>()

const emit = defineEmits<{
  'update:seleccionados': [codigos: string[]]
  toggle: [codigo: string]
}>()

const temasAgrupados = computed(() => {
  if (props.agrupados) return props.agrupados

  const grupos: Record<GrupoTema, Tema[]> = {
    componente_ambiental: [],
    trigger_art11: [],
    etapa_seia: [],
    sector: [],
    otro: [],
  }

  props.temas.forEach((tema) => {
    if (grupos[tema.grupo]) {
      grupos[tema.grupo].push(tema)
    } else {
      grupos.otro.push(tema)
    }
  })

  return grupos
})

const gruposConTemas = computed(() => {
  return (Object.entries(temasAgrupados.value) as [GrupoTema, Tema[]][]).filter(
    ([, temas]) => temas.length > 0
  )
})

function estaSeleccionado(codigo: string): boolean {
  return props.seleccionados.includes(codigo)
}

function toggleTema(codigo: string) {
  emit('toggle', codigo)

  if (props.multiselect) {
    const nuevos = estaSeleccionado(codigo)
      ? props.seleccionados.filter((c) => c !== codigo)
      : [...props.seleccionados, codigo]
    emit('update:seleccionados', nuevos)
  } else {
    emit('update:seleccionados', estaSeleccionado(codigo) ? [] : [codigo])
  }
}

function limpiarSeleccion() {
  emit('update:seleccionados', [])
}

function getColorBadge(tema: Tema): string {
  if (tema.color) {
    return `background-color: ${tema.color}; color: white;`
  }
  return ''
}
</script>

<template>
  <div class="tema-selector space-y-3">
    <!-- Header con limpiar -->
    <div v-if="seleccionados.length > 0" class="flex items-center justify-between">
      <span class="text-xs opacity-60">{{ seleccionados.length }} tema(s) seleccionado(s)</span>
      <button class="btn btn-ghost btn-xs" @click="limpiarSeleccion">Limpiar</button>
    </div>

    <!-- Grupos de temas -->
    <div v-for="[grupo, temasGrupo] in gruposConTemas" :key="grupo" class="space-y-1">
      <h4 class="text-xs font-semibold opacity-70 uppercase tracking-wide">
        {{ GRUPOS_TEMA[grupo]?.label || grupo }}
      </h4>

      <div class="flex flex-wrap gap-1">
        <button
          v-for="tema in temasGrupo"
          :key="tema.id"
          class="badge badge-lg gap-1 cursor-pointer transition-all hover:scale-105"
          :class="estaSeleccionado(tema.codigo) ? 'badge-primary' : 'badge-outline'"
          :style="estaSeleccionado(tema.codigo) ? getColorBadge(tema) : ''"
          @click="toggleTema(tema.codigo)"
        >
          <span>{{ tema.nombre }}</span>
          <span v-if="mostrarCantidad && tema.cantidad_fragmentos > 0" class="opacity-60">
            ({{ tema.cantidad_fragmentos }})
          </span>
        </button>
      </div>
    </div>

    <!-- Estado vacio -->
    <div v-if="gruposConTemas.length === 0" class="text-center py-4 opacity-50">
      <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 mx-auto mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
      </svg>
      <p class="text-sm">Sin temas disponibles</p>
    </div>
  </div>
</template>

<style scoped>
.badge {
  font-weight: 500;
}
</style>
