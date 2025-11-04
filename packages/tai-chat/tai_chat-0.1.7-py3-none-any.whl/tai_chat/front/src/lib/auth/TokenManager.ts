/**
 * Gestor de tokens JWT
 * Maneja almacenamiento, validación y renovación de tokens
 */

import type { AuthSession, TokenPayload } from './types';

const STORAGE_KEYS = {
  TOKEN: 'auth_token',
  USER: 'auth_user',
  SESSION_ID: 'auth_session_id',
  EXPIRES_AT: 'auth_expires_at'
} as const;

export class TokenManager {
  private static instance: TokenManager;
  
  static getInstance(): TokenManager {
    if (!TokenManager.instance) {
      TokenManager.instance = new TokenManager();
    }
    return TokenManager.instance;
  }

  /**
   * Almacena una sesión completa en localStorage
   */
  storeSession(session: AuthSession): void {
    try {
      localStorage.setItem(STORAGE_KEYS.TOKEN, session.token);
      localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(session.user));
      localStorage.setItem(STORAGE_KEYS.SESSION_ID, session.sessionId);
      localStorage.setItem(STORAGE_KEYS.EXPIRES_AT, session.expiresAt.toString());
    } catch (error) {
      console.error('Error storing session:', error);
    }
  }

  /**
   * Recupera la sesión desde localStorage
   */
  getStoredSession(): AuthSession | null {
    try {
      const token = localStorage.getItem(STORAGE_KEYS.TOKEN);
      const userStr = localStorage.getItem(STORAGE_KEYS.USER);
      const sessionId = localStorage.getItem(STORAGE_KEYS.SESSION_ID);
      const expiresAtStr = localStorage.getItem(STORAGE_KEYS.EXPIRES_AT);

      if (!token || !userStr || !sessionId || !expiresAtStr) {
        return null;
      }

      const user = JSON.parse(userStr);
      const expiresAt = parseInt(expiresAtStr, 10);

      return {
        token,
        user,
        sessionId,
        expiresAt
      };
    } catch (error) {
      console.error('Error retrieving stored session:', error);
      return null;
    }
  }

  /**
   * Obtiene solo el token actual
   */
  getToken(): string | null {
    try {
      return localStorage.getItem(STORAGE_KEYS.TOKEN);
    } catch (error) {
      console.error('Error getting token:', error);
      return null;
    }
  }

  /**
   * Limpia toda la información de sesión
   */
  clearSession(): void {
    try {
      Object.values(STORAGE_KEYS).forEach(key => {
        localStorage.removeItem(key);
      });
    } catch (error) {
      console.error('Error clearing session:', error);
    }
  }

  /**
   * Verifica si el token ha expirado
   */
  isTokenExpired(token?: string): boolean {
    try {
      const tokenToCheck = token || this.getToken();
      if (!tokenToCheck) return true;

      const payload = this.decodeTokenPayload(tokenToCheck);
      if (!payload) return true;

      const now = Date.now() / 1000;
      return payload.exp < now;
    } catch (error) {
      console.error('Error checking token expiration:', error);
      return true;
    }
  }

  /**
   * Decodifica el payload del token JWT (sin validar firma)
   */
  decodeTokenPayload(token: string): TokenPayload | null {
    try {
      const parts = token.split('.');
      if (parts.length !== 3) return null;

      const payload = parts[1];
      const decoded = atob(payload.replace(/-/g, '+').replace(/_/g, '/'));
      return JSON.parse(decoded) as TokenPayload;
    } catch (error) {
      console.error('Error decoding token payload:', error);
      return null;
    }
  }

  /**
   * Verifica si hay una sesión válida almacenada
   */
  hasValidStoredSession(): boolean {
    const session = this.getStoredSession();
    if (!session) return false;

    return !this.isTokenExpired(session.token);
  }

  /**
   * Obtiene información del usuario desde el token almacenado
   */
  getUserFromToken(): TokenPayload | null {
    const token = this.getToken();
    if (!token) return null;

    return this.decodeTokenPayload(token);
  }

  /**
   * Escucha cambios en localStorage para sincronizar entre pestañas
   */
  onStorageChange(callback: (session: AuthSession | null) => void): () => void {
    const handleStorageChange = (e: StorageEvent) => {
      if (Object.values(STORAGE_KEYS).includes(e.key as any)) {
        const session = this.getStoredSession();
        callback(session);
      }
    };

    window.addEventListener('storage', handleStorageChange);
    
    // Retorna función para cleanup
    return () => {
      window.removeEventListener('storage', handleStorageChange);
    };
  }
}
