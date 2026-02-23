"use client";

import ChatWidget from "@/components/chat/ChatWidget";
import DecisionVisualizer from "@/components/admin/DecisionVisualizer";
import GlassContainer from "@/components/ui/GlassContainer";
import { Sparkles, MessageSquare, Activity, Search, Loader2, Send, Bot as BotIcon } from "lucide-react";
import { useState, useCallback } from "react";
import { Message } from "@/components/chat/ChatMessage";
import { cn } from "@/lib/utils";
import { apiService, Bot, SessionLogEntry } from "@/lib/apiService";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useUIStore } from "@/lib/store";
import { StateBadge } from "@/components/StateBadge";

function turnsToMessages(turns: { role: string; content: string; metadata?: any }[]): Message[] {
    return (turns || []).map((t) => ({
        role: t.role as "user" | "assistant" | "system",
        content: t.content,
        metadata: t.metadata,
    }));
}

export default function MonitorPage() {
    const queryClient = useQueryClient();
    const tenantId = useUIStore((s) => s.currentTenantId) || "";
    const [input, setInput] = useState("");
    const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
    const [filterBotId, setFilterBotId] = useState<string>("");
    const [filterChannel, setFilterChannel] = useState<string>("");
    const [filterState, setFilterState] = useState<string>("");

    const { data: sessions = [], isLoading: isSessionsLoading, refetch: refetchSessions } = useQuery({
        queryKey: ["sessions", "monitor", filterBotId, filterChannel],
        queryFn: () =>
            apiService.listSessions({
                active_only: true,
                bot_id: filterBotId || undefined,
                channel_code: filterChannel || undefined,
                limit: 100,
            }),
        refetchInterval: 10000,
    });

    const filteredSessions = sessions.filter(s =>
        !filterState || (s.lifecycle_state || "").toLowerCase() === filterState.toLowerCase()
    );

    const selectedSession = sessions.find((s) => s.id === selectedSessionId);

    const { data: turnsData, isLoading: isTurnsLoading, refetch: refetchTurns } = useQuery({
        queryKey: ["session-turns", selectedSessionId],
        queryFn: () => (selectedSessionId ? apiService.getSessionTurns(selectedSessionId) : null),
        enabled: !!selectedSessionId,
    });

    const { data: sessionStats } = useQuery({
        queryKey: ["sessionStats", selectedSessionId],
        queryFn: () => (selectedSessionId ? apiService.getSessionStats(selectedSessionId) : null),
        enabled: !!selectedSessionId,
    });

    const { data: bots = [] } = useQuery({
        queryKey: ["bots", "active"],
        queryFn: () => apiService.listBots({ status: "active" }),
    });

    const sendMutation = useMutation({
        mutationFn: async (text: string) => {
            if (!selectedSessionId || !selectedSession) throw new Error("No session");
            return apiService.sendMessage(tenantId, selectedSession.bot_id, text, selectedSessionId);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["session-turns", selectedSessionId] });
            queryClient.invalidateQueries({ queryKey: ["sessions", "monitor"] });
        },
    });

    const handoverMutation = useMutation({
        mutationFn: () => (selectedSessionId ? apiService.handoverSession(selectedSessionId) : Promise.reject(new Error("No session"))),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["sessions", "monitor"] });
            queryClient.invalidateQueries({ queryKey: ["session-turns", selectedSessionId] });
        },
    });

    const messages: Message[] = turnsToMessages(turnsData?.turns || []);

    const handleSend = useCallback(() => {
        if (!input.trim() || !selectedSessionId) return;
        const text = input.trim();
        setInput("");
        sendMutation.mutate(text);
    }, [input, selectedSessionId, sendMutation]);

    const channels = [...new Set(sessions.map((s) => s.channel_code))].filter(Boolean).sort();

    return (
        <div className="h-full flex flex-col gap-6">
            <GlassContainer className="w-full p-4 flex flex-col bg-white/5 border-white/5">
                <div className="flex items-center gap-4">
                    <h3 className="text-[10px] font-black text-white uppercase tracking-widest border-r border-white/10 pr-4 py-1 hidden md:block">
                        Live Monitor
                    </h3>
                    <div className="flex-1 flex gap-2 flex-wrap">
                        <select
                            value={filterBotId}
                            onChange={(e) => setFilterBotId(e.target.value)}
                            className="bg-white/5 border border-white/10 rounded-xl px-4 py-2 text-xs text-gray-300 focus:outline-none focus:border-accent"
                        >
                            <option value="">Tất cả Bot</option>
                            {bots.map((b: Bot) => (
                                <option key={b.id} value={b.id}>{b.name}</option>
                            ))}
                        </select>
                        <select
                            value={filterChannel}
                            onChange={(e) => setFilterChannel(e.target.value)}
                            className="bg-white/5 border border-white/10 rounded-xl px-4 py-2 text-xs text-gray-300 focus:outline-none focus:border-accent"
                        >
                            <option value="">Tất cả kênh</option>
                            {channels.map((ch) => (
                                <option key={ch} value={ch}>{ch}</option>
                            ))}
                        </select>
                        <select
                            value={filterState}
                            onChange={(e) => setFilterState(e.target.value)}
                            className="bg-white/5 border border-white/10 rounded-xl px-4 py-2 text-xs text-gray-300 focus:outline-none focus:border-accent"
                        >
                            <option value="">Tất cả trạng thái</option>
                            <option value="idle">IDLE</option>
                            <option value="searching">SEARCHING</option>
                            <option value="filtering">FILTERING</option>
                            <option value="viewing">VIEWING</option>
                            <option value="comparing">COMPARING</option>
                            <option value="purchasing">PURCHASING</option>
                            <option value="handover">HANDOVER</option>
                            <option value="completed">COMPLETED</option>
                            <option value="closed">CLOSED</option>
                        </select>
                    </div>
                </div>
            </GlassContainer>

            <div className="flex-1 flex gap-6 min-h-0">
                {/* Session Sidebar */}
                <GlassContainer className="w-80 p-6 flex flex-col bg-white/5 border-white/5">
                    <div className="flex items-center justify-between mb-6">
                        <h3 className="text-sm font-bold text-white flex items-center gap-2">
                            <MessageSquare className="w-4 h-4 text-accent" /> Phiên đang hoạt động
                        </h3>
                        <Search className="w-4 h-4 text-gray-400" />
                    </div>

                    <div className="flex-1 space-y-3 overflow-y-auto no-scrollbar">
                        {isSessionsLoading ? (
                            <div className="py-12 flex justify-center">
                                <Loader2 className="w-6 h-6 animate-spin text-accent" />
                            </div>
                        ) : sessions.length === 0 ? (
                            <div className="py-12 text-center text-xs text-gray-500 italic">
                                Không có phiên nào đang hoạt động
                            </div>
                        ) : (
                            filteredSessions.map((s: SessionLogEntry) => (
                                <div
                                    key={s.id}
                                    onClick={() => setSelectedSessionId(s.id)}
                                    className={cn(
                                        "p-4 rounded-2xl border cursor-pointer transition-all duration-300",
                                        selectedSessionId === s.id
                                            ? "bg-accent/10 border-accent/30 text-white"
                                            : "bg-white/5 border-white/5 text-gray-400 hover:bg-white/10"
                                    )}
                                >
                                    <div className="flex items-center justify-between mb-1">
                                        <span className="text-[10px] font-mono text-gray-500 truncate max-w-[120px]">
                                            {s.id.slice(0, 8)}...
                                        </span>
                                        <StateBadge state={s.lifecycle_state || "idle"} />
                                    </div>
                                    <div className="text-[10px] text-gray-400 flex gap-2">
                                        <span>{s.channel_code}</span>
                                        <span>•</span>
                                        <span>{bots.find((b) => b.id === s.bot_id)?.name || s.bot_id?.slice(0, 8)}</span>
                                    </div>
                                    <div className="text-[8px] mt-2 text-gray-500">
                                        {s.created_at ? new Date(s.created_at).toLocaleString() : "—"}
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                </GlassContainer>

                {/* Main Monitor Window */}
                <GlassContainer className="flex-1 flex flex-col relative overflow-hidden bg-white/5 border-white/5">
                    <div className="h-20 border-b border-white/5 flex items-center justify-between px-6">
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-full glass-effect flex items-center justify-center text-accent">
                                <Activity className="w-5 h-5 animate-pulse" />
                            </div>
                            <div>
                                <div className="flex items-center gap-2">
                                    <h2 className="text-sm font-bold text-white">
                                        {selectedSessionId
                                            ? `Session: ${selectedSessionId.slice(0, 12)}...`
                                            : "Chọn phiên để xem"}
                                    </h2>
                                    {selectedSession && (
                                        <StateBadge state={selectedSession.lifecycle_state || "idle"} />
                                    )}
                                </div>
                                <p className="text-[10px] text-gray-500 font-bold uppercase tracking-widest">
                                    {selectedSession?.channel_code || "—"}
                                </p>
                            </div>
                        </div>
                        <button
                            onClick={() => selectedSessionId && handoverMutation.mutate()}
                            disabled={!selectedSessionId || handoverMutation.isPending || selectedSession?.lifecycle_state === "handover"}
                            className="px-4 py-2 bg-red-500/10 hover:bg-red-500/20 text-red-500 text-[10px] font-bold uppercase tracking-widest rounded-xl transition-all disabled:opacity-50"
                            title={selectedSession?.lifecycle_state === "handover" ? "Đã tiếp quản" : "Tiếp quản (chuyển sang nhân viên hỗ trợ)"}
                        >
                            {handoverMutation.isPending ? "..." : selectedSession?.lifecycle_state === "handover" ? "Đã tiếp quản" : "Take Over"}
                        </button>
                    </div>

                    <ChatWidget
                        messages={
                            isTurnsLoading
                                ? []
                                : messages.length === 0 && selectedSessionId
                                    ? [{ role: "assistant" as const, content: "Đang tải lịch sử hội thoại...", metadata: {} }]
                                    : messages
                        }
                    />

                    <div className="p-6 bg-white/5 border-t border-white/5">
                        <div className="relative flex items-center">
                            <input
                                type="text"
                                placeholder={
                                    selectedSessionId
                                        ? "Nhập tin nhắn để tương tác..."
                                        : "Chọn phiên để gửi tin"
                                }
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                onKeyDown={(e) => e.key === "Enter" && handleSend()}
                                disabled={!selectedSessionId || sendMutation.isPending}
                                className="w-full bg-white/5 border border-white/10 rounded-2xl py-4 pl-6 pr-24 focus:outline-none focus:border-accent/50 transition-all text-gray-200 placeholder:text-gray-500 disabled:opacity-50"
                            />
                            <div className="absolute right-4 flex items-center gap-3">
                                <button
                                    onClick={handleSend}
                                    disabled={!selectedSessionId || !input.trim() || sendMutation.isPending}
                                    className="premium-gradient p-2 rounded-xl shadow-lg hover:brightness-110 active:scale-95 transition-all disabled:opacity-50"
                                >
                                    {sendMutation.isPending ? (
                                        <Loader2 className="text-white w-6 h-6 animate-spin" />
                                    ) : (
                                        <Send className="text-white w-6 h-6" />
                                    )}
                                </button>
                            </div>
                        </div>
                    </div>
                </GlassContainer>

                {/* Decision Pane */}
                <GlassContainer className="w-[400px] p-8 flex flex-col bg-white/5 border-white/5">
                    <div className="flex items-center justify-between mb-8">
                        <h3 className="text-xs font-black text-gray-400 uppercase tracking-[0.2em]">Decision Tracing</h3>
                        <Sparkles className="w-4 h-4 text-accent animate-spin-slow" />
                    </div>
                    <div className="flex-1 overflow-y-auto pr-2 no-scrollbar">
                        <DecisionVisualizer
                            steps={
                                sessionStats?.timeline?.map((t) => ({
                                    tier: t.tier,
                                    type: t.type,
                                    reason: t.reason,
                                    status: "success" as const,
                                    latency: t.latency,
                                })) || []
                            }
                        />
                    </div>
                </GlassContainer>
            </div>
        </div>
    );
}
