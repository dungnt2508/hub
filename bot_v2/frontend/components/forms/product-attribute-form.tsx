'use client';

import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { Input } from './input';
import { Select } from './select';
import { Button } from './button';
import { productsApi } from '@/lib/api';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import type { ProductAttribute, UUID } from '@/lib/types';

interface ProductAttributeFormProps {
  tenantId: UUID;
  productId: UUID;
  attribute?: ProductAttribute;
  onSuccess?: () => void;
  onCancel?: () => void;
}

interface ProductAttributeFormData {
  attributes_key: string;
  attributes_value: string;
  attributes_value_type: string;
}

export function ProductAttributeForm({
  tenantId,
  productId,
  attribute,
  onSuccess,
  onCancel,
}: ProductAttributeFormProps) {
  const isEdit = !!attribute;
  const queryClient = useQueryClient();
  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<ProductAttributeFormData>({
    defaultValues: {
      attributes_key: attribute?.attributes_key || '',
      attributes_value: attribute?.attributes_value || '',
      attributes_value_type: attribute?.attributes_value_type || 'string',
    },
  });

  useEffect(() => {
    if (attribute) {
      reset({
        attributes_key: attribute.attributes_key,
        attributes_value: attribute.attributes_value,
        attributes_value_type: attribute.attributes_value_type,
      });
    }
  }, [attribute, reset]);

  const createMutation = useMutation({
    mutationFn: (data: ProductAttributeFormData) =>
      productsApi.createAttribute(tenantId, productId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['product', tenantId, productId] });
      onSuccess?.();
    },
  });

  const updateMutation = useMutation({
    mutationFn: (data: Partial<ProductAttributeFormData>) => {
      if (!attribute) throw new Error('Attribute ID required');
      return productsApi.updateAttribute(tenantId, productId, attribute.id, data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['product', tenantId, productId] });
      onSuccess?.();
    },
  });

  const onSubmit = (data: ProductAttributeFormData) => {
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
        label="Key"
        {...register('attributes_key', { required: 'Key là bắt buộc' })}
        error={errors.attributes_key?.message}
        required
      />

      <Input
        label="Value"
        {...register('attributes_value', { required: 'Value là bắt buộc' })}
        error={errors.attributes_value?.message}
        required
      />

      <Select
        label="Value Type"
        {...register('attributes_value_type', { required: 'Type là bắt buộc' })}
        error={errors.attributes_value_type?.message}
        options={[
          { value: 'string', label: 'String' },
          { value: 'number', label: 'Number' },
          { value: 'boolean', label: 'Boolean' },
          { value: 'json', label: 'JSON' },
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
