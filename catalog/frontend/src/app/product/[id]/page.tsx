'use client';

import { useState, useEffect } from 'react';
import Navbar from "@/components/marketplace/Navbar";
import Footer from "@/components/marketplace/Footer";
import productService, { Product } from '@/services/product.service';
import { ArrowLeft, Check, Shield, Download, MessageCircle, ExternalLink } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import toast from 'react-hot-toast';

export default function ProductDetailPage() {
  const params = useParams();
  const productId = params?.id as string;
  const [product, setProduct] = useState<Product | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (productId) {
      fetchProduct();
    }
  }, [productId]);

  const fetchProduct = async () => {
    try {
      setLoading(true);
      const data = await productService.getProduct(productId);
      setProduct(data);
    } catch (error: any) {
      toast.error('Không thể tải thông tin sản phẩm');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async () => {
    if (!product) return;
    
    try {
      // Record download
      await productService.recordDownload(product.id);
      toast.success('Đang tải workflow...');
    } catch (error: any) {
      toast.error('Không thể tải workflow');
    }
  };

  const handleContact = () => {
    window.location.href = '/contact';
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffDays === 0) return 'Hôm nay';
    if (diffDays === 1) return 'Hôm qua';
    if (diffDays < 7) return `${diffDays} ngày trước`;
    return date.toLocaleDateString('vi-VN');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-white dark:bg-[#0B0C10] text-gray-900 dark:text-slate-200 font-sans">
        <Navbar />
        <main className="container mx-auto px-4 py-12">
          <div className="text-center py-12">
            <div className="h-8 w-8 border-2 border-primary/30 border-t-primary rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-slate-400">Đang tải...</p>
          </div>
        </main>
        <Footer />
      </div>
    );
  }

  if (!product) {
    return (
      <div className="min-h-screen bg-white dark:bg-[#0B0C10] text-gray-900 dark:text-slate-200 font-sans">
        <Navbar />
        <main className="container mx-auto px-4 py-12">
          <div className="text-center py-12">
            <p className="text-slate-400 mb-4">Không tìm thấy sản phẩm</p>
            <Link
              href="/products"
              className="text-primary hover:text-[#FF8559] transition-colors"
            >
              Quay lại danh sách sản phẩm
            </Link>
          </div>
        </main>
        <Footer />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0B0C10] text-slate-200 font-sans">
      <Navbar />

      <main className="container mx-auto px-4 py-12">
        <Link
          href="/products"
          className="inline-flex items-center text-gray-600 dark:text-slate-400 hover:text-gray-900 dark:hover:text-white mb-8 transition-colors"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Quay lại danh sách sản phẩm
        </Link>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-10">
          <section className="lg:col-span-2 space-y-6">
            <header>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-3">
                {product.title}
              </h1>
              <p className="text-gray-600 dark:text-slate-400 max-w-2xl mb-4">
                {product.description}
              </p>
              <div className="flex items-center gap-4 text-sm text-gray-500 dark:text-slate-500">
                <span>Tác giả: Team gsnake</span>
                <span>•</span>
                <span>{product.downloads} lượt tải</span>
                <span>•</span>
                <span>⭐ {product.rating.toFixed(1)}</span>
              </div>
            </header>

            {product.longDescription && (
              <div className="bg-gray-50 dark:bg-[#111218] border border-gray-200 dark:border-slate-800 rounded-2xl p-6">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                  Mô tả chi tiết
                </h2>
                <div 
                  className="text-gray-700 dark:text-slate-300 leading-relaxed prose prose-invert max-w-none"
                  dangerouslySetInnerHTML={{ __html: product.longDescription }}
                />
              </div>
            )}

            <div className="bg-gray-50 dark:bg-[#111218] border border-gray-200 dark:border-slate-800 rounded-2xl p-6">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                Ảnh / Preview workflow
              </h2>
              {product.previewImageUrl ? (
                <div className="aspect-video rounded-xl overflow-hidden">
                  <img
                    src={product.previewImageUrl}
                    alt={product.title}
                    className="w-full h-full object-cover"
                  />
                </div>
              ) : (
                <div className="aspect-video rounded-xl border border-dashed border-gray-300 dark:border-slate-700 bg-gray-100 dark:bg-slate-900/40 flex items-center justify-center text-gray-500 dark:text-slate-500 text-sm">
                  <div className="text-center">
                    <ExternalLink className="h-12 w-12 mx-auto mb-2 text-gray-400 dark:text-slate-600" />
                    <p>Chưa có preview</p>
                  </div>
                </div>
              )}
            </div>

            {product.features && product.features.length > 0 && (
              <div className="bg-gray-50 dark:bg-[#111218] border border-gray-200 dark:border-slate-800 rounded-2xl p-6">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                  Tính năng chính
                </h2>
                <ul className="space-y-3">
                  {product.features.map((f, idx) => (
                    <li key={idx} className="flex gap-3 items-start">
                      <Check className="h-5 w-5 text-primary mt-0.5 flex-shrink-0" />
                      <span className="text-gray-700 dark:text-slate-200">{f}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {product.installGuide && (
              <div className="bg-gray-50 dark:bg-[#111218] border border-gray-200 dark:border-slate-800 rounded-2xl p-6">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                  Hướng dẫn cài đặt cơ bản
                </h2>
                <div className="text-gray-700 dark:text-slate-300 leading-relaxed whitespace-pre-line">
                  {product.installGuide}
                </div>
              </div>
            )}
          </section>

          <aside className="lg:col-span-1">
            <div className="sticky top-24 space-y-6">
              <div className="bg-gray-50 dark:bg-[#111218] border border-gray-200 dark:border-slate-800 rounded-2xl p-6">
                <div className="mb-6">
                  <p className="text-sm text-gray-600 dark:text-slate-400 mb-2">Trạng thái</p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">
                    {product.isFree ? "Miễn phí" : `${product.price?.toLocaleString('vi-VN')} VNĐ`}
                  </p>
                </div>

                <button
                  onClick={handleDownload}
                  className="w-full bg-primary hover:bg-[#FF8559] text-white font-semibold py-3 rounded-lg mb-3 transition-colors flex items-center justify-center gap-2"
                >
                  <Download className="h-4 w-4" />
                  {product.workflowFileUrl ? 'Tải workflow' : 'Liên hệ để tải'}
                </button>
                
                <button
                  onClick={handleContact}
                  className="w-full border border-gray-300 dark:border-slate-700 hover:border-primary text-gray-700 dark:text-slate-100 hover:text-gray-900 dark:hover:text-white font-semibold py-3 rounded-lg transition-colors flex items-center justify-center gap-2"
                >
                  <MessageCircle className="h-4 w-4" />
                  Liên hệ team để cài đặt
                </button>

                <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-slate-500 mt-4 pt-4 border-t border-gray-200 dark:border-slate-800">
                  <Shield className="h-3 w-3 text-primary" />
                  <span>Workflow nội bộ, có thể chỉnh sửa theo yêu cầu.</span>
                </div>
              </div>

              {product.requirements && product.requirements.length > 0 && (
                <div className="bg-gray-50 dark:bg-[#111218] border border-gray-200 dark:border-slate-800 rounded-2xl p-6">
                  <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">
                    Yêu cầu tích hợp
                  </h3>
                  <ul className="space-y-2 text-sm text-gray-700 dark:text-slate-200">
                    {product.requirements.map((r, idx) => (
                      <li key={idx} className="flex items-start gap-2">
                        <span className="text-primary mt-1">•</span>
                        <span>{r}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {product.version && (
                <div className="bg-gray-50 dark:bg-[#111218] border border-gray-200 dark:border-slate-800 rounded-2xl p-6">
                  <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">
                    Thông tin phiên bản
                  </h3>
                  <div className="space-y-2 text-sm text-gray-600 dark:text-slate-400">
                    <div className="flex justify-between">
                      <span>Phiên bản:</span>
                      <span className="text-gray-900 dark:text-slate-200">{product.version}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Cập nhật:</span>
                      <span className="text-gray-900 dark:text-slate-200">{formatDate(product.updatedAt)}</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </aside>
        </div>
      </main>

      <Footer />
    </div>
  );
}
