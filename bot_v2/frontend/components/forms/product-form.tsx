'use client';

import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { Input } from './input';
import { Select } from './select';
import { Button } from './button';
import { productsApi } from '@/lib/api';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import type { Product, UUID } from '@/lib/types';

interface ProductFormProps {
  tenantId: UUID;
  product?: Product;
  onSuccess?: () => void;
  onCancel?: () => void;
}

interface ProductFormData {
  sku: string;
  slug: string;
  name: string;
  category?: string;
  status: string;
}

export function ProductForm({ tenantId, product, onSuccess, onCancel }: ProductFormProps) {
  const isEdit = !!product;
  const queryClient = useQueryClient();
  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<ProductFormData>({
    defaultValues: {
      sku: product?.sku || '',
      slug: product?.slug || '',
      name: product?.name || '',
      category: product?.category || '',
      status: product?.status || 'active',
    },
  });

  useEffect(() => {
    if (product) {
      reset({
        sku: product.sku,
        slug: product.slug,
        name: product.name,
        category: product.category || '',
        status: product.status,
      });
    }
  }, [product, reset]);

  const createMutation = useMutation({
    mutationFn: (data: ProductFormData) => productsApi.create(tenantId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products', tenantId] });
      onSuccess?.();
    },
  });

  const updateMutation = useMutation({
    mutationFn: (data: Partial<ProductFormData>) => {
      if (!product) throw new Error('Product ID required');
      return productsApi.update(tenantId, product.id, data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products', tenantId] });
      queryClient.invalidateQueries({ queryKey: ['product', tenantId, product?.id] });
      onSuccess?.();
    },
  });

  const onSubmit = (data: ProductFormData) => {
    if (isEdit) {
      updateMutation.mutate(data);
    } else {
      createMutation.mutate(data);
    }
  };

  const isLoading = createMutation.isPending || updateMutation.isPending;

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <Input
        label="SKU"
        {...register('sku', { required: 'SKU là bắt buộc' })}
        error={errors.sku?.message}
        required
      />

      <Input
        label="Slug"
        {...register('slug', { required: 'Slug là bắt buộc' })}
        error={errors.slug?.message}
        required
        helperText="URL-friendly identifier"
      />

      <Input
        label="Tên sản phẩm"
        {...register('name', { required: 'Tên sản phẩm là bắt buộc' })}
        error={errors.name?.message}
        required
      />

      <Input
        label="Category"
        {...register('category')}
        error={errors.category?.message}
        helperText="Optional: Product category"
      />

      <Select
        label="Status"
        {...register('status', { required: 'Status là bắt buộc' })}
        error={errors.status?.message}
        options={[
          { value: 'active', label: 'Active' },
          { value: 'inactive', label: 'Inactive' },
          { value: 'archived', label: 'Archived' },
        ]}
        required
      />

      <div className="flex items-center justify-end gap-3 pt-4">
        {onCancel && (
          <Button type="button" variant="outline" onClick={onCancel}>
            Hủy
          </Button>
        )}
        <Button type="submit" isLoading={isLoading}>
          {isEdit ? 'Cập nhật' : 'Tạo mới'}
        </Button>
      </div>
    </form>
  );
}
