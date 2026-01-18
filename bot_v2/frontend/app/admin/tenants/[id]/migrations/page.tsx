'use client';

import { useQuery } from '@tanstack/react-query';
import { migrationsApi, tenantsApi } from '@/lib/api';
import { MainLayout } from '@/components/layout/main-layout';
import { useParams } from 'next/navigation';
import { formatDate } from '@/lib/utils';
import { useState } from 'react';

export default function MigrationsPage() {
  const params = useParams();
  const tenantId = params.id as string;
  const [selectedStatus, setSelectedStatus] = useState<string>('');

  const { data: tenant } = useQuery({
    queryKey: ['tenant', tenantId],
    queryFn: () => tenantsApi.get(tenantId),
    enabled: !!tenantId,
  });

  const { data: migrations, isLoading, error } = useQuery({
    queryKey: ['migrations', tenantId, selectedStatus],
    queryFn: () => migrationsApi.list(tenantId, { status: selectedStatus || undefined }),
    enabled: !!tenantId,
  });

  if (isLoading) {
    return (
      <MainLayout>
        <div className="flex items-center justify-center h-64">
          <p className="text-gray-500">Đang tải...</p>
        </div>
      </MainLayout>
    );
  }

  if (error) {
    return (
      <MainLayout>
        <div className="flex items-center justify-center h-64">
          <p className="text-red-500">Lỗi: {String(error)}</p>
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              Migrations - {tenant?.name || 'Tenant'}
            </h1>
            <p className="text-sm text-gray-500 mt-1">Quản lý migration jobs</p>
          </div>
        </div>

        <div className="flex gap-4">
          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Tất cả status</option>
            <option value="pending">Pending</option>
            <option value="processing">Processing</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
          </select>
        </div>

        <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Source Type
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Ngày tạo
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Ngày cập nhật
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {migrations?.map((migration) => (
                <tr key={migration.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">
                      {migration.source_type}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={`px-2 py-1 text-xs font-semibold rounded-full ${
                        migration.status === 'completed'
                          ? 'bg-green-100 text-green-800'
                          : migration.status === 'failed'
                          ? 'bg-red-100 text-red-800'
                          : migration.status === 'processing'
                          ? 'bg-blue-100 text-blue-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      {migration.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {formatDate(migration.created_at)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {formatDate(migration.updated_at)}
                  </td>
                </tr>
              ))}
              {(!migrations || migrations.length === 0) && (
                <tr>
                  <td colSpan={4} className="px-6 py-4 text-center text-sm text-gray-500">
                    Không có migration nào
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </MainLayout>
  );
}
