<script lang="ts">
  import { formatTime } from '../utils';
  import type { Message } from '../types';
  import { authStore } from '../stores';
  import logoImage from '../assets/logo_alpha_transp.png';
  import { onDestroy } from 'svelte';
  import { marked } from 'marked';

  interface Props {
    message: Message;
  }

  let { message }: Props = $props();

  const isUser = $derived(message.role === 'user');
  const isAssistant = $derived(message.role === 'assistant');
  const isSystem = $derived(message.role === 'system');
  const isStreaming = $derived(message.isStreaming || false);
  const userInitial = $derived($authStore.user?.username?.charAt(0).toUpperCase() || 'U');

  // Variables para el efecto typewriter
  let displayedContent = $state('');
  let typewriterInterval: ReturnType<typeof setInterval> | null = null;
  let currentIndex = $state(0);
  let isTypewriterActive = $state(false);
  let previousContentLength = $state(0);

  // Configuración del typewriter
  const TYPEWRITER_SPEED = 15; // ms por carácter (más bajo = más rápido)

  function startOrContinueTypewriter(targetContent: string) {
    // Si ya hay un typewriter activo, solo actualizar el objetivo
    if (isTypewriterActive) {
      return; // El interval ya está corriendo y usará el contenido actualizado
    }

    isTypewriterActive = true;
    currentIndex = displayedContent.length;
    
    typewriterInterval = setInterval(() => {
      const currentTarget = message.content; // Siempre usar el contenido más actual
      
      if (currentIndex < currentTarget.length) {
        displayedContent = currentTarget.substring(0, currentIndex + 1);
        currentIndex++;
      } else {
        // Hemos terminado de mostrar todo el contenido disponible
        if (typewriterInterval) {
          clearInterval(typewriterInterval);
          typewriterInterval = null;
        }
        isTypewriterActive = false;
      }
    }, TYPEWRITER_SPEED);
  }

  // Efecto que solo observa el contenido del mensaje
  $effect(() => {
    const content = message.content;
    const contentLength = content.length;
    
    // Si es un mensaje de usuario o sistema, mostrar inmediatamente
    if (!isAssistant) {
      displayedContent = content;
      previousContentLength = contentLength;
      return;
    }
    
    // Para mensajes del asistente
    if (contentLength === 0) {
      // Mensaje vacío, resetear
      displayedContent = '';
      previousContentLength = 0;
      return;
    }
    
    // Si es la primera vez o el contenido creció
    if (contentLength > previousContentLength) {
      previousContentLength = contentLength;
      
      // Si el contenido es nuevo (primera vez) y viene con streaming
      if (displayedContent === '' && isStreaming) {
        startOrContinueTypewriter(content);
      }
      // Si ya hay contenido mostrado pero llegó más contenido
      else if (displayedContent.length > 0 && contentLength > displayedContent.length) {
        startOrContinueTypewriter(content);
      }
      // Si no está en streaming, mostrar todo inmediatamente
      else if (!isStreaming) {
        displayedContent = content;
      }
    }
  });

  onDestroy(() => {
    if (typewriterInterval) {
      clearInterval(typewriterInterval);
      typewriterInterval = null;
    }
  });

  function copyToClipboard() {
    navigator.clipboard.writeText(message.content);
  }

  // Configurar marked para renderizado seguro
  marked.setOptions({
    breaks: true, // Convertir saltos de línea simples en <br>
    gfm: true,    // GitHub Flavored Markdown
  });

  // Función para renderizar markdown de forma segura
  function formatContent(content: string): string {
    if (!isAssistant) return content;
    
    try {
      // Usar marked para parsear el markdown
      const htmlContent = marked.parse(content) as string;
      
      // Aplicar clases de Tailwind a los elementos HTML generados
      return htmlContent
        // Encabezados
        .replace(/<h1>/g, '<h1 class="text-2xl font-bold text-text mt-4 mb-3">')
        .replace(/<h2>/g, '<h2 class="text-xl font-semibold text-text mt-4 mb-2">')
        .replace(/<h3>/g, '<h3 class="text-lg font-semibold text-text mt-4 mb-2">')
        .replace(/<h4>/g, '<h4 class="text-base font-semibold text-text mt-4 mb-2">')
        .replace(/<h5>/g, '<h5 class="text-sm font-semibold text-text mt-4 mb-2">')
        .replace(/<h6>/g, '<h6 class="text-xs font-semibold text-text-secondary mt-4 mb-2">')
        
        // Bloques de código
        .replace(/<pre><code/g, '<pre class="bg-surface border border-border rounded-md p-3 my-2 overflow-x-auto"><code class="text-sm font-mono"')
        .replace(/<code>/g, '<code class="bg-surface border border-border px-1.5 py-0.5 rounded text-sm font-mono">')
        
        // Párrafos
        .replace(/<p>/g, '<p class="mb-2">')
        
        // Listas
        .replace(/<ul>/g, '<ul class="list-disc list-inside ml-4 mb-2">')
        .replace(/<ol>/g, '<ol class="list-decimal list-inside ml-4 mb-2">')
        .replace(/<li>/g, '<li class="mb-1">')
        
        // Enlaces
        .replace(/<a href/g, '<a class="text-primary hover:text-primary-600 underline" target="_blank" rel="noopener noreferrer" href')
        
        // Texto en negrita y cursiva
        .replace(/<strong>/g, '<strong class="font-semibold">')
        .replace(/<em>/g, '<em class="italic">');
        
    } catch (error) {
      console.error('Error parsing markdown:', error);
      // Fallback: retornar el contenido sin procesar
      return content.replace(/\n/g, '<br>');
    }
  }
</script>

<div class="flex {isUser ? 'justify-end' : 'justify-start'} {isSystem ? 'justify-center' : ''}">
  <div class="{isUser ? 'max-w-xs lg:max-w-md xl:max-w-lg' : 'w-full'}">
    {#if isSystem}
      <!-- System Message -->
      <div class="text-center py-2">
        <span class="text-xs text-text-secondary bg-surface px-3 py-1 rounded-full border border-border">
          {message.content}
        </span>
      </div>
    {:else}
      <!-- User/Assistant Message -->
      {#if isUser}
        <!-- User Message - Keep bubble format -->
        <div class="flex flex-row-reverse space-x-2 space-x-reverse">
          <!-- Avatar -->
          <div class="flex-shrink-0">
            <div class="w-8 h-8 bg-primary text-white rounded-full flex items-center justify-center text-sm font-medium">
              {userInitial}
            </div>
          </div>

          <!-- Message Bubble -->
          <div class="group">
            <div class="bg-primary text-white rounded-2xl px-4 py-3 shadow-sm rounded-br-md">
              <div class="text-sm leading-relaxed">
                {message.content}
              </div>
            </div>
            
            <!-- Message Info -->
            <div class="flex items-center justify-end mt-1 space-x-2 opacity-0 group-hover:opacity-100 transition-opacity">
              <span class="text-xs text-text-secondary">
                {formatTime(message.timestamp)}
              </span>
              
              <!-- Copy button -->
              <button
                onclick={copyToClipboard}
                class="text-text-secondary hover:text-primary text-xs p-1 rounded transition-colors cursor-pointer"
                aria-label="Copiar mensaje"
              >
                <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"></path>
                </svg>
              </button>
            </div>
          </div>
        </div>
      {:else}
        <!-- Assistant Message - Plain text format -->
        <div class="flex flex-row space-x-3 w-full">
          <!-- Avatar -->
          <div class="flex-shrink-0">
            <div class="w-8 h-8 rounded-full flex items-center justify-center bg-white">
              <img src={logoImage} alt="TAI Chatbot Logo" class="w-7 h-7 object-contain" />
            </div>
          </div>

          <!-- Message Content - Plain text -->
          <div class="group flex-1 min-w-0">
            <div class="text-text leading-relaxed markdown-content">
              {@html formatContent(isAssistant ? displayedContent : message.content)}
            </div>
            
            <!-- Message Info -->
            <div class="flex items-center justify-start mt-2 space-x-2 opacity-0 group-hover:opacity-100 transition-opacity">
              <span class="text-xs text-text-secondary">
                {formatTime(message.timestamp)}
              </span>
              
              <!-- Copy button -->
              <button
                onclick={copyToClipboard}
                class="text-text-secondary hover:text-primary text-xs p-1 rounded transition-colors cursor-pointer"
                aria-label="Copiar mensaje"
              >
                <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"></path>
                </svg>
              </button>
            </div>
          </div>
        </div>
      {/if}
    {/if}
  </div>
</div>

<style>
  :global(.group:hover .opacity-0) {
    opacity: 1;
  }
  
  /* Estilos para contenido markdown */
  :global(.markdown-content) {
    line-height: 1.6;
  }
  
  :global(.markdown-content h1:first-child),
  :global(.markdown-content h2:first-child),
  :global(.markdown-content h3:first-child),
  :global(.markdown-content h4:first-child),
  :global(.markdown-content h5:first-child),
  :global(.markdown-content h6:first-child) {
    margin-top: 0;
  }
  
  :global(.markdown-content p:last-child) {
    margin-bottom: 0;
  }
  
  :global(.markdown-content pre) {
    white-space: pre-wrap;
    word-wrap: break-word;
  }
  
  :global(.markdown-content blockquote) {
    border-left: 4px solid var(--color-border);
    padding-left: 1rem;
    margin: 1rem 0;
    font-style: italic;
    color: var(--color-text-secondary);
  }
</style>
