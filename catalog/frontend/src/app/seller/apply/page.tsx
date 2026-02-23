'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';
import sellerService from '@/services/seller.service';
import toast from 'react-hot-toast';
import Link from 'next/link';

export default function SellerApplyPage() {
    const { user, loading: authLoading } = useAuth();
    const router = useRouter();
    const [status, setStatus] = useState<{
        status: 'pending' | 'approved' | 'rejected' | null;
        application: any;
        rejection_reason?: string | null;
    } | null>(null);
    const [loading, setLoading] = useState(true);
    const [submitting, setSubmitting] = useState(false);

    useEffect(() => {
        if (!authLoading) {
            if (!user) {
                router.push('/login');
                return;
            }
            fetchStatus();
        }
    }, [user, authLoading, router]);

    const fetchStatus = async () => {
        try {
            setLoading(true);
            const data = await sellerService.getApplicationStatus();
            setStatus(data);
        } catch (error: any) {
            toast.error(error.response?.data?.message || 'Không thể tải trạng thái');
        } finally {
            setLoading(false);
        }
    };

    const handleApply = async () => {
        if (!confirm('Bạn có chắc chắn muốn đăng ký làm seller?')) return;

        try {
            setSubmitting(true);
            await sellerService.requestSellerStatus();
            toast.success('Đã gửi đơn đăng ký seller thành công. Vui lòng chờ admin duyệt.');
            fetchStatus();
        } catch (error: any) {
            toast.error(error.response?.data?.message || 'Không thể gửi đơn đăng ký');
        } finally {
            setSubmitting(false);
        }
    };

    if (authLoading || loading) {
        return (
            <div className="min-h-screen bg-white dark:bg-[#0B0C10] flex items-center justify-center">
                <div className="text-gray-600 dark:text-slate-400">Đang tải...</div>
            </div>
        );
    }

    if (!user) {
        return null;
    }

    const getStatusDisplay = () => {
        if (!status) return null;

        switch (status.status) {
            case 'approved':
                return (
                    <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-6 mb-6">
                        <div className="flex items-center gap-3 mb-2">
                            <svg className="w-6 h-6 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            <h3 className="text-lg font-semibold text-green-800 dark:text-green-400">
                                Bạn đã được duyệt làm seller!
                            </h3>
                        </div>
                        <p className="text-green-700 dark:text-green-300 mb-4">
                            Bạn có thể bắt đầu tạo và quản lý sản phẩm của mình.
                        </p>
                        <Link
                            href="/seller/upload"
                            className="inline-block px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                        >
                            Tạo sản phẩm đầu tiên
                        </Link>
                    </div>
                );

            case 'pending':
                return (
                    <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-6 mb-6">
                        <div className="flex items-center gap-3 mb-2">
                            <svg className="w-6 h-6 text-yellow-600 dark:text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            <h3 className="text-lg font-semibold text-yellow-800 dark:text-yellow-400">
                                Đơn đăng ký của bạn đang chờ duyệt
                            </h3>
                        </div>
                        <p className="text-yellow-700 dark:text-yellow-300">
                            Vui lòng chờ admin xem xét và duyệt đơn của bạn. Bạn sẽ nhận được thông báo khi có kết quả.
                        </p>
                    </div>
                );

            case 'rejected':
                return (
                    <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6 mb-6">
                        <div className="flex items-center gap-3 mb-2">
                            <svg className="w-6 h-6 text-red-600 dark:text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            <h3 className="text-lg font-semibold text-red-800 dark:text-red-400">
                                Đơn đăng ký của bạn đã bị từ chối
                            </h3>
                        </div>
                        {status.rejection_reason && (
                            <div className="mb-4">
                                <p className="text-sm font-medium text-red-700 dark:text-red-300 mb-1">Lý do:</p>
                                <p className="text-red-600 dark:text-red-400">{status.rejection_reason}</p>
                            </div>
                        )}
                        <p className="text-red-700 dark:text-red-300 mb-4">
                            Bạn có thể gửi lại đơn đăng ký sau khi đã khắc phục các vấn đề được nêu.
                        </p>
                        <button
                            onClick={handleApply}
                            disabled={submitting}
                            className="px-6 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50"
                        >
                            {submitting ? 'Đang gửi...' : 'Gửi lại đơn đăng ký'}
                        </button>
                    </div>
                );

            default:
                return null;
        }
    };

    return (
        <div className="min-h-screen bg-white dark:bg-[#0B0C10] py-8">
            <div className="container mx-auto px-4 max-w-3xl">
                <div className="mb-8">
                    <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
                        Đăng ký làm Seller
                    </h1>
                    <p className="text-gray-600 dark:text-slate-400">
                        Trở thành seller để bán sản phẩm và workflow của bạn trên marketplace
                    </p>
                </div>

                {getStatusDisplay()}

                {status?.status === null && (
                    <div className="bg-white dark:bg-slate-800 rounded-lg shadow p-8 border border-gray-200 dark:border-slate-700">
                        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                            Thông tin về Seller
                        </h2>
                        <div className="space-y-4 text-gray-700 dark:text-slate-300 mb-6">
                            <p>
                                Khi trở thành seller, bạn sẽ có thể:
                            </p>
                            <ul className="list-disc list-inside space-y-2 ml-4">
                                <li>Tạo và quản lý sản phẩm của mình</li>
                                <li>Upload workflow và template</li>
                                <li>Đặt giá cho sản phẩm (miễn phí hoặc có phí)</li>
                                <li>Nhận phản hồi từ người dùng</li>
                                <li>Theo dõi số lượt tải xuống</li>
                            </ul>
                            <p className="mt-4">
                                <strong>Lưu ý:</strong> Tất cả sản phẩm của bạn sẽ cần được admin duyệt trước khi được publish.
                            </p>
                        </div>
                        <button
                            onClick={handleApply}
                            disabled={submitting}
                            className="w-full px-6 py-3 bg-gray-900 dark:bg-white text-white dark:text-gray-900 rounded-lg hover:bg-gray-800 dark:hover:bg-slate-200 transition-colors font-semibold disabled:opacity-50"
                        >
                            {submitting ? 'Đang gửi đơn...' : 'Đăng ký làm Seller'}
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
}

