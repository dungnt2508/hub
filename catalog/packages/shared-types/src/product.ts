import { ProductType, ProductStatus, ProductReviewStatus, ProductStockStatus, ProductPriceType } from './enums';

/**
 * Product DTO (API response format - camelCase)
 */
export interface ProductDto {
    id: string;
    sellerId: string;
    title: string;
    description: string;
    longDescription?: string;
    type: ProductType;
    tags: string[];
    workflowFileUrl?: string;
    thumbnailUrl?: string;
    previewImageUrl?: string;
    videoUrl?: string;
    contactChannel?: string;
    isFree: boolean;
    price?: number;
    currency?: string;
    priceType?: ProductPriceType;
    stockStatus?: ProductStockStatus;
    stockQuantity?: number | null;
    status: ProductStatus;
    reviewStatus: ProductReviewStatus;
    reviewedAt?: string | null;
    reviewedBy?: string | null;
    rejectionReason?: string | null;
    downloads: number;
    rating: number;
    reviewsCount: number;
    version?: string;
    requirements: string[];
    features: string[];
    installGuide?: string;
    metadata: Record<string, any>;
    // Phase 1 new fields
    changelog?: string;
    license?: string;
    authorContact?: string;
    supportUrl?: string;
    screenshots?: string[];
    platformRequirements?: Record<string, any>;
    requiredCredentials?: string[];
    ownershipDeclaration?: boolean;
    ownershipProofUrl?: string;
    termsAcceptedAt?: string | null;
    securityScanStatus?: string;
    securityScanResult?: Record<string, any>;
    securityScanAt?: string | null;
    createdAt: string;
    updatedAt: string;
}

/**
 * Create product DTO (input)
 */
export interface CreateProductDto {
    title: string;
    description: string;
    longDescription?: string;
    type: ProductType;
    tags?: string[];
    workflowFileUrl?: string;
    thumbnailUrl?: string;
    previewImageUrl?: string;
    videoUrl?: string;
    contactChannel?: string;
    isFree: boolean;
    price?: number;
    currency?: string;
    priceType?: ProductPriceType;
    stockStatus?: ProductStockStatus;
    stockQuantity?: number | null;
    version?: string;
    requirements?: string[];
    features?: string[];
    installGuide?: string;
    metadata?: Record<string, any>;
    // Phase 1 new fields
    changelog?: string;
    license?: string;
    authorContact?: string;
    supportUrl?: string;
    screenshots?: string[];
    platformRequirements?: Record<string, any>;
    requiredCredentials?: string[];
    ownershipDeclaration?: boolean;
    ownershipProofUrl?: string;
}

/**
 * Update product DTO (input)
 */
export interface UpdateProductDto {
    title?: string;
    description?: string;
    longDescription?: string;
    type?: ProductType;
    tags?: string[];
    workflowFileUrl?: string;
    thumbnailUrl?: string;
    previewImageUrl?: string;
    videoUrl?: string;
    contactChannel?: string;
    isFree?: boolean;
    price?: number;
    currency?: string;
    priceType?: ProductPriceType;
    stockStatus?: ProductStockStatus;
    stockQuantity?: number | null;
    version?: string;
    requirements?: string[];
    features?: string[];
    installGuide?: string;
    metadata?: Record<string, any>;
    // Phase 1 new fields
    changelog?: string;
    license?: string;
    authorContact?: string;
    supportUrl?: string;
    screenshots?: string[];
    platformRequirements?: Record<string, any>;
    requiredCredentials?: string[];
    ownershipDeclaration?: boolean;
    ownershipProofUrl?: string;
}

/**
 * Product filters for querying
 */
export interface ProductFilters {
    type?: ProductType;
    search?: string;
    tags?: string[];
    sellerId?: string;
    priceType?: ProductPriceType;
    isFree?: boolean;
    limit?: number;
    offset?: number;
    sortBy?: 'created_at' | 'rating' | 'downloads';
    sortOrder?: 'asc' | 'desc';
    // Legacy snake_case support (for backward compatibility)
    seller_id?: string;
    price_type?: ProductPriceType;
    is_free?: boolean;
    sort_by?: 'created_at' | 'rating' | 'downloads';
    sort_order?: 'asc' | 'desc';
}

/**
 * Products response with pagination
 */
export interface ProductsResponse {
    products: ProductDto[];
    total: number;
    limit: number;
    offset: number;
}

