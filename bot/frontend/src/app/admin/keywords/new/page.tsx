'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import AdminLayout from '@/components/AdminLayout';
import adminConfigService, { KeywordHint } from '@/services/admin-config.service';
import { ArrowLeft, Save, Plus, X } from 'lucide-react';
import toast from 'react-hot-toast';
import Link from 'next/link';

export default function NewKeywordHintPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    rule_name: '',
    enabled: true,
    domain: '',
    keywords: {} as Record<string, number>,
    scope: 'global',
    description: '',
  });
  const [keywordInput, setKeywordInput] = useState('');
  const [weightInput, setWeightInput] = useState('1.0');

  const handleAddKeyword = () => {
    if (!keywordInput.trim()) return;
    const weight = parseFloat(weightInput) || 1.0;
    setFormData({
      ...formData,
      keywords: { ...formData.keywords, [keywordInput.trim()]: weight },
    });
    setKeywordInput('');
    setWeightInput('1.0');
  };

  const handleRemoveKeyword = (keyword: string) => {
    const newKeywords = { ...formData.keywords };
    delete newKeywords[keyword];
    setFormData({ ...formData, keywords: newKeywords });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (Object.keys(formData.keywords).length === 0) {
      toast.error('Vui lòng thêm ít nhất một keyword');
      return;
    }

    setLoading(true);
    try {
      await adminConfigService.createKeywordHint(formData);
      toast.success('Đã tạo keyword hint');
      router.push('/admin/keywords');
    } catch (error: any) {
      toast.error(error.message || 'Không thể tạo keyword hint');
    } finally {
      setLoading(false);
    }
  };

  return (
    <AdminLayout>
      <div className="space-y-6">
        <div className="flex items-center space-x-4">
          <Link
            href="/admin/keywords"
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
          >
            <ArrowLeft className="h-5 w-5" />
          </Link>
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Tạo Keyword Hint</h1>
            <p className="mt-2 text-gray-600 dark:text-gray-400">
              Tạo keyword hint mới cho domain boosting
            </p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 p-6 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Rule Name *
              </label>
              <input
                type="text"
                required
                value={formData.rule_name}
                onChange={(e) => setFormData({ ...formData, rule_name: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white"
                placeholder="HR Keywords"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Domain *
              </label>
              <input
                type="text"
                required
                value={formData.domain}
                onChange={(e) => setFormData({ ...formData, domain: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white"
                placeholder="hr"
              />
            </div>

            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Keywords *
              </label>
              <div className="flex space-x-2 mb-3">
                <input
                  type="text"
                  value={keywordInput}
                  onChange={(e) => setKeywordInput(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddKeyword())}
                  placeholder="Keyword"
                  className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white"
                />
                <input
                  type="number"
                  step="0.1"
                  min="0"
                  value={weightInput}
                  onChange={(e) => setWeightInput(e.target.value)}
                  placeholder="Weight"
                  className="w-24 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white"
                />
                <button
                  type="button"
                  onClick={handleAddKeyword}
                  className="flex items-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
                >
                  <Plus className="h-5 w-5" />
                </button>
              </div>
              <div className="flex flex-wrap gap-2">
                {Object.entries(formData.keywords).map(([keyword, weight]) => (
                  <span
                    key={keyword}
                    className="inline-flex items-center px-3 py-1 bg-primary-100 dark:bg-primary-900/30 text-primary-800 dark:text-primary-400 rounded-lg text-sm"
                  >
                    {keyword} ({weight})
                    <button
                      type="button"
                      onClick={() => handleRemoveKeyword(keyword)}
                      className="ml-2 hover:text-primary-600"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </span>
                ))}
              </div>
              {Object.keys(formData.keywords).length === 0 && (
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Chưa có keywords. Nhập keyword và weight rồi nhấn + để thêm.
                </p>
              )}
            </div>

            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Description
              </label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                rows={3}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white"
                placeholder="Mô tả keyword hint này..."
              />
            </div>
          </div>

          <div className="flex items-center justify-end space-x-4 pt-4 border-t border-gray-200 dark:border-gray-700">
            <Link
              href="/admin/keywords"
              className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            >
              Hủy
            </Link>
            <button
              type="submit"
              disabled={loading}
              className="flex items-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <Save className="h-5 w-5 mr-2" />
              {loading ? 'Đang lưu...' : 'Lưu'}
            </button>
          </div>
        </form>
      </div>
    </AdminLayout>
  );
}

