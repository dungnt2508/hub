/**
 * Product Workflow types
 * Type-specific data for workflow products
 */

/**
 * Product Workflow (internal - snake_case from DB)
 */
export interface ProductWorkflow {
    id: string;
    product_id: string;
    n8n_version: string | null;
    workflow_json_url: string | null;
    env_example_url: string | null;
    readme_url: string | null;
    workflow_file_checksum: string | null;
    nodes_count: number | null;
    triggers: string[];
    credentials_required: string[];
    created_at: Date;
    updated_at: Date;
}

/**
 * Product Workflow DTO (API response - camelCase)
 */
export interface ProductWorkflowDto {
    id: string;
    productId: string;
    n8nVersion: string | null;
    workflowJsonUrl: string | null;
    envExampleUrl: string | null;
    readmeUrl: string | null;
    workflowFileChecksum: string | null;
    nodesCount: number | null;
    triggers: string[];
    credentialsRequired: string[];
    createdAt: string;
    updatedAt: string;
}

/**
 * Create Product Workflow input
 */
export interface CreateProductWorkflowInput {
    product_id: string;
    n8n_version?: string;
    workflow_json_url?: string;
    env_example_url?: string;
    readme_url?: string;
    workflow_file_checksum?: string;
    nodes_count?: number;
    triggers?: string[];
    credentials_required?: string[];
}

/**
 * Update Product Workflow input
 */
export interface UpdateProductWorkflowInput {
    n8n_version?: string;
    workflow_json_url?: string;
    env_example_url?: string;
    readme_url?: string;
    workflow_file_checksum?: string;
    nodes_count?: number;
    triggers?: string[];
    credentials_required?: string[];
}

