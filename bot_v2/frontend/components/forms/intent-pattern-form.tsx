'use client';

import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { Input } from './input';
import { Select } from './select';
import { Button } from './button';
import { intentsApi } from '@/lib/api';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import type { IntentPattern, UUID } from '@/lib/types';

interface IntentPatternFormProps {
  tenantId: UUID;
  intentId: UUID;
  pattern?: IntentPattern;
  onSuccess?: () => void;
  onCancel?: () => void;
}

interface IntentPatternFormData {
  type: string;
  pattern: string;
  weight: number;
}

export function IntentPatternForm({
  tenantId,
  intentId,
  pattern,
  onSuccess,
  onCancel,
}: IntentPatternFormProps) {
  const isEdit = !!pattern;
  const queryClient = useQueryClient();
  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<IntentPatternFormData>({
    defaultValues: {
      type: pattern?.type || 'keyword',
      pattern: pattern?.pattern || '',
      weight: pattern?.weight ?? 1.0,
    },
  });

  useEffect(() => {
    if (pattern) {
      reset({
        type: pattern.type,
        pattern: pattern.pattern,
        weight: pattern.weight,
      });
    }
  }, [pattern, reset]);

  const createMutation = useMutation({
    mutationFn: (data: IntentPatternFormData) =>
      intentsApi.createPattern(tenantId, intentId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['intent', tenantId, intentId] });
      onSuccess?.();
    },
  });

  const updateMutation = useMutation({
    mutationFn: (data: Partial<IntentPatternFormData>) => {
      if (!pattern) throw new Error('Pattern ID required');
      return intentsApi.updatePattern(tenantId, intentId, pattern.id, data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['intent', tenantId, intentId] });
      onSuccess?.();
    },
  });

  const onSubmit = (data: IntentPatternFormData) => {
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
        label="Pattern Type"
        {...register('type', { required: 'Type là bắt buộc' })}
        error={errors.type?.message}
        options={[
          { value: 'keyword', label: 'Keyword' },
          { value: 'phrase', label: 'Phrase' },
          { value: 'regex', label: 'Regex' },
        ]}
        required
      />

      <Input
        label="Pattern"
        {...register('pattern', { required: 'Pattern là bắt buộc' })}
        error={errors.pattern?.message}
        required
        helperText="Pattern string hoặc regex expression"
      />

      <Input
        label="Weight"
        type="number"
        step="0.1"
        min="0"
        max="1"
        {...register('weight', {
          required: 'Weight là bắt buộc',
          valueAsNumber: true,
          min: { value: 0, message: 'Weight phải >= 0' },
          max: { value: 1, message: 'Weight phải <= 1' },
        })}
        error={errors.weight?.message}
        required
        helperText="Weight từ 0.0 đến 1.0"
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
