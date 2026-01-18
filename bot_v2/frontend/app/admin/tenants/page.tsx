'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { tenantsApi } from '@/lib/api';
import { MainLayout } from '@/components/layout/main-layout';
import { Modal } from '@/components/forms/modal';
import { TenantForm } from '@/components/forms/tenant-form';
import { Button } from '@/components/forms/button';
import Link from 'next/link';
import { formatDate } from '@/lib/utils';
import type { Tenant } from '@/lib/types';

export default function TenantsPage() {
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [editingTenant, setEditingTenant] = useState<Tenant | null>(null);
  const [deletingTenant, setDeletingTenant] = useState<Tenant | null>(null);
  const { data: tenants, isLoading, error } = useQuery({
    queryKey: ['tenants'],
    queryFn: () => tenantsApi.list(),
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
          <h1 className="text-2xl font-bold text-gray-900">Tenants</h1>
          <Button onClick={() => setIsCreateModalOpen(true)}>
            + Tạo Tenant
          </Button>
        </div>

        <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Tên
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Plan
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Settings Version
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
              {tenants?.map((tenant) => (
                <tr key={tenant.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">
                      {tenant.name}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={`px-2 py-1 text-xs font-semibold rounded-full ${
                        tenant.status === 'active'
                          ? 'bg-green-100 text-green-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      {tenant.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {tenant.plan || '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {tenant.settings_version}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {formatDate(tenant.created_at)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <div className="flex items-center gap-3">
                      <Link
                        href={`/admin/tenants/${tenant.id}/channels`}
                        className="text-blue-600 hover:text-blue-900"
                      >
                        Xem
                      </Link>
                      <button
                        onClick={() => setEditingTenant(tenant)}
                        className="text-green-600 hover:text-green-900"
                      >
                        Sửa
                      </button>
                      <button
                        onClick={() => setDeletingTenant(tenant)}
                        className="text-red-600 hover:text-red-900"
                      >
                        Xóa
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {(!tenants || tenants.length === 0) && (
                <tr>
                  <td colSpan={6} className="px-6 py-4 text-center text-sm text-gray-500">
                    Không có tenant nào
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
        title="Tạo Tenant mới"
        size="md"
      >
        <TenantForm
          onSuccess={() => setIsCreateModalOpen(false)}
          onCancel={() => setIsCreateModalOpen(false)}
        />
      </Modal>

      {/* Edit Modal */}
      <Modal
        isOpen={!!editingTenant}
        onClose={() => setEditingTenant(null)}
        title="Sửa Tenant"
        size="md"
      >
        {editingTenant && (
          <TenantForm
            tenant={editingTenant}
            onSuccess={() => setEditingTenant(null)}
            onCancel={() => setEditingTenant(null)}
          />
        )}
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={!!deletingTenant}
        onClose={() => setDeletingTenant(null)}
        title="Xác nhận xóa Tenant"
        size="sm"
        footer={
          <>
            <Button variant="outline" onClick={() => setDeletingTenant(null)}>
              Hủy
            </Button>
            <Button
              variant="danger"
              onClick={async () => {
                if (deletingTenant) {
                  try {
                    await tenantsApi.delete(deletingTenant.id);
                    queryClient.invalidateQueries({ queryKey: ['tenants'] });
                    setDeletingTenant(null);
                  } catch (error) {
                    alert('Lỗi khi xóa tenant: ' + String(error));
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
          Bạn có chắc chắn muốn xóa tenant <strong>{deletingTenant?.name}</strong>?
          <br />
          <span className="text-sm text-red-600 mt-2 block">
            Hành động này không thể hoàn tác!
          </span>
        </p>
      </Modal>
    </MainLayout>
  );
}
