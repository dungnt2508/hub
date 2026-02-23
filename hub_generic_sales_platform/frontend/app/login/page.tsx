"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "../../lib/authStore";
import GlassContainer from "@/components/ui/GlassContainer";
import { MessageSquare, Lock, Mail, Loader2, AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";

export default function LoginPage() {
  const router = useRouter();
  const { login, isAuthenticated, checkAuth } = useAuthStore();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Check if already authenticated
  useEffect(() => {
    checkAuth().then(() => {
      if (isAuthenticated) {
        router.push("/");
      }
    });
  }, [isAuthenticated, router, checkAuth]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      await login(email, password);
      router.push("/");
    } catch (err: any) {
      setError(err.message || "Đăng nhập thất bại. Vui lòng kiểm tra lại email và mật khẩu.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <GlassContainer className="w-full max-w-md p-8 bg-white/5 border-white/10">
        {/* Logo & Title */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 premium-gradient rounded-2xl mb-4 shadow-lg">
            <MessageSquare className="text-white w-8 h-8" />
          </div>
          <h1 className="text-3xl font-black tracking-tighter bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent mb-2">
            IRIS HUB
          </h1>
          <p className="text-sm text-gray-500 font-medium">AI Assistant Hub v4.0.0</p>
        </div>

        {/* Login Form */}
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Error Message */}
          {error && (
            <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-xl flex items-center gap-3">
              <AlertCircle className="w-5 h-5 text-red-500 shrink-0" />
              <p className="text-sm text-red-400">{error}</p>
            </div>
          )}

          {/* Email Input */}
          <div className="space-y-2">
            <label className="text-xs font-bold text-gray-400 uppercase tracking-widest flex items-center gap-2">
              <Mail className="w-3.5 h-3.5" />
              Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="admin@demo.com"
              className="w-full bg-white/5 border border-white/10 rounded-xl py-3 px-4 focus:outline-none focus:border-accent/50 transition-all text-gray-200 placeholder:text-gray-600"
              disabled={isLoading}
            />
          </div>

          {/* Password Input */}
          <div className="space-y-2">
            <label className="text-xs font-bold text-gray-400 uppercase tracking-widest flex items-center gap-2">
              <Lock className="w-3.5 h-3.5" />
              Mật khẩu
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              placeholder="••••••••"
              className="w-full bg-white/5 border border-white/10 rounded-xl py-3 px-4 focus:outline-none focus:border-accent/50 transition-all text-gray-200 placeholder:text-gray-600"
              disabled={isLoading}
            />
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={isLoading}
            className={cn(
              "w-full premium-gradient py-3 rounded-xl text-sm font-bold text-white shadow-lg transition-all",
              "hover:brightness-110 active:scale-[0.98]",
              "disabled:opacity-50 disabled:cursor-not-allowed",
              "flex items-center justify-center gap-2"
            )}
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Đang đăng nhập...
              </>
            ) : (
              "Đăng nhập"
            )}
          </button>
        </form>

        {/* Demo Credentials Hint */}
        <div className="mt-6 p-4 bg-white/5 rounded-xl border border-white/5">
          <p className="text-xs text-gray-500 text-center">
            Demo: <span className="font-mono text-gray-400">owner@anycar.vn</span> / <span className="font-mono text-gray-400">123456</span>
          </p>
        </div>
      </GlassContainer>
    </div>
  );
}
