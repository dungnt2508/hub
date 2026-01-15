import { ProductType, ProductStatus, ProductReviewStatus, ProductPriceType, ProductStockStatus } from './enums';

/**
 * Product model (internal - snake_case for database)
 * Used by backend repositories and services
 */
export interface Product {
    id: string;
    seller_id: string;
    title: string;
    description: string;
    long_description?: string;
    type: ProductType;
    tags: string[];
    workflow_file_url?: string;
    thumbnail_url?: string;
    preview_image_url?: string;
    video_url?: string;
    contact_channel?: string;
    is_free: boolean;
    price?: number;
    currency?: string;
    price_type?: ProductPriceType;
    stock_status?: ProductStockStatus;
    stock_quantity?: number | null;
    status: ProductStatus;
    review_status: ProductReviewStatus;
    reviewed_at?: Date | null;
    reviewed_by?: string | null;
    rejection_reason?: string | null;
    downloads: number;
    sales_count?: number;
    rating: number;
    reviews_count: number;
    version?: string;
    requirements: string[];
    features: string[];
    install_guide?: string;
    metadata: Record<string, any>;
    // Phase 1 new fields
    changelog?: string;
    license?: string;
    author_contact?: string;
    support_url?: string;
    screenshots?: string[];
    platform_requirements?: Record<string, any>;
    required_credentials?: string[];
    ownership_declaration?: boolean;
    ownership_proof_url?: string;
    terms_accepted_at?: Date | null;
    security_scan_status?: string;
    security_scan_result?: Record<string, any>;
    security_scan_at?: Date | null;
    created_at: Date;
    updated_at: Date;
}

/**
 * Create product input (internal - snake_case)
 */
export interface CreateProductInput {
    seller_id: string;
    title: string;
    description: string;
    long_description?: string;
    type: ProductType;
    tags?: string[];
    workflow_file_url?: string;
    thumbnail_url?: string;
    preview_image_url?: string;
    video_url?: string;
    contact_channel?: string;
    is_free: boolean;
    price?: number;
    currency?: string;
    price_type?: ProductPriceType;
    stock_status?: ProductStockStatus;
    stock_quantity?: number | null;
    status?: ProductStatus;
    version?: string;
    requirements?: string[];
    features?: string[];
    install_guide?: string;
    metadata?: Record<string, any>;
    // Phase 1 new fields
    changelog?: string;
    license?: string;
    author_contact?: string;
    support_url?: string;
    screenshots?: string[];
    platform_requirements?: Record<string, any>;
    required_credentials?: string[];
    ownership_declaration?: boolean;
    ownership_proof_url?: string;
    terms_accepted_at?: Date | null;
}

/**
 * Update product input (internal - snake_case)
 */
export interface UpdateProductInput {
    title?: string;
    description?: string;
    long_description?: string;
    type?: ProductType;
    tags?: string[];
    workflow_file_url?: string;
    thumbnail_url?: string;
    preview_image_url?: string;
    video_url?: string;
    contact_channel?: string;
    is_free?: boolean;
    price?: number;
    currency?: string;
    price_type?: ProductPriceType;
    stock_status?: ProductStockStatus;
    stock_quantity?: number | null;
    status?: ProductStatus;
    version?: string;
    requirements?: string[];
    features?: string[];
    install_guide?: string;
    metadata?: Record<string, any>;
    // Phase 1 new fields
    changelog?: string;
    license?: string;
    author_contact?: string;
    support_url?: string;
    screenshots?: string[];
    platform_requirements?: Record<string, any>;
    required_credentials?: string[];
    ownership_declaration?: boolean;
    ownership_proof_url?: string;
    terms_accepted_at?: Date | null;
}

/**
 * Product query filters (internal - snake_case)
 */
export interface ProductQueryFilters {
    type?: ProductType;
    status?: ProductStatus;
    review_status?: ProductReviewStatus;
    is_free?: boolean;
    seller_id?: string;
    search?: string;
    tags?: string[];
    limit?: number;
    offset?: number;
    sort_by?: 'created_at' | 'rating' | 'downloads' | 'price' | 'sales_count';
    price_type?: ProductPriceType;
    sort_order?: 'asc' | 'desc';
}

