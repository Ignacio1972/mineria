<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import type { DocumentoDetalle, DocumentoUpdateData, Categoria } from '@/types'
import { TIPOS_DOCUMENTO, ESTADOS_DOCUMENTO } from '@/types'

const props = defineProps<{
  documento: DocumentoDetalle | null
  categorias: Categoria[]
  procesando: boolean
}>()

const emit = defineEmits<{
  (e: 'guardar', data: DocumentoUpdateData): void
  (e: 'cerrar'): void
}>()

// Formulario de edición
const formulario = ref<DocumentoUpdateData>({})

// Opciones predefinidas
const TRIGGERS_ART11 = ['a', 'b', 'c', 'd', 'e', 'f']
const COMPONENTES_AMBIENTALES = [
  'Agua', 'Aire', 'Suelo', 'Flora', 'Fauna', 'Ecosistemas',
  'Paisaje', 'Patrimonio', 'Medio Humano', 'Ruido', 'Residuos'
]
const SECTORES = [
  'Minería', 'Energía', 'Transporte', 'Industria', 'Infraestructura',
  'Acuicultura', 'Forestal', 'Agropecuario', 'Inmobiliario', 'Otros'
]
const REGIONES = [
  'Arica y Parinacota', 'Tarapacá', 'Antofagasta', 'Atacama', 'Coquimbo',
  'Valparaíso', 'Metropolitana', 'O\'Higgins', 'Maule', 'Ñuble',
  'Biobío', 'Araucanía', 'Los Ríos', 'Los Lagos', 'Aysén', 'Magallanes'
]

// Inicializar formulario cuando cambia el documento
watch(
  () => props.documento,
  (doc) => {
    if (doc) {
      formulario.value = {
        titulo: doc.titulo,
        tipo: doc.tipo,
        numero: doc.numero || undefined,
        fecha_publicacion: doc.fecha_publicacion || undefined,
        fecha_vigencia: doc.fecha_vigencia || undefined,
        organismo: doc.organismo || undefined,
        url_fuente: doc.url_fuente || undefined,
        resolucion_aprobatoria: doc.resolucion_aprobatoria || undefined,
        estado: doc.estado,
        categoria_id: doc.categoria_id || undefined,
        sectores: doc.sectores || [],
        triggers_art11: doc.triggers_art11 || [],
        componentes_ambientales: doc.componentes_ambientales || [],
        regiones_aplicables: doc.regiones_aplicables || [],
        etapa_proceso: doc.etapa_proceso || undefined,
        actor_principal: doc.actor_principal || undefined,
        resumen: doc.resumen || undefined,
        palabras_clave: doc.palabras_clave || [],
      }
    }
  },
  { immediate: true }
)

// Computed para verificar cambios
const hayaCambios = computed(() => {
  if (!props.documento) return false
  return JSON.stringify(formulario.value) !== JSON.stringify({
    titulo: props.documento.titulo,
    tipo: props.documento.tipo,
    numero: props.documento.numero || undefined,
    fecha_publicacion: props.documento.fecha_publicacion || undefined,
    fecha_vigencia: props.documento.fecha_vigencia || undefined,
    organismo: props.documento.organismo || undefined,
    url_fuente: props.documento.url_fuente || undefined,
    resolucion_aprobatoria: props.documento.resolucion_aprobatoria || undefined,
    estado: props.documento.estado,
    categoria_id: props.documento.categoria_id || undefined,
    sectores: props.documento.sectores || [],
    triggers_art11: props.documento.triggers_art11 || [],
    componentes_ambientales: props.documento.componentes_ambientales || [],
    regiones_aplicables: props.documento.regiones_aplicables || [],
    etapa_proceso: props.documento.etapa_proceso || undefined,
    actor_principal: props.documento.actor_principal || undefined,
    resumen: props.documento.resumen || undefined,
    palabras_clave: props.documento.palabras_clave || [],
  })
})

// Handlers
function guardar() {
  if (!hayaCambios.value) return
  emit('guardar', formulario.value)
}

function toggleEnArray(array: string[] | undefined, valor: string): string[] {
  const arr = array || []
  const idx = arr.indexOf(valor)
  if (idx >= 0) {
    return arr.filter((v) => v !== valor)
  }
  return [...arr, valor]
}

// Palabras clave como string separado por comas
const palabrasClaveStr = computed({
  get: () => formulario.value.palabras_clave?.join(', ') || '',
  set: (val: string) => {
    formulario.value.palabras_clave = val
      .split(',')
      .map((s) => s.trim())
      .filter(Boolean)
  },
})
</script>

<template>
  <dialog :class="{ 'modal modal-open': documento }">
    <div class="modal-box max-w-4xl max-h-[90vh] overflow-y-auto">
      <h3 class="font-bold text-lg mb-4 flex items-center gap-2">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
        </svg>
        Editar Documento
      </h3>

      <form @submit.prevent="guardar" class="space-y-6">
        <!-- Seccion: Información básica -->
        <div class="space-y-4">
          <h4 class="font-medium text-sm text-base-content/70 border-b border-base-300 pb-1">
            Información Básica
          </h4>

          <!-- Titulo -->
          <div class="form-control">
            <label class="label">
              <span class="label-text">Título *</span>
            </label>
            <input
              v-model="formulario.titulo"
              type="text"
              class="input input-bordered"
              placeholder="Título del documento"
              required
            />
          </div>

          <!-- Tipo, Numero, Estado -->
          <div class="grid grid-cols-3 gap-4">
            <div class="form-control">
              <label class="label">
                <span class="label-text">Tipo</span>
              </label>
              <select v-model="formulario.tipo" class="select select-bordered">
                <option v-for="tipo in TIPOS_DOCUMENTO" :key="tipo.value" :value="tipo.value">
                  {{ tipo.label }}
                </option>
              </select>
            </div>

            <div class="form-control">
              <label class="label">
                <span class="label-text">Número</span>
              </label>
              <input
                v-model="formulario.numero"
                type="text"
                class="input input-bordered"
                placeholder="Ej: 19.300"
              />
            </div>

            <div class="form-control">
              <label class="label">
                <span class="label-text">Estado</span>
              </label>
              <select v-model="formulario.estado" class="select select-bordered">
                <option v-for="estado in ESTADOS_DOCUMENTO" :key="estado.value" :value="estado.value">
                  {{ estado.label }}
                </option>
              </select>
            </div>
          </div>

          <!-- Categoria -->
          <div class="form-control">
            <label class="label">
              <span class="label-text">Categoría</span>
            </label>
            <select v-model="formulario.categoria_id" class="select select-bordered">
              <option :value="undefined">Sin categoría</option>
              <option v-for="cat in categorias" :key="cat.id" :value="cat.id">
                {{ cat.nombre }}
              </option>
            </select>
          </div>
        </div>

        <!-- Seccion: Fechas y organismo -->
        <div class="space-y-4">
          <h4 class="font-medium text-sm text-base-content/70 border-b border-base-300 pb-1">
            Fechas y Origen
          </h4>

          <div class="grid grid-cols-2 gap-4">
            <div class="form-control">
              <label class="label">
                <span class="label-text">Fecha Publicación</span>
              </label>
              <input
                v-model="formulario.fecha_publicacion"
                type="date"
                class="input input-bordered"
              />
            </div>

            <div class="form-control">
              <label class="label">
                <span class="label-text">Fecha Vigencia</span>
              </label>
              <input
                v-model="formulario.fecha_vigencia"
                type="date"
                class="input input-bordered"
              />
            </div>
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div class="form-control">
              <label class="label">
                <span class="label-text">Organismo</span>
              </label>
              <input
                v-model="formulario.organismo"
                type="text"
                class="input input-bordered"
                placeholder="Ej: Ministerio del Medio Ambiente"
              />
            </div>

            <div class="form-control">
              <label class="label">
                <span class="label-text">Resolución Aprobatoria</span>
              </label>
              <input
                v-model="formulario.resolucion_aprobatoria"
                type="text"
                class="input input-bordered"
                placeholder="Ej: Res. Ex. 123/2024"
              />
            </div>
          </div>

          <div class="form-control">
            <label class="label">
              <span class="label-text">URL Fuente</span>
            </label>
            <input
              v-model="formulario.url_fuente"
              type="url"
              class="input input-bordered"
              placeholder="https://..."
            />
          </div>
        </div>

        <!-- Seccion: Clasificación temática -->
        <div class="space-y-4">
          <h4 class="font-medium text-sm text-base-content/70 border-b border-base-300 pb-1">
            Clasificación Temática
          </h4>

          <!-- Triggers Art. 11 -->
          <div class="form-control">
            <label class="label">
              <span class="label-text">Triggers Art. 11</span>
            </label>
            <div class="flex flex-wrap gap-2">
              <label
                v-for="trigger in TRIGGERS_ART11"
                :key="trigger"
                class="label cursor-pointer gap-2 bg-base-200 rounded-lg px-3 py-1"
              >
                <input
                  type="checkbox"
                  class="checkbox checkbox-sm checkbox-error"
                  :checked="formulario.triggers_art11?.includes(trigger)"
                  @change="formulario.triggers_art11 = toggleEnArray(formulario.triggers_art11, trigger)"
                />
                <span class="label-text">Letra {{ trigger }})</span>
              </label>
            </div>
          </div>

          <!-- Componentes ambientales -->
          <div class="form-control">
            <label class="label">
              <span class="label-text">Componentes Ambientales</span>
            </label>
            <div class="flex flex-wrap gap-2">
              <label
                v-for="comp in COMPONENTES_AMBIENTALES"
                :key="comp"
                class="label cursor-pointer gap-2 bg-base-200 rounded-lg px-3 py-1"
              >
                <input
                  type="checkbox"
                  class="checkbox checkbox-sm checkbox-info"
                  :checked="formulario.componentes_ambientales?.includes(comp)"
                  @change="formulario.componentes_ambientales = toggleEnArray(formulario.componentes_ambientales, comp)"
                />
                <span class="label-text text-sm">{{ comp }}</span>
              </label>
            </div>
          </div>

          <!-- Sectores -->
          <div class="form-control">
            <label class="label">
              <span class="label-text">Sectores</span>
            </label>
            <div class="flex flex-wrap gap-2">
              <label
                v-for="sector in SECTORES"
                :key="sector"
                class="label cursor-pointer gap-2 bg-base-200 rounded-lg px-3 py-1"
              >
                <input
                  type="checkbox"
                  class="checkbox checkbox-sm checkbox-success"
                  :checked="formulario.sectores?.includes(sector)"
                  @change="formulario.sectores = toggleEnArray(formulario.sectores, sector)"
                />
                <span class="label-text text-sm">{{ sector }}</span>
              </label>
            </div>
          </div>

          <!-- Regiones aplicables -->
          <div class="form-control">
            <label class="label">
              <span class="label-text">Regiones Aplicables</span>
            </label>
            <div class="grid grid-cols-4 gap-2">
              <label
                v-for="region in REGIONES"
                :key="region"
                class="label cursor-pointer gap-2 bg-base-200 rounded-lg px-2 py-1"
              >
                <input
                  type="checkbox"
                  class="checkbox checkbox-xs"
                  :checked="formulario.regiones_aplicables?.includes(region)"
                  @change="formulario.regiones_aplicables = toggleEnArray(formulario.regiones_aplicables, region)"
                />
                <span class="label-text text-xs">{{ region }}</span>
              </label>
            </div>
          </div>
        </div>

        <!-- Seccion: Contenido -->
        <div class="space-y-4">
          <h4 class="font-medium text-sm text-base-content/70 border-b border-base-300 pb-1">
            Contenido y Resumen
          </h4>

          <!-- Resumen -->
          <div class="form-control">
            <label class="label">
              <span class="label-text">Resumen</span>
            </label>
            <textarea
              v-model="formulario.resumen"
              class="textarea textarea-bordered h-24"
              placeholder="Resumen del documento..."
            ></textarea>
          </div>

          <!-- Palabras clave -->
          <div class="form-control">
            <label class="label">
              <span class="label-text">Palabras Clave</span>
              <span class="label-text-alt">Separadas por coma</span>
            </label>
            <input
              v-model="palabrasClaveStr"
              type="text"
              class="input input-bordered"
              placeholder="palabra1, palabra2, palabra3"
            />
          </div>

          <!-- Etapa y actor -->
          <div class="grid grid-cols-2 gap-4">
            <div class="form-control">
              <label class="label">
                <span class="label-text">Etapa del Proceso</span>
              </label>
              <select v-model="formulario.etapa_proceso" class="select select-bordered">
                <option :value="undefined">Sin especificar</option>
                <option value="admisibilidad">Admisibilidad</option>
                <option value="evaluacion">Evaluación</option>
                <option value="calificacion">Calificación</option>
                <option value="seguimiento">Seguimiento</option>
                <option value="fiscalizacion">Fiscalización</option>
              </select>
            </div>

            <div class="form-control">
              <label class="label">
                <span class="label-text">Actor Principal</span>
              </label>
              <select v-model="formulario.actor_principal" class="select select-bordered">
                <option :value="undefined">Sin especificar</option>
                <option value="titular">Titular</option>
                <option value="sea">SEA</option>
                <option value="organo_sectorial">Órgano Sectorial</option>
                <option value="comunidad">Comunidad</option>
                <option value="tribunal">Tribunal</option>
              </select>
            </div>
          </div>
        </div>

        <!-- Acciones -->
        <div class="modal-action">
          <button type="button" class="btn btn-ghost" @click="emit('cerrar')">
            Cancelar
          </button>
          <button
            type="submit"
            class="btn btn-primary"
            :disabled="procesando || !hayaCambios"
          >
            <span v-if="procesando" class="loading loading-spinner loading-sm"></span>
            <span v-else-if="!hayaCambios">Sin cambios</span>
            <span v-else>Guardar cambios</span>
          </button>
        </div>
      </form>
    </div>

    <form method="dialog" class="modal-backdrop">
      <button @click="emit('cerrar')">close</button>
    </form>
  </dialog>
</template>
