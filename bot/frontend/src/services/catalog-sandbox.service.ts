/**
 * Catalog Sandbox Service - API calls for catalog domain testing
 */
import { apiClient } from '@/shared/api/client';

export interface CatalogQuery {
  question: string;
  tenant_id?: string;
}

export interface IntentClassificationResult {
  intent_type: 'PRODUCT_SEARCH' | 'PRODUCT_SPECIFIC_INFO' | 'PRODUCT_COMPARISON' | 'PRODUCT_COUNT';
  confidence: number;
  reason: string;
  extracted_info: Record<string, any>;
}

export interface CatalogQueryResponse {
  answer: string;
  intent_type: string;
  retrieval_method: 'vector_search' | 'hybrid_search' | 'db_query' | 'db_count';
  products_found: number;
  confidence: number;
  classification: IntentClassificationResult;
  sources?: Array<{
    title: string;
    excerpt?: string;
  }>;
}

class CatalogSandboxService {
  /**
   * Test catalog query with intent classification and hybrid search
   */
  async testQuery(request: CatalogQuery): Promise<CatalogQueryResponse> {
    try {
      const response = await apiClient.post<CatalogQueryResponse>(
        '/api/catalog/query',
        request
      );
      return response;
    } catch (error: any) {
      throw new Error(error.message || 'Failed to process catalog query');
    }
  }

  /**
   * Get intent classification result (without executing full pipeline)
   */
  async classifyIntent(question: string): Promise<IntentClassificationResult> {
    try {
      const response = await apiClient.post<IntentClassificationResult>(
        '/api/catalog/classify-intent',
        { question }
      );
      return response;
    } catch (error: any) {
      throw new Error(error.message || 'Failed to classify intent');
    }
  }

  /**
   * Test hybrid search with specific attribute
   */
  async testHybridSearch(attribute: string, limit: number = 5) {
    try {
      const response = await apiClient.post<any>(
        '/api/catalog/search/attribute',
        { attribute, limit }
      );
      return response;
    } catch (error: any) {
      throw new Error(error.message || 'Failed to test hybrid search');
    }
  }

  /**
   * Get catalog statistics
   */
  async getCatalogStats() {
    try {
      const response = await apiClient.get<any>('/api/catalog/stats');
      return response;
    } catch (error: any) {
      throw new Error(error.message || 'Failed to get catalog statistics');
    }
  }
}

export default new CatalogSandboxService();

