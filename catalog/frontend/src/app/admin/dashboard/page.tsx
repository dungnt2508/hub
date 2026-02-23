'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';
import adminService, { DashboardStats } from '@/services/admin.service';
import toast from 'react-hot-toast';
import Link from 'next/link';
import Navbar from '@/components/marketplace/Navbar';
import Footer from '@/components/marketplace/Footer';

export default function AdminDashboard() {
    const { user, loading: authLoading } = useAuth();
    const router = useRouter();
    const [stats, setStats] = useState<DashboardStats | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!authLoading) {
            if (!user) {
                router.push('/login');
                return;
            }
            if (user.role !== 'admin') {
                router.push('/');
                toast.error('Bạn không có quyền truy cập trang này. Bạn cần có role admin.');
                return;
            }
            fetchStats();
        }
    }, [user, authLoading, router]);

    const fetchStats = async () => {
        try {
            setLoading(true);
            const data = await adminService.getDashboardStats();
            setStats(data);
        } catch (error: any) {
            console.error('Error fetching dashboard stats:', error);
            const errorMessage = error.response?.data?.message || error.message || 'Không thể tải thống kê';
            toast.error(errorMessage);
            // Set default stats to prevent crash
            setStats({
                users: {
                    total: 0,
                    sellers: 0,
                    pending_seller_applications: 0,
                },
                products: {
                    total: 0,
                    pending_review: 0,
                    published: 0,
                },
            });
        } finally {
            setLoading(false);
        }
    };

    if (authLoading || loading) {
        return (
            <>
                <Navbar />
                <div className="min-h-screen bg-white dark:bg-[#0B0C10] flex items-center justify-center">
                    <div className="text-gray-600 dark:text-slate-400">Đang tải...</div>
                </div>
                <Footer />
            </>
        );
    }

    if (!user || user.role !== 'admin') {
        return (
            <>
                <Navbar />
                <div className="min-h-screen bg-white dark:bg-[#0B0C10] flex items-center justify-center">
                    <div className="text-gray-600 dark:text-slate-400">Bạn không có quyền truy cập trang này</div>
                </div>
                <Footer />
            </>
        );
    }

    return (
        <>
            <Navbar />
            <div className="min-h-screen bg-white dark:bg-[#0B0C10] py-8">
                <div className="container mx-auto px-4">
                    <div className="mb-8">
                        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
                            Admin Dashboard
                        </h1>
                        <p className="text-gray-600 dark:text-slate-400">
                            Quản lý người dùng, sellers và sản phẩm
                        </p>
                    </div>

                {stats && (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                        {/* Total Users */}
                        <div className="bg-white dark:bg-slate-800 rounded-lg shadow p-6 border border-gray-200 dark:border-slate-700">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm text-gray-600 dark:text-slate-400">Tổng người dùng</p>
                                    <p className="text-2xl font-bold text-gray-900 dark:text-white mt-2">
                                        {stats.users.total}
                                    </p>
                                </div>
                                <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900/30 rounded-full flex items-center justify-center">
                                    <svg className="w-6 h-6 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                                    </svg>
                                </div>
                            </div>
                        </div>

                        {/* Total Sellers */}
                        <div className="bg-white dark:bg-slate-800 rounded-lg shadow p-6 border border-gray-200 dark:border-slate-700">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm text-gray-600 dark:text-slate-400">Sellers đã duyệt</p>
                                    <p className="text-2xl font-bold text-gray-900 dark:text-white mt-2">
                                        {stats.users.sellers}
                                    </p>
                                </div>
                                <div className="w-12 h-12 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center">
                                    <svg className="w-6 h-6 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                    </svg>
                                </div>
                            </div>
                        </div>

                        {/* Pending Seller Applications */}
                        <div className="bg-white dark:bg-slate-800 rounded-lg shadow p-6 border border-gray-200 dark:border-slate-700">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm text-gray-600 dark:text-slate-400">Đơn seller chờ duyệt</p>
                                    <p className="text-2xl font-bold text-gray-900 dark:text-white mt-2">
                                        {stats.users.pending_seller_applications}
                                    </p>
                                </div>
                                <div className="w-12 h-12 bg-yellow-100 dark:bg-yellow-900/30 rounded-full flex items-center justify-center">
                                    <svg className="w-6 h-6 text-yellow-600 dark:text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                                    </svg>
                                </div>
                            </div>
                        </div>

                        {/* Pending Products */}
                        <div className="bg-white dark:bg-slate-800 rounded-lg shadow p-6 border border-gray-200 dark:border-slate-700">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm text-gray-600 dark:text-slate-400">Sản phẩm chờ duyệt</p>
                                    <p className="text-2xl font-bold text-gray-900 dark:text-white mt-2">
                                        {stats.products.pending_review}
                                    </p>
                                </div>
                                <div className="w-12 h-12 bg-purple-100 dark:bg-purple-900/30 rounded-full flex items-center justify-center">
                                    <svg className="w-6 h-6 text-purple-600 dark:text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                                    </svg>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {/* Quick Actions */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <Link
                        href="/admin/sellers"
                        className="bg-white dark:bg-slate-800 rounded-lg shadow p-6 border border-gray-200 dark:border-slate-700 hover:shadow-lg transition-shadow"
                    >
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                            Quản lý Sellers
                        </h3>
                        <p className="text-sm text-gray-600 dark:text-slate-400">
                            Xem và duyệt đơn xin làm seller
                        </p>
                    </Link>

                    <Link
                        href="/admin/products"
                        className="bg-white dark:bg-slate-800 rounded-lg shadow p-6 border border-gray-200 dark:border-slate-700 hover:shadow-lg transition-shadow"
                    >
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                            Duyệt Sản phẩm
                        </h3>
                        <p className="text-sm text-gray-600 dark:text-slate-400">
                            Xem và duyệt sản phẩm đang chờ
                        </p>
                    </Link>

                    <Link
                        href="/admin/users"
                        className="bg-white dark:bg-slate-800 rounded-lg shadow p-6 border border-gray-200 dark:border-slate-700 hover:shadow-lg transition-shadow"
                    >
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                            Quản lý Người dùng
                        </h3>
                        <p className="text-sm text-gray-600 dark:text-slate-400">
                            Xem danh sách tất cả người dùng
                        </p>
                    </Link>
                </div>
                </div>
            </div>
            <Footer />
        </>
    );
}

