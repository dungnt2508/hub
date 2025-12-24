'use client';

import Link from 'next/link';
import { Star, TrendingUp, Download } from 'lucide-react';
import { useEffect, useState } from 'react';

interface TrendingProduct {
  id: string;
  title: string;
  rating: number;
  downloads: number;
  trend: number; // +250, -100
  description: string;
  tags: string[];
  isNew: boolean;
}

export default function TrendingSection() {
  const [products, setProducts] = useState<TrendingProduct[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Mock trending data - replace with API call
    const mockTrending: TrendingProduct[] = [
      {
        id: '1',
        title: 'Email Marketing Automation',
        rating: 4.8,
        downloads: 2500,
        trend: 520,
        description: 'Tự động gửi email campaign, tracking engagement',
        tags: ['Email', 'Marketing', 'Automation'],
        isNew: false,
      },
      {
        id: '2',
        title: 'CRM to Notion Sync',
        rating: 4.7,
        downloads: 1800,
        trend: 380,
        description: 'Đồng bộ CRM data sang Notion workspace',
        tags: ['CRM', 'Notion', 'Integration'],
        isNew: true,
      },
      {
        id: '3',
        title: 'Instagram Post Scheduler',
        rating: 4.6,
        downloads: 1500,
        trend: -120,
        description: 'Schedule & auto-post hình ảnh lên Instagram',
        tags: ['Social Media', 'Instagram', 'Marketing'],
        isNew: false,
      },
      {
        id: '4',
        title: 'AI Content Generator',
        rating: 4.9,
        downloads: 3200,
        trend: 650,
        description: 'Generate AI-powered content cho blog, email',
        tags: ['AI', 'Content', 'Automation'],
        isNew: true,
      },
      {
        id: '5',
        title: 'Slack Notification Hub',
        rating: 4.5,
        downloads: 1200,
        trend: 220,
        description: 'Gửi thông báo đặc biệt lên Slack channel',
        tags: ['Slack', 'Notification', 'Integration'],
        isNew: false,
      },
      {
        id: '6',
        title: 'Lead Scoring Pipeline',
        rating: 4.7,
        downloads: 900,
        trend: 340,
        description: 'Tự động đánh giá điểm lead từ email interaction',
        tags: ['Sales', 'CRM', 'AI'],
        isNew: true,
      },
    ];

    setProducts(mockTrending);
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
    <section className="py-20 px-4 bg-gray-50 dark:bg-slate-900/30">
      <div className="container mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-12">
          <div>
            <h2 className="text-4xl font-bold text-gray-900 dark:text-white mb-2 flex items-center gap-3">
              <TrendingUp className="h-8 w-8 text-primary" />
              Workflows Được Yêu Thích
            </h2>
            <p className="text-gray-600 dark:text-slate-400">
              Các workflow được download nhiều nhất và được rating cao nhất tuần này
            </p>
          </div>
        </div>

        {/* Products List */}
        <div className="space-y-4">
          {products.map((product, index) => (
            <Link key={product.id} href={`/products/${product.id}`}>
              <div className="group bg-white dark:bg-slate-800/50 border border-gray-200 dark:border-slate-700 rounded-xl p-6 hover:shadow-lg hover:border-primary/50 dark:hover:border-primary/30 transition-all duration-300 cursor-pointer">
                <div className="flex items-center gap-6">
                  {/* Rank Badge */}
                  <div className="flex-shrink-0">
                    <div className={`flex items-center justify-center h-12 w-12 rounded-full font-bold text-white ${
                      index === 0 ? 'bg-yellow-500' :
                      index === 1 ? 'bg-gray-400' :
                      index === 2 ? 'bg-orange-600' :
                      'bg-gray-600'
                    }`}>
                      #{index + 1}
                    </div>
                  </div>

                  {/* Content */}
                  <div className="flex-grow">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="text-lg font-bold text-gray-900 dark:text-white group-hover:text-primary transition-colors">
                        {product.title}
                      </h3>
                      {product.isNew && (
                        <span className="inline-block px-2.5 py-0.5 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 text-xs font-bold rounded-full">
                          MỚI
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-gray-600 dark:text-slate-400 mb-3">
                      {product.description}
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {product.tags.map((tag) => (
                        <span
                          key={tag}
                          className="inline-block px-3 py-1 bg-gray-100 dark:bg-slate-700 text-gray-700 dark:text-slate-300 text-xs font-medium rounded-full"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Stats */}
                  <div className="flex-shrink-0 flex items-center gap-8">
                    {/* Rating */}
                    <div className="text-center">
                      <div className="flex items-center gap-1 mb-1">
                        <Star className="h-5 w-5 fill-yellow-400 text-yellow-400" />
                        <span className="font-bold text-gray-900 dark:text-white">
                          {product.rating}
                        </span>
                      </div>
                      <p className="text-xs text-gray-500 dark:text-slate-500">Rating</p>
                    </div>

                    {/* Downloads */}
                    <div className="text-center">
                      <div className="flex items-center gap-1 mb-1">
                        <Download className="h-5 w-5 text-primary" />
                        <span className="font-bold text-gray-900 dark:text-white">
                          {(product.downloads / 1000).toFixed(1)}K
                        </span>
                      </div>
                      <p className="text-xs text-gray-500 dark:text-slate-500">Downloads</p>
                    </div>

                    {/* Trend */}
                    <div className="text-center">
                      <div className={`flex items-center gap-1 mb-1 font-bold ${
                        product.trend > 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
                      }`}>
                        <TrendingUp className={`h-5 w-5 ${product.trend < 0 ? 'rotate-180' : ''}`} />
                        <span>{Math.abs(product.trend)}</span>
                      </div>
                      <p className="text-xs text-gray-500 dark:text-slate-500">Tuần này</p>
                    </div>

                    {/* Arrow */}
                    <span className="text-2xl text-gray-400 dark:text-slate-600 group-hover:text-primary group-hover:translate-x-2 transition-all">
                      →
                    </span>
                  </div>
                </div>
              </div>
            </Link>
          ))}
        </div>

        {/* View All CTA */}
        <div className="mt-12 text-center">
          <Link
            href="/products"
            className="inline-flex items-center gap-2 text-primary hover:text-[#FF8559] font-semibold text-lg transition-colors"
          >
            <span>Xem Tất Cả Workflows Trending</span>
            <span>→</span>
          </Link>
        </div>
      </div>
    </section>
  );
}

