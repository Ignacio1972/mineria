export function formatearFecha(fecha: string | Date): string {
  const date = typeof fecha === 'string' ? new Date(fecha) : fecha;
  return date.toLocaleDateString('es-CL', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });
}

export function formatearFechaCorta(fecha: string | Date): string {
  const date = typeof fecha === 'string' ? new Date(fecha) : fecha;
  return date.toLocaleDateString('es-CL');
}

export function formatearNumero(num: number): string {
  return num.toLocaleString('es-CL');
}

export function formatearPorcentaje(num: number, decimales = 1): string {
  return `${(num * 100).toFixed(decimales)}%`;
}

export function formatearSuperficie(hectareas: number): string {
  if (hectareas >= 1000) {
    return `${formatearNumero(hectareas / 100)} km²`;
  }
  return `${formatearNumero(hectareas)} ha`;
}

export function formatearMoneda(musd: number): string {
  if (musd >= 1000) {
    return `US$ ${formatearNumero(musd / 1000)} MM`;
  }
  return `US$ ${formatearNumero(musd)} M`;
}

export function formatearCoordenadas(lon: number, lat: number): string {
  const lonDir = lon >= 0 ? 'E' : 'W';
  const latDir = lat >= 0 ? 'N' : 'S';
  return `${Math.abs(lat).toFixed(4)}° ${latDir}, ${Math.abs(lon).toFixed(4)}° ${lonDir}`;
}

export function capitalizarPrimeraLetra(texto: string): string {
  if (!texto) return '';
  return texto.charAt(0).toUpperCase() + texto.slice(1).toLowerCase();
}

export function slugify(texto: string): string {
  return texto
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
}
