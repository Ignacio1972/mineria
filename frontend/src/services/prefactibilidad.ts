import { post, get, downloadFile } from './api';
import type {
  AnalisisRequest,
  AnalisisRapidoRequest,
  FormatoExportacion,
} from '@/types';
import type { ResultadoAnalisis, AuditoriaAnalisis } from '@/types';

export async function ejecutarAnalisis(
  request: AnalisisRequest
): Promise<ResultadoAnalisis> {
  return post<ResultadoAnalisis>('/prefactibilidad/analisis', request);
}

export async function ejecutarAnalisisRapido(
  request: AnalisisRapidoRequest
): Promise<ResultadoAnalisis> {
  return post<ResultadoAnalisis>('/prefactibilidad/analisis-rapido', request);
}

/**
 * Ejecuta análisis integrado con persistencia en BD.
 * Este es el método preferido ya que guarda los resultados.
 */
export async function ejecutarAnalisisIntegrado(
  proyectoId: number,
  tipo: 'rapido' | 'completo' = 'rapido',
  secciones?: string[]
): Promise<ResultadoAnalisis> {
  await post<{
    analisis_id: number;
    proyecto_id: number;
    fecha_analisis: string;
    tipo_analisis: string;
    via_ingreso_recomendada: string;
    confianza: number;
    nivel_confianza: string;
    justificacion: string;
    triggers_detectados: number;
    alertas_criticas: number;
    alertas_altas: number;
    alertas_totales: number;
    estado_proyecto: string;
    metricas: {
      tiempo_gis_ms: number;
      tiempo_rag_ms: number;
      tiempo_llm_ms: number;
      tiempo_total_ms: number;
      tokens_usados: number;
    };
    informe: Record<string, unknown> | null;
  }>('/prefactibilidad/analisis-integrado', {
    proyecto_id: proyectoId,
    tipo,
    secciones,
  });

  // Obtener el análisis completo recién creado
  return obtenerUltimoAnalisis(proyectoId);
}

/**
 * Obtiene el último análisis de un proyecto desde la BD.
 */
export async function obtenerUltimoAnalisis(
  proyectoId: number
): Promise<ResultadoAnalisis> {
  return get<ResultadoAnalisis>(`/prefactibilidad/proyecto/${proyectoId}/ultimo-analisis`);
}

/**
 * Obtiene el historial de análisis de un proyecto.
 */
export async function obtenerHistorialAnalisis(
  proyectoId: number
): Promise<Array<{
  id: number;
  fecha_analisis: string;
  tipo_analisis: string;
  via_ingreso_recomendada: string;
  confianza: number;
  triggers_count: number;
  tiempo_procesamiento_ms: number;
  tiene_informe: boolean;
}>> {
  return get(`/prefactibilidad/proyecto/${proyectoId}/historial-analisis`);
}

export async function exportarInforme(
  resultado: ResultadoAnalisis,
  formato: FormatoExportacion
): Promise<void> {
  const filename = `informe_${resultado.proyecto.nombre.replace(/\s+/g, '_')}_${Date.now()}.${formato}`;
  await downloadFile(
    `/prefactibilidad/exportar/${formato}`,
    { resultado },
    filename
  );
}

export async function obtenerSeccionesDisponibles(): Promise<string[]> {
  const response = await post<{ secciones: string[] }>(
    '/prefactibilidad/secciones-disponibles'
  );
  return response.secciones;
}

export async function obtenerMatrizDecision(): Promise<Record<string, number>> {
  return post<Record<string, number>>('/prefactibilidad/matriz-decision');
}

/**
 * Obtiene la auditoría de un análisis específico.
 * Contiene trazabilidad completa: capas GIS, normativa citada, métricas, etc.
 */
export async function obtenerAuditoria(
  analisisId: number
): Promise<AuditoriaAnalisis> {
  return get<AuditoriaAnalisis>(`/prefactibilidad/analisis/${analisisId}/auditoria`);
}
