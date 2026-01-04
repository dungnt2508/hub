import { apiClient } from '@/shared/api/client';

// Types
export interface PatternRule {
  id: string;
  tenant_id?: string;
  rule_name: string;
  enabled: boolean;
  pattern_regex: string;
  pattern_flags: string;
  target_domain: string;
  target_intent?: string;
  intent_type?: string;
  slots_extraction?: Record<string, any>;
  priority: number;
  scope: string;
  scope_filter?: Record<string, any>;
  description?: string;
  version: number;
  created_by?: string;
  created_at: string;
  updated_at: string;
}

export interface PatternRuleCreate {
  tenant_id?: string;
  rule_name: string;
  enabled?: boolean;
  pattern_regex: string;
  pattern_flags?: string;
  target_domain: string;
  target_intent?: string;
  intent_type?: string;
  slots_extraction?: Record<string, any>;
  priority?: number;
  scope?: string;
  scope_filter?: Record<string, any>;
  description?: string;
}

export interface KeywordHint {
  id: string;
  tenant_id?: string;
  rule_name: string;
  enabled: boolean;
  domain: string;
  keywords: Record<string, number>;
  scope: string;
  scope_filter?: Record<string, any>;
  description?: string;
  created_by?: string;
  created_at: string;
  updated_at: string;
}

export interface RoutingRule {
  id: string;
  tenant_id?: string;
  rule_name: string;
  enabled: boolean;
  intent_pattern: Record<string, any>;
  target_domain?: string;
  target_agent?: string;
  target_workflow?: Record<string, any>;
  priority: number;
  fallback_chain?: Array<Record<string, any>>;
  scope: string;
  scope_filter?: Record<string, any>;
  description?: string;
  version: number;
  created_by?: string;
  created_at: string;
  updated_at: string;
}

export interface PromptTemplate {
  id: string;
  tenant_id?: string;
  template_name: string;
  template_type: string;
  domain?: string;
  agent?: string;
  enabled: boolean;
  template_text: string;
  variables?: Record<string, any>;
  version: number;
  is_active: boolean;
  description?: string;
  created_by?: string;
  created_at: string;
  updated_at: string;
}

export interface TestSandboxRequest {
  message: string;
  tenant_id?: string;
  user_context?: Record<string, any>;
}

export interface TestSandboxResponse {
  routing_result: {
    domain: string;
    intent?: string;
    intent_type?: string;
    confidence: number;
    source: string;
    status: string;
  };
  trace: {
    trace_id: string;
    spans: Array<{
      step: string;
      input?: any;
      output?: any;
      duration_ms?: number;
      score?: number;
      decision_source?: string;
    }>;
  };
  configs_used: Array<{
    step: string;
    source: string;
    score?: number;
  }>;
}

export interface AuditLog {
  id: string;
  tenant_id?: string;
  config_type: string;
  config_id: string;
  config_name?: string;
  changed_by: string;
  changed_by_email?: string;
  action: string;
  old_value?: Record<string, any>;
  new_value?: Record<string, any>;
  diff?: Record<string, any>;
  changed_at: string;
  reason?: string;
}

class AdminConfigService {
  private baseUrl = '/api/admin/v1';

  // ==================== Authentication ====================
  async login(email: string, password: string) {
    const response = await apiClient.post<{ user: any; token: string; expires_in: number }>(
      `${this.baseUrl}/auth/login`,
      { email, password }
    );
    return response;
  }

  async getCurrentUser() {
    return apiClient.get(`${this.baseUrl}/auth/me`);
  }

  // ==================== Pattern Rules ====================
  async listPatternRules(params?: {
    tenant_id?: string;
    enabled?: boolean;
    limit?: number;
    offset?: number;
  }) {
    return apiClient.get<{ items: PatternRule[]; total: number; limit: number; offset: number }>(
      `${this.baseUrl}/pattern-rules`,
      { params }
    );
  }

  async getPatternRule(id: string) {
    return apiClient.get<PatternRule>(`${this.baseUrl}/pattern-rules/${id}`);
  }

  async createPatternRule(data: PatternRuleCreate) {
    return apiClient.post<PatternRule>(`${this.baseUrl}/pattern-rules`, data);
  }

  async updatePatternRule(id: string, data: Partial<PatternRuleCreate>) {
    return apiClient.put<PatternRule>(`${this.baseUrl}/pattern-rules/${id}`, data);
  }

  async deletePatternRule(id: string) {
    return apiClient.delete(`${this.baseUrl}/pattern-rules/${id}`);
  }

  async enablePatternRule(id: string) {
    return apiClient.patch<PatternRule>(`${this.baseUrl}/pattern-rules/${id}/enable`);
  }

  async disablePatternRule(id: string) {
    return apiClient.patch<PatternRule>(`${this.baseUrl}/pattern-rules/${id}/disable`);
  }

  // ==================== Keyword Hints ====================
  async listKeywordHints(params?: {
    tenant_id?: string;
    enabled?: boolean;
    limit?: number;
    offset?: number;
  }) {
    return apiClient.get<{ items: KeywordHint[]; total: number; limit: number; offset: number }>(
      `${this.baseUrl}/keyword-hints`,
      { params }
    );
  }

  async getKeywordHint(id: string) {
    return apiClient.get<KeywordHint>(`${this.baseUrl}/keyword-hints/${id}`);
  }

  async createKeywordHint(data: Partial<KeywordHint>) {
    return apiClient.post<KeywordHint>(`${this.baseUrl}/keyword-hints`, data);
  }

  async updateKeywordHint(id: string, data: Partial<KeywordHint>) {
    return apiClient.put<KeywordHint>(`${this.baseUrl}/keyword-hints/${id}`, data);
  }

  async deleteKeywordHint(id: string) {
    return apiClient.delete(`${this.baseUrl}/keyword-hints/${id}`);
  }

  // ==================== Routing Rules ====================
  async listRoutingRules(params?: {
    tenant_id?: string;
    enabled?: boolean;
    limit?: number;
    offset?: number;
  }) {
    return apiClient.get<{ items: RoutingRule[]; total: number; limit: number; offset: number }>(
      `${this.baseUrl}/routing-rules`,
      { params }
    );
  }

  async getRoutingRule(id: string) {
    return apiClient.get<RoutingRule>(`${this.baseUrl}/routing-rules/${id}`);
  }

  async createRoutingRule(data: Partial<RoutingRule>) {
    return apiClient.post<RoutingRule>(`${this.baseUrl}/routing-rules`, data);
  }

  async updateRoutingRule(id: string, data: Partial<RoutingRule>) {
    return apiClient.put<RoutingRule>(`${this.baseUrl}/routing-rules/${id}`, data);
  }

  async deleteRoutingRule(id: string) {
    return apiClient.delete(`${this.baseUrl}/routing-rules/${id}`);
  }

  // ==================== Prompt Templates ====================
  async listPromptTemplates(params?: {
    tenant_id?: string;
    template_type?: string;
    domain?: string;
    agent?: string;
    active_only?: boolean;
    limit?: number;
    offset?: number;
  }) {
    return apiClient.get<{ items: PromptTemplate[]; total: number; limit: number; offset: number }>(
      `${this.baseUrl}/prompt-templates`,
      { params }
    );
  }

  async getPromptTemplate(id: string) {
    return apiClient.get<PromptTemplate>(`${this.baseUrl}/prompt-templates/${id}`);
  }

  async createPromptTemplate(data: Partial<PromptTemplate>) {
    return apiClient.post<PromptTemplate>(`${this.baseUrl}/prompt-templates`, data);
  }

  async updatePromptTemplate(id: string, data: Partial<PromptTemplate>) {
    return apiClient.put<PromptTemplate>(`${this.baseUrl}/prompt-templates/${id}`, data);
  }

  async deletePromptTemplate(id: string) {
    return apiClient.delete(`${this.baseUrl}/prompt-templates/${id}`);
  }

  async listTemplateVersions(id: string) {
    return apiClient.get<Array<{ id: string; version: number; template_text: string; is_active: boolean; created_at: string }>>(
      `${this.baseUrl}/prompt-templates/${id}/versions`
    );
  }

  async rollbackTemplate(id: string, targetVersion: number) {
    return apiClient.post<PromptTemplate>(
      `${this.baseUrl}/prompt-templates/${id}/rollback?target_version=${targetVersion}`
    );
  }

  // ==================== Test Sandbox ====================
  async testSandbox(request: TestSandboxRequest) {
    return apiClient.post<TestSandboxResponse>(`${this.baseUrl}/test-sandbox`, request);
  }

  // ==================== Audit Logs ====================
  async listAuditLogs(params?: {
    tenant_id?: string;
    config_type?: string;
    config_id?: string;
    changed_by?: string;
    start_date?: string;
    end_date?: string;
    limit?: number;
    offset?: number;
  }) {
    return apiClient.get<{ items: AuditLog[]; total: number; limit: number; offset: number }>(
      `${this.baseUrl}/audit-logs`,
      { params }
    );
  }
}

export default new AdminConfigService();

