// Servicio base para llamadas HTTP a la API
import { authService } from '../auth/AuthService';
import { AUTH_ERROR_CODES } from '../auth/types';
import { configStore } from '../stores/config';
import { get } from 'svelte/store';


// Función para obtener la URL de la API dinámicamente
const getApiBaseUrl = () => get(configStore).apiUrl;

export class ApiError extends Error {
  constructor(public status: number, message: string, public data?: any) {
    super(message);
    this.name = 'ApiError';
  }
}

// Estructura de respuesta de la API
export interface APIResponse<T> {
  status: 'success' | 'error' | 'warning';
  data?: T;
  message?: string;
  errors?: Array<{
    code: string;
    message: string;
    details?: any;
    field?: string;
  }>;
  meta?: any;
}

export async function apiRequest<T>(
  endpoint: string, 
  options: RequestInit = {}
): Promise<T> {
  const url = `${getApiBaseUrl()}${endpoint}`;
  
  // Agregar automáticamente headers de autenticación si no es un endpoint de auth
  const isAuthEndpoint = endpoint.startsWith('/auth/');
  const authHeaders = !isAuthEndpoint ? authService.getAuthHeaders() : {};
  
  const config: RequestInit = {
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders,
      ...options.headers,
    },
    ...options,
  };

  try {
    const response = await fetch(url, config);
    
    if (!response.ok) {
      // Intentar parsear la respuesta de error
      try {
        const errorResponse: APIResponse<null> = await response.json();
        
        // Manejar errores de autenticación automáticamente
        if (!isAuthEndpoint && errorResponse.errors?.[0]) {
          const errorCode = errorResponse.errors[0].code;
          if (Object.values(AUTH_ERROR_CODES).includes(errorCode as any)) {
            const authError = {
              code: errorCode,
              message: errorResponse.errors[0].message,
              details: errorResponse.errors[0].details
            };
            authService.handleAuthError(authError);
          }
        }
        
        const errorMessage = errorResponse.message || 'Error en la API';
        const errorDetails = errorResponse.errors?.[0]?.message || errorMessage;
        throw new ApiError(response.status, errorDetails, errorResponse);
      } catch (parseError) {
        throw new ApiError(response.status, `HTTP ${response.status}: ${response.statusText}`, null);
      }
    }

    // Parsear la respuesta
    const apiResponse: APIResponse<T> = await response.json();
    
    // Verificar si la API devolvió un error en el status
    if (apiResponse.status === 'error') {
      // Manejar errores de autenticación automáticamente
      if (!isAuthEndpoint && apiResponse.errors?.[0]) {
        const errorCode = apiResponse.errors[0].code;
        if (Object.values(AUTH_ERROR_CODES).includes(errorCode as any)) {
          const authError = {
            code: errorCode,
            message: apiResponse.errors[0].message,
            details: apiResponse.errors[0].details
          };
          authService.handleAuthError(authError);
        }
      }
      
      const errorMessage = apiResponse.message || 'Error en la API';
      const errorDetails = apiResponse.errors?.[0]?.message || errorMessage;
      throw new ApiError(response.status, errorDetails, apiResponse);
    }
    
    // Devolver solo los datos
    return apiResponse.data as T;
    
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw new ApiError(0, 'Error de conexión: ' + (error as Error).message, error);
  }
}
