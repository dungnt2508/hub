"use client";

import { cn } from "@/lib/utils";

export type LifecycleState =
    | "idle"
    | "browsing"
    | "searching"
    | "viewing"
    | "comparing"
    | "analyzing"
    | "purchasing"
    | "handover"
    | "completed"
    | "closed"
    | "error"
    | "waiting_input"
    | "filtering";

interface StateBadgeProps {
    state: string;
    className?: string;
}

const STATE_CONFIG: Record<string, { label: string; color: string }> = {
    idle: { label: "Sẵn sàng", color: "bg-gray-500/10 text-gray-500 border-gray-500/20" },
    browsing: { label: "Đang xem", color: "bg-blue-500/10 text-blue-500 border-blue-500/20" },
    searching: { label: "Tìm kiếm", color: "bg-cyan-500/10 text-cyan-500 border-cyan-500/20" },
    viewing: { label: "Chi tiết", color: "bg-purple-500/10 text-purple-500 border-purple-500/20" },
    comparing: { label: "So sánh", color: "bg-orange-500/10 text-orange-500 border-orange-500/20" },
    analyzing: { label: "Phân tích", color: "bg-yellow-500/10 text-yellow-500 border-yellow-500/20" },
    purchasing: { label: "Thanh toán", color: "bg-green-500/10 text-green-500 border-green-500/20" },
    handover: { label: "Nhân viên hỗ trợ", color: "bg-red-500/10 text-red-500 border-red-500/20" },
    completed: { label: "Hoàn tất", color: "bg-emerald-500/10 text-emerald-500 border-emerald-500/20" },
    closed: { label: "Đã đóng", color: "bg-neutral-500/10 text-neutral-500 border-neutral-500/20" },
    error: { label: "Lỗi", color: "bg-red-500/10 text-red-500 border-red-500/20" },
    waiting_input: { label: "Đợi khách", color: "bg-pink-500/10 text-pink-500 border-pink-500/20" },
    filtering: { label: "Lọc", color: "bg-indigo-500/10 text-indigo-500 border-indigo-500/20" },
};

export function StateBadge({ state, className }: StateBadgeProps) {
    const s = state?.toLowerCase() || "idle";
    const config = STATE_CONFIG[s] || { label: state, color: "bg-gray-500/10 text-gray-500 border-gray-500/20" };

    return (
        <span className={cn(
            "px-2 py-0.5 rounded text-[10px] font-black uppercase tracking-wider border",
            config.color,
            className
        )}>
            {config.label}
        </span>
    );
}
