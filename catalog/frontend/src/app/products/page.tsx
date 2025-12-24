'use client';

import { useState, useEffect } from 'react';
import Navbar from "@/components/marketplace/Navbar";
import Footer from "@/components/marketplace/Footer";
import TemplateCard from "@/components/marketplace/TemplateCard";
import productService, { Product, ProductFilters } from '@/services/product.service';
import { ProductType } from '@gsnake/shared-types';
import { Search, X } from 'lucide-react';
import toast from 'react-hot-toast';

const PRODUCT_TYPES = [
  { value: 'all' as const, label: 'Tất cả' },
  { value: 'workflow' as const, label: 'Workflow' },
  { value: 'tool' as const, label: 'Tool' },
  { value: 'integration' as const, label: 'Integration Pack' },
];

export default function ProductsPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedType, setSelectedType] = useState<'all' | 'workflow' | 'tool' | 'integration'>('all');
  const [total, setTotal] = useState(0);

  useEffect(() => {
    fetchProducts();
  }, [selectedType, searchQuery]);

  const fetchProducts = async () => {
    try {
      setLoading(true);
      const filters: ProductFilters = {
        search: searchQuery || undefined,
        type: selectedType !== 'all' ? selectedType as ProductType : undefined,
        limit: 50 as number | undefined,
      };
      
      const result = await productService.getProducts(filters);
      setProducts(result.products);
      setTotal(result.total);
    } catch (error: any) {
      toast.error('Không thể tải danh sách sản phẩm');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-white dark:bg-[#0B0C10] text-gray-900 dark:text-slate-200 font-sans">
      <Navbar />

      <main className="container mx-auto px-4 py-12">
        <header className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            Catalog workflow & tool n8n
          </h1>
          <p className="text-gray-600 dark:text-slate-400">
            Danh sách template nội bộ: workflow, tool UI, integration pack có thể plug-and-play.
          </p>
        </header>

        {/* Search and Filters */}
        <section className="mb-8 space-y-4">
          <div className="relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400 dark:text-slate-500" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Tìm kiếm workflow, tool, hoặc tag..."
              className="w-full pl-12 pr-4 py-3 bg-gray-100 dark:bg-slate-900/50 border border-gray-200 dark:border-slate-800 rounded-lg text-gray-900 dark:text-white placeholder:text-gray-400 dark:placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 dark:text-slate-500 hover:text-gray-900 dark:hover:text-white transition-colors"
              >
                <X className="h-5 w-5" />
              </button>
            )}
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <div className="flex flex-wrap gap-2">
              {PRODUCT_TYPES.map((type) => (
                <button
                  key={type.value}
                  onClick={() => setSelectedType(type.value)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    selectedType === type.value
                      ? 'bg-primary text-white'
                      : 'bg-gray-100 dark:bg-slate-900/50 border border-gray-200 dark:border-slate-800 text-gray-700 dark:text-slate-300 hover:bg-gray-200 dark:hover:bg-slate-800/50'
                  }`}
                >
                  {type.label}
                </button>
              ))}
            </div>

            {selectedType !== 'all' && (
              <button
                onClick={() => setSelectedType('all')}
                className="text-sm text-gray-500 dark:text-slate-500 hover:text-gray-700 dark:hover:text-slate-300 transition-colors"
              >
                Xóa bộ lọc
              </button>
            )}
          </div>
        </section>

        {/* Results */}
        <section>
          <div className="mb-4 text-sm text-gray-600 dark:text-slate-400">
            Tìm thấy {total} sản phẩm
          </div>

          {loading ? (
            <div className="text-center py-12">
              <div className="h-8 w-8 border-2 border-primary/30 border-t-primary rounded-full animate-spin mx-auto mb-4"></div>
              <p className="text-gray-600 dark:text-slate-400">Đang tải...</p>
            </div>
          ) : products.length === 0 ? (
            <div className="text-center py-12 bg-gray-50 dark:bg-[#111218] border border-gray-200 dark:border-slate-800 rounded-2xl">
              <p className="text-gray-600 dark:text-slate-400 mb-2">Không tìm thấy sản phẩm nào</p>
              <p className="text-sm text-gray-500 dark:text-slate-500">Thử thay đổi từ khóa tìm kiếm hoặc bộ lọc</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8">
              {products.map((p) => (
                <TemplateCard
                  key={p.id}
                  id={p.id}
                  title={p.title}
                  description={p.description}
                  price={p.isFree ? 'Miễn phí' : `${p.price?.toLocaleString('vi-VN')} VNĐ`}
                  author="Team gsnake"
                  downloads={p.downloads}
                  rating={p.rating}
                  tags={p.tags}
                />
              ))}
            </div>
          )}
        </section>

        {/* Quick Links */}
        {/* <section className="mt-12 pt-8 border-t border-slate-800">
          <div className="flex flex-wrap gap-4 justify-center">
            <Link
              href="/products/workflow"
              className="px-6 py-2 bg-slate-900/50 border border-slate-800 rounded-lg text-slate-300 hover:bg-slate-800/50 transition-colors"
            >
              Xem tất cả Workflow →
            </Link>
            <Link
              href="/products/tools"
              className="px-6 py-2 bg-slate-900/50 border border-slate-800 rounded-lg text-slate-300 hover:bg-slate-800/50 transition-colors"
            >
              Xem tất cả Tool →
            </Link>
          </div>
        </section> */}
      </main>

      <Footer />
    </div>
  );
}
