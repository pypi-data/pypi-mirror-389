// Re-export everything from lib
export * from './stores';
export * from './services';
export * from './utils';

// Export components explicitly to avoid conflicts
export { 
  Layout, 
  Login, 
  Chat as ChatComponent, 
  ChatSidebar, 
  ChatWindow, 
  MessageBubble 
} from './components';

// Export types explicitly
export type { 
  User, 
  Message, 
  Chat as ChatType, 
  AuthState, 
  ChatState, 
  ThemeConfig, 
  AppConfig 
} from './types';
