"use client";

import GlassContainer from "@/components/ui/GlassContainer";
import { RefreshCw, Send, RotateCcw, Copy, ChevronDown, ChevronUp } from "lucide-react";
import { useState, useRef, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiService, SessionStats } from "@/lib/apiService";
import ChatWidget from "@/components/chat/ChatWidget";
import { Message } from "@/components/chat/ChatMessage";
import { cn } from "@/lib/utils";
import DecisionVisualizer from "@/components/admin/DecisionVisualizer";
import { StateBadge } from "@/components/StateBadge";

export default function StudioPage() {
    // State
    const [selectedBotId, setSelectedBotId] = useState<string>("");
    const [sessionId, setSessionId] = useState<string>("");
    const [messages, setMessages] = useState<Message[]>([]);
    const [inputValue, setInputValue] = useState("");
    const [isTyping, setIsTyping] = useState(false);
    const [debugPanelOpen, setDebugPanelOpen] = useState(true);
    const [resumeSessionIdInput, setResumeSessionIdInput] = useState("");
    const [scenarioPlaying, setScenarioPlaying] = useState(false);

    const SCENARIO_PRESETS = [
        { id: "retail", label: "Retail: Browse & Compare", messages: ["Cho tôi xem laptop", "Cái thứ 2 giá bao nhiêu?", "So sánh cái 1 và 2"] },
        { id: "finance", label: "Finance: Loan Query", messages: ["Tôi muốn vay 500 triệu", "Lãi suất bao nhiêu?"] },
        { id: "auto", label: "Auto: Trade-in", messages: ["Định giá xe cũ Toyota Vios 2020", "Giá thị trường hiện tại?"] },
    ];

    const queryClient = useQueryClient();

    // Session stats (debug)
    const { data: sessionStats } = useQuery({
        queryKey: ["session-stats", sessionId],
        queryFn: () => apiService.getSessionStats(sessionId),
        enabled: !!sessionId,
    });
    const { data: sessionState } = useQuery({
        queryKey: ["session-state", sessionId],
        queryFn: () => apiService.getSessionState(sessionId),
        enabled: !!sessionId,
    });

    // Fetch Bots
    const { data: bots = [], isLoading: isLoadingBots } = useQuery({
        queryKey: ["bots"],
        queryFn: () => apiService.listBots({ status: "active" }),
    });

    // Select first bot by default
    useEffect(() => {
        if (bots.length > 0 && !selectedBotId) {
            setSelectedBotId(bots[0].id);
        }
    }, [bots, selectedBotId]);

    // Send Message Mutation
    const sendMessageMutation = useMutation({
        mutationFn: async ({ botId, text, currentSessionId }: { botId: string, text: string, currentSessionId?: string }) => {
            // Studio: debug=true for lifecycle_state in response
            return apiService.sendMessage("", botId, text, currentSessionId, { debug: true });
        },
        onSuccess: (data) => {
            setSessionId(data.session_id);
            // Stats query auto-refetches when sessionId updates (queryKey changes)
            const assistantMsg: Message = {
                role: "assistant",
                content: data.response,
                metadata: data.metadata
            };
            setMessages(prev => [...prev, assistantMsg]);
            setIsTyping(false);
        },
        onError: (error) => {
            console.error("Chat error:", error);
            const errorMsg: Message = {
                role: "assistant",
                content: "⚠️ **Error:** Failed to connect to the bot. Please check your connection or try again."
            };
            setMessages(prev => [...prev, errorMsg]);
            setIsTyping(false);
        }
    });

    const handleSendMessage = (e?: React.FormEvent) => {
        e?.preventDefault();
        if (!inputValue.trim() || !selectedBotId) return;

        const userText = inputValue;
        setInputValue("");
        setIsTyping(true);

        // Add User Message
        const userMsg: Message = { role: "user", content: userText };
        setMessages(prev => [...prev, userMsg]);

        // Trigger API
        sendMessageMutation.mutate({
            botId: selectedBotId,
            text: userText,
            currentSessionId: sessionId || undefined
        });
    };

    const handleResetSession = () => {
        setSessionId("");
        setMessages([]);
        setInputValue("");
    };

    const selectedBot = bots.find(b => b.id === selectedBotId);

    const decisionSteps = sessionStats?.timeline?.map((t) => ({
        tier: t.tier,
        type: t.type,
        reason: t.reason,
        status: "success" as const,
        latency: t.latency,
    })) ?? [];

    const copySessionId = () => {
        if (sessionId) {
            navigator.clipboard.writeText(sessionId);
        }
    };

    const resumeSessionMutation = useMutation({
        mutationFn: (sid: string) => apiService.getSessionTurns(sid),
        onSuccess: (data) => {
            setSessionId(data.session_id);
            setMessages(data.turns.map((t) => ({
                role: t.role as "user" | "assistant",
                content: t.content,
                metadata: t.role === "assistant" && t.metadata ? { g_ui: t.metadata } : undefined,
            })));
            setResumeSessionIdInput("");
        },
    });
    const handleResumeSession = () => {
        const sid = resumeSessionIdInput.trim();
        if (sid) resumeSessionMutation.mutate(sid);
    };

    const runScenario = async (messages: string[]) => {
        if (!selectedBotId || scenarioPlaying) return;
        setScenarioPlaying(true);
        handleResetSession();  // Start fresh
        let currentSid = "";
        for (const msg of messages) {
            try {
                const data = await apiService.sendMessage("", selectedBotId, msg, currentSid || undefined, { debug: true });
                currentSid = data.session_id;
                setSessionId(data.session_id);
                setMessages((prev) => [
                    ...prev,
                    { role: "user" as const, content: msg },
                    { role: "assistant" as const, content: data.response, metadata: data.metadata },
                ]);
            } catch {
                break;
            }
        }
        if (currentSid) {
            queryClient.invalidateQueries({ queryKey: ["session-stats", currentSid] });
        }
        setScenarioPlaying(false);
    };

    return (
        <div className="h-full flex flex-col space-y-4">
            {/* Header */}
            <div className="flex items-center justify-between shrink-0">
                <div className="flex flex-col">
                    <h1 className="text-2xl font-black text-white">AI Sandbox</h1>
                    <p className="text-xs text-secondary font-bold uppercase tracking-[0.2em] mt-1">
                        Test & Debug Agent Flows
                    </p>
                </div>
            </div>

            <div className="flex-1 grid grid-cols-12 gap-6 min-h-0">
                {/* Configuration Panel (Left) */}
                <GlassContainer className="col-span-3 p-4 flex flex-col bg-white/5 border-white/5 space-y-6">
                    <div>
                        <label className="text-[10px] font-black text-gray-400 uppercase tracking-widest block mb-2">
                            Select Bot
                        </label>
                        {isLoadingBots ? (
                            <div className="h-10 w-full bg-white/5 animate-pulse rounded-xl"></div>
                        ) : (
                            <select
                                value={selectedBotId}
                                onChange={(e) => {
                                    setSelectedBotId(e.target.value);
                                    handleResetSession();
                                }}
                                className="w-full bg-white/5 border border-white/10 rounded-xl py-2 px-3 text-xs font-bold text-white focus:outline-none focus:border-accent/50"
                            >
                                {bots.map(bot => (
                                    <option key={bot.id} value={bot.id}>
                                        {bot.name} ({bot.code})
                                    </option>
                                ))}
                            </select>
                        )}
                    </div>

                    {selectedBot && (
                        <div className="p-4 bg-white/5 rounded-xl border border-white/5 space-y-3">
                            <div className="flex items-center gap-2">
                                <span className={cn(
                                    "w-2 h-2 rounded-full",
                                    selectedBot.status === "active" ? "bg-green-500" : "bg-gray-500"
                                )}></span>
                                <span className="text-xs font-bold text-gray-200">
                                    {selectedBot.status === "active" ? "Active" : "Archived"}
                                </span>
                            </div>
                            <div className="space-y-1">
                                <div className="text-[9px] font-bold text-gray-500 uppercase">Domain</div>
                                <div className="text-xs text-gray-300">{selectedBot.domain?.name || "Global"}</div>
                            </div>
                            <div className="space-y-1">
                                <div className="text-[9px] font-bold text-gray-500 uppercase">Capabilities</div>
                                <div className="flex flex-wrap gap-1">
                                    {selectedBot.capabilities?.map((cap, i) => (
                                        <span key={i} className="px-1.5 py-0.5 bg-accent/10 rounded text-[9px] font-bold text-accent">
                                            {cap}
                                        </span>
                                    )) || <span className="text-[9px] text-gray-500 italic">None</span>}
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Debug: Session Stats */}
                    {sessionId && sessionStats && (
                        <div className="p-3 bg-white/5 rounded-xl border border-white/5 space-y-2">
                            <div className="text-[9px] font-bold text-gray-500 uppercase">Session Stats</div>
                            <div className="text-xs text-gray-300 space-y-1">
                                <div>Turns: {sessionStats.summary.total_turns}</div>
                                <div>Cost: {sessionStats.summary.total_cost}</div>
                                <div>Avg latency: {sessionStats.summary.avg_latency_ms}ms</div>
                            </div>
                        </div>
                    )}
                    {/* Debug: State & Slots */}
                    {sessionId && sessionState && (
                        <div className="p-3 bg-white/5 rounded-xl border border-white/5 space-y-2">
                            <div className="text-xs">
                                <StateBadge state={sessionState.lifecycle_state} />
                            </div>
                            {sessionState.slots?.length > 0 && (
                                <div className="space-y-1">
                                    <div className="text-[9px] font-bold text-gray-500 uppercase">Slots</div>
                                    <div className="text-[10px] text-gray-400 space-y-0.5">
                                        {sessionState.slots.map((s, i) => (
                                            <div key={i} className="flex gap-2">
                                                <span className="text-accent">{s.key}:</span>
                                                <span>{s.value}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    )}

                    {/* Scenario Presets */}
                    <div className="space-y-2">
                        <div className="text-[9px] font-bold text-gray-500 uppercase">Quick Scenarios</div>
                        <select
                            onChange={(e) => {
                                const preset = SCENARIO_PRESETS.find((p) => p.id === e.target.value);
                                if (preset) runScenario(preset.messages);
                                e.target.value = "";
                            }}
                            disabled={!selectedBotId || scenarioPlaying}
                            className="w-full bg-black/20 border border-white/10 rounded-lg px-2 py-1.5 text-[10px] text-white"
                        >
                            <option value="">Run scenario...</option>
                            {SCENARIO_PRESETS.map((p) => (
                                <option key={p.id} value={p.id}>{p.label}</option>
                            ))}
                        </select>
                    </div>

                    {/* Resume Session */}
                    <div className="space-y-2">
                        <div className="text-[9px] font-bold text-gray-500 uppercase">Resume Session</div>
                        <div className="flex gap-2">
                            <input
                                type="text"
                                value={resumeSessionIdInput}
                                onChange={(e) => setResumeSessionIdInput(e.target.value)}
                                placeholder="Paste session ID..."
                                className="flex-1 bg-black/20 border border-white/10 rounded-lg px-2 py-1.5 text-[10px] text-white placeholder:text-gray-600"
                            />
                            <button
                                onClick={handleResumeSession}
                                disabled={!resumeSessionIdInput.trim() || resumeSessionMutation.isPending}
                                className="px-2 py-1.5 bg-accent/20 hover:bg-accent/30 border border-accent/30 rounded-lg text-[10px] font-bold text-accent disabled:opacity-50"
                            >
                                {resumeSessionMutation.isPending ? "..." : "Load"}
                            </button>
                        </div>
                    </div>

                    <div className="mt-auto space-y-2">
                        {sessionId && (
                            <button
                                onClick={copySessionId}
                                className="w-full flex items-center justify-center gap-2 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl text-xs font-bold text-gray-300 transition-all">
                                <Copy className="w-3.5 h-3.5" />
                                Copy Session ID
                            </button>
                        )}
                        <button
                            onClick={handleResetSession}
                            className="w-full flex items-center justify-center gap-2 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl text-xs font-bold text-gray-300 transition-all">
                            <RotateCcw className="w-3.5 h-3.5" />
                            Reset Session
                        </button>
                    </div>
                </GlassContainer>

                {/* Chat Playground (Right) */}
                <GlassContainer className="col-span-9 flex flex-col bg-black/20 border-white/10 overflow-hidden relative">
                    {/* Debug: Decision Timeline */}
                    {sessionId && decisionSteps.length > 0 && (
                        <div className="shrink-0 border-b border-white/5">
                            <button
                                onClick={() => setDebugPanelOpen(!debugPanelOpen)}
                                className="w-full flex items-center justify-between px-4 py-2 text-[10px] font-bold text-gray-400 uppercase tracking-widest hover:bg-white/5">
                                Decision Timeline ({decisionSteps.length} turns)
                                {debugPanelOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                            </button>
                            {debugPanelOpen && (
                                <div className="p-4 max-h-48 overflow-y-auto custom-scrollbar">
                                    <DecisionVisualizer steps={decisionSteps} />
                                </div>
                            )}
                        </div>
                    )}
                    {/* Chat Area */}
                    <div className="flex-1 overflow-hidden flex flex-col relative min-h-0">
                        {selectedBotId ? (
                            <ChatWidget messages={messages} />
                        ) : (
                            <div className="h-full flex items-center justify-center text-gray-500 text-sm font-medium">
                                Select a bot to start testing
                            </div>
                        )}
                    </div>

                    {/* Input Area */}
                    <div className="p-4 bg-white/5 border-t border-white/5">
                        <form onSubmit={handleSendMessage} className="flex gap-4">
                            <input
                                type="text"
                                value={inputValue}
                                onChange={(e) => setInputValue(e.target.value)}
                                placeholder="Type a message to test..."
                                className="flex-1 bg-black/20 border border-white/10 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-accent/50 transition-all placeholder:text-gray-600"
                                disabled={!selectedBotId || isTyping}
                            />
                            <button
                                type="submit"
                                disabled={!selectedBotId || isTyping || !inputValue.trim()}
                                className="px-6 premium-gradient rounded-xl flex items-center justify-center text-white shadow-lg transition-transform hover:scale-105 active:scale-95 disabled:opacity-50 disabled:scale-100"
                            >
                                {isTyping ? (
                                    <RefreshCw className="w-5 h-5 animate-spin" />
                                ) : (
                                    <Send className="w-5 h-5" />
                                )}
                            </button>
                        </form>
                        <div className="flex justify-between mt-2 px-1">
                            <span className="text-[9px] font-medium text-gray-600">
                                Session ID: {sessionId || "Not Started"}
                            </span>
                            <span className="text-[9px] font-medium text-gray-600">
                                Enter to send • Shift+Enter for new line
                            </span>
                        </div>
                    </div>
                </GlassContainer>
            </div>
        </div>
    );
}
