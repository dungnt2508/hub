/**
 * Product Review Audit Log types
 */

export type ReviewAuditAction = 'approved' | 'rejected' | 'requested_changes' | 'flagged';

/**
 * Product Review Audit Log (internal - snake_case from DB)
 */
export interface ProductReviewAuditLog {
    id: string;
    product_id: string;
    reviewer_id: string;
    action: ReviewAuditAction;
    review_status_before: string | null;
    review_status_after: string | null;
    reason: string | null;
    checklist_items: Record<string, any>;
    notes: string | null;
    created_at: Date;
}

/**
 * Product Review Audit Log DTO (API response - camelCase)
 */
export interface ProductReviewAuditLogDto {
    id: string;
    productId: string;
    reviewerId: string;
    action: ReviewAuditAction;
    reviewStatusBefore: string | null;
    reviewStatusAfter: string | null;
    reason: string | null;
    checklistItems: Record<string, any>;
    notes: string | null;
    createdAt: string;
}

/**
 * Create Product Review Audit Log input
 */
export interface CreateProductReviewAuditLogInput {
    product_id: string;
    reviewer_id: string;
    action: ReviewAuditAction;
    review_status_before?: string | null;
    review_status_after?: string | null;
    reason?: string | null;
    checklist_items?: Record<string, any>;
    notes?: string | null;
}

