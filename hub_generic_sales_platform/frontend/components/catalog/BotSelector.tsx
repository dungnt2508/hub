import { Bot as BotIcon, LayoutGrid } from "lucide-react";
import { cn } from "@/lib/utils";
import GlassContainer from "@/components/ui/GlassContainer";
import { Bot } from "@/lib/apiService";

/** "ALL" = hiển thị tất cả sản phẩm không filter theo domain (bao gồm từ Migration) */
export const BOT_ID_ALL = "ALL";

interface BotSelectorProps {
    bots: Bot[];
    selectedBotId: string | null;
    onSelectBot: (botId: string) => void;
    isLoading: boolean;
    /** Cho phép chọn "Tất cả" để xem sản phẩm từ mọi domain (kể cả Migration) */
    showAllOption?: boolean;
}

export default function BotSelector({ bots, selectedBotId, onSelectBot, isLoading, showAllOption }: BotSelectorProps) {
    return (
        <GlassContainer className="w-full p-2 flex items-center gap-4 bg-white/5 border-white/5 mb-4">
            <h3 className="text-[10px] font-black text-white uppercase tracking-widest border-r border-white/10 pr-4 py-1 hidden md:block whitespace-nowrap">
                Active Bot
            </h3>

            <div className="flex-1 flex gap-2 overflow-x-auto no-scrollbar py-1">
                {showAllOption && (
                    <button
                        onClick={() => onSelectBot(BOT_ID_ALL)}
                        className={cn(
                            "flex items-center gap-2 px-3 py-1.5 rounded-xl transition-all border text-left min-w-[100px]",
                            selectedBotId === BOT_ID_ALL
                                ? "bg-accent/10 border-accent/30"
                                : "bg-white/5 border-white/5 hover:bg-white/10"
                        )}
                    >
                        <div className={cn(
                            "w-6 h-6 rounded-lg flex items-center justify-center flex-shrink-0",
                            selectedBotId === BOT_ID_ALL ? "bg-accent/20 text-accent" : "bg-white/5 text-gray-500"
                        )}>
                            <LayoutGrid className="w-3.5 h-3.5" />
                        </div>
                        <div className="text-[10px] font-bold text-gray-400">Tất cả</div>
                    </button>
                )}
                {isLoading ? (
                    <div className="py-2 flex justify-center w-full">
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-accent"></div>
                    </div>
                ) : (
                    bots.map((bot) => (
                        <button
                            key={bot.id}
                            onClick={() => onSelectBot(bot.id)}
                            className={cn(
                                "flex items-center gap-2 px-3 py-1.5 rounded-xl transition-all border text-left min-w-[120px]",
                                selectedBotId === bot.id
                                    ? "bg-accent/10 border-accent/30"
                                    : "bg-white/5 border-white/5 hover:bg-white/10"
                            )}
                        >
                            <div className={cn(
                                "w-6 h-6 rounded-lg flex items-center justify-center flex-shrink-0",
                                selectedBotId === bot.id ? "bg-accent/20 text-accent" : "bg-white/5 text-gray-500"
                            )}>
                                <BotIcon className="w-3.5 h-3.5" />
                            </div>
                            <div className="flex-1 min-w-0">
                                <div className={cn(
                                    "text-[10px] font-bold truncate",
                                    selectedBotId === bot.id ? "text-white" : "text-gray-400"
                                )}>
                                    {bot.name}
                                </div>
                            </div>
                        </button>
                    ))
                )}
            </div>
        </GlassContainer>
    );
}
