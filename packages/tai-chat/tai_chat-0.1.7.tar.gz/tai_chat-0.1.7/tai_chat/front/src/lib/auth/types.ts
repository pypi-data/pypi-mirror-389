/**
 * Tipos TypeScript para el sistema de autenticación
 */

export interface LoginRequest {
  username: string;
  pwd: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
  session_id: string;
}

export interface User {
  id?: number;
  username: string;
  email?: string;
  nombre?: string;
  apellido?: string;
  activo?: boolean;
  // Añadir otros campos según tu modelo de usuario
}

export interface TokenPayload {
  username: string;
  session_id: string;
  exp: number;
  iat: number;
}

export type AuthState = 
  | 'loading'           // Verificando autenticación inicial
  | 'authenticated'     // Usuario logueado correctamente
  | 'unauthenticated'   // Necesita login
  | 'session_invalidated' // Sesión cerrada por login concurrente
  | 'session_expired'     // Sesión expirada por tiempo

export interface AuthError {
  code: string;
  message: string;
  details?: any;
}

export interface AuthSession {
  token: string;
  user: User;
  sessionId: string;
  expiresAt: number;
}

// Códigos de error de autenticación específicos
export const AUTH_ERROR_CODES = {
  INVALID_CREDENTIALS: 'INVALID_CREDENTIALS',
  SESSION_INVALIDATED: 'SESSION_INVALIDATED',
  SESSION_EXPIRED: 'SESSION_EXPIRED',
  INVALID_TOKEN: 'INVALID_TOKEN',
  TOKEN_EXPIRED: 'TOKEN_EXPIRED',
  UNAUTHORIZED_ACCESS: 'UNAUTHORIZED_ACCESS',
  CONCURRENT_SESSION_DETECTED: 'CONCURRENT_SESSION_DETECTED',
  PASSWORD_EXPIRED: 'PASSWORD_EXPIRED'
} as const;

export type AuthErrorCode = typeof AUTH_ERROR_CODES[keyof typeof AUTH_ERROR_CODES];

// Mensajes de error localizados
export const AUTH_ERROR_MESSAGES: Record<AuthErrorCode, string> = {
  [AUTH_ERROR_CODES.INVALID_CREDENTIALS]: 'Usuario o contraseña incorrectos',
  [AUTH_ERROR_CODES.SESSION_INVALIDATED]: 'Tu sesión ha sido cerrada porque se inició otra sesión con tus credenciales',
  [AUTH_ERROR_CODES.SESSION_EXPIRED]: 'Tu sesión ha expirado. Por favor, inicia sesión nuevamente',
  [AUTH_ERROR_CODES.INVALID_TOKEN]: 'Token de acceso inválido',
  [AUTH_ERROR_CODES.TOKEN_EXPIRED]: 'Token de acceso expirado',
  [AUTH_ERROR_CODES.UNAUTHORIZED_ACCESS]: 'No tienes permisos para acceder a este recurso',
  [AUTH_ERROR_CODES.CONCURRENT_SESSION_DETECTED]: 'Se detectó otra sesión activa con tus credenciales',
  [AUTH_ERROR_CODES.PASSWORD_EXPIRED]: 'Tu contraseña ha expirado. Debes renovarla para continuar'
};
