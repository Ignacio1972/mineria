import { describe, it, expect } from 'vitest';
import {
  formatearFecha,
  formatearFechaCorta,
  formatearNumero,
  formatearPorcentaje,
  formatearSuperficie,
  formatearMoneda,
  formatearCoordenadas,
  capitalizarPrimeraLetra,
  slugify,
} from '@/utils/format';

describe('formatearNumero', () => {
  it('formatea números correctamente para es-CL', () => {
    expect(formatearNumero(1000)).toContain('1');
    expect(formatearNumero(1000000)).toContain('1');
  });
});

describe('formatearPorcentaje', () => {
  it('formatea porcentajes correctamente', () => {
    expect(formatearPorcentaje(0.5)).toBe('50.0%');
    expect(formatearPorcentaje(0.123, 2)).toBe('12.30%');
    expect(formatearPorcentaje(1)).toBe('100.0%');
  });
});

describe('formatearSuperficie', () => {
  it('formatea hectáreas pequeñas', () => {
    expect(formatearSuperficie(100)).toContain('ha');
  });

  it('convierte a km² para superficies grandes', () => {
    expect(formatearSuperficie(10000)).toContain('km²');
  });
});

describe('formatearMoneda', () => {
  it('formatea millones de USD', () => {
    expect(formatearMoneda(500)).toContain('US$');
    expect(formatearMoneda(500)).toContain('M');
  });

  it('formatea miles de millones de USD', () => {
    expect(formatearMoneda(5000)).toContain('MM');
  });
});

describe('formatearCoordenadas', () => {
  it('formatea coordenadas con dirección', () => {
    const resultado = formatearCoordenadas(-70.6, -33.4);
    expect(resultado).toContain('S');
    expect(resultado).toContain('W');
    expect(resultado).toContain('33.4');
    expect(resultado).toContain('70.6');
  });

  it('usa N y E para coordenadas positivas', () => {
    const resultado = formatearCoordenadas(10, 20);
    expect(resultado).toContain('N');
    expect(resultado).toContain('E');
  });
});

describe('capitalizarPrimeraLetra', () => {
  it('capitaliza la primera letra', () => {
    expect(capitalizarPrimeraLetra('hola')).toBe('Hola');
    expect(capitalizarPrimeraLetra('MUNDO')).toBe('Mundo');
  });

  it('maneja strings vacíos', () => {
    expect(capitalizarPrimeraLetra('')).toBe('');
  });
});

describe('slugify', () => {
  it('convierte texto a slug', () => {
    expect(slugify('Proyecto Minero')).toBe('proyecto-minero');
    expect(slugify('Área Protegida')).toBe('area-protegida');
  });

  it('elimina caracteres especiales', () => {
    expect(slugify('Test!@#$%')).toBe('test');
  });

  it('maneja múltiples espacios', () => {
    expect(slugify('Muchos   Espacios')).toBe('muchos-espacios');
  });
});

describe('formatearFecha', () => {
  it('formatea fechas correctamente', () => {
    const fecha = new Date('2024-01-15');
    const resultado = formatearFecha(fecha);
    expect(resultado).toContain('2024');
    expect(resultado).toContain('15');
  });

  it('acepta strings de fecha', () => {
    const resultado = formatearFecha('2024-06-20');
    expect(resultado).toContain('2024');
  });
});

describe('formatearFechaCorta', () => {
  it('formatea fecha en formato corto', () => {
    const resultado = formatearFechaCorta('2024-01-15');
    expect(resultado).toMatch(/\d/);
  });
});
