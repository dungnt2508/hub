interface ChatRecommendation {
  productId: string;
  title: string;
  match: number;
  reason: string;
}

interface ChatResponse {
  understanding: string;
  recommendations: ChatRecommendation[];
  clarifyingQuestion?: string;
  suggestPills: string[];
}

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  recommendations?: ChatRecommendation[];
}

class ChatService {
  private baseUrl = process.env.NEXT_PUBLIC_API_URL || '/api';

  /**
   * Get product recommendations based on user query
   */
  async getRecommendations(
    query: string,
    limit: number = 3
  ): Promise<ChatResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/chat/recommendations`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query, limit }),
      });

      if (!response.ok) {
        throw new Error('Failed to get recommendations');
      }

      const data = await response.json();
      return data.data;
    } catch (error) {
      console.error('Error getting recommendations:', error);
      throw error;
    }
  }

  /**
   * Send chat message and get response
   */
  async sendMessage(message: string, conversationId?: string): Promise<ChatResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/chat/message`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message, conversationId }),
      });

      if (!response.ok) {
        throw new Error('Failed to send message');
      }

      const data = await response.json();
      return data.data;
    } catch (error) {
      console.error('Error sending message:', error);
      throw error;
    }
  }

  /**
   * Get chat history
   */
  async getChatHistory(conversationId: string): Promise<ChatMessage[]> {
    try {
      const response = await fetch(`${this.baseUrl}/chat/history/${conversationId}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to get chat history');
      }

      const data = await response.json();
      return data.data;
    } catch (error) {
      console.error('Error getting chat history:', error);
      return [];
    }
  }

  /**
   * Capture lead email
   */
  async captureLead(email: string, conversationId?: string): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/chat/lead`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, conversationId }),
      });

      if (!response.ok) {
        throw new Error('Failed to capture lead');
      }
    } catch (error) {
      console.error('Error capturing lead:', error);
      throw error;
    }
  }

  /**
   * Get popular categories
   */
  async getPopularCategories(): Promise<string[]> {
    try {
      const response = await fetch(`${this.baseUrl}/chat/categories`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to get categories');
      }

      const data = await response.json();
      return data.data;
    } catch (error) {
      console.error('Error getting categories:', error);
      return ['Email Marketing', 'CRM', 'Social Media', 'Data Sync'];
    }
  }

  /**
   * Search products
   */
  async searchProducts(
    query: string,
    limit: number = 5
  ): Promise<any[]> {
    try {
      const response = await fetch(`${this.baseUrl}/chat/search`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query, limit }),
      });

      if (!response.ok) {
        throw new Error('Failed to search products');
      }

      const data = await response.json();
      return data.data;
    } catch (error) {
      console.error('Error searching products:', error);
      return [];
    }
  }

  /**
   * Generate unique conversation ID
   */
  generateConversationId(): string {
    return `conv_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Save conversation to localStorage
   */
  saveConversationToLocal(conversationId: string, messages: ChatMessage[]): void {
    try {
      localStorage.setItem(
        `chat_${conversationId}`,
        JSON.stringify({
          conversationId,
          messages,
          savedAt: new Date().toISOString(),
        })
      );
    } catch (error) {
      console.error('Error saving conversation:', error);
    }
  }

  /**
   * Load conversation from localStorage
   */
  loadConversationFromLocal(conversationId: string): ChatMessage[] | null {
    try {
      const data = localStorage.getItem(`chat_${conversationId}`);
      if (!data) return null;

      const { messages } = JSON.parse(data);
      return messages.map((msg: any) => ({
        ...msg,
        timestamp: new Date(msg.timestamp),
      }));
    } catch (error) {
      console.error('Error loading conversation:', error);
      return null;
    }
  }

  /**
   * Clear conversation from localStorage
   */
  clearConversationFromLocal(conversationId: string): void {
    try {
      localStorage.removeItem(`chat_${conversationId}`);
    } catch (error) {
      console.error('Error clearing conversation:', error);
    }
  }
}

export const chatService = new ChatService();

