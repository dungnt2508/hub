import { ReviewStatus } from './enums';

/**
 * Review DTO (API response format - camelCase)
 */
export interface ReviewDto {
    id: string;
    productId: string;
    userId: string;
    rating: number;
    content?: string | null;
    status: ReviewStatus;
    createdAt: string;
    updatedAt: string;
}
