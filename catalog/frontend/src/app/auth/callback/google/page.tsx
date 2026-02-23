'use client';

import { useEffect, useState, Suspense, useRef } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { apiClient } from '@/shared/api/client';
import Navbar from '@/components/marketplace/Navbar';
import Footer from '@/components/marketplace/Footer';

function GoogleCallbackContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const processedRef = useRef(false);

  useEffect(() => {
    const code = searchParams.get('code');
    const state = searchParams.get('state') || '/';

    const handle = async () => {
      if (processedRef.current) return;
      processedRef.current = true;

      if (!code) {
        setError('Thiếu mã xác thực Google');
        return;
      }

      try {
        // RULE: Use backend endpoint to exchange code (backend has client_secret)
        // RULE: Backend will verify id_token and issue internal JWT tokens
        const response = await apiClient.get<{ 
          user: any; 
          token: string;  // access_token (backward compatibility)
          refreshToken?: string;  // refresh_token
        }>(`/auth/google/callback?code=${encodeURIComponent(code)}`);
        
        // RULE: Store tokens in localStorage
        if (response.token) {
          localStorage.setItem('token', response.token);
        }
        if (response.refreshToken) {
          localStorage.setItem('refresh_token', response.refreshToken);
        }

        // Reload to let AuthProvider fetch /auth/me with new token
        window.location.href = state || '/';
      } catch (err: any) {
        setError(err.message || 'Xác thực Google thất bại');
      }
    };

    handle();
  }, [searchParams, router]);

  return (
    <div className="min-h-screen bg-white dark:bg-[#0B0C10] text-gray-900 dark:text-slate-200 font-sans">
      <Navbar />
      <main className="container mx-auto px-4 py-16">
        <div className="max-w-md mx-auto bg-white dark:bg-[#111218] border border-gray-200 dark:border-slate-800 rounded-2xl p-8 text-center">
          {error ? (
            <>
              <p className="text-red-500 font-semibold mb-2">Đăng nhập thất bại</p>
              <p className="text-sm text-gray-600 dark:text-slate-400">{error}</p>
            </>
          ) : (
            <>
              <div className="h-8 w-8 border-2 border-primary/30 border-t-primary rounded-full animate-spin mx-auto mb-4"></div>
              <p className="text-sm text-gray-600 dark:text-slate-400">Đang hoàn tất đăng nhập Google...</p>
            </>
          )}
        </div>
      </main>
      <Footer />
    </div>
  );
}

export default function GoogleCallbackPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-white dark:bg-[#0B0C10] flex items-center justify-center">
        <div className="text-gray-600 dark:text-slate-400">Đang tải...</div>
      </div>
    }>
      <GoogleCallbackContent />
    </Suspense>
  );
}
