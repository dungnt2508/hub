'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/lib/auth-context';
import Navbar from '@/components/marketplace/Navbar';
import Footer from '@/components/marketplace/Footer';
import { Mail, Lock, CheckCircle, ArrowRight } from 'lucide-react';

export default function RegisterPage() {
    const router = useRouter();
    const { register, getRedirectRoute } = useAuth();
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const validatePassword = (pwd: string) => {
        if (pwd.length < 8) return 'Mật khẩu phải có ít nhất 8 ký tự';
        if (!/[A-Z]/.test(pwd)) return 'Mật khẩu phải có ít nhất 1 chữ hoa';
        if (!/[a-z]/.test(pwd)) return 'Mật khẩu phải có ít nhất 1 chữ thường';
        if (!/[0-9]/.test(pwd)) return 'Mật khẩu phải có ít nhất 1 số';
        return null;
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');

        if (password !== confirmPassword) {
            setError('Mật khẩu xác nhận không khớp');
            return;
        }

        const passwordError = validatePassword(password);
        if (passwordError) {
            setError(passwordError);
            return;
        }

        setLoading(true);

        try {
            await register(email, password);
            // Redirect based on user role (usually USER role for new registrations)
            router.push(getRedirectRoute());
        } catch (err: any) {
            setError(err.response?.data?.message || err.message || 'Đăng ký thất bại. Email có thể đã được sử dụng.');
        } finally {
            setLoading(false);
        }
    };

    const passwordStrength = password.length > 0 ? (
        password.length >= 8 && /[A-Z]/.test(password) && /[a-z]/.test(password) && /[0-9]/.test(password) ? 'strong' :
        password.length >= 6 ? 'medium' : 'weak'
    ) : null;

    return (
        <div className="min-h-screen bg-white dark:bg-[#0B0C10] text-gray-900 dark:text-slate-200 font-sans">
            <Navbar />

            <main className="flex items-center justify-center py-20 px-4">
                <div className="w-full max-w-md">
                    <div className="bg-white dark:bg-[#111218] rounded-2xl border border-gray-200 dark:border-slate-800 p-8 shadow-2xl shadow-black/20">
                        <div className="text-center mb-8">
                            <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">Tạo tài khoản</h1>
                            <p className="text-gray-600 dark:text-slate-400 text-sm">
                                Bắt đầu hành trình với n8n workflow marketplace
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
                                {passwordStrength && (
                                    <div className="mt-2">
                                        <div className="flex gap-1 mb-1">
                                            {[1, 2, 3].map((i) => (
                                                <div
                                                    key={i}
                                                    className={`h-1 flex-1 rounded ${
                                                        passwordStrength === 'strong' ? 'bg-green-500' :
                                                        passwordStrength === 'medium' && i <= 2 ? 'bg-yellow-500' :
                                                        passwordStrength === 'weak' && i === 1 ? 'bg-red-500' :
                                                        'bg-gray-300 dark:bg-slate-700'
                                                    }`}
                                                />
                                            ))}
                                        </div>
                                        <p className="text-xs text-gray-500 dark:text-slate-500">
                                            {passwordStrength === 'strong' && '✓ Mật khẩu mạnh'}
                                            {passwordStrength === 'medium' && '⚠ Mật khẩu trung bình'}
                                            {passwordStrength === 'weak' && '✗ Mật khẩu yếu'}
                                        </p>
                                    </div>
                                )}
                            </div>

                            <div>
                                <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">
                                    Xác nhận mật khẩu
                                </label>
                                <div className="relative">
                                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400 dark:text-slate-500" />
                                    <input
                                        id="confirmPassword"
                                        type="password"
                                        value={confirmPassword}
                                        onChange={(e) => setConfirmPassword(e.target.value)}
                                        required
                                        className="w-full pl-10 pr-4 py-3 bg-gray-50 dark:bg-slate-900/50 border border-gray-200 dark:border-slate-800 rounded-lg text-gray-900 dark:text-white placeholder:text-gray-400 dark:placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all"
                                        placeholder="••••••••"
                                    />
                                </div>
                                {confirmPassword && password === confirmPassword && (
                                    <div className="mt-2 flex items-center gap-2 text-xs text-green-400">
                                        <CheckCircle className="h-3 w-3" />
                                        <span>Mật khẩu khớp</span>
                                    </div>
                                )}
                            </div>

                            <button
                                type="submit"
                                disabled={loading}
                                className="w-full py-3 bg-primary hover:bg-[#FF8559] text-white rounded-lg font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                            >
                                {loading ? (
                                    <>
                                        <div className="h-4 w-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                                        <span>Đang tạo tài khoản...</span>
                                    </>
                                ) : (
                                    <>
                                        <span>Đăng ký</span>
                                        <ArrowRight className="h-4 w-4" />
                                    </>
                                )}
                            </button>
                        </form>

                        <div className="mt-6 text-center">
                            <p className="text-gray-600 dark:text-slate-400 text-sm">
                                Đã có tài khoản?{' '}
                                <Link href="/login" className="text-primary hover:text-[#FF8559] font-semibold transition-colors">
                                    Đăng nhập ngay
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
