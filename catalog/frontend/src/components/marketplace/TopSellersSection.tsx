'use client';

import Link from 'next/link';
import { Star, ShieldCheck } from 'lucide-react';
import { useState, useEffect } from 'react';

interface Seller {
  id: string;
  name: string;
  avatar: string;
  rating: number;
  reviewCount: number;
  productCount: number;
  description: string;
  verified: boolean;
  sales?: number;
}

export default function TopSellersSection() {
  const [sellers, setSellers] = useState<Seller[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Mock sellers data
    const mockSellers: Seller[] = [
      {
        id: '1',
        name: 'gsnake Team',
        avatar: '🐍',
        rating: 4.9,
        reviewCount: 324,
        productCount: 28,
        description: 'Premium n8n workflows & automation solutions',
        verified: true,
        sales: 2400,
      },
      {
        id: '2',
        name: 'Automation Pro',
        avatar: '⚡',
        rating: 4.8,
        reviewCount: 156,
        productCount: 15,
        description: 'Advanced marketing & CRM automation',
        verified: true,
        sales: 1200,
      },
      {
        id: '3',
        name: 'Data Ninja',
        avatar: '🥷',
        rating: 4.7,
        reviewCount: 89,
        productCount: 12,
        description: 'Data processing & analytics workflows',
        verified: true,
        sales: 850,
      },
      {
        id: '4',
        name: 'Integration Master',
        avatar: '🔌',
        rating: 4.6,
        reviewCount: 124,
        productCount: 18,
        description: 'API integration & webhook solutions',
        verified: false,
        sales: 650,
      },
    ];

    setSellers(mockSellers);
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
            Người Bán Nổi Bật
          </h2>
          <p className="text-lg text-gray-600 dark:text-slate-400 max-w-2xl mx-auto">
            Những nhà phát triển hàng đầu với các workflow chất lượng cao
          </p>
        </div>

        {/* Sellers Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {sellers.map((seller) => (
            <Link key={seller.id} href={`/seller/${seller.id}`}>
              <div className="group h-full bg-gradient-to-br from-white to-gray-50 dark:from-slate-900/50 dark:to-slate-800/30 border border-gray-200 dark:border-slate-800 rounded-xl p-6 hover:shadow-lg hover:border-primary/50 dark:hover:border-primary/30 transition-all duration-300 hover:-translate-y-1 cursor-pointer">
                {/* Avatar */}
                <div className="flex flex-col items-center mb-6">
                  <div className="w-16 h-16 rounded-full bg-gradient-to-br from-primary to-orange-600 flex items-center justify-center text-4xl mb-3 group-hover:scale-110 transition-transform duration-300 shadow-lg">
                    {seller.avatar}
                  </div>

                  {/* Verified Badge */}
                  {seller.verified && (
                    <div className="absolute mt-14 bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 p-1.5 rounded-full">
                      <ShieldCheck className="h-4 w-4" />
                    </div>
                  )}
                </div>

                {/* Content */}
                <div className="text-center">
                  <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-1 group-hover:text-primary transition-colors line-clamp-2">
                    {seller.name}
                  </h3>
                  <p className="text-sm text-gray-600 dark:text-slate-400 mb-4 line-clamp-2">
                    {seller.description}
                  </p>

                  {/* Rating */}
                  <div className="flex items-center justify-center gap-2 mb-4">
                    <div className="flex items-center gap-1">
                      <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                      <span className="font-bold text-gray-900 dark:text-white">
                        {seller.rating}
                      </span>
                    </div>
                    <span className="text-xs text-gray-500 dark:text-slate-500">
                      ({seller.reviewCount} reviews)
                    </span>
                  </div>

                  {/* Stats */}
                  <div className="grid grid-cols-2 gap-3 mb-6 py-4 border-y border-gray-200 dark:border-slate-700">
                    <div>
                      <p className="text-2xl font-bold text-primary">
                        {seller.productCount}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-slate-500">
                        Workflows
                      </p>
                    </div>
                    <div>
                      <p className="text-2xl font-bold text-gray-900 dark:text-white">
                        {seller.sales ? (seller.sales / 100).toFixed(0) + 'K' : '-'}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-slate-500">
                        Downloads
                      </p>
                    </div>
                  </div>

                  {/* CTA Button */}
                  <button className="w-full bg-primary hover:bg-[#FF8559] text-white px-4 py-2.5 rounded-lg font-semibold transition-all duration-300 hover:shadow-lg hover:shadow-primary/30 group-hover:scale-105">
                    Xem Shop
                  </button>
                </div>
              </div>
            </Link>
          ))}
        </div>

        {/* Bottom CTA */}
        <div className="mt-16 text-center">
          <p className="text-gray-600 dark:text-slate-400 mb-6">
            Bạn cũng muốn bán workflow chất lượng cao?
          </p>
          <Link
            href="/seller/apply"
            className="inline-flex items-center gap-2 bg-gray-900 dark:bg-white text-white dark:text-gray-900 px-8 py-3 rounded-full font-semibold hover:shadow-lg transition-all duration-300 hover:scale-105"
          >
            <span>Trở Thành Seller</span>
            <span>→</span>
          </Link>
        </div>
      </div>
    </section>
  );
}

