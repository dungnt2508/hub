'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import AdminLayout from '@/components/AdminLayout';
import { Route, Hash, FileText, TestTube, FileSearch, Users, Code, Database, FlaskConical, PlaySquare } from 'lucide-react';
import Link from 'next/link';
import UseCaseList from '@/components/UseCaseList';

export default function AdminDashboard() {
  const [user, setUser] = useState<any>(null);

  useEffect(() => {
    // Load user from localStorage (middleware already checked auth)
    const userStr = localStorage.getItem('admin_user');
    if (userStr) {
      try {
        setUser(JSON.parse(userStr));
      } catch (e) {
        console.error('Failed to parse user from localStorage', e);
      }
    }
  }, []);

  const quickLinks = [
    {
      href: '/admin/patterns',
      icon: Hash,
      title: 'Pattern Rules',
      description: 'Quản lý regex patterns cho routing',
      color: 'bg-blue-500',
    },
    {
      href: '/admin/keywords',
      icon: Hash,
      title: 'Keyword Hints',
      description: 'Quản lý keyword hints cho domain boosting',
      color: 'bg-green-500',
    },
    {
      href: '/admin/routing/rules',
      icon: Route,
      title: 'Routing Rules',
      description: 'Quản lý intent-based routing',
      color: 'bg-purple-500',
    },
    {
      href: '/admin/prompts',
      icon: FileText,
      title: 'Prompt Templates',
      description: 'Quản lý prompt templates với versioning',
      color: 'bg-orange-500',
    },
    {
      href: '/admin/test-sandbox',
      icon: TestTube,
      title: 'Test Sandbox',
      description: 'Test routing với trace visualization',
      color: 'bg-pink-500',
    },
    {
      href: '/admin/domain-sandboxes',
      icon: FlaskConical,
      title: 'Domain Sandboxes',
      description: 'Domain-specific risk simulators (DBA, HR, Catalog)',
      color: 'bg-amber-500',
    },
    {
      href: '/admin/domain-sandboxes/dba',
      icon: Database,
      title: 'DBA Risk Simulator',
      description: 'Test database operations safety và risk assessment',
      color: 'bg-red-500',
    },
    {
      href: '/admin/dba/use-cases',
      icon: PlaySquare,
      title: 'DBA Use Cases',
      description: 'Metadata-driven use case execution với query editor',
      color: 'bg-teal-500',
    },
    {
      href: '/admin/audit-logs',
      icon: FileSearch,
      title: 'Audit Logs',
      description: 'Xem lịch sử thay đổi config',
      color: 'bg-indigo-500',
    },
  ];

  return (
    <AdminLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Dashboard</h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Quản lý cấu hình runtime cho bot service
          </p>
        </div>

        {user && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 border border-gray-200 dark:border-gray-700">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              Thông tin tài khoản
            </h2>
            <div className="space-y-1 text-sm">
              <div>
                <span className="text-gray-600 dark:text-gray-400">Email: </span>
                <span className="text-gray-900 dark:text-white">{user.email}</span>
              </div>
              <div>
                <span className="text-gray-600 dark:text-gray-400">Role: </span>
                <span className="text-gray-900 dark:text-white capitalize">{user.role}</span>
              </div>
            </div>
          </div>
        )}

        {/* Available Use Cases */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white flex items-center">
              <Code className="h-5 w-5 mr-2" />
              Use Cases Có Sẵn
            </h2>
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
            Danh sách các use cases (intents) đã được implement trong hệ thống. 
            Sử dụng khi tạo routing rules, pattern rules, hoặc keyword hints.
          </p>
          <UseCaseList />
        </div>

        <div>
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            Quick Links
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {quickLinks.map((link) => {
              const Icon = link.icon;
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 border border-gray-200 dark:border-gray-700 hover:shadow-lg transition-shadow"
                >
                  <div className="flex items-start space-x-4">
                    <div className={`${link.color} p-3 rounded-lg`}>
                      <Icon className="h-6 w-6 text-white" />
                    </div>
                    <div className="flex-1">
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-1">
                        {link.title}
                      </h3>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        {link.description}
                      </p>
                    </div>
                  </div>
                </Link>
              );
            })}
          </div>
        </div>
      </div>
    </AdminLayout>
  );
}

