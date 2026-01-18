'use client';

import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { Input } from './input';
import { Select } from './select';
import { Button } from './button';
import { intentsApi } from '@/lib/api';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import type { Intent, UUID } from '@/lib/types';

interface IntentFormProps {
  tenantId: UUID;
  intent?: Intent;
  onSuccess?: () => void;
  onCancel?: () => void;
}

interface IntentFormData {
  name: string;
  domain: string;
  priority: number;
}

export function IntentForm({ tenantId, intent, onSuccess, onCancel }: IntentFormProps) {
  const isEdit = !!intent;
  const queryClient = useQueryClient();
  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<IntentFormData>({
    defaultValues: {
      name: intent?.name || '',
      domain: intent?.domain || '',
      priority: intent?.priority ?? 0,
    },
  });

  useEffect(() => {
    if (intent) {
      reset({
        name: intent.name,
        domain: intent.domain,
        priority: intent.priority,
      });
    }
  }, [intent, reset]);

  const createMutation = useMutation({
    mutationFn: (data: IntentFormData) => intentsApi.create(tenantId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['intents', tenantId] });
      onSuccess?.();
    },
  });

  const updateMutation = useMutation({
    mutationFn: (data: Partial<IntentFormData>) => {
      if (!intent) throw new Error('Intent ID required');
      return intentsApi.update(tenantId, intent.id, data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['intents', tenantId] });
      queryClient.invalidateQueries({ queryKey: ['intent', tenantId, intent?.id] });
      onSuccess?.();
    },
  });

  const onSubmit = (data: IntentFormData) => {
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
        label="Intent Name"
        {...register('name', { required: 'Intent name là bắt buộc' })}
        error={errors.name?.message}
        required
      />

      <Input
        label="Domain"
        {...register('domain', { required: 'Domain là bắt buộc' })}
        error={errors.domain?.message}
        required
        helperText="Domain như: product, faq, use_case, comparison"
      />

      <Input
        label="Priority"
        type="number"
        {...register('priority', {
          required: 'Priority là bắt buộc',
          valueAsNumber: true,
          min: { value: 0, message: 'Priority phải >= 0' },
        })}
        error={errors.priority?.message}
        required
        helperText="Priority cao hơn = ưu tiên hơn"
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
