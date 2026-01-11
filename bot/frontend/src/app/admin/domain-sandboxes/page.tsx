'use client';

import { useState } from 'react';
import AdminLayout from '@/components/AdminLayout';
import Link from 'next/link';
import { Database, Users, Package, Plus } from 'lucide-react';

interface DomainCard {
  id: string;
  icon: React.ReactNode;
  title: string;
  description: string;
  riskLevel: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  href: string;
  focus: string[];
}

const DOMAINS: DomainCard[] = [
  {
    id: 'dba',
    icon: <Database className="h-12 w-12" />,
    title: 'DBA Risk Simulator',
    description: 'Test database operations safety',
    riskLevel: 'CRITICAL',
    href: '/admin/domain-sandboxes/dba',
    focus: ['Connection safety', 'SQL injection', 'Query performance', 'Permissions'],
  },
  {
    id: 'hr',
    icon: <Users className="h-12 w-12" />,
    title: 'HR Policy Simulator',
    description: 'Test leave policies and RBAC',
    riskLevel: 'MEDIUM',
    href: '/admin/domain-sandboxes/hr',
    focus: ['RBAC enforcement', 'Policy compliance', 'Concurrent requests'],
  },
  {
    id: 'catalog',
    icon: <Package className="h-12 w-12" />,
    title: 'Catalog Quality Simulator',
    description: 'Test search and recommendations',
    riskLevel: 'LOW',
    href: '/admin/domain-sandboxes/catalog',
    focus: ['Search quality', 'Recommendations', 'Vector DB fallback'],
  },
];

function getRiskColor(level: string): string {
  switch (level) {
    case 'CRITICAL':
    case 'HIGH':
      return 'text-red-600 dark:text-red-400';
    case 'MEDIUM':
      return 'text-yellow-600 dark:text-yellow-400';
    case 'LOW':
      return 'text-green-600 dark:text-green-400';
    default:
      return 'text-gray-600 dark:text-gray-400';
  }
}

function getRiskBadge(level: string): string {
  switch (level) {
    case 'CRITICAL':
    case 'HIGH':
      return '🔴';
    case 'MEDIUM':
      return '🟡';
    case 'LOW':
      return '🟢';
    default:
      return '⚪';
  }
}

export default function DomainSandboxesPage() {
  return (
    <AdminLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Domain-Specific Risk Simulators
          </h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Test domain-specific risks and failure scenarios before execution
          </p>
        </div>

        {/* Domain Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {DOMAINS.map((domain) => (
            <Link key={domain.id} href={domain.href}>
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 p-6 hover:shadow-lg hover:border-primary-500 dark:hover:border-primary-500 transition-all cursor-pointer h-full">
                <div className="flex items-start justify-between mb-4">
                  <div className="text-primary-600 dark:text-primary-400">
                    {domain.icon}
                  </div>
                  <div className={`text-2xl font-bold ${getRiskColor(domain.riskLevel)}`}>
                    {getRiskBadge(domain.riskLevel)}
                  </div>
                </div>

                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                  {domain.title}
                </h3>

                <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                  {domain.description}
                </p>

                <div className="space-y-2">
                  <div className="text-xs font-medium text-gray-700 dark:text-gray-300 uppercase tracking-wide">
                    Focus Areas:
                  </div>
                  <ul className="space-y-1">
                    {domain.focus.map((item, idx) => (
                      <li
                        key={idx}
                        className="text-sm text-gray-600 dark:text-gray-400 flex items-center"
                      >
                        <span className="w-1.5 h-1.5 bg-primary-600 rounded-full mr-2" />
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                  <span className="text-sm font-medium text-primary-600 dark:text-primary-400 flex items-center">
                    Enter Sandbox →
                  </span>
                </div>
              </div>
            </Link>
          ))}

          {/* Custom Domain Placeholder */}
          <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg border-2 border-dashed border-gray-300 dark:border-gray-600 p-6 flex items-center justify-center">
            <div className="text-center">
              <Plus className="h-12 w-12 text-gray-400 dark:text-gray-500 mx-auto mb-2" />
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                Add Custom Domain
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                Coming soon
              </p>
            </div>
          </div>
        </div>

        {/* Info Box */}
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
          <p className="text-sm text-blue-800 dark:text-blue-200">
            <strong>ℹ️ What is a Risk Simulator?</strong> Each sandbox tests domain-specific risks
            and failure scenarios. It's not a generic test suite, but a production-ready safety
            checker tailored to each domain's critical operations.
          </p>
        </div>
      </div>
    </AdminLayout>
  );
}
