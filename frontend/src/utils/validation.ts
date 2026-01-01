import type { DatosProyecto } from '@/types';

export interface ErrorValidacion {
  campo: string;
  mensaje: string;
}

export function validarProyecto(datos: Partial<DatosProyecto>): ErrorValidacion[] {
  const errores: ErrorValidacion[] = [];

  if (!datos.nombre || datos.nombre.trim().length < 3) {
    errores.push({
      campo: 'nombre',
      mensaje: 'El nombre del proyecto debe tener al menos 3 caracteres',
    });
  }

  if (datos.nombre && datos.nombre.length > 200) {
    errores.push({
      campo: 'nombre',
      mensaje: 'El nombre del proyecto no puede exceder 200 caracteres',
    });
  }

  if (datos.superficie_ha != null && datos.superficie_ha < 0) {
    errores.push({
      campo: 'superficie_ha',
      mensaje: 'La superficie no puede ser negativa',
    });
  }

  if (datos.vida_util_anos != null && datos.vida_util_anos < 0) {
    errores.push({
      campo: 'vida_util_anos',
      mensaje: 'La vida útil no puede ser negativa',
    });
  }

  if (datos.uso_agua_lps != null && datos.uso_agua_lps < 0) {
    errores.push({
      campo: 'uso_agua_lps',
      mensaje: 'El uso de agua no puede ser negativo',
    });
  }

  if (datos.energia_mw != null && datos.energia_mw < 0) {
    errores.push({
      campo: 'energia_mw',
      mensaje: 'La energía no puede ser negativa',
    });
  }

  if (datos.trabajadores_construccion != null && datos.trabajadores_construccion < 0) {
    errores.push({
      campo: 'trabajadores_construccion',
      mensaje: 'El número de trabajadores no puede ser negativo',
    });
  }

  if (datos.trabajadores_operacion != null && datos.trabajadores_operacion < 0) {
    errores.push({
      campo: 'trabajadores_operacion',
      mensaje: 'El número de trabajadores no puede ser negativo',
    });
  }

  if (datos.inversion_musd != null && datos.inversion_musd < 0) {
    errores.push({
      campo: 'inversion_musd',
      mensaje: 'La inversión no puede ser negativa',
    });
  }

  return errores;
}

export function esProyectoValido(datos: Partial<DatosProyecto>): boolean {
  return validarProyecto(datos).length === 0;
}

export function validarEmail(email: string): boolean {
  const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return regex.test(email);
}

export function validarCoordenadas(lon: number, lat: number): boolean {
  return lon >= -180 && lon <= 180 && lat >= -90 && lat <= 90;
}

export function validarCoordenadasChile(lon: number, lat: number): boolean {
  // Límites aproximados de Chile continental
  return lon >= -76 && lon <= -66 && lat >= -56 && lat <= -17;
}
