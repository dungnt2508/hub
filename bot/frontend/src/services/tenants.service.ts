import { apiClient } from '@/shared/api/client';

export interface Tenant {
  id: string;
  name: string;
  plan: string;
  web_embed_enabled: boolean;
  web_embed_origins: string[];
  telegram_enabled: boolean;
  teams_enabled: boolean;
  rate_limit_per_hour: number;
  rate_limit_per_day: number;
  created_at?: string;
  updated_at?: string;
}

export interface CreateTenantRequest {
  name: string;
  web_embed_origins: string[];
  plan?: string;
  telegram_enabled?: boolean;
  teams_enabled?: boolean;
}

export interface UpdateTenantRequest {
  name?: string;
  plan?: string;
  web_embed_enabled?: boolean;
  web_embed_origins?: string[];
  telegram_enabled?: boolean;
  teams_enabled?: boolean;
}

const tenantsService = {
  async listTenants(params?: { limit?: number; offset?: number }) {
    return await apiClient.get('/api/admin/v1/tenants', { params });
  },

  async getTenant(tenantId: string) {
    return await apiClient.get(`/api/admin/v1/tenants/${tenantId}`);
  },

  async createTenant(data: CreateTenantRequest) {
    return await apiClient.post('/api/admin/v1/tenants', data);
  },

  async updateTenant(tenantId: string, data: UpdateTenantRequest) {
    return await apiClient.put(`/api/admin/v1/tenants/${tenantId}`, data);
  },
};

export default tenantsService;

