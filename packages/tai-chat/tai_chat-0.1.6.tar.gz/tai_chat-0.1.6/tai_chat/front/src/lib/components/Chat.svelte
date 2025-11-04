<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { chatStore, chatActions, authStore } from '../stores';
  import { chatService } from '../services';
  import { authService } from '../auth';
  import ChatSidebar from './ChatSidebar.svelte';
  import ChatWindow from './ChatWindow.svelte';
  import type { Chat } from '../types';

  let isSidebarOpen = $state(false); // Inicia cerrado, se abrirá después según el tamaño de pantalla
  let isLoading = $state(true);
  let isClient = $state(false);
  let unsubscribeChat: (() => void) | null = null;
  let unsubscribeStreamingUpdate: (() => void) | null = null;
  let unsubscribeAuth: (() => void) | null = null;
  let removeResizeListener: (() => void) | null = null;

  onMount(async () => {
    isClient = true;
    
    // Configurar el estado inicial del sidebar basado en el tamaño de pantalla
    if (typeof window !== 'undefined') {
      const updateSidebarState = () => {
        isSidebarOpen = window.innerWidth >= 1024; // lg breakpoint
      };
      
      // Configurar estado inicial
      updateSidebarState();
      
      // Escuchar cambios de tamaño de ventana
      window.addEventListener('resize', updateSidebarState);
      
      // Guardar la función de cleanup
      removeResizeListener = () => {
        window.removeEventListener('resize', updateSidebarState);
      };
    }
    
    // Subscribe to auth changes - just for navigation, no circular calls
    unsubscribeAuth = authStore.subscribe(auth => {
      // Just listen to changes, don't trigger logout here
      // The actual logout should be triggered by user action
    });

    // Load user's chats
    await loadChats();
    isLoading = false;
  });

  onDestroy(() => {
    if (unsubscribeChat) unsubscribeChat();
    if (unsubscribeStreamingUpdate) unsubscribeStreamingUpdate();
    if (unsubscribeAuth) unsubscribeAuth();
    if (removeResizeListener) removeResizeListener();
    chatService.disconnectWebSocket();
  });

  async function loadChats() {
    try {
      chatActions.setLoading(true);
      const chats = await chatService.getChats();
      chatActions.setChats(chats);
      
      // If there are chats, select the most recent one
      if (chats.length > 0) {
        await selectChat(chats[0]);
      }
    } catch (error) {
      console.error('Failed to load chats:', error);
      chatActions.setError('No se pudieron cargar los chats');
    } finally {
      chatActions.setLoading(false);
    }
  }

  async function selectChat(chat: Chat) {
    try {
      chatActions.setCurrentChat(chat);
      chatService.connectWebSocket(chat.id);
      
      // Setup message handler
      if (unsubscribeChat) unsubscribeChat();
      unsubscribeChat = chatService.onMessage((message) => {
        chatActions.addMessage(message);
      });

      // Setup streaming update handler  
      if (unsubscribeStreamingUpdate) unsubscribeStreamingUpdate();
      unsubscribeStreamingUpdate = chatService.onStreamingUpdate((message) => {
        chatActions.updateMessage(message.id, message);
      });
    } catch (error) {
      console.error('Failed to select chat:', error);
      chatActions.setError('No se pudo conectar al chat');
    }
  }

  async function createNewChat() {
    try {
      // Obtener el usuario actual del authStore
      const currentAuth = $authStore;
      if (!currentAuth.user) {
        chatActions.setError('No hay usuario autenticado');
        return;
      }

      const newChat = await chatService.createChat({
        title: 'Nuevo Chat',
        username: currentAuth.user.username
      });
      chatActions.addChat(newChat);
      await selectChat(newChat);
    } catch (error) {
      console.error('Failed to create chat:', error);
      chatActions.setError('No se pudo crear el chat');
    }
  }

  async function deleteChat(chatId: string) {
    try {
      await chatService.deleteChat(chatId);
      chatActions.removeChat(chatId);
      
      // If we deleted the current chat, select another one or create new
      const currentState = $chatStore;
      if (currentState.currentChat?.id === chatId) {
        if (currentState.chats.length > 0) {
          await selectChat(currentState.chats[0]);
        } else {
          await createNewChat();
        }
      }
    } catch (error) {
      console.error('Failed to delete chat:', error);
      chatActions.setError('No se pudo eliminar el chat');
    }
  }

  function toggleSidebar() {
    // Simple toggle - el comportamiento responsive se maneja en CSS
    isSidebarOpen = !isSidebarOpen;
  }

  async function logout() {
    try {
      // The authService now handles both backend notification and local cleanup
      await authService.logout();
    } catch (error) {
      console.error('Error during logout:', error);
    }
  }
</script>

{#if !isClient}
  <!-- Server-side: show loading -->
  <div class="min-h-screen flex items-center justify-center bg-background">
    <div class="text-center">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
      <p class="text-text-secondary">Cargando...</p>
    </div>
  </div>
{:else if isLoading}
  <div class="min-h-screen flex items-center justify-center bg-background">
    <div class="text-center">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
      <p class="text-text-secondary">Cargando...</p>
    </div>
  </div>
{:else}
  <div class="flex h-screen bg-background">
    <!-- Sidebar -->
    <ChatSidebar 
      {isSidebarOpen}
      onToggleSidebar={toggleSidebar}
      onSelectChat={selectChat}
      onNewChat={createNewChat}
      onDeleteChat={deleteChat}
      onLogout={logout}
    />

    <!-- Main Chat Area -->
    <div class="flex-1 flex flex-col min-w-0 relative z-40">
      <ChatWindow 
        onToggleSidebar={toggleSidebar}
      />
    </div>
  </div>
{/if}
