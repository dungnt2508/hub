import { apiClient } from '@/shared/api/client';

/**
 * DBA Use Cases Service
 * 
 * Service for managing DBA use cases - metadata-driven, no hardcoding
 */

export interface UseCaseMetadata {
  id: string;
  name: string;
  description: string;
  icon: string;
  intent: string;
  required_slots: string[];
  optional_slots: string[];
  source_allowed: string[];
  playbook_name?: string;
  tags?: string[];
  param_schema?: Record<string, any>;
  editable_query_schema?: Record<string, any>;
  output_schema?: Record<string, any>;
  execution_limits?: {
    timeout_seconds?: number;
    max_rows?: number;
    max_execution_time_ms?: number;
  };
  capability_flags?: {
    can_edit_query?: boolean;
    can_export?: boolean;
    can_schedule?: boolean;
    requires_approval?: boolean;
  };
  query_templates?: {
    playbook_name: string;
    templates_by_db: Record<string, Array<{
      step_number: number;
      purpose: string;
      read_only: boolean;
      description?: string;
      query_text?: string; // SQL query text for review
    }>>;
  };
}

export interface UseCaseListResponse {
  status: string;
  total: number;
  use_cases: UseCaseMetadata[];
}

export interface UseCaseDetailResponse {
  status: string;
  use_case: UseCaseMetadata;
}

export interface ExecuteUseCaseRequest {
  use_case_id: string;
  connection_id: string;
  params: Record<string, any>;
  query_overrides?: Record<string, string>; // step_number -> query_text
}

export interface ExecuteUseCaseResponse {
  status: string;
  pipeline?: {
    risk_assessment?: any;
    execution_plan?: any;
    execution_results?: any;
    interpretation?: any;
  };
}

class DBAUseCasesService {
  private baseUrl = '/api/dba';

  /**
   * Get all use cases
   */
  async listUseCases(): Promise<UseCaseMetadata[]> {
    try {
      const response = await apiClient.get<UseCaseListResponse>(
        `${this.baseUrl}/use-cases`
      );
      return response.use_cases || [];
    } catch (error: any) {
      throw new Error(`Failed to load use cases: ${error.message}`);
    }
  }

  /**
   * Get detailed metadata for a specific use case
   */
  async getUseCaseDetail(useCaseId: string): Promise<UseCaseMetadata> {
    try {
      const response = await apiClient.get<UseCaseDetailResponse>(
        `${this.baseUrl}/use-cases/${useCaseId}`
      );
      return response.use_case;
    } catch (error: any) {
      throw new Error(`Failed to load use case detail: ${error.message}`);
    }
  }

  /**
   * Execute a use case
   */
  async executeUseCase(
    request: ExecuteUseCaseRequest
  ): Promise<ExecuteUseCaseResponse> {
    try {
      const params = new URLSearchParams({
        connection_id: request.connection_id,
        use_case: request.use_case_id,
      });

      // Note: params and query_overrides would need to be sent in body
      // For now, we'll use the existing execute-playbook endpoint
      const response = await apiClient.post<ExecuteUseCaseResponse>(
        `${this.baseUrl}/execute-playbook?${params.toString()}`,
        {
          params: request.params,
          query_overrides: request.query_overrides,
        }
      );
      return response;
    } catch (error: any) {
      throw new Error(`Failed to execute use case: ${error.message}`);
    }
  }
}

export default new DBAUseCasesService();

