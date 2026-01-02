<script setup lang="ts">
import { ref, watch, onMounted } from 'vue';
import { storeToRefs } from 'pinia';
import { useMapStore } from '@/stores/map';
import type { GeometriaGeoJSON } from '@/types';
import MapControls from './MapControls.vue';
import DrawTools from './DrawTools.vue';

const props = defineProps<{
  geometria?: GeometriaGeoJSON | null
  readonly?: boolean
}>()

const emit = defineEmits<{
  (e: 'update:geometria', geom: GeometriaGeoJSON | null): void
}>()

const GEOSERVER_URL = import.meta.env.VITE_GEOSERVER_URL || 'http://localhost:9085/geoserver';

const mapStore = useMapStore();
const { herramientaDibujo } = storeToRefs(mapStore);

const mapRef = ref<HTMLDivElement | null>(null);
const tooltipRef = ref<HTMLDivElement | null>(null);
const olMap = ref<any>(null);
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

  // Crear capas WMS para cada capa GIS
  function createWMSLayer(capaId: string, visible: boolean, opacidad: number) {
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
      if (currentCenter) {
        const dx = Math.abs(currentCenter[0] - targetCenter[0]);
        const dy = Math.abs(currentCenter[1] - targetCenter[1]);
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
    <DrawTools v-if="!props.readonly" class="absolute bottom-24 left-4 z-50" :tiene-geometria="!!props.geometria" />
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
