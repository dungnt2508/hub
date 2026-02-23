"use client";

import { Bot as BotIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import GlassContainer from "@/components/ui/GlassContainer";
import { Bot } from "@/lib/apiService";

interface MigrationInputFormProps {
    url: string;
    onUrlChange: (url: string) => void;
    bots: Bot[];
    selectedBotId: string | null;
    onSelectBot: (botId: string) => void;
    onStartScrape: () => void;
    isBotsLoading: boolean;
    isScraping: boolean;
    hasSelectedBot: boolean;
}

export default function MigrationInputForm({
    url,
    onUrlChange,
    bots,
    selectedBotId,
    onSelectBot,
    onStartScrape,
    isBotsLoading,
    isScraping,
    hasSelectedBot,
}: MigrationInputFormProps) {
    return (
        <GlassContainer className="p-6 bg-white/5 border-white/10">
            <h3 className="text-[10px] font-black text-white uppercase tracking-widest mb-4">Nguồn: Web Scraper (MVP)</h3>

            {/* URL Input - đặt trước để thấy ngay */}
            <div className="mb-6">
                <label className="text-xs font-bold text-accent uppercase tracking-wider block mb-2">
                    Nhập URL trang sản phẩm
                </label>
                <div className="flex flex-col sm:flex-row gap-3">
                    <input
                        type="url"
                        value={url}
                        onChange={(e) => onUrlChange(e.target.value)}
                        placeholder="https://tiki.vn/... hoặc https://shopee.vn/..."
                        className="flex-1 w-full bg-white/15 border-2 border-white/25 rounded-xl p-4 text-base text-white placeholder:text-gray-400 focus:outline-none focus:border-accent focus:ring-2 focus:ring-accent/40 min-w-0"
                    />
                    <button
                        onClick={onStartScrape}
                        disabled={!hasSelectedBot || !url.trim() || isScraping}
                        className="px-6 py-3 premium-gradient rounded-xl text-sm font-bold text-white disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap h-[52px]"
                    >
                        {isScraping ? "Đang cào..." : "Bắt đầu cào"}
                    </button>
                </div>
            </div>

            {/* Bot Selector */}
            <div>
                <label className="text-[10px] font-bold text-gray-500 uppercase tracking-wider block mb-2">Chọn Bot (bắt buộc)</label>
                <div className="flex gap-2 overflow-x-auto no-scrollbar py-1">
                    {isBotsLoading ? (
                        <div className="py-2"><div className="animate-spin rounded-full h-4 w-4 border-b-2 border-accent"></div></div>
                    ) : bots.map((bot: Bot) => (
                        <button
                            key={bot.id}
                            onClick={() => onSelectBot(bot.id)}
                            className={cn(
                                "min-w-[120px] p-3 rounded-2xl flex items-center gap-3 group transition-all text-left",
                                selectedBotId === bot.id ? "bg-accent/10 border border-accent/30 text-accent" : "bg-white/5 border border-white/5 hover:bg-white/10"
                            )}
                        >
                            <div className={cn("p-1.5 rounded-xl flex-shrink-0", selectedBotId === bot.id ? "bg-accent/20 text-accent" : "bg-white/5 text-gray-500")}>
                                <BotIcon className="w-3.5 h-3.5" />
                            </div>
                            <div className="flex-1 min-w-0">
                                <div className={cn("text-[10px] font-bold truncate", selectedBotId === bot.id ? "text-white" : "text-gray-400")}>{bot.name}</div>
                                <div className="text-[7px] font-mono text-gray-600 uppercase mt-0.5 truncate">{bot.code}</div>
                            </div>
                        </button>
                    ))}
                </div>
            </div>
        </GlassContainer>
    );
}
