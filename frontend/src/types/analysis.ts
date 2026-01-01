export type Severidad = 'CRITICA' | 'ALTA' | 'MEDIA' | 'BAJA' | 'INFO';
export type NivelConfianza = 'MUY_ALTA' | 'ALTA' | 'MEDIA' | 'BAJA';
export type ViaIngreso = 'EIA' | 'DIA';
export type LetraTrigger = 'a' | 'b' | 'c' | 'd' | 'e' | 'f';

export interface Trigger {
  letra: LetraTrigger;
  descripcion: string;
  detalle: string;
  severidad: Severidad;
  fundamento_legal: string;
  peso: number;
}

export interface Alerta {
  id: string;
  nivel: Severidad;
  categoria: string;
  titulo: string;
  descripcion: string;
  acciones_requeridas: string[];
}

export interface ClasificacionSEIA {
  via_ingreso_recomendada: ViaIngreso;
  confianza: number;
  nivel_confianza: NivelConfianza;
  justificacion: string;
  puntaje_matriz: number;
}

export interface InterseccionGIS {
  capa: string;
  nombre_elemento?: string;
  porcentaje_interseccion?: number;
  area_afectada_ha?: number;
  distancia_metros?: number;
  dentro: boolean;
}

export interface ResultadoGIS {
  intersecciones: InterseccionGIS[];
  alertas_gis: string[];
  area_proyecto_ha: number;
  centroide: [number, number];
}

export interface SeccionInforme {
  titulo: string;
  contenido: string;
  orden: number;
}

export interface Informe {
  secciones: SeccionInforme[];
  texto_completo: string;
  fecha_generacion: string;
}

export interface NormativaCitada {
  nombre: string;
  articulo?: string;
  relevancia: number;
  extracto: string;
}

export interface Metricas {
  tiempo_analisis_segundos: number;
  tiempo_gis_ms: number;
  tiempo_rag_ms: number;
  tiempo_llm_ms?: number;
  tokens_utilizados?: number;
}

// Tipos para Auditoría de Análisis
export interface CapaGISUsada {
  nombre: string;
  fecha: string;
  version?: string;
  elementos_encontrados: number;
}

export interface NormativaAuditoria {
  tipo: string;
  numero: string;
  articulo?: string;
  letra?: string;
  descripcion?: string;
}

export interface AuditoriaAnalisis {
  id: string;
  analisis_id: number;
  capas_gis_usadas: CapaGISUsada[];
  documentos_referenciados: string[];
  normativa_citada: NormativaAuditoria[];
  checksum_datos_entrada: string;
  version_modelo_llm?: string;
  version_sistema?: string;
  tiempo_gis_ms?: number;
  tiempo_rag_ms?: number;
  tiempo_llm_ms?: number;
  tokens_usados?: number;
  created_at: string;
}

export interface ResultadoAnalisis {
  id: string;
  fecha_analisis: string;
  proyecto: import('./project').DatosProyecto;
  geometria: import('./project').GeometriaGeoJSON;
  resultado_gis: ResultadoGIS;
  clasificacion_seia: ClasificacionSEIA;
  triggers: Trigger[];
  alertas: Alerta[];
  normativa_citada: NormativaCitada[];
  informe?: Informe;
  metricas: Metricas;
}

export const SEVERIDAD_COLORES: Record<Severidad, string> = {
  CRITICA: 'error',
  ALTA: 'warning',
  MEDIA: 'info',
  BAJA: 'success',
  INFO: 'neutral',
};

export const SEVERIDAD_ORDEN: Record<Severidad, number> = {
  CRITICA: 0,
  ALTA: 1,
  MEDIA: 2,
  BAJA: 3,
  INFO: 4,
};
