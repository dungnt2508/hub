'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import AdminLayout from '@/components/AdminLayout';
import dbaConnectionsService from '@/services/dba-connections.service';
import { ArrowLeft, Save, Play, CheckCircle, XCircle } from 'lucide-react';
import toast from 'react-hot-toast';
import Link from 'next/link';

export default function NewConnectionPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string; connection_info?: any } | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    db_type: 'postgresql',
    connection_string: '',
    description: '',
    environment: '',
    tags: '',
    tenant_id: '',
  });

  const handleTestConnection = async () => {
    if (!formData.connection_string) {
      toast.error('Vui lòng nhập connection string để test');
      return;
    }

    try {
      setTesting(true);
      setTestResult(null);
      const result = await dbaConnectionsService.testConnectionString(
        formData.db_type,
        formData.connection_string
      );
      setTestResult(result);
      if (result.success) {
        toast.success('Connection test thành công');
      } else {
        toast.error(result.message || 'Connection test thất bại');
      }
    } catch (error: any) {
      const errorMessage = error.message || 'Connection test lỗi';
      setTestResult({
        success: false,
        message: errorMessage,
      });
      toast.error(errorMessage);
    } finally {
      setTesting(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.name || !formData.connection_string) {
      toast.error('Vui lòng điền đầy đủ thông tin bắt buộc');
      return;
    }

    try {
      setLoading(true);
      await dbaConnectionsService.createConnection({
        ...formData,
        tags: formData.tags ? formData.tags.split(',').map(t => t.trim()) : [],
        tenant_id: formData.tenant_id || undefined,
      });
      toast.success('Đã tạo connection');
      router.push('/admin/dba/connections');
    } catch (error: any) {
      toast.error(error.message || 'Không thể tạo connection');
    } finally {
      setLoading(false);
    }
  };

  return (
    <AdminLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Link
              href="/admin/dba/connections"
              className="text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
            >
              <ArrowLeft className="h-5 w-5" />
            </Link>
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Tạo Connection</h1>
              <p className="mt-2 text-gray-600 dark:text-gray-400">
                Tạo mới database connection cho DBA domain
              </p>
            </div>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 p-6">
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Connection Name <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                required
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="e.g., SQL Server Production 01"
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Database Type <span className="text-red-500">*</span>
              </label>
              <select
                required
                value={formData.db_type}
                onChange={(e) => setFormData({ ...formData, db_type: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              >
                <option value="postgresql">PostgreSQL</option>
                <option value="mysql">MySQL</option>
                <option value="sqlserver">SQL Server</option>
                <option value="mongodb">MongoDB</option>
                <option value="oracle">Oracle</option>
              </select>
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Connection String <span className="text-red-500">*</span>
                </label>
                <button
                  type="button"
                  onClick={handleTestConnection}
                  disabled={testing || !formData.connection_string}
                  className="flex items-center px-3 py-1.5 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Play className="h-4 w-4 mr-1.5" />
                  {testing ? 'Đang test...' : 'Test Connection'}
                </button>
              </div>
              <textarea
                required
                value={formData.connection_string}
                onChange={(e) => {
                  setFormData({ ...formData, connection_string: e.target.value });
                  setTestResult(null); // Clear test result when connection string changes
                }}
                placeholder="e.g., mssql+pyodbc://user:pass@server:1433/db"
                rows={3}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent font-mono text-sm"
              />
              <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                Connection string sẽ được encrypt khi lưu vào database
              </p>
              
              {testResult && (
                <div className={`mt-3 p-3 rounded-lg border ${
                  testResult.success
                    ? 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800'
                    : 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800'
                }`}>
                  <div className="flex items-start">
                    {testResult.success ? (
                      <CheckCircle className="h-5 w-5 text-green-600 dark:text-green-400 mr-2 mt-0.5" />
                    ) : (
                      <XCircle className="h-5 w-5 text-red-600 dark:text-red-400 mr-2 mt-0.5" />
                    )}
                    <div className="flex-1">
                      <div className={`text-sm font-medium ${
                        testResult.success
                          ? 'text-green-800 dark:text-green-400'
                          : 'text-red-800 dark:text-red-400'
                      }`}>
                        {testResult.success ? 'Test thành công' : 'Test thất bại'}
                      </div>
                      <div className={`text-xs mt-1 ${
                        testResult.success
                          ? 'text-green-700 dark:text-green-300'
                          : 'text-red-700 dark:text-red-300'
                      }`}>
                        {testResult.message}
                      </div>
                      {testResult.success && testResult.connection_info && (
                        <div className="mt-2 text-xs text-green-700 dark:text-green-300">
                          <div>Database: {testResult.connection_info.database || 'N/A'}</div>
                          {testResult.connection_info.version && (
                            <div>Version: {testResult.connection_info.version}</div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Description
              </label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="Mô tả connection..."
                rows={2}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Environment
                </label>
                <select
                  value={formData.environment}
                  onChange={(e) => setFormData({ ...formData, environment: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                >
                  <option value="">Select environment</option>
                  <option value="production">Production</option>
                  <option value="staging">Staging</option>
                  <option value="development">Development</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Tenant ID (optional)
                </label>
                <input
                  type="text"
                  value={formData.tenant_id}
                  onChange={(e) => setFormData({ ...formData, tenant_id: e.target.value })}
                  placeholder="tenant-uuid"
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Tags (comma-separated)
              </label>
              <input
                type="text"
                value={formData.tags}
                onChange={(e) => setFormData({ ...formData, tags: e.target.value })}
                placeholder="e.g., production, sqlserver, critical"
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>

            <div className="flex items-center justify-end space-x-4 pt-4 border-t border-gray-200 dark:border-gray-700">
              <Link
                href="/admin/dba/connections"
                className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              >
                Hủy
              </Link>
              <button
                type="submit"
                disabled={loading}
                className="flex items-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Save className="h-5 w-5 mr-2" />
                {loading ? 'Đang tạo...' : 'Tạo Connection'}
              </button>
            </div>
          </div>
        </form>
      </div>
    </AdminLayout>
  );
}

