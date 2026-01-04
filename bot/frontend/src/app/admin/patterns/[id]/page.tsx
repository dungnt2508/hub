'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import AdminLayout from '@/components/AdminLayout';
import adminConfigService, { PatternRule, PatternRuleCreate } from '@/services/admin-config.service';
import { ArrowLeft, Save } from 'lucide-react';
import toast from 'react-hot-toast';
import Link from 'next/link';

export default function EditPatternRulePage() {
  const router = useRouter();
  const params = useParams();
  const ruleId = params.id as string;
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [formData, setFormData] = useState<Partial<PatternRuleCreate>>({});

  useEffect(() => {
    if (ruleId) {
      fetchRule();
    }
  }, [ruleId]);

  const fetchRule = async () => {
    try {
      setLoading(true);
      const rule = await adminConfigService.getPatternRule(ruleId);
      setFormData({
        rule_name: rule.rule_name,
        enabled: rule.enabled,
        pattern_regex: rule.pattern_regex,
        pattern_flags: rule.pattern_flags,
        target_domain: rule.target_domain,
        target_intent: rule.target_intent || '',
        intent_type: rule.intent_type || 'OPERATION',
        slots_extraction: rule.slots_extraction,
        priority: rule.priority,
        scope: rule.scope,
        scope_filter: rule.scope_filter,
        description: rule.description || '',
      });
    } catch (error: any) {
      toast.error(error.message || 'Không thể tải pattern rule');
      router.push('/admin/patterns');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);

    try {
      await adminConfigService.updatePatternRule(ruleId, formData);
      toast.success('Đã cập nhật pattern rule');
      router.push('/admin/patterns');
    } catch (error: any) {
      toast.error(error.message || 'Không thể cập nhật pattern rule');
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

  return (
    <AdminLayout>
      <div className="space-y-6">
        <div className="flex items-center space-x-4">
          <Link
            href="/admin/patterns"
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
          >
            <ArrowLeft className="h-5 w-5" />
          </Link>
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Chỉnh sửa Pattern Rule</h1>
            <p className="mt-2 text-gray-600 dark:text-gray-400">
              Cập nhật pattern rule
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
                value={formData.rule_name || ''}
                onChange={(e) => setFormData({ ...formData, rule_name: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Target Domain *
              </label>
              <input
                type="text"
                required
                value={formData.target_domain || ''}
                onChange={(e) => setFormData({ ...formData, target_domain: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white"
              />
            </div>

            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Pattern Regex *
              </label>
              <input
                type="text"
                required
                value={formData.pattern_regex || ''}
                onChange={(e) => setFormData({ ...formData, pattern_regex: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white font-mono text-sm"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Pattern Flags
              </label>
              <select
                value={formData.pattern_flags || 'IGNORECASE'}
                onChange={(e) => setFormData({ ...formData, pattern_flags: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white"
              >
                <option value="IGNORECASE">IGNORECASE</option>
                <option value="MULTILINE">MULTILINE</option>
                <option value="DOTALL">DOTALL</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Priority
              </label>
              <input
                type="number"
                min="0"
                max="100"
                value={formData.priority || 0}
                onChange={(e) => setFormData({ ...formData, priority: parseInt(e.target.value) || 0 })}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Target Intent
              </label>
              <input
                type="text"
                value={formData.target_intent || ''}
                onChange={(e) => setFormData({ ...formData, target_intent: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Intent Type
              </label>
              <select
                value={formData.intent_type || 'OPERATION'}
                onChange={(e) => setFormData({ ...formData, intent_type: e.target.value as any })}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white"
              >
                <option value="OPERATION">OPERATION</option>
                <option value="KNOWLEDGE">KNOWLEDGE</option>
              </select>
            </div>

            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Description
              </label>
              <textarea
                value={formData.description || ''}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                rows={3}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white"
              />
            </div>
          </div>

          <div className="flex items-center justify-end space-x-4 pt-4 border-t border-gray-200 dark:border-gray-700">
            <Link
              href="/admin/patterns"
              className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            >
              Hủy
            </Link>
            <button
              type="submit"
              disabled={saving}
              className="flex items-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <Save className="h-5 w-5 mr-2" />
              {saving ? 'Đang lưu...' : 'Lưu'}
            </button>
          </div>
        </form>
      </div>
    </AdminLayout>
  );
}

