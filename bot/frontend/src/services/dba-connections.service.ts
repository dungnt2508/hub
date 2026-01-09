import { apiClient } from '@/shared/api/client';

export interface DatabaseConnection {
  connection_id: string;
  name: string;
  db_type: string;
  description?: string;
  environment?: string;
  tags?: string[];
  status: string;
  last_tested_at?: string;
  last_error?: string;
  created_by?: string;
  tenant_id?: string;
  created_at: string;
  updated_at: string;
}

export interface CreateConnectionRequest {
  name: string;
  db_type: string;
  connection_string: string;
  description?: string;
  environment?: string;
  tags?: string[];
  tenant_id?: string;
}

export interface UpdateConnectionRequest {
  name?: string;
  db_type?: string;
  connection_string?: string;
  description?: string;
  environment?: string;
  tags?: string[];
  status?: string;
}

const dbaConnectionsService = {
  async listConnections(params?: {
    db_type?: string;
    tenant_id?: string;
    environment?: string;
    status?: string;
  }) {
    return await apiClient.get('/api/admin/v1/dba/connections', { params });
  },

  async getConnection(connectionId: string) {
    return await apiClient.get(`/api/admin/v1/dba/connections/${connectionId}`);
  },

  async createConnection(data: CreateConnectionRequest) {
    return await apiClient.post('/api/admin/v1/dba/connections', data);
  },

  async updateConnection(connectionId: string, data: UpdateConnectionRequest) {
    return await apiClient.put(`/api/admin/v1/dba/connections/${connectionId}`, data);
  },

  async deleteConnection(connectionId: string) {
    await apiClient.delete(`/api/admin/v1/dba/connections/${connectionId}`);
  },

  async testConnection(connectionId: string) {
    return await apiClient.post(`/api/admin/v1/dba/connections/${connectionId}/test`);
  },

  async testConnectionString(dbType: string, connectionString: string) {
    return await apiClient.post('/api/admin/v1/dba/connections/test', {
      db_type: dbType,
      connection_string: connectionString,
    });
  },
};

export default dbaConnectionsService;

