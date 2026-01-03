<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();
const password = ref('');
const error = ref(false);
const loading = ref(false);

// Password hardcodeado - cambiar aquí
const PASSWORD_CORRECTO = '4321';

const handleLogin = () => {
  loading.value = true;
  error.value = false;

  // Pequeño delay para feedback visual
  setTimeout(() => {
    if (password.value === PASSWORD_CORRECTO) {
      sessionStorage.setItem('auth', 'true');
      router.push('/');
    } else {
      error.value = true;
      password.value = '';
    }
    loading.value = false;
  }, 300);
};
</script>

<template>
  <div class="min-h-screen bg-base-200 flex items-center justify-center p-4">
    <div class="card w-full max-w-sm bg-base-100 shadow-xl">
      <div class="card-body">
        <h2 class="card-title justify-center text-2xl mb-2 text-center">
          Asistente para Estudios de Impacto Ambiental
        </h2>
        <p class="text-center text-base-content/60 text-sm mb-4">
          Ingrese la contraseña para continuar
        </p>

        <form @submit.prevent="handleLogin">
          <div class="form-control">
            <input
              v-model="password"
              type="password"
              placeholder="Contraseña"
              class="input input-bordered w-full"
              :class="{ 'input-error': error }"
              autofocus
              :disabled="loading"
            />
            <label v-if="error" class="label">
              <span class="label-text-alt text-error">Contraseña incorrecta</span>
            </label>
          </div>

          <div class="form-control mt-4">
            <button
              type="submit"
              class="btn btn-primary w-full"
              :disabled="loading || !password"
            >
              <span v-if="loading" class="loading loading-spinner loading-sm"></span>
              <span v-else>Entrar</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>
