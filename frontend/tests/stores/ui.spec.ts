import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import { useUIStore } from '@/stores/ui';

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
  randomUUID: () => 'toast-uuid-123',
});

// Mock document.documentElement.setAttribute
const setAttributeMock = vi.fn();
Object.defineProperty(document.documentElement, 'setAttribute', {
  value: setAttributeMock,
  writable: true,
});

describe('useUIStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe('estado inicial', () => {
    it('tiene valores por defecto correctos', () => {
      const store = useUIStore();

      expect(store.sidebarAbierto).toBe(true);
      expect(store.panelResultadosExpandido).toBe(false);
      expect(store.tabResultadosActivo).toBe('resumen');
      expect(store.modalAbierto).toBeNull();
      expect(store.toasts).toEqual([]);
      expect(store.tema).toBe('corporate');
    });

    it('mostrandoResultados refleja panelResultadosExpandido', () => {
      const store = useUIStore();
      expect(store.mostrandoResultados).toBe(false);

      store.expandirResultados();
      expect(store.mostrandoResultados).toBe(true);
    });
  });

  describe('sidebar', () => {
    it('toggleSidebar alterna el estado', () => {
      const store = useUIStore();
      expect(store.sidebarAbierto).toBe(true);

      store.toggleSidebar();
      expect(store.sidebarAbierto).toBe(false);

      store.toggleSidebar();
      expect(store.sidebarAbierto).toBe(true);
    });

    it('abrirSidebar abre el sidebar', () => {
      const store = useUIStore();
      store.sidebarAbierto = false;

      store.abrirSidebar();
      expect(store.sidebarAbierto).toBe(true);
    });

    it('cerrarSidebar cierra el sidebar', () => {
      const store = useUIStore();
      store.cerrarSidebar();
      expect(store.sidebarAbierto).toBe(false);
    });
  });

  describe('panel de resultados', () => {
    it('togglePanelResultados alterna el estado', () => {
      const store = useUIStore();
      expect(store.panelResultadosExpandido).toBe(false);

      store.togglePanelResultados();
      expect(store.panelResultadosExpandido).toBe(true);

      store.togglePanelResultados();
      expect(store.panelResultadosExpandido).toBe(false);
    });

    it('expandirResultados expande el panel', () => {
      const store = useUIStore();
      store.expandirResultados();
      expect(store.panelResultadosExpandido).toBe(true);
    });

    it('colapsarResultados colapsa el panel', () => {
      const store = useUIStore();
      store.expandirResultados();
      store.colapsarResultados();
      expect(store.panelResultadosExpandido).toBe(false);
    });

    it('setTabResultados cambia la tab activa', () => {
      const store = useUIStore();
      store.setTabResultados('alertas');
      expect(store.tabResultadosActivo).toBe('alertas');
    });

    it('setTabResultados expande el panel si esta colapsado', () => {
      const store = useUIStore();
      expect(store.panelResultadosExpandido).toBe(false);

      store.setTabResultados('gis');

      expect(store.tabResultadosActivo).toBe('gis');
      expect(store.panelResultadosExpandido).toBe(true);
    });

    it('setTabResultados no afecta panel ya expandido', () => {
      const store = useUIStore();
      store.expandirResultados();
      store.setTabResultados('triggers');

      expect(store.panelResultadosExpandido).toBe(true);
    });
  });

  describe('modales', () => {
    it('abrirModal establece el modal activo', () => {
      const store = useUIStore();
      store.abrirModal('confirmar-eliminar');
      expect(store.modalAbierto).toBe('confirmar-eliminar');
    });

    it('cerrarModal limpia el modal activo', () => {
      const store = useUIStore();
      store.abrirModal('test');
      store.cerrarModal();
      expect(store.modalAbierto).toBeNull();
    });
  });

  describe('toasts', () => {
    it('mostrarToast agrega un toast a la lista', () => {
      const store = useUIStore();
      store.mostrarToast('Mensaje de prueba', 'info');

      expect(store.toasts.length).toBe(1);
      expect(store.toasts[0].mensaje).toBe('Mensaje de prueba');
      expect(store.toasts[0].tipo).toBe('info');
      expect(store.toasts[0].id).toBe('toast-uuid-123');
    });

    it('mostrarToast usa tipo info por defecto', () => {
      const store = useUIStore();
      store.mostrarToast('Test');

      expect(store.toasts[0].tipo).toBe('info');
    });

    it('mostrarToast retorna el id del toast', () => {
      const store = useUIStore();
      const id = store.mostrarToast('Test');

      expect(id).toBe('toast-uuid-123');
    });

    it('mostrarToast elimina automaticamente despues de duracion', () => {
      const store = useUIStore();
      store.mostrarToast('Test', 'success', 3000);

      expect(store.toasts.length).toBe(1);

      vi.advanceTimersByTime(3000);

      expect(store.toasts.length).toBe(0);
    });

    it('mostrarToast no elimina con duracion 0', () => {
      const store = useUIStore();
      store.mostrarToast('Permanente', 'error', 0);

      vi.advanceTimersByTime(10000);

      expect(store.toasts.length).toBe(1);
    });

    it('eliminarToast remueve toast especifico', () => {
      const store = useUIStore();

      // Agregar multiples toasts con diferentes IDs
      vi.stubGlobal('crypto', { randomUUID: () => 'toast-1' });
      store.mostrarToast('Toast 1', 'info', 0);

      vi.stubGlobal('crypto', { randomUUID: () => 'toast-2' });
      store.mostrarToast('Toast 2', 'info', 0);

      expect(store.toasts.length).toBe(2);

      store.eliminarToast('toast-1');

      expect(store.toasts.length).toBe(1);
      expect(store.toasts[0].id).toBe('toast-2');
    });

    it('soporta diferentes tipos de toast', () => {
      const store = useUIStore();
      const tipos: Array<'success' | 'error' | 'warning' | 'info'> = [
        'success',
        'error',
        'warning',
        'info',
      ];

      tipos.forEach((tipo, index) => {
        vi.stubGlobal('crypto', { randomUUID: () => `toast-${index}` });
        store.mostrarToast(`Toast ${tipo}`, tipo, 0);
      });

      expect(store.toasts.length).toBe(4);
      tipos.forEach((tipo, index) => {
        expect(store.toasts[index].tipo).toBe(tipo);
      });
    });
  });

  describe('tema', () => {
    it('toggleTema alterna entre corporate y dark', () => {
      const store = useUIStore();
      expect(store.tema).toBe('corporate');

      store.toggleTema();
      expect(store.tema).toBe('dark');

      store.toggleTema();
      expect(store.tema).toBe('corporate');
    });

    it('toggleTema actualiza atributo data-theme en document', () => {
      const store = useUIStore();
      store.toggleTema();

      expect(setAttributeMock).toHaveBeenCalledWith('data-theme', 'dark');
    });

    it('toggleTema persiste en localStorage', () => {
      const store = useUIStore();
      store.toggleTema();

      expect(localStorageMock.setItem).toHaveBeenCalledWith('tema_mineria', 'dark');
    });

    it('cargarTema carga tema desde localStorage', () => {
      localStorageMock.getItem.mockReturnValue('dark');

      const store = useUIStore();
      store.cargarTema();

      expect(store.tema).toBe('dark');
      expect(setAttributeMock).toHaveBeenCalledWith('data-theme', 'dark');
    });

    it('cargarTema no hace nada si localStorage esta vacio', () => {
      localStorageMock.getItem.mockReturnValue(null);

      const store = useUIStore();
      const temaInicial = store.tema;
      store.cargarTema();

      expect(store.tema).toBe(temaInicial);
    });
  });
});
