"use client";

import { cn } from "@/lib/utils";
import { MigrationJob } from "@/lib/apiService";
import { Eye, CheckCircle } from "lucide-react";

interface MigrationJobListProps {
    jobs: MigrationJob[];
    isLoading: boolean;
    onViewPreview: (job: MigrationJob) => void;
    onConfirm: (job: MigrationJob) => void;
}

const STATUS_COLORS: Record<string, string> = {
    pending: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
    processing: "bg-blue-500/20 text-blue-400 border-blue-500/30",
    staged: "bg-green-500/20 text-green-400 border-green-500/30",
    completed: "bg-gray-500/20 text-gray-400 border-gray-500/30",
    failed: "bg-red-500/20 text-red-400 border-red-500/30",
};

export default function MigrationJobList({
    jobs,
    isLoading,
    onViewPreview,
    onConfirm,
}: MigrationJobListProps) {
    const formatDate = (iso: string) => {
        try {
            const d = new Date(iso);
            return d.toLocaleString("vi-VN", { dateStyle: "short", timeStyle: "short" });
        } catch {
            return iso;
        }
    };

    return (
        <div className="overflow-x-auto">
            <table className="w-full text-left">
                <thead>
                    <tr className="border-b border-white/10">
                        <th className="pb-3 text-[10px] font-black text-gray-500 uppercase tracking-widest">ID</th>
                        <th className="pb-3 text-[10px] font-black text-gray-500 uppercase tracking-widest">URL / Nguồn</th>
                        <th className="pb-3 text-[10px] font-black text-gray-500 uppercase tracking-widest">Trạng thái</th>
                        <th className="pb-3 text-[10px] font-black text-gray-500 uppercase tracking-widest">Tạo lúc</th>
                        <th className="pb-3 text-[10px] font-black text-gray-500 uppercase tracking-widest">Thao tác</th>
                    </tr>
                </thead>
                <tbody>
                    {isLoading ? (
                        <tr>
                            <td colSpan={5} className="py-12 text-center">
                                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-accent mx-auto"></div>
                                <p className="text-xs text-gray-500 mt-2">Đang tải...</p>
                            </td>
                        </tr>
                    ) : jobs.length === 0 ? (
                        <tr>
                            <td colSpan={5} className="py-16 text-center text-gray-500 italic">
                                Chưa có job nào. Nhập URL và bắt đầu cào.
                            </td>
                        </tr>
                    ) : (
                        jobs.map((job) => (
                            <tr key={job.id} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                                <td className="py-3">
                                    <span className="text-xs font-mono text-gray-400">{job.id.slice(0, 8)}...</span>
                                </td>
                                <td className="py-3">
                                    <span className="text-xs text-white truncate max-w-[200px] block" title={job.metadata?.url || job.metadata?.filename || "-"}>
                                        {job.metadata?.url || job.metadata?.filename || "-"}
                                    </span>
                                </td>
                                <td className="py-3">
                                    <span className={cn(
                                        "px-2 py-0.5 rounded-lg text-[9px] font-bold uppercase border",
                                        STATUS_COLORS[job.status] || "bg-gray-500/20 text-gray-400"
                                    )}>
                                        {job.status}
                                    </span>
                                </td>
                                <td className="py-3 text-xs text-gray-500">
                                    {formatDate(job.created_at)}
                                </td>
                                <td className="py-3">
                                    <div className="flex gap-2">
                                        {(job.status === "staged" || job.status === "completed" || job.status === "failed") && (
                                            <button
                                                onClick={() => onViewPreview(job)}
                                                className="p-2 rounded-lg bg-white/5 hover:bg-white/10 text-gray-400 hover:text-accent transition-colors"
                                                title="Xem Preview"
                                            >
                                                <Eye className="w-4 h-4" />
                                            </button>
                                        )}
                                        {job.status === "staged" && (
                                            <button
                                                onClick={() => onConfirm(job)}
                                                className="p-2 rounded-lg bg-green-500/20 hover:bg-green-500/30 text-green-400 transition-colors"
                                                title="Xác nhận Commit"
                                            >
                                                <CheckCircle className="w-4 h-4" />
                                            </button>
                                        )}
                                    </div>
                                </td>
                            </tr>
                        ))
                    )}
                </tbody>
            </table>
        </div>
    );
}
