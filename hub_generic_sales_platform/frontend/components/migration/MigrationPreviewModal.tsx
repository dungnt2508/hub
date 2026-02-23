"use client";

import { XCircle } from "lucide-react";
import GlassContainer from "@/components/ui/GlassContainer";
import { MigrationJob } from "@/lib/apiService";

interface StagedVariant {
    sku?: string;
    name?: string;
    price?: number;
    inventory?: number;
}

interface StagedOffering {
    code?: string;
    name?: string;
    description?: string;
    attributes?: Record<string, string>;
    price?: number;
    inventory?: number;
    variants?: StagedVariant[];
}

interface MigrationPreviewModalProps {
    job: MigrationJob | null;
    onClose: () => void;
    onConfirm: (job: MigrationJob) => void;
    isConfirming: boolean;
}

function formatPrice(v: number | undefined): string {
    if (v == null || Number.isNaN(v)) return "-";
    return v.toLocaleString("vi-VN") + " VND";
}

function getOfferingPrice(o: StagedOffering): string {
    if (o.price != null && !Number.isNaN(o.price)) return formatPrice(o.price);
    const vs = o.variants || [];
    if (vs.length === 0) return "-";
    const prices = vs.map((v) => v.price).filter((p): p is number => p != null && !Number.isNaN(p));
    if (prices.length === 0) return "-";
    const min = Math.min(...prices);
    const max = Math.max(...prices);
    return min === max ? formatPrice(min) : `${formatPrice(min)} – ${formatPrice(max)}`;
}

function getOfferingInventory(o: StagedOffering): string {
    if (o.inventory != null && !Number.isNaN(o.inventory)) return String(o.inventory);
    const vs = o.variants || [];
    const hasInv = vs.some((v) => v.inventory != null && !Number.isNaN(v.inventory));
    if (!hasInv) return "-";
    const total = vs.reduce((s, v) => s + (v.inventory ?? 0), 0);
    return String(total);
}

export default function MigrationPreviewModal({
    job,
    onClose,
    onConfirm,
    isConfirming,
}: MigrationPreviewModalProps) {
    if (!job) return null;

    // Thống nhất: staged_data dùng "offerings" (fallback products cho job cũ đã cache)
    const offerings: StagedOffering[] = job.staged_data?.offerings ?? job.staged_data?.products ?? [];
    const hasError = job.status === "failed" && job.error_log;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
            <GlassContainer className="w-full max-w-4xl max-h-[90vh] p-8 bg-[#0A0A0A] border-white/10 shadow-2xl overflow-hidden flex flex-col">
                <div className="flex items-center justify-between mb-6 flex-shrink-0">
                    <h3 className="text-xl font-black text-white">Preview: {job.id.slice(0, 8)}...</h3>
                    <button onClick={onClose} className="text-gray-500 hover:text-white transition-colors">
                        <XCircle className="w-6 h-6" />
                    </button>
                </div>

                {hasError && (
                    <div className="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-xl text-red-400 text-sm">
                        <div className="font-bold mb-1">Lỗi</div>
                        <pre className="text-xs whitespace-pre-wrap overflow-auto max-h-32">{job.error_log}</pre>
                    </div>
                )}

                {offerings.length === 0 && !hasError && (
                    <div className="py-12 text-center text-gray-500 italic">Chưa có dữ liệu staged</div>
                )}

                {offerings.length > 0 && (
                    <div className="flex-1 overflow-auto pr-2 custom-scrollbar mb-6">
                        <table className="w-full text-left border-collapse">
                            <thead>
                                <tr className="border-b border-white/10">
                                    <th className="pb-2 pr-3 text-[10px] font-black text-gray-500 uppercase tracking-widest">Code</th>
                                    <th className="pb-2 pr-3 text-[10px] font-black text-gray-500 uppercase tracking-widest">Tên</th>
                                    <th className="pb-2 pr-3 text-[10px] font-black text-gray-500 uppercase tracking-widest">Mô tả</th>
                                    <th className="pb-2 pr-3 text-[10px] font-black text-gray-500 uppercase tracking-widest">Variants</th>
                                    <th className="pb-2 pr-3 text-[10px] font-black text-gray-500 uppercase tracking-widest">Price</th>
                                    <th className="pb-2 pr-3 text-[10px] font-black text-gray-500 uppercase tracking-widest">Inventory</th>
                                </tr>
                            </thead>
                            <tbody>
                                {offerings.map((o, idx) => (
                                    <tr key={idx} className="border-b border-white/5">
                                        <td className="py-3 pr-3 text-xs font-mono text-accent">{o.code || "-"}</td>
                                        <td className="py-3 pr-3 text-xs text-white">{o.name || "-"}</td>
                                        <td className="py-3 pr-3 text-xs text-gray-400 max-w-[220px]">
                                            <span className="line-clamp-2" title={o.description || undefined}>
                                                {o.description || "-"}
                                            </span>
                                        </td>
                                        <td className="py-3 pr-3">
                                            {o.variants?.length ? (
                                                <div className="space-y-1 max-w-[180px]">
                                                    {o.variants.map((v, vIdx) => (
                                                        <div key={vIdx} className="text-[10px] text-gray-400">
                                                            {v.sku || "-"}: {v.name || "-"}
                                                            {v.price != null && ` — ${formatPrice(v.price)}`}
                                                            {v.inventory != null && ` (SL: ${v.inventory})`}
                                                        </div>
                                                    ))}
                                                </div>
                                            ) : (
                                                <span className="text-gray-500">-</span>
                                            )}
                                        </td>
                                        <td className="py-3 pr-3 text-xs text-accent font-mono">{getOfferingPrice(o)}</td>
                                        <td className="py-3 pr-3 text-xs text-gray-400">{getOfferingInventory(o)}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}

                {job.status === "staged" && offerings.length > 0 && (
                    <div className="flex gap-3 flex-shrink-0">
                        <button
                            onClick={onClose}
                            className="flex-1 py-3 rounded-xl text-gray-400 hover:text-white border border-white/10"
                        >
                            Đóng
                        </button>
                        <button
                            onClick={() => onConfirm(job)}
                            disabled={isConfirming}
                            className="flex-1 py-3 premium-gradient rounded-xl text-sm font-bold text-white disabled:opacity-50"
                        >
                            {isConfirming ? "Đang commit..." : "Xác nhận Commit vào Catalog"}
                        </button>
                    </div>
                )}
            </GlassContainer>
        </div>
    );
}
