<script setup lang="ts">
import { ref, watch, onMounted } from 'vue';
import { storeToRefs } from 'pinia';
import { useMapStore } from '@/stores/map';
import type { GeometriaGeoJSON } from '@/types';
import MapControls from './MapControls.vue';
import DrawTools from './DrawTools.vue';
import LayerPanel from './LayerPanel.vue';

const props = defineProps<{
  geometria?: GeometriaGeoJSON | null
  readonly?: boolean
}>()

const emit = defineEmits<{
  (e: 'update:geometria', geom: GeometriaGeoJSON | null): void
}>()

function onImportarKML(geom: GeometriaGeoJSON) {
  emit('update:geometria', geom);
}

const GEOSERVER_URL = import.meta.env.VITE_GEOSERVER_URL || 'http://localhost:9085/geoserver';

const mapStore = useMapStore();
const { herramientaDibujo } = storeToRefs(mapStore);

const mapRef = ref<HTMLDivElement | null>(null);
const tooltipRef = ref<HTMLDivElement | null>(null);
const olMap = ref<any>(null);
const layerPanelOpen = ref(false);
const drawInteraction = ref<any>(null);
const modifyInteraction = ref<any>(null);
const projectLayer = ref<any>(null);
const wmsLayers = ref<Map<string, any>>(new Map());
const tooltipOverlay = ref<any>(null);
const tooltipContent = ref<string>('');

// Flag para evitar feedback loop entre OpenLayers y Pinia
// Se usa para ignorar eventos del mapa durante animaciones programáticas
let isProgrammaticMove = false;

onMounted(async () => {
  if (!mapRef.value) return;

  const ol = await import('ol');
  const { Map, View, Overlay } = ol;
  const { Tile: TileLayer, Vector: VectorLayer } = await import('ol/layer');
  const { OSM, XYZ, TileWMS } = await import('ol/source');
  const { Vector: VectorSource } = await import('ol/source');
  const { Draw, Modify } = await import('ol/interaction');
  const { Style, Fill, Stroke } = await import('ol/style');
  const { fromLonLat, toLonLat } = await import('ol/proj');
  const GeoJSON = (await import('ol/format/GeoJSON')).default;

  const projectSource = new VectorSource();

  projectLayer.value = new VectorLayer({
    source: projectSource,
    style: new Style({
      fill: new Fill({
        color: 'rgba(59, 130, 246, 0.3)',
      }),
      stroke: new Stroke({
        color: '#3b82f6',
        width: 3,
      }),
    }),
  });

  const osmLayer = new TileLayer({
    source: new OSM(),
    visible: mapStore.mapaBase === 'osm',
  });

  const satelliteLayer = new TileLayer({
    source: new XYZ({
      url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
      attributions: 'Tiles &copy; Esri',
    }),
    visible: mapStore.mapaBase === 'satellite',
  });

  olMap.value = new Map({
    target: mapRef.value,
    layers: [osmLayer, satelliteLayer, projectLayer.value],
    view: new View({
      center: fromLonLat(mapStore.centro),
      zoom: mapStore.zoom,
    }),
    controls: [], // Desactivar controles predeterminados (usamos nuestros propios MapControls y DrawTools)
  });

  // Crear tooltip overlay
  if (tooltipRef.value) {
    tooltipOverlay.value = new Overlay({
      element: tooltipRef.value,
      positioning: 'bottom-center',
      offset: [0, -10],
      stopEvent: false,
    });
    olMap.value.addOverlay(tooltipOverlay.value);
  }

  // Crear capas WMS para cada capa GIS (local o externa)
  function createWMSLayer(capaId: string, visible: boolean, opacidad: number) {
    // Buscar la definición de la capa para verificar si es externa
    const capaDef = mapStore.capas.find(c => c.id === capaId);

    if (capaDef?.wmsExterno) {
      // Capa WMS externa (ej: CIREN, IDE Chile, etc.)
      const layer = new TileLayer({
        source: new TileWMS({
          url: capaDef.wmsExterno.url,
          params: {
            LAYERS: capaDef.wmsExterno.layers,
            FORMAT: 'image/png',
            TRANSPARENT: true,
          },
          crossOrigin: 'anonymous',
        }),
        visible: visible,
        opacity: opacidad,
      });
      return layer;
    }

    // Capa WMS local (GeoServer)
    const layer = new TileLayer({
      source: new TileWMS({
        url: `${GEOSERVER_URL}/wms`,
        params: {
          LAYERS: `mineria:${capaId}`,
          TILED: true,
          FORMAT: 'image/png',
          TRANSPARENT: true,
        },
        serverType: 'geoserver',
      }),
      visible: visible,
      opacity: opacidad,
    });
    return layer;
  }

  // Inicializar capas WMS
  for (const capa of mapStore.capas) {
    const layer = createWMSLayer(capa.id, capa.visible, capa.opacidad);
    wmsLayers.value.set(capa.id, layer);
    olMap.value.getLayers().insertAt(2, layer); // Insertar antes de projectLayer
  }

  // Watch cambios de visibilidad de capas - watch individual por cada propiedad
  watch(
    () => mapStore.capas.map(c => ({ id: c.id, visible: c.visible, opacidad: c.opacidad })),
    (capasState) => {
      console.log('[GIS] Actualizando capas en mapa:', capasState);
      for (const capa of capasState) {
        const layer = wmsLayers.value.get(capa.id);
        if (layer) {
          console.log(`[GIS] Capa ${capa.id}: visible=${capa.visible}, opacidad=${capa.opacidad}`);
          layer.setVisible(capa.visible);
          layer.setOpacity(capa.opacidad);
        } else if (capa.visible) {
          // Crear nueva capa si no existe
          console.log(`[GIS] Creando nueva capa: ${capa.id}`);
          const newLayer = createWMSLayer(capa.id, capa.visible, capa.opacidad);
          wmsLayers.value.set(capa.id, newLayer);
          olMap.value.getLayers().insertAt(2, newLayer);
        }
      }
    },
    { deep: true, immediate: true }
  );

  // Tooltip en hover sobre features del proyecto
  olMap.value.on('pointermove', (evt: any) => {
    if (evt.dragging || !tooltipOverlay.value) return;

    const feature = olMap.value.forEachFeatureAtPixel(evt.pixel, (f: any) => f);
    if (feature) {
      const props = feature.getProperties();
      const nombre = props.nombre || props.name || 'Área del proyecto';
      tooltipContent.value = nombre;
      tooltipOverlay.value.setPosition(evt.coordinate);
      if (tooltipRef.value) {
        tooltipRef.value.style.display = 'block';
      }
    } else {
      if (tooltipRef.value) {
        tooltipRef.value.style.display = 'none';
      }
    }
  });

  // Cargar capas desde la API
  mapStore.cargarCapasDesdeAPI();

  // Sincronizar vista del mapa al store solo cuando el mapa termina de moverse
  // Usamos 'moveend' en lugar de 'change:center' para evitar actualizaciones durante animaciones
  olMap.value.on('moveend', () => {
    if (isProgrammaticMove) return; // Ignorar si fue un movimiento programático

    const view = olMap.value.getView();
    const center = view.getCenter();
    const currentZoom = view.getZoom();

    if (center) {
      const lonLat = toLonLat(center);
      if (lonLat[0] !== undefined && lonLat[1] !== undefined) {
        mapStore.setCentro([lonLat[0], lonLat[1]]);
      }
    }
    if (currentZoom !== undefined) {
      mapStore.setZoom(Math.round(currentZoom));
    }
  });

  // Watch for draw mode changes
  watch(
    herramientaDibujo,
    (herramienta) => {
      if (drawInteraction.value) {
        olMap.value.removeInteraction(drawInteraction.value);
        drawInteraction.value = null;
      }
      if (modifyInteraction.value) {
        olMap.value.removeInteraction(modifyInteraction.value);
        modifyInteraction.value = null;
      }

      if (herramienta === 'polygon') {
        drawInteraction.value = new Draw({
          source: projectSource,
          type: 'Polygon',
        });

        drawInteraction.value.on('drawend', (event: any) => {
          projectSource.clear();
          const geojson = new GeoJSON();
          const feature = event.feature;
          const geometry = geojson.writeGeometryObject(feature.getGeometry(), {
            dataProjection: 'EPSG:4326',
            featureProjection: 'EPSG:3857',
          }) as GeometriaGeoJSON;
          emit('update:geometria', geometry);
          mapStore.desactivarEdicion();
        });

        olMap.value.addInteraction(drawInteraction.value);
      } else if (herramienta === 'modify') {
        modifyInteraction.value = new Modify({
          source: projectSource,
        });

        modifyInteraction.value.on('modifyend', () => {
          const features = projectSource.getFeatures();
          const firstFeature = features[0];
          if (firstFeature) {
            const geojson = new GeoJSON();
            const geom = firstFeature.getGeometry();
            if (geom) {
              const geometry = geojson.writeGeometryObject(geom, {
                dataProjection: 'EPSG:4326',
                featureProjection: 'EPSG:3857',
              }) as GeometriaGeoJSON;
              emit('update:geometria', geometry);
            }
          }
        });

        olMap.value.addInteraction(modifyInteraction.value);
      } else if (herramienta === 'delete') {
        projectSource.clear();
        emit('update:geometria', null);
        mapStore.desactivarEdicion();
      }
    }
  );

  // Watch for base map changes
  watch(
    () => mapStore.mapaBase,
    (base) => {
      osmLayer.setVisible(base === 'osm');
      satelliteLayer.setVisible(base === 'satellite');
    }
  );

  // Watch for geometry changes
  watch(
    () => props.geometria,
    (geom) => {
      projectSource.clear();
      if (geom) {
        const GeoJSONFormat = new GeoJSON();
        const result = GeoJSONFormat.readFeature(
          { type: 'Feature', geometry: geom },
          {
            dataProjection: 'EPSG:4326',
            featureProjection: 'EPSG:3857',
          }
        );
        const feature = Array.isArray(result) ? result[0] : result;
        if (feature) {
          projectSource.addFeature(feature);
        }
      }
    },
    { immediate: true }
  );

  // Watch for zoom changes desde el store (ej: botones de zoom)
  watch(
    () => mapStore.zoom,
    (newZoom) => {
      const currentZoom = olMap.value.getView().getZoom();
      if (Math.abs((currentZoom || 0) - newZoom) > 0.5) {
        isProgrammaticMove = true;
        olMap.value.getView().animate({
          zoom: newZoom,
          duration: 250
        }, () => {
          // Callback cuando termina la animación
          isProgrammaticMove = false;
        });
      }
    }
  );

  // Watch for center changes desde el store (ej: centrarEnRegion)
  watch(
    () => mapStore.centro,
    (newCenter) => {
      const currentCenter = olMap.value.getView().getCenter();
      const targetCenter = fromLonLat(newCenter);

      // Solo animar si el cambio es significativo (más de 1000 metros)
      if (currentCenter && targetCenter[0] !== undefined && targetCenter[1] !== undefined) {
        const dx = Math.abs((currentCenter[0] ?? 0) - targetCenter[0]);
        const dy = Math.abs((currentCenter[1] ?? 0) - targetCenter[1]);
        if (dx < 1000 && dy < 1000) return; // Ignorar cambios pequeños
      }

      isProgrammaticMove = true;
      olMap.value.getView().animate({
        center: targetCenter,
        duration: 250
      }, () => {
        // Callback cuando termina la animación
        isProgrammaticMove = false;
      });
    }
  );
});
</script>

<template>
  <div class="relative w-full h-full">
    <!-- El mapa tiene z-0 para crear stacking context, los controles z-50 estarán encima -->
    <div ref="mapRef" class="w-full h-full z-0"></div>
    <MapControls class="absolute top-4 right-4 z-50" />
    <DrawTools
      v-if="!props.readonly"
      class="absolute bottom-24 left-4 z-50"
      :tiene-geometria="!!props.geometria"
      @importar="onImportarKML"
    />

    <!-- Panel de capas GIS (superior izquierda) -->
    <div class="absolute top-4 left-4 z-50">
      <button
        class="btn btn-sm bg-base-100 shadow-lg"
        :class="{ 'btn-primary': layerPanelOpen }"
        @click="layerPanelOpen = !layerPanelOpen"
        title="Capas GIS"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
        </svg>
        <span class="hidden sm:inline ml-1">Capas</span>
      </button>
      <div
        v-if="layerPanelOpen"
        class="mt-2 bg-base-100 rounded-lg shadow-lg p-3 w-64 max-h-96 overflow-y-auto"
      >
        <div class="flex items-center justify-between mb-2">
          <h3 class="font-semibold text-sm">Capas GIS</h3>
          <button class="btn btn-ghost btn-xs" @click="layerPanelOpen = false">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <LayerPanel />
      </div>
    </div>

    <!-- Tooltip -->
    <div
      ref="tooltipRef"
      class="absolute bg-base-100 text-base-content px-2 py-1 rounded shadow-lg text-sm pointer-events-none z-20 border border-base-300"
      style="display: none"
    >
      {{ tooltipContent }}
    </div>
  </div>
</template>

<style>
@import 'ol/ol.css';
</style>
