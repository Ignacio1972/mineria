import { describe, it, expect, vi, beforeEach } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import { useProject } from '@/composables/useProject';
import { useProjectStore } from '@/stores/project';
import { useAnalysisStore } from '@/stores/analysis';
import { useUIStore } from '@/stores/ui';
import type { GeometriaGeoJSON } from '@/types';

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
  randomUUID: () => 'test-uuid-123',
});

// Mock window.confirm
vi.stubGlobal('confirm', vi.fn());

describe('useProject', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
    vi.mocked(window.confirm).mockReturnValue(true);
  });

  describe('propiedades computadas', () => {
    it('expone proyecto actual', () => {
      const projectStore = useProjectStore();
      projectStore.crearNuevoProyecto();

      const { proyecto } = useProject();

      expect(proyecto.value).not.toBeNull();
    });

    it('expone datos del proyecto', () => {
      const projectStore = useProjectStore();
      projectStore.crearNuevoProyecto();
      projectStore.actualizarDatos({ nombre: 'Test' });

      const { datos } = useProject();

      expect(datos.value?.nombre).toBe('Test');
    });

    it('expone geometria del proyecto', () => {
      const projectStore = useProjectStore();
      projectStore.crearNuevoProyecto();
      const geom: GeometriaGeoJSON = { type: 'Polygon', coordinates: [] };
      projectStore.actualizarGeometria(geom);

      const { geometria } = useProject();

      expect(geometria.value).toEqual(geom);
    });

    it('esNuevo es true sin id', () => {
      const { esNuevo } = useProject();
      expect(esNuevo.value).toBe(true);
    });

    it('tieneModificaciones refleja estado del store', () => {
      const projectStore = useProjectStore();
      const { tieneModificaciones } = useProject();

      expect(tieneModificaciones.value).toBe(false);

      projectStore.crearNuevoProyecto();
      projectStore.actualizarDatos({ nombre: 'Cambio' });

      expect(tieneModificaciones.value).toBe(true);
    });

    it('esValido refleja validacion del store', () => {
      const projectStore = useProjectStore();
      const { esValido } = useProject();

      expect(esValido.value).toBe(false);

      projectStore.crearNuevoProyecto();
      projectStore.actualizarDatos({ nombre: 'Test' });
      projectStore.actualizarGeometria({ type: 'Polygon', coordinates: [[]] });

      expect(esValido.value).toBe(true);
    });
  });

  describe('iniciarNuevoProyecto', () => {
    it('crea nuevo proyecto', () => {
      const projectStore = useProjectStore();
      const { iniciarNuevoProyecto } = useProject();

      iniciarNuevoProyecto();

      expect(projectStore.proyecto).not.toBeNull();
    });

    it('limpia resultado de analisis', () => {
      const analysisStore = useAnalysisStore();
      analysisStore.resultado = { id: 'test' } as any;

      const { iniciarNuevoProyecto } = useProject();
      iniciarNuevoProyecto();

      expect(analysisStore.resultado).toBeNull();
    });

    it('colapsa panel de resultados', () => {
      const uiStore = useUIStore();
      uiStore.expandirResultados();

      const { iniciarNuevoProyecto } = useProject();
      iniciarNuevoProyecto();

      expect(uiStore.panelResultadosExpandido).toBe(false);
    });

    it('muestra toast informativo', () => {
      const uiStore = useUIStore();
      const spy = vi.spyOn(uiStore, 'mostrarToast');

      const { iniciarNuevoProyecto } = useProject();
      iniciarNuevoProyecto();

      expect(spy).toHaveBeenCalledWith('Nuevo proyecto iniciado', 'info');
    });

    it('pide confirmacion si hay cambios sin guardar', () => {
      const projectStore = useProjectStore();
      projectStore.crearNuevoProyecto();
      projectStore.actualizarDatos({ nombre: 'Cambio' });

      const { iniciarNuevoProyecto } = useProject();
      iniciarNuevoProyecto();

      expect(window.confirm).toHaveBeenCalled();
    });

    it('no crea proyecto si usuario cancela confirmacion', () => {
      const projectStore = useProjectStore();
      projectStore.crearNuevoProyecto();
      projectStore.actualizarDatos({ nombre: 'Cambio' });
      const idOriginal = projectStore.proyecto?.id;

      vi.mocked(window.confirm).mockReturnValue(false);

      const { iniciarNuevoProyecto } = useProject();
      iniciarNuevoProyecto();

      expect(projectStore.proyecto?.id).toBe(idOriginal);
    });
  });

  describe('actualizarDatos', () => {
    it('actualiza datos del proyecto', () => {
      const projectStore = useProjectStore();
      const { actualizarDatos } = useProject();

      actualizarDatos({ nombre: 'Minera Norte', region: 'Antofagasta' });

      expect(projectStore.proyecto?.datos.nombre).toBe('Minera Norte');
      expect(projectStore.proyecto?.datos.region).toBe('Antofagasta');
    });
  });

  describe('actualizarGeometria', () => {
    it('actualiza geometria del proyecto', () => {
      const projectStore = useProjectStore();
      const { actualizarGeometria } = useProject();

      const geom: GeometriaGeoJSON = {
        type: 'Polygon',
        coordinates: [[[-70, -23], [-70, -24], [-69, -24], [-69, -23], [-70, -23]]],
      };

      actualizarGeometria(geom);

      expect(projectStore.proyecto?.geometria).toEqual(geom);
    });

    it('muestra toast cuando se agrega geometria', () => {
      const uiStore = useUIStore();
      const spy = vi.spyOn(uiStore, 'mostrarToast');

      const { actualizarGeometria } = useProject();
      actualizarGeometria({ type: 'Polygon', coordinates: [[]] });

      expect(spy).toHaveBeenCalledWith('Geometría del proyecto actualizada', 'success');
    });

    it('no muestra toast cuando se elimina geometria', () => {
      const uiStore = useUIStore();
      const spy = vi.spyOn(uiStore, 'mostrarToast');

      const { actualizarGeometria } = useProject();
      actualizarGeometria(null);

      expect(spy).not.toHaveBeenCalled();
    });
  });

  describe('guardar', () => {
    it('requiere nombre del proyecto', () => {
      const projectStore = useProjectStore();
      projectStore.crearNuevoProyecto();
      const uiStore = useUIStore();
      const spy = vi.spyOn(uiStore, 'mostrarToast');

      const { guardar } = useProject();
      const result = guardar();

      expect(result).toBe(false);
      expect(spy).toHaveBeenCalledWith('Ingrese un nombre para el proyecto', 'warning');
    });

    it('guarda proyecto con nombre', () => {
      const projectStore = useProjectStore();
      projectStore.crearNuevoProyecto();
      projectStore.actualizarDatos({ nombre: 'Proyecto Test' });

      const { guardar } = useProject();
      const result = guardar();

      expect(result).toBe(true);
      expect(projectStore.proyectosGuardados.length).toBe(1);
    });

    it('muestra toast de exito al guardar', () => {
      const projectStore = useProjectStore();
      projectStore.crearNuevoProyecto();
      projectStore.actualizarDatos({ nombre: 'Test' });
      const uiStore = useUIStore();
      const spy = vi.spyOn(uiStore, 'mostrarToast');

      const { guardar } = useProject();
      guardar();

      expect(spy).toHaveBeenCalledWith('Proyecto guardado', 'success');
    });
  });

  describe('cargar', () => {
    it('carga proyecto por id', () => {
      const projectStore = useProjectStore();
      projectStore.crearNuevoProyecto();
      projectStore.actualizarDatos({ nombre: 'Proyecto Guardado' });
      projectStore.guardarProyecto();
      const id = projectStore.proyecto!.id;
      projectStore.limpiarProyecto();

      const { cargar } = useProject();
      cargar(id);

      expect(projectStore.proyecto?.datos.nombre).toBe('Proyecto Guardado');
    });

    it('pide confirmacion si hay cambios sin guardar', () => {
      const projectStore = useProjectStore();
      projectStore.crearNuevoProyecto();
      projectStore.actualizarDatos({ nombre: 'Cambio' });

      const { cargar } = useProject();
      cargar('some-id');

      expect(window.confirm).toHaveBeenCalled();
    });

    it('limpia resultado de analisis al cargar', () => {
      const projectStore = useProjectStore();
      const analysisStore = useAnalysisStore();
      analysisStore.resultado = { id: 'test' } as any;

      projectStore.crearNuevoProyecto();
      projectStore.guardarProyecto();
      const id = projectStore.proyecto!.id;

      const { cargar } = useProject();
      cargar(id);

      expect(analysisStore.resultado).toBeNull();
    });
  });

  describe('eliminar', () => {
    it('elimina proyecto despues de confirmacion', () => {
      const projectStore = useProjectStore();
      projectStore.crearNuevoProyecto();
      projectStore.guardarProyecto();
      const id = projectStore.proyecto!.id;

      const { eliminar } = useProject();
      eliminar(id);

      expect(projectStore.proyectosGuardados.length).toBe(0);
    });

    it('no elimina si usuario cancela', () => {
      const projectStore = useProjectStore();
      projectStore.crearNuevoProyecto();
      projectStore.guardarProyecto();
      const id = projectStore.proyecto!.id;

      vi.mocked(window.confirm).mockReturnValue(false);

      const { eliminar } = useProject();
      eliminar(id);

      expect(projectStore.proyectosGuardados.length).toBe(1);
    });
  });

  describe('limpiar', () => {
    it('limpia proyecto actual', () => {
      const projectStore = useProjectStore();
      projectStore.crearNuevoProyecto();

      const { limpiar } = useProject();
      limpiar();

      expect(projectStore.proyecto).toBeNull();
    });

    it('pide confirmacion si hay cambios', () => {
      const projectStore = useProjectStore();
      projectStore.crearNuevoProyecto();
      projectStore.actualizarDatos({ nombre: 'Cambio' });

      const { limpiar } = useProject();
      limpiar();

      expect(window.confirm).toHaveBeenCalled();
    });
  });
});
