'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';
import Navbar from '@/components/marketplace/Navbar';
import Footer from '@/components/marketplace/Footer';
import productService, { Product } from '@/services/product.service';
import { Plus, Edit, Trash2, Eye, EyeOff, ExternalLink, Download, Search, Filter, ShieldX, ShieldCheck } from 'lucide-react';
import Link from 'next/link';
import toast from 'react-hot-toast';

export default function SellerDashboard() {
  const router = useRouter();
  const { user } = useAuth();
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'draft' | 'published' | 'archived'>('all');

  // Redirect if not logged in or not approved seller
  useEffect(() => {
    if (!user) {
      router.push('/login?returnTo=/seller/dashboard');
      return;
    }
    // Check if user is approved seller
    if (user.role !== 'seller' && user.seller_status !== 'approved') {
      if (user.seller_status === 'pending') {
        toast.error('Đơn đăng ký seller của bạn đang chờ duyệt. Vui lòng đợi admin phê duyệt.');
        router.push('/seller/apply');
      } else if (user.seller_status === 'rejected') {
        toast.error('Đơn đăng ký seller của bạn đã bị từ chối. Vui lòng kiểm tra và gửi lại đơn.');
        router.push('/seller/apply');
      } else {
        toast.error('Bạn cần đăng ký làm seller trước.');
        router.push('/seller/apply');
      }
    }
  }, [user, router]);

  useEffect(() => {
    if (user) {
      fetchProducts();
    }
  }, [user, statusFilter]);

  const fetchProducts = async () => {
    try {
      setLoading(true);
      const data = await productService.getMyProducts(true);
      setProducts(data);
    } catch (error: any) {
      toast.error('Không thể tải danh sách sản phẩm');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string, title: string) => {
    if (!confirm(`Bạn có chắc muốn xóa "${title}"?`)) {
      return;
    }

    try {
      await productService.deleteProduct(id);
      toast.success('Xóa sản phẩm thành công');
      fetchProducts();
    } catch (error: any) {
      const message = error.response?.data?.message || error.message || 'Xóa sản phẩm thất bại';
      toast.error(message);
    }
  };

  const handlePublish = async (id: string) => {
    try {
      await productService.publishProduct(id);
      toast.success('Đã publish sản phẩm, chờ admin phê duyệt');
      fetchProducts();
    } catch (error: any) {
      const message = error.response?.data?.message || error.message || 'Publish thất bại';
      toast.error(message);
    }
  };

  const handleUnpublish = async (id: string) => {
    try {
      await productService.unpublishProduct(id);
      toast.success('Đã unpublish sản phẩm');
      fetchProducts();
    } catch (error: any) {
      const message = error.response?.data?.message || error.message || 'Unpublish thất bại';
      toast.error(message);
    }
  };

  const getStatusBadge = (status: string, reviewStatus?: string) => {
    const styles = {
      draft: 'bg-slate-700 text-slate-300',
      published: 'bg-green-500/20 text-green-400 border border-green-500/30',
      archived: 'bg-slate-800 text-slate-400',
    };
    const labels = {
      draft: 'Draft',
      published: 'Published',
      archived: 'Archived',
    };
    return (
      <div className="flex items-center gap-2">
        <span className={`px-2 py-1 rounded text-xs font-medium ${styles[status as keyof typeof styles]}`}>
          {labels[status as keyof typeof labels]}
        </span>
        {reviewStatus === 'pending' && (
          <span className="inline-flex items-center gap-1 px-2 py-1 rounded text-[11px] font-medium bg-amber-500/15 text-amber-400 border border-amber-500/30">
            <ShieldCheck className="h-3 w-3" />
            Chờ duyệt
          </span>
        )}
        {reviewStatus === 'rejected' && (
          <span className="inline-flex items-center gap-1 px-2 py-1 rounded text-[11px] font-medium bg-red-500/15 text-red-400 border border-red-500/30">
            <ShieldX className="h-3 w-3" />
            Bị từ chối
          </span>
        )}
      </div>
    );
  };

  const filteredProducts = products.filter((product) => {
    const matchesSearch = 
      product.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      product.description.toLowerCase().includes(searchQuery.toLowerCase());
    
    const matchesStatus = statusFilter === 'all' || product.status === statusFilter;
    
    return matchesSearch && matchesStatus;
  });

  const stats = {
    total: products.length,
    published: products.filter(p => p.status === 'published').length,
    draft: products.filter(p => p.status === 'draft').length,
    pending: products.filter(p => p.reviewStatus === 'pending').length,
    rejected: products.filter(p => p.reviewStatus === 'rejected').length,
    downloads: products.reduce((sum, p) => sum + p.downloads, 0),
  };

  if (!user) {
    return null;
  }

  return (
    <div className="min-h-screen bg-white dark:bg-[#0B0C10] text-gray-900 dark:text-slate-200 font-sans">
      <Navbar />

      <main className="container mx-auto px-4 py-12">
        <div className="max-w-7xl mx-auto">
          <header className="mb-8">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">Seller Dashboard</h1>
                <p className="text-gray-600 dark:text-slate-400">Quản lý sản phẩm của bạn</p>
              </div>
              <Link
                href="/seller/upload"
                className="inline-flex items-center gap-2 px-6 py-3 bg-primary hover:bg-[#FF8559] text-white font-semibold rounded-lg transition-colors"
              >
                <Plus className="h-4 w-4" />
                Tải lên sản phẩm mới
              </Link>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
              <div className="bg-gray-50 dark:bg-[#111218] border border-gray-200 dark:border-slate-800 rounded-lg p-4">
                <p className="text-sm text-gray-600 dark:text-slate-400 mb-1">Tổng sản phẩm</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{stats.total}</p>
              </div>
              <div className="bg-gray-50 dark:bg-[#111218] border border-gray-200 dark:border-slate-800 rounded-lg p-4">
                <p className="text-sm text-gray-600 dark:text-slate-400 mb-1">Đã publish</p>
                <p className="text-2xl font-bold text-green-600 dark:text-green-400">{stats.published}</p>
              </div>
              <div className="bg-gray-50 dark:bg-[#111218] border border-gray-200 dark:border-slate-800 rounded-lg p-4">
                <p className="text-sm text-gray-600 dark:text-slate-400 mb-1">Draft</p>
                <p className="text-2xl font-bold text-gray-600 dark:text-slate-400">{stats.draft}</p>
              </div>
              <div className="bg-gray-50 dark:bg-[#111218] border border-gray-200 dark:border-slate-800 rounded-lg p-4">
                <p className="text-sm text-gray-600 dark:text-slate-400 mb-1">Chờ duyệt</p>
                <p className="text-2xl font-bold text-amber-500">{stats.pending}</p>
              </div>
              <div className="bg-gray-50 dark:bg-[#111218] border border-gray-200 dark:border-slate-800 rounded-lg p-4">
                <p className="text-sm text-gray-600 dark:text-slate-400 mb-1">Bị từ chối</p>
                <p className="text-2xl font-bold text-red-500">{stats.rejected}</p>
              </div>
              <div className="bg-gray-50 dark:bg-[#111218] border border-gray-200 dark:border-slate-800 rounded-lg p-4">
                <p className="text-sm text-gray-600 dark:text-slate-400 mb-1">Tổng lượt tải</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{stats.downloads}</p>
              </div>
            </div>

            {/* Filters */}
            <div className="flex flex-col md:flex-row gap-4 mb-6">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400 dark:text-slate-500" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Tìm kiếm sản phẩm..."
                  className="w-full pl-10 pr-4 py-2 bg-gray-100 dark:bg-slate-900/50 border border-gray-200 dark:border-slate-800 rounded-lg text-gray-900 dark:text-white placeholder:text-gray-400 dark:placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all"
                />
              </div>
              <div className="flex gap-2">
                {(['all', 'draft', 'published', 'archived'] as const).map((status) => (
                  <button
                    key={status}
                    onClick={() => setStatusFilter(status)}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                      statusFilter === status
                        ? 'bg-primary text-white'
                        : 'bg-slate-900/50 border border-slate-800 text-slate-300 hover:bg-slate-800/50'
                    }`}
                  >
                    {status === 'all' ? 'Tất cả' : status.charAt(0).toUpperCase() + status.slice(1)}
                  </button>
                ))}
              </div>
            </div>
          </header>

          {/* Products List */}
          {loading ? (
            <div className="text-center py-12">
              <div className="h-8 w-8 border-2 border-primary/30 border-t-primary rounded-full animate-spin mx-auto mb-4"></div>
              <p className="text-gray-600 dark:text-slate-400">Đang tải...</p>
            </div>
          ) : filteredProducts.length === 0 ? (
            <div className="text-center py-12 bg-gray-50 dark:bg-[#111218] border border-gray-200 dark:border-slate-800 rounded-2xl">
              <p className="text-gray-600 dark:text-slate-400 mb-4">Chưa có sản phẩm nào</p>
              <Link
                href="/seller/upload"
                className="inline-flex items-center gap-2 px-6 py-3 bg-primary hover:bg-[#FF8559] text-white font-semibold rounded-lg transition-colors"
              >
                <Plus className="h-4 w-4" />
                Tạo sản phẩm đầu tiên
              </Link>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4">
              {filteredProducts.map((product) => (
                <div
                  key={product.id}
                  className="bg-white dark:bg-[#111218] border border-gray-200 dark:border-slate-800 rounded-lg p-6 hover:border-gray-300 dark:hover:border-slate-700 transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2 flex-wrap">
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{product.title}</h3>
                        {getStatusBadge(product.status, (product as any).reviewStatus || (product as any).review_status)}
                        {product.isFree ? (
                          <span className="px-2 py-1 bg-green-500/20 text-green-600 dark:text-green-400 rounded text-xs font-medium">
                            Miễn phí
                          </span>
                        ) : (
                          <span className="px-2 py-1 bg-primary/20 text-primary rounded text-xs font-medium">
                            {product.price?.toLocaleString('vi-VN')} VNĐ
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-gray-600 dark:text-slate-400 mb-3 line-clamp-2">{product.description}</p>
                      <div className="flex items-center gap-4 text-xs text-gray-500 dark:text-slate-500 flex-wrap">
                        <span>Type: {product.type}</span>
                        <span>•</span>
                        <span>{product.downloads} lượt tải</span>
                        <span>•</span>
                        <span>⭐ {product.rating.toFixed(1)}</span>
                        {product.version && (
                          <>
                            <span>•</span>
                            <span>v{product.version}</span>
                          </>
                        )}
                        {((product as any).reviewStatus || (product as any).review_status) === 'pending' && (
                          <>
                            <span>•</span>
                            <span className="text-amber-400">Đang chờ admin duyệt</span>
                          </>
                        )}
                        {((product as any).reviewStatus || (product as any).review_status) === 'rejected' && (
                          <>
                            <span>•</span>
                            <span className="text-red-400">
                              Bị từ chối{(product as any).rejectionReason ? `: ${(product as any).rejectionReason}` : ''}
                            </span>
                          </>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-2 ml-4">
                      {product.status === 'published' && (
                        <Link
                          href={`/product/${product.id}`}
                          target="_blank"
                          className="p-2 text-gray-500 dark:text-slate-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
                          title="Xem trên site"
                        >
                          <ExternalLink className="h-4 w-4" />
                        </Link>
                      )}
                      <Link
                        href={`/seller/edit/${product.id}`}
                        className="p-2 text-gray-500 dark:text-slate-400 hover:text-primary hover:bg-gray-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
                        title="Chỉnh sửa"
                      >
                        <Edit className="h-4 w-4" />
                      </Link>
                      {product.status === 'draft' ? (
                        <button
                          onClick={() => handlePublish(product.id)}
                          className="p-2 text-gray-500 dark:text-slate-400 hover:text-green-600 dark:hover:text-green-400 hover:bg-gray-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
                          title="Publish"
                        >
                          <Eye className="h-4 w-4" />
                        </button>
                      ) : product.status === 'published' ? (
                        <button
                          onClick={() => handleUnpublish(product.id)}
                          className="p-2 text-gray-500 dark:text-slate-400 hover:text-yellow-600 dark:hover:text-yellow-400 hover:bg-gray-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
                          title="Unpublish"
                        >
                          <EyeOff className="h-4 w-4" />
                        </button>
                      ) : null}
                      <button
                        onClick={() => handleDelete(product.id, product.title)}
                        className="p-2 text-gray-500 dark:text-slate-400 hover:text-red-600 dark:hover:text-red-400 hover:bg-gray-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
                        title="Xóa"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>

      <Footer />
    </div>
  );
}

