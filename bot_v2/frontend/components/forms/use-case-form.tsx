'use client';

import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { Select } from './select';
import { Textarea } from './textarea';
import { Button } from './button';
import { productsApi } from '@/lib/api';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import type { UseCase, UUID } from '@/lib/types';

interface UseCaseFormProps {
  tenantId: UUID;
  productId: UUID;
  useCase?: UseCase;
  onSuccess?: () => void;
  onCancel?: () => void;
}

interface UseCaseFormData {
  type: string;
  description: string;
}

export function UseCaseForm({
  tenantId,
  productId,
  useCase,
  onSuccess,
  onCancel,
}: UseCaseFormProps) {
  const isEdit = !!useCase;
  const queryClient = useQueryClient();
  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<UseCaseFormData>({
    defaultValues: {
      type: useCase?.type || 'allowed',
      description: useCase?.description || '',
    },
  });

  useEffect(() => {
    if (useCase) {
      reset({
        type: useCase.type,
        description: useCase.description,
      });
    }
  }, [useCase, reset]);

  const createMutation = useMutation({
    mutationFn: (data: UseCaseFormData) =>
      productsApi.createUseCase(tenantId, productId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['product', tenantId, productId] });
      onSuccess?.();
    },
  });

  const updateMutation = useMutation({
    mutationFn: (data: Partial<UseCaseFormData>) => {
      if (!useCase) throw new Error('Use Case ID required');
      return productsApi.updateUseCase(tenantId, productId, useCase.id, data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['product', tenantId, productId] });
      onSuccess?.();
    },
  });

  const onSubmit = (data: UseCaseFormData) => {
    if (isEdit) {
      updateMutation.mutate(data);
    } else {
      createMutation.mutate(data);
    }
  };

  const isLoading = createMutation.isPending || updateMutation.isPending;

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <Select
        label="Type"
        {...register('type', { required: 'Type là bắt buộc' })}
        error={errors.type?.message}
        options={[
          { value: 'allowed', label: 'Allowed' },
          { value: 'disallowed', label: 'Disallowed' },
          { value: 'unknown', label: 'Unknown' },
        ]}
        required
      />

      <Textarea
        label="Description"
        {...register('description', { required: 'Description là bắt buộc' })}
        error={errors.description?.message}
        required
        rows={4}
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
