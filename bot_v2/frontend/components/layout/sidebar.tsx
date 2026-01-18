'use client';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import clsx from 'clsx';
import { useAuth } from '@/lib/auth-context';
import { Button } from '@/components/forms/button';

interface NavItem {
  name: string;
  href: string;
  icon?: string;
}

interface SidebarProps {
  tenantId?: string;
}

const baseNavItems: NavItem[] = [
  { name: 'Tenants', href: '/admin/tenants' },
  { name: 'Users', href: '/admin/users' },
];

const tenantNavItems = (tenantId: string): NavItem[] => [
  { name: 'Channels', href: `/admin/tenants/${tenantId}/channels` },
  { name: 'Catalog', href: `/admin/tenants/${tenantId}/catalog` },
  { name: 'Intents', href: `/admin/tenants/${tenantId}/intents` },
  { name: 'Migrations', href: `/admin/tenants/${tenantId}/migrations` },
  { name: 'Logs', href: `/admin/tenants/${tenantId}/logs` },
  { name: 'Failed Queries', href: `/admin/tenants/${tenantId}/failed-queries` },
];

export function Sidebar({ tenantId }: SidebarProps) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuth();
  
  const navItems = tenantId 
    ? [...baseNavItems, ...tenantNavItems(tenantId)]
    : baseNavItems;

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  return (
    <aside className="w-64 bg-gray-50 border-r border-gray-200 min-h-screen flex flex-col">
      <div className="p-4 border-b border-gray-200">
        <h1 className="text-xl font-bold text-gray-900">Bot V2 Admin</h1>
      </div>
      <nav className="p-4 flex-1">
        <ul className="space-y-1">
          {navItems.map((item) => {
            const isActive = pathname === item.href || 
              (item.href !== '/admin/tenants' && pathname?.startsWith(item.href));
            
            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className={clsx(
                    'block px-4 py-2 rounded-md text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-gray-900 text-white'
                      : 'text-gray-700 hover:bg-gray-100'
                  )}
                >
                  {item.name}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>
      <div className="p-4 border-t border-gray-200">
        <div className="mb-3">
          <div className="text-sm font-medium text-gray-900">{user?.name || 'User'}</div>
          <div className="text-xs text-gray-500">{user?.email}</div>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={handleLogout}
          className="w-full"
        >
          Đăng xuất
        </Button>
      </div>
    </aside>
  );
}
