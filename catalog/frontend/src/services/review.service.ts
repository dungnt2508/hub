import { apiClient } from '@/shared/api/client';
import { ReviewDto } from '@gsnake/shared-types';

export type Review = ReviewDto;

class ReviewService {
  async getProductReviews(productId: string, limit: number = 50, offset: number = 0): Promise<{ reviews: Review[]; total: number; limit: number; offset: number }> {
    const resp = await apiClient.get(`/reviews/product/${productId}?limit=${limit}&offset=${offset}`);
    return resp;
  }

  async createReview(productId: string, rating: number, content?: string): Promise<Review> {
    const resp = await apiClient.post<{ review: Review }>('/reviews', {
      product_id: productId,
      rating,
      content,
    });
    return resp.review;
  }

  async updateReview(id: string, rating?: number, content?: string): Promise<Review> {
    const resp = await apiClient.put<{ review: Review }>(`/reviews/${id}`, { rating, content });
    return resp.review;
  }

  async deleteReview(id: string): Promise<void> {
    await apiClient.delete(`/reviews/${id}`);
  }
}

export default new ReviewService();


