import { describe, it, expect, vi, beforeEach } from 'vitest';
import { buscarNormativa, obtenerArticulo } from '@/services/legal';
import type { BusquedaNormativaRequest, BusquedaNormativaResponse } from '@/types';

// Mock del servicio api
vi.mock('@/services/api', () => ({
  post: vi.fn(),
}));

import { post } from '@/services/api';

const mockBusquedaResponse: BusquedaNormativaResponse = {
  resultados: [
    {
      documento: 'Ley 19.300',
      seccion: 'Artículo 11',
      contenido: 'Los proyectos o actividades que se enumeran a continuación...',
      relevancia: 0.95,
    },
    {
      documento: 'DS 40/2012',
      seccion: 'Artículo 8',
      contenido: 'Se someterán al Sistema de Evaluación de Impacto Ambiental...',
      relevancia: 0.88,
    },
  ],
  total: 2,
};

describe('Legal Service', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('buscarNormativa', () => {
    it('busca con query simple', async () => {
      vi.mocked(post).mockResolvedValue(mockBusquedaResponse);

      const request: BusquedaNormativaRequest = {
        query: 'areas protegidas mineria',
      };

      await buscarNormativa(request);

      expect(post).toHaveBeenCalledWith('/legal/buscar', request);
    });

    it('busca con filtros de tipo documento', async () => {
      vi.mocked(post).mockResolvedValue(mockBusquedaResponse);

      const request: BusquedaNormativaRequest = {
        query: 'evaluacion ambiental',
        filtros: {
          tipo_documento: ['ley', 'decreto'],
        },
      };

      await buscarNormativa(request);

      expect(post).toHaveBeenCalledWith('/legal/buscar', {
        query: 'evaluacion ambiental',
        filtros: {
          tipo_documento: ['ley', 'decreto'],
        },
      });
    });

    it('busca con filtros de temas', async () => {
      vi.mocked(post).mockResolvedValue(mockBusquedaResponse);

      const request: BusquedaNormativaRequest = {
        query: 'glaciares',
        filtros: {
          temas: ['recursos_hidricos', 'areas_protegidas'],
        },
      };

      await buscarNormativa(request);

      expect(post).toHaveBeenCalledWith('/legal/buscar', expect.objectContaining({
        filtros: expect.objectContaining({
          temas: ['recursos_hidricos', 'areas_protegidas'],
        }),
      }));
    });

    it('busca con limite', async () => {
      vi.mocked(post).mockResolvedValue(mockBusquedaResponse);

      const request: BusquedaNormativaRequest = {
        query: 'mineria',
        limite: 5,
      };

      await buscarNormativa(request);

      expect(post).toHaveBeenCalledWith('/legal/buscar', expect.objectContaining({
        limite: 5,
      }));
    });

    it('retorna resultados con relevancia', async () => {
      vi.mocked(post).mockResolvedValue(mockBusquedaResponse);

      const result = await buscarNormativa({ query: 'test' });

      expect(result.resultados.length).toBe(2);
      expect(result.resultados[0].relevancia).toBe(0.95);
      expect(result.total).toBe(2);
    });

    it('retorna documentos y secciones', async () => {
      vi.mocked(post).mockResolvedValue(mockBusquedaResponse);

      const result = await buscarNormativa({ query: 'test' });

      expect(result.resultados[0].documento).toBe('Ley 19.300');
      expect(result.resultados[0].seccion).toBe('Artículo 11');
    });

    it('maneja busqueda sin resultados', async () => {
      vi.mocked(post).mockResolvedValue({ resultados: [], total: 0 });

      const result = await buscarNormativa({ query: 'termino inexistente' });

      expect(result.resultados).toEqual([]);
      expect(result.total).toBe(0);
    });
  });

  describe('obtenerArticulo', () => {
    it('obtiene articulo especifico', async () => {
      vi.mocked(post).mockResolvedValue({
        contenido: 'Los proyectos o actividades susceptibles...',
        contexto: 'Ley sobre Bases Generales del Medio Ambiente',
      });

      await obtenerArticulo('Ley 19.300', '11');

      expect(post).toHaveBeenCalledWith('/legal/articulo', {
        documento: 'Ley 19.300',
        articulo: '11',
      });
    });

    it('retorna contenido y contexto', async () => {
      vi.mocked(post).mockResolvedValue({
        contenido: 'Contenido del articulo...',
        contexto: 'Contexto normativo',
      });

      const result = await obtenerArticulo('DS 40/2012', '8');

      expect(result.contenido).toBe('Contenido del articulo...');
      expect(result.contexto).toBe('Contexto normativo');
    });

    it('soporta diferentes formatos de articulo', async () => {
      vi.mocked(post).mockResolvedValue({ contenido: '', contexto: '' });

      // Artículo con letra
      await obtenerArticulo('Ley 19.300', '11 letra d)');
      expect(post).toHaveBeenCalledWith('/legal/articulo', {
        documento: 'Ley 19.300',
        articulo: '11 letra d)',
      });
    });
  });
});
