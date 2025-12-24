'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

interface MenuItem {
    href: string;
    label: string;
    icon: string;
}

interface MenuGroup {
    title?: string;
    items: MenuItem[];
}

const menuGroups: MenuGroup[] = [
    {
        // Trang chủ
        items: [
            { href: '/dashboard', label: 'Tổng quan', icon: '📊' },
        ],
    },
    // Các tính năng persona bot/LLM - Ẩn tạm thời, tập trung vào marketplace mini
    // {
    //     // Nội dung
    //     title: 'Nội dung',
    //     items: [
    //         { href: '/dashboard/articles', label: 'Bài báo', icon: '📰' },
    //         { href: '/dashboard/summaries', label: 'Tóm tắt', icon: '📝' },
    //     ],
    // },
    // {
    //     // Tự động hóa
    //     title: 'Tự động hóa',
    //     items: [
    //         { href: '/dashboard/schedules', label: 'Lịch trình', icon: '⏰' },
    //     ],
    // },
    // {
    //     // Tương tác
    //     title: 'Tương tác',
    //     items: [
    //         { href: '/dashboard/chat', label: 'Trò chuyện', icon: '💬' },
    //     ],
    // },
    // {
    //     // Hệ thống
    //     title: 'Hệ thống',
    //     items: [
    //         { href: '/dashboard/tools', label: 'Công cụ', icon: '🛠️' },
    //     ],
    // },
    {
        // Hệ thống
        title: 'Hệ thống',
        items: [
            { href: '/dashboard/settings', label: 'Cài đặt', icon: '⚙️' },
        ],
    },
];

export default function Sidebar({ isOpen, setIsOpen }: { isOpen: boolean; setIsOpen: (v: boolean) => void }) {
    const pathname = usePathname();

    return (
        <>
            {/* Mobile Overlay */}
            {isOpen && (
                <div
                    className="fixed inset-0 bg-black/50 z-20 lg:hidden"
                    onClick={() => setIsOpen(false)}
                />
            )}

            {/* Sidebar Container */}
            <aside
                className={`fixed top-0 left-0 z-30 h-screen w-64 bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800 transition-transform duration-300 ease-in-out transform lg:translate-x-0 ${isOpen ? 'translate-x-0' : '-translate-x-full'
                    }`}
            >
                {/* Logo Area */}
                <div className="h-16 flex items-center justify-between px-6 border-b border-gray-200 dark:border-gray-800">
                    <Link href="/" className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-indigo-600">
                        Marketplace
                    </Link>
                    <button onClick={() => setIsOpen(false)} className="lg:hidden text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200">
                        ✕
                    </button>
                </div>

                {/* Navigation Links */}
                <nav className="p-4 space-y-4 overflow-y-auto h-[calc(100vh-4rem)]">
                    {menuGroups.map((group, groupIndex) => (
                        <div key={groupIndex} className="space-y-1">
                            {group.title && (
                                <div className="px-4 py-2 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                                    {group.title}
                                </div>
                            )}
                            {group.items.map((item) => {
                                const isActive = pathname === item.href;
                                return (
                                    <Link
                                        key={item.href}
                                        href={item.href}
                                        onClick={() => setIsOpen(false)} // Close on mobile click
                                        className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${isActive
                                            ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 font-medium'
                                            : 'text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800 hover:text-gray-900 dark:hover:text-gray-200'
                                            }`}
                                    >
                                        <span className="text-xl">{item.icon}</span>
                                        <span>{item.label}</span>
                                    </Link>
                                );
                            })}
                        </div>
                    ))}
                </nav>

                {/* User Profile / Footer (Optional) */}
                <div className="absolute bottom-0 w-full p-4 border-t border-gray-200 dark:border-gray-800">
                    {/* Placeholder for mini user profile or logout */}
                </div>
            </aside>
        </>
    );
}
