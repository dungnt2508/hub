"use client";

import GlassContainer from "@/components/ui/GlassContainer";
import { User, Shield, Bell, Cpu, Key, Save, LogOut, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiService } from "@/lib/apiService";
import { useAuthStore } from "@/lib/authStore";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { toast } from "sonner";

export default function SettingsPage() {
    const queryClient = useQueryClient();
    const router = useRouter();
    const { logout } = useAuthStore();
    const [activeSection, setActiveSection] = useState("profile");

    const [passwordForm, setPasswordForm] = useState({
        current_password: "",
        new_password: "",
        confirm_password: "",
    });

    const { data: user, isLoading: isUserLoading } = useQuery({
        queryKey: ["current-user"],
        queryFn: () => apiService.getCurrentUser(),
    });

    const changePasswordMutation = useMutation({
        mutationFn: () =>
            apiService.changePassword(passwordForm.current_password, passwordForm.new_password),
        onSuccess: () => {
            setPasswordForm({ current_password: "", new_password: "", confirm_password: "" });
            toast.success("Đã đổi mật khẩu thành công.");
        },
        onError: (error: any) => {
            toast.error(error.response?.data?.detail || "Lỗi khi đổi mật khẩu");
        },
    });

    const handleChangePassword = (e: React.FormEvent) => {
        e.preventDefault();
        if (passwordForm.new_password !== passwordForm.confirm_password) {
            toast.error("Mật khẩu mới không khớp.");
            return;
        }
        if (passwordForm.new_password.length < 6) {
            toast.error("Mật khẩu mới phải có ít nhất 6 ký tự.");
            return;
        }
        changePasswordMutation.mutate();
    };

    const handleLogout = () => {
        logout();
        router.push("/login");
    };

    const sections = [
        { id: "profile", label: "Profile & Identity", icon: User },
        { id: "security", label: "Đổi mật khẩu", icon: Shield },
        { id: "model", label: "Model Selection", icon: Cpu },
        { id: "notifications", label: "Notifications", icon: Bell },
    ];

    return (
        <div className="h-full flex flex-col space-y-6">
            <div className="flex items-center justify-between">
                <div className="flex flex-col">
                    <h1 className="text-2xl font-black text-white italic">Cài đặt</h1>
                    <p className="text-xs text-gray-500 font-bold uppercase tracking-[0.2em] mt-1 pr-2">Profile & Security</p>
                </div>
            </div>

            <div className="flex-1 grid grid-cols-12 gap-8 min-h-0">
                <div className="col-span-3 flex flex-col gap-2">
                    {sections.map((item) => (
                        <button
                            key={item.id}
                            onClick={() => setActiveSection(item.id)}
                            className={cn(
                                "flex items-center gap-4 p-4 rounded-2xl cursor-pointer transition-all duration-300 text-left",
                                activeSection === item.id ? "bg-white/10 text-white border border-white/5" : "text-gray-500 hover:text-gray-300 hover:bg-white/5"
                            )}
                        >
                            <item.icon className="w-5 h-5" />
                            <span className="text-sm font-bold">{item.label}</span>
                        </button>
                    ))}
                    <button
                        onClick={handleLogout}
                        className="mt-auto p-4 flex items-center gap-4 text-red-500/60 hover:text-red-500 cursor-pointer transition-colors group"
                    >
                        <LogOut className="w-5 h-5 group-hover:-translate-x-1 transition-transform" />
                        <span className="text-sm font-bold">Đăng xuất</span>
                    </button>
                </div>

                <GlassContainer className="col-span-9 p-10 bg-white/5 border-white/5 overflow-y-auto no-scrollbar">
                    <div className="max-w-2xl space-y-10">
                        {activeSection === "profile" && (
                            <div>
                                <h3 className="text-lg font-black text-white mb-6 underline decoration-accent/40 decoration-4 underline-offset-8">Profile & Identity</h3>
                                {isUserLoading ? (
                                    <div className="flex items-center gap-2 text-gray-500"><Loader2 className="w-5 h-5 animate-spin" /> Đang tải...</div>
                                ) : user ? (
                                    <div className="space-y-4">
                                        <div>
                                            <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest block mb-2">Email</label>
                                            <input type="text" readOnly value={user.email} className="w-full bg-white/5 border border-white/10 rounded-xl p-4 text-sm text-gray-300 focus:outline-none" />
                                        </div>
                                        <div>
                                            <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest block mb-2">Role</label>
                                            <input type="text" readOnly value={user.role} className="w-full bg-white/5 border border-white/10 rounded-xl p-4 text-sm text-gray-300 focus:outline-none capitalize" />
                                        </div>
                                        <div>
                                            <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest block mb-2">Tenant</label>
                                            <input type="text" readOnly value={user.tenant_name || user.tenant_id} className="w-full bg-white/5 border border-white/10 rounded-xl p-4 text-sm text-gray-300 focus:outline-none" />
                                        </div>
                                    </div>
                                ) : (
                                    <p className="text-gray-500 text-sm">Không tải được thông tin user</p>
                                )}
                            </div>
                        )}

                        {activeSection === "security" && (
                            <div>
                                <h3 className="text-lg font-black text-white mb-6 underline decoration-accent/40 decoration-4 underline-offset-8">Đổi mật khẩu</h3>
                                <form onSubmit={handleChangePassword} className="space-y-4">
                                    <div>
                                        <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest block mb-2">Mật khẩu hiện tại</label>
                                        <input
                                            type="password"
                                            value={passwordForm.current_password}
                                            onChange={(e) => setPasswordForm({ ...passwordForm, current_password: e.target.value })}
                                            placeholder="••••••••"
                                            className="w-full bg-white/5 border border-white/10 rounded-xl p-4 text-sm text-white focus:outline-none focus:border-accent placeholder:text-gray-600"
                                            required
                                        />
                                    </div>
                                    <div>
                                        <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest block mb-2">Mật khẩu mới</label>
                                        <input
                                            type="password"
                                            value={passwordForm.new_password}
                                            onChange={(e) => setPasswordForm({ ...passwordForm, new_password: e.target.value })}
                                            placeholder="••••••••"
                                            minLength={6}
                                            className="w-full bg-white/5 border border-white/10 rounded-xl p-4 text-sm text-white focus:outline-none focus:border-accent placeholder:text-gray-600"
                                            required
                                        />
                                    </div>
                                    <div>
                                        <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest block mb-2">Xác nhận mật khẩu mới</label>
                                        <input
                                            type="password"
                                            value={passwordForm.confirm_password}
                                            onChange={(e) => setPasswordForm({ ...passwordForm, confirm_password: e.target.value })}
                                            placeholder="••••••••"
                                            className="w-full bg-white/5 border border-white/10 rounded-xl p-4 text-sm text-white focus:outline-none focus:border-accent placeholder:text-gray-600"
                                            required
                                        />
                                    </div>
                                    <button
                                        type="submit"
                                        disabled={changePasswordMutation.isPending || !passwordForm.current_password || !passwordForm.new_password || !passwordForm.confirm_password}
                                        className="flex items-center gap-2 px-6 py-3 premium-gradient rounded-xl text-xs font-black text-white shadow-lg disabled:opacity-50"
                                    >
                                        {changePasswordMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Key className="w-4 h-4" />}
                                        {changePasswordMutation.isPending ? "Đang xử lý..." : "Đổi mật khẩu"}
                                    </button>
                                </form>
                            </div>
                        )}

                        {activeSection === "model" && (
                            <div>
                                <h3 className="text-lg font-black text-white mb-6 italic underline decoration-secondary/40 decoration-4 underline-offset-8">Model Orchestration</h3>
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="p-4 rounded-2xl bg-accent/5 border border-accent/20 flex flex-col justify-between">
                                        <div className="flex items-center gap-3 mb-4">
                                            <Cpu className="w-5 h-5 text-accent" />
                                            <span className="text-xs font-black text-white uppercase tracking-widest">Primary Engine</span>
                                        </div>
                                        <div className="text-lg font-bold text-accent">GPT-4o Mini</div>
                                        <div className="text-[8px] text-gray-500 mt-2 font-black uppercase tracking-tighter">Current ROI: +92%</div>
                                    </div>
                                    <div className="p-4 rounded-2xl bg-white/5 border border-white/10 opacity-40 grayscale flex flex-col justify-between">
                                        <div className="flex items-center gap-3 mb-4">
                                            <Cpu className="w-5 h-5 text-gray-400" />
                                            <span className="text-xs font-black text-gray-400 uppercase tracking-widest">Fallback Engine</span>
                                        </div>
                                        <div className="text-lg font-bold text-gray-500 italic">Gemini 1.5 Pro</div>
                                        <div className="text-[8px] text-gray-600 mt-2 font-black uppercase tracking-tighter">Requires Pro Subscription</div>
                                    </div>
                                </div>
                                <p className="text-[10px] text-gray-500 mt-4 italic">Model configuration is managed per Bot. Cấu hình theo từng Bot tại trang Bot & Kịch bản.</p>
                            </div>
                        )}

                        {activeSection === "notifications" && (
                            <div>
                                <h3 className="text-lg font-black text-white mb-6 underline decoration-accent/40 decoration-4 underline-offset-8">Notifications</h3>
                                <p className="text-sm text-gray-400">Tính năng thông báo đang phát triển.</p>
                            </div>
                        )}
                    </div>
                </GlassContainer>
            </div>
        </div>
    );
}
