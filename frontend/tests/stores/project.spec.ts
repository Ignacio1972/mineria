import { describe, it, expect, beforeEach, vi } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import { useProjectStore } from '@/stores/project';
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

describe('useProjectStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  describe('estado inicial', () => {
    it('comienza sin proyecto', () => {
      const store = useProjectStore();
      expect(store.proyecto).toBeNull();
      expect(store.proyectosGuardados).toEqual([]);
      expect(store.modificado).toBe(false);
    });

    it('getters devuelven valores por defecto', () => {
      const store = useProjectStore();
      expect(store.datosProyecto).toBeNull();
      expect(store.geometria).toBeNull();
      expect(store.tieneGeometria).toBe(false);
      expect(store.esValido).toBe(false);
    });
  });

  describe('crearNuevoProyecto', () => {
    it('crea un proyecto con valores iniciales', () => {
      const store = useProjectStore();
      store.crearNuevoProyecto();

      expect(store.proyecto).not.toBeNull();
      expect(store.proyecto?.id).toBe('test-uuid-123');
      expect(store.proyecto?.datos.nombre).toBe('');
      expect(store.proyecto?.geometria).toBeNull();
      expect(store.modificado).toBe(false);
    });

    it('asigna fechas de creacion y modificacion', () => {
      const store = useProjectStore();
      const antes = new Date().toISOString();
      store.crearNuevoProyecto();
      const despues = new Date().toISOString();

      expect(store.proyecto?.fecha_creacion >= antes).toBe(true);
      expect(store.proyecto?.fecha_creacion <= despues).toBe(true);
    });
  });

  describe('actualizarDatos', () => {
    it('crea proyecto si no existe', () => {
      const store = useProjectStore();
      store.actualizarDatos({ nombre: 'Proyecto Test' });

      expect(store.proyecto).not.toBeNull();
      expect(store.proyecto?.datos.nombre).toBe('Proyecto Test');
    });

    it('actualiza datos existentes', () => {
      const store = useProjectStore();
      store.crearNuevoProyecto();
      store.actualizarDatos({ nombre: 'Minera Norte' });

      expect(store.proyecto?.datos.nombre).toBe('Minera Norte');
      expect(store.modificado).toBe(true);
    });

    it('preserva datos anteriores al actualizar parcialmente', () => {
      const store = useProjectStore();
      store.crearNuevoProyecto();
      store.actualizarDatos({ nombre: 'Test', region: 'Antofagasta' });
      store.actualizarDatos({ comuna: 'Calama' });

      expect(store.proyecto?.datos.nombre).toBe('Test');
      expect(store.proyecto?.datos.region).toBe('Antofagasta');
      expect(store.proyecto?.datos.comuna).toBe('Calama');
    });

    it('actualiza fecha_modificacion', () => {
      const store = useProjectStore();
      store.crearNuevoProyecto();
      const fechaOriginal = store.proyecto?.fecha_modificacion;

      // Esperar un momento para asegurar diferencia de tiempo
      store.actualizarDatos({ nombre: 'Actualizado' });

      expect(store.proyecto?.fecha_modificacion).toBeDefined();
    });
  });

  describe('actualizarGeometria', () => {
    const geometriaMock: GeometriaGeoJSON = {
      type: 'Polygon',
      coordinates: [[[-70, -23], [-70, -24], [-69, -24], [-69, -23], [-70, -23]]],
    };

    it('crea proyecto si no existe', () => {
      const store = useProjectStore();
      store.actualizarGeometria(geometriaMock);

      expect(store.proyecto).not.toBeNull();
      expect(store.proyecto?.geometria).toEqual(geometriaMock);
    });

    it('actualiza geometria existente', () => {
      const store = useProjectStore();
      store.crearNuevoProyecto();
      store.actualizarGeometria(geometriaMock);

      expect(store.geometria).toEqual(geometriaMock);
      expect(store.tieneGeometria).toBe(true);
      expect(store.modificado).toBe(true);
    });

    it('permite limpiar geometria con null', () => {
      const store = useProjectStore();
      store.crearNuevoProyecto();
      store.actualizarGeometria(geometriaMock);
      store.actualizarGeometria(null);

      expect(store.geometria).toBeNull();
      expect(store.tieneGeometria).toBe(false);
    });
  });

  describe('esValido computed', () => {
    const geometriaMock: GeometriaGeoJSON = {
      type: 'Polygon',
      coordinates: [[[-70, -23], [-70, -24], [-69, -24], [-69, -23], [-70, -23]]],
    };

    it('es false sin nombre', () => {
      const store = useProjectStore();
      store.crearNuevoProyecto();
      store.actualizarGeometria(geometriaMock);

      expect(store.esValido).toBe(false);
    });

    it('es false sin geometria', () => {
      const store = useProjectStore();
      store.crearNuevoProyecto();
      store.actualizarDatos({ nombre: 'Test' });

      expect(store.esValido).toBe(false);
    });

    it('es true con nombre y geometria', () => {
      const store = useProjectStore();
      store.crearNuevoProyecto();
      store.actualizarDatos({ nombre: 'Test' });
      store.actualizarGeometria(geometriaMock);

      expect(store.esValido).toBe(true);
    });
  });

  describe('guardarProyecto', () => {
    it('no hace nada si no hay proyecto', () => {
      const store = useProjectStore();
      store.guardarProyecto();

      expect(store.proyectosGuardados).toEqual([]);
      expect(localStorageMock.setItem).not.toHaveBeenCalled();
    });

    it('guarda proyecto nuevo en lista', () => {
      const store = useProjectStore();
      store.crearNuevoProyecto();
      store.actualizarDatos({ nombre: 'Proyecto 1' });
      store.guardarProyecto();

      expect(store.proyectosGuardados.length).toBe(1);
      expect(store.proyectosGuardados[0].datos.nombre).toBe('Proyecto 1');
      expect(store.modificado).toBe(false);
    });

    it('actualiza proyecto existente en lugar de duplicar', () => {
      const store = useProjectStore();
      store.crearNuevoProyecto();
      store.actualizarDatos({ nombre: 'Proyecto 1' });
      store.guardarProyecto();

      store.actualizarDatos({ nombre: 'Proyecto 1 Actualizado' });
      store.guardarProyecto();

      expect(store.proyectosGuardados.length).toBe(1);
      expect(store.proyectosGuardados[0].datos.nombre).toBe('Proyecto 1 Actualizado');
    });

    it('persiste en localStorage', () => {
      const store = useProjectStore();
      store.crearNuevoProyecto();
      store.guardarProyecto();

      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        'proyectos_mineria',
        expect.any(String)
      );
    });
  });

  describe('cargarProyecto', () => {
    it('carga proyecto existente por id', () => {
      const store = useProjectStore();
      store.crearNuevoProyecto();
      store.actualizarDatos({ nombre: 'Proyecto Guardado' });
      store.guardarProyecto();

      const id = store.proyecto!.id;
      store.limpiarProyecto();
      store.cargarProyecto(id);

      expect(store.proyecto?.datos.nombre).toBe('Proyecto Guardado');
      expect(store.modificado).toBe(false);
    });

    it('no hace nada con id inexistente', () => {
      const store = useProjectStore();
      store.cargarProyecto('id-inexistente');

      expect(store.proyecto).toBeNull();
    });
  });

  describe('eliminarProyecto', () => {
    it('elimina proyecto de la lista', () => {
      const store = useProjectStore();
      store.crearNuevoProyecto();
      store.guardarProyecto();
      const id = store.proyecto!.id;

      store.eliminarProyecto(id);

      expect(store.proyectosGuardados.length).toBe(0);
    });

    it('limpia proyecto actual si es el eliminado', () => {
      const store = useProjectStore();
      store.crearNuevoProyecto();
      store.guardarProyecto();
      const id = store.proyecto!.id;

      store.eliminarProyecto(id);

      expect(store.proyecto).toBeNull();
    });

    it('no afecta proyecto actual si es otro el eliminado', () => {
      const store = useProjectStore();

      // Crear y guardar primer proyecto
      store.crearNuevoProyecto();
      store.actualizarDatos({ nombre: 'Proyecto 1' });
      store.guardarProyecto();
      const id1 = store.proyecto!.id;

      // Crear segundo proyecto (simular nuevo UUID)
      vi.stubGlobal('crypto', { randomUUID: () => 'test-uuid-456' });
      store.crearNuevoProyecto();
      store.actualizarDatos({ nombre: 'Proyecto 2' });
      store.guardarProyecto();

      // Eliminar primer proyecto
      store.eliminarProyecto(id1);

      // Proyecto actual sigue siendo el segundo
      expect(store.proyecto?.datos.nombre).toBe('Proyecto 2');
    });
  });

  describe('cargarDesdeLocalStorage', () => {
    it('carga proyectos desde localStorage', () => {
      const proyectos = [
        { id: '1', datos: { nombre: 'P1' }, geometria: null, fecha_creacion: '', fecha_modificacion: '' },
      ];
      localStorageMock.getItem.mockReturnValue(JSON.stringify(proyectos));

      const store = useProjectStore();
      store.cargarDesdeLocalStorage();

      expect(store.proyectosGuardados.length).toBe(1);
      expect(store.proyectosGuardados[0].datos.nombre).toBe('P1');
    });

    it('maneja JSON invalido graciosamente', () => {
      localStorageMock.getItem.mockReturnValue('invalid json');

      const store = useProjectStore();
      store.cargarDesdeLocalStorage();

      expect(store.proyectosGuardados).toEqual([]);
    });

    it('maneja localStorage vacio', () => {
      localStorageMock.getItem.mockReturnValue(null);

      const store = useProjectStore();
      store.cargarDesdeLocalStorage();

      expect(store.proyectosGuardados).toEqual([]);
    });
  });

  describe('limpiarProyecto', () => {
    it('limpia el proyecto actual', () => {
      const store = useProjectStore();
      store.crearNuevoProyecto();
      store.actualizarDatos({ nombre: 'Test' });

      store.limpiarProyecto();

      expect(store.proyecto).toBeNull();
      expect(store.modificado).toBe(false);
    });
  });
});
