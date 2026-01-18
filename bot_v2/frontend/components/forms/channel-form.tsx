'use client';

import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { Input } from './input';
import { Select } from './select';
import { Textarea } from './textarea';
import { Button } from './button';
import { channelsApi } from '@/lib/api';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import type { Channel, UUID } from '@/lib/types';

interface ChannelFormProps {
  tenantId: UUID;
  channel?: Channel;
  onSuccess?: () => void;
  onCancel?: () => void;
}

interface ChannelFormData {
  type: string;
  enabled: boolean;
  config_json?: string; // JSON string for editing
}

export function ChannelForm({ tenantId, channel, onSuccess, onCancel }: ChannelFormProps) {
  const isEdit = !!channel;
  const queryClient = useQueryClient();
  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
    watch,
  } = useForm<ChannelFormData>({
    defaultValues: {
      type: channel?.type || '',
      enabled: channel?.enabled ?? true,
      config_json: channel?.config_json ? JSON.stringify(channel.config_json, null, 2) : '',
    },
  });

  useEffect(() => {
    if (channel) {
      reset({
        type: channel.type,
        enabled: channel.enabled,
        config_json: channel.config_json ? JSON.stringify(channel.config_json, null, 2) : '',
      });
    }
  }, [channel, reset]);

  const createMutation = useMutation({
    mutationFn: (data: ChannelFormData) => {
      let config_json = undefined;
      if (data.config_json && data.config_json.trim()) {
        try {
          config_json = JSON.parse(data.config_json);
        } catch (e) {
          throw new Error('Invalid JSON in config_json');
        }
      }
      return channelsApi.create(tenantId, {
        type: data.type,
        enabled: data.enabled,
        config_json,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['channels', tenantId] });
      onSuccess?.();
    },
  });

  const updateMutation = useMutation({
    mutationFn: (data: Partial<ChannelFormData>) => {
      if (!channel) throw new Error('Channel ID required');
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
      return channelsApi.update(tenantId, channel.id, {
        type: data.type,
        enabled: data.enabled,
        config_json,
      } as any);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['channels', tenantId] });
      onSuccess?.();
    },
  });

  const onSubmit = (data: ChannelFormData) => {
    if (isEdit) {
      updateMutation.mutate(data);
    } else {
      createMutation.mutate(data);
    }
  };

  const isLoading = createMutation.isPending || updateMutation.isPending;
  const configJson = watch('config_json');
  const [configError, setConfigError] = useState<string>('');

  const validateConfigJson = (value: string) => {
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

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <Input
        label="Channel Type"
        {...register('type', { required: 'Channel type là bắt buộc' })}
        error={errors.type?.message}
        required
        helperText="Ví dụ: web, telegram, whatsapp, etc."
      />

      <div className="flex items-center gap-2">
        <input
          type="checkbox"
          id="enabled"
          {...register('enabled')}
          className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
        />
        <label htmlFor="enabled" className="text-sm font-medium text-gray-700">
          Enabled
        </label>
      </div>

      <Textarea
        label="Config JSON"
        {...register('config_json', {
          validate: validateConfigJson,
        })}
        error={errors.config_json?.message || configError}
        helperText="Optional: Channel configuration as JSON"
        rows={6}
        placeholder='{"webhook_url": "https://...", "api_key": "..."}'
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
