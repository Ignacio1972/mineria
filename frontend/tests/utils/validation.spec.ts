import { describe, it, expect } from 'vitest';
import {
  validarProyecto,
  esProyectoValido,
  validarEmail,
  validarCoordenadas,
  validarCoordenadasChile,
} from '@/utils/validation';

describe('validarProyecto', () => {
  it('retorna error si nombre está vacío', () => {
    const errores = validarProyecto({ nombre: '' });
    expect(errores.some((e) => e.campo === 'nombre')).toBe(true);
  });

  it('retorna error si nombre tiene menos de 3 caracteres', () => {
    const errores = validarProyecto({ nombre: 'AB' });
    expect(errores.some((e) => e.campo === 'nombre')).toBe(true);
  });

  it('no retorna error si nombre es válido', () => {
    const errores = validarProyecto({ nombre: 'Proyecto Minero Los Andes' });
    expect(errores.some((e) => e.campo === 'nombre')).toBe(false);
  });

  it('retorna error si superficie es negativa', () => {
    const errores = validarProyecto({ nombre: 'Test', superficie_ha: -10 });
    expect(errores.some((e) => e.campo === 'superficie_ha')).toBe(true);
  });

  it('no retorna error si superficie es positiva', () => {
    const errores = validarProyecto({ nombre: 'Test', superficie_ha: 100 });
    expect(errores.some((e) => e.campo === 'superficie_ha')).toBe(false);
  });

  it('retorna error si inversión es negativa', () => {
    const errores = validarProyecto({ nombre: 'Test', inversion_musd: -5 });
    expect(errores.some((e) => e.campo === 'inversion_musd')).toBe(true);
  });
});

describe('esProyectoValido', () => {
  it('retorna false para proyecto inválido', () => {
    expect(esProyectoValido({ nombre: '' })).toBe(false);
  });

  it('retorna true para proyecto válido', () => {
    expect(esProyectoValido({ nombre: 'Proyecto Válido' })).toBe(true);
  });
});

describe('validarEmail', () => {
  it('valida emails correctos', () => {
    expect(validarEmail('test@example.com')).toBe(true);
    expect(validarEmail('user.name@domain.cl')).toBe(true);
  });

  it('rechaza emails inválidos', () => {
    expect(validarEmail('invalid')).toBe(false);
    expect(validarEmail('invalid@')).toBe(false);
    expect(validarEmail('@domain.com')).toBe(false);
  });
});


describe('validarCoordenadas', () => {
  it('acepta coordenadas válidas', () => {
    expect(validarCoordenadas(-70.6, -33.4)).toBe(true);
    expect(validarCoordenadas(0, 0)).toBe(true);
    expect(validarCoordenadas(-180, -90)).toBe(true);
    expect(validarCoordenadas(180, 90)).toBe(true);
  });

  it('rechaza coordenadas fuera de rango', () => {
    expect(validarCoordenadas(-181, 0)).toBe(false);
    expect(validarCoordenadas(0, 91)).toBe(false);
  });
});

describe('validarCoordenadasChile', () => {
  it('acepta coordenadas dentro de Chile', () => {
    expect(validarCoordenadasChile(-70.6, -33.4)).toBe(true); // Santiago
    expect(validarCoordenadasChile(-70.4, -23.6)).toBe(true); // Antofagasta
    expect(validarCoordenadasChile(-73.0, -40.0)).toBe(true); // Valdivia
  });

  it('rechaza coordenadas fuera de Chile', () => {
    expect(validarCoordenadasChile(-58.0, -34.0)).toBe(false); // Buenos Aires
    expect(validarCoordenadasChile(-77.0, -12.0)).toBe(false); // Lima
    expect(validarCoordenadasChile(0, 0)).toBe(false);
  });
});
