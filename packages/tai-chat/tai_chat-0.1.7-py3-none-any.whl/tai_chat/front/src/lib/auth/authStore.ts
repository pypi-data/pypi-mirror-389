/**
 * Store de Svelte para el estado global de autenticación
 */

import { writable, derived, get } from 'svelte/store';
import type { AuthState, User, AuthError, AuthSession } from './types';
import { TokenManager } from './TokenManager';

interface AuthStoreState {
  state: AuthState;
  user: User | null;
  token: string | null;
  sessionId: string | null;
  error: AuthError | null;
  isLoading: boolean;
}

const initialState: AuthStoreState = {
  state: 'loading',
  user: null,
  token: null,
  sessionId: null,
  error: null,
  isLoading: true
};

// Store principal de autenticación
const authStore = writable<AuthStoreState>(initialState);

// Instancia del TokenManager
const tokenManager = TokenManager.getInstance();

// Callback para limpiar datos cuando el usuario se desautentica
let onUnauthenticatedCallback: (() => void) | undefined;

export const auth = {
  // Suscripción al store
  subscribe: authStore.subscribe,

  /**
   * Inicializa el estado de autenticación desde localStorage
   */
  init(): void {
    const storedSession = tokenManager.getStoredSession();
    
    if (storedSession && !tokenManager.isTokenExpired(storedSession.token)) {
      // Restaurar sesión válida
      authStore.update(state => ({
        ...state,
        state: 'authenticated',
        user: storedSession.user,
        token: storedSession.token,
        sessionId: storedSession.sessionId,
        error: null,
        isLoading: false
      }));
    } else {
      // No hay sesión válida
      tokenManager.clearSession();
      authStore.update(state => ({
        ...state,
        state: 'unauthenticated',
        user: null,
        token: null,
        sessionId: null,
        error: null,
        isLoading: false
      }));
    }

    // Configurar listener para cambios entre pestañas
    tokenManager.onStorageChange((session) => {
      if (session && !tokenManager.isTokenExpired(session.token)) {
        // Otra pestaña inició sesión
        authStore.update(state => ({
          ...state,
          state: 'authenticated',
          user: session.user,
          token: session.token,
          sessionId: session.sessionId,
          error: null,
          isLoading: false
        }));
      } else {
        // Otra pestaña cerró sesión
        authStore.update(state => ({
          ...state,
          state: 'unauthenticated',
          user: null,
          token: null,
          sessionId: null,
          error: null,
          isLoading: false
        }));
        
        // Limpiar datos relacionados con el usuario
        onUnauthenticatedCallback?.();
      }
    });
  },

  /**
   * Establece el estado de autenticación exitosa
   */
  setAuthenticated(session: AuthSession): void {
    tokenManager.storeSession(session);
    
    authStore.update(state => ({
      ...state,
      state: 'authenticated',
      user: session.user,
      token: session.token,
      sessionId: session.sessionId,
      error: null,
      isLoading: false
    }));
  },

  /**
   * Establece el estado de no autenticado
   */
  setUnauthenticated(error?: AuthError): void {
    tokenManager.clearSession();
    
    authStore.update(state => ({
      ...state,
      state: 'unauthenticated',
      user: null,
      token: null,
      sessionId: null,
      error: error || null,
      isLoading: false
    }));

    // Limpiar datos relacionados con el usuario
    onUnauthenticatedCallback?.();
  },

  /**
   * Establece el estado de sesión invalidada
   */
  setSessionInvalidated(error: AuthError): void {
    tokenManager.clearSession();
    
    authStore.update(state => ({
      ...state,
      state: 'session_invalidated',
      user: null,
      token: null,
      sessionId: null,
      error,
      isLoading: false
    }));

    // Limpiar datos relacionados con el usuario
    onUnauthenticatedCallback?.();
  },

  /**
   * Establece el estado de sesión expirada
   */
  setSessionExpired(error: AuthError): void {
    tokenManager.clearSession();
    
    authStore.update(state => ({
      ...state,
      state: 'session_expired',
      user: null,
      token: null,
      sessionId: null,
      error,
      isLoading: false
    }));

    // Limpiar datos relacionados con el usuario
    onUnauthenticatedCallback?.();
  },

  /**
   * Establece el estado de carga
   */
  setLoading(isLoading: boolean): void {
    authStore.update(state => ({
      ...state,
      isLoading
    }));
  },

  /**
   * Limpia errores
   */
  clearError(): void {
    authStore.update(state => ({
      ...state,
      error: null
    }));
  },

  /**
   * Obtiene el estado actual de forma síncrona
   */
  getState(): AuthStoreState {
    return get(authStore);
  },

  /**
   * Verifica si el usuario está autenticado
   */
  isAuthenticated(): boolean {
    const state = get(authStore);
    return state.state === 'authenticated' && !!state.token;
  },

  /**
   * Obtiene el token actual
   */
  getToken(): string | null {
    const state = get(authStore);
    return state.token;
  },

  /**
   * Obtiene el usuario actual
   */
  getUser(): User | null {
    const state = get(authStore);
    return state.user;
  },

  /**
   * Registra un callback que se ejecutará cuando el usuario se desautentique
   */
  onUnauthenticated(callback: () => void): void {
    onUnauthenticatedCallback = callback;
  }
};

// Stores derivados para uso conveniente en componentes
export const isAuthenticated = derived(
  authStore,
  ($auth) => $auth.state === 'authenticated'
);

export const isLoading = derived(
  authStore,
  ($auth) => $auth.isLoading
);

export const currentUser = derived(
  authStore,
  ($auth) => $auth.user
);

export const authError = derived(
  authStore,
  ($auth) => $auth.error
);

export const authState = derived(
  authStore,
  ($auth) => $auth.state
);

// Inicializar el store cuando se importa
if (typeof window !== 'undefined') {
  auth.init();
}
