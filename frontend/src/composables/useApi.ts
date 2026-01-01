import { ref, type Ref } from 'vue';
import type { ApiError } from '@/types';

interface UseApiOptions<T> {
  immediate?: boolean;
  onSuccess?: (data: T) => void;
  onError?: (error: ApiError) => void;
}

interface UseApiReturn<T, P extends unknown[]> {
  data: Ref<T | null>;
  error: Ref<ApiError | null>;
  loading: Ref<boolean>;
  execute: (...params: P) => Promise<T | null>;
  reset: () => void;
}

export function useApi<T, P extends unknown[] = []>(
  fn: (...params: P) => Promise<T>,
  options: UseApiOptions<T> = {}
): UseApiReturn<T, P> {
  const data = ref<T | null>(null) as Ref<T | null>;
  const error = ref<ApiError | null>(null);
  const loading = ref(false);

  async function execute(...params: P): Promise<T | null> {
    loading.value = true;
    error.value = null;

    try {
      const result = await fn(...params);
      data.value = result;
      options.onSuccess?.(result);
      return result;
    } catch (e) {
      const apiError: ApiError = {
        detail: e instanceof Error ? e.message : 'Error desconocido',
      };
      error.value = apiError;
      options.onError?.(apiError);
      return null;
    } finally {
      loading.value = false;
    }
  }

  function reset() {
    data.value = null;
    error.value = null;
    loading.value = false;
  }

  return {
    data,
    error,
    loading,
    execute,
    reset,
  };
}
