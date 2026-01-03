<script setup lang="ts">
import { computed } from 'vue'
import type { PreguntaConRespuesta } from '@/types/recopilacion'

const props = defineProps<{
  pregunta: PreguntaConRespuesta
  modelValue: unknown
  disabled?: boolean
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: unknown): void
}>()

const valor = computed({
  get: () => props.modelValue ?? props.pregunta.respuesta_actual ?? '',
  set: (v) => emit('update:modelValue', v),
})

const esInvalida = computed(
  () => !props.pregunta.es_valida && props.pregunta.mensaje_validacion
)

const claseInput = computed(() => {
  if (esInvalida.value) return 'input-error'
  if (valor.value !== '' && valor.value !== null) return 'input-success'
  return ''
})
</script>

<template>
  <div class="form-control w-full">
    <!-- Label -->
    <label class="label">
      <span class="label-text">
        {{ pregunta.pregunta }}
        <span v-if="pregunta.es_obligatoria" class="text-error">*</span>
      </span>
    </label>

    <!-- Descripcion -->
    <p v-if="pregunta.descripcion" class="text-xs opacity-60 mb-2">
      {{ pregunta.descripcion }}
    </p>

    <!-- Input segun tipo -->
    <!-- Texto -->
    <input
      v-if="pregunta.tipo_respuesta === 'texto'"
      v-model="valor"
      type="text"
      class="input input-bordered w-full"
      :class="claseInput"
      :disabled="disabled"
      :placeholder="`Ingrese ${pregunta.pregunta.toLowerCase()}`"
    />

    <!-- Numero -->
    <input
      v-else-if="pregunta.tipo_respuesta === 'numero'"
      v-model.number="valor"
      type="number"
      class="input input-bordered w-full"
      :class="claseInput"
      :disabled="disabled"
      :min="pregunta.validaciones?.min"
      :max="pregunta.validaciones?.max"
    />

    <!-- Fecha -->
    <input
      v-else-if="pregunta.tipo_respuesta === 'fecha'"
      v-model="valor"
      type="date"
      class="input input-bordered w-full"
      :class="claseInput"
      :disabled="disabled"
    />

    <!-- Seleccion -->
    <select
      v-else-if="pregunta.tipo_respuesta === 'seleccion'"
      v-model="valor"
      class="select select-bordered w-full"
      :class="claseInput"
      :disabled="disabled"
    >
      <option value="">Seleccione una opcion</option>
      <option
        v-for="opcion in pregunta.opciones"
        :key="opcion.valor"
        :value="opcion.valor"
      >
        {{ opcion.etiqueta }}
      </option>
    </select>

    <!-- Seleccion Multiple -->
    <div
      v-else-if="pregunta.tipo_respuesta === 'seleccion_multiple'"
      class="space-y-2"
    >
      <label
        v-for="opcion in pregunta.opciones"
        :key="opcion.valor"
        class="flex items-center gap-2 cursor-pointer"
      >
        <input
          type="checkbox"
          class="checkbox checkbox-sm"
          :value="opcion.valor"
          :checked="Array.isArray(valor) && valor.includes(opcion.valor)"
          :disabled="disabled"
          @change="
            (e) => {
              const checked = (e.target as HTMLInputElement).checked
              const arr = Array.isArray(valor) ? [...valor] : []
              if (checked) {
                arr.push(opcion.valor)
              } else {
                const idx = arr.indexOf(opcion.valor)
                if (idx >= 0) arr.splice(idx, 1)
              }
              valor = arr
            }
          "
        />
        <span class="text-sm">{{ opcion.etiqueta }}</span>
      </label>
    </div>

    <!-- Booleano -->
    <div v-else-if="pregunta.tipo_respuesta === 'booleano'" class="flex gap-4">
      <label class="flex items-center gap-2 cursor-pointer">
        <input
          type="radio"
          class="radio radio-sm"
          :name="`bool_${pregunta.codigo_pregunta}`"
          :checked="valor === true"
          :disabled="disabled"
          @change="valor = true"
        />
        <span>Si</span>
      </label>
      <label class="flex items-center gap-2 cursor-pointer">
        <input
          type="radio"
          class="radio radio-sm"
          :name="`bool_${pregunta.codigo_pregunta}`"
          :checked="valor === false"
          :disabled="disabled"
          @change="valor = false"
        />
        <span>No</span>
      </label>
    </div>

    <!-- Coordenadas -->
    <div
      v-else-if="pregunta.tipo_respuesta === 'coordenadas'"
      class="grid grid-cols-2 gap-2"
    >
      <div>
        <label class="label label-text-alt">Este (X)</label>
        <input
          type="number"
          class="input input-bordered input-sm w-full"
          :class="claseInput"
          :disabled="disabled"
          :value="(valor as {x?: number})?.x ?? ''"
          @input="
            (e) => {
              const v = (valor as {x?: number, y?: number}) ?? {}
              valor = { ...v, x: parseFloat((e.target as HTMLInputElement).value) }
            }
          "
        />
      </div>
      <div>
        <label class="label label-text-alt">Norte (Y)</label>
        <input
          type="number"
          class="input input-bordered input-sm w-full"
          :class="claseInput"
          :disabled="disabled"
          :value="(valor as {y?: number})?.y ?? ''"
          @input="
            (e) => {
              const v = (valor as {x?: number, y?: number}) ?? {}
              valor = { ...v, y: parseFloat((e.target as HTMLInputElement).value) }
            }
          "
        />
      </div>
    </div>

    <!-- Default: textarea -->
    <textarea
      v-else
      :value="String(valor ?? '')"
      class="textarea textarea-bordered w-full"
      :class="claseInput"
      :disabled="disabled"
      rows="3"
      :placeholder="`Ingrese ${pregunta.pregunta.toLowerCase()}`"
      @input="(e) => (valor = (e.target as HTMLTextAreaElement).value)"
    ></textarea>

    <!-- Mensaje de error -->
    <label v-if="esInvalida" class="label">
      <span class="label-text-alt text-error">
        {{ pregunta.mensaje_validacion }}
      </span>
    </label>
  </div>
</template>
