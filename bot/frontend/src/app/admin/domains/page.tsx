'use client';

import { useState, useEffect } from 'react';
import AdminLayout from '@/components/AdminLayout';
import { apiClient } from '@/shared/api/client';
import { FolderTree, Database, Users, Code, CheckCircle } from 'lucide-react';
import toast from 'react-hot-toast';
import Link from 'next/link';

interface Domain {
  name: string;
  display_name: string;
  description: string;
  intent_type: string;
  intents: Array<{
    intent: string;
    display_name: string;
    description: string;
    intent_type: string;
  }>;
}

export default function DomainsPage() {
  const [domains, setDomains] = useState<Domain[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDomains();
  }, []);

  const fetchDomains = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get<{ domains: Domain[] }>('/api/admin/v1/use-cases');
      setDomains(response.domains || []);
    } catch (error: any) {
      toast.error(error.message || 'Không thể tải domains');
    } finally {
      setLoading(false);
    }
  };

  const getDomainIcon = (domainName: string) => {
    switch (domainName) {
      case 'hr':
        return Users;
      case 'dba':
        return Database;
      case 'catalog':
        return FolderTree;
      default:
        return Code;
    }
  };

  const getDomainColor = (domainName: string) => {
    switch (domainName) {
      case 'hr':
        return 'bg-blue-500';
      case 'dba':
        return 'bg-purple-500';
      case 'catalog':
        return 'bg-green-500';
      default:
        return 'bg-gray-500';
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
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Domains Overview</h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Tổng quan về các domains và use cases trong hệ thống
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {domains.map((domain) => {
            const Icon = getDomainIcon(domain.name);
            const color = getDomainColor(domain.name);
            
            return (
              <div
                key={domain.name}
                className="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 p-6 hover:shadow-lg transition-shadow"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center">
                    <div className={`${color} p-3 rounded-lg mr-3`}>
                      <Icon className="h-6 w-6 text-white" />
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                        {domain.display_name}
                      </h3>
                      <p className="text-sm text-gray-500 dark:text-gray-400">{domain.name}</p>
                    </div>
                  </div>
                </div>

                <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                  {domain.description}
                </p>

                <div className="mb-4">
                  <div className="flex items-center justify-between text-sm mb-2">
                    <span className="text-gray-600 dark:text-gray-400">Use Cases:</span>
                    <span className="font-semibold text-gray-900 dark:text-white">
                      {domain.intents.length}
                    </span>
                  </div>
                  <div className="space-y-1">
                    {domain.intents.slice(0, 3).map((intent) => (
                      <div
                        key={intent.intent}
                        className="text-xs text-gray-500 dark:text-gray-400 flex items-center"
                      >
                        <CheckCircle className="h-3 w-3 mr-1 text-green-500" />
                        {intent.display_name}
                      </div>
                    ))}
                    {domain.intents.length > 3 && (
                      <div className="text-xs text-gray-400">
                        +{domain.intents.length - 3} more...
                      </div>
                    )}
                  </div>
                </div>

                {domain.name === 'dba' && (
                  <Link
                    href="/admin/dba/connections"
                    className="text-sm text-primary-600 hover:text-primary-700 dark:text-primary-400 dark:hover:text-primary-300"
                  >
                    Quản lý Connections →
                  </Link>
                )}
              </div>
            );
          })}
        </div>

        {/* Summary */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 p-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Summary</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <div className="text-2xl font-bold text-gray-900 dark:text-white">
                {domains.length}
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">Total Domains</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-gray-900 dark:text-white">
                {domains.reduce((sum, d) => sum + d.intents.length, 0)}
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">Total Use Cases</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-gray-900 dark:text-white">
                {domains.filter((d) => d.intent_type === 'OPERATION').length}
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">Operation Domains</div>
            </div>
          </div>
        </div>
      </div>
    </AdminLayout>
  );
}

