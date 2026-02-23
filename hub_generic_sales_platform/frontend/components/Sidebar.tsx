"use client";

import { LayoutDashboard, Settings, MessageSquare, ChevronLeft, UserCircle } from "lucide-react";
import GlassContainer from "./ui/GlassContainer";
import { cn } from "@/lib/utils";
import { useUIStore } from "@/lib/store";
import { useAuthStore } from "@/lib/authStore";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { LogOut } from "lucide-react";
import { NAV_GROUPS, canSeeNavItem, DASHBOARD_HREF, SETTINGS_HREF } from "@/lib/navConfig";

export default function Sidebar() {
    const { isSidebarCollapsed, setSidebarCollapsed } = useUIStore();
    const { user, logout } = useAuthStore();
    const pathname = usePathname();
    const router = useRouter();
    const userRole = user?.role;

    const handleLogout = () => {
        logout();
        router.push("/login");
    };

    const filteredGroups = NAV_GROUPS.map((group) => ({
        ...group,
        items: group.items.filter((item) => canSeeNavItem(item, userRole)),
    })).filter((g) => g.items.length > 0);

    return (
        <GlassContainer className={cn(
            "h-[calc(100vh-2rem)] flex flex-col transition-all duration-500 ease-in-out border-white/5",
            isSidebarCollapsed ? "w-20" : "w-64"
        )}>
            {/* Logo Section */}
            <div className="p-6 flex items-center gap-4">
                <div className="w-10 h-10 premium-gradient rounded-xl flex items-center justify-center shadow-lg shrink-0">
                    <MessageSquare className="text-white w-5 h-5" />
                </div>
                {!isSidebarCollapsed && (
                    <div className="flex flex-col overflow-hidden">
                        <span className="text-lg font-black tracking-tighter bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent leading-tight">
                            IRIS HUB
                        </span>
                        <span className="text-[10px] font-bold text-accent uppercase tracking-widest leading-none">
                            v4.0.0 (2026)
                        </span>
                    </div>
                )}
            </div>

            {/* Navigation Groups */}
            <nav className="flex-1 px-4 py-6 space-y-8 overflow-y-auto no-scrollbar">
                {/* Home/Dashboard is still a top-level link */}
                <Link
                    href={DASHBOARD_HREF}
                    className={cn(
                        "group flex items-center gap-4 p-3.5 rounded-2xl cursor-pointer transition-all duration-300",
                        pathname === DASHBOARD_HREF
                            ? "bg-accent/10 border border-accent/20 text-white shadow-[0_0_20px_rgba(168,85,247,0.1)]"
                            : "text-gray-400 hover:bg-white/5 hover:text-gray-200 border border-transparent"
                    )}
                >
                    <LayoutDashboard className={cn(
                        "w-5 h-5 transition-transform duration-300 group-hover:scale-110 shrink-0",
                        pathname === DASHBOARD_HREF && "text-accent"
                    )} />
                    {!isSidebarCollapsed && (
                        <span className="font-semibold text-sm tracking-wide truncate">Tổng quan</span>
                    )}
                </Link>

                {filteredGroups.map((group, groupIndex) => (
                    <div key={group.label || `group-${groupIndex}`} className="space-y-2">
                        {!isSidebarCollapsed && group.label && (
                            <h3 className="px-4 text-[10px] font-bold text-gray-500 uppercase tracking-[0.2em] mb-3">
                                {group.label}
                            </h3>
                        )}
                        <div className="space-y-1">
                            {group.items.map((item) => {
                                const isActive = pathname === item.href;
                                return (
                                    <Link
                                        key={item.href}
                                        href={item.href}
                                        className={cn(
                                            "group flex items-center gap-4 p-3.5 rounded-2xl cursor-pointer transition-all duration-300",
                                            isActive
                                                ? "bg-accent/10 border border-accent/20 text-white shadow-[0_0_20px_rgba(168,85,247,0.1)]"
                                                : "text-gray-400 hover:bg-white/5 hover:text-gray-200 border border-transparent"
                                        )}
                                    >
                                        <item.icon className={cn(
                                            "w-5 h-5 transition-transform duration-300 group-hover:scale-110 shrink-0",
                                            isActive && "text-accent"
                                        )} />
                                        {!isSidebarCollapsed && (
                                            <span className="font-semibold text-sm tracking-wide truncate">{item.label}</span>
                                        )}
                                        {isActive && !isSidebarCollapsed && (
                                            <div className="ml-auto w-1.5 h-1.5 rounded-full bg-accent animate-pulse shadow-[0_0_8px_var(--accent-primary)]"></div>
                                        )}
                                    </Link>
                                );
                            })}
                        </div>
                    </div>
                ))}
            </nav>

            {/* User & Settings */}
            <div className="p-4 border-t border-white/5 bg-white/5 space-y-1">
                <Link
                    href={SETTINGS_HREF}
                    className={cn(
                        "flex items-center gap-4 p-3 text-gray-400 hover:text-white rounded-2xl transition-colors",
                        pathname === SETTINGS_HREF && "text-white"
                    )}
                >
                    <Settings className="w-5 h-5 shrink-0" />
                    {!isSidebarCollapsed && <span className="font-medium text-sm">Settings</span>}
                </Link>

                <div className="flex items-center gap-3 p-3 mt-2 bg-white/5 rounded-2xl border border-white/5">
                    <UserCircle className="w-5 h-5 text-gray-500 shrink-0" />
                    {!isSidebarCollapsed && (
                        <div className="flex flex-col text-[10px] overflow-hidden flex-1">
                            <span className="font-bold text-gray-300 truncate">{user?.email || "User"}</span>
                            <span className="text-gray-500 truncate italic capitalize">{user?.role || "viewer"}</span>
                        </div>
                    )}
                </div>

                <button
                    onClick={handleLogout}
                    className="w-full mt-2 flex items-center justify-center gap-2 p-2 rounded-xl border border-red-500/20 hover:bg-red-500/10 text-red-500 hover:text-red-400 group transition-all"
                >
                    <LogOut className="w-4 h-4" />
                    {!isSidebarCollapsed && (
                        <span className="text-xs font-bold">Đăng xuất</span>
                    )}
                </button>

                <button
                    onClick={() => setSidebarCollapsed(!isSidebarCollapsed)}
                    className="w-full mt-4 flex items-center justify-center p-2 rounded-xl border border-white/5 hover:bg-accent/10 text-gray-500 hover:text-accent group transition-all"
                >
                    <ChevronLeft className={cn(
                        "w-4 h-4 transition-transform duration-500",
                        isSidebarCollapsed && "rotate-180"
                    )} />
                </button>
            </div>
        </GlassContainer>
    );
}
