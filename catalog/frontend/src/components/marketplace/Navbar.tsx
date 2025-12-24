'use client';

import Link from 'next/link';
import { Search, Menu, X, User, Sun, Moon, Monitor } from 'lucide-react';
import { useState } from 'react';
import { useAuth } from '@/lib/auth-context';
import { useTheme } from '@/lib/theme-context';

export default function Navbar() {
    const [isMenuOpen, setIsMenuOpen] = useState(false);
    const [isThemeMenuOpen, setIsThemeMenuOpen] = useState(false);
    const { user, logout } = useAuth();
    const { theme, resolvedTheme, setTheme } = useTheme();

    return (
        <nav className="sticky top-0 z-50 w-full border-b border-gray-200 dark:border-white/5 bg-white/80 dark:bg-[#0B0C10]/80 backdrop-blur-md">
            <div className="container mx-auto px-4 md:px-6">
                <div className="flex h-16 items-center justify-between">
                    <div className="flex items-center gap-8">
                        <Link href="/" className="flex items-center gap-2 group">
                            <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-orange-500 to-pink-600 flex items-center justify-center group-hover:shadow-lg group-hover:shadow-orange-500/20 transition-all">
                                <span className="font-bold text-white">n8n</span>
                            </div>
                            <span className="text-xl font-bold text-gray-900 dark:text-white tracking-tight">Market</span>
                        </Link>
                        <div className="hidden md:flex items-center gap-6 text-sm font-medium text-gray-600 dark:text-slate-400">
                            <Link href="/products" className="hover:text-gray-900 dark:hover:text-white transition-colors">Sản phẩm</Link>
                            {/* <Link href="/products/workflow" className="hover:text-white transition-colors">Workflow</Link>
                            <Link href="/products/tools" className="hover:text-white transition-colors">Tool</Link> */}
                            <Link href="/about" className="hover:text-gray-900 dark:hover:text-white transition-colors">Giới thiệu</Link>
                            <Link href="/contact" className="hover:text-gray-900 dark:hover:text-white transition-colors">Liên hệ</Link>
                        </div>
                    </div>

                    <div className="hidden md:flex items-center gap-4">
                        <div className="relative group">
                            <Search className="absolute left-3 top-2.5 h-4 w-4 text-gray-400 dark:text-slate-500 group-focus-within:text-primary transition-colors" />
                            <input
                                type="search"
                                placeholder="Search workflows..."
                                className="h-10 w-64 rounded-full bg-gray-100 dark:bg-slate-900/50 border border-gray-200 dark:border-slate-800 pl-10 pr-4 text-sm text-gray-900 dark:text-slate-200 placeholder:text-gray-400 dark:placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-transparent transition-all"
                            />
                        </div>
                        <div className="h-6 w-px bg-gray-200 dark:bg-slate-800 mx-2"></div>
                        
                        {/* Theme Toggle */}
                        <div className="relative">
                            <button
                                onClick={() => setIsThemeMenuOpen(!isThemeMenuOpen)}
                                className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-slate-800 transition-colors"
                                aria-label="Toggle theme"
                            >
                                {resolvedTheme === 'dark' ? (
                                    <Moon className="h-5 w-5 text-gray-700 dark:text-slate-300" />
                                ) : (
                                    <Sun className="h-5 w-5 text-gray-700 dark:text-slate-300" />
                                )}
                            </button>
                            
                            {isThemeMenuOpen && (
                                <>
                                    <div 
                                        className="fixed inset-0 z-10" 
                                        onClick={() => setIsThemeMenuOpen(false)}
                                    />
                                    <div className="absolute right-0 mt-2 w-40 bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-lg shadow-lg z-20 overflow-hidden">
                                        <button
                                            onClick={() => { setTheme('light'); setIsThemeMenuOpen(false); }}
                                            className={`w-full px-4 py-2 text-left text-sm flex items-center gap-2 hover:bg-gray-100 dark:hover:bg-slate-800 transition-colors ${
                                                theme === 'light' ? 'bg-gray-100 dark:bg-slate-800 text-primary' : 'text-gray-700 dark:text-slate-300'
                                            }`}
                                        >
                                            <Sun className="h-4 w-4" />
                                            Sáng
                                        </button>
                                        <button
                                            onClick={() => { setTheme('dark'); setIsThemeMenuOpen(false); }}
                                            className={`w-full px-4 py-2 text-left text-sm flex items-center gap-2 hover:bg-gray-100 dark:hover:bg-slate-800 transition-colors ${
                                                theme === 'dark' ? 'bg-gray-100 dark:bg-slate-800 text-primary' : 'text-gray-700 dark:text-slate-300'
                                            }`}
                                        >
                                            <Moon className="h-4 w-4" />
                                            Tối
                                        </button>
                                        <button
                                            onClick={() => { setTheme('system'); setIsThemeMenuOpen(false); }}
                                            className={`w-full px-4 py-2 text-left text-sm flex items-center gap-2 hover:bg-gray-100 dark:hover:bg-slate-800 transition-colors ${
                                                theme === 'system' ? 'bg-gray-100 dark:bg-slate-800 text-primary' : 'text-gray-700 dark:text-slate-300'
                                            }`}
                                        >
                                            <Monitor className="h-4 w-4" />
                                            Hệ thống
                                        </button>
                                    </div>
                                </>
                            )}
                        </div>
                        
                        <div className="h-6 w-px bg-gray-200 dark:bg-slate-800 mx-2"></div>
                        {user ? (
                            <>
                                {user.role === 'admin' && (
                                    <>
                                        <Link
                                            href="/admin/dashboard"
                                            className="text-sm font-medium text-gray-700 dark:text-slate-300 hover:text-gray-900 dark:hover:text-white transition-colors"
                                        >
                                            Admin
                                        </Link>
                                        <div className="h-6 w-px bg-gray-200 dark:bg-slate-800 mx-2"></div>
                                    </>
                                )}
                                {(user.role === 'seller' || user.seller_status === 'approved') && (
                                    <>
                                        <Link
                                            href="/seller/dashboard"
                                            className="text-sm font-medium text-gray-700 dark:text-slate-300 hover:text-gray-900 dark:hover:text-white transition-colors"
                                        >
                                            Seller Dashboard
                                        </Link>
                                        <Link
                                            href="/seller/upload"
                                            className="text-sm font-medium text-primary hover:text-[#FF8559] transition-colors"
                                        >
                                            Bán hàng
                                        </Link>
                                        <div className="h-6 w-px bg-gray-200 dark:bg-slate-800 mx-2"></div>
                                    </>
                                )}
                                {/* TODO: Re-enable when marketplace feature is fully implemented
                                {(!user.role || user.role === 'user') && user.seller_status !== 'approved' && (
                                    <>
                                        <Link
                                            href="/seller/apply"
                                            className="text-sm font-medium text-gray-700 dark:text-slate-300 hover:text-gray-900 dark:hover:text-white transition-colors"
                                        >
                                            Trở thành Seller
                                        </Link>
                                        <div className="h-6 w-px bg-gray-200 dark:bg-slate-800 mx-2"></div>
                                    </>
                                )}
                                */}
                                <div className="flex items-center gap-2 text-sm text-gray-700 dark:text-slate-300">
                                    <User className="h-4 w-4" />
                                    <span>{user.email}</span>
                                </div>
                                <button
                                    onClick={logout}
                                    className="text-sm font-medium text-gray-700 dark:text-slate-300 hover:text-gray-900 dark:hover:text-white transition-colors"
                                >
                                    Đăng xuất
                                </button>
                            </>
                        ) : (
                            <>
                                <Link href="/login" className="text-sm font-medium text-gray-700 dark:text-slate-300 hover:text-gray-900 dark:hover:text-white transition-colors">
                                    Đăng nhập
                                </Link>
                                <Link
                                    href="/register"
                                    className="rounded-full bg-gray-900 dark:bg-white px-5 py-2 text-sm font-bold text-white dark:text-slate-900 hover:bg-gray-800 dark:hover:bg-slate-200 transition-colors"
                                >
                                    Đăng ký
                                </Link>
                            </>
                        )}
                    </div>

                    <button className="md:hidden text-gray-700 dark:text-slate-300" onClick={() => setIsMenuOpen(!isMenuOpen)}>
                        {isMenuOpen ? <X /> : <Menu />}
                    </button>
                </div>
            </div>
        </nav>
    );
}
