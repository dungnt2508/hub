// Re-export shared types
export type { UserDto as User } from '@gsnake/shared-types';
export type { ArticleDto as Article } from '@gsnake/shared-types';
export { ArticleStatus, SourceType } from '@gsnake/shared-types';

// Local types (not shared with backend)
export interface Persona {
    id: string;
    user_id: string;
    language_style: string;
    tone: string;
    topics_interest: string[];
    created_at: string;
    updated_at: string;
}

export interface Schedule {
    id: string;
    user_id: string;
    article_url: string;
    frequency: 'daily' | 'weekly' | 'monthly';
    last_fetched?: string;
    next_fetch: string;
    workflow_id?: string;
}

export interface ToolRequest {
    id: string;
    user_id: string;
    request_payload: Record<string, any>;
    status: 'pending' | 'processing' | 'done' | 'failed';
    result?: Record<string, any>;
    workflow_id?: string;
    created_at: string;
    updated_at: string;
}

export interface ChatMessage {
    role: 'user' | 'assistant' | 'system';
    content: string;
}
