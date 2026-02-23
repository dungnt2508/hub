"use client";

import GlassContainer from "@/components/ui/GlassContainer";
import { Bot, Plus, Search, Filter, Edit3, Trash2, CheckCircle, XCircle, Code, Layers, Settings, Archive, RefreshCcw } from "lucide-react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiService, Bot as BotType } from "@/lib/apiService";
import { cn } from "@/lib/utils";
import { useState, useEffect } from "react";

// Sub-component for Domain Data Schema Preview
const AttributePreview = ({ domainId, definitions, isLoading }: { domainId: string, definitions: any[], isLoading: boolean }) => {
    if (!domainId) return (
        <div className="p-4 bg-white/5 rounded-xl border border-dashed border-white/10 text-center">
            <p className="text-[10px] text-gray-500 font-bold uppercase tracking-widest italic">No domain selected - Bot will use Global knowledge only</p>
        </div>
    );

    if (isLoading) return (
        <div className="flex items-center justify-center p-4 bg-white/5 rounded-xl border border-white/10">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-accent"></div>
        </div>
    );

    return (
        <div className="bg-white/5 rounded-xl border border-white/10 overflow-hidden">
            <div className="px-4 py-2 bg-white/5 border-b border-white/10 flex items-center justify-between">
                <span className="text-[9px] font-black text-gray-400 uppercase tracking-widest">Data Schema Preview</span>
                <span className="px-1.5 py-0.5 rounded bg-accent/20 text-[8px] font-bold text-accent">{definitions.length} Attributes</span>
            </div>
            <div className="p-3">
                {definitions.length === 0 ? (
                    <p className="text-[10px] text-gray-500 italic">This domain has no custom attribute definitions.</p>
                ) : (
                    <div className="grid grid-cols-2 gap-2">
                        {definitions.map((def) => (
                            <div key={def.id} className="flex items-center gap-2 group">
                                <span className="w-1.5 h-1.5 rounded-full bg-accent/40" />
                                <div className="flex flex-col">
                                    <span className="text-[10px] font-bold text-gray-200">{def.key}</span>
                                    <span className="text-[8px] text-gray-500 uppercase font-medium">{def.value_type} • {def.scope}</span>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};

export default function BotsPage() {
    const queryClient = useQueryClient();
    const [searchTerm, setSearchTerm] = useState("");
    const [filter, setFilter] = useState<"all" | "active" | "archived">("all");
    const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
    const [isVersionModalOpen, setIsVersionModalOpen] = useState(false);
    const [isSettingsModalOpen, setIsSettingsModalOpen] = useState(false);
    const [selectedBot, setSelectedBot] = useState<BotType | null>(null);
    const [newBotName, setNewBotName] = useState("");
    const [newBotCode, setNewBotCode] = useState("");
    const [selectedBotDomainId, setSelectedBotDomainId] = useState("");

    // --- QUERIES ---

    // Fetch Bots
    const { data: bots = [], isLoading, error } = useQuery({
        queryKey: ["bots"],
        queryFn: () => apiService.listBots(),
    });

    // Fetch Versions
    const { data: versions = [], isLoading: isLoadingVersions } = useQuery({
        queryKey: ["bot-versions", selectedBot?.id],
        queryFn: () => apiService.listBotVersions(selectedBot!.id),
        enabled: !!selectedBot && isVersionModalOpen,
    });

    // Fetch Knowledge Domains
    const { data: domains = [] } = useQuery({
        queryKey: ["knowledge-domains"],
        queryFn: () => apiService.listDomains(),
    });

    // Fetch All System Capabilities
    const { data: allCapabilities = [] } = useQuery({
        queryKey: ["all-capabilities"],
        queryFn: () => apiService.listCapabilities(),
        enabled: isVersionModalOpen,
    });

    // Fetch Domain Attribute Definitions (Preview)
    const { data: attrDefinitions = [], isLoading: isLoadingAttrs } = useQuery({
        queryKey: ["attribute-definitions", selectedBotDomainId],
        queryFn: () => apiService.listAttributeDefinitions(selectedBotDomainId || undefined),
        enabled: isCreateModalOpen || isSettingsModalOpen,
    });

    // --- MUTATIONS ---

    // Create Bot
    const createMutation = useMutation({
        mutationFn: ({ name, code, domain_id }: { name: string; code: string; domain_id?: string }) =>
            apiService.createBot(name, code, domain_id),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["bots"] });
            setIsCreateModalOpen(false);
            setNewBotName("");
            setNewBotCode("");
            setSelectedBotDomainId("");
        },
    });

    // Update Bot Settings
    const updateMutation = useMutation({
        mutationFn: ({ id, data }: { id: string; data: Partial<BotType> }) =>
            apiService.updateBot(id, data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["bots"] });
            setIsSettingsModalOpen(false);
            setSelectedBot(null);
        },
    });

    // Delete Bot
    const deleteMutation = useMutation({
        mutationFn: (id: string) => apiService.deleteBot(id),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["bots"] });
        },
    });

    // Toggle Bot Status (Active/Archived)
    const statusMutation = useMutation({
        mutationFn: ({ id, status }: { id: string; status: string }) =>
            apiService.updateBotStatus(id, status),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["bots"] });
        },
    });

    // Create New Bot Version
    const createVersionMutation = useMutation({
        mutationFn: (botId: string) => apiService.createBotVersion(botId),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["bot-versions", selectedBot?.id] });
            queryClient.invalidateQueries({ queryKey: ["bots"] });
        },
    });

    // Activate Specific Version
    const activateVersionMutation = useMutation({
        mutationFn: ({ botId, versionId }: { botId: string; versionId: string }) =>
            apiService.activateBotVersion(botId, versionId),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["bot-versions", selectedBot?.id] });
            queryClient.invalidateQueries({ queryKey: ["bots"] });
        },
    });

    // Update Version Capabilities
    const updateCapabilitiesMutation = useMutation({
        mutationFn: ({ versionId, codes }: { versionId: string; codes: string[] }) =>
            apiService.updateBotVersionCapabilities(selectedBot!.id, versionId, codes),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["bot-versions", selectedBot?.id] });
            queryClient.invalidateQueries({ queryKey: ["bots"] });
        },
    });

    // --- HELPERS ---

    const filteredBots = bots.filter(b => {
        const matchesSearch = b.name.toLowerCase().includes(searchTerm.toLowerCase()) || b.code.toLowerCase().includes(searchTerm.toLowerCase());
        const matchesFilter = filter === "all" || b.status === filter;
        return matchesSearch && matchesFilter;
    });

    const handleDelete = (id: string, name: string) => {
        if (confirm(`Bạn có chắc chắn muốn xóa Bot "${name}" không?`)) {
            deleteMutation.mutate(id);
        }
    };

    const toggleStatus = (id: string, currentStatus: string) => {
        const newStatus = currentStatus === "active" ? "archived" : "active";
        statusMutation.mutate({ id, status: newStatus });
    };

    const toggleCapability = (version: any, capCode: string) => {
        const currentCodes = version.capabilities?.map((c: any) => c.code) || [];
        const newCodes = currentCodes.includes(capCode)
            ? currentCodes.filter((c: string) => c !== capCode)
            : [...currentCodes, capCode];

        updateCapabilitiesMutation.mutate({ versionId: version.id, codes: newCodes });
    };

    const handleCreateSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (newBotName.trim() && newBotCode.trim()) {
            createMutation.mutate({
                name: newBotName.trim(),
                code: newBotCode.trim(),
                domain_id: selectedBotDomainId || undefined
            });
        }
    };

    const handleUpdateSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (selectedBot && newBotName.trim() && newBotCode.trim()) {
            updateMutation.mutate({
                id: selectedBot.id,
                data: {
                    name: newBotName.trim(),
                    // Code and Domain are immutable after creation as per requirement
                    // code: newBotCode.trim(),
                    // domain_id: selectedBotDomainId || null
                }
            });
        }
    };

    const openVersionModal = (bot: BotType) => {
        setSelectedBot(bot);
        setIsVersionModalOpen(true);
    };

    const openSettingsModal = (bot: BotType) => {
        setSelectedBot(bot);
        setNewBotName(bot.name);
        setNewBotCode(bot.code);
        setSelectedBotDomainId(bot.domain_id || "");
        setIsSettingsModalOpen(true);
    };

    const stats = {
        total: bots.length,
        active: bots.filter(b => b.status === "active").length,
        archived: bots.filter(b => b.status === "archived").length,
        capabilities: bots.filter(b => b.status === "active").reduce((acc, b) => acc + (b.capabilities?.length || 0), 0),
    };

    return (
        <div className="h-full flex flex-col space-y-6">
            <div className="flex items-center justify-between">
                <div className="flex flex-col">
                    <h1 className="text-2xl font-black text-white">Bot & kịch bản</h1>
                    <p className="text-xs text-gray-500 font-bold uppercase tracking-[0.2em] mt-1">QUẢN LÝ, CẤU HÌNH VÀ TRIỂN KHAI BOT CỦA BẠN</p>
                </div>
                <div className="flex gap-3">
                    <button
                        onClick={() => setIsCreateModalOpen(true)}
                        className="flex items-center gap-2 px-6 py-2 premium-gradient rounded-xl text-xs font-bold text-white shadow-lg transition-all hover:scale-[1.02] active:scale-[0.98]">
                        <Plus className="w-4 h-4" /> New Bot
                    </button>
                </div>
            </div>

            {/* Stats Summary */}
            <div className="grid grid-cols-4 gap-6">
                <div className="p-6 bg-white/5 rounded-3xl border border-white/5 flex items-center gap-6">
                    <div className="w-14 h-14 rounded-2xl bg-accent/20 flex items-center justify-center text-accent">
                        <Bot className="w-8 h-8" />
                    </div>
                    <div>
                        <div className="text-2xl font-black text-white">{stats.total}</div>
                        <div className="text-[10px] font-bold text-gray-500 uppercase tracking-widest">Total Bots</div>
                    </div>
                </div>
                <div className="p-6 bg-white/5 rounded-3xl border border-white/5 flex items-center gap-6">
                    <div className="w-14 h-14 rounded-2xl bg-green-500/20 flex items-center justify-center text-green-500">
                        <CheckCircle className="w-8 h-8" />
                    </div>
                    <div>
                        <div className="text-2xl font-black text-white">{stats.active}</div>
                        <div className="text-[10px] font-bold text-gray-500 uppercase tracking-widest">Active</div>
                    </div>
                </div>
                <div className="p-6 bg-white/5 rounded-3xl border border-white/5 flex items-center gap-6">
                    <div className="w-14 h-14 rounded-2xl bg-orange-500/20 flex items-center justify-center text-orange-500">
                        <Layers className="w-8 h-8" />
                    </div>
                    <div>
                        <div className="text-2xl font-black text-white">{stats.archived}</div>
                        <div className="text-[10px] font-bold text-gray-500 uppercase tracking-widest">Archived</div>
                    </div>
                </div>
                <div className="p-6 bg-white/5 rounded-3xl border border-white/5 flex items-center gap-6">
                    <div className="w-14 h-14 rounded-2xl bg-purple-500/20 flex items-center justify-center text-purple-500">
                        <Code className="w-8 h-8" />
                    </div>
                    <div>
                        <div className="text-2xl font-black text-white">{stats.capabilities}</div>
                        <div className="text-[10px] font-bold text-gray-500 uppercase tracking-widest">Capabilities</div>
                    </div>
                </div>
            </div>

            {/* Main Table Area */}
            <GlassContainer className="flex-1 p-8 flex flex-col bg-white/5 border-white/5 min-h-0">
                <div className="flex items-center justify-between mb-8">
                    <div className="flex bg-white/5 p-1 rounded-xl">
                        <button
                            onClick={() => setFilter("all")}
                            className={cn(
                                "px-6 py-2 rounded-lg text-xs font-bold transition-all shadow-sm",
                                filter === "all" ? "bg-white/10 text-white" : "text-gray-500 hover:text-gray-300"
                            )}>All Bots</button>
                        <button
                            onClick={() => setFilter("active")}
                            className={cn(
                                "px-6 py-2 rounded-lg text-xs font-bold transition-all",
                                filter === "active" ? "bg-white/10 text-white" : "text-gray-500 hover:text-gray-300"
                            )}>Active Only</button>
                        <button
                            onClick={() => setFilter("archived")}
                            className={cn(
                                "px-6 py-2 rounded-lg text-xs font-bold transition-all",
                                filter === "archived" ? "bg-white/10 text-white" : "text-gray-500 hover:text-gray-300"
                            )}>Archived</button>
                    </div>
                    <div className="flex gap-4">
                        <div className="relative">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                            <input
                                type="text"
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                placeholder="Search bots..."
                                className="bg-white/5 border border-white/10 rounded-xl py-2 pl-10 pr-4 text-xs focus:outline-none focus:border-accent/40 w-64 text-gray-300"
                            />
                        </div>
                    </div>
                </div>

                <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar no-scrollbar">
                    {isLoading ? (
                        <div className="h-full flex items-center justify-center">
                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-accent"></div>
                        </div>
                    ) : error ? (
                        <div className="h-full flex items-center justify-center text-red-500 text-sm">
                            Error loading bots. Please try again.
                        </div>
                    ) : (
                        <table className="w-full text-left">
                            <thead>
                                <tr className="text-[10px] font-black text-gray-500 uppercase tracking-widest border-b border-white/5">
                                    <th className="pb-4 pl-4 font-black">Bot Info</th>
                                    <th className="pb-4 font-black">Status</th>
                                    <th className="pb-4 font-black">Versions</th>
                                    <th className="pb-4 font-black">Capabilities</th>
                                    <th className="pb-4 font-black text-right pr-4">Actions</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-white/5">
                                {filteredBots.map((item) => (
                                    <tr key={item.id} className="group hover:bg-white/[0.02] transition-colors">
                                        <td className="py-4 pl-4">
                                            <div className="text-sm font-bold text-gray-200">{item.name}</div>
                                            <div className="flex flex-col mt-0.5 space-y-0.5">
                                                <div className="text-[9px] text-gray-500 font-medium font-mono uppercase">ID: {item.id}</div>
                                                <div className="text-[9px] text-gray-500 font-bold font-mono">CODE: {item.code}</div>
                                                <div className="flex items-center gap-1 pt-0.5">
                                                    <div className={cn(
                                                        "w-1 h-1 rounded-full opacity-40",
                                                        item.domain ? "bg-accent" : "bg-gray-600"
                                                    )} />
                                                    <span className="text-[9px] font-bold text-gray-500 uppercase tracking-wide">
                                                        Domain: {item.domain?.name || "Global"}
                                                    </span>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="py-4">
                                            <button
                                                onClick={() => toggleStatus(item.id, item.status)}
                                                className={cn(
                                                    "px-2 py-0.5 rounded-md border text-[9px] font-bold uppercase transition-all",
                                                    item.status === "active"
                                                        ? "bg-green-500/10 border-green-500/30 text-green-500"
                                                        : "bg-gray-500/10 border-gray-500/30 text-gray-500"
                                                )}>{item.status}</button>
                                        </td>
                                        <td className="py-4">
                                            <div className="flex items-center gap-2">
                                                <div className="text-sm font-black text-white">{item.versions_count || 0}</div>
                                                <span className="text-[10px] text-gray-500">versions</span>
                                            </div>
                                        </td>
                                        <td className="py-4">
                                            <div className="flex flex-wrap gap-1">
                                                {item.capabilities && item.capabilities.length > 0 ? (
                                                    <>
                                                        {item.capabilities.slice(0, 2).map((cap, i) => (
                                                            <span key={i} className="px-2 py-0.5 rounded-md bg-accent/10 border border-accent/20 text-[8px] font-bold text-accent uppercase">
                                                                {cap}
                                                            </span>
                                                        ))}
                                                        {item.capabilities.length > 2 && (
                                                            <span className="px-2 py-0.5 rounded-md bg-white/5 border border-white/10 text-[8px] font-bold text-gray-400">
                                                                +{item.capabilities.length - 2}
                                                            </span>
                                                        )}
                                                    </>
                                                ) : (
                                                    <span className="px-2 py-0.5 rounded-md bg-white/5 border border-white/10 text-[8px] font-bold text-gray-500 uppercase italic">
                                                        No Active Version
                                                    </span>
                                                )}
                                            </div>
                                        </td>
                                        <td className="py-4 text-right pr-4">
                                            <div className="flex justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                                <button
                                                    onClick={() => openVersionModal(item)}
                                                    className="p-2 bg-white/5 rounded-lg border border-white/10 text-gray-400 hover:text-cyan-500 hover:border-cyan-500/40" title="Manage Versions">
                                                    <Layers className="w-3.5 h-3.5" />
                                                </button>
                                                <button
                                                    onClick={() => openSettingsModal(item)}
                                                    className="p-2 bg-white/5 rounded-lg border border-white/10 text-gray-400 hover:text-purple-500 hover:border-purple-500/40" title="Settings">
                                                    <Settings className="w-3.5 h-3.5" />
                                                </button>
                                                <button
                                                    onClick={() => toggleStatus(item.id, item.status)}
                                                    className={cn(
                                                        "p-2 bg-white/5 rounded-lg border border-white/10 transition-all",
                                                        item.status === "active"
                                                            ? "text-gray-400 hover:text-orange-500 hover:border-orange-500/40"
                                                            : "text-gray-400 hover:text-green-500 hover:border-green-500/40"
                                                    )}
                                                    title={item.status === "active" ? "Archive Bot" : "Restore Bot"}>
                                                    {item.status === "active" ? <Archive className="w-3.5 h-3.5" /> : <RefreshCcw className="w-3.5 h-3.5" />}
                                                </button>
                                                <button
                                                    onClick={() => handleDelete(item.id, item.name)}
                                                    className="p-2 bg-white/5 rounded-lg border border-white/10 text-gray-400 hover:text-red-500 hover:border-red-500/40" title="Delete">
                                                    <Trash2 className="w-3.5 h-3.5" />
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    )}
                </div>
            </GlassContainer>

            {/* --- MODALS --- */}

            {/* Create Bot Modal */}
            {isCreateModalOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
                    <GlassContainer className="w-full max-w-md p-8 bg-white/10 border-white/10 shadow-2xl animate-in fade-in zoom-in duration-200">
                        <div className="flex items-center justify-between mb-8">
                            <h2 className="text-xl font-black text-white">Create New AI Bot</h2>
                            <button
                                onClick={() => setIsCreateModalOpen(false)}
                                className="text-gray-400 hover:text-white transition-colors">
                                <XCircle className="w-6 h-6" />
                            </button>
                        </div>

                        <form onSubmit={handleCreateSubmit} className="space-y-6">
                            <div className="space-y-2">
                                <label className="text-xs font-bold text-gray-400 uppercase tracking-widest block">Bot Name</label>
                                <input
                                    type="text"
                                    value={newBotName}
                                    onChange={(e) => setNewBotName(e.target.value)}
                                    placeholder="e.g. Customer Support AI"
                                    className="w-full bg-white/5 border border-white/10 rounded-xl py-3 px-4 text-sm text-gray-200 focus:outline-none focus:border-accent/50 transition-all"
                                    required
                                    autoFocus
                                />
                            </div>

                            <div className="space-y-2">
                                <label className="text-xs font-bold text-gray-400 uppercase tracking-widest block">Bot Code (Unique ID)</label>
                                <input
                                    type="text"
                                    value={newBotCode}
                                    onChange={(e) => setNewBotCode(e.target.value.toLowerCase().replace(/\s+/g, '-'))}
                                    placeholder="e.g. support-bot"
                                    className="w-full bg-white/5 border border-white/10 rounded-xl py-3 px-4 text-sm font-mono text-gray-200 focus:outline-none focus:border-accent/50 transition-all"
                                    required
                                />
                                <p className="text-[10px] text-gray-500 font-medium italic">Lowercase, no spaces. Used for API identification.</p>
                            </div>

                            <div className="space-y-4">
                                <div className="space-y-2">
                                    <label className="text-xs font-bold text-gray-400 uppercase tracking-widest block">Domain (Knowledge Scope)</label>
                                    <select
                                        value={selectedBotDomainId}
                                        onChange={(e) => setSelectedBotDomainId(e.target.value)}
                                        className="w-full bg-white/5 border border-white/10 rounded-xl py-3 px-4 text-sm text-gray-200 focus:outline-none focus:border-accent/50 transition-all appearance-none"
                                    >
                                        <option value="">Global / No Specific Domain</option>
                                        {domains.map((dom: any) => (
                                            <option key={dom.id} value={dom.id}>{dom.name}</option>
                                        ))}
                                    </select>
                                    <p className="text-[10px] text-gray-500 font-medium italic">Assigning a domain scopes the bot to specific products and FAQs.</p>
                                </div>

                                <AttributePreview
                                    domainId={selectedBotDomainId}
                                    definitions={attrDefinitions}
                                    isLoading={isLoadingAttrs}
                                />
                            </div>

                            <div className="flex gap-4 pt-4">
                                <button
                                    type="button"
                                    onClick={() => setIsCreateModalOpen(false)}
                                    className="flex-1 py-3 bg-white/5 border border-white/10 rounded-xl text-sm font-bold text-gray-400 hover:bg-white/10 transition-all">
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    disabled={createMutation.isPending || !newBotName.trim() || !newBotCode.trim()}
                                    className="flex-1 premium-gradient py-3 rounded-xl text-sm font-bold text-white shadow-lg transition-all hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50 disabled:scale-100">
                                    {createMutation.isPending ? "Creating..." : "Create Bot"}
                                </button>
                            </div>
                        </form>
                    </GlassContainer>
                </div>
            )}

            {/* Manage Versions Modal */}
            {isVersionModalOpen && selectedBot && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
                    <GlassContainer className="w-full max-w-4xl p-8 bg-white/10 border-white/10 shadow-2xl animate-in fade-in zoom-in duration-200">
                        <div className="flex items-center justify-between mb-8">
                            <div>
                                <h2 className="text-xl font-black text-white">Manage Versions & Capabilities</h2>
                                <p className="text-[10px] text-gray-500 font-bold uppercase tracking-widest mt-1">{selectedBot.name} ({selectedBot.code})</p>
                            </div>
                            <button
                                onClick={() => setIsVersionModalOpen(false)}
                                className="text-gray-400 hover:text-white transition-colors">
                                <XCircle className="w-6 h-6" />
                            </button>
                        </div>

                        <div className="space-y-6">
                            <div className="flex items-center justify-between">
                                <div className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">Version History</div>
                                <button
                                    onClick={() => createVersionMutation.mutate(selectedBot.id)}
                                    disabled={createVersionMutation.isPending}
                                    className="flex items-center gap-2 px-4 py-1.5 bg-accent/20 border border-accent/40 rounded-lg text-[10px] font-bold text-accent hover:bg-accent/30 transition-all disabled:opacity-50">
                                    <Plus className="w-3 h-3" /> {createVersionMutation.isPending ? "Creating..." : "New Version"}
                                </button>
                            </div>

                            <div className="max-h-[400px] overflow-y-auto pr-2 custom-scrollbar no-scrollbar">
                                {isLoadingVersions ? (
                                    <div className="py-12 flex items-center justify-center">
                                        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-accent"></div>
                                    </div>
                                ) : versions.length === 0 ? (
                                    <div className="py-12 text-center text-xs text-gray-500 font-bold uppercase tracking-widest bg-white/5 rounded-2xl border border-white/5 italic">
                                        No versions found. Create your first version.
                                    </div>
                                ) : (
                                    <table className="w-full text-left">
                                        <thead>
                                            <tr className="text-[9px] font-black text-gray-500 uppercase tracking-widest border-b border-white/5">
                                                <th className="pb-3 pl-4">v#</th>
                                                <th className="pb-3">Status</th>
                                                <th className="pb-3">Capabilities</th>
                                                <th className="pb-3">Created</th>
                                                <th className="pb-3 text-right pr-4">Actions</th>
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-white/5">
                                            {versions.map((v) => (
                                                <tr key={v.id} className="group hover:bg-white/[0.02] transition-colors">
                                                    <td className="py-4 pl-4 align-top">
                                                        <div className="text-sm font-black text-white">v{v.version}</div>
                                                    </td>
                                                    <td className="py-4 align-top">
                                                        {v.is_active ? (
                                                            <span className="px-2 py-0.5 rounded-md bg-green-500/10 border border-green-500/30 text-[8px] font-bold text-green-500 uppercase">Active</span>
                                                        ) : (
                                                            <span className="px-2 py-0.5 rounded-md bg-white/5 border border-white/10 text-[8px] font-bold text-gray-500 uppercase">Inactive</span>
                                                        )}
                                                    </td>
                                                    <td className="py-4 align-top">
                                                        <div className="flex flex-wrap gap-2 max-w-xs">
                                                            {allCapabilities.map((cap) => {
                                                                const isEnabled = v.capabilities?.some((c: any) => c.code === cap.code);
                                                                return (
                                                                    <button
                                                                        key={cap.id}
                                                                        type="button"
                                                                        onClick={() => toggleCapability(v, cap.code)}
                                                                        disabled={updateCapabilitiesMutation.isPending}
                                                                        className={cn(
                                                                            "px-2 py-1 rounded-lg text-[9px] font-bold transition-all border cursor-pointer hover:scale-105 active:scale-95",
                                                                            isEnabled
                                                                                ? "bg-accent/20 border-accent/40 text-accent shadow-[0_0_10px_rgba(168,85,247,0.3)]"
                                                                                : "bg-white/5 border-white/10 text-gray-500 hover:border-white/20 hover:bg-white/10"
                                                                        )}
                                                                        title={cap.description}
                                                                    >
                                                                        {cap.code.toUpperCase()}
                                                                    </button>
                                                                );
                                                            })}
                                                        </div>
                                                    </td>
                                                    <td className="py-4 align-top">
                                                        <div className="text-[10px] font-medium text-gray-500">{new Date().toLocaleDateString()}</div>
                                                    </td>
                                                    <td className="py-4 text-right pr-4 align-top">
                                                        <button
                                                            disabled={v.is_active || activateVersionMutation.isPending}
                                                            onClick={() => activateVersionMutation.mutate({ botId: selectedBot.id, versionId: v.id })}
                                                            className="text-[9px] font-black text-accent uppercase tracking-widest hover:underline disabled:opacity-30 disabled:no-underline">
                                                            {activateVersionMutation.isPending ? "..." : "Activate"}
                                                        </button>
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                )}
                            </div>
                        </div>

                        <div className="mt-8 pt-6 border-t border-white/10 flex justify-end">
                            <button
                                onClick={() => setIsVersionModalOpen(false)}
                                className="px-6 py-2 bg-white/5 border border-white/10 rounded-xl text-xs font-bold text-gray-400 hover:bg-white/10 transition-all">
                                Close
                            </button>
                        </div>
                    </GlassContainer>
                </div>
            )}

            {/* Settings Modal */}
            {isSettingsModalOpen && selectedBot && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
                    <GlassContainer className="w-full max-w-md p-8 bg-white/10 border-white/10 shadow-2xl animate-in fade-in zoom-in duration-200">
                        <div className="flex items-center justify-between mb-8">
                            <h2 className="text-xl font-black text-white">Bot Settings</h2>
                            <button
                                onClick={() => setIsSettingsModalOpen(false)}
                                className="text-gray-400 hover:text-white transition-colors">
                                <XCircle className="w-6 h-6" />
                            </button>
                        </div>

                        <form onSubmit={handleUpdateSubmit} className="space-y-6">
                            <div className="space-y-2">
                                <label className="text-xs font-bold text-gray-400 uppercase tracking-widest block">Bot Name</label>
                                <input
                                    type="text"
                                    value={newBotName}
                                    onChange={(e) => setNewBotName(e.target.value)}
                                    placeholder="e.g. Customer Support AI"
                                    className="w-full bg-white/5 border border-white/10 rounded-xl py-3 px-4 text-sm text-gray-200 focus:outline-none focus:border-accent/50 transition-all"
                                    required
                                />
                            </div>

                            <div className="space-y-2">
                                <label className="text-xs font-bold text-gray-400 uppercase tracking-widest block">Bot Code (Unique ID)</label>
                                <input
                                    type="text"
                                    value={newBotCode}
                                    disabled
                                    className="w-full bg-white/5 border border-white/10 rounded-xl py-3 px-4 text-sm font-mono text-gray-500 cursor-not-allowed"
                                />
                                <p className="text-[9px] text-orange-500/60 font-medium italic">Primary identifier cannot be changed after creation.</p>
                            </div>

                            <div className="space-y-4">
                                <div className="space-y-2">
                                    <label className="text-xs font-bold text-gray-400 uppercase tracking-widest block">Domain</label>
                                    <select
                                        value={selectedBotDomainId}
                                        disabled
                                        className="w-full bg-white/5 border border-white/10 rounded-xl py-3 px-4 text-sm text-gray-500 cursor-not-allowed appearance-none"
                                    >
                                        <option value="">Global / No Specific Domain</option>
                                        {domains.map((dom: any) => (
                                            <option key={dom.id} value={dom.id}>{dom.name}</option>
                                        ))}
                                    </select>
                                    <p className="text-[9px] text-orange-500/60 font-medium italic">Domain scope is fixed. Delete bot and recreate to change domain.</p>
                                </div>

                                <AttributePreview
                                    domainId={selectedBotDomainId}
                                    definitions={attrDefinitions}
                                    isLoading={isLoadingAttrs}
                                />
                            </div>

                            <div className="flex gap-4 pt-4">
                                <button
                                    type="button"
                                    onClick={() => setIsSettingsModalOpen(false)}
                                    className="flex-1 py-3 bg-white/5 border border-white/10 rounded-xl text-sm font-bold text-gray-400 hover:bg-white/10 transition-all">
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    disabled={updateMutation.isPending || !newBotName.trim() || !newBotCode.trim()}
                                    className="flex-1 premium-gradient py-3 rounded-xl text-sm font-bold text-white shadow-lg transition-all hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50 disabled:scale-100">
                                    {updateMutation.isPending ? "Saving..." : "Save Settings"}
                                </button>
                            </div>
                        </form>
                    </GlassContainer>
                </div>
            )}
        </div>
    );
}
