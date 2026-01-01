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
    if (geom.type === 'Polygon') {
      const coords = geom.coordinates[0] as number[][];
      if (!coords || coords.length === 0) return;
      const lons = coords.map((c) => c[0]).filter((v): v is number => v !== undefined);
      const lats = coords.map((c) => c[1]).filter((v): v is number => v !== undefined);
      if (lons.length === 0 || lats.length === 0) return;
      const centerLon = (Math.min(...lons) + Math.max(...lons)) / 2;
      const centerLat = (Math.min(...lats) + Math.max(...lats)) / 2;
      mapStore.setCentro([centerLon, centerLat]);
      mapStore.setZoom(12);
    }
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
