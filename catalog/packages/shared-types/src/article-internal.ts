import { ArticleStatus, SourceType } from './enums';

/**
 * Article model (internal - snake_case for database)
 * Used by backend repositories and services
 */
export interface Article {
    id: string;
    url?: string; // Kept for backward compatibility, but source_value is preferred
    title?: string;
    fetched_at?: Date;
    summary?: string; // Simple summary
    source?: string; // Source name/origin
    source_type: SourceType;
    source_value: string; // URL or file path
    raw_text?: string;
    metadata?: Record<string, any>;
    user_id: string;
    workflow_id?: string;
    status: ArticleStatus;
    created_at: Date;
}

/**
 * Create article input (internal - snake_case)
 */
export interface CreateArticleInput {
    user_id: string;
    source_type: SourceType;
    source_value: string;
    title?: string;
    url?: string; // Optional
    metadata?: Record<string, any>;
}

