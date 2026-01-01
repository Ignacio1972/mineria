import { ref, computed } from 'vue';
import { useAnalysisStore } from '@/stores/analysis';
import { useUIStore } from '@/stores/ui';
import { exportarInforme } from '@/services/prefactibilidad';
import type { FormatoExportacion } from '@/types';
import { FORMATOS_EXPORTACION } from '@/types';

export function useExport() {
  const analysisStore = useAnalysisStore();
  const uiStore = useUIStore();
  const exportando = ref(false);
  const formatoSeleccionado = ref<FormatoExportacion>('pdf');

  const puedeExportar = computed(() => !!analysisStore.resultado);
  const formatos = FORMATOS_EXPORTACION;

  async function exportar(formato?: FormatoExportacion) {
    const fmt = formato || formatoSeleccionado.value;

    if (!analysisStore.resultado) {
      uiStore.mostrarToast('No hay resultado para exportar', 'warning');
      return false;
    }

    exportando.value = true;

    try {
      await exportarInforme(analysisStore.resultado, fmt);
      uiStore.mostrarToast(
        `Informe exportado como ${fmt.toUpperCase()}`,
        'success'
      );
      return true;
    } catch {
      uiStore.mostrarToast('Error al exportar el informe', 'error');
      return false;
    } finally {
      exportando.value = false;
    }
  }

  function seleccionarFormato(formato: FormatoExportacion) {
    formatoSeleccionado.value = formato;
  }

  return {
    exportando,
    formatoSeleccionado,
    puedeExportar,
    formatos,
    exportar,
    seleccionarFormato,
  };
}
