import { describe, it, expect, vi, beforeEach } from 'vitest';
import {
  obtenerCapasGIS,
  obtenerCapaGeoJSON,
  analizarEspacial,
  validarGeometria,
  calcularArea,
} from '@/services/gis';
import type { GeometriaGeoJSON, ResultadoGIS, FeatureCollection } from '@/types';

// Mock del servicio api
vi.mock('@/services/api', () => ({
  get: vi.fn(),
  post: vi.fn(),
}));

import { get, post } from '@/services/api';

const mockGeometria: GeometriaGeoJSON = {
  type: 'Polygon',
  coordinates: [[[-70, -23], [-70, -24], [-69, -24], [-69, -23], [-70, -23]]],
};

const mockResultadoGIS: ResultadoGIS = {
  intersecciones: [
    {
      capa: 'snaspe',
      nombre_elemento: 'Reserva Nacional Los Flamencos',
      dentro: true,
      porcentaje_interseccion: 25.5,
      area_afectada_ha: 127.5,
    },
    {
      capa: 'glaciares',
      nombre_elemento: 'Glaciar El Tatio',
      dentro: false,
      distancia_metros: 1500,
    },
  ],
  alertas_gis: [
    'El proyecto intersecta con el SNASPE',
    'Proximidad a glaciar detectada',
  ],
  area_proyecto_ha: 500,
  centroide: [-69.5, -23.5],
};

const mockFeatureCollection: FeatureCollection = {
  type: 'FeatureCollection',
  name: 'snaspe',
  features: [
    {
      type: 'Feature',
      geometry: {
        type: 'Polygon',
        coordinates: [[[-70, -23], [-70, -24], [-69, -24], [-69, -23], [-70, -23]]],
      },
      properties: {
        nombre: 'Reserva Nacional Los Flamencos',
        categoria: 'Reserva Nacional',
      },
    },
  ],
  totalFeatures: 1,
};

describe('GIS Service', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('obtenerCapasGIS', () => {
    it('llama al endpoint correcto', async () => {
      const mockCapas = {
        capas: {
          snaspe: { nombre: 'SNASPE', registros: 100 },
          glaciares: { nombre: 'Glaciares', registros: 50 },
        },
      };
      vi.mocked(get).mockResolvedValue(mockCapas);

      await obtenerCapasGIS();

      expect(get).toHaveBeenCalledWith('/gis/capas');
    });

    it('retorna informacion de capas', async () => {
      const mockCapas = {
        capas: {
          snaspe: { nombre: 'SNASPE', registros: 100 },
        },
      };
      vi.mocked(get).mockResolvedValue(mockCapas);

      const result = await obtenerCapasGIS();

      expect(result.capas.snaspe).toBeDefined();
      expect(result.capas.snaspe.registros).toBe(100);
    });
  });

  describe('obtenerCapaGeoJSON', () => {
    it('obtiene capa sin parametros', async () => {
      vi.mocked(get).mockResolvedValue(mockFeatureCollection);

      await obtenerCapaGeoJSON('snaspe');

      expect(get).toHaveBeenCalledWith('/gis/capas/snaspe/geojson');
    });

    it('incluye bbox en query string', async () => {
      vi.mocked(get).mockResolvedValue(mockFeatureCollection);

      await obtenerCapaGeoJSON('snaspe', '-71,-24,-69,-22');

      expect(get).toHaveBeenCalledWith('/gis/capas/snaspe/geojson?bbox=-71%2C-24%2C-69%2C-22');
    });

    it('incluye limit en query string', async () => {
      vi.mocked(get).mockResolvedValue(mockFeatureCollection);

      await obtenerCapaGeoJSON('snaspe', undefined, 100);

      expect(get).toHaveBeenCalledWith('/gis/capas/snaspe/geojson?limit=100');
    });

    it('incluye bbox y limit', async () => {
      vi.mocked(get).mockResolvedValue(mockFeatureCollection);

      await obtenerCapaGeoJSON('snaspe', '-71,-24,-69,-22', 50);

      expect(get).toHaveBeenCalledWith(
        expect.stringContaining('bbox=')
      );
      expect(get).toHaveBeenCalledWith(
        expect.stringContaining('limit=50')
      );
    });

    it('retorna FeatureCollection', async () => {
      vi.mocked(get).mockResolvedValue(mockFeatureCollection);

      const result = await obtenerCapaGeoJSON('snaspe');

      expect(result.type).toBe('FeatureCollection');
      expect(result.features.length).toBe(1);
    });
  });

  describe('analizarEspacial', () => {
    it('envia geometria para analisis', async () => {
      vi.mocked(post).mockResolvedValue(mockResultadoGIS);

      await analizarEspacial(mockGeometria);

      expect(post).toHaveBeenCalledWith('/gis/analisis-espacial', {
        geometria: mockGeometria,
        proyecto: undefined,
      });
    });

    it('incluye datos del proyecto si se proporcionan', async () => {
      vi.mocked(post).mockResolvedValue(mockResultadoGIS);

      const proyecto = { nombre: 'Test', region: 'Antofagasta' };
      await analizarEspacial(mockGeometria, proyecto);

      expect(post).toHaveBeenCalledWith('/gis/analisis-espacial', {
        geometria: mockGeometria,
        proyecto,
      });
    });

    it('retorna resultado con intersecciones', async () => {
      vi.mocked(post).mockResolvedValue(mockResultadoGIS);

      const result = await analizarEspacial(mockGeometria);

      expect(result.intersecciones.length).toBe(2);
      expect(result.intersecciones[0].capa).toBe('snaspe');
    });

    it('retorna alertas GIS', async () => {
      vi.mocked(post).mockResolvedValue(mockResultadoGIS);

      const result = await analizarEspacial(mockGeometria);

      expect(result.alertas_gis.length).toBe(2);
    });

    it('retorna area y centroide', async () => {
      vi.mocked(post).mockResolvedValue(mockResultadoGIS);

      const result = await analizarEspacial(mockGeometria);

      expect(result.area_proyecto_ha).toBe(500);
      expect(result.centroide).toEqual([-69.5, -23.5]);
    });
  });

  describe('validarGeometria', () => {
    it('valida geometria valida', async () => {
      vi.mocked(post).mockResolvedValue({ valido: true, errores: [] });

      const result = await validarGeometria(mockGeometria);

      expect(post).toHaveBeenCalledWith('/gis/validar-geometria', {
        geometria: mockGeometria,
      });
      expect(result.valido).toBe(true);
      expect(result.errores).toEqual([]);
    });

    it('retorna errores para geometria invalida', async () => {
      vi.mocked(post).mockResolvedValue({
        valido: false,
        errores: ['El poligono se auto-intersecta', 'Area demasiado pequena'],
      });

      const result = await validarGeometria(mockGeometria);

      expect(result.valido).toBe(false);
      expect(result.errores.length).toBe(2);
    });
  });

  describe('calcularArea', () => {
    it('calcula area y perimetro', async () => {
      vi.mocked(post).mockResolvedValue({ area_ha: 500.25, perimetro_km: 12.5 });

      const result = await calcularArea(mockGeometria);

      expect(post).toHaveBeenCalledWith('/gis/calcular-area', {
        geometria: mockGeometria,
      });
      expect(result.area_ha).toBe(500.25);
      expect(result.perimetro_km).toBe(12.5);
    });
  });
});
