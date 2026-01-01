import { post } from './api';
import type { BusquedaNormativaRequest, BusquedaNormativaResponse } from '@/types';

export async function buscarNormativa(
  request: BusquedaNormativaRequest
): Promise<BusquedaNormativaResponse> {
  return post<BusquedaNormativaResponse>('/legal/buscar', request);
}

export async function obtenerArticulo(
  documento: string,
  articulo: string
): Promise<{ contenido: string; contexto: string }> {
  return post<{ contenido: string; contexto: string }>('/legal/articulo', {
    documento,
    articulo,
  });
}
