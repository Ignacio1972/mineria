import type { DatosProyecto, GeometriaGeoJSON } from './project';
import type { ResultadoAnalisis } from './analysis';

export interface ApiError {
  detail: string;
  status_code?: number;
}

export interface ApiResponse<T> {
  data: T | null;
  error: ApiError | null;
  loading: boolean;
}

export interface AnalisisRequest {
  proyecto: DatosProyecto;
  geometria: GeometriaGeoJSON;
  generar_informe_llm?: boolean;
  secciones_informe?: string[];
}

export interface AnalisisRapidoRequest {
  proyecto: DatosProyecto;
  geometria: GeometriaGeoJSON;
}

export interface ExportarRequest {
  resultado: ResultadoAnalisis;
  formato: 'pdf' | 'docx' | 'txt' | 'html';
}

export interface BusquedaNormativaRequest {
  query: string;
  filtros?: {
    tipo_documento?: string[];
    temas?: string[];
  };
  limite?: number;
}

export interface BusquedaNormativaResponse {
  resultados: Array<{
    documento: string;
    seccion: string;
    contenido: string;
    relevancia: number;
  }>;
  total: number;
}

export interface HealthCheckResponse {
  status: 'ok' | 'degraded' | 'error';
  services: {
    database: boolean;
    gis: boolean;
    rag: boolean;
    llm: boolean;
  };
}

export type FormatoExportacion = 'pdf' | 'docx' | 'txt' | 'html';

export const FORMATOS_EXPORTACION: Array<{
  valor: FormatoExportacion;
  nombre: string;
  icono: string;
}> = [
  { valor: 'pdf', nombre: 'PDF', icono: 'file-pdf' },
  { valor: 'docx', nombre: 'Word', icono: 'file-word' },
  { valor: 'txt', nombre: 'Texto', icono: 'file-text' },
  { valor: 'html', nombre: 'HTML', icono: 'file-code' },
];
