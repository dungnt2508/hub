import { apiClient } from '@/shared/api/client';

// Types for DBA Sandbox

export interface Connection {
  id: string;
  name: string;
  db_type: 'sql_server' | 'postgresql' | 'mysql' | 'mariadb';
  host: string;
  port: number;
  is_production: boolean;
  is_available: boolean;
  user_permissions?: string[];
}

export interface ConnectionValidationResult {
  connection_id: string;
  is_alive: boolean;
  db_type: string;
  is_production: boolean;
  user_permissions: string[];
  error?: string;
  duration_ms?: number;
}

export interface QuerySafetyResult {
  query: string;
  syntax_valid: boolean;
  sql_injection_safe: boolean;
  performance_acceptable: boolean;
  estimated_rows?: number;
  estimated_duration_ms?: number;
  sensitive_columns_found?: string[];
  warnings: string[];
  errors: string[];
  duration_ms?: number;
}

export interface FailureSimulationResult {
  scenario: string;
  simulated_error: string;
  handled_gracefully: boolean;
  error_message_quality: 'good' | 'acceptable' | 'poor';
  logged_for_debugging: boolean;
  suggestions: string[];
  duration_ms?: number;
}

export interface CheckResult {
  check_id: string;
  check_name: string;
  passed: boolean;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  message?: string;
  details?: Record<string, any>;
}

export interface GateCheck {
  gate_name: string;
  status: 'PASS' | 'BLOCK' | 'WARN';
  reason: string;
}

export interface RiskAssessmentResponse {
  final_decision: 'GO' | 'GO-WITH-CONDITIONS' | 'NO-GO';
  risk_level: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  decision_explanation: string;
  can_execute: boolean;
  gates: GateCheck[];
  critical_issues: string[];
  warnings: string[];
  checks_passed: Array<{ check_name: string }>;
  recommendations: string[];
  trace: {
    timestamp: string;
    duration_ms: number;
    steps: Array<{
      step: string;
      duration_ms: number;
      result: 'pass' | 'fail' | 'warn';
    }>;
  };
}

export interface UseCase {
  id: string;
  name: string;
  description: string;
  intent: string;
  required_slots: string[];
  optional_slots: string[];
  source_allowed: string[];
  icon: string;
}

export interface DBATestSandboxRequest {
  connection_id: string;
  scenario?: string;
  sql_query?: string;
  simulate_failures?: string[];
}

class DBASandboxService {
  private baseUrl = '/api/dba';

  /**
   * Run DBA risk assessment - shows gates, decision, and execution trace
   * 
   * Returns:
   * - final_decision: GO or NO-GO
   * - risk_level: CRITICAL, HIGH, MEDIUM, LOW
   * - gates: All 4 hard gates with status (PASS/BLOCK/WARN) and reason
   * - trace: Step-by-step execution checklist
   */
  async runRiskAssessment(
    request: DBATestSandboxRequest
  ): Promise<RiskAssessmentResponse> {
    try {
      const params = new URLSearchParams({
        connection_id: request.connection_id,
      });
      
      if (request.scenario) {
        params.append('use_case', request.scenario);
      }
      
      if (request.sql_query) {
        params.append('sql_query', request.sql_query);
      }
      
      const response = await apiClient.post<RiskAssessmentResponse>(
        `${this.baseUrl}/risk-assessment?${params.toString()}`,
        {}
      );
      return response;
    } catch (error: any) {
      throw new Error(`Risk assessment failed: ${error.message}`);
    }
  }

  /**
   * Validate database connection safety (legacy - for compatibility)
   */
  async validateConnection(connectionId: string): Promise<ConnectionValidationResult> {
    try {
      const response = await apiClient.post<ConnectionValidationResult>(
        `${this.baseUrl}/validate-connection`,
        { connection_id: connectionId }
      );
      return response;
    } catch (error: any) {
      throw new Error(`Connection validation failed: ${error.message}`);
    }
  }

  /**
   * Check SQL query safety (legacy - for compatibility)
   */
  async checkQuerySafety(
    connectionId: string,
    sqlQuery: string
  ): Promise<QuerySafetyResult> {
    try {
      const response = await apiClient.post<QuerySafetyResult>(
        `${this.baseUrl}/check-query-safety`,
        {
          connection_id: connectionId,
          sql_query: sqlQuery,
        }
      );
      return response;
    } catch (error: any) {
      throw new Error(`Query safety check failed: ${error.message}`);
    }
  }

  /**
   * Simulate failure scenario (legacy - for compatibility)
   */
  async simulateFailure(
    connectionId: string,
    scenario: string
  ): Promise<FailureSimulationResult> {
    try {
      const response = await apiClient.post<FailureSimulationResult>(
        `${this.baseUrl}/simulate-failure`,
        {
          connection_id: connectionId,
          scenario,
        }
      );
      return response;
    } catch (error: any) {
      throw new Error(`Failure simulation failed: ${error.message}`);
    }
  }

  /**
   * Get available connections from backend registry
   */
  async getConnections(): Promise<Connection[]> {
    try {
      const response = await apiClient.get<{ connections: Connection[] }>(
        `${this.baseUrl}/connections`
      );
      
      if (!response.connections || response.connections.length === 0) {
        // Return mock if no connections configured
        return [
          {
            id: 'dev-1',
            name: 'DEV_DB',
            db_type: 'sql_server',
            host: 'localhost',
            port: 1433,
            is_production: false,
            is_available: false,
            user_permissions: [],
          } as Connection,
        ];
      }
      
      return response.connections;
    } catch (error: any) {
      console.warn('Failed to load real connections, using defaults:', error.message);
      
      // Return sensible defaults if backend fails
      return [
        {
          id: 'dev-1',
          name: 'DEV_DB',
          db_type: 'sql_server',
          host: 'localhost',
          port: 1433,
          is_production: false,
          is_available: false,
          user_permissions: [],
        } as Connection,
      ];
    }
  }

  /**
   * Get connection details
   */
  async getConnection(connectionId: string): Promise<Connection> {
    try {
      const response = await apiClient.get<Connection>(
        `${this.baseUrl}/connections/${connectionId}`
      );
      return response;
    } catch (error: any) {
      throw new Error(`Failed to load connection: ${error.message}`);
    }
  }

  /**
   * Get available DBA use cases
   */
  async getUseCases(): Promise<UseCase[]> {
    try {
      const response = await apiClient.get<{ use_cases: UseCase[] }>(
        '/api/admin/v1/test-sandbox/dba/use-cases'
      );
      return response.use_cases || [];
    } catch (error: any) {
      throw new Error(`Failed to load use cases: ${error.message}`);
    }
  }

  /**
   * Execute full playbook pipeline (Risk → Plan → Execute → Interpret)
   * 
   * Returns complete pipeline result with:
   * - Risk Assessment (gates, decision)
   * - Execution Plan (structured SQL steps)
   * - Execution Results (raw database results)
   * - Interpretation (LLM analysis and findings)
   */
  async executePlaybook(
    connectionId: string,
    useCaseId: string
  ): Promise<any> {
    try {
      const params = new URLSearchParams({
        connection_id: connectionId,
        use_case: useCaseId,
      });
      
      const response = await apiClient.post<any>(
        `${this.baseUrl}/execute-playbook?${params.toString()}`,
        {}
      );
      return response;
    } catch (error: any) {
      throw new Error(`Playbook execution failed: ${error.message}`);
    }
  }

  /**
   * Get risk matrix
   */
  async getRiskMatrix(): Promise<any> {
    try {
      // This could be loaded from a static JSON file or API
      const response = await fetch('/admin/domain-sandboxes/dba/utils/dba-risk-matrix.json');
      const data = await response.json();
      return data.dba_sandbox;
    } catch (error: any) {
      throw new Error(`Failed to load risk matrix: ${error.message}`);
    }
  }
}

export default new DBASandboxService();
