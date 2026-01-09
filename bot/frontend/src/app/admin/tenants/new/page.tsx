'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import AdminLayout from '@/components/AdminLayout';
import tenantsService from '@/services/tenants.service';
import { ArrowLeft, Save } from 'lucide-react';
import toast from 'react-hot-toast';
import Link from 'next/link';

export default function NewTenantPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [nameError, setNameError] = useState<string>('');
  const [formData, setFormData] = useState({
    name: '',
    web_embed_origins: '',
    plan: 'basic',
    telegram_enabled: false,
    teams_enabled: false,
  });

  const validateName = (name: string): string => {
    if (!name || !name.trim()) {
      return 'Tenant name là bắt buộc';
    }
    if (name.trim().length < 3) {
      return 'Tenant name phải có ít nhất 3 ký tự';
    }
    if (name.trim().length > 255) {
      return 'Tenant name không được vượt quá 255 ký tự';
    }
    // Check for valid characters (alphanumeric, spaces, hyphens, underscores)
    if (!/^[a-zA-Z0-9\s\-_]+$/.test(name.trim())) {
      return 'Tenant name chỉ được chứa chữ cái, số, khoảng trắng, dấu gạch ngang và gạch dưới';
    }
    return '';
  };

  const handleNameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setFormData({ ...formData, name: value });
    setNameError(validateName(value));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    const nameValidationError = validateName(formData.name);
    if (nameValidationError) {
      setNameError(nameValidationError);
      toast.error(nameValidationError);
      return;
    }
    
    if (!formData.name || !formData.web_embed_origins) {
      toast.error('Vui lòng điền đầy đủ thông tin bắt buộc');
      return;
    }

    try {
      setLoading(true);
      await tenantsService.createTenant({
        name: formData.name.trim(),
        web_embed_origins: formData.web_embed_origins.split(',').map(o => o.trim()).filter(o => o),
      });
      toast.success('Đã tạo tenant');
      router.push('/admin/tenants');
    } catch (error: any) {
      const errorMessage = error.message || 'Không thể tạo tenant';
      if (errorMessage.includes('already exists') || errorMessage.includes('duplicate')) {
        setNameError('Tenant name đã tồn tại. Vui lòng chọn tên khác.');
      }
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

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
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Tạo Tenant</h1>
            <p className="mt-2 text-gray-600 dark:text-gray-400">
              Tạo tenant mới cho multi-tenant system
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
                onChange={handleNameChange}
                onBlur={() => {
                  if (formData.name) {
                    setNameError(validateName(formData.name));
                  }
                }}
                placeholder="e.g., GSNAKE Catalog"
                className={`w-full px-4 py-2 border rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent ${
                  nameError
                    ? 'border-red-500 dark:border-red-500'
                    : 'border-gray-300 dark:border-gray-600'
                }`}
              />
              {nameError && (
                <p className="mt-1 text-sm text-red-600 dark:text-red-400">{nameError}</p>
              )}
              <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                Tên tenant phải duy nhất, từ 3-255 ký tự, chỉ chứa chữ cái, số, khoảng trắng, dấu gạch ngang và gạch dưới
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Web Embed Origins <span className="text-red-500">*</span>
              </label>
              <textarea
                required
                value={formData.web_embed_origins}
                onChange={(e) => setFormData({ ...formData, web_embed_origins: e.target.value })}
                placeholder="e.g., https://catalog.example.com, https://www.example.com"
                rows={3}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
              <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                Comma-separated list of allowed origins
              </p>
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

            <div className="space-y-4">
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

            <div className="flex items-center justify-end space-x-4 pt-4 border-t border-gray-200 dark:border-gray-700">
              <Link
                href="/admin/tenants"
                className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              >
                Hủy
              </Link>
              <button
                type="submit"
                disabled={loading}
                className="flex items-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Save className="h-5 w-5 mr-2" />
                {loading ? 'Đang tạo...' : 'Tạo Tenant'}
              </button>
            </div>
          </div>
        </form>
      </div>
    </AdminLayout>
  );
}

