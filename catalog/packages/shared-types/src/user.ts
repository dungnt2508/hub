import { UserRole, SellerStatus } from './enums';

/**
 * User model (internal - snake_case for database)
 * Used by backend repositories and services
 */
export interface User {
    id: string;
    email: string;
    password_hash?: string;
    azure_id?: string;
    role: UserRole;
    seller_status?: SellerStatus | null;
    seller_approved_at?: Date | null;
    seller_approved_by?: string | null;
    seller_rejection_reason?: string | null;
    created_at: Date;
    updated_at: Date;
}

/**
 * Create user input (internal - snake_case)
 */
export interface CreateUserInput {
    email: string;
    password?: string;
    azure_id?: string;
    role?: UserRole;
}

/**
 * Seller application (internal - snake_case)
 */
export interface SellerApplication {
    id: string;
    user_id: string;
    application_data?: Record<string, any>;
    status: SellerStatus;
    reviewed_at?: Date | null;
    reviewed_by?: string | null;
    rejection_reason?: string | null;
    created_at: Date;
    updated_at: Date;
}

