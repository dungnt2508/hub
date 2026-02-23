'use client';

import Link from 'next/link';
import { Zap, Globe, Shield, Cpu, Workflow, BarChart3, Database, AlertCircle } from 'lucide-react';
import { useState, useEffect } from 'react';

interface Category {
  id: string;
  name: string;
  icon: React.ReactNode;
  color: string;
  count: number;
  description: string;
  href: string;
}

export default function CategoryShowcase() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch or define categories
    const defaultCategories: Category[] = [
      {
        id: '1',
        name: 'Marketing & Social',
        icon: <Zap className="h-8 w-8" />,
        color: 'from-orange-500 to-red-500',
        count: 24,
        description: 'Automation cho Instagram, Email, Social Media',
        href: '/products?category=marketing',
      },
      {
        id: '2',
        name: 'Sales & CRM',
        icon: <Globe className="h-8 w-8" />,
        color: 'from-blue-500 to-cyan-500',
        count: 18,
        description: 'Pipeline management, Lead nurturing',
        href: '/products?category=sales',
      },
      {
        id: '3',
        name: 'AI & Automation',
        icon: <Cpu className="h-8 w-8" />,
        color: 'from-purple-500 to-pink-500',
        count: 32,
        description: 'Advanced workflows với AI/ML',
        href: '/products?category=ai',
      },
      {
        id: '4',
        name: 'Data & Analytics',
        icon: <BarChart3 className="h-8 w-8" />,
        color: 'from-green-500 to-emerald-500',
        count: 15,
        description: 'Data processing, Reporting, Insights',
        href: '/products?category=data',
      },
      {
        id: '5',
        name: 'Integrations',
        icon: <Database className="h-8 w-8" />,
        color: 'from-yellow-500 to-orange-500',
        count: 28,
        description: 'API connections, Webhooks, Sync',
        href: '/products?category=integration',
      },
      {
        id: '6',
        name: 'Security & DevOps',
        icon: <Shield className="h-8 w-8" />,
        color: 'from-red-500 to-pink-600',
        count: 12,
        description: 'Monitoring, Alerts, Security',
        href: '/products?category=security',
      },
    ];

    setCategories(defaultCategories);
    setLoading(false);
  }, []);

  if (loading) {
    return (
      <div className="flex justify-center items-center py-20">
        <div className="h-8 w-8 border-2 border-primary/30 border-t-primary rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <section className="py-20 px-4 bg-white dark:bg-[#0B0C10]">
      <div className="container mx-auto">
        {/* Header */}
        <div className="text-center mb-16">
          <h2 className="text-4xl font-bold text-gray-900 dark:text-white mb-4">
            Khám Phá Danh Mục Sản Phẩm
          </h2>
          <p className="text-lg text-gray-600 dark:text-slate-400 max-w-2xl mx-auto">
            Chọn danh mục phù hợp với nhu cầu tự động hóa của bạn
          </p>
        </div>

        {/* Categories Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {categories.map((category) => (
            <Link
              key={category.id}
              href={category.href}
              className="group"
            >
              <div className="h-full bg-gradient-to-br from-white to-gray-50 dark:from-slate-900/50 dark:to-slate-800/30 border border-gray-200 dark:border-slate-800 rounded-2xl p-8 hover:shadow-lg dark:hover:shadow-lg dark:hover:shadow-primary/10 transition-all duration-300 hover:-translate-y-1">
                {/* Icon Background */}
                <div className={`inline-flex p-4 rounded-xl bg-gradient-to-br ${category.color} mb-6 group-hover:scale-110 transition-transform duration-300 text-white`}>
                  {category.icon}
                </div>

                {/* Content */}
                <div className="flex flex-col flex-grow">
                  <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2 group-hover:text-primary transition-colors">
                    {category.name}
                  </h3>
                  <p className="text-sm text-gray-600 dark:text-slate-400 mb-4">
                    {category.description}
                  </p>

                  {/* Count */}
                  <div className="mt-auto flex items-center justify-between">
                    <span className="inline-block px-3 py-1 bg-gray-100 dark:bg-slate-800 rounded-full text-sm font-medium text-gray-700 dark:text-slate-300">
                      {category.count} workflows
                    </span>
                    <span className="text-primary font-semibold group-hover:translate-x-1 transition-transform">
                      →
                    </span>
                  </div>
                </div>
              </div>
            </Link>
          ))}
        </div>

        {/* CTA */}
        <div className="mt-16 text-center">
          <Link
            href="/products"
            className="inline-flex items-center gap-2 bg-primary hover:bg-[#FF8559] text-white px-8 py-4 rounded-full font-semibold transition-all duration-300 hover:shadow-lg hover:shadow-primary/30 hover:scale-105"
          >
            <span>Xem Tất Cả Sản Phẩm</span>
            <span>→</span>
          </Link>
        </div>
      </div>
    </section>
  );
}

