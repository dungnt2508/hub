'use client';

import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { Textarea } from './textarea';
import { Button } from './button';
import { intentsApi } from '@/lib/api';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import type { IntentHint, UUID } from '@/lib/types';

interface IntentHintFormProps {
  tenantId: UUID;
  intentId: UUID;
  hint?: IntentHint;
  onSuccess?: () => void;
  onCancel?: () => void;
}

interface IntentHintFormData {
  hint_text: string;
}

export function IntentHintForm({
  tenantId,
  intentId,
  hint,
  onSuccess,
  onCancel,
}: IntentHintFormProps) {
  const isEdit = !!hint;
  const queryClient = useQueryClient();
  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<IntentHintFormData>({
    defaultValues: {
      hint_text: hint?.hint_text || '',
    },
  });

  useEffect(() => {
    if (hint) {
      reset({
        hint_text: hint.hint_text,
      });
    }
  }, [hint, reset]);

  const createMutation = useMutation({
    mutationFn: (data: IntentHintFormData) =>
      intentsApi.createHint(tenantId, intentId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['intent', tenantId, intentId] });
      onSuccess?.();
    },
  });

  const updateMutation = useMutation({
    mutationFn: (data: Partial<IntentHintFormData>) => {
      if (!hint) throw new Error('Hint ID required');
      return intentsApi.updateHint(tenantId, intentId, hint.id, data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['intent', tenantId, intentId] });
      onSuccess?.();
    },
  });

  const onSubmit = (data: IntentHintFormData) => {
    if (isEdit) {
      updateMutation.mutate(data);
    } else {
      createMutation.mutate(data);
    }
  };

  const isLoading = createMutation.isPending || updateMutation.isPending;

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <Textarea
        label="Hint Text"
        {...register('hint_text', { required: 'Hint text là bắt buộc' })}
        error={errors.hint_text?.message}
        required
        rows={4}
        helperText="Hint text để giúp LLM phân biệt intent này với intents khác"
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
