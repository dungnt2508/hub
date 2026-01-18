'use client';

import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { Input } from './input';
import { Select } from './select';
import { Textarea } from './textarea';
import { Button } from './button';
import { intentsApi } from '@/lib/api';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import type { IntentAction, UUID } from '@/lib/types';

interface IntentActionFormProps {
  tenantId: UUID;
  intentId: UUID;
  action?: IntentAction;
  onSuccess?: () => void;
  onCancel?: () => void;
}

interface IntentActionFormData {
  action_type: string;
  config_json?: string; // JSON string for editing
  priority: number;
}

export function IntentActionForm({
  tenantId,
  intentId,
  action,
  onSuccess,
  onCancel,
}: IntentActionFormProps) {
  const isEdit = !!action;
  const queryClient = useQueryClient();
  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
    watch,
  } = useForm<IntentActionFormData>({
    defaultValues: {
      action_type: action?.action_type || 'query_db',
      config_json: action?.config_json ? JSON.stringify(action.config_json, null, 2) : '',
      priority: action?.priority ?? 0,
    },
  });

  const configJson = watch('config_json');
  const [configError, setConfigError] = useState<string>('');

  useEffect(() => {
    if (action) {
      reset({
        action_type: action.action_type,
        config_json: action.config_json ? JSON.stringify(action.config_json, null, 2) : '',
        priority: action.priority,
      });
    }
  }, [action, reset]);

  const validateConfigJson = (value?: string) => {
    if (!value || !value.trim()) return true;
    try {
      JSON.parse(value);
      setConfigError('');
      return true;
    } catch (e) {
      setConfigError('Invalid JSON format');
      return false;
    }
  };

  const createMutation = useMutation({
    mutationFn: (data: IntentActionFormData) => {
      let config_json = undefined;
      if (data.config_json && data.config_json.trim()) {
        try {
          config_json = JSON.parse(data.config_json);
        } catch (e) {
          throw new Error('Invalid JSON in config_json');
        }
      }
      return intentsApi.createAction(tenantId, intentId, {
        action_type: data.action_type,
        config_json,
        priority: data.priority,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['intent', tenantId, intentId] });
      onSuccess?.();
    },
  });

  const updateMutation = useMutation({
    mutationFn: (data: Partial<IntentActionFormData>) => {
      if (!action) throw new Error('Action ID required');
      let config_json = undefined;
      if (data.config_json !== undefined) {
        if (data.config_json && data.config_json.trim()) {
          try {
            config_json = JSON.parse(data.config_json);
          } catch (e) {
            throw new Error('Invalid JSON in config_json');
          }
        } else {
          config_json = null;
        }
      }
      return intentsApi.updateAction(tenantId, intentId, action.id, {
        action_type: data.action_type,
        config_json,
        priority: data.priority,
      } as any);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['intent', tenantId, intentId] });
      onSuccess?.();
    },
  });

  const onSubmit = (data: IntentActionFormData) => {
    if (!validateConfigJson(data.config_json)) {
      return;
    }
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
        label="Action Type"
        {...register('action_type', { required: 'Action type là bắt buộc' })}
        error={errors.action_type?.message}
        options={[
          { value: 'query_db', label: 'Query DB' },
          { value: 'handoff', label: 'Handoff' },
          { value: 'refuse', label: 'Refuse' },
          { value: 'rag', label: 'RAG' },
        ]}
        required
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
        helperText="Priority cao hơn = thực thi trước"
      />

      <Textarea
        label="Config JSON"
        {...register('config_json', {
          validate: (value) => validateConfigJson(value),
        })}
        error={errors.config_json?.message || configError}
        helperText="Optional: Action configuration as JSON"
        rows={6}
        placeholder='{"domain": "product", "action": "get_info"}'
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
