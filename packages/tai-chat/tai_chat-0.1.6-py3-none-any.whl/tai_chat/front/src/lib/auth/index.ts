/**
 * Módulo de autenticación - Exportaciones principales
 */

// Servicios
export { authService } from './AuthService';
export { TokenManager } from './TokenManager';

// Stores
export { 
  auth, 
  isAuthenticated, 
  isLoading, 
  currentUser, 
  authError, 
  authState 
} from './authStore';

// Tipos
export type {
  User,
  LoginRequest,
  LoginResponse,
  AuthState,
  AuthError,
  AuthSession,
  TokenPayload,
  AuthErrorCode
} from './types';

export { AUTH_ERROR_CODES, AUTH_ERROR_MESSAGES } from './types';

// Inicialización automática del servicio de autenticación
if (typeof window !== 'undefined') {
  import('./AuthService').then(({ authService }) => {
    authService.initialize().catch(console.error);
  });
}
