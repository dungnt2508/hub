'use client';

import { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { intentsApi, tenantsApi } from '@/lib/api';
import { MainLayout } from '@/components/layout/main-layout';
import { Modal } from '@/components/forms/modal';
import { IntentForm } from '@/components/forms/intent-form';
import { Button } from '@/components/forms/button';
import { useParams } from 'next/navigation';
import { formatDate } from '@/lib/utils';
import Link from 'next/link';
import type { Intent } from '@/lib/types';

export default function IntentsPage() {
  const params = useParams();
  const tenantId = params.id as string;
  const queryClient = useQueryClient();
  const [selectedDomain, setSelectedDomain] = useState<string>('');
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [editingIntent, setEditingIntent] = useState<Intent | null>(null);
  const [deletingIntent, setDeletingIntent] = useState<Intent | null>(null);

  const { data: tenant } = useQuery({
    queryKey: ['tenant', tenantId],
    queryFn: () => tenantsApi.get(tenantId),
    enabled: !!tenantId,
  });

  const { data: intents, isLoading, error } = useQuery({
    queryKey: ['intents', tenantId, selectedDomain],
    queryFn: () => intentsApi.list(tenantId, selectedDomain || undefined),
    enabled: !!tenantId,
  });

  const domains = Array.from(new Set(intents?.map((i) => i.domain) || []));

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
              Intents & Routing - {tenant?.name || 'Tenant'}
            </h1>
            <p className="text-sm text-gray-500 mt-1">Quản lý intents, patterns, hints, actions</p>
          </div>
          <Button onClick={() => setIsCreateModalOpen(true)}>
            + Tạo Intent
          </Button>
        </div>

        <div className="flex gap-4">
          <select
            value={selectedDomain}
            onChange={(e) => setSelectedDomain(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Tất cả domains</option>
            {domains.map((domain) => (
              <option key={domain} value={domain}>
                {domain}
              </option>
            ))}
          </select>
        </div>

        <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Name
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Domain
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Priority
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Ngày tạo
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {intents?.map((intent) => (
                <tr key={intent.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">
                      {intent.name}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">
                      {intent.domain}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {intent.priority}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {formatDate(intent.created_at)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <div className="flex items-center gap-3">
                      <Link
                        href={`/admin/tenants/${tenantId}/intents/${intent.id}`}
                        className="text-blue-600 hover:text-blue-900"
                      >
                        Xem
                      </Link>
                      <button
                        onClick={() => setEditingIntent(intent)}
                        className="text-green-600 hover:text-green-900"
                      >
                        Sửa
                      </button>
                      <button
                        onClick={() => setDeletingIntent(intent)}
                        className="text-red-600 hover:text-red-900"
                      >
                        Xóa
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {(!intents || intents.length === 0) && (
                <tr>
                  <td colSpan={5} className="px-6 py-4 text-center text-sm text-gray-500">
                    Không có intent nào
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Create Modal */}
      <Modal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        title="Tạo Intent mới"
        size="md"
      >
        <IntentForm
          tenantId={tenantId}
          onSuccess={() => setIsCreateModalOpen(false)}
          onCancel={() => setIsCreateModalOpen(false)}
        />
      </Modal>

      {/* Edit Modal */}
      <Modal
        isOpen={!!editingIntent}
        onClose={() => setEditingIntent(null)}
        title="Sửa Intent"
        size="md"
      >
        {editingIntent && (
          <IntentForm
            tenantId={tenantId}
            intent={editingIntent}
            onSuccess={() => setEditingIntent(null)}
            onCancel={() => setEditingIntent(null)}
          />
        )}
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={!!deletingIntent}
        onClose={() => setDeletingIntent(null)}
        title="Xác nhận xóa Intent"
        size="sm"
        footer={
          <>
            <Button variant="outline" onClick={() => setDeletingIntent(null)}>
              Hủy
            </Button>
            <Button
              variant="danger"
              onClick={async () => {
                if (deletingIntent) {
                  try {
                    await intentsApi.delete(tenantId, deletingIntent.id);
                    queryClient.invalidateQueries({ queryKey: ['intents', tenantId] });
                    setDeletingIntent(null);
                  } catch (error) {
                    alert('Lỗi khi xóa intent: ' + String(error));
                  }
                }
              }}
            >
              Xóa
            </Button>
          </>
        }
      >
        <p className="text-gray-700">
          Bạn có chắc chắn muốn xóa intent <strong>{deletingIntent?.name}</strong>?
          <br />
          <span className="text-sm text-red-600 mt-2 block">
            Hành động này không thể hoàn tác!
          </span>
        </p>
      </Modal>
    </MainLayout>
  );
}
