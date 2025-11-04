import { writable } from 'svelte/store';
import type { AppConfig } from '../types';
import { themeActions } from './theme';
// Default configuration that can be overridden by tai-chat CLI
const defaultConfig: AppConfig = {
  apiUrl: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  wsUrl: import.meta.env.VITE_WS_URL || `${(import.meta.env.VITE_API_URL || 'http://localhost:8000').replace('http', 'ws')}/streaming/ws/chat`,
  theme: {
    primary: '#3b82f6',
    secondary: '#6b7280',
    accent: '#10b981',
    background: '#ffffff',
    surface: '#f9fafb',
    text: '#111827',
    textSecondary: '#6b7280',
    border: '#e5e7eb',
    success: '#10b981',
    warning: '#f59e0b',
    error: '#ef4444'
  }
};

export const configStore = writable<AppConfig>(defaultConfig);

export const configActions = {
  setConfig: (config: Partial<AppConfig>) => {
    configStore.update(current => {
      const newConfig = { ...current, ...config };
      
      // If theme is updated, apply it
      if (config.theme) {
        themeActions.setCustomTheme({ ...current.theme, ...config.theme });
      }
      
      return newConfig;
    });
  },
};
