import { UserRole } from './enums';

/**
 * User DTO (API response format)
 */
export interface UserDto {
    id: string;
    email: string;
    role: UserRole;
    sellerStatus?: string | null;
    createdAt: string;
    updatedAt: string;
}

/**
 * Auth response DTO
 */
export interface AuthResponseDto {
    user: UserDto;
    token: string;
}

/**
 * Login DTO (input)
 */
export interface LoginDto {
    email: string;
    password: string;
}

/**
 * Register DTO (input)
 */
export interface RegisterDto {
    email: string;
    password: string;
}

