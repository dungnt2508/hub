'use client';

import { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { channelsApi, tenantsApi } from '@/lib/api';
import { MainLayout } from '@/components/layout/main-layout';
import { Modal } from '@/components/forms/modal';
import { ChannelForm } from '@/components/forms/channel-form';
import { Button } from '@/components/forms/button';
import { useParams } from 'next/navigation';
import { formatDate } from '@/lib/utils';
import type { Channel } from '@/lib/types';

export default function ChannelsPage() {
  const params = useParams();
  const tenantId = params.id as string;
  const queryClient = useQueryClient();
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [editingChannel, setEditingChannel] = useState<Channel | null>(null);
  const [deletingChannel, setDeletingChannel] = useState<Channel | null>(null);

  const { data: tenant } = useQuery({
    queryKey: ['tenant', tenantId],
    queryFn: () => tenantsApi.get(tenantId),
    enabled: !!tenantId,
  });

  const { data: channels, isLoading, error } = useQuery({
    queryKey: ['channels', tenantId],
    queryFn: () => channelsApi.list(tenantId),
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
            Channels - {tenant?.name || 'Tenant'}
          </h1>
          <p className="text-sm text-gray-500 mt-1">Quản lý kênh cho tenant</p>
        </div>

        <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Type
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Config
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
              {channels?.map((channel) => (
                <tr key={channel.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">
                      {channel.type}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={`px-2 py-1 text-xs font-semibold rounded-full ${
                        channel.enabled
                          ? 'bg-green-100 text-green-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      {channel.enabled ? 'Enabled' : 'Disabled'}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-sm text-gray-500">
                      {channel.config_json ? (
                        <pre className="text-xs bg-gray-50 p-2 rounded">
                          {JSON.stringify(channel.config_json, null, 2)}
                        </pre>
                      ) : (
                        '-'
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {formatDate(channel.created_at)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <div className="flex items-center gap-3">
                      <button
                        onClick={() => setEditingChannel(channel)}
                        className="text-green-600 hover:text-green-900"
                      >
                        Sửa
                      </button>
                      <button
                        onClick={() => setDeletingChannel(channel)}
                        className="text-red-600 hover:text-red-900"
                      >
                        Xóa
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {(!channels || channels.length === 0) && (
                <tr>
                  <td colSpan={5} className="px-6 py-4 text-center text-sm text-gray-500">
                    Không có channel nào
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
        title="Tạo Channel mới"
        size="lg"
      >
        <ChannelForm
          tenantId={tenantId}
          onSuccess={() => setIsCreateModalOpen(false)}
          onCancel={() => setIsCreateModalOpen(false)}
        />
      </Modal>

      {/* Edit Modal */}
      <Modal
        isOpen={!!editingChannel}
        onClose={() => setEditingChannel(null)}
        title="Sửa Channel"
        size="lg"
      >
        {editingChannel && (
          <ChannelForm
            tenantId={tenantId}
            channel={editingChannel}
            onSuccess={() => setEditingChannel(null)}
            onCancel={() => setEditingChannel(null)}
          />
        )}
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={!!deletingChannel}
        onClose={() => setDeletingChannel(null)}
        title="Xác nhận xóa Channel"
        size="sm"
        footer={
          <>
            <Button variant="outline" onClick={() => setDeletingChannel(null)}>
              Hủy
            </Button>
            <Button
              variant="danger"
              onClick={async () => {
                if (deletingChannel) {
                  try {
                    await channelsApi.delete(tenantId, deletingChannel.id);
                    queryClient.invalidateQueries({ queryKey: ['channels', tenantId] });
                    setDeletingChannel(null);
                  } catch (error) {
                    alert('Lỗi khi xóa channel: ' + String(error));
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
          Bạn có chắc chắn muốn xóa channel <strong>{deletingChannel?.type}</strong>?
          <br />
          <span className="text-sm text-red-600 mt-2 block">
            Hành động này không thể hoàn tác!
          </span>
        </p>
      </Modal>
    </MainLayout>
  );
}
