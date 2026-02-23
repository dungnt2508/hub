import { apiClient } from '@/shared/api/client';

export interface DashboardStats {
  users: {
    total: number;
    sellers: number;
    pending_seller_applications: number;
  };
  products: {
    total: number;
    pending_review: number;
    published: number;
  };
}

export interface Seller {
  id: string;
  email: string;
  role: string;
  seller_status: string | null;
  seller_approved_at: string | null;
  seller_approved_by: string | null;
  seller_rejection_reason: string | null;
  created_at: string;
}

export interface SellerApplication {
  id: string;
  user_id: string;
  user?: {
    id: string;
    email: string;
    created_at: string;
  };
  application_data?: Record<string, any>;
  status: string;
  reviewed_at: string | null;
  reviewed_by: string | null;
  rejection_reason: string | null;
  created_at: string;
}

class AdminService {
  /**
   * Get dashboard statistics
   */
  async getDashboardStats(): Promise<DashboardStats> {
    // apiClient.get() already unwraps response.data, so response is already the data
    const response = await apiClient.get<DashboardStats>('/admin/dashboard');
    return response;
  }

  /**
   * Get all sellers
   */
  async getSellers(status?: string): Promise<Seller[]> {
    const params = status ? `?status=${status}` : '';
    // apiClient.get() already unwraps response.data, so response is already the data
    const response = await apiClient.get<{ sellers: Seller[] }>(`/admin/sellers${params}`);
    return response.sellers;
  }

  /**
   * Get all seller applications
   */
  async getSellerApplications(status?: string): Promise<SellerApplication[]> {
    const params = status ? `?status=${status}` : '';
    // apiClient.get() already unwraps response.data, so response is already the data
    const response = await apiClient.get<{ applications: SellerApplication[] }>(`/admin/seller-applications${params}`);
    return response.applications;
  }

  /**
   * Approve seller
   */
  async approveSeller(userId: string): Promise<Seller> {
    // apiClient.post() already unwraps response.data, so response is already the data
    const response = await apiClient.post<{ seller: Seller }>(`/admin/sellers/${userId}/approve`);
    return response.seller;
  }

  /**
   * Reject seller
   */
  async rejectSeller(userId: string, reason: string): Promise<Seller> {
    // apiClient.post() already unwraps response.data, so response is already the data
    const response = await apiClient.post<{ seller: Seller }>(`/admin/sellers/${userId}/reject`, { reason });
    return response.seller;
  }

  /**
   * Get products pending review
   */
  async getProductsPendingReview(limit: number = 50, offset: number = 0): Promise<{ products: any[] }> {
    // apiClient.get() already unwraps response.data, so response is already the data
    const response = await apiClient.get<{ products: any[] }>(`/admin/products/pending?limit=${limit}&offset=${offset}`);
    return response;
  }

  /**
   * Approve product
   */
  async approveProduct(productId: string) {
    // apiClient.post() already unwraps response.data, so response is already the data
    const response = await apiClient.post<{ product: any }>(`/admin/products/${productId}/approve`);
    return response.product;
  }

  /**
   * Reject product
   */
  async rejectProduct(productId: string, reason: string) {
    // apiClient.post() already unwraps response.data, so response is already the data
    const response = await apiClient.post<{ product: any }>(`/admin/products/${productId}/reject`, { reason });
    return response.product;
  }

  /**
   * Update user role
   */
  async updateUserRole(userId: string, role: 'user' | 'seller' | 'admin') {
    // apiClient.put() already unwraps response.data, so response is already the data
    const response = await apiClient.put<{ user: any }>(`/admin/users/${userId}/role`, { role });
    return response.user;
  }
}

export default new AdminService();

