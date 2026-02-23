"use client";

import { usePathname } from "next/navigation";
import Sidebar from "@/components/Sidebar";
import ProtectedRoute from "@/components/ProtectedRoute";

interface AuthLayoutProps {
  children: React.ReactNode;
}

export function AuthLayout({ children }: AuthLayoutProps) {
  const pathname = usePathname();
  const isLoginPage = pathname === "/login";
  const isWidgetPage = pathname === "/widget";

  // Login & Widget pages: no sidebar or protection
  if (isLoginPage || isWidgetPage) {
    return <>{children}</>;
  }

  // Protected pages need sidebar and authentication
  return (
    <ProtectedRoute>
      <div className="flex h-screen overflow-hidden p-4 gap-4">
        <Sidebar />
        <main className="flex-1 min-w-0 relative">
          {children}
        </main>
      </div>
    </ProtectedRoute>
  );
}
