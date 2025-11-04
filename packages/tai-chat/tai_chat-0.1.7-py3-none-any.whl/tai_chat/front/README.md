# TAI Chat Frontend

Frontend desarrollado en Svelte/SvelteKit para el framework `tai-chat`.

## Características

### 🎨 **Sistema de Temas Configurable**
- Tema claro/oscuro automático
- Colores completamente personalizables vía configuración
- CSS Variables para fácil customización
- Integración con Tailwind CSS

### 🏗️ **Arquitectura Modular**
```
src/
├── lib/
│   ├── components/     # Componentes Svelte reutilizables
│   ├── stores/        # Estado global con Svelte stores
│   ├── services/      # Servicios para API y WebSocket
│   ├── types/         # Definiciones TypeScript
│   └── utils/         # Utilidades y helpers
├── routes/            # Páginas SvelteKit
└── static/           # Archivos estáticos
```

### 📱 **Componentes Principales**

#### **Layout.svelte**
- Layout base con inicialización de stores
- Aplicación automática de temas
- CSS variables dinámicas

#### **Login.svelte**
- Autenticación con validación
- Modo login/registro
- Manejo de errores
- Diseño responsive

#### **Chat.svelte**
- Componente principal de chat
- Gestión de estado de chats
- Integración WebSocket
- Manejo de errores

#### **ChatSidebar.svelte**
- Lista de chats
- Perfil de usuario
- Configuraciones rápidas
- Navegación

#### **ChatWindow.svelte**
- Ventana principal de conversación
- Input de mensajes
- Scroll automático
- Indicador de escritura

#### **MessageBubble.svelte**
- Burbujas de mensajes
- Formateo de contenido
- Timestamps
- Acciones (copiar, etc.)

### 🔄 **Gestión de Estado**

#### **authStore**
```typescript
interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  token: string | null;
}
```

#### **chatStore**
```typescript
interface ChatState {
  currentChat: Chat | null;
  chats: Chat[];
  isLoading: boolean;
  error: string | null;
}
```

#### **themeStore**
```typescript
interface ThemeConfig {
  primary: string;
  secondary: string;
  accent: string;
  background: string;
  surface: string;
  text: string;
  // ... más colores
}
```

### 🌐 **Servicios**

#### **AuthService**
- Login/registro
- Validación de tokens
- Renovación automática
- Gestión de sesiones

#### **ChatService**
- API REST para chats
- WebSocket para tiempo real
- Fallback HTTP
- Gestión de conexiones

### ⚙️ **Configuración**

La configuración se puede inyectar vía:

1. **Archivo estático** (`/static/config.json`)
2. **Variables de entorno**
3. **Configuración dinámica** (API endpoint)

```json
{
  "apiUrl": "http://localhost:8000/api",
  "wsUrl": "ws://localhost:8000/ws",
  "llmModel": "gpt-4",
  "mcpServerUrl": "http://localhost:8001",
  "theme": {
    "primary": "#3b82f6",
    "secondary": "#6b7280"
  }
}
```

### 🚀 **Comandos de Desarrollo**

```bash
# Instalar dependencias
npm install

# Desarrollo
npm run dev

# Build
npm run build

# Preview
npm run preview

# Type checking
npm run check
```

### 🎯 **Integración con TAI-Chat CLI**

El CLI de `tai-chat` puede:

1. **Generar configuración personalizada**
2. **Customizar temas** automáticamente
3. **Inyectar variables** de entorno
4. **Configurar endpoints** del backend
5. **Personalizar branding**

Este frontend está diseñado para ser completamente personalizable através del CLI de `tai-chat` mientras mantiene una experiencia de usuario consistente y moderna.
