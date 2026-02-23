/**
 * Product Artifact types
 * Represents files/artifacts associated with products
 */

export type ArtifactType = 
    | 'workflow_json'
    | 'readme'
    | 'env_example'
    | 'source_zip'
    | 'manifest'
    | 'install_script'
    | 'test_scripts'
    | 'screenshot'
    | 'thumbnail'
    | 'other';

/**
 * Product Artifact (internal - snake_case from DB)
 */
export interface ProductArtifact {
    id: string;
    product_id: string;
    artifact_type: ArtifactType;
    file_name: string;
    file_url: string;
    file_size: number | null;
    mime_type: string | null;
    checksum: string | null;
    version: string | null;
    is_primary: boolean;
    metadata: Record<string, any>;
    created_at: Date;
    updated_at: Date;
}

/**
 * Product Artifact DTO (API response - camelCase)
 */
export interface ProductArtifactDto {
    id: string;
    productId: string;
    artifactType: ArtifactType;
    fileName: string;
    fileUrl: string;
    fileSize: number | null;
    mimeType: string | null;
    checksum: string | null;
    version: string | null;
    isPrimary: boolean;
    metadata: Record<string, any>;
    createdAt: string;
    updatedAt: string;
}

/**
 * Create Product Artifact input
 */
export interface CreateProductArtifactInput {
    product_id: string;
    artifact_type: ArtifactType;
    file_name: string;
    file_url: string;
    file_size?: number;
    mime_type?: string;
    checksum?: string;
    version?: string;
    is_primary?: boolean;
    metadata?: Record<string, any>;
}

/**
 * Update Product Artifact input
 */
export interface UpdateProductArtifactInput {
    artifact_type?: ArtifactType;
    file_name?: string;
    file_url?: string;
    file_size?: number;
    mime_type?: string;
    checksum?: string;
    version?: string;
    is_primary?: boolean;
    metadata?: Record<string, any>;
}

