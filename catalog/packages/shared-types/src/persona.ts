/**
 * Persona model (internal - snake_case for database)
 * Used by backend repositories and services
 */
export interface Persona {
    id: string;
    user_id: string;
    language_style: string; // formal, casual, etc.
    tone: string; // witty, neutral, professional, etc.
    topics_interest: string[]; // Array of topics
    created_at: Date;
    updated_at: Date;
}

/**
 * Create persona input (internal - snake_case)
 */
export interface CreatePersonaInput {
    user_id: string;
    language_style: string;
    tone: string;
    topics_interest: string[];
}

/**
 * Update persona input (internal - snake_case)
 */
export interface UpdatePersonaInput {
    language_style?: string;
    tone?: string;
    topics_interest?: string[];
}

