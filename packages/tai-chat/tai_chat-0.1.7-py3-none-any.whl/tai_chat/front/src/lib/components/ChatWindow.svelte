<script lang="ts">
  import { onMount } from 'svelte';
  import { chatStore, chatActions } from '../stores';
  import { chatService } from '../services';
  import MessageBubble from './MessageBubble.svelte';
  import logoImage from '../assets/logo_alpha_transp.png';

  interface Props {
    onToggleSidebar?: () => void;
  }

  let { onToggleSidebar }: Props = $props();

  let messageInput = $state('');
  let messagesContainer: HTMLElement;
  let messageTextarea = $state<HTMLTextAreaElement>();
  let isTyping = $state(false);
  let isSending = $state(false);
  let isEditingTitle = $state(false);
  let editingTitle = $state('');

  const currentChat = $derived($chatStore.currentChat);
  const messages = $derived(currentChat?.messages || []);
  const error = $derived($chatStore.error);
  const isLoading = $derived($chatStore.isLoading);

  onMount(() => {
    scrollToBottom();
  });

  $effect(() => {
    if (messages) {
      setTimeout(scrollToBottom, 100);
    }
  });

  // Efecto para detectar cuando llega una respuesta del bot y ocultar "IA escribiendo..."
  $effect(() => {
    if (messages && messages.length > 0) {
      const lastMessage = messages[messages.length - 1];
      // Si el último mensaje es del bot y estamos mostrando "IA escribiendo...", ocultarlo
      if (lastMessage.role === 'assistant' && isTyping) {
        isTyping = false;
        // Hacer autofocus en el textarea cuando la IA termine de responder
        setTimeout(() => {
          if (messageTextarea) {
            messageTextarea.focus();
          }
        }, 100);
      }
    }
  });

  function scrollToBottom() {
    if (messagesContainer) {
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
  }

  async function sendMessage() {
    if (!messageInput.trim() || isSending || !currentChat) return;

    const content = messageInput.trim();
    messageInput = '';
    isSending = true;

    try {
      // Always use HTTP to send messages (WebSocket is for receiving)
      console.log('📤 Using HTTP to send message');
      await chatService.sendMessageHttp({
        content,
        chatId: currentChat.id
      });
      isTyping = true;

      // Note: La respuesta del bot llegará via WebSocket y se agregará al store
      // via los message handlers, y cuando eso suceda, isTyping se establecerá en false
      
    } catch (error) {
      console.error('❌ Failed to send message:', error);
      chatActions.setError('No se pudo enviar el mensaje');
      isTyping = false; // Ocultar indicador en caso de error
    } finally {
      isSending = false; // El botón ya no está enviando
      // NOTA: NO removemos isTyping aquí, eso se hará cuando llegue la respuesta del bot
    }
  }

  function handleKeyDown(event: KeyboardEvent) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  }

  function autoResize(event: Event) {
    const textarea = event.target as HTMLTextAreaElement;
    textarea.style.height = 'auto';
    const scrollHeight = textarea.scrollHeight;
    const maxHeight = 120; // max-height en px
    const minHeight = 44;  // min-height en px
    
    if (scrollHeight <= maxHeight) {
      textarea.style.height = Math.max(scrollHeight, minHeight) + 'px';
    } else {
      textarea.style.height = maxHeight + 'px';
    }
  }

  function toggleSidebar() {
    onToggleSidebar?.();
  }

  function cancelOperation() {
    // Cancela la operación en curso
    isTyping = false;
    isSending = false;
    
    // Cancela las operaciones pendientes en el servicio
    chatService.cancelPendingOperations();
    
    console.log('Operation cancelled by user');
  }

  function clearError() {
    chatActions.setError(null);
  }

  function startEditingTitle() {
    if (currentChat) {
      isEditingTitle = true;
      editingTitle = currentChat.title || 'Nuevo Chat';
    }
  }

  async function saveTitle() {
    if (currentChat && editingTitle.trim()) {
      try {
        console.log('🔄 Updating chat title from:', currentChat.title, 'to:', editingTitle.trim());
        // Llamar al servicio para actualizar el título en el backend
        const updatedChat = await chatService.updateChatTitle(currentChat.id, editingTitle.trim());
        console.log('📥 Received updated chat:', updatedChat);
        // Actualizar el store con la respuesta del backend
        chatActions.updateChat(currentChat.id, { 
          title: updatedChat.title,
          updatedAt: updatedChat.updatedAt
        });
        isEditingTitle = false;
        console.log('✅ Chat title updated successfully to:', updatedChat.title);
      } catch (error) {
        console.error('❌ Failed to update chat title:', error);
        chatActions.setError('No se pudo actualizar el título del chat');
        // Revertir el título en la UI
        editingTitle = currentChat.title || 'Nuevo Chat';
      }
    }
  }

  function cancelEditingTitle() {
    isEditingTitle = false;
    editingTitle = '';
  }

  async function handleTitleKeyDown(event: KeyboardEvent) {
    if (event.key === 'Enter') {
      event.preventDefault();
      await saveTitle();
    } else if (event.key === 'Escape') {
      event.preventDefault();
      cancelEditingTitle();
    }
  }
</script>

<div class="flex flex-col h-full bg-background">
  <!-- Header -->
  <div class="bg-surface border-b border-border p-4 flex items-center justify-between">
    <div class="flex items-center space-x-3">
      <button
        onclick={toggleSidebar}
        class="lg:hidden p-2 text-text-secondary hover:text-primary hover:bg-background rounded-md cursor-pointer hover:scale-105"
        aria-label="Toggle sidebar"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"></path>
        </svg>
      </button>
      
      <div class="flex-1">
        {#if isEditingTitle && currentChat}
          <div class="flex items-center space-x-2">
            <input
              bind:value={editingTitle}
              onkeydown={handleTitleKeyDown}
              class="text-lg font-semibold text-text bg-transparent border-b border-primary focus:outline-none focus:border-primary flex-1"
              placeholder="Título del chat"
            />
            <button
              onclick={saveTitle}
              class="p-1 text-primary hover:text-accent transition-colors cursor-pointer"
              title="Guardar"
              aria-label="Guardar título"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
              </svg>
            </button>
            <button
              onclick={cancelEditingTitle}
              class="p-1 text-text-secondary hover:text-error transition-colors cursor-pointer"
              title="Cancelar"
              aria-label="Cancelar edición"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
              </svg>
            </button>
          </div>
        {:else}
          <div class="flex items-center space-x-2 group">
            <button 
              onclick={startEditingTitle}
              onkeydown={(e) => e.key === 'Enter' && startEditingTitle()}
              class="text-lg font-semibold text-text cursor-pointer bg-transparent border-none p-0 hover:text-primary transition-colors text-left"
              aria-label="Editar título del chat"
            >
              {currentChat?.title || 'Bienvenido'}
            </button>
            {#if currentChat}
              <button
                onclick={startEditingTitle}
                onkeydown={(e) => e.key === 'Enter' && startEditingTitle()}
                class="p-1 text-text-secondary hover:text-primary transition-colors opacity-0 group-hover:opacity-100 cursor-pointer"
                title="Editar título"
                aria-label="Editar título del chat"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path>
                </svg>
              </button>
            {/if}
          </div>
        {/if}
        {#if currentChat}
          <p class="text-sm text-text-secondary">
            {messages.length} {messages.length === 1 ? 'mensaje' : 'mensajes'}
          </p>
        {/if}
      </div>
    </div>
  </div>

  <!-- Error Message -->
  <!-- {#if error}
    <div class="mx-4 mt-4 p-3 bg-error bg-opacity-10 border border-error border-opacity-20 rounded-md flex items-center justify-between">
      <span class="text-error text-sm">{error}</span>
      <button
        onclick={clearError}
        class="text-error hover:text-opacity-70"
        aria-label="Cerrar error"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
        </svg>
      </button>
    </div>
  {/if} -->

  <!-- Messages -->
  <div 
    bind:this={messagesContainer}
    class="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-styled"
  >
    {#if !currentChat}
      <div class="h-full flex items-center justify-center text-center">
        <div>
          <h3 class="text-lg font-medium text-text mb-2">¡Hola! 👋</h3>
          <p class="text-text-secondary">
            Selecciona un chat existente o crea uno nuevo para consultar tus datos.
          </p>
        </div>
      </div>
    {:else if messages.length === 0}
      <div class="h-full flex items-center justify-center text-center">
        <div>
          <div class="w-16 h-16 rounded-full flex items-center justify-center mx-auto">
            <img src={logoImage} alt="TAI Chatbot Logo" class="w-10 h-10 object-contain" />
          </div>
          <h3 class="text-lg font-medium text-text mb-2">Nuevo chat</h3>
          <p class="text-text-secondary">
            Escribe tu primer mensaje para comenzar la conversación.
          </p>
        </div>
      </div>
    {:else}
      {#each messages as message (message.id)}
        <MessageBubble {message} />
      {/each}
    {/if}

    <!-- Indicador de "IA escribiendo..." -->
    {#if isTyping}
      <div class="flex justify-start">
        <div class="max-w-xs lg:max-w-md bg-background rounded-lg px-4 py-3">
          <div class="flex items-center space-x-2 text-text-secondary text-sm">
            <div class="flex space-x-1">
              <div class="w-2 h-2 bg-current rounded-full animate-bounce"></div>
              <div class="w-2 h-2 bg-current rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
              <div class="w-2 h-2 bg-current rounded-full animate-bounce" style="animation-delay: 0.4s"></div>
            </div>
            <span>Buscando la mejor respuesta...</span>
          </div>
        </div>
      </div>
    {/if}

    {#if isLoading}
      <div class="flex justify-center">
        <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
      </div>
    {/if}
  </div>

  <!-- Input Area -->
  {#if currentChat}
    <div class="p-4">
      <div class="flex items-center space-x-3">
        <div class="flex-1">
          <textarea
            bind:this={messageTextarea}
            bind:value={messageInput}
            onkeydown={handleKeyDown}
            oninput={autoResize}
            placeholder="Escribe tu mensaje..."
            class="w-full px-4 py-3 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent bg-background text-text resize-none overflow-hidden"
            rows="1"
            disabled={isSending}
            style="min-height: 60px; height: 60px;"
          ></textarea>
        </div>
        
        <button
          onclick={isTyping ? cancelOperation : sendMessage}
          onkeydown={(e) => e.key === 'Enter' && (isTyping ? cancelOperation() : sendMessage())}
          disabled={!isTyping && (!messageInput.trim() || isSending)}
          class="w-12 h-12 {isTyping ? 'bg-red-500 hover:bg-red-600' : 'bg-primary hover:bg-opacity-90'} text-white rounded-full focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center justify-center flex-shrink-0 cursor-pointer"
          aria-label={isTyping ? "Cancelar operación" : "Enviar mensaje"}
        >
          {#if isSending}
            <svg class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          {:else if isTyping}
            <!-- Stop icon -->
            <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
              <rect x="6" y="6" width="12" height="12" rx="1"></rect>
            </svg>
          {:else}
            <!-- Send icon -->
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 10l7-7m0 0l7 7m-7-7v18"></path>
            </svg>
          {/if}
        </button>
      </div>
      
      <p class="text-xs text-text-secondary mt-2 text-center">
        Presiona Enter para enviar, Shift + Enter para nueva línea
      </p>
    </div>
  {/if}
</div>

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
