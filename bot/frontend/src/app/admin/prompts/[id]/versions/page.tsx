'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import AdminLayout from '@/components/AdminLayout';
import adminConfigService from '@/services/admin-config.service';
import { ArrowLeft, RotateCcw, CheckCircle } from 'lucide-react';
import toast from 'react-hot-toast';
import Link from 'next/link';

interface TemplateVersion {
  id: string;
  version: number;
  template_text: string;
  is_active: boolean;
  created_at: string;
}

export default function TemplateVersionsPage() {
  const router = useRouter();
  const params = useParams();
  const templateId = params.id as string;
  const [loading, setLoading] = useState(true);
  const [versions, setVersions] = useState<TemplateVersion[]>([]);
  const [rollingBack, setRollingBack] = useState<string | null>(null);

  useEffect(() => {
    if (templateId) {
      fetchVersions();
    }
  }, [templateId]);

  const fetchVersions = async () => {
    try {
      setLoading(true);
      const data = await adminConfigService.listTemplateVersions(templateId);
      setVersions(data);
    } catch (error: any) {
      toast.error(error.message || 'Không thể tải versions');
      router.push('/admin/prompts');
    } finally {
      setLoading(false);
    }
  };

  const handleRollback = async (version: number) => {
    if (!confirm(`Bạn có chắc muốn rollback về version ${version}?`)) return;

    setRollingBack(`${version}`);
    try {
      await adminConfigService.rollbackTemplate(templateId, version);
      toast.success(`Đã rollback về version ${version}`);
      fetchVersions();
    } catch (error: any) {
      toast.error(error.message || 'Không thể rollback');
    } finally {
      setRollingBack(null);
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
            href="/admin/prompts"
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
          >
            <ArrowLeft className="h-5 w-5" />
          </Link>
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Version History</h1>
            <p className="mt-2 text-gray-600 dark:text-gray-400">
              Xem và rollback các versions của prompt template
            </p>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 overflow-hidden">
          <div className="divide-y divide-gray-200 dark:divide-gray-700">
            {versions.map((version) => (
              <div
                key={version.id}
                className="p-6 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <span className="text-lg font-semibold text-gray-900 dark:text-white">
                        Version {version.version}
                      </span>
                      {version.is_active && (
                        <span className="inline-flex items-center px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400">
                          <CheckCircle className="h-3 w-3 mr-1" />
                          Active
                        </span>
                      )}
                      <span className="text-sm text-gray-500 dark:text-gray-400">
                        {new Date(version.created_at).toLocaleString('vi-VN')}
                      </span>
                    </div>
                    <pre className="mt-3 p-4 bg-gray-100 dark:bg-gray-700 rounded-lg text-sm overflow-x-auto whitespace-pre-wrap">
                      {version.template_text}
                    </pre>
                  </div>
                  {!version.is_active && (
                    <button
                      onClick={() => handleRollback(version.version)}
                      disabled={rollingBack === `${version.version}`}
                      className="ml-4 flex items-center px-4 py-2 text-sm bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                      <RotateCcw className="h-4 w-4 mr-2" />
                      {rollingBack === `${version.version}` ? 'Rolling back...' : 'Rollback'}
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </AdminLayout>
  );
}

