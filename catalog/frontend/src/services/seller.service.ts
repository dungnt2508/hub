import { apiClient } from '@/shared/api/client';

export interface SellerStatus {
  status: 'pending' | 'approved' | 'rejected' | null;
  application: any;
  rejection_reason?: string | null;
}

class SellerService {
  /**
   * Request seller status
   */
  async requestSellerStatus(applicationData?: Record<string, any>): Promise<void> {
    await apiClient.post('/seller/apply', { application_data: applicationData });
  }

  /**
   * Get seller application status
   */
  async getApplicationStatus(): Promise<SellerStatus> {
    // apiClient.get() already unwraps response.data, so response is already the data
    const response = await apiClient.get<SellerStatus>('/seller/status');
    return response;
  }
}

export default new SellerService();

