import { UserRole } from './enums';

/**
 * JWT payload (internal)
 */
export interface JWTPayload {
    userId: string;
    email: string;
    role?: UserRole;
}

/**
 * Login input (internal)
 */
export interface LoginInput {
    email: string;
    password: string;
}

/**
 * Register input (internal)
 */
export interface RegisterInput {
    email: string;
    password: string;
}

/**
 * Chat message (internal)
 */
export interface ChatMessage {
    role: 'user' | 'assistant' | 'system';
    content: string;
}

/**
 * Chat request (internal)
 */
export interface ChatRequest {
    messages: ChatMessage[];
    stream?: boolean;
}

