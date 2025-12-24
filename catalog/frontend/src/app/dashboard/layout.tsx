'use client';

import { useState } from 'react';
import Sidebar from '@/components/Sidebar';
import Header from '@/components/Header';
import { useAuth } from '@/lib/auth-context';
import Link from 'next/link';

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
    const [sidebarOpen, setSidebarOpen] = useState(false);
    const { user, loading } = useAuth();

    if (loading) {
        return <div className="flex h-screen items-center justify-center">Đang tải...</div>;
    }

    // Lần đầu (hoặc khi chưa đăng nhập), cho phép xem thông tin giới thiệu thay vì auto redirect login
    if (!user) {
        return (
            <main className="flex min-h-screen items-center justify-center bg-gray-50 dark:bg-gray-950 px-4">
                <div className="max-w-md w-full bg-white dark:bg-gray-900 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-800 p-8 text-center space-y-4">
                    <h1 className="text-xl font-semibold text-gray-900 dark:text-white">
                        Khu vực Dashboard yêu cầu đăng nhập
                    </h1>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                        Bạn vẫn có thể duyệt catalog workflow/tool ở trang chủ mà không cần tài khoản.
                        Khi sẵn sàng sử dụng các tính năng cá nhân hóa, hãy đăng nhập hoặc đăng ký.
                    </p>
                    <div className="flex flex-col sm:flex-row gap-3 justify-center mt-4">
                        <Link
                            href="/login"
                            className="inline-flex items-center justify-center px-4 py-2 rounded-lg text-sm font-medium bg-blue-600 text-white hover:bg-blue-700 transition-colors"
                        >
                            Đăng nhập
                        </Link>
                        <Link
                            href="/register"
                            className="inline-flex items-center justify-center px-4 py-2 rounded-lg text-sm font-medium border border-gray-300 dark:border-gray-700 text-gray-800 dark:text-gray-100 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                        >
                            Đăng ký
                        </Link>
                        <Link
                            href="/"
                            className="inline-flex items-center justify-center px-4 py-2 rounded-lg text-sm font-medium text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white transition-colors"
                        >
                            Quay lại trang chủ
                        </Link>
                    </div>
                </div>
            </main>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-950 flex">
            <Sidebar isOpen={sidebarOpen} setIsOpen={setSidebarOpen} />

            <div className="flex-1 flex flex-col lg:ml-64 min-w-0">
                <Header onMenuClick={() => setSidebarOpen(true)} />

                <main className="flex-1 p-4 lg:p-8 overflow-y-auto">
                    {children}
                </main>
            </div>
        </div>
    );
}
