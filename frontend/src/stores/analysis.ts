import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { ResultadoAnalisis, Severidad, AuditoriaAnalisis } from '@/types';
import {
  ejecutarAnalisisIntegrado,
  obtenerUltimoAnalisis,
  obtenerHistorialAnalisis,
  obtenerAuditoria,
} from '@/services/prefactibilidad';
import { useProyectosStore } from './proyectos';

export const useAnalysisStore = defineStore('analysis', () => {
  const resultado = ref<ResultadoAnalisis | null>(null);
  const historial = ref<ResultadoAnalisis[]>([]);
  const auditoria = ref<AuditoriaAnalisis | null>(null);
  const cargando = ref(false);
  const cargandoHistorial = ref(false);
  const cargandoAuditoria = ref(false);
  const error = ref<string | null>(null);
  const modoAnalisis = ref<'completo' | 'rapido'>('rapido');

  const tieneResultado = computed(() => !!resultado.value);

  const clasificacion = computed(() => resultado.value?.clasificacion_seia || null);

  const triggers = computed(() => resultado.value?.triggers || []);

  const alertas = computed(() => resultado.value?.alertas || []);

  const alertasPorSeveridad = computed(() => {
    const grouped: Record<Severidad, typeof alertas.value> = {
      CRITICA: [],
      ALTA: [],
      MEDIA: [],
      BAJA: [],
      INFO: [],
    };

    for (const alerta of alertas.value) {
      grouped[alerta.nivel].push(alerta);
    }

    return grouped;
  });

  const conteoAlertas = computed(() => ({
    CRITICA: alertasPorSeveridad.value.CRITICA.length,
    ALTA: alertasPorSeveridad.value.ALTA.length,
    MEDIA: alertasPorSeveridad.value.MEDIA.length,
    BAJA: alertasPorSeveridad.value.BAJA.length,
    INFO: alertasPorSeveridad.value.INFO.length,
    total: alertas.value.length,
  }));

  const informe = computed(() => resultado.value?.informe || null);

  /**
   * Ejecuta análisis con persistencia en BD.
   * Usa el endpoint /analisis-integrado que guarda los resultados.
   */
  async function analizarProyecto(usarLLM = false) {
    const proyectosStore = useProyectosStore();
    const proyecto = proyectosStore.proyectoActual;

    if (!proyecto?.nombre || !proyecto?.geometria) {
      error.value = 'Debe completar los datos del proyecto y dibujar el polígono';
      return;
    }

    // Verificar que el proyecto tiene ID (está guardado en BD)
    if (!proyecto.id) {
      error.value = 'El proyecto debe estar guardado antes de analizar';
      return;
    }

    const proyectoId = parseInt(proyecto.id, 10);
    if (isNaN(proyectoId)) {
      error.value = 'ID de proyecto inválido';
      return;
    }

    cargando.value = true;
    error.value = null;

    try {
      const tipo = usarLLM ? 'completo' : 'rapido';
      modoAnalisis.value = tipo;

      // Usar análisis integrado que persiste en BD
      resultado.value = await ejecutarAnalisisIntegrado(proyectoId, tipo);

      // Agregar al historial local (como cache)
      historial.value.unshift(resultado.value);
      if (historial.value.length > 10) {
        historial.value = historial.value.slice(0, 10);
      }
    } catch (e) {
      const errorMsg = e instanceof Error ? e.message :
        (e as { detail?: string })?.detail || 'Error al ejecutar el análisis';
      error.value = errorMsg;
      resultado.value = null;
    } finally {
      cargando.value = false;
    }
  }

  /**
   * Carga el último análisis de un proyecto desde la BD.
   * Usar al montar la vista de análisis.
   */
  async function cargarUltimoAnalisis(proyectoId: number) {
    console.log('[AnalysisStore] cargarUltimoAnalisis llamado con proyectoId:', proyectoId);
    cargando.value = true;
    error.value = null;

    try {
      console.log('[AnalysisStore] Llamando a obtenerUltimoAnalisis...');
      resultado.value = await obtenerUltimoAnalisis(proyectoId);
      console.log('[AnalysisStore] Resultado obtenido:', resultado.value?.id);
    } catch (e) {
      // 404 es esperado si no hay análisis previos
      const status = (e as { status_code?: number })?.status_code;
      console.log('[AnalysisStore] Error status:', status, e);
      if (status !== 404) {
        console.warn('Error cargando análisis:', e);
      }
      resultado.value = null;
    } finally {
      cargando.value = false;
    }
  }

  /**
   * Carga el historial de análisis de un proyecto desde la BD.
   */
  async function cargarHistorialDesdeServidor(proyectoId: number) {
    cargandoHistorial.value = true;

    try {
      const historialBD = await obtenerHistorialAnalisis(proyectoId);
      // El historial del servidor es un resumen, no el análisis completo
      // Mantenerlo por separado o convertir según necesidades
      console.log('Historial cargado desde BD:', historialBD.length, 'análisis');
    } catch (e) {
      console.warn('Error cargando historial:', e);
    } finally {
      cargandoHistorial.value = false;
    }
  }

  /**
   * Carga la auditoría de un análisis específico.
   * Contiene trazabilidad completa del análisis.
   */
  async function cargarAuditoria(analisisId: number) {
    cargandoAuditoria.value = true;

    try {
      auditoria.value = await obtenerAuditoria(analisisId);
    } catch (e) {
      console.warn('Error cargando auditoría:', e);
      auditoria.value = null;
    } finally {
      cargandoAuditoria.value = false;
    }
  }

  function limpiarResultado() {
    resultado.value = null;
    auditoria.value = null;
    error.value = null;
  }

  function cargarHistorial() {
    const saved = localStorage.getItem('historial_analisis');
    if (saved) {
      try {
        historial.value = JSON.parse(saved);
      } catch {
        historial.value = [];
      }
    }
  }

  function cargarResultadoHistorial(id: string) {
    const found = historial.value.find((r) => r.id === id);
    if (found) {
      resultado.value = found;
    }
  }

  return {
    resultado,
    historial,
    auditoria,
    cargando,
    cargandoHistorial,
    cargandoAuditoria,
    error,
    modoAnalisis,
    tieneResultado,
    clasificacion,
    triggers,
    alertas,
    alertasPorSeveridad,
    conteoAlertas,
    informe,
    analizarProyecto,
    cargarUltimoAnalisis,
    cargarHistorialDesdeServidor,
    cargarAuditoria,
    limpiarResultado,
    cargarHistorial,
    cargarResultadoHistorial,
  };
});
