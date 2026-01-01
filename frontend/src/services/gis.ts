import { get, post } from './api';
import type { GeometriaGeoJSON, DatosProyecto } from '@/types';
import type { ResultadoGIS, CapasGISResponse, FeatureCollection } from '@/types';

export async function obtenerCapasGIS(): Promise<CapasGISResponse> {
  return get<CapasGISResponse>('/gis/capas');
}

export async function obtenerCapaGeoJSON(
  capa: string,
  bbox?: string,
  limit?: number
): Promise<FeatureCollection> {
  const params = new URLSearchParams();
  if (bbox) params.set('bbox', bbox);
  if (limit) params.set('limit', limit.toString());

  const queryString = params.toString();
  const url = `/gis/capas/${capa}/geojson${queryString ? `?${queryString}` : ''}`;

  return get<FeatureCollection>(url);
}

export async function analizarEspacial(
  geometria: GeometriaGeoJSON,
  proyecto?: Partial<DatosProyecto>
): Promise<ResultadoGIS> {
  return post<ResultadoGIS>('/gis/analisis-espacial', {
    geometria,
    proyecto,
  });
}

export async function validarGeometria(
  geometria: GeometriaGeoJSON
): Promise<{ valido: boolean; errores: string[] }> {
  return post<{ valido: boolean; errores: string[] }>('/gis/validar-geometria', {
    geometria,
  });
}

export async function calcularArea(
  geometria: GeometriaGeoJSON
): Promise<{ area_ha: number; perimetro_km: number }> {
  return post<{ area_ha: number; perimetro_km: number }>('/gis/calcular-area', {
    geometria,
  });
}
