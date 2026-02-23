/**
 * Standard API response structure
 */
export interface ApiResponse<T> {
    error: boolean;
    data?: T;
    message?: string;
    code?: string;
    details?: Record<string, any>;
    requestId?: string;
}

/**
 * Paginated response structure
 */
export interface PaginatedResponse<T> {
    items: T[];
    total: number;
    limit: number;
    offset: number;
}

