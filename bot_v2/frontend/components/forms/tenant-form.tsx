'use client';

import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { Input } from './input';
import { Select } from './select';
import { Button } from './button';
import { tenantsApi } from '@/lib/api';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import type { Tenant } from '@/lib/types';

interface TenantFormProps {
  tenant?: Tenant;
  onSuccess?: () => void;
  onCancel?: () => void;
}

interface TenantFormData {
  name: string;
  status: string;
  plan?: string;
}

export function TenantForm({ tenant, onSuccess, onCancel }: TenantFormProps) {
  const isEdit = !!tenant;
  const queryClient = useQueryClient();
  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<TenantFormData>({
    defaultValues: {
      name: tenant?.name || '',
      status: tenant?.status || 'active',
      plan: tenant?.plan || '',
    },
  });

  useEffect(() => {
    if (tenant) {
      reset({
        name: tenant.name,
        status: tenant.status,
        plan: tenant.plan || '',
      });
    }
  }, [tenant, reset]);

  const createMutation = useMutation({
    mutationFn: (data: TenantFormData) => tenantsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tenants'] });
      onSuccess?.();
    },
  });

  const updateMutation = useMutation({
    mutationFn: (data: Partial<TenantFormData>) => {
      if (!tenant) throw new Error('Tenant ID required');
      return tenantsApi.update(tenant.id, data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tenants'] });
      queryClient.invalidateQueries({ queryKey: ['tenant', tenant?.id] });
      onSuccess?.();
    },
  });

  const onSubmit = (data: TenantFormData) => {
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
        label="Tên Tenant"
        {...register('name', { required: 'Tên tenant là bắt buộc' })}
        error={errors.name?.message}
        required
      />

      <Select
        label="Status"
        {...register('status', { required: 'Status là bắt buộc' })}
        error={errors.status?.message}
        options={[
          { value: 'active', label: 'Active' },
          { value: 'inactive', label: 'Inactive' },
          { value: 'suspended', label: 'Suspended' },
        ]}
        required
      />

      <Input
        label="Plan"
        {...register('plan')}
        error={errors.plan?.message}
        helperText="Optional: Plan name"
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
