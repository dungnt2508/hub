'use client';

import { useQuery } from '@tanstack/react-query';
import { observabilityApi, tenantsApi } from '@/lib/api';
import { MainLayout } from '@/components/layout/main-layout';
import { useParams } from 'next/navigation';
import { formatDate } from '@/lib/utils';

export default function FailedQueriesPage() {
  const params = useParams();
  const tenantId = params.id as string;

  const { data: tenant } = useQuery({
    queryKey: ['tenant', tenantId],
    queryFn: () => tenantsApi.get(tenantId),
    enabled: !!tenantId,
  });

  const { data: queries, isLoading, error } = useQuery({
    queryKey: ['failed-queries', tenantId],
    queryFn: () => observabilityApi.failedQueries(tenantId),
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
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Failed Queries - {tenant?.name || 'Tenant'}
          </h1>
          <p className="text-sm text-gray-500 mt-1">Xem các queries thất bại</p>
        </div>

        <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Query
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Reason
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Thời gian
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {queries?.map((query) => (
                <tr key={query.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <div className="text-sm font-medium text-gray-900 max-w-md">
                      {query.query}
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-sm text-red-600">
                      {query.reason || 'Unknown'}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {formatDate(query.created_at)}
                  </td>
                </tr>
              ))}
              {(!queries || queries.length === 0) && (
                <tr>
                  <td colSpan={3} className="px-6 py-4 text-center text-sm text-gray-500">
                    Không có failed queries nào
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
