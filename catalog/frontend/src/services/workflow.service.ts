import { apiClient } from '@/shared/api/client';

export interface ProductWorkflow {
  id: string;
  productId: string;
  n8nVersion: string | null;
  workflowJsonUrl: string | null;
  envExampleUrl: string | null;
  readmeUrl: string | null;
  workflowFileChecksum: string | null;
  nodesCount: number | null;
  triggers: string[];
  credentialsRequired: string[];
  createdAt: string;
  updatedAt: string;
}

export interface CreateWorkflowDetailsInput {
  n8nVersion?: string;
  workflowJsonUrl?: string;
  envExampleUrl?: string;
  readmeUrl?: string;
}

class WorkflowService {
  /**
   * Create or update workflow details
   */
  async createOrUpdateWorkflowDetails(
    productId: string,
    data: CreateWorkflowDetailsInput
  ): Promise<ProductWorkflow> {
    const response = await apiClient.post<{ workflow: ProductWorkflow }>(
      `/products/${productId}/workflow-details`,
      {
        n8n_version: data.n8nVersion,
        workflow_json_url: data.workflowJsonUrl,
        env_example_url: data.envExampleUrl,
        readme_url: data.readmeUrl,
      }
    );
    return response.workflow;
  }

  /**
   * Get workflow details for a product
   */
  async getWorkflowDetails(productId: string): Promise<ProductWorkflow | null> {
    try {
      const response = await apiClient.get<{ workflow: ProductWorkflow }>(
        `/products/${productId}/workflow-details`
      );
      return response.workflow;
    } catch (error: any) {
      if (error.response?.status === 404) {
        return null;
      }
      throw error;
    }
  }
}

export default new WorkflowService();

