'use client';

import { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { productsApi, tenantsApi } from '@/lib/api';
import { MainLayout } from '@/components/layout/main-layout';
import { Modal } from '@/components/forms/modal';
import { ProductForm } from '@/components/forms/product-form';
import { Button } from '@/components/forms/button';
import { useParams } from 'next/navigation';
import { formatDate } from '@/lib/utils';
import Link from 'next/link';
import type { Product } from '@/lib/types';

export default function CatalogPage() {
  const params = useParams();
  const tenantId = params.id as string;
  const queryClient = useQueryClient();
  const [searchQuery, setSearchQuery] = useState('');
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [editingProduct, setEditingProduct] = useState<Product | null>(null);
  const [deletingProduct, setDeletingProduct] = useState<Product | null>(null);

  const { data: tenant } = useQuery({
    queryKey: ['tenant', tenantId],
    queryFn: () => tenantsApi.get(tenantId),
    enabled: !!tenantId,
  });

  const { data: products, isLoading, error } = useQuery({
    queryKey: ['products', tenantId, searchQuery],
    queryFn: () => productsApi.list(tenantId, { query: searchQuery || undefined }),
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
              Catalog - {tenant?.name || 'Tenant'}
            </h1>
            <p className="text-sm text-gray-500 mt-1">Quản lý sản phẩm, attributes, FAQs, use cases</p>
          </div>
          <Button onClick={() => setIsCreateModalOpen(true)}>
            + Tạo Product
          </Button>
        </div>

        <div className="flex gap-4">
          <input
            type="text"
            placeholder="Tìm kiếm sản phẩm..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  SKU
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Tên
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Category
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
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
              {products?.map((product) => (
                <tr key={product.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">
                      {product.sku}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">
                      {product.name}
                    </div>
                    <div className="text-sm text-gray-500">{product.slug}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {product.category || '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={`px-2 py-1 text-xs font-semibold rounded-full ${
                        product.status === 'active'
                          ? 'bg-green-100 text-green-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      {product.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {formatDate(product.created_at)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <div className="flex items-center gap-3">
                      <Link
                        href={`/admin/tenants/${tenantId}/catalog/${product.id}`}
                        className="text-blue-600 hover:text-blue-900"
                      >
                        Xem
                      </Link>
                      <button
                        onClick={() => setEditingProduct(product)}
                        className="text-green-600 hover:text-green-900"
                      >
                        Sửa
                      </button>
                      <button
                        onClick={() => setDeletingProduct(product)}
                        className="text-red-600 hover:text-red-900"
                      >
                        Xóa
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {(!products || products.length === 0) && (
                <tr>
                  <td colSpan={6} className="px-6 py-4 text-center text-sm text-gray-500">
                    Không có sản phẩm nào
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
        title="Tạo Product mới"
        size="lg"
      >
        <ProductForm
          tenantId={tenantId}
          onSuccess={() => setIsCreateModalOpen(false)}
          onCancel={() => setIsCreateModalOpen(false)}
        />
      </Modal>

      {/* Edit Modal */}
      <Modal
        isOpen={!!editingProduct}
        onClose={() => setEditingProduct(null)}
        title="Sửa Product"
        size="lg"
      >
        {editingProduct && (
          <ProductForm
            tenantId={tenantId}
            product={editingProduct}
            onSuccess={() => setEditingProduct(null)}
            onCancel={() => setEditingProduct(null)}
          />
        )}
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={!!deletingProduct}
        onClose={() => setDeletingProduct(null)}
        title="Xác nhận xóa Product"
        size="sm"
        footer={
          <>
            <Button variant="outline" onClick={() => setDeletingProduct(null)}>
              Hủy
            </Button>
            <Button
              variant="danger"
              onClick={async () => {
                if (deletingProduct) {
                  try {
                    await productsApi.delete(tenantId, deletingProduct.id);
                    queryClient.invalidateQueries({ queryKey: ['products', tenantId] });
                    setDeletingProduct(null);
                  } catch (error) {
                    alert('Lỗi khi xóa product: ' + String(error));
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
          Bạn có chắc chắn muốn xóa product <strong>{deletingProduct?.name}</strong>?
          <br />
          <span className="text-sm text-red-600 mt-2 block">
            Hành động này không thể hoàn tác!
          </span>
        </p>
      </Modal>
    </MainLayout>
  );
}
