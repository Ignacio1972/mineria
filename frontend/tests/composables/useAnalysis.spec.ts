import { describe, it, expect, vi, beforeEach } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import { useAnalysis } from '@/composables/useAnalysis';
import { useAnalysisStore } from '@/stores/analysis';
import { useProjectStore } from '@/stores/project';
import { useUIStore } from '@/stores/ui';
import type { ResultadoAnalisis, GeometriaGeoJSON } from '@/types';

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  clear: vi.fn(),
  removeItem: vi.fn(),
  length: 0,
  key: vi.fn(),
};
Object.defineProperty(window, 'localStorage', { value: localStorageMock });

// Mock crypto.randomUUID
vi.stubGlobal('crypto', {
  randomUUID: () => 'test-uuid',
});

// Mock servicios
vi.mock('@/services/prefactibilidad', () => ({
  ejecutarAnalisis: vi.fn(),
  ejecutarAnalisisRapido: vi.fn(),
  exportarInforme: vi.fn(),
}));

import { ejecutarAnalisis, ejecutarAnalisisRapido, exportarInforme } from '@/services/prefactibilidad';

const mockGeometria: GeometriaGeoJSON = {
  type: 'Polygon',
  coordinates: [[[-70, -23], [-70, -24], [-69, -24], [-69, -23], [-70, -23]]],
};

const mockResultadoDIA: ResultadoAnalisis = {
  id: 'analisis-001',
  fecha_analisis: '2024-01-15',
  proyecto: { nombre: 'Test' },
  geometria: mockGeometria,
  resultado_gis: { intersecciones: [], alertas_gis: [], area_proyecto_ha: 100, centroide: [0, 0] },
  clasificacion_seia: {
    via_ingreso_recomendada: 'DIA',
    confianza: 0.8,
    nivel_confianza: 'ALTA',
    justificacion: 'Sin afectaciones',
    puntaje_matriz: 0.3,
  },
  triggers: [],
  alertas: [],
  normativa_citada: [],
  metricas: { tiempo_analisis_segundos: 1, tiempo_gis_ms: 100, tiempo_rag_ms: 100 },
};

const mockResultadoEIA: ResultadoAnalisis = {
  ...mockResultadoDIA,
  clasificacion_seia: {
    via_ingreso_recomendada: 'EIA',
    confianza: 0.9,
    nivel_confianza: 'MUY_ALTA',
    justificacion: 'Afecta area protegida',
    puntaje_matriz: 0.85,
  },
  alertas: [
    { id: '1', nivel: 'CRITICA', categoria: 'areas_protegidas', titulo: 'Test', descripcion: '', acciones_requeridas: [] },
    { id: '2', nivel: 'ALTA', categoria: 'recursos', titulo: 'Test 2', descripcion: '', acciones_requeridas: [] },
  ],
};

describe('useAnalysis', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
    localStorageMock.getItem.mockReturnValue(null);
  });

  describe('propiedades computadas', () => {
    it('expone resultado del store', () => {
      const analysisStore = useAnalysisStore();
      analysisStore.resultado = mockResultadoDIA;

      const { resultado } = useAnalysis();

      expect(resultado.value).toEqual(mockResultadoDIA);
    });

    it('expone estado de carga', () => {
      const analysisStore = useAnalysisStore();
      analysisStore.cargando = true;

      const { cargando } = useAnalysis();

      expect(cargando.value).toBe(true);
    });

    it('expone error', () => {
      const analysisStore = useAnalysisStore();
      analysisStore.error = 'Error de prueba';

      const { error } = useAnalysis();

      expect(error.value).toBe('Error de prueba');
    });
  });

  describe('puedeAnalizar', () => {
    it('es false sin proyecto valido', () => {
      const { puedeAnalizar } = useAnalysis();
      expect(puedeAnalizar.value).toBe(false);
    });

    it('es true con proyecto valido', () => {
      const projectStore = useProjectStore();
      projectStore.crearNuevoProyecto();
      projectStore.actualizarDatos({ nombre: 'Test' });
      projectStore.actualizarGeometria(mockGeometria);

      const { puedeAnalizar } = useAnalysis();

      expect(puedeAnalizar.value).toBe(true);
    });
  });

  describe('resumenClasificacion', () => {
    it('es null sin resultado', () => {
      const { resumenClasificacion } = useAnalysis();
      expect(resumenClasificacion.value).toBeNull();
    });

    it('resume clasificacion DIA', () => {
      const analysisStore = useAnalysisStore();
      analysisStore.resultado = mockResultadoDIA;

      const { resumenClasificacion } = useAnalysis();

      expect(resumenClasificacion.value?.via).toBe('DIA');
      expect(resumenClasificacion.value?.esEIA).toBe(false);
      expect(resumenClasificacion.value?.colorClase).toContain('success');
    });

    it('resume clasificacion EIA', () => {
      const analysisStore = useAnalysisStore();
      analysisStore.resultado = mockResultadoEIA;

      const { resumenClasificacion } = useAnalysis();

      expect(resumenClasificacion.value?.via).toBe('EIA');
      expect(resumenClasificacion.value?.esEIA).toBe(true);
      expect(resumenClasificacion.value?.colorClase).toContain('warning');
    });
  });

  describe('resumenRiesgo', () => {
    it('muestra sin alertas cuando no hay', () => {
      const analysisStore = useAnalysisStore();
      analysisStore.resultado = mockResultadoDIA;

      const { resumenRiesgo } = useAnalysis();

      expect(resumenRiesgo.value).toBe('Sin alertas');
    });

    it('muestra alertas criticas si existen', () => {
      const analysisStore = useAnalysisStore();
      analysisStore.resultado = mockResultadoEIA;

      const { resumenRiesgo } = useAnalysis();

      expect(resumenRiesgo.value).toContain('críticas');
    });
  });

  describe('colorRiesgo', () => {
    it('es success sin alertas', () => {
      const analysisStore = useAnalysisStore();
      analysisStore.resultado = mockResultadoDIA;

      const { colorRiesgo } = useAnalysis();

      expect(colorRiesgo.value).toBe('success');
    });

    it('es error con alertas criticas', () => {
      const analysisStore = useAnalysisStore();
      analysisStore.resultado = mockResultadoEIA;

      const { colorRiesgo } = useAnalysis();

      expect(colorRiesgo.value).toBe('error');
    });
  });

  describe('ejecutarAnalisisRapido', () => {
    it('ejecuta analisis sin LLM', async () => {
      vi.mocked(ejecutarAnalisisRapido).mockResolvedValue(mockResultadoDIA);
      const projectStore = useProjectStore();
      projectStore.crearNuevoProyecto();
      projectStore.actualizarDatos({ nombre: 'Test' });
      projectStore.actualizarGeometria(mockGeometria);

      const { ejecutarAnalisisRapido: ejecutar } = useAnalysis();
      await ejecutar();

      expect(ejecutarAnalisisRapido).toHaveBeenCalled();
    });

    it('expande panel de resultados al terminar', async () => {
      vi.mocked(ejecutarAnalisisRapido).mockResolvedValue(mockResultadoDIA);
      const projectStore = useProjectStore();
      projectStore.crearNuevoProyecto();
      projectStore.actualizarDatos({ nombre: 'Test' });
      projectStore.actualizarGeometria(mockGeometria);
      const uiStore = useUIStore();

      const { ejecutarAnalisisRapido: ejecutar } = useAnalysis();
      await ejecutar();

      expect(uiStore.panelResultadosExpandido).toBe(true);
    });
  });

  describe('ejecutarAnalisisCompleto', () => {
    it('ejecuta analisis con LLM', async () => {
      vi.mocked(ejecutarAnalisis).mockResolvedValue(mockResultadoDIA);
      const projectStore = useProjectStore();
      projectStore.crearNuevoProyecto();
      projectStore.actualizarDatos({ nombre: 'Test' });
      projectStore.actualizarGeometria(mockGeometria);

      const { ejecutarAnalisisCompleto } = useAnalysis();
      await ejecutarAnalisisCompleto();

      expect(ejecutarAnalisis).toHaveBeenCalled();
    });
  });

  describe('exportar', () => {
    it('no exporta sin resultado', async () => {
      const uiStore = useUIStore();
      const spy = vi.spyOn(uiStore, 'mostrarToast');

      const { exportar } = useAnalysis();
      await exportar('pdf');

      expect(exportarInforme).not.toHaveBeenCalled();
      expect(spy).toHaveBeenCalledWith('No hay resultado para exportar', 'warning');
    });

    it('exporta a formato especificado', async () => {
      vi.mocked(exportarInforme).mockResolvedValue();
      const analysisStore = useAnalysisStore();
      analysisStore.resultado = mockResultadoDIA;

      const { exportar } = useAnalysis();
      await exportar('pdf');

      expect(exportarInforme).toHaveBeenCalledWith(mockResultadoDIA, 'pdf');
    });

    it('muestra toast de exito', async () => {
      vi.mocked(exportarInforme).mockResolvedValue();
      const analysisStore = useAnalysisStore();
      analysisStore.resultado = mockResultadoDIA;
      const uiStore = useUIStore();
      const spy = vi.spyOn(uiStore, 'mostrarToast');

      const { exportar } = useAnalysis();
      await exportar('docx');

      expect(spy).toHaveBeenCalledWith('Informe exportado como DOCX', 'success');
    });

    it('maneja errores de exportacion', async () => {
      vi.mocked(exportarInforme).mockRejectedValue(new Error('Error'));
      const analysisStore = useAnalysisStore();
      analysisStore.resultado = mockResultadoDIA;
      const uiStore = useUIStore();
      const spy = vi.spyOn(uiStore, 'mostrarToast');

      const { exportar } = useAnalysis();
      await exportar('pdf');

      expect(spy).toHaveBeenCalledWith('Error al exportar el informe', 'error');
    });
  });

  describe('getSeveridadColor', () => {
    it('retorna colores correctos para cada severidad', () => {
      const { getSeveridadColor } = useAnalysis();

      expect(getSeveridadColor('CRITICA')).toBe('error');
      expect(getSeveridadColor('ALTA')).toBe('warning');
      expect(getSeveridadColor('MEDIA')).toBe('info');
      expect(getSeveridadColor('BAJA')).toBe('success');
      expect(getSeveridadColor('INFO')).toBe('neutral');
    });
  });

  describe('getSeveridadIcono', () => {
    it('retorna iconos correctos', () => {
      const { getSeveridadIcono } = useAnalysis();

      expect(getSeveridadIcono('CRITICA')).toBe('!');
      expect(getSeveridadIcono('ALTA')).toBe('!');
      expect(getSeveridadIcono('MEDIA')).toBe('i');
      expect(getSeveridadIcono('BAJA')).toBe('');
      expect(getSeveridadIcono('INFO')).toBe('i');
    });
  });
});
