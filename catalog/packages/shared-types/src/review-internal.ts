import { ReviewStatus } from './enums';

/**
 * Review model (internal - snake_case for database)
 * Used by backend repositories and services
 */
export interface Review {
    id: string;
    product_id: string;
    user_id: string;
    rating: number;
    content?: string | null;
    status: ReviewStatus;
    created_at: Date;
    updated_at: Date;
}

/**
 * Create review input (internal - snake_case)
 */
export interface CreateReviewInput {
    product_id: string;
    user_id: string;
    rating: number;
    content?: string | null;
    status?: ReviewStatus;
}

/**
 * Update review input (internal - snake_case)
 */
export interface UpdateReviewInput {
    rating?: number;
    content?: string | null;
    status?: ReviewStatus;
}

/**
 * Review query filters (internal - snake_case)
 */
export interface ReviewQueryFilters {
    product_id?: string;
    user_id?: string;
    status?: ReviewStatus;
    limit?: number;
    offset?: number;
}

