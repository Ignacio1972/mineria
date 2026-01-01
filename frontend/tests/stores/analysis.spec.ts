import { describe, it, expect, beforeEach, vi } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import { useAnalysisStore } from '@/stores/analysis';
import { useProjectStore } from '@/stores/project';
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

// Mock servicios de prefactibilidad
vi.mock('@/services/prefactibilidad', () => ({
  ejecutarAnalisis: vi.fn(),
  ejecutarAnalisisRapido: vi.fn(),
}));

import { ejecutarAnalisis, ejecutarAnalisisRapido } from '@/services/prefactibilidad';

// Mock crypto.randomUUID para project store
vi.stubGlobal('crypto', {
  randomUUID: () => 'test-uuid-123',
});

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
    intersecciones: [
      { capa: 'snaspe', nombre_elemento: 'Reserva Test', dentro: true, porcentaje_interseccion: 15 },
    ],
    alertas_gis: ['Intersecta con area protegida'],
    area_proyecto_ha: 500,
    centroide: [-69.5, -23.5],
  },
  clasificacion_seia: {
    via_ingreso_recomendada: 'EIA',
    confianza: 0.85,
    nivel_confianza: 'ALTA',
    justificacion: 'El proyecto intersecta con area protegida SNASPE',
    puntaje_matriz: 0.78,
  },
  triggers: [
    {
      letra: 'd',
      descripcion: 'Localizacion en areas protegidas',
      detalle: 'El proyecto se ubica dentro de la Reserva Test',
      severidad: 'CRITICA',
      fundamento_legal: 'Art. 11 letra d) Ley 19.300',
      peso: 1.0,
    },
  ],
  alertas: [
    {
      id: 'alert-1',
      nivel: 'CRITICA',
      categoria: 'areas_protegidas',
      titulo: 'Interseccion con SNASPE',
      descripcion: 'El proyecto intersecta con la Reserva Test',
      acciones_requeridas: ['Obtener autorizacion de CONAF'],
    },
    {
      id: 'alert-2',
      nivel: 'ALTA',
      categoria: 'recursos_hidricos',
      titulo: 'Proximidad a glaciar',
      descripcion: 'El proyecto esta a 500m de un glaciar',
      acciones_requeridas: ['Evaluar impacto en glaciar'],
    },
    {
      id: 'alert-3',
      nivel: 'MEDIA',
      categoria: 'comunidades',
      titulo: 'Comunidad cercana',
      descripcion: 'Comunidad a 2km del proyecto',
      acciones_requeridas: ['Realizar consulta ciudadana'],
    },
  ],
  normativa_citada: [
    {
      nombre: 'Ley 19.300',
      articulo: '11',
      relevancia: 0.95,
      extracto: 'Los proyectos que se encuentren ubicados...',
    },
  ],
  metricas: {
    tiempo_analisis_segundos: 2.5,
    tiempo_gis_ms: 150,
    tiempo_rag_ms: 300,
  },
};

const mockGeometria: GeometriaGeoJSON = {
  type: 'Polygon',
  coordinates: [[[-70, -23], [-70, -24], [-69, -24], [-69, -23], [-70, -23]]],
};

describe('useAnalysisStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
    localStorageMock.getItem.mockReturnValue(null);
  });

  describe('estado inicial', () => {
    it('comienza sin resultado', () => {
      const store = useAnalysisStore();

      expect(store.resultado).toBeNull();
      expect(store.historial).toEqual([]);
      expect(store.cargando).toBe(false);
      expect(store.error).toBeNull();
      expect(store.modoAnalisis).toBe('rapido');
    });

    it('getters devuelven valores por defecto', () => {
      const store = useAnalysisStore();

      expect(store.tieneResultado).toBe(false);
      expect(store.clasificacion).toBeNull();
      expect(store.triggers).toEqual([]);
      expect(store.alertas).toEqual([]);
      expect(store.informe).toBeNull();
    });
  });

  describe('alertasPorSeveridad computed', () => {
    it('agrupa alertas por severidad correctamente', () => {
      const store = useAnalysisStore();
      store.resultado = mockResultado;

      const porSeveridad = store.alertasPorSeveridad;

      expect(porSeveridad.CRITICA.length).toBe(1);
      expect(porSeveridad.ALTA.length).toBe(1);
      expect(porSeveridad.MEDIA.length).toBe(1);
      expect(porSeveridad.BAJA.length).toBe(0);
      expect(porSeveridad.INFO.length).toBe(0);
    });

    it('devuelve arrays vacios sin resultado', () => {
      const store = useAnalysisStore();
      const porSeveridad = store.alertasPorSeveridad;

      expect(porSeveridad.CRITICA).toEqual([]);
      expect(porSeveridad.ALTA).toEqual([]);
    });
  });

  describe('conteoAlertas computed', () => {
    it('cuenta alertas por severidad', () => {
      const store = useAnalysisStore();
      store.resultado = mockResultado;

      const conteo = store.conteoAlertas;

      expect(conteo.CRITICA).toBe(1);
      expect(conteo.ALTA).toBe(1);
      expect(conteo.MEDIA).toBe(1);
      expect(conteo.BAJA).toBe(0);
      expect(conteo.INFO).toBe(0);
      expect(conteo.total).toBe(3);
    });
  });

  describe('analizarProyecto', () => {
    it('requiere datos y geometria del proyecto', async () => {
      const store = useAnalysisStore();
      const projectStore = useProjectStore();

      await store.analizarProyecto();

      expect(store.error).toBe('Debe completar los datos del proyecto y dibujar el polígono');
      expect(ejecutarAnalisis).not.toHaveBeenCalled();
      expect(ejecutarAnalisisRapido).not.toHaveBeenCalled();
    });

    it('ejecuta analisis rapido por defecto', async () => {
      vi.mocked(ejecutarAnalisisRapido).mockResolvedValue(mockResultado);

      const store = useAnalysisStore();
      const projectStore = useProjectStore();

      projectStore.crearNuevoProyecto();
      projectStore.actualizarDatos({ nombre: 'Test' });
      projectStore.actualizarGeometria(mockGeometria);

      await store.analizarProyecto(false);

      expect(ejecutarAnalisisRapido).toHaveBeenCalled();
      expect(ejecutarAnalisis).not.toHaveBeenCalled();
      expect(store.modoAnalisis).toBe('rapido');
      expect(store.resultado).toEqual(mockResultado);
    });

    it('ejecuta analisis completo con LLM cuando se solicita', async () => {
      vi.mocked(ejecutarAnalisis).mockResolvedValue(mockResultado);

      const store = useAnalysisStore();
      const projectStore = useProjectStore();

      projectStore.crearNuevoProyecto();
      projectStore.actualizarDatos({ nombre: 'Test' });
      projectStore.actualizarGeometria(mockGeometria);

      await store.analizarProyecto(true);

      expect(ejecutarAnalisis).toHaveBeenCalled();
      expect(ejecutarAnalisisRapido).not.toHaveBeenCalled();
      expect(store.modoAnalisis).toBe('completo');
    });

    it('establece cargando durante el analisis', async () => {
      vi.mocked(ejecutarAnalisisRapido).mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve(mockResultado), 100))
      );

      const store = useAnalysisStore();
      const projectStore = useProjectStore();

      projectStore.crearNuevoProyecto();
      projectStore.actualizarDatos({ nombre: 'Test' });
      projectStore.actualizarGeometria(mockGeometria);

      const promise = store.analizarProyecto();

      expect(store.cargando).toBe(true);
      expect(store.error).toBeNull();

      await promise;

      expect(store.cargando).toBe(false);
    });

    it('maneja errores del servicio', async () => {
      vi.mocked(ejecutarAnalisisRapido).mockRejectedValue(new Error('Error del servidor'));

      const store = useAnalysisStore();
      const projectStore = useProjectStore();

      projectStore.crearNuevoProyecto();
      projectStore.actualizarDatos({ nombre: 'Test' });
      projectStore.actualizarGeometria(mockGeometria);

      await store.analizarProyecto();

      expect(store.error).toBe('Error del servidor');
      expect(store.resultado).toBeNull();
      expect(store.cargando).toBe(false);
    });

    it('agrega resultado al historial', async () => {
      vi.mocked(ejecutarAnalisisRapido).mockResolvedValue(mockResultado);

      const store = useAnalysisStore();
      const projectStore = useProjectStore();

      projectStore.crearNuevoProyecto();
      projectStore.actualizarDatos({ nombre: 'Test' });
      projectStore.actualizarGeometria(mockGeometria);

      await store.analizarProyecto();

      expect(store.historial.length).toBe(1);
      expect(store.historial[0]).toEqual(mockResultado);
    });

    it('limita historial a 10 elementos', async () => {
      vi.mocked(ejecutarAnalisisRapido).mockResolvedValue(mockResultado);

      const store = useAnalysisStore();
      const projectStore = useProjectStore();

      projectStore.crearNuevoProyecto();
      projectStore.actualizarDatos({ nombre: 'Test' });
      projectStore.actualizarGeometria(mockGeometria);

      // Agregar 12 analisis
      for (let i = 0; i < 12; i++) {
        await store.analizarProyecto();
      }

      expect(store.historial.length).toBe(10);
    });

    it('persiste historial en localStorage', async () => {
      vi.mocked(ejecutarAnalisisRapido).mockResolvedValue(mockResultado);

      const store = useAnalysisStore();
      const projectStore = useProjectStore();

      projectStore.crearNuevoProyecto();
      projectStore.actualizarDatos({ nombre: 'Test' });
      projectStore.actualizarGeometria(mockGeometria);

      await store.analizarProyecto();

      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        'historial_analisis',
        expect.any(String)
      );
    });
  });

  describe('limpiarResultado', () => {
    it('limpia resultado y error', () => {
      const store = useAnalysisStore();
      store.resultado = mockResultado;
      store.error = 'Error previo';

      store.limpiarResultado();

      expect(store.resultado).toBeNull();
      expect(store.error).toBeNull();
    });
  });

  describe('cargarHistorial', () => {
    it('carga historial desde localStorage', () => {
      const historialGuardado = [mockResultado];
      localStorageMock.getItem.mockReturnValue(JSON.stringify(historialGuardado));

      const store = useAnalysisStore();
      store.cargarHistorial();

      expect(store.historial.length).toBe(1);
      expect(store.historial[0].id).toBe(mockResultado.id);
    });

    it('maneja JSON invalido graciosamente', () => {
      localStorageMock.getItem.mockReturnValue('invalid json');

      const store = useAnalysisStore();
      store.cargarHistorial();

      expect(store.historial).toEqual([]);
    });

    it('maneja localStorage vacio', () => {
      localStorageMock.getItem.mockReturnValue(null);

      const store = useAnalysisStore();
      store.cargarHistorial();

      expect(store.historial).toEqual([]);
    });
  });

  describe('cargarResultadoHistorial', () => {
    it('carga resultado del historial por id', () => {
      const store = useAnalysisStore();
      store.historial = [mockResultado];

      store.cargarResultadoHistorial('analisis-001');

      expect(store.resultado).toEqual(mockResultado);
    });

    it('no hace nada con id inexistente', () => {
      const store = useAnalysisStore();
      store.historial = [mockResultado];
      store.resultado = null;

      store.cargarResultadoHistorial('id-inexistente');

      expect(store.resultado).toBeNull();
    });
  });

  describe('clasificacion computed', () => {
    it('devuelve clasificacion SEIA del resultado', () => {
      const store = useAnalysisStore();
      store.resultado = mockResultado;

      expect(store.clasificacion).toEqual(mockResultado.clasificacion_seia);
      expect(store.clasificacion?.via_ingreso_recomendada).toBe('EIA');
    });
  });

  describe('triggers computed', () => {
    it('devuelve triggers del resultado', () => {
      const store = useAnalysisStore();
      store.resultado = mockResultado;

      expect(store.triggers.length).toBe(1);
      expect(store.triggers[0].letra).toBe('d');
    });
  });

  describe('informe computed', () => {
    it('devuelve null si no hay informe', () => {
      const store = useAnalysisStore();
      store.resultado = mockResultado;

      expect(store.informe).toBeNull();
    });

    it('devuelve informe si existe', () => {
      const store = useAnalysisStore();
      const resultadoConInforme = {
        ...mockResultado,
        informe: {
          secciones: [],
          texto_completo: 'Informe completo',
          fecha_generacion: '2024-01-15',
        },
      };
      store.resultado = resultadoConInforme;

      expect(store.informe).not.toBeNull();
      expect(store.informe?.texto_completo).toBe('Informe completo');
    });
  });
});
