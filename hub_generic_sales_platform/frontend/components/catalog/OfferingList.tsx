import { Search, Filter, Plus, Bot as BotIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import GlassContainer from "@/components/ui/GlassContainer";
import { TenantOffering } from "@/lib/apiService";

interface OfferingListProps {
    offerings: TenantOffering[];
    selectedOfferingId: string | null;
    onSelectOffering: (offering: TenantOffering) => void;
    isLoading: boolean;
    searchTerm: string;
    onSearchChange: (term: string) => void;
    filter: "all" | "active" | "draft" | "archived";
    onFilterChange: (filter: "all" | "active" | "draft" | "archived") => void;
    selectedChannel: string;
    onChannelChange: (channel: string) => void;
    onCreateOffering: () => void;
    hasSelectedBot: boolean;
    /** False khi chọn "Tất cả" - không thể tạo mới */
    canCreate?: boolean;
}

export default function OfferingList({
    offerings,
    selectedOfferingId,
    onSelectOffering,
    isLoading,
    searchTerm,
    onSearchChange,
    filter,
    onFilterChange,
    selectedChannel,
    onChannelChange,
    onCreateOffering,
    hasSelectedBot,
    canCreate = true
}: OfferingListProps) {
    // Filter logic is assumed to be done by parent or here. 
    // The parent passed "filteredOfferings" in the original code, but here we take raw or filtered?
    // Let's assume the parent does the heavy lifting of filtering to keep this pure, 
    // BUT the prompt implies this component handles the UI for filtering.
    // I'll take `offerings` as the *already filtered* list if possible, OR I filter here.
    // The original code filtered in the main page. Let's start with accepting the *display* list, 
    // but we also need the UI controls.

    // Actually, to make it cleaner, let's accept the `offerings` list that IS ALREADY FILTERED by the parent 
    // based on search/filter, OR we move that logic here. 
    // For now, I will assume `offerings` passed in ARE the ones to display, 
    // but I render the CONTROLS here.

    return (
        <GlassContainer className="col-span-1 md:col-span-4 p-4 md:p-6 flex flex-col bg-white/5 border-white/5 min-h-[400px] md:min-h-0">
            <div className="flex items-center justify-between mb-4">
                <h3 className="text-[10px] font-black text-white uppercase tracking-widest">Offerings</h3>
                <div className="relative">
                    <Search className="absolute left-2 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-500" />
                    <input
                        type="text"
                        value={searchTerm}
                        onChange={(e) => onSearchChange(e.target.value)}
                        placeholder="Search..."
                        className="bg-white/5 border border-white/10 rounded-lg py-1.5 pl-8 pr-3 text-[10px] focus:outline-none focus:border-accent/40 w-32 text-gray-300"
                    />
                </div>
            </div>

            {!hasSelectedBot ? (
                <div className="flex-1 flex flex-col items-center justify-center text-center p-8 bg-white/2 rounded-2xl border border-dashed border-white/5">
                    <BotIcon className="w-8 h-8 text-gray-600 mb-2 opacity-20" />
                    <p className="text-[10px] font-bold text-gray-600 uppercase tracking-widest">Select a bot first</p>
                </div>
            ) : (
                <>
                    {/* Controls */}
                    <div className="flex flex-col gap-3 mb-4">
                        <div className="flex gap-2">
                            <button
                                onClick={() => onFilterChange(filter === "all" ? "active" : filter === "active" ? "draft" : filter === "draft" ? "archived" : "all")}
                                className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-white/5 border border-white/10 rounded-xl text-[10px] font-bold text-gray-400 hover:bg-white/10 transition-all">
                                <Filter className="w-3 h-3" /> {filter === "all" ? "All Status" : filter === "active" ? "Active" : filter === "draft" ? "Draft" : "Archived"}
                            </button>
                            <select
                                value={selectedChannel}
                                onChange={(e) => onChannelChange(e.target.value)}
                                className="flex-1 bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-[10px] font-bold text-gray-400 focus:outline-none focus:border-accent/40 outline-none">
                                <option value="WEB">Web Channel</option>
                                <option value="ZALO">Zalo API</option>
                                <option value="FACEBOOK">Facebook Messenger</option>
                            </select>
                        </div>
                        <button
                            onClick={onCreateOffering}
                            disabled={!canCreate}
                            className="w-full flex items-center justify-center gap-2 px-4 py-2 premium-gradient rounded-xl text-[10px] font-bold text-white shadow-lg transition-transform active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed">
                            <Plus className="w-3.5 h-3.5" /> New Offering
                        </button>
                    </div>

                    <div className="flex-1 space-y-2 overflow-y-auto no-scrollbar">
                        {isLoading ? (
                            <div className="py-12 flex items-center justify-center">
                                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-accent"></div>
                            </div>
                        ) : offerings.length === 0 ? (
                            <div className="py-12 text-center text-xs text-gray-500 font-bold uppercase tracking-widest bg-white/5 rounded-2xl border border-white/5 italic">
                                No offerings found
                            </div>
                        ) : (
                            offerings.map((offering: any) => (
                                <div
                                    key={offering.id}
                                    onClick={() => onSelectOffering(offering)}
                                    className={cn(
                                        "p-4 bg-white/5 border rounded-2xl hover:border-accent/40 transition-all cursor-pointer group",
                                        selectedOfferingId === offering.id ? "border-accent/40 bg-accent/5" : "border-white/5"
                                    )}>
                                    <div className="flex items-center justify-between mb-2">
                                        <div className="flex flex-col">
                                            <span className="text-xs font-bold text-white group-hover:text-accent transition-colors">{offering.name}</span>
                                            <span className="text-[8px] text-gray-500 font-mono mt-0.5">{offering.code}</span>
                                        </div>
                                        <span className={cn(
                                            "text-[8px] px-1.5 py-0.5 rounded font-black uppercase",
                                            offering.status === "active" ? "bg-green-500/20 text-green-500" :
                                                offering.status === "draft" ? "bg-orange-500/20 text-orange-500" :
                                                    "bg-gray-500/20 text-gray-500"
                                        )}>{offering.status}</span>
                                    </div>
                                    <div className="flex items-center justify-between">
                                        <div className="text-[10px] text-gray-400 font-bold">
                                            v{offering.version}
                                        </div>
                                        <div className="text-[10px] font-black text-white">
                                            {offering.price ? `${offering.price.amount.toLocaleString()} ${offering.price.currency}` : "N/A"}
                                        </div>
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                </>
            )}
        </GlassContainer>
    );
}
