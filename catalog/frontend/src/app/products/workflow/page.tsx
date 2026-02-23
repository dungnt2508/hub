'use client';

import { useEffect, useState } from 'react';
import Navbar from "@/components/marketplace/Navbar";
import Footer from "@/components/marketplace/Footer";
import TemplateCard from "@/components/marketplace/TemplateCard";
import productService, { Product } from '@/services/product.service';
import { ProductType } from '@gsnake/shared-types';
import { Search, X, ArrowLeft } from 'lucide-react';
import Link from 'next/link';

export default function WorkflowsPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    let isActive = true;
    const timer = setTimeout(async () => {
      try {
        setLoading(true);
        setErrorMessage(null);
        const result = await productService.getProducts({
          type: ProductType.WORKFLOW,
          search: searchQuery || undefined,
          limit: 50,
        });
        if (!isActive) return;
        setProducts(result.products);
        setTotal(result.total);
      } catch (error) {
        if (!isActive) return;
        setErrorMessage('Không thể tải danh sách workflow');
      } finally {
        if (isActive) {
          setLoading(false);
        }
      }
    }, 300);

    return () => {
      isActive = false;
      clearTimeout(timer);
    };
  }, [searchQuery]);

  const formatPrice = (product: Product) => {
    if (product.isFree) return 'Miễn phí';
    if (product.price !== undefined && product.price !== null) {
      const currency = product.currency || 'VND';
      return `${product.price.toLocaleString('vi-VN')} ${currency}`;
    }
    return 'Chưa có giá';
  };

  return (
    <div className="min-h-screen bg-[#0B0C10] text-slate-200 font-sans">
      <Navbar />

      <main className="container mx-auto px-4 py-12">
        <Link
          href="/products"
          className="inline-flex items-center text-slate-400 hover:text-white mb-6 transition-colors"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Quay lại danh sách sản phẩm
        </Link>

        <header className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">
            Tất cả Workflow
          </h1>
          <p className="text-slate-400">
            Danh sách các workflow n8n có sẵn trong catalog
          </p>
        </header>

        {/* Search */}
        <section className="mb-8">
          <div className="relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-500" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Tìm kiếm workflow..."
              className="w-full pl-12 pr-4 py-3 bg-slate-900/50 border border-slate-800 rounded-lg text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-500 hover:text-white transition-colors"
              >
                <X className="h-5 w-5" />
              </button>
            )}
          </div>
        </section>

        {/* Results */}
        <section>
          <div className="mb-4 text-sm text-slate-400">
            Tìm thấy {total} workflow
          </div>

          {loading ? (
            <div className="text-center py-12">
              <div className="h-8 w-8 border-2 border-primary/30 border-t-primary rounded-full animate-spin mx-auto mb-4"></div>
              <p className="text-slate-400">Đang tải...</p>
            </div>
          ) : errorMessage ? (
            <div className="text-center py-12 bg-[#111218] border border-slate-800 rounded-2xl">
              <p className="text-slate-400 mb-2">{errorMessage}</p>
              <p className="text-sm text-slate-500">Vui lòng thử lại sau</p>
            </div>
          ) : products.length === 0 ? (
            <div className="text-center py-12 bg-[#111218] border border-slate-800 rounded-2xl">
              <p className="text-slate-400 mb-2">Không tìm thấy workflow nào</p>
              <p className="text-sm text-slate-500">Thử thay đổi từ khóa tìm kiếm</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8">
              {products.map((workflow) => (
                <TemplateCard
                  key={workflow.id}
                  id={workflow.id}
                  title={workflow.title}
                  description={workflow.description || 'Chưa có mô tả'}
                  price={formatPrice(workflow)}
                  author="Đang cập nhật"
                  downloads={workflow.downloads}
                  rating={workflow.rating}
                  tags={workflow.tags}
                />
              ))}
            </div>
          )}
        </section>
      </main>

      <Footer />
    </div>
  );
}

