'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    // Redirect to login if not authenticated, otherwise to dashboard
    const token = localStorage.getItem('admin_token');
    if (token) {
      router.push('/admin/dashboard');
    } else {
      router.push('/login');
    }
  }, [router]);

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-gray-600">Đang chuyển hướng...</div>
    </div>
  );
}

