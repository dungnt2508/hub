import { Package } from "lucide-react";
import { cn } from "@/lib/utils";

interface StatsProps {
    stats: {
        total: number;
        active: number;
        draft: number;
        archived: number;
    };
}

export default function CatalogStats({ stats }: StatsProps) {
    return (
        <div className="grid grid-cols-4 gap-3 mb-4">
            <div className="p-3 bg-white/5 rounded-2xl border border-white/5 flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-accent/20 flex items-center justify-center text-accent">
                    <Package className="w-4 h-4" />
                </div>
                <div>
                    <div className="text-lg font-black text-white leading-none">{stats.total}</div>
                    <div className="text-[8px] font-bold text-gray-500 uppercase tracking-widest mt-1">Total</div>
                </div>
            </div>
            <div className="p-3 bg-white/5 rounded-2xl border border-white/5 flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-green-500/20 flex items-center justify-center text-green-500">
                    <Package className="w-4 h-4" />
                </div>
                <div>
                    <div className="text-lg font-black text-white leading-none">{stats.active}</div>
                    <div className="text-[8px] font-bold text-gray-500 uppercase tracking-widest mt-1">Active</div>
                </div>
            </div>
            <div className="p-3 bg-white/5 rounded-2xl border border-white/5 flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-orange-500/20 flex items-center justify-center text-orange-500">
                    <Package className="w-4 h-4" />
                </div>
                <div>
                    <div className="text-lg font-black text-white leading-none">{stats.draft}</div>
                    <div className="text-[8px] font-bold text-gray-500 uppercase tracking-widest mt-1">Draft</div>
                </div>
            </div>
            <div className="p-3 bg-white/5 rounded-2xl border border-white/5 flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-gray-500/20 flex items-center justify-center text-gray-500">
                    <Package className="w-4 h-4" />
                </div>
                <div>
                    <div className="text-lg font-black text-white leading-none">{stats.archived}</div>
                    <div className="text-[8px] font-bold text-gray-500 uppercase tracking-widest mt-1">Archived</div>
                </div>
            </div>
        </div>
    );
}
