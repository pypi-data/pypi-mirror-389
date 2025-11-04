<script lang="ts">
  import { onMount } from 'svelte';
  import { formatRelativeTime, truncateText } from '$lib/utils/helpers';
  import { authStore } from '$lib/stores/auth';
  import { chatStore } from '$lib/stores/chat';
  import { themeStore, isDarkMode, themeActions } from '$lib/stores/theme';
  import type { Chat, User } from '$lib/types';

  interface Props {
    isSidebarOpen?: boolean;
    onNewChat?: () => void;
    onSelectChat?: (chat: Chat) => void;
    onDeleteChat?: (chatId: string) => void;
    onLogout?: () => void;
    onToggleSidebar?: () => void;
  }

  let { 
    isSidebarOpen = true, 
    onNewChat, 
    onSelectChat, 
    onDeleteChat, 
    onLogout,
    onToggleSidebar
  }: Props = $props();

  let user = $state<User | null>(null);
  let chats = $state<Chat[]>([]);
  let currentChat = $state<Chat | null>(null);
  
  // Estado para el modal de confirmación
  let showDeleteModal = $state(false);
  let chatToDelete = $state<Chat | null>(null);

  // Usar directamente el store derivado en lugar de una variable local
  const darkMode = $derived($isDarkMode);

  // Subscribe to store changes
  onMount(() => {
    const unsubAuth = authStore.subscribe(store => {
      user = store.user;
    });
    
    const unsubChat = chatStore.subscribe(store => {
      chats = store.chats;
      currentChat = store.currentChat;
    });

    return () => {
      unsubAuth();
      unsubChat();
    };
  });

  function getChatTitle(chat: Chat): string {
    if (chat.title) {
      return chat.title;
    }
    
    const firstMessage = chat.messages[0];
    if (firstMessage) {
      return truncateText(firstMessage.content, 30);
    }
    
    return 'Chat nuevo';
  }

  function selectChat(chat: Chat) {
    onSelectChat?.(chat);
  }

  function createNewChat() {
    onNewChat?.();
  }

  function openDeleteModal(chat: Chat, event: Event) {
    event.stopPropagation();
    chatToDelete = chat;
    showDeleteModal = true;
  }

  function confirmDelete() {
    if (chatToDelete) {
      onDeleteChat?.(chatToDelete.id);
      showDeleteModal = false;
      chatToDelete = null;
    }
  }

  function cancelDelete() {
    showDeleteModal = false;
    chatToDelete = null;
  }

  function logout() {
    onLogout?.();
  }

  function toggleDarkMode() {
    themeActions.toggleDarkMode();
  }

  function toggleSidebar() {
    onToggleSidebar?.();
  }
</script>

<!-- Overlay for mobile -->
{#if isSidebarOpen}
  <div 
    class="fixed top-0 right-0 bottom-0 left-80 bg-black bg-opacity-50 z-30 lg:hidden"
    onclick={toggleSidebar}
    role="button"
    tabindex="0"
    onkeydown={(e) => e.key === 'Escape' && toggleSidebar()}
  ></div>
{/if}

<!-- Sidebar -->
<div class="
  fixed lg:relative inset-y-0 left-0 z-50 
  w-80 bg-surface border-r border-border
  {isSidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
  flex flex-col
">
  <!-- Header -->
  <div class="p-4 border-b border-border">
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-2xl font-semibold text-text">Finsa mantenimiento</h2>
      
      <!-- Botón para cerrar sidebar en móvil -->
      <button
        onclick={toggleSidebar}
        class="lg:hidden p-2 text-text-secondary hover:text-primary hover:bg-background rounded-md cursor-pointer hover:scale-105"
        aria-label="Cerrar sidebar"
        title="Cerrar sidebar"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
        </svg>
      </button>
    </div>

    <!-- Botón Nuevo Chat -->
    <button
      onclick={createNewChat}
      class="w-full flex items-center justify-center space-x-2 p-3 mb-4 text-text-secondary hover:text-primary hover:bg-primary/5 border border-border hover:border-primary/30 rounded-lg transition-all duration-200 ease-in-out cursor-pointer group"
      title="Crear nuevo chat"
    >
      <svg class="w-5 h-5 transition-colors duration-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>
      </svg>
      <span class="font-medium">Nuevo chat</span>
    </button>
  </div>

  <!-- Chat List -->
  <div class="flex-1 overflow-y-auto scrollbar-styled">
    {#if chats.length === 0}
      <div class="p-4 text-center">
        <div class="text-text-secondary text-sm">
          Empieza una conversación creando un nuevo chat.
        </div>
      </div>
    {:else}
      {#each chats as chat (chat.id)}
        <div
          class="group p-3 border-b border-border hover:bg-background cursor-pointer transition-all duration-200 hover:shadow-sm {currentChat?.id === chat.id ? 'bg-background border-l-4 border-l-primary shadow-sm' : ''}"
          onclick={() => selectChat(chat)}
          role="button"
          tabindex="0"
          onkeydown={(e) => e.key === 'Enter' && selectChat(chat)}
        >
          <div class="flex items-start justify-between">
            <div class="flex-1 min-w-0">
              <h3 class="text-sm font-medium text-text truncate mb-1">
                {getChatTitle(chat)}
              </h3>
              <div class="flex items-center justify-between">
                <p class="text-xs text-text-secondary">
                  {chat.messages.length} {chat.messages.length === 1 ? 'mensaje' : 'mensajes'}
                </p>
                <span class="text-xs text-text-secondary">
                  {formatRelativeTime(chat.updatedAt)}
                </span>
              </div>
            </div>
            <button
              onclick={(e) => openDeleteModal(chat, e)}
              class="group/delete p-1.5 text-text-secondary hover:text-red-500 rounded-full ease-in-out opacity-0 group-hover:opacity-100 transform hover:scale-115 active:scale-95 cursor-pointer"
              aria-label="Eliminar chat"
              title="Eliminar chat"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
              </svg>
            </button>
          </div>
        </div>
      {/each}
    {/if}
  </div>

  <!-- Footer -->
  <div class="p-4 border-t border-border">
    <div class="flex items-center justify-between">
      <!-- User info -->
      {#if user}
        <div class="flex items-center space-x-3">
          <div class="w-8 h-8 bg-primary text-white rounded-full flex items-center justify-center text-sm font-medium">
            {user.username?.charAt(0).toUpperCase() || 'U'}
          </div>
          <div class="flex-1 min-w-0">
            <p class="text-sm font-medium text-text truncate">{user.username}</p>
            <p class="text-xs text-text-secondary truncate">{user.email}</p>
          </div>
        </div>
      {:else}
        <div></div>
      {/if}

      <!-- Botones a la derecha -->
      <div class="flex items-center space-x-2">
        <button
          onclick={toggleDarkMode}
          class="group p-2 text-text-secondary hover:text-primary hover:bg-primary/10 rounded-full transition-all duration-200 ease-in-out transform hover:scale-105 active:scale-95 cursor-pointer shadow-lg shadow-transparent hover:shadow-primary/50"
          aria-label={darkMode ? 'Modo claro' : 'Modo oscuro'}
          title={darkMode ? 'Cambiar a modo claro' : 'Cambiar a modo oscuro'}
        >
          {#if darkMode}
            <svg class="w-5 h-5 transition-colors duration-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"></path>
            </svg>
          {:else}
            <svg class="w-5 h-5 transition-colors duration-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"></path>
            </svg>
          {/if}
        </button>

        <button
          onclick={logout}
          class="group p-2 text-text-secondary rounded-full transition-all duration-200 ease-in-out transform hover:scale-105 active:scale-95 cursor-pointer"
          aria-label="Cerrar sesión"
          title="Cerrar sesión"
        >
          <svg class="w-5 h-5 transition-colors duration-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"></path>
          </svg>
        </button>
      </div>
    </div>
  </div>
</div>

<!-- Modal de confirmación para eliminar chat -->
{#if showDeleteModal}
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[100] p-4">
    <div class="bg-surface rounded-xl shadow-2xl max-w-md w-full mx-4 transform transition-all duration-300 scale-100">
      <!-- Header del modal -->
      <div class="p-6 border-b border-border">
        <div class="flex items-center space-x-3">
          <!-- <div class="w-12 h-12 bg-error bg-opacity-10 rounded-full flex items-center justify-center">
            <svg class="w-6 h-6 text-error" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.996-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"></path>
            </svg>
          </div> -->
          <div>
            <h3 class="text-lg font-semibold text-text">Eliminar chat</h3>
            <p class="text-sm text-text-secondary">Esta acción no se puede deshacer</p>
          </div>
        </div>
      </div>

      <!-- Contenido del modal -->
      <div class="p-6">
        <p class="text-text mb-2">
          ¿Estás seguro de que quieres eliminar este chat?
        </p>
        {#if chatToDelete}
          <div class="bg-background rounded-lg p-3 border border-border">
            <p class="text-sm font-medium text-text truncate">
              {getChatTitle(chatToDelete)}
            </p>
            <p class="text-xs text-text-secondary mt-1">
              {chatToDelete.messages.length} {chatToDelete.messages.length === 1 ? 'mensaje' : 'mensajes'}
            </p>
          </div>
        {/if}
        <p class="text-sm text-text-secondary mt-3">
          Se eliminarán todos los mensajes de forma permanente.
        </p>
      </div>

      <!-- Botones del modal -->
      <div class="p-6 border-t border-border flex justify-end space-x-3">
        <button
          onclick={cancelDelete}
          class="px-4 py-2 text-text-secondary font-medium cursor-pointer transition-all duration-100 hover:scale-105"
        >
          Cancelar
        </button>
        <button
          onclick={confirmDelete}
          class="px-4 py-2 bg-error text-white rounded-lg transition-all duration-100 font-medium hover:shadow-lg transform hover:scale-105 active:scale-95 cursor-pointer"
        >
          Eliminar chat
        </button>
      </div>
    </div>
  </div>
{/if}

<style>
  /* Custom scrollbar styles */
  .scrollbar-styled {
    scrollbar-width: thin;
    scrollbar-color: #CBD5E1 transparent;
  }

  /* Webkit browsers (Chrome, Safari, Edge) */
  .scrollbar-styled::-webkit-scrollbar {
    width: 8px;
  }

  .scrollbar-styled::-webkit-scrollbar-track {
    background: transparent;
    border-radius: 10px;
  }

  .scrollbar-styled::-webkit-scrollbar-thumb {
    background: #CBD5E1;
    border-radius: 10px;
    border: 2px solid transparent;
    background-clip: content-box;
  }

  .scrollbar-styled::-webkit-scrollbar-thumb:hover {
    background: #94A3B8;
    background-clip: content-box;
  }

  /* Dark mode support */
  :global(.dark) .scrollbar-styled {
    scrollbar-color: #475569 transparent;
  }

  :global(.dark) .scrollbar-styled::-webkit-scrollbar-thumb {
    background: #475569;
    background-clip: content-box;
  }

  :global(.dark) .scrollbar-styled::-webkit-scrollbar-thumb:hover {
    background: #64748B;
    background-clip: content-box;
  }
</style>
