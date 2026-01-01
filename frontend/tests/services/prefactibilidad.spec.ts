import { describe, it, expect, vi, beforeEach } from 'vitest';
import {
  ejecutarAnalisis,
  ejecutarAnalisisRapido,
  exportarInforme,
  obtenerSeccionesDisponibles,
  obtenerMatrizDecision,
} from '@/services/prefactibilidad';
import type { ResultadoAnalisis, AnalisisRequest, AnalisisRapidoRequest } from '@/types';

// Mock del servicio api
vi.mock('@/services/api', () => ({
  post: vi.fn(),
  downloadFile: vi.fn(),
}));

import { post, downloadFile } from '@/services/api';

const mockResultado: ResultadoAnalisis = {
  id: 'analisis-001',
  fecha_analisis: '2024-01-15T10:30:00Z',
  proyecto: {
    nombre: 'Proyecto Test',
    region: 'Antofagasta',
  },
  geometria: {
    type: 'Polygon',
    coordinates: [[[-70, -23], [-70, -24], [-69, -24], [-69, -23], [-70, -23]]],
  },
  resultado_gis: {
    intersecciones: [],
    alertas_gis: [],
    area_proyecto_ha: 500,
    centroide: [-69.5, -23.5],
  },
  clasificacion_seia: {
    via_ingreso_recomendada: 'DIA',
    confianza: 0.75,
    nivel_confianza: 'ALTA',
    justificacion: 'Sin afectaciones significativas',
    puntaje_matriz: 0.35,
  },
  triggers: [],
  alertas: [],
  normativa_citada: [],
  metricas: {
    tiempo_analisis_segundos: 1.5,
    tiempo_gis_ms: 100,
    tiempo_rag_ms: 200,
  },
};

const mockRequest: AnalisisRequest = {
  proyecto: {
    nombre: 'Proyecto Test',
    region: 'Antofagasta',
  },
  geometria: {
    type: 'Polygon',
    coordinates: [[[-70, -23], [-70, -24], [-69, -24], [-69, -23], [-70, -23]]],
  },
  generar_informe_llm: true,
};

describe('Prefactibilidad Service', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('ejecutarAnalisis', () => {
    it('llama al endpoint correcto', async () => {
      vi.mocked(post).mockResolvedValue(mockResultado);

      await ejecutarAnalisis(mockRequest);

      expect(post).toHaveBeenCalledWith('/prefactibilidad/analisis', mockRequest);
    });

    it('retorna resultado del analisis', async () => {
      vi.mocked(post).mockResolvedValue(mockResultado);

      const result = await ejecutarAnalisis(mockRequest);

      expect(result).toEqual(mockResultado);
      expect(result.clasificacion_seia.via_ingreso_recomendada).toBe('DIA');
    });

    it('propaga errores del servidor', async () => {
      vi.mocked(post).mockRejectedValue(new Error('Error del servidor'));

      await expect(ejecutarAnalisis(mockRequest)).rejects.toThrow('Error del servidor');
    });
  });

  describe('ejecutarAnalisisRapido', () => {
    it('llama al endpoint de analisis rapido', async () => {
      vi.mocked(post).mockResolvedValue(mockResultado);

      const requestRapido: AnalisisRapidoRequest = {
        proyecto: mockRequest.proyecto,
        geometria: mockRequest.geometria,
      };

      await ejecutarAnalisisRapido(requestRapido);

      expect(post).toHaveBeenCalledWith('/prefactibilidad/analisis-rapido', requestRapido);
    });

    it('retorna resultado sin informe LLM', async () => {
      vi.mocked(post).mockResolvedValue(mockResultado);

      const result = await ejecutarAnalisisRapido({
        proyecto: mockRequest.proyecto,
        geometria: mockRequest.geometria,
      });

      expect(result.informe).toBeUndefined();
    });
  });

  describe('exportarInforme', () => {
    it('exporta a PDF', async () => {
      vi.mocked(downloadFile).mockResolvedValue();

      await exportarInforme(mockResultado, 'pdf');

      expect(downloadFile).toHaveBeenCalledWith(
        '/prefactibilidad/exportar/pdf',
        { resultado: mockResultado },
        expect.stringContaining('.pdf')
      );
    });

    it('exporta a DOCX', async () => {
      vi.mocked(downloadFile).mockResolvedValue();

      await exportarInforme(mockResultado, 'docx');

      expect(downloadFile).toHaveBeenCalledWith(
        '/prefactibilidad/exportar/docx',
        { resultado: mockResultado },
        expect.stringContaining('.docx')
      );
    });

    it('genera nombre de archivo con nombre del proyecto', async () => {
      vi.mocked(downloadFile).mockResolvedValue();

      await exportarInforme(mockResultado, 'pdf');

      expect(downloadFile).toHaveBeenCalledWith(
        expect.any(String),
        expect.any(Object),
        expect.stringContaining('Proyecto_Test')
      );
    });

    it('reemplaza espacios en nombre de archivo', async () => {
      vi.mocked(downloadFile).mockResolvedValue();
      const resultadoConEspacios = {
        ...mockResultado,
        proyecto: { nombre: 'Minera Gran Norte' },
      };

      await exportarInforme(resultadoConEspacios, 'pdf');

      const llamada = vi.mocked(downloadFile).mock.calls[0];
      const filename = llamada[2];
      expect(filename).not.toContain(' ');
      expect(filename).toContain('Minera_Gran_Norte');
    });

    it('soporta todos los formatos', async () => {
      vi.mocked(downloadFile).mockResolvedValue();
      const formatos: Array<'pdf' | 'docx' | 'txt' | 'html'> = ['pdf', 'docx', 'txt', 'html'];

      for (const formato of formatos) {
        await exportarInforme(mockResultado, formato);
        expect(downloadFile).toHaveBeenCalledWith(
          `/prefactibilidad/exportar/${formato}`,
          expect.any(Object),
          expect.stringContaining(`.${formato}`)
        );
      }
    });
  });

  describe('obtenerSeccionesDisponibles', () => {
    it('retorna lista de secciones', async () => {
      const secciones = ['resumen', 'descripcion', 'analisis_gis', 'clasificacion'];
      vi.mocked(post).mockResolvedValue({ secciones });

      const result = await obtenerSeccionesDisponibles();

      expect(post).toHaveBeenCalledWith('/prefactibilidad/secciones-disponibles');
      expect(result).toEqual(secciones);
    });
  });

  describe('obtenerMatrizDecision', () => {
    it('retorna pesos de la matriz', async () => {
      const matriz = {
        area_protegida: 1.0,
        glaciar: 0.9,
        comunidad_indigena: 0.8,
      };
      vi.mocked(post).mockResolvedValue(matriz);

      const result = await obtenerMatrizDecision();

      expect(post).toHaveBeenCalledWith('/prefactibilidad/matriz-decision');
      expect(result).toEqual(matriz);
    });
  });
});
