import { computed, ref } from 'vue';
import { useMapStore } from '@/stores/map';
import type { GeometriaGeoJSON } from '@/types';

export function useMap() {
  const mapStore = useMapStore();
  const mapRef = ref<unknown>(null);

  const centro = computed({
    get: () => mapStore.centro,
    set: (val) => mapStore.setCentro(val),
  });

  const zoom = computed({
    get: () => mapStore.zoom,
    set: (val) => mapStore.setZoom(val),
  });

  const capas = computed(() => mapStore.capas);
  const capasVisibles = computed(() => mapStore.capasVisibles);
  const capasPorCategoria = computed(() => mapStore.capasPorCategoria);

  const modoEdicion = computed(() => mapStore.modoEdicion);
  const herramientaActiva = computed(() => mapStore.herramientaDibujo);
  const mapaBase = computed(() => mapStore.mapaBase);

  function toggleCapa(id: string) {
    mapStore.toggleCapa(id);
  }

  function setOpacidad(id: string, opacidad: number) {
    mapStore.setOpacidad(id, opacidad);
  }

  function zoomIn() {
    mapStore.zoomIn();
  }

  function zoomOut() {
    mapStore.zoomOut();
  }

  function activarDibujo() {
    mapStore.activarDibujo();
  }

  function activarModificar() {
    mapStore.activarModificar();
  }

  function activarEliminar() {
    mapStore.activarEliminar();
  }

  function desactivarEdicion() {
    mapStore.desactivarEdicion();
  }

  function toggleMapaBase() {
    mapStore.toggleMapaBase();
  }

  function centrarEnChile() {
    mapStore.centrarEnChile();
  }

  function centrarEnAntofagasta() {
    mapStore.centrarEnAntofagasta();
  }

  function centrarEnGeometria(geom: GeometriaGeoJSON) {
    let allCoords: number[][] = [];

    if (geom.type === 'Polygon') {
      const coords = geom.coordinates[0] as number[][];
      if (coords && coords.length > 0) {
        allCoords = coords;
      }
    } else if (geom.type === 'MultiPolygon') {
      const multiCoords = geom.coordinates as number[][][][];
      for (const polygon of multiCoords) {
        if (polygon[0]) {
          allCoords = allCoords.concat(polygon[0]);
        }
      }
    }

    if (allCoords.length === 0) return;

    const lons = allCoords.map((c) => c[0]).filter((v): v is number => v !== undefined);
    const lats = allCoords.map((c) => c[1]).filter((v): v is number => v !== undefined);
    if (lons.length === 0 || lats.length === 0) return;

    const minLon = Math.min(...lons);
    const maxLon = Math.max(...lons);
    const minLat = Math.min(...lats);
    const maxLat = Math.max(...lats);

    const centerLon = (minLon + maxLon) / 2;
    const centerLat = (minLat + maxLat) / 2;

    // Calcular zoom basado en el tamaño del bounding box
    const deltaLon = maxLon - minLon;
    const deltaLat = maxLat - minLat;
    const maxDelta = Math.max(deltaLon, deltaLat);

    // Ajustar zoom según el tamaño (más pequeño = más zoom)
    let zoom = 14;
    if (maxDelta > 1) zoom = 8;
    else if (maxDelta > 0.5) zoom = 9;
    else if (maxDelta > 0.2) zoom = 10;
    else if (maxDelta > 0.1) zoom = 11;
    else if (maxDelta > 0.05) zoom = 12;
    else if (maxDelta > 0.02) zoom = 13;
    else if (maxDelta > 0.01) zoom = 14;
    else zoom = 15;

    mapStore.setCentro([centerLon, centerLat]);
    mapStore.setZoom(zoom);
  }

  return {
    mapRef,
    centro,
    zoom,
    capas,
    capasVisibles,
    capasPorCategoria,
    modoEdicion,
    herramientaActiva,
    mapaBase,
    toggleCapa,
    setOpacidad,
    zoomIn,
    zoomOut,
    activarDibujo,
    activarModificar,
    activarEliminar,
    desactivarEdicion,
    toggleMapaBase,
    centrarEnChile,
    centrarEnAntofagasta,
    centrarEnGeometria,
  };
}
