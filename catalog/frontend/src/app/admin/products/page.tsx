'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';
import adminService from '@/services/admin.service';
import toast from 'react-hot-toast';
import Link from 'next/link';

interface Product {
    id: string;
    title: string;
    description: string;
    seller_id: string;
    review_status: string;
    rejection_reason?: string | null;
    created_at: string;
    thumbnail_url?: string | null;
}

export default function AdminProductsPage() {
    const { user, loading: authLoading } = useAuth();
    const router = useRouter();
    const [products, setProducts] = useState<Product[]>([]);
    const [loading, setLoading] = useState(true);
    const [rejectingId, setRejectingId] = useState<string | null>(null);
    const [rejectReason, setRejectReason] = useState('');

    useEffect(() => {
        if (!authLoading) {
            if (!user || user.role !== 'admin') {
                router.push('/');
                return;
            }
            fetchProducts();
        }
    }, [user, authLoading, router]);

    const fetchProducts = async () => {
        try {
            setLoading(true);
            const result = await adminService.getProductsPendingReview();
            setProducts(result.products || []);
        } catch (error: any) {
            toast.error(error.response?.data?.message || 'Không thể tải danh sách sản phẩm');
        } finally {
            setLoading(false);
        }
    };

    const handleApprove = async (productId: string) => {
        if (!confirm('Bạn có chắc chắn muốn duyệt sản phẩm này?')) return;

        try {
            await adminService.approveProduct(productId);
            toast.success('Đã duyệt sản phẩm thành công');
            fetchProducts();
        } catch (error: any) {
            toast.error(error.response?.data?.message || 'Không thể duyệt sản phẩm');
        }
    };

    const handleReject = async (productId: string) => {
        if (!rejectReason.trim()) {
            toast.error('Vui lòng nhập lý do từ chối');
            return;
        }

        try {
            await adminService.rejectProduct(productId, rejectReason);
            toast.success('Đã từ chối sản phẩm');
            setRejectingId(null);
            setRejectReason('');
            fetchProducts();
        } catch (error: any) {
            toast.error(error.response?.data?.message || 'Không thể từ chối sản phẩm');
        }
    };

    if (authLoading || loading) {
        return (
            <div className="min-h-screen bg-white dark:bg-[#0B0C10] flex items-center justify-center">
                <div className="text-gray-600 dark:text-slate-400">Đang tải...</div>
            </div>
        );
    }

    if (!user || user.role !== 'admin') {
        return null;
    }

    return (
        <div className="min-h-screen bg-white dark:bg-[#0B0C10] py-8">
            <div className="container mx-auto px-4">
                <div className="mb-8">
                    <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
                        Duyệt Sản phẩm
                    </h1>
                    <p className="text-gray-600 dark:text-slate-400">
                        Xem và duyệt sản phẩm đang chờ phê duyệt
                    </p>
                </div>

                {products.length === 0 ? (
                    <div className="bg-white dark:bg-slate-800 rounded-lg shadow p-8 text-center border border-gray-200 dark:border-slate-700">
                        <p className="text-gray-600 dark:text-slate-400">Không có sản phẩm nào chờ duyệt</p>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {products.map((product) => (
                            <div
                                key={product.id}
                                className="bg-white dark:bg-slate-800 rounded-lg shadow border border-gray-200 dark:border-slate-700 overflow-hidden"
                            >
                                {product.thumbnail_url && (
                                    <img
                                        src={product.thumbnail_url}
                                        alt={product.title}
                                        className="w-full h-48 object-cover"
                                    />
                                )}
                                <div className="p-6">
                                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                                        {product.title || 'Chưa có tiêu đề'}
                                    </h3>
                                    <p className="text-sm text-gray-600 dark:text-slate-400 mb-4 line-clamp-3">
                                        {product.description || 'Chưa có mô tả'}
                                    </p>
                                    <p className="text-xs text-gray-500 dark:text-slate-500 mb-4">
                                        Ngày tạo: {new Date(product.created_at).toLocaleDateString('vi-VN')}
                                    </p>
                                    {product.rejection_reason && (
                                        <p className="text-sm text-red-600 dark:text-red-400 mb-4">
                                            Lý do từ chối trước: {product.rejection_reason}
                                        </p>
                                    )}
                                    <div className="flex gap-2">
                                        <Link
                                            href={`/product/${product.id}`}
                                            target="_blank"
                                            className="flex-1 px-4 py-2 bg-gray-200 dark:bg-slate-700 text-gray-700 dark:text-slate-300 rounded-lg hover:bg-gray-300 dark:hover:bg-slate-600 transition-colors text-center text-sm"
                                        >
                                            Xem chi tiết
                                        </Link>
                                        <button
                                            onClick={() => handleApprove(product.id)}
                                            className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm"
                                        >
                                            Duyệt
                                        </button>
                                        <button
                                            onClick={() => setRejectingId(rejectingId === product.id ? null : product.id)}
                                            className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors text-sm"
                                        >
                                            Từ chối
                                        </button>
                                    </div>

                                    {rejectingId === product.id && (
                                        <div className="mt-4 p-4 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-800">
                                            <label className="block text-sm font-medium text-gray-900 dark:text-white mb-2">
                                                Lý do từ chối:
                                            </label>
                                            <textarea
                                                value={rejectReason}
                                                onChange={(e) => setRejectReason(e.target.value)}
                                                className="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-gray-900 dark:text-white"
                                                rows={3}
                                                placeholder="Nhập lý do từ chối..."
                                            />
                                            <div className="flex gap-2 mt-2">
                                                <button
                                                    onClick={() => handleReject(product.id)}
                                                    className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors text-sm"
                                                >
                                                    Xác nhận từ chối
                                                </button>
                                                <button
                                                    onClick={() => {
                                                        setRejectingId(null);
                                                        setRejectReason('');
                                                    }}
                                                    className="flex-1 px-4 py-2 bg-gray-200 dark:bg-slate-700 text-gray-700 dark:text-slate-300 rounded-lg hover:bg-gray-300 dark:hover:bg-slate-600 transition-colors text-sm"
                                                >
                                                    Hủy
                                                </button>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}

