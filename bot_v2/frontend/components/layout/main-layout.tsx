'use client';

import { Sidebar } from './sidebar';
import { usePathname } from 'next/navigation';
import { AuthGuard } from '@/components/auth/auth-guard';

export function MainLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const match = pathname?.match(/\/admin\/tenants\/([^/]+)/);
  const tenantId = match ? match[1] : undefined;
  
  return (
    <AuthGuard>
      <div className="flex min-h-screen">
        <Sidebar tenantId={tenantId} />
        <main className="flex-1 p-8 bg-white">
          {children}
        </main>
      </div>
    </AuthGuard>
  );
}
