'use client';

import { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { productsApi, tenantsApi } from '@/lib/api';
import { MainLayout } from '@/components/layout/main-layout';
import { Modal } from '@/components/forms/modal';
import { ProductAttributeForm } from '@/components/forms/product-attribute-form';
import { UseCaseForm } from '@/components/forms/use-case-form';
import { FAQForm } from '@/components/forms/faq-form';
import { Button } from '@/components/forms/button';
import { useParams } from 'next/navigation';
import { formatDate } from '@/lib/utils';
import Link from 'next/link';
import type { ProductAttribute, UseCase, FAQ } from '@/lib/types';

export default function ProductDetailPage() {
  const params = useParams();
  const tenantId = params.id as string;
  const productId = params.productId as string;
  const queryClient = useQueryClient();
  
  // Attribute modals
  const [isCreateAttributeOpen, setIsCreateAttributeOpen] = useState(false);
  const [editingAttribute, setEditingAttribute] = useState<ProductAttribute | null>(null);
  const [deletingAttribute, setDeletingAttribute] = useState<ProductAttribute | null>(null);
  
  // Use case modals
  const [isCreateUseCaseOpen, setIsCreateUseCaseOpen] = useState(false);
  const [editingUseCase, setEditingUseCase] = useState<UseCase | null>(null);
  const [deletingUseCase, setDeletingUseCase] = useState<UseCase | null>(null);
  
  // FAQ modals
  const [isCreateFAQOpen, setIsCreateFAQOpen] = useState(false);
  const [editingFAQ, setEditingFAQ] = useState<FAQ | null>(null);
  const [deletingFAQ, setDeletingFAQ] = useState<FAQ | null>(null);

  const { data: tenant } = useQuery({
    queryKey: ['tenant', tenantId],
    queryFn: () => tenantsApi.get(tenantId),
    enabled: !!tenantId,
  });

  const { data: productDetail, isLoading, error } = useQuery({
    queryKey: ['product', tenantId, productId],
    queryFn: () => productsApi.get(tenantId, productId),
    enabled: !!tenantId && !!productId,
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

  if (error || !productDetail) {
    return (
      <MainLayout>
        <div className="flex items-center justify-center h-64">
          <p className="text-red-500">Lỗi: {String(error || 'Không tìm thấy sản phẩm')}</p>
        </div>
      </MainLayout>
    );
  }

  const { product, attributes, use_cases, faqs } = productDetail;

  return (
    <MainLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <Link
              href={`/admin/tenants/${tenantId}/catalog`}
              className="text-sm text-gray-500 hover:text-gray-700 mb-2 inline-block"
            >
              ← Quay lại Catalog
            </Link>
            <h1 className="text-2xl font-bold text-gray-900">{product.name}</h1>
            <p className="text-sm text-gray-500 mt-1">
              SKU: {product.sku} | Slug: {product.slug}
            </p>
          </div>
        </div>

        {/* Product Info */}
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Thông tin sản phẩm</h2>
          <dl className="grid grid-cols-2 gap-4">
            <div>
              <dt className="text-sm font-medium text-gray-500">Category</dt>
              <dd className="text-sm text-gray-900 mt-1">{product.category || '-'}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Status</dt>
              <dd className="text-sm text-gray-900 mt-1">
                <span
                  className={`px-2 py-1 text-xs font-semibold rounded-full ${
                    product.status === 'active'
                      ? 'bg-green-100 text-green-800'
                      : 'bg-gray-100 text-gray-800'
                  }`}
                >
                  {product.status}
                </span>
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Ngày tạo</dt>
              <dd className="text-sm text-gray-900 mt-1">{formatDate(product.created_at)}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Ngày cập nhật</dt>
              <dd className="text-sm text-gray-900 mt-1">{formatDate(product.updated_at)}</dd>
            </div>
          </dl>
        </div>

        {/* Attributes */}
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Attributes ({attributes.length})
          </h2>
          {attributes.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Key
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Value
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Type
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {attributes.map((attr) => (
                    <tr key={attr.id}>
                      <td className="px-4 py-3 text-sm font-medium text-gray-900">
                        {attr.attributes_key}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-500">
                        {attr.attributes_value}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-500">
                        {attr.attributes_value_type}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm font-medium">
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => setEditingAttribute(attr)}
                            className="text-green-600 hover:text-green-900"
                          >
                            Sửa
                          </button>
                          <button
                            onClick={() => setDeletingAttribute(attr)}
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
            <p className="text-sm text-gray-500">Không có attributes</p>
          )}
        </div>

        {/* Use Cases */}
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">
              Use Cases ({use_cases.length})
            </h2>
            <Button size="sm" onClick={() => setIsCreateUseCaseOpen(true)}>
              + Thêm Use Case
            </Button>
          </div>
          {use_cases.length > 0 ? (
            <div className="space-y-3">
              {use_cases.map((uc) => (
                <div key={uc.id} className="border border-gray-200 rounded p-3">
                  <div className="flex items-center gap-2 mb-2">
                    <span
                      className={`px-2 py-1 text-xs font-semibold rounded-full ${
                        uc.type === 'allowed'
                          ? 'bg-green-100 text-green-800'
                          : uc.type === 'disallowed'
                          ? 'bg-red-100 text-red-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      {uc.type}
                    </span>
                  </div>
                  <p className="text-sm text-gray-700">{uc.description}</p>
                  <div className="flex items-center gap-2 mt-2">
                    <button
                      onClick={() => setEditingUseCase(uc)}
                      className="text-xs text-green-600 hover:text-green-900"
                    >
                      Sửa
                    </button>
                    <button
                      onClick={() => setDeletingUseCase(uc)}
                      className="text-xs text-red-600 hover:text-red-900"
                    >
                      Xóa
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-500">Không có use cases</p>
          )}
        </div>

        {/* FAQs */}
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">
              FAQs ({faqs.length})
            </h2>
            <Button size="sm" onClick={() => setIsCreateFAQOpen(true)}>
              + Thêm FAQ
            </Button>
          </div>
          {faqs.length > 0 ? (
            <div className="space-y-4">
              {faqs.map((faq) => (
                <div key={faq.id} className="border border-gray-200 rounded p-4">
                  <div className="mb-2">
                    <span className="text-xs text-gray-500">Scope: {faq.scope}</span>
                  </div>
                  <h4 className="text-sm font-medium text-gray-900 mb-2">{faq.question}</h4>
                  <p className="text-sm text-gray-700">{faq.answer}</p>
                  <div className="flex items-center gap-2 mt-2">
                    <button
                      onClick={() => setEditingFAQ(faq)}
                      className="text-xs text-green-600 hover:text-green-900"
                    >
                      Sửa
                    </button>
                    <button
                      onClick={() => setDeletingFAQ(faq)}
                      className="text-xs text-red-600 hover:text-red-900"
                    >
                      Xóa
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-500">Không có FAQs</p>
          )}
        </div>
      </div>

      {/* Attribute Modals */}
      <Modal
        isOpen={isCreateAttributeOpen}
        onClose={() => setIsCreateAttributeOpen(false)}
        title="Thêm Attribute"
        size="md"
      >
        <ProductAttributeForm
          tenantId={tenantId}
          productId={productId}
          onSuccess={() => setIsCreateAttributeOpen(false)}
          onCancel={() => setIsCreateAttributeOpen(false)}
        />
      </Modal>

      <Modal
        isOpen={!!editingAttribute}
        onClose={() => setEditingAttribute(null)}
        title="Sửa Attribute"
        size="md"
      >
        {editingAttribute && (
          <ProductAttributeForm
            tenantId={tenantId}
            productId={productId}
            attribute={editingAttribute}
            onSuccess={() => setEditingAttribute(null)}
            onCancel={() => setEditingAttribute(null)}
          />
        )}
      </Modal>

      <Modal
        isOpen={!!deletingAttribute}
        onClose={() => setDeletingAttribute(null)}
        title="Xác nhận xóa Attribute"
        size="sm"
        footer={
          <>
            <Button variant="outline" onClick={() => setDeletingAttribute(null)}>
              Hủy
            </Button>
            <Button
              variant="danger"
              onClick={async () => {
                if (deletingAttribute) {
                  try {
                    await productsApi.deleteAttribute(tenantId, productId, deletingAttribute.id);
                    queryClient.invalidateQueries({ queryKey: ['product', tenantId, productId] });
                    setDeletingAttribute(null);
                  } catch (error) {
                    alert('Lỗi khi xóa attribute: ' + String(error));
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
          Bạn có chắc chắn muốn xóa attribute <strong>{deletingAttribute?.attributes_key}</strong>?
        </p>
      </Modal>

      {/* Use Case Modals */}
      <Modal
        isOpen={isCreateUseCaseOpen}
        onClose={() => setIsCreateUseCaseOpen(false)}
        title="Thêm Use Case"
        size="md"
      >
        <UseCaseForm
          tenantId={tenantId}
          productId={productId}
          onSuccess={() => setIsCreateUseCaseOpen(false)}
          onCancel={() => setIsCreateUseCaseOpen(false)}
        />
      </Modal>

      <Modal
        isOpen={!!editingUseCase}
        onClose={() => setEditingUseCase(null)}
        title="Sửa Use Case"
        size="md"
      >
        {editingUseCase && (
          <UseCaseForm
            tenantId={tenantId}
            productId={productId}
            useCase={editingUseCase}
            onSuccess={() => setEditingUseCase(null)}
            onCancel={() => setEditingUseCase(null)}
          />
        )}
      </Modal>

      <Modal
        isOpen={!!deletingUseCase}
        onClose={() => setDeletingUseCase(null)}
        title="Xác nhận xóa Use Case"
        size="sm"
        footer={
          <>
            <Button variant="outline" onClick={() => setDeletingUseCase(null)}>
              Hủy
            </Button>
            <Button
              variant="danger"
              onClick={async () => {
                if (deletingUseCase) {
                  try {
                    await productsApi.deleteUseCase(tenantId, productId, deletingUseCase.id);
                    queryClient.invalidateQueries({ queryKey: ['product', tenantId, productId] });
                    setDeletingUseCase(null);
                  } catch (error) {
                    alert('Lỗi khi xóa use case: ' + String(error));
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
          Bạn có chắc chắn muốn xóa use case này?
        </p>
      </Modal>

      {/* FAQ Modals */}
      <Modal
        isOpen={isCreateFAQOpen}
        onClose={() => setIsCreateFAQOpen(false)}
        title="Thêm FAQ"
        size="lg"
      >
        <FAQForm
          tenantId={tenantId}
          productId={productId}
          onSuccess={() => setIsCreateFAQOpen(false)}
          onCancel={() => setIsCreateFAQOpen(false)}
        />
      </Modal>

      <Modal
        isOpen={!!editingFAQ}
        onClose={() => setEditingFAQ(null)}
        title="Sửa FAQ"
        size="lg"
      >
        {editingFAQ && (
          <FAQForm
            tenantId={tenantId}
            productId={productId}
            faq={editingFAQ}
            onSuccess={() => setEditingFAQ(null)}
            onCancel={() => setEditingFAQ(null)}
          />
        )}
      </Modal>

      <Modal
        isOpen={!!deletingFAQ}
        onClose={() => setDeletingFAQ(null)}
        title="Xác nhận xóa FAQ"
        size="sm"
        footer={
          <>
            <Button variant="outline" onClick={() => setDeletingFAQ(null)}>
              Hủy
            </Button>
            <Button
              variant="danger"
              onClick={async () => {
                if (deletingFAQ) {
                  try {
                    await productsApi.deleteFAQ(tenantId, deletingFAQ.id);
                    queryClient.invalidateQueries({ queryKey: ['product', tenantId, productId] });
                    setDeletingFAQ(null);
                  } catch (error) {
                    alert('Lỗi khi xóa FAQ: ' + String(error));
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
          Bạn có chắc chắn muốn xóa FAQ <strong>{deletingFAQ?.question}</strong>?
        </p>
      </Modal>
    </MainLayout>
  );
}
