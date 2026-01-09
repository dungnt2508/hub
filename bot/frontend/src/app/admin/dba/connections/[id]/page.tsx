'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import AdminLayout from '@/components/AdminLayout';
import dbaConnectionsService, { DatabaseConnection } from '@/services/dba-connections.service';
import { ArrowLeft, Save, Play } from 'lucide-react';
import toast from 'react-hot-toast';
import Link from 'next/link';
import { useMutation } from '@tanstack/react-query';

export default function EditConnectionPage() {
  const router = useRouter();
  const params = useParams();
  const connectionId = params.id as string;
  const [loading, setLoading] = useState(true);
  const [connection, setConnection] = useState<DatabaseConnection | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    db_type: 'postgresql',
    connection_string: '',
    description: '',
    environment: '',
    tags: '',
    status: 'active',
  });

  useEffect(() => {
    if (connectionId) {
      fetchConnection();
    }
  }, [connectionId]);

  const fetchConnection = async () => {
    try {
      setLoading(true);
      const data = await dbaConnectionsService.getConnection(connectionId);
      setConnection(data);
      setFormData({
        name: data.name || '',
        db_type: data.db_type || 'postgresql',
        connection_string: '', // Don't show encrypted string
        description: data.description || '',
        environment: data.environment || '',
        tags: data.tags?.join(', ') || '',
        status: data.status || 'active',
      });
    } catch (error: any) {
      toast.error(error.message || 'Không thể tải connection');
      router.push('/admin/dba/connections');
    } finally {
      setLoading(false);
    }
  };

  const updateMutation = useMutation({
    mutationFn: (data: any) => dbaConnectionsService.updateConnection(connectionId, data),
    onSuccess: () => {
      toast.success('Đã cập nhật connection');
      router.push('/admin/dba/connections');
    },
    onError: (error: any) => {
      toast.error(error.message || 'Không thể cập nhật connection');
    },
  });

  const testMutation = useMutation({
    mutationFn: () => dbaConnectionsService.testConnection(connectionId),
    onSuccess: (data) => {
      if (data.success) {
        toast.success('Connection test thành công');
      } else {
        toast.error(data.message || 'Connection test thất bại');
      }
      fetchConnection();
    },
    onError: (error: any) => {
      toast.error(error.message || 'Connection test lỗi');
    },
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.name) {
      toast.error('Vui lòng điền đầy đủ thông tin bắt buộc');
      return;
    }

    updateMutation.mutate({
      ...formData,
      tags: formData.tags ? formData.tags.split(',').map(t => t.trim()) : [],
      connection_string: formData.connection_string || undefined, // Only update if provided
    });
  };

  if (loading) {
    return (
      <AdminLayout>
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-600 dark:text-gray-400">Đang tải...</div>
        </div>
      </AdminLayout>
    );
  }

  if (!connection) {
    return null;
  }

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
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Chỉnh Sửa Connection</h1>
              <p className="mt-2 text-gray-600 dark:text-gray-400">
                {connection.name}
              </p>
            </div>
          </div>
          <button
            onClick={() => testMutation.mutate()}
            disabled={testMutation.isPending}
            className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
          >
            <Play className="h-5 w-5 mr-2" />
            {testMutation.isPending ? 'Đang test...' : 'Test Connection'}
          </button>
        </div>

        {connection.last_error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
            <div className="text-sm text-red-800 dark:text-red-400">
              <strong>Last Error:</strong> {connection.last_error}
            </div>
          </div>
        )}

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
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Database Type
              </label>
              <select
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
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Connection String (để trống nếu không muốn thay đổi)
              </label>
              <textarea
                value={formData.connection_string}
                onChange={(e) => setFormData({ ...formData, connection_string: e.target.value })}
                placeholder="Nhập connection string mới nếu muốn thay đổi..."
                rows={3}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent font-mono text-sm"
              />
              <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                Connection string hiện tại đã được encrypt. Nhập connection string mới nếu muốn thay đổi.
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Description
              </label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
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
                  Status
                </label>
                <select
                  value={formData.status}
                  onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                >
                  <option value="active">Active</option>
                  <option value="inactive">Inactive</option>
                  <option value="error">Error</option>
                </select>
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

            {connection.last_tested_at && (
              <div className="text-sm text-gray-500 dark:text-gray-400">
                Last tested: {new Date(connection.last_tested_at).toLocaleString('vi-VN')}
              </div>
            )}

            <div className="flex items-center justify-end space-x-4 pt-4 border-t border-gray-200 dark:border-gray-700">
              <Link
                href="/admin/dba/connections"
                className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              >
                Hủy
              </Link>
              <button
                type="submit"
                disabled={updateMutation.isPending}
                className="flex items-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Save className="h-5 w-5 mr-2" />
                {updateMutation.isPending ? 'Đang lưu...' : 'Lưu Thay Đổi'}
              </button>
            </div>
          </div>
        </form>
      </div>
    </AdminLayout>
  );
}

