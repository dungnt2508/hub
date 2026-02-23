/**
 * Shared enums used across frontend and backend
 */

export enum UserRole {
    USER = 'user',
    SELLER = 'seller',
    ADMIN = 'admin',
}

export enum SellerStatus {
    PENDING = 'pending',
    APPROVED = 'approved',
    REJECTED = 'rejected',
}

export enum ProductType {
    WORKFLOW = 'workflow',
    TOOL = 'tool',
    INTEGRATION = 'integration',
}

export enum ProductStatus {
    DRAFT = 'draft',
    PUBLISHED = 'published',
    ARCHIVED = 'archived',
}

export enum ProductReviewStatus {
    PENDING = 'pending',
    APPROVED = 'approved',
    REJECTED = 'rejected',
}

export enum ArticleStatus {
    PENDING = 'pending',
    PROCESSING = 'processing',
    DONE = 'done',
    FAILED = 'failed',
}

export enum SourceType {
    URL = 'url',
    RSS = 'rss',
    FILE = 'file',
}

export enum ToolRequestStatus {
    PENDING = 'pending',
    PROCESSING = 'processing',
    DONE = 'done',
    FAILED = 'failed',
}

export enum ProductPriceType {
    FREE = 'free',
    ONETIME = 'onetime',
    SUBSCRIPTION = 'subscription',
}

export enum ProductStockStatus {
    IN_STOCK = 'in_stock',
    OUT_OF_STOCK = 'out_of_stock',
    UNKNOWN = 'unknown',
}

export enum ReviewStatus {
    PENDING = 'pending',
    APPROVED = 'approved',
    REJECTED = 'rejected',
}

