import { writable } from 'svelte/store';
import type { ChatState, Chat, Message } from '../types';

const initialChatState: ChatState = {
  currentChat: null,
  chats: [],
  isLoading: false,
  error: null
};

export const chatStore = writable<ChatState>(initialChatState);

export const chatActions = {
  setLoading: (isLoading: boolean) => {
    chatStore.update(state => ({ ...state, isLoading }));
  },

  setError: (error: string | null) => {
    chatStore.update(state => ({ ...state, error }));
  },

  setChats: (chats: Chat[]) => {
    chatStore.update(state => ({ ...state, chats }));
  },

  setCurrentChat: (chat: Chat | null) => {
    chatStore.update(state => ({ ...state, currentChat: chat }));
  },

  addChat: (chat: Chat) => {
    chatStore.update(state => ({
      ...state,
      chats: [chat, ...state.chats],
      currentChat: chat
    }));
  },

  updateChat: (chatId: string, updates: Partial<Chat>) => {
    chatStore.update(state => ({
      ...state,
      chats: state.chats.map(chat => 
        chat.id === chatId ? { ...chat, ...updates } : chat
      ),
      currentChat: state.currentChat?.id === chatId 
        ? { ...state.currentChat, ...updates }
        : state.currentChat
    }));
  },

  addMessage: (message: Message) => {
    console.log(`Adding ${message.role} message to store:`);
    console.log('   Message ID:', message.id);
    console.log('   Message content:', message.content.substring(0, 30) + '...');
    chatStore.update(state => {
      const updatedChats = state.chats.map(chat => {
        if (chat.id === message.chatId) {
          // Check if message already exists to prevent duplicates
          const messageExists = chat.messages.some(existingMsg => existingMsg.id === message.id);
          if (messageExists) {
            console.log('Message already exists, skipping:', message.id);
            return chat; // Don't add duplicate
          }

          return { ...chat, messages: [...chat.messages, message], updatedAt: new Date() };
        }
        return chat;
      });
      
      const updatedCurrentChat = state.currentChat?.id === message.chatId
        ? (() => {
            // Check if message already exists in current chat
            const messageExists = state.currentChat.messages.some(existingMsg => existingMsg.id === message.id);
            if (messageExists) {
              console.log('Message already exists in current chat, skipping:', message.id);
              return state.currentChat; // Don't add duplicate
            }

            return { ...state.currentChat, messages: [...state.currentChat.messages, message], updatedAt: new Date() };
          })()
        : state.currentChat;

      return {
        ...state,
        chats: updatedChats,
        currentChat: updatedCurrentChat
      };
    });
  },

  removeChat: (chatId: string) => {
    chatStore.update(state => ({
      ...state,
      chats: state.chats.filter(chat => chat.id !== chatId),
      currentChat: state.currentChat?.id === chatId ? null : state.currentChat
    }));
  },

  updateMessage: (messageId: string, updates: Partial<Message>) => {
    chatStore.update(state => {
      const updatedChats = state.chats.map(chat => ({
        ...chat,
        messages: chat.messages.map(message =>
          message.id === messageId ? { ...message, ...updates } : message
        )
      }));

      const updatedCurrentChat = state.currentChat ? {
        ...state.currentChat,
        messages: state.currentChat.messages.map(message =>
          message.id === messageId ? { ...message, ...updates } : message
        )
      } : null;

      return {
        ...state,
        chats: updatedChats,
        currentChat: updatedCurrentChat
      };
    });
  },

  clearChats: () => {
    chatStore.update(state => ({
      ...state,
      chats: [],
      currentChat: null
    }));
  }
};
