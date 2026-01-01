import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useApi } from '@/composables/useApi';

describe('useApi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('estado inicial', () => {
    it('comienza con valores por defecto', () => {
      const { data, error, loading } = useApi(async () => 'test');

      expect(data.value).toBeNull();
      expect(error.value).toBeNull();
      expect(loading.value).toBe(false);
    });
  });

  describe('execute', () => {
    it('retorna datos de funcion exitosa', async () => {
      const mockFn = vi.fn().mockResolvedValue({ id: 1, nombre: 'Test' });
      const { execute, data } = useApi(mockFn);

      const result = await execute();

      expect(result).toEqual({ id: 1, nombre: 'Test' });
      expect(data.value).toEqual({ id: 1, nombre: 'Test' });
    });

    it('pasa parametros a la funcion', async () => {
      const mockFn = vi.fn().mockResolvedValue('ok');
      const { execute } = useApi(mockFn);

      await execute('param1', 123);

      expect(mockFn).toHaveBeenCalledWith('param1', 123);
    });

    it('establece loading durante ejecucion', async () => {
      let resolve: (value: string) => void;
      const mockFn = vi.fn().mockImplementation(
        () => new Promise((r) => { resolve = r; })
      );
      const { execute, loading } = useApi(mockFn);

      const promise = execute();
      expect(loading.value).toBe(true);

      resolve!('done');
      await promise;
      expect(loading.value).toBe(false);
    });

    it('maneja errores y establece error.value', async () => {
      const mockFn = vi.fn().mockRejectedValue(new Error('Fallo'));
      const { execute, data, error } = useApi(mockFn);

      const result = await execute();

      expect(result).toBeNull();
      expect(data.value).toBeNull();
      expect(error.value?.detail).toBe('Fallo');
    });

    it('limpia error previo al ejecutar nuevamente', async () => {
      const mockFn = vi.fn()
        .mockRejectedValueOnce(new Error('Error 1'))
        .mockResolvedValueOnce('Exito');
      const { execute, error } = useApi(mockFn);

      await execute();
      expect(error.value).not.toBeNull();

      await execute();
      expect(error.value).toBeNull();
    });
  });

  describe('callbacks', () => {
    it('llama onSuccess cuando la funcion tiene exito', async () => {
      const onSuccess = vi.fn();
      const mockFn = vi.fn().mockResolvedValue({ valor: 42 });
      const { execute } = useApi(mockFn, { onSuccess });

      await execute();

      expect(onSuccess).toHaveBeenCalledWith({ valor: 42 });
    });

    it('llama onError cuando la funcion falla', async () => {
      const onError = vi.fn();
      const mockFn = vi.fn().mockRejectedValue(new Error('Error test'));
      const { execute } = useApi(mockFn, { onError });

      await execute();

      expect(onError).toHaveBeenCalledWith(
        expect.objectContaining({ detail: 'Error test' })
      );
    });

    it('no llama onSuccess cuando hay error', async () => {
      const onSuccess = vi.fn();
      const mockFn = vi.fn().mockRejectedValue(new Error('Error'));
      const { execute } = useApi(mockFn, { onSuccess });

      await execute();

      expect(onSuccess).not.toHaveBeenCalled();
    });

    it('no llama onError cuando tiene exito', async () => {
      const onError = vi.fn();
      const mockFn = vi.fn().mockResolvedValue('ok');
      const { execute } = useApi(mockFn, { onError });

      await execute();

      expect(onError).not.toHaveBeenCalled();
    });
  });

  describe('reset', () => {
    it('limpia todos los estados', async () => {
      const mockFn = vi.fn().mockResolvedValue({ data: 'test' });
      const { execute, reset, data, loading, error } = useApi(mockFn);

      await execute();
      expect(data.value).not.toBeNull();

      reset();

      expect(data.value).toBeNull();
      expect(error.value).toBeNull();
      expect(loading.value).toBe(false);
    });

    it('reset limpia error despues de fallo', async () => {
      const mockFn = vi.fn().mockRejectedValue(new Error('Error'));
      const { execute, reset, error } = useApi(mockFn);

      await execute();
      expect(error.value).not.toBeNull();

      reset();
      expect(error.value).toBeNull();
    });
  });

  describe('tipado', () => {
    it('infiere tipos correctamente', async () => {
      interface Usuario { id: number; nombre: string; }
      const mockFn = vi.fn().mockResolvedValue({ id: 1, nombre: 'Test' });
      const { execute, data } = useApi<Usuario>(mockFn);

      await execute();

      // TypeScript deberia inferir que data.value es Usuario | null
      expect(data.value?.id).toBe(1);
      expect(data.value?.nombre).toBe('Test');
    });
  });
});
