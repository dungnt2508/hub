import { SourceType } from './enums';

/**
 * Fetch schedule model (internal - snake_case for database)
 * Used by backend repositories and services
 */
export interface FetchSchedule {
    id: string;
    user_id: string;
    article_url?: string; // Deprecated
    source_type: SourceType;
    source_value: string;
    frequency: string; // 'daily', 'weekly', etc.
    last_fetched?: Date;
    next_fetch: Date;
    workflow_id?: string;
    active: boolean;
}

/**
 * Create schedule input (internal - snake_case)
 */
export interface CreateScheduleInput {
    user_id: string;
    source_type: SourceType;
    source_value: string;
    frequency: string;
}

