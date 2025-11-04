import type { Chat, Message } from '../types';
import { get } from 'svelte/store';
import { configStore } from '../stores/config';
import { authService } from '../auth/AuthService';
import { auth } from '../auth/authStore';
import { apiRequest } from './api';

export interface SendMessageRequest {
  content: string;
  chatId?: string;
}

export interface CreateChatRequest {
  title?: string;
  username?: string;
}

class ChatService {
  private ws: WebSocket | null = null;
  private messageHandlers: Set<(message: Message) => void> = new Set();
  private pendingTimeouts: Map<string, number> = new Map();
  private abortController: AbortController | null = null;
  private streamingMessages: Map<string, Message> = new Map(); // Para rastrear mensajes en streaming
  private streamingUpdateHandlers: Set<(message: Message) => void> = new Set();

  private get config() {
    return get(configStore);
  }

  private get wsUrl(): string {
    // Convertir HTTP URL a WebSocket URL
    return this.config.wsUrl;
  }

  // Función para transformar datos del backend al formato del frontend
  private transformBackendChatToFrontend(backendChat: any): Chat {
    return {
      id: String(backendChat.id), // Convertir número a string
      title: backendChat.title,
      userId: backendChat.username, // username -> userId
      messages: (backendChat.messages || []).map((msg: any) => ({
        id: String(msg.id),
        content: msg.content,
        role: this.transformRole(msg.role), // Transformar roles del backend
        timestamp: new Date(msg.timestamp || msg.created_at),
        userId: msg.user_id || msg.username || (this.transformRole(msg.role) === 'assistant' ? 'assistant' : 'user'),
        chatId: String(backendChat.id),
        metadata: msg.metadata
      })),
      createdAt: new Date(backendChat.created_at), // created_at -> createdAt
      updatedAt: new Date(backendChat.updated_at), // updated_at -> updatedAt
      isActive: backendChat.is_active // is_active -> isActive
    };
  }

  // Función para transformar roles del backend al frontend
  private transformRole(backendRole: string): 'user' | 'assistant' | 'system' {
    switch (backendRole) {
      case 'human':
        return 'user';
      case 'ai':
        return 'assistant';
      case 'system':
        return 'system';
      default:
        return backendRole as 'user' | 'assistant' | 'system';
    }
  }

  // HTTP API methods
  async getChats(): Promise<Chat[]> {
    // Obtener el usuario logueado del store de autenticación
    const currentUser = auth.getUser();
    const username = currentUser?.username;

    if (!username) {
      throw new Error('Usuario no autenticado');
    }

    const backendChats = await apiRequest<any[]>(`/chat?includes=messages&order_by=updated_at&order=DESC&username=${encodeURIComponent(username)}`, {
      method: 'GET'
    });
    
    // Transformar los datos del backend al formato del frontend
    return backendChats.map(chat => this.transformBackendChatToFrontend(chat));
  }

  async getChat(chatId: string): Promise<Chat> {

    const backendChat = await apiRequest<any>(`/chat/${chatId}?includes=messages`, {
      method: 'GET'
    });
    
    return this.transformBackendChatToFrontend(backendChat);
  }

  async createChat(data: CreateChatRequest): Promise<Chat> {

    const backendChat = await apiRequest<any>('/chat', {
      method: 'POST',
      body: JSON.stringify(data)
    });
    
    return this.transformBackendChatToFrontend(backendChat);
  }

    async deleteChat(chatId: string): Promise<void> {
    
    await apiRequest(`/streaming/chat/context/${chatId}`, {
      method: 'DELETE'
    });

    await apiRequest(`/chat/${chatId}`, {
      method: 'DELETE'
    });

  }

  async updateChatTitle(chatId: string, title: string): Promise<Chat> {
    // Update the title in the backend
    await apiRequest<any>(`/chat/${chatId}`, {
      method: 'PATCH',
      body: JSON.stringify({ title })
    });
    
    // Fetch the updated chat to get the complete object
    const updatedBackendChat = await apiRequest<any>(`/chat/${chatId}`);
    return this.transformBackendChatToFrontend(updatedBackendChat);
  }

  // WebSocket methods for real-time chat
  connectWebSocket(chatId: string): void {

    console.log('Attempting to connect WebSocket for chat:', chatId);

    const token = authService.getToken();
    if (!token) {
      console.error('No authentication token for WebSocket');
      throw new Error('No authentication token');
    }

    this.disconnectWebSocket();

    // Use the new streaming WebSocket endpoint
    const wsUrl = `${this.wsUrl}/${chatId}?token=${token}`;
    
    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      console.log('✅ WebSocket connected to streaming endpoint for chat:', chatId);
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        // Handle different types of streaming messages
        if (data.type === 'connection_established') {
          // Handle connection established message
          console.log('✅ WebSocket connection established');

        } else if (data.type === 'pong') {
          console.log('🔄 Received pong');

        } else if (data.type === 'ping') {
          console.log('🔄 Received ping');

        } else if (data.type === 'message_received') {
          console.log('✅ Message received by backend');

        } else if (data.type === 'assistant_response_start') {
          // Handle AI starting to answer
          console.log('AI answering');

        } else if (data.type === 'assistant_response_error') {
          console.error('❌ Streaming error:', data.error);

        } else if (data.type === 'AIMessageChunk') {
          // Use a consistent ID for the streaming message for this chat
          const messageId = data.id;
          let streamingMessage = this.streamingMessages.get(messageId);
          
          if (!streamingMessage) {
            // Create new streaming message
            streamingMessage = {
              id: messageId,
              content: data.content,
              role: 'assistant',
              timestamp: new Date(),
              userId: 'assistant',
              chatId: chatId,
              isStreaming: true
            };
            this.streamingMessages.set(messageId, streamingMessage);
            // Notify as new message
            this.messageHandlers.forEach(handler => handler(streamingMessage!));
          } else {
            // Update existing streaming message
            streamingMessage.content += data.content;
            // Notify streaming update handlers
            this.streamingUpdateHandlers.forEach(handler => handler(streamingMessage!));
          }

        } else if (data.type === 'assistant_response_complete') {
          console.log('🤖✅ Assistant response complete:', data.data);
          
          // Find the streaming message for this chat
          const messageId = data.data.id;
          const streamingMessage = this.streamingMessages.get(messageId);

          if (streamingMessage) {
            // Simply update the streaming message to mark it as complete
            this.streamingUpdateHandlers.forEach(handler => handler({
              ...streamingMessage,
              content: data.data.content, // Use final content from backend
              isStreaming: false
            }));
            
            // Remove from streaming messages
            this.streamingMessages.delete(messageId);
          } else {
            // Fallback: create new message if no streaming message found
            const assistantMessage: Message = {
              id: String(data.data.id),
              content: data.data.content,
              role: 'assistant',
              timestamp: new Date(),
              userId: 'assistant',
              chatId: chatId
            };
            this.messageHandlers.forEach(handler => handler(assistantMessage));
          }

        } else {
          console.log('🔄 Other WebSocket message type:', data.type, data);
        }
      } catch (error) {
        console.error('❌ Failed to parse WebSocket message:', error, 'Raw data:', event.data);
      }
    };

    this.ws.onclose = (event) => {
      console.log('❌ WebSocket disconnected. Code:', event.code, 'Reason:', event.reason);
    };

    this.ws.onerror = (error) => {
      console.error('❌ WebSocket error:', error);
    };
  }

  disconnectWebSocket(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  sendMessage(message: SendMessageRequest): void {

    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      throw new Error('WebSocket not connected');
    }

    this.ws.send(JSON.stringify({
      type: 'message',
      data: message
    }));
  }

  cancelPendingOperations(): void {
    // Cancel all pending timeouts
    this.pendingTimeouts.forEach((timeoutId, chatId) => {
      clearTimeout(timeoutId);
      console.log('Cancelled pending operation for chat:', chatId);
    });
    this.pendingTimeouts.clear();

    // Cancel any pending HTTP requests
    if (this.abortController) {
      this.abortController.abort();
      this.abortController = null;
    }
  }

  onMessage(handler: (message: Message) => void): () => void {
    this.messageHandlers.add(handler);
    return () => this.messageHandlers.delete(handler);
  }

  onStreamingUpdate(handler: (message: Message) => void): () => void {
    this.streamingUpdateHandlers.add(handler);
    return () => this.streamingUpdateHandlers.delete(handler);
  }

  async sendMessageHttp(data: SendMessageRequest): Promise<Message> {

    // Use the new streaming endpoint for real implementation
    if (!data.chatId) {
      throw new Error('Chat ID is required');
    }

    // Send message to backend first to get the real ID from database
    try {
      const response = await apiRequest<any>('/streaming/chat/send', {
        method: 'POST',
        body: JSON.stringify({
          chat_id: parseInt(data.chatId), // Convert to integer
          content: data.content
        })
      });

      // The response contains: { user_id, msg_id, connections_notified, chat_id }
      // We need to create the user message with the real ID from the database
      const userMessage: Message = {
        id: String(response.msg_id), // Use the real ID from database
        content: data.content,
        role: 'user',
        timestamp: new Date(),
        userId: response.user_id,
        chatId: String(response.chat_id)
      };

      // Notify handlers about user message (so it appears in UI)
      this.messageHandlers.forEach(handler => handler(userMessage));

      // Note: The assistant response will come via WebSocket streaming
      // or we could fetch the updated chat to get the complete conversation

      return userMessage;
    } catch (error) {
      console.error('Failed to send message to backend:', error);
      throw error;
    }
  }
}

export const chatService = new ChatService();
