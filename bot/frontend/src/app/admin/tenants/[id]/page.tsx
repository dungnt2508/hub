'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import AdminLayout from '@/components/AdminLayout';
import tenantsService, { Tenant } from '@/services/tenants.service';
import { ArrowLeft, Save } from 'lucide-react';
import toast from 'react-hot-toast';
import Link from 'next/link';

export default function EditTenantPage() {
  const router = useRouter();
  const params = useParams();
  const tenantId = params.id as string;
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [tenant, setTenant] = useState<Tenant | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    plan: 'basic',
    web_embed_enabled: false,
    web_embed_origins: '',
    telegram_enabled: false,
    teams_enabled: false,
  });

  useEffect(() => {
    if (tenantId) {
      fetchTenant();
    }
  }, [tenantId]);

  const fetchTenant = async () => {
    try {
      setLoading(true);
      const data = await tenantsService.getTenant(tenantId);
      setTenant(data);
      setFormData({
        name: data.name || '',
        plan: data.plan || 'basic',
        web_embed_enabled: data.web_embed_enabled || false,
        web_embed_origins: data.web_embed_origins?.join(', ') || '',
        telegram_enabled: data.telegram_enabled || false,
        teams_enabled: data.teams_enabled || false,
      });
    } catch (error: any) {
      toast.error(error.message || 'Không thể tải tenant');
      router.push('/admin/tenants');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.name) {
      toast.error('Vui lòng điền đầy đủ thông tin bắt buộc');
      return;
    }

    try {
      setSaving(true);
      await tenantsService.updateTenant(tenantId, {
        ...formData,
        web_embed_origins: formData.web_embed_origins.split(',').map(o => o.trim()),
      });
      toast.success('Đã cập nhật tenant');
      router.push('/admin/tenants');
    } catch (error: any) {
      toast.error(error.message || 'Không thể cập nhật tenant');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <AdminLayout>
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-600 dark:text-gray-400">Đang tải...</div>
        </div>
      </AdminLayout>
    );
  }

  if (!tenant) {
    return null;
  }

  return (
    <AdminLayout>
      <div className="space-y-6">
        <div className="flex items-center space-x-4">
          <Link
            href="/admin/tenants"
            className="text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
          >
            <ArrowLeft className="h-5 w-5" />
          </Link>
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Chỉnh Sửa Tenant</h1>
            <p className="mt-2 text-gray-600 dark:text-gray-400">
              {tenant.name}
            </p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 p-6">
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Tenant Name <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                required
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Plan
              </label>
              <select
                value={formData.plan}
                onChange={(e) => setFormData({ ...formData, plan: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              >
                <option value="basic">Basic</option>
                <option value="professional">Professional</option>
                <option value="enterprise">Enterprise</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Web Embed Origins
              </label>
              <textarea
                value={formData.web_embed_origins}
                onChange={(e) => setFormData({ ...formData, web_embed_origins: e.target.value })}
                rows={3}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
              <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                Comma-separated list of allowed origins
              </p>
            </div>

            <div className="space-y-4">
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="web_embed_enabled"
                  checked={formData.web_embed_enabled}
                  onChange={(e) => setFormData({ ...formData, web_embed_enabled: e.target.checked })}
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                />
                <label htmlFor="web_embed_enabled" className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                  Enable Web Embed
                </label>
              </div>

              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="telegram_enabled"
                  checked={formData.telegram_enabled}
                  onChange={(e) => setFormData({ ...formData, telegram_enabled: e.target.checked })}
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                />
                <label htmlFor="telegram_enabled" className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                  Enable Telegram Bot
                </label>
              </div>

              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="teams_enabled"
                  checked={formData.teams_enabled}
                  onChange={(e) => setFormData({ ...formData, teams_enabled: e.target.checked })}
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                />
                <label htmlFor="teams_enabled" className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                  Enable Teams Bot
                </label>
              </div>
            </div>

            <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4">
              <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Rate Limits</h3>
              <div className="text-sm text-gray-600 dark:text-gray-400">
                <div>{tenant.rate_limit_per_hour} requests/hour</div>
                <div>{tenant.rate_limit_per_day} requests/day</div>
              </div>
            </div>

            <div className="flex items-center justify-end space-x-4 pt-4 border-t border-gray-200 dark:border-gray-700">
              <Link
                href="/admin/tenants"
                className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              >
                Hủy
              </Link>
              <button
                type="submit"
                disabled={saving}
                className="flex items-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Save className="h-5 w-5 mr-2" />
                {saving ? 'Đang lưu...' : 'Lưu Thay Đổi'}
              </button>
            </div>
          </div>
        </form>
      </div>
    </AdminLayout>
  );
}

