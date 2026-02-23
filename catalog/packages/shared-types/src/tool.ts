import { ToolRequestStatus } from './enums';

/**
 * Tool request model (internal - snake_case for database)
 * Used by backend repositories and services
 */
export interface ToolRequest {
    id: string;
    user_id: string;
    request_payload: Record<string, any>;
    status: ToolRequestStatus;
    result?: Record<string, any>;
    workflow_id?: string;
    created_at: Date;
    updated_at: Date;
}

/**
 * Create tool request input (internal - snake_case)
 */
export interface CreateToolRequestInput {
    user_id: string;
    request_payload: Record<string, any>;
}

