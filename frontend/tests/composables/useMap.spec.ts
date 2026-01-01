import { describe, it, expect, vi, beforeEach } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import { useMap } from '@/composables/useMap';
import { useMapStore } from '@/stores/map';
import type { GeometriaGeoJSON } from '@/types';

// Mock import.meta.env
vi.stubEnv('VITE_GEOSERVER_URL', 'http://localhost:9085/geoserver');

// Mock servicio API
vi.mock('@/services/api', () => ({
  get: vi.fn(),
}));

describe('useMap', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  describe('propiedades computadas', () => {
    it('expone centro del mapa', () => {
      const { centro } = useMap();
      expect(centro.value).toEqual([-70.6693, -33.4489]);
    });

    it('permite modificar centro', () => {
      const mapStore = useMapStore();
      const { centro } = useMap();

      centro.value = [-68.5, -22.0];

      expect(mapStore.centro).toEqual([-68.5, -22.0]);
    });

    it('expone zoom del mapa', () => {
      const { zoom } = useMap();
      expect(zoom.value).toBe(6);
    });

    it('permite modificar zoom', () => {
      const mapStore = useMapStore();
      const { zoom } = useMap();

      zoom.value = 10;

      expect(mapStore.zoom).toBe(10);
    });

    it('expone capas del mapa', () => {
      const { capas } = useMap();
      expect(capas.value.length).toBeGreaterThan(0);
    });

    it('expone capas visibles', () => {
      const { capasVisibles } = useMap();
      expect(Array.isArray(capasVisibles.value)).toBe(true);
    });

    it('expone capas por categoria', () => {
      const { capasPorCategoria } = useMap();
      expect(typeof capasPorCategoria.value).toBe('object');
    });

    it('expone estado de edicion', () => {
      const { modoEdicion, herramientaActiva } = useMap();
      expect(modoEdicion.value).toBe(false);
      expect(herramientaActiva.value).toBeNull();
    });

    it('expone mapa base', () => {
      const { mapaBase } = useMap();
      expect(mapaBase.value).toBe('osm');
    });
  });

  describe('metodos de capas', () => {
    it('toggleCapa alterna visibilidad', () => {
      const mapStore = useMapStore();
      const { toggleCapa } = useMap();
      const capaInicial = mapStore.capas.find(c => c.id === 'snaspe');
      const visibleInicial = capaInicial?.visible;

      toggleCapa('snaspe');

      expect(mapStore.capas.find(c => c.id === 'snaspe')?.visible).toBe(!visibleInicial);
    });

    it('setOpacidad cambia opacidad de capa', () => {
      const mapStore = useMapStore();
      const { setOpacidad } = useMap();

      setOpacidad('snaspe', 0.5);

      expect(mapStore.capas.find(c => c.id === 'snaspe')?.opacidad).toBe(0.5);
    });
  });

  describe('metodos de navegacion', () => {
    it('zoomIn incrementa zoom', () => {
      const mapStore = useMapStore();
      const { zoomIn } = useMap();
      const zoomInicial = mapStore.zoom;

      zoomIn();

      expect(mapStore.zoom).toBe(zoomInicial + 1);
    });

    it('zoomOut decrementa zoom', () => {
      const mapStore = useMapStore();
      const { zoomOut } = useMap();
      const zoomInicial = mapStore.zoom;

      zoomOut();

      expect(mapStore.zoom).toBe(zoomInicial - 1);
    });

    it('centrarEnChile establece vista nacional', () => {
      const mapStore = useMapStore();
      const { centrarEnChile } = useMap();

      centrarEnChile();

      expect(mapStore.centro).toEqual([-70.6693, -33.4489]);
      expect(mapStore.zoom).toBe(5);
    });

    it('centrarEnAntofagasta establece vista regional', () => {
      const mapStore = useMapStore();
      const { centrarEnAntofagasta } = useMap();

      centrarEnAntofagasta();

      expect(mapStore.centro).toEqual([-70.4, -23.65]);
      expect(mapStore.zoom).toBe(8);
    });
  });

  describe('metodos de edicion', () => {
    it('activarDibujo activa modo poligono', () => {
      const mapStore = useMapStore();
      const { activarDibujo } = useMap();

      activarDibujo();

      expect(mapStore.modoEdicion).toBe(true);
      expect(mapStore.herramientaDibujo).toBe('polygon');
    });

    it('activarModificar activa modo modify', () => {
      const mapStore = useMapStore();
      const { activarModificar } = useMap();

      activarModificar();

      expect(mapStore.modoEdicion).toBe(true);
      expect(mapStore.herramientaDibujo).toBe('modify');
    });

    it('activarEliminar activa modo delete', () => {
      const mapStore = useMapStore();
      const { activarEliminar } = useMap();

      activarEliminar();

      expect(mapStore.modoEdicion).toBe(true);
      expect(mapStore.herramientaDibujo).toBe('delete');
    });

    it('desactivarEdicion limpia modo edicion', () => {
      const mapStore = useMapStore();
      const { activarDibujo, desactivarEdicion } = useMap();

      activarDibujo();
      desactivarEdicion();

      expect(mapStore.modoEdicion).toBe(false);
      expect(mapStore.herramientaDibujo).toBeNull();
    });
  });

  describe('mapa base', () => {
    it('toggleMapaBase alterna entre osm y satellite', () => {
      const mapStore = useMapStore();
      const { toggleMapaBase } = useMap();

      expect(mapStore.mapaBase).toBe('osm');

      toggleMapaBase();
      expect(mapStore.mapaBase).toBe('satellite');

      toggleMapaBase();
      expect(mapStore.mapaBase).toBe('osm');
    });
  });

  describe('centrarEnGeometria', () => {
    it('centra mapa en geometria de poligono', () => {
      const mapStore = useMapStore();
      const { centrarEnGeometria } = useMap();

      const geometria: GeometriaGeoJSON = {
        type: 'Polygon',
        coordinates: [[
          [-70, -23],
          [-70, -24],
          [-69, -24],
          [-69, -23],
          [-70, -23],
        ]],
      };

      centrarEnGeometria(geometria);

      expect(mapStore.centro[0]).toBeCloseTo(-69.5);
      expect(mapStore.centro[1]).toBeCloseTo(-23.5);
      expect(mapStore.zoom).toBe(12);
    });

    it('maneja geometria con coordenadas vacias', () => {
      const mapStore = useMapStore();
      const centroOriginal = [...mapStore.centro];
      const { centrarEnGeometria } = useMap();

      const geometria: GeometriaGeoJSON = {
        type: 'Polygon',
        coordinates: [[]],
      };

      centrarEnGeometria(geometria);

      // No deberia cambiar el centro
      expect(mapStore.centro).toEqual(centroOriginal);
    });
  });

  describe('mapRef', () => {
    it('expone referencia al mapa', () => {
      const { mapRef } = useMap();
      expect(mapRef.value).toBeNull();
    });
  });
});
