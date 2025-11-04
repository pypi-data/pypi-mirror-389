/**
 * AuthService - Servicio centralizado para manejo de autenticación
 */

import type { LoginRequest, LoginResponse, User, AuthError } from './types';
import { AUTH_ERROR_CODES, AUTH_ERROR_MESSAGES } from './types';
import { TokenManager } from './TokenManager';
import { auth } from './authStore';
import { apiRequest } from '../services/api';

export class AuthService {
  private static instance: AuthService;
  private tokenManager: TokenManager;

  private constructor() {
    this.tokenManager = TokenManager.getInstance();
  }

  static getInstance(): AuthService {
    if (!AuthService.instance) {
      AuthService.instance = new AuthService();
    }
    return AuthService.instance;
  }

  /**
   * Inicializa el servicio de autenticación
   */
  async initialize(): Promise<void> {
    auth.init();
    
    // Si hay una sesión válida, verificar con el servidor
    if (this.isAuthenticated()) {
      try {
        await this.validateCurrentSession();
      } catch (error) {
        console.warn('Error al validar sesión inicial:', error);
        auth.setUnauthenticated();
      }
    }
  }

  /**
   * Realiza el login del usuario
   */
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    try {
      auth.setLoading(false);
      auth.clearError();

      const response = await apiRequest<LoginResponse>('/auth/login', {
        method: 'POST',
        body: JSON.stringify(credentials)
      });

      // Crear sesión usando el TokenManager y la respuesta del login
      const session = this.createSessionFromLoginResponse(response);
      // Si llegamos aquí, la contraseña es válida
      auth.setAuthenticated(session);
      return response;
    } catch (error: any) {
      // Si el error es de contraseña expirada, no lo mapeamos
      if (error.code === AUTH_ERROR_CODES.PASSWORD_EXPIRED) {
        throw error;
      }
      const authError = this.mapApiErrorToAuthError(error);
      auth.setUnauthenticated(authError);
      throw authError;
    } finally {
      auth.setLoading(false);
    }
  }

  /**
   * Realiza el logout del usuario
   */
  async logout(): Promise<void> {
    try {
      // Intentar notificar al servidor del logout
      const token = this.tokenManager.getToken();
      if (token) {
        try {
          await apiRequest('/auth/logout', {
            method: 'POST',
            headers: this.getAuthHeaders()
          });
        } catch (error) {
          // Ignorar errores del servidor en logout
          console.warn('Error al notificar logout al servidor:', error);
        }
      }
    } finally {
      // Siempre limpiar la sesión local (esto también limpiará los chats a través del callback)
      auth.setUnauthenticated();
    }
  }

  /**
   * Valida la sesión actual con el servidor
   */
  async validateCurrentSession(): Promise<User> {
    try {
      const user = await apiRequest<User>('/auth/me', {
        method: 'GET',
        headers: this.getAuthHeaders()
      });

      // Actualizar información del usuario en el store
      const currentSession = this.tokenManager.getStoredSession();
      if (currentSession) {
        const updatedSession = {
          ...currentSession,
          user // Este user ahora incluye password_expiration
        };
        auth.setAuthenticated(updatedSession);
      }

      return user;
    } catch (error: any) {
      const authError = this.mapApiErrorToAuthError(error);
      this.handleAuthError(authError);
      throw authError;
    }
  }

  /**
   * Obtiene el usuario currente
   */
  getCurrentUser(): User | null {
    return auth.getUser();
  }

  /**
   * Verifica si el usuario está autenticado
   */
  isAuthenticated(): boolean {
    return auth.isAuthenticated();
  }

  /**
   * Obtiene el token actual
   */
  getToken(): string | null {
    return this.tokenManager.getToken();
  }

  /**
   * Obtiene los headers de autorización
   */
  getAuthHeaders(): { Authorization: string } | {} {
    const token = this.tokenManager.getToken();
    return token ? { Authorization: `Bearer ${token}` } : {};
  }

  /**
   * Maneja errores de autenticación automáticamente
   */
  handleAuthError(error: AuthError): void {
    switch (error.code) {
      case AUTH_ERROR_CODES.SESSION_INVALIDATED:
      case AUTH_ERROR_CODES.CONCURRENT_SESSION_DETECTED:
        auth.setSessionInvalidated(error);
        break;

      case AUTH_ERROR_CODES.SESSION_EXPIRED:
      case AUTH_ERROR_CODES.TOKEN_EXPIRED:
        auth.setSessionExpired(error);
        break;

      case AUTH_ERROR_CODES.INVALID_TOKEN:
      case AUTH_ERROR_CODES.UNAUTHORIZED_ACCESS:
        auth.setUnauthenticated(error);
        break;

      default:
        auth.setUnauthenticated(error);
        break;
    }
  }

  /**
   * Crea una sesión a partir de la respuesta de login
   */
  private createSessionFromLoginResponse(loginResponse: LoginResponse): any {
    const payload = this.tokenManager.decodeTokenPayload(loginResponse.access_token);
    const expiresAt = payload?.exp ? payload.exp * 1000 : Date.now() + (24 * 60 * 60 * 1000); // 24h por defecto

    return {
      token: loginResponse.access_token,
      user: loginResponse.user,
      sessionId: loginResponse.session_id || payload?.session_id || '',
      expiresAt
    };
  }

  /**
   * Mapea errores de la API a errores de autenticación
   */
  private mapApiErrorToAuthError(error: any): AuthError {
    if (error?.data?.errors?.[0]) {
      const apiError = error.data.errors[0];
      const code = apiError.code as keyof typeof AUTH_ERROR_CODES;
      
      if (AUTH_ERROR_CODES[code]) {
        return {
          code: AUTH_ERROR_CODES[code],
          message: AUTH_ERROR_MESSAGES[AUTH_ERROR_CODES[code]] || apiError.message,
          details: apiError.details
        };
      }
    }

    // Detectar errores HTTP específicos
    if (error?.message) {
      const message = error.message.toLowerCase();
      
      // HTTP 401 = credenciales inválidas
      if (message.includes('401') || message.includes('unauthorized')) {
        return {
          code: AUTH_ERROR_CODES.INVALID_CREDENTIALS,
          message: AUTH_ERROR_MESSAGES[AUTH_ERROR_CODES.INVALID_CREDENTIALS],
          details: error
        };
      }
      
      // HTTP 403 = acceso no autorizado
      if (message.includes('403') || message.includes('forbidden')) {
        return {
          code: AUTH_ERROR_CODES.UNAUTHORIZED_ACCESS,
          message: AUTH_ERROR_MESSAGES[AUTH_ERROR_CODES.UNAUTHORIZED_ACCESS],
          details: error
        };
      }
    }

    // Error genérico
    return {
      code: 'UNKNOWN_ERROR',
      message: error?.message || 'Error desconocido en la autenticación',
      details: error
    };
  }

  /**
   * Verifica si el token está próximo a expirar y necesita renovación
   */
  needsTokenRefresh(): boolean {
    const token = this.tokenManager.getToken();
    return !token || this.tokenManager.isTokenExpired(token);
  }

  /**
   * Fuerza una validación de la sesión actual
   */
  async refreshSession(): Promise<void> {
    if (!this.isAuthenticated()) {
      throw new Error('No hay sesión activa para renovar');
    }

    await this.validateCurrentSession();
  }
}

// Exportar instancia singleton
export const authService = AuthService.getInstance();
