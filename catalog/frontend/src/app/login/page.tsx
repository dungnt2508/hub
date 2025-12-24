'use client';

import { useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/lib/auth-context';
import { apiClient } from '@/shared/api/client';
import Navbar from '@/components/marketplace/Navbar';
import Footer from '@/components/marketplace/Footer';
import { Mail, Lock, ArrowRight } from 'lucide-react';

export default function LoginPage() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const { login, getRedirectRoute } = useAuth();
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const [oauthLoading, setOauthLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            await login(email, password);
            // Redirect based on user role, or return to previous page if specified
            const returnTo = searchParams.get('returnTo') || getRedirectRoute();
            router.push(returnTo);
        } catch (err: any) {
            // apiClient formats errors as ErrorResponse, so err.message is available directly
            setError(err.message || err.response?.data?.message || 'Đăng nhập thất bại. Vui lòng kiểm tra lại email và mật khẩu.');
        } finally {
            setLoading(false);
        }
    };

    const buildState = () => {
        return searchParams.get('returnTo') || '/';
    };

    const handleAzureLogin = async () => {
        try {
            setError('');
            setOauthLoading(true);
            // apiClient.get() already unwraps response.data, so response is already the data
            const response = await apiClient.get<{ authUrl: string }>('/auth/azure', {
                params: { state: buildState() },
            });
            const authUrl = response.authUrl;
            window.location.href = authUrl;
        } catch (err: any) {
            setError('Không thể kết nối với Azure. Vui lòng thử lại.');
        } finally {
            setOauthLoading(false);
        }
    };

    const handleGoogleLogin = async () => {
        try {
            setError('');
            setOauthLoading(true);
            const response = await apiClient.get<{ authUrl: string }>('/auth/google', {
                params: { state: buildState() },
            });
            const authUrl = response.authUrl;
            window.location.href = authUrl;
        } catch (err: any) {
            setError('Không thể kết nối với Google. Vui lòng thử lại.');
        } finally {
            setOauthLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-white dark:bg-[#0B0C10] text-gray-900 dark:text-slate-200 font-sans">
            <Navbar />

            <main className="flex items-center justify-center py-20 px-4">
                <div className="w-full max-w-md">
                    <div className="bg-white dark:bg-[#111218] rounded-2xl border border-gray-200 dark:border-slate-800 p-8 shadow-2xl shadow-black/20">
                        <div className="text-center mb-8">
                            <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">Chào mừng trở lại</h1>
                            <p className="text-gray-600 dark:text-slate-400 text-sm">
                                Đăng nhập để truy cập dashboard và quản lý workflow của bạn
                            </p>
                        </div>

                        {error && (
                            <div className="mb-6 p-4 bg-red-500/10 border border-red-500/30 text-red-400 rounded-lg text-sm">
                                {error}
                            </div>
                        )}

                        <form onSubmit={handleSubmit} className="space-y-5">
                            <div>
                                <label htmlFor="email" className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">
                                    Email
                                </label>
                                <div className="relative">
                                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400 dark:text-slate-500" />
                                    <input
                                        id="email"
                                        type="email"
                                        value={email}
                                        onChange={(e) => setEmail(e.target.value)}
                                        required
                                        className="w-full pl-10 pr-4 py-3 bg-gray-50 dark:bg-slate-900/50 border border-gray-200 dark:border-slate-800 rounded-lg text-gray-900 dark:text-white placeholder:text-gray-400 dark:placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all"
                                        placeholder="you@example.com"
                                    />
                                </div>
                            </div>

                            <div>
                                <label htmlFor="password" className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">
                                    Mật khẩu
                                </label>
                                <div className="relative">
                                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400 dark:text-slate-500" />
                                    <input
                                        id="password"
                                        type="password"
                                        value={password}
                                        onChange={(e) => setPassword(e.target.value)}
                                        required
                                        className="w-full pl-10 pr-4 py-3 bg-gray-50 dark:bg-slate-900/50 border border-gray-200 dark:border-slate-800 rounded-lg text-gray-900 dark:text-white placeholder:text-gray-400 dark:placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all"
                                        placeholder="••••••••"
                                    />
                                </div>
                            </div>

                            <button
                                type="submit"
                                disabled={loading}
                                className="w-full py-3 bg-primary hover:bg-[#FF8559] text-white rounded-lg font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                            >
                                {loading ? (
                                    <>
                                        <div className="h-4 w-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                                        <span>Đang đăng nhập...</span>
                                    </>
                                ) : (
                                    <>
                                        <span>Đăng nhập</span>
                                        <ArrowRight className="h-4 w-4" />
                                    </>
                                )}
                            </button>
                        </form>

                        <div className="mt-6">
                            <div className="relative">
                                <div className="absolute inset-0 flex items-center">
                                    <div className="w-full border-t border-slate-800"></div>
                                </div>
                                <div className="relative flex justify-center text-sm">
                                    <span className="px-3 bg-white dark:bg-[#111218] text-gray-500 dark:text-slate-500">Hoặc</span>
                                </div>
                            </div>

                            <button 
                                onClick={handleAzureLogin}
                                disabled={oauthLoading}
                                className="mt-4 w-full py-3 bg-gray-100 dark:bg-slate-900/50 border border-gray-200 dark:border-slate-800 rounded-lg font-semibold hover:bg-gray-200 dark:hover:bg-slate-800/50 transition-colors flex items-center justify-center gap-2 text-gray-700 dark:text-slate-200 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                <svg className="w-5 h-5" viewBox="0 0 24 24">
                                    <path fill="#00A4EF" d="M0 0h11.377v11.372H0z" />
                                    <path fill="#FFB900" d="M12.623 0H24v11.372H12.623z" />
                                    <path fill="#7FBA00" d="M0 12.628h11.377V24H0z" />
                                    <path fill="#F25022" d="M12.623 12.628H24V24H12.623z" />
                                </svg>
                                Đăng nhập bằng Azure
                            </button>

                            <button
                                onClick={handleGoogleLogin}
                                disabled={oauthLoading}
                                className="mt-3 w-full py-3 bg-gray-100 dark:bg-slate-900/50 border border-gray-200 dark:border-slate-800 rounded-lg font-semibold hover:bg-gray-200 dark:hover:bg-slate-800/50 transition-colors flex items-center justify-center gap-2 text-gray-700 dark:text-slate-200 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                <svg className="w-5 h-5" viewBox="0 0 48 48" aria-hidden="true">
                                    <path fill="#EA4335" d="M24 9.5c3.54 0 6 1.54 7.38 2.83l5.4-5.4C33.9 3.58 29.47 2 24 2 14.82 2 6.71 7.44 3.14 15.09l6.91 5.36C11.79 14.01 17.42 9.5 24 9.5z" />
                                    <path fill="#4285F4" d="M46.5 24.5c0-1.64-.15-3.21-.43-4.72H24v9.13h12.65c-.54 2.9-2.17 5.36-4.61 7.01l7.1 5.5C43.83 37.82 46.5 31.7 46.5 24.5z" />
                                    <path fill="#FBBC05" d="M10.05 28.45a14.49 14.49 0 0 1-.76-4.45c0-1.54.27-3.03.75-4.44l-6.9-5.36A23.892 23.892 0 0 0 1.5 24c0 3.9.93 7.58 2.57 10.8l5.98-6.35z" />
                                    <path fill="#34A853" d="M24 46c6.48 0 11.9-2.14 15.87-5.86l-7.1-5.5c-2 1.35-4.6 2.14-8.77 2.14-6.58 0-12.21-4.51-13.9-10.66l-6.91 5.36C6.7 40.56 14.82 46 24 46z" />
                                    <path fill="none" d="M1.5 1.5h45v45h-45z" />
                                </svg>
                                Đăng nhập bằng Google
                            </button>
                        </div>

                        <div className="mt-6 text-center">
                            <p className="text-gray-600 dark:text-slate-400 text-sm">
                                Chưa có tài khoản?{' '}
                                <Link href="/register" className="text-primary hover:text-[#FF8559] font-semibold transition-colors">
                                    Đăng ký ngay
                                </Link>
                            </p>
                        </div>

                        <div className="mt-6 text-center">
                            <Link href="/" className="text-sm text-gray-500 dark:text-slate-500 hover:text-gray-700 dark:hover:text-slate-400 transition-colors">
                                ← Quay lại trang chủ
                            </Link>
                        </div>
                    </div>
                </div>
            </main>

            <Footer />
        </div>
    );
}
