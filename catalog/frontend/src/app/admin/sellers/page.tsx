'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';
import adminService, { SellerApplication } from '@/services/admin.service';
import toast from 'react-hot-toast';

export default function AdminSellersPage() {
    const { user, loading: authLoading } = useAuth();
    const router = useRouter();
    const [applications, setApplications] = useState<SellerApplication[]>([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState<'all' | 'pending' | 'approved' | 'rejected'>('all');
    const [rejectingId, setRejectingId] = useState<string | null>(null);
    const [rejectReason, setRejectReason] = useState('');

    useEffect(() => {
        if (!authLoading) {
            if (!user || user.role !== 'admin') {
                router.push('/');
                return;
            }
            fetchApplications();
        }
    }, [user, authLoading, router, filter]);

    const fetchApplications = async () => {
        try {
            setLoading(true);
            const status = filter === 'all' ? undefined : filter;
            const data = await adminService.getSellerApplications(status);
            setApplications(data);
        } catch (error: any) {
            toast.error(error.response?.data?.message || 'Không thể tải danh sách đơn');
        } finally {
            setLoading(false);
        }
    };

    const handleApprove = async (userId: string) => {
        if (!confirm('Bạn có chắc chắn muốn duyệt đơn này?')) return;

        try {
            await adminService.approveSeller(userId);
            toast.success('Đã duyệt seller thành công');
            fetchApplications();
        } catch (error: any) {
            toast.error(error.response?.data?.message || 'Không thể duyệt seller');
        }
    };

    const handleReject = async (userId: string) => {
        if (!rejectReason.trim()) {
            toast.error('Vui lòng nhập lý do từ chối');
            return;
        }

        try {
            await adminService.rejectSeller(userId, rejectReason);
            toast.success('Đã từ chối đơn');
            setRejectingId(null);
            setRejectReason('');
            fetchApplications();
        } catch (error: any) {
            toast.error(error.response?.data?.message || 'Không thể từ chối đơn');
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

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'approved':
                return 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-400';
            case 'rejected':
                return 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-400';
            case 'pending':
                return 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-400';
            default:
                return 'bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-400';
        }
    };

    const getStatusText = (status: string) => {
        switch (status) {
            case 'approved':
                return 'Đã duyệt';
            case 'rejected':
                return 'Đã từ chối';
            case 'pending':
                return 'Chờ duyệt';
            default:
                return status;
        }
    };

    return (
        <div className="min-h-screen bg-white dark:bg-[#0B0C10] py-8">
            <div className="container mx-auto px-4">
                <div className="mb-8">
                    <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
                        Quản lý Sellers
                    </h1>
                    <p className="text-gray-600 dark:text-slate-400">
                        Duyệt và quản lý đơn xin làm seller
                    </p>
                </div>

                {/* Filter */}
                <div className="mb-6 flex gap-2">
                    {(['all', 'pending', 'approved', 'rejected'] as const).map((f) => (
                        <button
                            key={f}
                            onClick={() => setFilter(f)}
                            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                                filter === f
                                    ? 'bg-gray-900 dark:bg-white text-white dark:text-gray-900'
                                    : 'bg-white dark:bg-slate-800 text-gray-700 dark:text-slate-300 border border-gray-200 dark:border-slate-700 hover:bg-gray-50 dark:hover:bg-slate-700'
                            }`}
                        >
                            {f === 'all' ? 'Tất cả' : f === 'pending' ? 'Chờ duyệt' : f === 'approved' ? 'Đã duyệt' : 'Đã từ chối'}
                        </button>
                    ))}
                </div>

                {/* Applications List */}
                {applications.length === 0 ? (
                    <div className="bg-white dark:bg-slate-800 rounded-lg shadow p-8 text-center border border-gray-200 dark:border-slate-700">
                        <p className="text-gray-600 dark:text-slate-400">Không có đơn nào</p>
                    </div>
                ) : (
                    <div className="space-y-4">
                        {applications.map((app) => (
                            <div
                                key={app.id}
                                className="bg-white dark:bg-slate-800 rounded-lg shadow p-6 border border-gray-200 dark:border-slate-700"
                            >
                                <div className="flex items-start justify-between">
                                    <div className="flex-1">
                                        <div className="flex items-center gap-3 mb-2">
                                            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                                                {app.user?.email || 'N/A'}
                                            </h3>
                                            <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(app.status)}`}>
                                                {getStatusText(app.status)}
                                            </span>
                                        </div>
                                        <p className="text-sm text-gray-600 dark:text-slate-400 mb-2">
                                            Ngày đăng ký: {new Date(app.created_at).toLocaleDateString('vi-VN')}
                                        </p>
                                        {app.rejection_reason && (
                                            <p className="text-sm text-red-600 dark:text-red-400 mt-2">
                                                Lý do từ chối: {app.rejection_reason}
                                            </p>
                                        )}
                                        {app.reviewed_at && (
                                            <p className="text-sm text-gray-600 dark:text-slate-400">
                                                Đã duyệt: {new Date(app.reviewed_at).toLocaleDateString('vi-VN')}
                                            </p>
                                        )}
                                    </div>
                                    <div className="flex gap-2">
                                        {app.status === 'pending' && (
                                            <>
                                                <button
                                                    onClick={() => handleApprove(app.user_id)}
                                                    className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                                                >
                                                    Duyệt
                                                </button>
                                                <button
                                                    onClick={() => setRejectingId(rejectingId === app.user_id ? null : app.user_id)}
                                                    className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
                                                >
                                                    Từ chối
                                                </button>
                                            </>
                                        )}
                                    </div>
                                </div>

                                {rejectingId === app.user_id && (
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
                                                onClick={() => handleReject(app.user_id)}
                                                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
                                            >
                                                Xác nhận từ chối
                                            </button>
                                            <button
                                                onClick={() => {
                                                    setRejectingId(null);
                                                    setRejectReason('');
                                                }}
                                                className="px-4 py-2 bg-gray-200 dark:bg-slate-700 text-gray-700 dark:text-slate-300 rounded-lg hover:bg-gray-300 dark:hover:bg-slate-600 transition-colors"
                                            >
                                                Hủy
                                            </button>
                                        </div>
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}

