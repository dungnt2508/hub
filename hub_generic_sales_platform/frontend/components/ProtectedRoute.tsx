"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useAuthStore } from "../lib/authStore";
import { Loader2 } from "lucide-react";

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export default function ProtectedRoute({ children }: ProtectedRouteProps) {
  const router = useRouter();
  const pathname = usePathname();
  const { isAuthenticated, isLoading, checkAuth } = useAuthStore();
  const [hasChecked, setHasChecked] = useState(false);

  useEffect(() => {
    const initAuth = async () => {
      await checkAuth();
      setHasChecked(true);
    };
    initAuth();
  }, [checkAuth]);

  useEffect(() => {
    if (hasChecked && !isLoading && !isAuthenticated && pathname !== "/login") {
      router.push("/login");
    }
  }, [isAuthenticated, isLoading, pathname, router, hasChecked]);

  // Show loading while checking auth
  if (!hasChecked || isLoading) {
    return (
      <div className="h-screen flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-8 h-8 text-accent animate-spin mx-auto mb-4" />
          <p className="text-sm text-gray-500 font-medium">Đang kiểm tra xác thực...</p>
        </div>
      </div>
    );
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    return null;
  }

  return <>{children}</>;
}
