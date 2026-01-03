<script setup lang="ts">
import { useMap } from '@/composables/useMap';
import { computed, ref } from 'vue';
import type { GeometriaGeoJSON } from '@/types';

const props = defineProps<{
  tieneGeometria?: boolean
}>()

const emit = defineEmits<{
  (e: 'importar', geom: GeometriaGeoJSON): void
}>()

const {
  modoEdicion,
  herramientaActiva,
  activarDibujo,
  activarModificar,
  activarEliminar,
  desactivarEdicion,
  centrarEnGeometria,
} = useMap();

const geometriaPresente = computed(() => props.tieneGeometria ?? false);
const fileInput = ref<HTMLInputElement | null>(null);
const importando = ref(false);
const errorImport = ref<string | null>(null);

// Función recursiva para eliminar la dimensión Z de las coordenadas
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function eliminarDimensionZ(coords: any): any {
  if (!Array.isArray(coords)) return coords;

  // Si es un punto [lon, lat, z?]
  if (typeof coords[0] === 'number') {
    return [coords[0], coords[1]]; // Solo lon, lat
  }

  // Si es un array de arrays, procesar recursivamente
  return coords.map(eliminarDimensionZ);
}

function abrirSelectorArchivo() {
  fileInput.value?.click();
}

async function onArchivoSeleccionado(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) return;

  // Validar extensión
  const extension = file.name.toLowerCase().split('.').pop();
  if (extension !== 'kml' && extension !== 'kmz') {
    errorImport.value = 'Solo se permiten archivos KML o KMZ';
    setTimeout(() => errorImport.value = null, 3000);
    input.value = '';
    return;
  }

  importando.value = true;
  errorImport.value = null;

  try {
    const contenido = await file.text();

    // Importar dinámicamente el parser de KML de OpenLayers
    const KML = (await import('ol/format/KML')).default;
    const kmlFormat = new KML({ extractStyles: false });

    // Parsear el KML
    const features = kmlFormat.readFeatures(contenido, {
      dataProjection: 'EPSG:4326',
      featureProjection: 'EPSG:4326',
    });

    if (features.length === 0) {
      throw new Error('No se encontraron geometrías en el archivo');
    }

    // Buscar el primer polígono válido
    let geometria: GeometriaGeoJSON | null = null;

    for (const feature of features) {
      const geom = feature.getGeometry();
      if (!geom) continue;

      const type = geom.getType();
      if (type === 'Polygon' || type === 'MultiPolygon') {
        const GeoJSON = (await import('ol/format/GeoJSON')).default;
        const geojsonFormat = new GeoJSON();
        geometria = geojsonFormat.writeGeometryObject(geom, {
          dataProjection: 'EPSG:4326',
          featureProjection: 'EPSG:4326',
        }) as GeometriaGeoJSON;

        // Eliminar dimensión Z si existe (KML suele incluir altitud)
        if (geometria && geometria.coordinates) {
          geometria.coordinates = eliminarDimensionZ(geometria.coordinates);
        }
        break;
      }
    }

    if (!geometria) {
      throw new Error('El archivo no contiene polígonos válidos');
    }

    emit('importar', geometria);

    // Centrar el mapa en la geometría importada
    centrarEnGeometria(geometria);
  } catch (e) {
    console.error('Error importando KML:', e);
    errorImport.value = e instanceof Error ? e.message : 'Error al importar archivo';
    setTimeout(() => errorImport.value = null, 4000);
  } finally {
    importando.value = false;
    input.value = '';
  }
}
</script>

<template>
  <div class="bg-base-100 rounded-lg shadow-lg p-2">
    <div class="flex gap-2">
      <div class="tooltip" data-tip="Dibujar polígono">
        <button
          class="btn btn-sm"
          :class="herramientaActiva === 'polygon' ? 'btn-primary' : 'btn-ghost'"
          @click="activarDibujo"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6z" />
          </svg>
        </button>
      </div>

      <div class="tooltip" data-tip="Importar KML">
        <button
          class="btn btn-sm btn-ghost"
          :disabled="importando"
          @click="abrirSelectorArchivo"
        >
          <span v-if="importando" class="loading loading-spinner loading-xs"></span>
          <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
          </svg>
        </button>
        <input
          ref="fileInput"
          type="file"
          accept=".kml,.kmz"
          class="hidden"
          @change="onArchivoSeleccionado"
        />
      </div>

      <div class="divider divider-horizontal mx-0"></div>

      <div class="tooltip" data-tip="Modificar polígono">
        <button
          class="btn btn-sm"
          :class="herramientaActiva === 'modify' ? 'btn-secondary' : 'btn-ghost'"
          :disabled="!geometriaPresente"
          @click="activarModificar"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
          </svg>
        </button>
      </div>

      <div class="tooltip" data-tip="Eliminar polígono">
        <button
          class="btn btn-sm btn-ghost"
          :disabled="!geometriaPresente"
          @click="activarEliminar"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
        </button>
      </div>

      <div v-if="modoEdicion" class="divider divider-horizontal mx-0"></div>

      <button
        v-if="modoEdicion"
        class="btn btn-sm btn-ghost"
        @click="desactivarEdicion"
      >
        Cancelar
      </button>
    </div>

    <!-- Mensajes de estado -->
    <div v-if="errorImport" class="mt-2 text-xs text-error">
      {{ errorImport }}
    </div>
    <div v-else-if="modoEdicion" class="mt-2 text-xs opacity-70">
      <span v-if="herramientaActiva === 'polygon'">
        Haga clic en el mapa para dibujar el polígono. Doble clic para finalizar.
      </span>
      <span v-else-if="herramientaActiva === 'modify'">
        Arrastre los vértices para modificar el polígono.
      </span>
    </div>
  </div>
</template>
