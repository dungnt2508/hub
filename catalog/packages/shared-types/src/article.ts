import { ArticleStatus, SourceType } from './enums';

/**
 * Article DTO (API response format)
 */
export interface ArticleDto {
    id: string;
    userId: string;
    sourceType: SourceType;
    sourceValue: string;
    url?: string;
    title?: string;
    fetchedAt?: string;
    summary?: string;
    source?: string;
    rawText?: string;
    metadata?: Record<string, any>;
    workflowId?: string;
    status: ArticleStatus;
    createdAt: string;
    updatedAt: string;
}

/**
 * Create article DTO (input)
 */
export interface CreateArticleDto {
    url?: string;
    sourceType: SourceType;
    sourceValue?: string;
    title?: string;
    metadata?: Record<string, any>;
}

