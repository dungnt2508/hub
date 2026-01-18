'use client';

import { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { intentsApi, tenantsApi } from '@/lib/api';
import { MainLayout } from '@/components/layout/main-layout';
import { Modal } from '@/components/forms/modal';
import { IntentPatternForm } from '@/components/forms/intent-pattern-form';
import { IntentHintForm } from '@/components/forms/intent-hint-form';
import { IntentActionForm } from '@/components/forms/intent-action-form';
import { Button } from '@/components/forms/button';
import { useParams } from 'next/navigation';
import { formatDate } from '@/lib/utils';
import Link from 'next/link';
import type { IntentPattern, IntentHint, IntentAction } from '@/lib/types';

export default function IntentDetailPage() {
  const params = useParams();
  const tenantId = params.id as string;
  const intentId = params.intentId as string;
  const queryClient = useQueryClient();
  
  // Pattern modals
  const [isCreatePatternOpen, setIsCreatePatternOpen] = useState(false);
  const [editingPattern, setEditingPattern] = useState<IntentPattern | null>(null);
  const [deletingPattern, setDeletingPattern] = useState<IntentPattern | null>(null);
  
  // Hint modals
  const [isCreateHintOpen, setIsCreateHintOpen] = useState(false);
  const [editingHint, setEditingHint] = useState<IntentHint | null>(null);
  const [deletingHint, setDeletingHint] = useState<IntentHint | null>(null);
  
  // Action modals
  const [isCreateActionOpen, setIsCreateActionOpen] = useState(false);
  const [editingAction, setEditingAction] = useState<IntentAction | null>(null);
  const [deletingAction, setDeletingAction] = useState<IntentAction | null>(null);

  const { data: tenant } = useQuery({
    queryKey: ['tenant', tenantId],
    queryFn: () => tenantsApi.get(tenantId),
    enabled: !!tenantId,
  });

  const { data: intentDetail, isLoading, error } = useQuery({
    queryKey: ['intent', tenantId, intentId],
    queryFn: () => intentsApi.get(tenantId, intentId),
    enabled: !!tenantId && !!intentId,
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

  if (error || !intentDetail) {
    return (
      <MainLayout>
        <div className="flex items-center justify-center h-64">
          <p className="text-red-500">Lỗi: {String(error || 'Không tìm thấy intent')}</p>
        </div>
      </MainLayout>
    );
  }

  const { intent, patterns, hints, actions } = intentDetail;

  return (
    <MainLayout>
      <div className="space-y-6">
        <div>
          <Link
            href={`/admin/tenants/${tenantId}/intents`}
            className="text-sm text-gray-500 hover:text-gray-700 mb-2 inline-block"
          >
            ← Quay lại Intents
          </Link>
          <h1 className="text-2xl font-bold text-gray-900">{intent.name}</h1>
          <p className="text-sm text-gray-500 mt-1">
            Domain: {intent.domain} | Priority: {intent.priority}
          </p>
        </div>

        {/* Intent Info */}
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Thông tin Intent</h2>
          <dl className="grid grid-cols-2 gap-4">
            <div>
              <dt className="text-sm font-medium text-gray-500">Domain</dt>
              <dd className="text-sm text-gray-900 mt-1">
                <span className="px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">
                  {intent.domain}
                </span>
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Priority</dt>
              <dd className="text-sm text-gray-900 mt-1">{intent.priority}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Ngày tạo</dt>
              <dd className="text-sm text-gray-900 mt-1">{formatDate(intent.created_at)}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Ngày cập nhật</dt>
              <dd className="text-sm text-gray-900 mt-1">{formatDate(intent.updated_at)}</dd>
            </div>
          </dl>
        </div>

        {/* Patterns */}
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">
              Patterns ({patterns.length})
            </h2>
            <Button size="sm" onClick={() => setIsCreatePatternOpen(true)}>
              + Thêm Pattern
            </Button>
          </div>
          {patterns.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Type
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Pattern
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Weight
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {patterns.map((pattern) => (
                    <tr key={pattern.id}>
                      <td className="px-4 py-3 text-sm font-medium text-gray-900">
                        <span className="px-2 py-1 text-xs font-semibold rounded-full bg-gray-100 text-gray-800">
                          {pattern.type}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-900 font-mono">
                        {pattern.pattern}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-500">
                        {pattern.weight}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm font-medium">
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => setEditingPattern(pattern)}
                            className="text-green-600 hover:text-green-900"
                          >
                            Sửa
                          </button>
                          <button
                            onClick={() => setDeletingPattern(pattern)}
                            className="text-red-600 hover:text-red-900"
                          >
                            Xóa
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-sm text-gray-500">Không có patterns</p>
          )}
        </div>

        {/* Hints */}
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">
              Hints ({hints.length})
            </h2>
            <Button size="sm" onClick={() => setIsCreateHintOpen(true)}>
              + Thêm Hint
            </Button>
          </div>
          {hints.length > 0 ? (
            <div className="space-y-2">
              {hints.map((hint) => (
                <div key={hint.id} className="border border-gray-200 rounded p-3">
                  <p className="text-sm text-gray-700">{hint.hint_text}</p>
                  <div className="flex items-center gap-2 mt-2">
                    <button
                      onClick={() => setEditingHint(hint)}
                      className="text-xs text-green-600 hover:text-green-900"
                    >
                      Sửa
                    </button>
                    <button
                      onClick={() => setDeletingHint(hint)}
                      className="text-xs text-red-600 hover:text-red-900"
                    >
                      Xóa
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-500">Không có hints</p>
          )}
        </div>

        {/* Actions */}
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">
              Actions ({actions.length})
            </h2>
            <Button size="sm" onClick={() => setIsCreateActionOpen(true)}>
              + Thêm Action
            </Button>
          </div>
          {actions.length > 0 ? (
            <div className="space-y-4">
              {actions.map((action) => (
                <div key={action.id} className="border border-gray-200 rounded p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">
                      {action.action_type}
                    </span>
                    <span className="text-xs text-gray-500">Priority: {action.priority}</span>
                  </div>
                  {action.config_json && (
                    <div className="mt-3">
                      <pre className="text-xs bg-gray-50 p-3 rounded overflow-x-auto">
                        {JSON.stringify(action.config_json, null, 2)}
                      </pre>
                    </div>
                  )}
                  <div className="flex items-center gap-2 mt-2">
                    <button
                      onClick={() => setEditingAction(action)}
                      className="text-xs text-green-600 hover:text-green-900"
                    >
                      Sửa
                    </button>
                    <button
                      onClick={() => setDeletingAction(action)}
                      className="text-xs text-red-600 hover:text-red-900"
                    >
                      Xóa
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-500">Không có actions</p>
          )}
        </div>
      </div>

      {/* Pattern Modals */}
      <Modal
        isOpen={isCreatePatternOpen}
        onClose={() => setIsCreatePatternOpen(false)}
        title="Thêm Pattern"
        size="md"
      >
        <IntentPatternForm
          tenantId={tenantId}
          intentId={intentId}
          onSuccess={() => setIsCreatePatternOpen(false)}
          onCancel={() => setIsCreatePatternOpen(false)}
        />
      </Modal>

      <Modal
        isOpen={!!editingPattern}
        onClose={() => setEditingPattern(null)}
        title="Sửa Pattern"
        size="md"
      >
        {editingPattern && (
          <IntentPatternForm
            tenantId={tenantId}
            intentId={intentId}
            pattern={editingPattern}
            onSuccess={() => setEditingPattern(null)}
            onCancel={() => setEditingPattern(null)}
          />
        )}
      </Modal>

      <Modal
        isOpen={!!deletingPattern}
        onClose={() => setDeletingPattern(null)}
        title="Xác nhận xóa Pattern"
        size="sm"
        footer={
          <>
            <Button variant="outline" onClick={() => setDeletingPattern(null)}>
              Hủy
            </Button>
            <Button
              variant="danger"
              onClick={async () => {
                if (deletingPattern) {
                  try {
                    await intentsApi.deletePattern(tenantId, intentId, deletingPattern.id);
                    queryClient.invalidateQueries({ queryKey: ['intent', tenantId, intentId] });
                    setDeletingPattern(null);
                  } catch (error) {
                    alert('Lỗi khi xóa pattern: ' + String(error));
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
          Bạn có chắc chắn muốn xóa pattern <strong>{deletingPattern?.pattern}</strong>?
        </p>
      </Modal>

      {/* Hint Modals */}
      <Modal
        isOpen={isCreateHintOpen}
        onClose={() => setIsCreateHintOpen(false)}
        title="Thêm Hint"
        size="md"
      >
        <IntentHintForm
          tenantId={tenantId}
          intentId={intentId}
          onSuccess={() => setIsCreateHintOpen(false)}
          onCancel={() => setIsCreateHintOpen(false)}
        />
      </Modal>

      <Modal
        isOpen={!!editingHint}
        onClose={() => setEditingHint(null)}
        title="Sửa Hint"
        size="md"
      >
        {editingHint && (
          <IntentHintForm
            tenantId={tenantId}
            intentId={intentId}
            hint={editingHint}
            onSuccess={() => setEditingHint(null)}
            onCancel={() => setEditingHint(null)}
          />
        )}
      </Modal>

      <Modal
        isOpen={!!deletingHint}
        onClose={() => setDeletingHint(null)}
        title="Xác nhận xóa Hint"
        size="sm"
        footer={
          <>
            <Button variant="outline" onClick={() => setDeletingHint(null)}>
              Hủy
            </Button>
            <Button
              variant="danger"
              onClick={async () => {
                if (deletingHint) {
                  try {
                    await intentsApi.deleteHint(tenantId, intentId, deletingHint.id);
                    queryClient.invalidateQueries({ queryKey: ['intent', tenantId, intentId] });
                    setDeletingHint(null);
                  } catch (error) {
                    alert('Lỗi khi xóa hint: ' + String(error));
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
          Bạn có chắc chắn muốn xóa hint này?
        </p>
      </Modal>

      {/* Action Modals */}
      <Modal
        isOpen={isCreateActionOpen}
        onClose={() => setIsCreateActionOpen(false)}
        title="Thêm Action"
        size="lg"
      >
        <IntentActionForm
          tenantId={tenantId}
          intentId={intentId}
          onSuccess={() => setIsCreateActionOpen(false)}
          onCancel={() => setIsCreateActionOpen(false)}
        />
      </Modal>

      <Modal
        isOpen={!!editingAction}
        onClose={() => setEditingAction(null)}
        title="Sửa Action"
        size="lg"
      >
        {editingAction && (
          <IntentActionForm
            tenantId={tenantId}
            intentId={intentId}
            action={editingAction}
            onSuccess={() => setEditingAction(null)}
            onCancel={() => setEditingAction(null)}
          />
        )}
      </Modal>

      <Modal
        isOpen={!!deletingAction}
        onClose={() => setDeletingAction(null)}
        title="Xác nhận xóa Action"
        size="sm"
        footer={
          <>
            <Button variant="outline" onClick={() => setDeletingAction(null)}>
              Hủy
            </Button>
            <Button
              variant="danger"
              onClick={async () => {
                if (deletingAction) {
                  try {
                    await intentsApi.deleteAction(tenantId, intentId, deletingAction.id);
                    queryClient.invalidateQueries({ queryKey: ['intent', tenantId, intentId] });
                    setDeletingAction(null);
                  } catch (error) {
                    alert('Lỗi khi xóa action: ' + String(error));
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
          Bạn có chắc chắn muốn xóa action <strong>{deletingAction?.action_type}</strong>?
        </p>
      </Modal>
    </MainLayout>
  );
}
