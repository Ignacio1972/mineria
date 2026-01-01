import { describe, it, expect, vi, beforeEach } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import { useExport } from '@/composables/useExport';
import { useAnalysisStore } from '@/stores/analysis';
import { useUIStore } from '@/stores/ui';
import type { ResultadoAnalisis } from '@/types';

// Mock del servicio de exportacion
vi.mock('@/services/prefactibilidad', () => ({
  exportarInforme: vi.fn(),
}));

import { exportarInforme } from '@/services/prefactibilidad';

// Mock crypto.randomUUID
vi.stubGlobal('crypto', {
  randomUUID: () => 'toast-uuid',
});

const mockResultado: ResultadoAnalisis = {
  id: 'analisis-001',
  fecha_analisis: '2024-01-15',
  proyecto: { nombre: 'Test' },
  geometria: { type: 'Polygon', coordinates: [] },
  resultado_gis: { intersecciones: [], alertas_gis: [], area_proyecto_ha: 100, centroide: [0, 0] },
  clasificacion_seia: { via_ingreso_recomendada: 'DIA', confianza: 0.8, nivel_confianza: 'ALTA', justificacion: '', puntaje_matriz: 0.5 },
  triggers: [],
  alertas: [],
  normativa_citada: [],
  metricas: { tiempo_analisis_segundos: 1, tiempo_gis_ms: 100, tiempo_rag_ms: 100 },
};

describe('useExport', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  describe('estado inicial', () => {
    it('comienza sin exportar y con formato PDF', () => {
      const { exportando, formatoSeleccionado } = useExport();

      expect(exportando.value).toBe(false);
      expect(formatoSeleccionado.value).toBe('pdf');
    });

    it('puedeExportar es false sin resultado', () => {
      const { puedeExportar } = useExport();

      expect(puedeExportar.value).toBe(false);
    });

    it('expone lista de formatos disponibles', () => {
      const { formatos } = useExport();

      expect(formatos.length).toBeGreaterThan(0);
      expect(formatos.find(f => f.valor === 'pdf')).toBeDefined();
      expect(formatos.find(f => f.valor === 'docx')).toBeDefined();
    });
  });

  describe('puedeExportar', () => {
    it('es true cuando hay resultado', () => {
      const analysisStore = useAnalysisStore();
      analysisStore.resultado = mockResultado;

      const { puedeExportar } = useExport();

      expect(puedeExportar.value).toBe(true);
    });
  });

  describe('seleccionarFormato', () => {
    it('cambia el formato seleccionado', () => {
      const { formatoSeleccionado, seleccionarFormato } = useExport();

      seleccionarFormato('docx');
      expect(formatoSeleccionado.value).toBe('docx');

      seleccionarFormato('html');
      expect(formatoSeleccionado.value).toBe('html');
    });
  });

  describe('exportar', () => {
    it('no exporta sin resultado', async () => {
      const { exportar } = useExport();

      const result = await exportar();

      expect(result).toBe(false);
      expect(exportarInforme).not.toHaveBeenCalled();
    });

    it('muestra toast de warning sin resultado', async () => {
      const uiStore = useUIStore();
      const spy = vi.spyOn(uiStore, 'mostrarToast');

      const { exportar } = useExport();
      await exportar();

      expect(spy).toHaveBeenCalledWith('No hay resultado para exportar', 'warning');
    });

    it('exporta con formato por defecto', async () => {
      vi.mocked(exportarInforme).mockResolvedValue();
      const analysisStore = useAnalysisStore();
      analysisStore.resultado = mockResultado;

      const { exportar } = useExport();
      const result = await exportar();

      expect(result).toBe(true);
      expect(exportarInforme).toHaveBeenCalledWith(mockResultado, 'pdf');
    });

    it('exporta con formato especificado', async () => {
      vi.mocked(exportarInforme).mockResolvedValue();
      const analysisStore = useAnalysisStore();
      analysisStore.resultado = mockResultado;

      const { exportar } = useExport();
      await exportar('docx');

      expect(exportarInforme).toHaveBeenCalledWith(mockResultado, 'docx');
    });

    it('usa formato seleccionado si no se especifica', async () => {
      vi.mocked(exportarInforme).mockResolvedValue();
      const analysisStore = useAnalysisStore();
      analysisStore.resultado = mockResultado;

      const { exportar, seleccionarFormato } = useExport();
      seleccionarFormato('txt');
      await exportar();

      expect(exportarInforme).toHaveBeenCalledWith(mockResultado, 'txt');
    });

    it('establece exportando durante la exportacion', async () => {
      let resolve: () => void;
      vi.mocked(exportarInforme).mockImplementation(
        () => new Promise((r) => { resolve = r; })
      );
      const analysisStore = useAnalysisStore();
      analysisStore.resultado = mockResultado;

      const { exportar, exportando } = useExport();
      const promise = exportar();

      expect(exportando.value).toBe(true);

      resolve!();
      await promise;

      expect(exportando.value).toBe(false);
    });

    it('muestra toast de exito al exportar', async () => {
      vi.mocked(exportarInforme).mockResolvedValue();
      const analysisStore = useAnalysisStore();
      analysisStore.resultado = mockResultado;
      const uiStore = useUIStore();
      const spy = vi.spyOn(uiStore, 'mostrarToast');

      const { exportar } = useExport();
      await exportar('pdf');

      expect(spy).toHaveBeenCalledWith('Informe exportado como PDF', 'success');
    });

    it('maneja errores de exportacion', async () => {
      vi.mocked(exportarInforme).mockRejectedValue(new Error('Error de red'));
      const analysisStore = useAnalysisStore();
      analysisStore.resultado = mockResultado;
      const uiStore = useUIStore();
      const spy = vi.spyOn(uiStore, 'mostrarToast');

      const { exportar } = useExport();
      const result = await exportar();

      expect(result).toBe(false);
      expect(spy).toHaveBeenCalledWith('Error al exportar el informe', 'error');
    });

    it('limpia exportando incluso con error', async () => {
      vi.mocked(exportarInforme).mockRejectedValue(new Error('Error'));
      const analysisStore = useAnalysisStore();
      analysisStore.resultado = mockResultado;

      const { exportar, exportando } = useExport();
      await exportar();

      expect(exportando.value).toBe(false);
    });
  });
});
