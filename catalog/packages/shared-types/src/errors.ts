/**
 * Error response structure
 */
export interface ErrorResponse {
    error: true;
    code: string;
    message: string;
    details?: Record<string, any>;
    requestId?: string;
}

/**
 * Common error codes
 */
export const ERROR_CODES = {
    // Auth errors
    INVALID_CREDENTIALS: 'INVALID_CREDENTIALS',
    EMAIL_ALREADY_EXISTS: 'EMAIL_ALREADY_EXISTS',
    INVALID_TOKEN: 'INVALID_TOKEN',
    TOKEN_EXPIRED: 'TOKEN_EXPIRED',
    AUTHENTICATION_REQUIRED: 'AUTHENTICATION_REQUIRED',
    
    // Authorization errors
    ADMIN_ACCESS_REQUIRED: 'ADMIN_ACCESS_REQUIRED',
    SELLER_ACCESS_REQUIRED: 'SELLER_ACCESS_REQUIRED',
    APPROVED_SELLER_REQUIRED: 'APPROVED_SELLER_REQUIRED',
    PRODUCT_UPDATE_FORBIDDEN: 'PRODUCT_UPDATE_FORBIDDEN',
    
    // Product errors
    PRODUCT_NOT_FOUND: 'PRODUCT_NOT_FOUND',
    SELLER_NOT_FOUND: 'SELLER_NOT_FOUND',
    PRODUCT_NOT_APPROVED: 'PRODUCT_NOT_APPROVED',
    
    // Validation errors
    INVALID_INPUT: 'INVALID_INPUT',
    VALIDATION_ERROR: 'VALIDATION_ERROR',
    
    // Internal errors
    INTERNAL_ERROR: 'INTERNAL_ERROR',
} as const;

export type ErrorCode = typeof ERROR_CODES[keyof typeof ERROR_CODES];

