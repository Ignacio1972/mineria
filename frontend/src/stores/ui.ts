import { defineStore } from 'pinia';
import { ref, computed } from 'vue';

type TabResultados = 'resumen' | 'gis' | 'triggers' | 'alertas' | 'informe' | 'auditoria';
type Toast = {
  id: string;
  mensaje: string;
  tipo: 'success' | 'error' | 'warning' | 'info';
  duracion?: number;
};

export const useUIStore = defineStore('ui', () => {
  const sidebarAbierto = ref(true);
  const panelResultadosExpandido = ref(false);
  const tabResultadosActivo = ref<TabResultados>('resumen');
  const modalAbierto = ref<string | null>(null);
  const toasts = ref<Toast[]>([]);
  const tema = ref<'corporate' | 'dark'>('corporate');

  const mostrandoResultados = computed(
    () => panelResultadosExpandido.value
  );

  function toggleSidebar() {
    sidebarAbierto.value = !sidebarAbierto.value;
  }

  function abrirSidebar() {
    sidebarAbierto.value = true;
  }

  function cerrarSidebar() {
    sidebarAbierto.value = false;
  }

  function togglePanelResultados() {
    panelResultadosExpandido.value = !panelResultadosExpandido.value;
  }

  function expandirResultados() {
    panelResultadosExpandido.value = true;
  }

  function colapsarResultados() {
    panelResultadosExpandido.value = false;
  }

  function setTabResultados(tab: TabResultados) {
    tabResultadosActivo.value = tab;
    if (!panelResultadosExpandido.value) {
      expandirResultados();
    }
  }

  function abrirModal(id: string) {
    modalAbierto.value = id;
  }

  function cerrarModal() {
    modalAbierto.value = null;
  }

  function mostrarToast(
    mensaje: string,
    tipo: Toast['tipo'] = 'info',
    duracion = 5000
  ) {
    const id = crypto.randomUUID();
    toasts.value.push({ id, mensaje, tipo, duracion });

    if (duracion > 0) {
      setTimeout(() => {
        eliminarToast(id);
      }, duracion);
    }

    return id;
  }

  function eliminarToast(id: string) {
    toasts.value = toasts.value.filter((t) => t.id !== id);
  }

  function toggleTema() {
    tema.value = tema.value === 'corporate' ? 'dark' : 'corporate';
    document.documentElement.setAttribute('data-theme', tema.value);
    localStorage.setItem('tema_mineria', tema.value);
  }

  function cargarTema() {
    const saved = localStorage.getItem('tema_mineria') as typeof tema.value | null;
    if (saved) {
      tema.value = saved;
      document.documentElement.setAttribute('data-theme', saved);
    }
  }

  return {
    sidebarAbierto,
    panelResultadosExpandido,
    tabResultadosActivo,
    modalAbierto,
    toasts,
    tema,
    mostrandoResultados,
    toggleSidebar,
    abrirSidebar,
    cerrarSidebar,
    togglePanelResultados,
    expandirResultados,
    colapsarResultados,
    setTabResultados,
    abrirModal,
    cerrarModal,
    mostrarToast,
    eliminarToast,
    toggleTema,
    cargarTema,
  };
});
