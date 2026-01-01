import { describe, it, expect, beforeEach, vi } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import { useMapStore } from '@/stores/map';

// Mock de import.meta.env
vi.stubEnv('VITE_GEOSERVER_URL', 'http://localhost:9085/geoserver');

// Mock del servicio API
vi.mock('@/services/api', () => ({
  get: vi.fn(),
}));

import { get } from '@/services/api';

describe('useMapStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  describe('estado inicial', () => {
    it('tiene centro en Chile', () => {
      const store = useMapStore();
      expect(store.centro).toEqual([-70.6693, -33.4489]);
    });

    it('tiene zoom inicial de 6', () => {
      const store = useMapStore();
      expect(store.zoom).toBe(6);
    });

    it('tiene capas predefinidas', () => {
      const store = useMapStore();
      expect(store.capas.length).toBeGreaterThan(0);
      expect(store.capas.find((c) => c.id === 'snaspe')).toBeDefined();
    });

    it('comienza sin modo edicion', () => {
      const store = useMapStore();
      expect(store.modoEdicion).toBe(false);
      expect(store.herramientaDibujo).toBeNull();
    });

    it('usa mapa OSM por defecto', () => {
      const store = useMapStore();
      expect(store.mapaBase).toBe('osm');
    });
  });

  describe('capasVisibles computed', () => {
    it('devuelve ids de capas visibles', () => {
      const store = useMapStore();
      const visibles = store.capasVisibles;

      // snaspe, glaciares, cuerpos_agua, etc. estan visibles por defecto
      expect(visibles).toContain('snaspe');
    });

    it('se actualiza al cambiar visibilidad', () => {
      const store = useMapStore();
      const capa = store.capas.find((c) => c.id === 'snaspe');

      if (capa) {
        capa.visible = false;
        expect(store.capasVisibles).not.toContain('snaspe');
      }
    });
  });

  describe('capasPorCategoria computed', () => {
    it('agrupa capas por categoria', () => {
      const store = useMapStore();
      const porCategoria = store.capasPorCategoria;

      expect(porCategoria['areas_protegidas']).toBeDefined();
      expect(porCategoria['recursos_hidricos']).toBeDefined();
    });
  });

  describe('toggleCapa', () => {
    it('alterna visibilidad de capa', () => {
      const store = useMapStore();
      const capaInicial = store.capas.find((c) => c.id === 'snaspe');
      const visibleInicial = capaInicial?.visible;

      store.toggleCapa('snaspe');

      expect(store.capas.find((c) => c.id === 'snaspe')?.visible).toBe(!visibleInicial);
    });

    it('no hace nada con id inexistente', () => {
      const store = useMapStore();
      const capasAntes = JSON.stringify(store.capas);

      store.toggleCapa('capa-inexistente');

      expect(JSON.stringify(store.capas)).toBe(capasAntes);
    });
  });

  describe('setOpacidad', () => {
    it('establece opacidad de capa', () => {
      const store = useMapStore();
      store.setOpacidad('snaspe', 0.5);

      expect(store.capas.find((c) => c.id === 'snaspe')?.opacidad).toBe(0.5);
    });

    it('limita opacidad minima a 0', () => {
      const store = useMapStore();
      store.setOpacidad('snaspe', -0.5);

      expect(store.capas.find((c) => c.id === 'snaspe')?.opacidad).toBe(0);
    });

    it('limita opacidad maxima a 1', () => {
      const store = useMapStore();
      store.setOpacidad('snaspe', 1.5);

      expect(store.capas.find((c) => c.id === 'snaspe')?.opacidad).toBe(1);
    });
  });

  describe('navegacion del mapa', () => {
    it('setCentro actualiza coordenadas', () => {
      const store = useMapStore();
      store.setCentro([-68.5, -22.0]);

      expect(store.centro).toEqual([-68.5, -22.0]);
    });

    it('setZoom actualiza nivel', () => {
      const store = useMapStore();
      store.setZoom(10);

      expect(store.zoom).toBe(10);
    });

    it('setZoom limita minimo a 3', () => {
      const store = useMapStore();
      store.setZoom(1);

      expect(store.zoom).toBe(3);
    });

    it('setZoom limita maximo a 18', () => {
      const store = useMapStore();
      store.setZoom(25);

      expect(store.zoom).toBe(18);
    });

    it('zoomIn incrementa zoom en 1', () => {
      const store = useMapStore();
      const zoomInicial = store.zoom;
      store.zoomIn();

      expect(store.zoom).toBe(zoomInicial + 1);
    });

    it('zoomOut decrementa zoom en 1', () => {
      const store = useMapStore();
      const zoomInicial = store.zoom;
      store.zoomOut();

      expect(store.zoom).toBe(zoomInicial - 1);
    });
  });

  describe('herramientas de dibujo', () => {
    it('activarDibujo activa modo poligono', () => {
      const store = useMapStore();
      store.activarDibujo();

      expect(store.modoEdicion).toBe(true);
      expect(store.herramientaDibujo).toBe('polygon');
    });

    it('activarModificar activa modo modify', () => {
      const store = useMapStore();
      store.activarModificar();

      expect(store.modoEdicion).toBe(true);
      expect(store.herramientaDibujo).toBe('modify');
    });

    it('activarEliminar activa modo delete', () => {
      const store = useMapStore();
      store.activarEliminar();

      expect(store.modoEdicion).toBe(true);
      expect(store.herramientaDibujo).toBe('delete');
    });

    it('desactivarEdicion limpia modo edicion', () => {
      const store = useMapStore();
      store.activarDibujo();
      store.desactivarEdicion();

      expect(store.modoEdicion).toBe(false);
      expect(store.herramientaDibujo).toBeNull();
    });
  });

  describe('mapa base', () => {
    it('toggleMapaBase alterna entre osm y satellite', () => {
      const store = useMapStore();
      expect(store.mapaBase).toBe('osm');

      store.toggleMapaBase();
      expect(store.mapaBase).toBe('satellite');

      store.toggleMapaBase();
      expect(store.mapaBase).toBe('osm');
    });
  });

  describe('ubicaciones predefinidas', () => {
    it('centrarEnChile establece vista nacional', () => {
      const store = useMapStore();
      store.setCentro([0, 0]);
      store.setZoom(15);

      store.centrarEnChile();

      expect(store.centro).toEqual([-70.6693, -33.4489]);
      expect(store.zoom).toBe(5);
    });

    it('centrarEnAntofagasta establece vista regional', () => {
      const store = useMapStore();
      store.centrarEnAntofagasta();

      expect(store.centro).toEqual([-70.4, -23.65]);
      expect(store.zoom).toBe(8);
    });
  });

  describe('cargarCapasDesdeAPI', () => {
    it('carga capas desde el servidor', async () => {
      const mockCapas = {
        capas: {
          snaspe: { nombre: 'SNASPE', registros: 100 },
          glaciares: { nombre: 'Glaciares', registros: 50 },
        },
      };
      vi.mocked(get).mockResolvedValue(mockCapas);

      const store = useMapStore();
      await store.cargarCapasDesdeAPI();

      expect(get).toHaveBeenCalledWith('/gis/capas');
      expect(store.cargandoCapas).toBe(false);
      expect(store.errorCapas).toBeNull();
    });

    it('maneja errores de carga', async () => {
      vi.mocked(get).mockRejectedValue(new Error('Error de red'));

      const store = useMapStore();
      await store.cargarCapasDesdeAPI();

      expect(store.errorCapas).toBe('Error de red');
      expect(store.cargandoCapas).toBe(false);
    });

    it('establece cargandoCapas durante la carga', async () => {
      vi.mocked(get).mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve({ capas: {} }), 100))
      );

      const store = useMapStore();
      const promise = store.cargarCapasDesdeAPI();

      expect(store.cargandoCapas).toBe(true);

      await promise;

      expect(store.cargandoCapas).toBe(false);
    });

    it('agrega capas nuevas desde API', async () => {
      const mockCapas = {
        capas: {
          nueva_capa: { nombre: 'Capa Nueva', registros: 25 },
        },
      };
      vi.mocked(get).mockResolvedValue(mockCapas);

      const store = useMapStore();
      const cantidadInicial = store.capas.length;
      await store.cargarCapasDesdeAPI();

      expect(store.capas.length).toBe(cantidadInicial + 1);
      expect(store.capas.find((c) => c.id === 'nueva_capa')).toBeDefined();
    });
  });

  describe('getWMSUrl', () => {
    it('genera URL WMS correcta', () => {
      const store = useMapStore();
      const url = store.getWMSUrl('snaspe');

      expect(url).toContain('service=WMS');
      expect(url).toContain('layers=mineria:snaspe');
      expect(url).toContain('format=image/png');
      expect(url).toContain('transparent=true');
    });
  });
});
