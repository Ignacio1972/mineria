import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { CapaGIS, CapaGISInfo } from '@/types';
import { CAPAS_DISPONIBLES, COORDENADAS_REGIONES } from '@/types';
import { get } from '@/services/api';

const GEOSERVER_URL = import.meta.env.VITE_GEOSERVER_URL || 'http://localhost:9085/geoserver';

// Claves para persistencia en localStorage
const STORAGE_KEY_CENTRO = 'map_centro';
const STORAGE_KEY_ZOOM = 'map_zoom';

// Valores por defecto (Antofagasta, II Región)
const DEFAULT_CENTRO: [number, number] = [-70.4, -23.65];
const DEFAULT_ZOOM = 8;

// Funciones de persistencia
function guardarEstadoMapa(centroVal: [number, number], zoomVal: number): void {
  try {
    localStorage.setItem(STORAGE_KEY_CENTRO, JSON.stringify(centroVal));
    localStorage.setItem(STORAGE_KEY_ZOOM, String(zoomVal));
  } catch (e) {
    console.warn('[MapStore] Error guardando estado en localStorage:', e);
  }
}

function recuperarCentro(): [number, number] {
  try {
    const stored = localStorage.getItem(STORAGE_KEY_CENTRO);
    if (stored) {
      const parsed = JSON.parse(stored);
      if (Array.isArray(parsed) && parsed.length === 2) {
        return [parsed[0], parsed[1]];
      }
    }
  } catch (e) {
    console.warn('[MapStore] Error recuperando centro desde localStorage:', e);
  }
  return DEFAULT_CENTRO;
}

function recuperarZoom(): number {
  try {
    const stored = localStorage.getItem(STORAGE_KEY_ZOOM);
    if (stored) {
      const parsed = parseInt(stored, 10);
      if (!isNaN(parsed) && parsed >= 3 && parsed <= 18) {
        return parsed;
      }
    }
  } catch (e) {
    console.warn('[MapStore] Error recuperando zoom desde localStorage:', e);
  }
  return DEFAULT_ZOOM;
}

export const useMapStore = defineStore('map', () => {
  // Inicializar desde localStorage o usar valores por defecto
  const centro = ref<[number, number]>(recuperarCentro());
  const zoom = ref(recuperarZoom());
  const capas = ref<CapaGIS[]>(CAPAS_DISPONIBLES.map((c) => ({ ...c })));
  const modoEdicion = ref(false);
  const herramientaDibujo = ref<'polygon' | 'modify' | 'delete' | null>(null);
  const mapaBase = ref<'osm' | 'satellite'>('osm');
  const cargandoCapas = ref(false);
  const errorCapas = ref<string | null>(null);

  const capasVisibles = computed(() =>
    capas.value.filter((c) => c.visible).map((c) => c.id)
  );

  const capasPorCategoria = computed(() => {
    const grouped: Record<string, CapaGIS[]> = {};
    for (const capa of capas.value) {
      const categoria = capa.categoria;
      if (!grouped[categoria]) {
        grouped[categoria] = [];
      }
      grouped[categoria]!.push(capa);
    }
    return grouped;
  });

  function toggleCapa(id: string) {
    const capa = capas.value.find((c) => c.id === id);
    if (capa) {
      capa.visible = !capa.visible;
      console.log(`[GIS] Capa "${capa.nombre}" visible: ${capa.visible}`);
    }
  }

  function setOpacidad(id: string, opacidad: number) {
    const capa = capas.value.find((c) => c.id === id);
    if (capa) {
      capa.opacidad = Math.max(0, Math.min(1, opacidad));
    }
  }

  function setCentro(coords: [number, number]) {
    centro.value = coords;
    guardarEstadoMapa(coords, zoom.value);
  }

  function setZoom(level: number) {
    zoom.value = Math.max(3, Math.min(18, level));
    guardarEstadoMapa(centro.value, zoom.value);
  }

  function zoomIn() {
    setZoom(zoom.value + 1);
  }

  function zoomOut() {
    setZoom(zoom.value - 1);
  }

  function activarDibujo() {
    modoEdicion.value = true;
    herramientaDibujo.value = 'polygon';
  }

  function activarModificar() {
    modoEdicion.value = true;
    herramientaDibujo.value = 'modify';
  }

  function activarEliminar() {
    modoEdicion.value = true;
    herramientaDibujo.value = 'delete';
  }

  function desactivarEdicion() {
    modoEdicion.value = false;
    herramientaDibujo.value = null;
  }

  function toggleMapaBase() {
    mapaBase.value = mapaBase.value === 'osm' ? 'satellite' : 'osm';
  }

  function centrarEnChile() {
    centro.value = [-70.6693, -33.4489];
    zoom.value = 5;
  }

  function centrarEnAntofagasta() {
    centro.value = [-70.4, -23.65];
    zoom.value = 8;
  }

  function centrarEnRegion(region: string) {
    const coords = COORDENADAS_REGIONES[region];
    if (coords) {
      centro.value = coords;
      zoom.value = 9;
    } else {
      // Fallback a Chile central si no se encuentra la region
      centrarEnChile();
    }
  }

  async function cargarCapasDesdeAPI() {
    cargandoCapas.value = true;
    errorCapas.value = null;
    try {
      const response = await get<{ capas: Record<string, CapaGISInfo> }>('/gis/capas');
      const capasAPI = response.capas;

      // Actualizar capas existentes con URLs de GeoServer
      for (const capa of capas.value) {
        const capaInfo = capasAPI[capa.id];
        if (capaInfo) {
          capa.url = `${GEOSERVER_URL}/wms?service=WMS&version=1.1.0&request=GetMap&layers=mineria:${capa.id}&format=image/png&transparent=true`;
        }
      }

      // Agregar nuevas capas que no estén en CAPAS_DISPONIBLES
      for (const [nombre, info] of Object.entries(capasAPI)) {
        if (!capas.value.find((c) => c.id === nombre) && !info.error) {
          capas.value.push({
            id: nombre,
            nombre: nombre.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase()),
            descripcion: `Capa ${nombre}`,
            tipo: 'vector',
            categoria: 'base',
            visible: false,
            opacidad: 0.7,
            url: `${GEOSERVER_URL}/wms?service=WMS&version=1.1.0&request=GetMap&layers=mineria:${nombre}&format=image/png&transparent=true`,
          });
        }
      }
    } catch (error) {
      errorCapas.value = error instanceof Error ? error.message : 'Error cargando capas';
      console.error('Error cargando capas desde API:', error);
    } finally {
      cargandoCapas.value = false;
    }
  }

  function getWMSUrl(capaId: string): string {
    return `${GEOSERVER_URL}/wms?service=WMS&version=1.1.0&request=GetMap&layers=mineria:${capaId}&format=image/png&transparent=true`;
  }

  return {
    centro,
    zoom,
    capas,
    modoEdicion,
    herramientaDibujo,
    mapaBase,
    cargandoCapas,
    errorCapas,
    capasVisibles,
    capasPorCategoria,
    toggleCapa,
    setOpacidad,
    setCentro,
    setZoom,
    zoomIn,
    zoomOut,
    activarDibujo,
    activarModificar,
    activarEliminar,
    desactivarEdicion,
    toggleMapaBase,
    centrarEnChile,
    centrarEnAntofagasta,
    centrarEnRegion,
    cargarCapasDesdeAPI,
    getWMSUrl,
  };
});
