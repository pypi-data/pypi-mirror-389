// Re-export auth types from the auth module
export type { User, AuthState, AuthSession, AuthError, LoginRequest, LoginResponse } from '../auth/types';

export interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant' | 'system';
  timestamp: Date;
  userId: string;
  chatId: string;
  isStreaming?: boolean;
  metadata?: Record<string, any>;
}

export interface Chat {
  id: string;
  title: string;
  userId: string;
  messages: Message[];
  createdAt: Date;
  updatedAt: Date;
  isActive: boolean;
}

export interface ChatState {
  currentChat: Chat | null;
  chats: Chat[];
  isLoading: boolean;
  error: string | null;
}

export interface ThemeConfig {
  primary: string;
  secondary: string;
  accent: string;
  background: string;
  surface: string;
  text: string;
  textSecondary: string;
  border: string;
  success: string;
  warning: string;
  error: string;
}

export interface AppConfig {
  apiUrl: string;
  wsUrl: string;
  theme: ThemeConfig;
}
