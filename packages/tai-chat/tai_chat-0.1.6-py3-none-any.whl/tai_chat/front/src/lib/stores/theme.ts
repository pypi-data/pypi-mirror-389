import { writable } from 'svelte/store';
import type { ThemeConfig } from '../types';

// Default theme configuration
const defaultTheme: ThemeConfig = {
  primary: '#3b82f6',      // blue-500
  secondary: '#6b7280',    // gray-500
  accent: '#10b981',       // emerald-500
  background: '#ffffff',   // white
  surface: '#f9fafb',      // gray-50
  text: '#111827',         // gray-900
  textSecondary: '#6b7280', // gray-500
  border: '#e5e7eb',       // gray-200
  success: '#10b981',      // emerald-500
  warning: '#f59e0b',      // amber-500
  error: '#ef4444'         // red-500
};

const darkTheme: ThemeConfig = {
  primary: '#3b82f6',      // blue-500
  secondary: '#9ca3af',    // gray-400
  accent: '#10b981',       // emerald-500
  background: '#111827',   // gray-900
  surface: '#1f2937',      // gray-800
  text: '#f9fafb',         // gray-50
  textSecondary: '#9ca3af', // gray-400
  border: '#374151',       // gray-700
  success: '#10b981',      // emerald-500
  warning: '#f59e0b',      // amber-500
  error: '#ef4444'         // red-500
};

// Theme store
export const themeStore = writable<ThemeConfig>(defaultTheme);
export const isDarkMode = writable<boolean>(false);

export const themeActions = {
  setTheme: (theme: Partial<ThemeConfig>) => {
    themeStore.update(current => ({ ...current, ...theme }));
    themeActions.applyTheme();
  },

  toggleDarkMode: () => {
    isDarkMode.update(currentDark => {
      const newDark = !currentDark;
      
      // Actualizar el tema
      themeStore.set(newDark ? darkTheme : defaultTheme);
      
      if (typeof window !== 'undefined') {
        // Guardar en localStorage
        localStorage.setItem('tai-chat-dark-mode', String(newDark));
        
        // Aplicar/quitar la clase CSS
        if (newDark) {
          document.documentElement.classList.add('dark');
        } else {
          document.documentElement.classList.remove('dark');
        }
      }
      
      themeActions.applyTheme();
      return newDark;
    });
  },

  setCustomTheme: (customTheme: ThemeConfig) => {
    themeStore.set(customTheme);
    if (typeof window !== 'undefined') {
      localStorage.setItem('tai-chat-custom-theme', JSON.stringify(customTheme));
    }
    themeActions.applyTheme();
  },

  applyTheme: () => {
    themeStore.subscribe(theme => {
      if (typeof window !== 'undefined') {
        const root = document.documentElement;
        root.style.setProperty('--color-primary', theme.primary);
        root.style.setProperty('--color-secondary', theme.secondary);
        root.style.setProperty('--color-accent', theme.accent);
        root.style.setProperty('--color-background', theme.background);
        root.style.setProperty('--color-surface', theme.surface);
        root.style.setProperty('--color-text', theme.text);
        root.style.setProperty('--color-text-secondary', theme.textSecondary);
        root.style.setProperty('--color-border', theme.border);
        root.style.setProperty('--color-success', theme.success);
        root.style.setProperty('--color-warning', theme.warning);
        root.style.setProperty('--color-error', theme.error);
      }
    })();
  },

  init: () => {
    if (typeof window !== 'undefined') {
      // Check for saved dark mode preference
      const savedDarkMode = localStorage.getItem('tai-chat-dark-mode');
      const isDark = savedDarkMode === 'true';
      
      isDarkMode.set(isDark);
      themeStore.set(isDark ? darkTheme : defaultTheme);
      
      // Aplicar o quitar la clase 'dark' según corresponda
      if (isDark) {
        document.documentElement.classList.add('dark');
      } else {
        document.documentElement.classList.remove('dark');
      }

      // Check for custom theme
      const savedTheme = localStorage.getItem('tai-chat-custom-theme');
      if (savedTheme) {
        try {
          const customTheme = JSON.parse(savedTheme);
          themeStore.set(customTheme);
        } catch (e) {
          console.warn('Invalid custom theme in localStorage');
        }
      }

      themeActions.applyTheme();
    }
  }
};
