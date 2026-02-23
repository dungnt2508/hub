/**
 * Summary model (internal - snake_case for database)
 * Used by backend repositories and services
 */
export interface Summary {
    id: string;
    article_id: string;
    summary_text: string;
    insights_json: any[]; // Array of insights
    data_points_json: any[]; // Array of data points
    created_at: Date;
}

/**
 * Create summary input (internal - snake_case)
 */
export interface CreateSummaryInput {
    article_id: string;
    summary_text: string;
    insights_json?: any[];
    data_points_json?: any[];
}

