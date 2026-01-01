import { computed } from 'vue';
import { useAnalysisStore } from '@/stores/analysis';
import { useProyectosStore } from '@/stores/proyectos';
import { useUIStore } from '@/stores/ui';
import { exportarInforme } from '@/services/prefactibilidad';
import type { FormatoExportacion, Severidad } from '@/types';

export function useAnalysis() {
  const analysisStore = useAnalysisStore();
  const proyectosStore = useProyectosStore();
  const uiStore = useUIStore();

  const puedeAnalizar = computed(() => proyectosStore.puedeAnalizar);

  const resumenClasificacion = computed(() => {
    const c = analysisStore.clasificacion;
    if (!c) return null;

    return {
      via: c.via_ingreso_recomendada,
      confianza: c.confianza,
      nivelConfianza: c.nivel_confianza,
      justificacion: c.justificacion,
      esEIA: c.via_ingreso_recomendada === 'EIA',
      colorClase:
        c.via_ingreso_recomendada === 'EIA'
          ? 'bg-warning text-warning-content'
          : 'bg-success text-success-content',
    };
  });

  const resumenRiesgo = computed(() => {
    const conteo = analysisStore.conteoAlertas;
    if (conteo.total === 0) return 'Sin alertas';
    if (conteo.CRITICA > 0) return `${conteo.CRITICA} alertas críticas`;
    if (conteo.ALTA > 0) return `${conteo.ALTA} alertas altas`;
    return `${conteo.total} alertas`;
  });

  const colorRiesgo = computed((): string => {
    const conteo = analysisStore.conteoAlertas;
    if (conteo.CRITICA > 0) return 'error';
    if (conteo.ALTA > 0) return 'warning';
    if (conteo.MEDIA > 0) return 'info';
    return 'success';
  });

  async function ejecutarAnalisisRapido() {
    await analysisStore.analizarProyecto(false);
    if (analysisStore.tieneResultado) {
      uiStore.expandirResultados();
      uiStore.setTabResultados('resumen');
    }
  }

  async function ejecutarAnalisisCompleto() {
    await analysisStore.analizarProyecto(true);
    if (analysisStore.tieneResultado) {
      uiStore.expandirResultados();
      uiStore.setTabResultados('resumen');
    }
  }

  async function exportar(formato: FormatoExportacion) {
    if (!analysisStore.resultado) {
      uiStore.mostrarToast('No hay resultado para exportar', 'warning');
      return;
    }

    try {
      await exportarInforme(analysisStore.resultado, formato);
      uiStore.mostrarToast(`Informe exportado como ${formato.toUpperCase()}`, 'success');
    } catch {
      uiStore.mostrarToast('Error al exportar el informe', 'error');
    }
  }

  function getSeveridadColor(severidad: Severidad): string {
    const colores: Record<Severidad, string> = {
      CRITICA: 'error',
      ALTA: 'warning',
      MEDIA: 'info',
      BAJA: 'success',
      INFO: 'neutral',
    };
    return colores[severidad];
  }

  function getSeveridadIcono(severidad: Severidad): string {
    const iconos: Record<Severidad, string> = {
      CRITICA: '!',
      ALTA: '!',
      MEDIA: 'i',
      BAJA: '',
      INFO: 'i',
    };
    return iconos[severidad];
  }

  return {
    resultado: computed(() => analysisStore.resultado),
    cargando: computed(() => analysisStore.cargando),
    error: computed(() => analysisStore.error),
    puedeAnalizar,
    resumenClasificacion,
    resumenRiesgo,
    colorRiesgo,
    ejecutarAnalisisRapido,
    ejecutarAnalisisCompleto,
    exportar,
    getSeveridadColor,
    getSeveridadIcono,
  };
}
