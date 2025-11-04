<script lang="ts">
  import { authService } from '../auth';

  interface Props {
    onLoginSuccess?: () => void;
  }

  let { onLoginSuccess }: Props = $props();

  let username = $state('');
  let pwd = $state('');
  let isLoading = $state(false);
  let error = $state('');
  let fieldErrors = $state({
    username: '',
    password: ''
  });

  function clearForm() {
    username = '';
    pwd = '';
    fieldErrors = {
      username: '',
      password: ''
    };
  }

  function validateForm() {
    let hasErrors = false;

    if (!username.trim()) {
      fieldErrors.username = 'El nombre de usuario es obligatorio';
      hasErrors = true;
    }

    if (!pwd) {
      fieldErrors.password = 'La contraseña es obligatoria';
      hasErrors = true;
    } else if (pwd.length < 0) {
      fieldErrors.password = 'La contraseña debe tener al menos 6 caracteres';
      hasErrors = true;
    }

    return hasErrors ? 'Error' : null;
  }

  async function handleSubmit(event: Event) {
    event.preventDefault();
    error = '';
    const validationError = validateForm();
    
    if (validationError) {
      error = validationError;
      return;
    }

    isLoading = true;

    try {
      const response = await authService.login({ username, pwd });
      // The authService now handles updating the store automatically
      onLoginSuccess?.();
    } catch (err) {
      error = err instanceof Error ? err.message : 'Ha ocurrido un error';
    } finally {
      isLoading = false;
    }
  }

  function handleKeyDown(event: KeyboardEvent) {
    if (event.key === 'Enter' && !isLoading) {
      handleSubmit(event);
    }
  }
</script>

<div class="min-h-screen flex items-center justify-center bg-background px-4">
  <div class="max-w-md w-full space-y-8">
    <!-- Logo/Title -->
    <div class="text-center">
      <h1 class="text-3xl font-bold text-primary mb-2">TAI Chat</h1>
      <p class="text-text-secondary">
        Inicia sesión en tu cuenta
      </p>
    </div>

    <!-- Form -->
    <div class="bg-surface rounded-lg shadow-lg p-6 border border-border">
      <form onsubmit={handleSubmit} class="space-y-4">
        <!-- Username -->
        <div>
          <label for="username" class="block text-sm font-medium text-text mb-1">
            Nombre de usuario
          </label>
          <input
            id="username"
            type="text"
            bind:value={username}
            onkeydown={handleKeyDown}
            class="w-full px-3 py-2 border {fieldErrors.username ? 'border-error' : 'border-border'} rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent bg-background text-text"
            placeholder="Ingresa tu nombre de usuario"
            disabled={isLoading}
          />
          {#if fieldErrors.username}
            <p class="text-error text-sm mt-1">{fieldErrors.username}</p>
          {/if}
        </div>

        <!-- Password -->
        <div>
          <label for="password" class="block text-sm font-medium text-text mb-1">
            Contraseña
          </label>
          <input
            id="password"
            type="password"
            bind:value={pwd}
            onkeydown={handleKeyDown}
            class="w-full px-3 py-2 border {fieldErrors.password ? 'border-error' : 'border-border'} rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent bg-background text-text"
            placeholder="••••••••"
            disabled={isLoading}
          />
          {#if fieldErrors.password}
            <p class="text-error text-sm mt-1">{fieldErrors.password}</p>
          {/if}
        </div>

        <!-- Error message -->
        {#if error}
          <div class="text-red-700 text-sm bg-red-50 border border-red-200 rounded-md p-3">
            <div class="flex items-start">
              <svg class="w-4 h-4 text-red-500 mt-0.5 mr-2 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
              </svg>
              <span>{error}</span>
            </div>
          </div>
        {/if}

        <!-- Submit button -->
        <button
          type="submit"
          disabled={isLoading}
          class="w-full bg-primary text-white py-2 px-4 rounded-md hover:bg-opacity-90 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
        >
          {#if isLoading}
            <span class="flex items-center justify-center">
              <svg class="animate-spin -ml-1 mr-3 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Procesando...
            </span>
          {:else}
            Iniciar Sesión
          {/if}
        </button>
      </form>
    </div>
  </div>
</div>
