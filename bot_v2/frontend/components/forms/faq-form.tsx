'use client';

import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { Select } from './select';
import { Textarea } from './textarea';
import { Input } from './input';
import { Button } from './button';
import { productsApi } from '@/lib/api';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import type { FAQ, UUID } from '@/lib/types';

interface FAQFormProps {
  tenantId: UUID;
  productId?: UUID | null; // null for global FAQs
  faq?: FAQ;
  onSuccess?: () => void;
  onCancel?: () => void;
}

interface FAQFormData {
  scope: string;
  question: string;
  answer: string;
}

export function FAQForm({
  tenantId,
  productId,
  faq,
  onSuccess,
  onCancel,
}: FAQFormProps) {
  const isEdit = !!faq;
  const queryClient = useQueryClient();
  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
    watch,
  } = useForm<FAQFormData>({
    defaultValues: {
      scope: faq?.scope || (productId ? 'product' : 'global'),
      question: faq?.question || '',
      answer: faq?.answer || '',
    },
  });

  const scope = watch('scope');

  useEffect(() => {
    if (faq) {
      reset({
        scope: faq.scope,
        question: faq.question,
        answer: faq.answer,
      });
    }
  }, [faq, reset]);

  const createMutation = useMutation({
    mutationFn: (data: FAQFormData) => {
      const actualProductId = scope === 'product' ? productId || null : null;
      return productsApi.createFAQ(tenantId, actualProductId, data);
    },
    onSuccess: () => {
      if (productId) {
        queryClient.invalidateQueries({ queryKey: ['product', tenantId, productId] });
      }
      queryClient.invalidateQueries({ queryKey: ['products', tenantId] });
      onSuccess?.();
    },
  });

  const updateMutation = useMutation({
    mutationFn: (data: Partial<FAQFormData>) => {
      if (!faq) throw new Error('FAQ ID required');
      return productsApi.updateFAQ(tenantId, faq.id, data);
    },
    onSuccess: () => {
      if (productId) {
        queryClient.invalidateQueries({ queryKey: ['product', tenantId, productId] });
      }
      queryClient.invalidateQueries({ queryKey: ['products', tenantId] });
      onSuccess?.();
    },
  });

  const onSubmit = (data: FAQFormData) => {
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
        label="Scope"
        {...register('scope', { required: 'Scope là bắt buộc' })}
        error={errors.scope?.message}
        options={[
          { value: 'global', label: 'Global' },
          { value: 'product', label: 'Product' },
        ]}
        required
      />

      {scope === 'product' && !productId && (
        <p className="text-sm text-yellow-600">
          Lưu ý: FAQ sẽ được tạo với scope product nhưng không gắn với product cụ thể
        </p>
      )}

      <Input
        label="Question"
        {...register('question', { required: 'Question là bắt buộc' })}
        error={errors.question?.message}
        required
      />

      <Textarea
        label="Answer"
        {...register('answer', { required: 'Answer là bắt buộc' })}
        error={errors.answer?.message}
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
