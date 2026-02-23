"use client";

import GlassContainer from "@/components/ui/GlassContainer";
import { Puzzle, MessageSquare, Globe, ExternalLink, ShieldCheck, Zap, AlertCircle, XCircle, Loader2, Bot as BotIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiService, SalesChannel, Bot, ChannelConfig } from "@/lib/apiService";
import { useUIStore } from "@/lib/store";
import { useState, useEffect } from "react";
import { toast } from "sonner";

// Helper to map channel code to UI properties
const getChannelUI = (code: string) => {
    const normalize = code.toUpperCase();
    if (normalize.includes("ZALO")) return { icon: MessageSquare, color: "text-blue-500", type: "Social" };
    if (normalize.includes("FACEBOOK") || normalize.includes("FB")) return { icon: MessageSquare, color: "text-indigo-500", type: "Social" };
    if (normalize.includes("WEB")) return { icon: Globe, color: "text-accent", type: "Native" };
    return { icon: Puzzle, color: "text-gray-500", type: "Custom" };
};

export default function IntegrationsPage() {
    const queryClient = useQueryClient();
    const tenantId = useUIStore((s) => s.currentTenantId);
    const [selectedBotId, setSelectedBotId] = useState<string>("");
    const [configModal, setConfigModal] = useState<{ channel: SalesChannel; config?: ChannelConfig } | null>(null);
    const [configForm, setConfigForm] = useState<Record<string, string>>({});

    const { data: channels = [], isLoading } = useQuery({
        queryKey: ["channels"],
        queryFn: () => apiService.listChannels(),
    });

    const { data: bots = [] } = useQuery({
        queryKey: ["bots", "active"],
        queryFn: () => apiService.listBots({ status: "active" }),
    });

    const { data: channelConfigs = [] } = useQuery({
        queryKey: ["channel-configs", selectedBotId],
        queryFn: () => apiService.listChannelConfigs({ bot_id: selectedBotId }),
        enabled: !!selectedBotId,
    });

    const { data: botVersions = [] } = useQuery({
        queryKey: ["bot-versions", selectedBotId],
        queryFn: () => apiService.listBotVersions(selectedBotId),
        enabled: !!selectedBotId,
    });

    const activeVersion = botVersions.find((v: any) => v.is_active);

    const createOrUpdateMutation = useMutation({
        mutationFn: (data: { bot_version_id: string; channel_code: string; config?: Record<string, unknown>; is_active?: boolean }) =>
            apiService.createOrUpdateChannelConfig(data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["channel-configs"] });
            setConfigModal(null);
        },
        onError: (e: any) => toast.error(e?.response?.data?.detail || "Lỗi lưu config"),
    });

    useEffect(() => {
        if (bots.length > 0 && !selectedBotId) setSelectedBotId(bots[0].id);
    }, [bots, selectedBotId]);

    const openConfigModal = (channel: SalesChannel) => {
        if (!selectedBotId) {
            toast.error("Vui lòng chọn Bot trước");
            return;
        }
        const cfg = channelConfigs.find((c: ChannelConfig) => c.channel_code.toUpperCase() === channel.code.toUpperCase());
        const config = (cfg?.config || {}) as Record<string, string>;
        setConfigForm({
            access_token: config.access_token || "",
            page_access_token: config.page_access_token || "",
            page_id: config.page_id || "",
            verify_token: config.verify_token || "",
        });
        setConfigModal({ channel, config: cfg });
    };

    const handleSaveConfig = (e: React.FormEvent) => {
        e.preventDefault();
        if (!selectedBotId || !configModal || !activeVersion) {
            toast.error("Bot chưa có version active. Vào trang Bots để tạo và kích hoạt version.");
            return;
        }
        const config: Record<string, string> = {};
        if (configForm.access_token) config.access_token = configForm.access_token;
        if (configForm.page_access_token) config.page_access_token = configForm.page_access_token;
        if (configForm.page_id) config.page_id = configForm.page_id;
        if (configForm.verify_token) config.verify_token = configForm.verify_token;
        createOrUpdateMutation.mutate({
            bot_version_id: activeVersion.id,
            channel_code: configModal.channel.code.toUpperCase(),
            config: Object.keys(config).length ? config : undefined,
            is_active: true,
        });
    };

    const getConfigForChannel = (code: string) =>
        channelConfigs.find((c: ChannelConfig) => c.channel_code.toUpperCase() === code.toUpperCase());

    return (
        <div className="h-full flex flex-col space-y-6">
            <div className="flex flex-col">
                <h1 className="text-2xl font-black text-white">Omnichannel Integrations</h1>
                <p className="text-xs text-secondary font-bold uppercase tracking-[0.2em] mt-1">Connect your "Brain" to the world</p>
            </div>

            {/* Bot selector */}
            <GlassContainer className="p-4 flex flex-col bg-white/5 border-white/5">
                <div className="flex items-center gap-4">
                    <h3 className="text-[10px] font-black text-white uppercase tracking-widest border-r border-white/10 pr-4 py-1">Bot cho Config</h3>
                    <div className="flex gap-2 overflow-x-auto no-scrollbar">
                        {bots.map((b: Bot) => (
                            <button
                                key={b.id}
                                onClick={() => setSelectedBotId(b.id)}
                                className={cn(
                                    "min-w-[120px] p-3 rounded-2xl flex items-center gap-2 transition-all text-left",
                                    selectedBotId === b.id ? "bg-accent/10 border border-accent/30" : "bg-white/5 border border-white/5 hover:bg-white/10"
                                )}
                            >
                                <BotIcon className={cn("w-4 h-4 shrink-0", selectedBotId === b.id ? "text-accent" : "text-gray-500")} />
                                <span className={cn("text-[10px] font-bold truncate", selectedBotId === b.id ? "text-white" : "text-gray-400")}>{b.name}</span>
                            </button>
                        ))}
                    </div>
                </div>
            </GlassContainer>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {isLoading ? (
                    [1, 2, 3].map((i) => (
                        <div key={i} className="h-48 bg-white/5 rounded-3xl animate-pulse border border-white/5"></div>
                    ))
                ) : channels.length === 0 ? (
                    <div className="col-span-3 p-12 bg-white/5 rounded-3xl border border-white/5 border-dashed flex flex-col items-center justify-center text-gray-500">
                        <Puzzle className="w-12 h-12 mb-4 opacity-20" />
                        <p className="text-sm font-bold">No channels configured</p>
                    </div>
                ) : (
                    channels.map((c) => {
                        const ui = getChannelUI(c.code);
                        const hasConfig = !!getConfigForChannel(c.code);
                        return (
                            <GlassContainer key={c.id} className="p-6 flex flex-col bg-white/5 border-white/5 group hover:border-accent/30 transition-all">
                                <div className="flex items-center justify-between mb-8">
                                    <div className={cn("p-3 rounded-2xl bg-white/5", ui.color)}>
                                        <ui.icon className="w-8 h-8" />
                                    </div>
                                    <div className="flex items-center gap-2">
                                        {hasConfig && (
                                            <span className="px-2 py-0.5 rounded bg-green-500/20 text-green-500 text-[8px] font-black uppercase">Configured</span>
                                        )}
                                        <span className={cn(
                                            "px-3 py-1 rounded-full text-[8px] font-black uppercase tracking-widest",
                                            c.is_active ? "bg-green-500/10 text-green-500" : "bg-gray-500/10 text-gray-500"
                                        )}>{c.is_active ? "Active" : "Disabled"}</span>
                                    </div>
                                </div>

                                <h3 className="text-lg font-bold text-white mb-1">{c.name}</h3>
                                <div className="flex items-center gap-2 mb-6">
                                    <span className="text-[10px] text-gray-500 font-bold uppercase tracking-widest">{ui.type} Integration</span>
                                    <span className="text-[10px] text-gray-600 font-mono bg-white/5 px-1.5 rounded">{c.code}</span>
                                </div>

                                <div className="mt-auto flex items-center gap-2">
                                    <button
                                        onClick={() => openConfigModal(c)}
                                        className="flex-1 py-3 glass-effect rounded-xl text-[10px] font-black uppercase tracking-widest hover:bg-white/10 transition-colors"
                                    >
                                        Config Settings
                                    </button>
                                    <button className="px-4 py-3 bg-white/5 border border-white/10 rounded-xl hover:text-white transition-colors">
                                        <ExternalLink className="w-4 h-4" />
                                    </button>
                                </div>
                            </GlassContainer>
                        );
                    })
                )}
            </div>

            <GlassContainer className="p-8 flex flex-col items-center justify-center bg-accent/5 border-accent/20 min-h-[300px]">
                <div className="w-16 h-16 rounded-full bg-accent/20 flex items-center justify-center text-accent mb-6 animate-pulse">
                    <ShieldCheck className="w-10 h-10" />
                </div>
                <h2 className="text-xl font-black text-white mb-2">Enterprise Security Protocol</h2>
                <p className="text-gray-400 text-sm max-w-lg text-center font-medium leading-relaxed">
                    All integrations are protected by IRIS Auth v4. Every message event is validated against tenant-specific keys before hitting the Hybrid Orchestrator.
                </p>
                <div className="mt-8 flex gap-4">
                    <div className="flex items-center gap-2 text-[10px] font-bold text-accent uppercase">
                        <Zap className="w-4 h-4" /> End-to-End Encryption
                    </div>
                    <div className="flex items-center gap-2 text-[10px] font-bold text-red-400 uppercase">
                        <AlertCircle className="w-4 h-4" /> Audit Logging Enabled
                    </div>
                </div>
            </GlassContainer>

            {/* Config Modal */}
            {configModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
                    <GlassContainer className="w-full max-w-md p-8 bg-white/10 border-white/10 shadow-2xl">
                        <div className="flex items-center justify-between mb-6">
                            <h2 className="text-xl font-black text-white">Channel Config: {configModal.channel.name}</h2>
                            <button onClick={() => setConfigModal(null)} className="text-gray-400 hover:text-white"><XCircle className="w-6 h-6" /></button>
                        </div>
                        <form onSubmit={handleSaveConfig} className="space-y-4">
                            {configModal.channel.code.toUpperCase().includes("ZALO") && (
                                <>
                                    <div>
                                        <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest block mb-2">Webhook URL (dán vào Zalo Developer)</label>
                                        <div className="flex gap-2">
                                            <input
                                                type="text"
                                                readOnly
                                                value={tenantId && selectedBotId
                                                    ? `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8386"}/webhooks/zalo/${tenantId}/${selectedBotId}/message`
                                                    : "Chọn Bot - đăng nhập để xem URL"}
                                                className="flex-1 bg-white/5 border border-white/10 rounded-xl p-3 text-xs text-gray-400 font-mono"
                                            />
                                            <button
                                                type="button"
                                                onClick={() => {
                                                    const url = `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8386"}/webhooks/zalo/${tenantId || ""}/${selectedBotId}/message`;
                                                    navigator.clipboard.writeText(url);
                                                    toast.success("Đã copy URL");
                                                }}
                                                className="px-4 py-2 bg-white/10 rounded-xl text-xs font-bold hover:bg-white/20"
                                            >
                                                Copy
                                            </button>
                                        </div>
                                    </div>
                                    <div>
                                        <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest block mb-2">Access Token (Zalo OA)</label>
                                        <input
                                            type="password"
                                            value={configForm.access_token}
                                            onChange={(e) => setConfigForm({ ...configForm, access_token: e.target.value })}
                                            placeholder="Zalo OA Access Token"
                                            className="w-full bg-white/5 border border-white/10 rounded-xl p-3 text-sm text-white focus:outline-none focus:border-accent font-mono"
                                        />
                                    </div>
                                </>
                            )}
                            {(configModal.channel.code.toUpperCase().includes("FACEBOOK") || configModal.channel.code.toUpperCase().includes("FB")) && (
                                <>
                                    <div>
                                        <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest block mb-2">Page Access Token</label>
                                        <input
                                            type="password"
                                            value={configForm.page_access_token}
                                            onChange={(e) => setConfigForm({ ...configForm, page_access_token: e.target.value })}
                                            placeholder="Facebook Page Access Token"
                                            className="w-full bg-white/5 border border-white/10 rounded-xl p-3 text-sm text-white focus:outline-none focus:border-accent font-mono"
                                        />
                                    </div>
                                    <div>
                                        <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest block mb-2">Page ID (optional)</label>
                                        <input
                                            type="text"
                                            value={configForm.page_id}
                                            onChange={(e) => setConfigForm({ ...configForm, page_id: e.target.value })}
                                            placeholder="Page ID"
                                            className="w-full bg-white/5 border border-white/10 rounded-xl p-3 text-sm text-white focus:outline-none focus:border-accent"
                                        />
                                    </div>
                                    <div>
                                        <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest block mb-2">Verify Token (webhook)</label>
                                        <input
                                            type="text"
                                            value={configForm.verify_token}
                                            onChange={(e) => setConfigForm({ ...configForm, verify_token: e.target.value })}
                                            placeholder="Verify token for webhook subscription"
                                            className="w-full bg-white/5 border border-white/10 rounded-xl p-3 text-sm text-white focus:outline-none focus:border-accent"
                                        />
                                    </div>
                                </>
                            )}
                            {configModal.channel.code.toUpperCase().includes("WEBCHAT") && (
                                <>
                                    <div>
                                        <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest block mb-2">Embed iframe (chèn vào website)</label>
                                        <textarea
                                            readOnly
                                            rows={3}
                                            value={`<iframe src="${typeof window !== "undefined" ? window.location.origin : ""}/widget?tenant_id=${tenantId}&bot_id=${selectedBotId}" width="400" height="500" style="border:none;border-radius:12px;"></iframe>`}
                                            className="w-full bg-white/5 border border-white/10 rounded-xl p-3 text-[10px] text-gray-400 font-mono"
                                        />
                                        <p className="text-[9px] text-gray-500 mt-1">Copy và dán vào HTML của website</p>
                                    </div>
                                </>
                            )}
                            {!configModal.channel.code.toUpperCase().includes("ZALO") && !configModal.channel.code.toUpperCase().includes("FACEBOOK") && !configModal.channel.code.toUpperCase().includes("FB") && !configModal.channel.code.toUpperCase().includes("WEBCHAT") && (
                                <div>
                                    <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest block mb-2">Custom Config (JSON)</label>
                                    <input
                                        type="text"
                                        value={configForm.access_token || ""}
                                        onChange={(e) => setConfigForm({ ...configForm, access_token: e.target.value })}
                                        placeholder='{"key": "value"}'
                                        className="w-full bg-white/5 border border-white/10 rounded-xl p-3 text-sm text-white focus:outline-none focus:border-accent font-mono"
                                    />
                                </div>
                            )}
                            <div className="flex gap-4 pt-4">
                                <button type="button" onClick={() => setConfigModal(null)} className="flex-1 py-3 bg-white/5 border border-white/10 rounded-xl text-sm font-bold text-gray-400 hover:bg-white/10">Cancel</button>
                                <button type="submit" disabled={createOrUpdateMutation.isPending} className="flex-1 premium-gradient py-3 rounded-xl text-sm font-bold text-white shadow-lg disabled:opacity-50">
                                    {createOrUpdateMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin mx-auto" /> : "Save"}
                                </button>
                            </div>
                        </form>
                    </GlassContainer>
                </div>
            )}
        </div>
    );
}
