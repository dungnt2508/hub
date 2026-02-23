"use client";

import GlassContainer from "@/components/ui/GlassContainer";
import { BookOpen, Search, Plus, Trash2, Edit3, Zap, GitCompare, Layers, ShieldCheck, XCircle, Bot as BotIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiService, FAQ, UseCase, Comparison, Guardrail, Bot } from "@/lib/apiService";

type TabType = "faqs" | "usecases" | "comparisons" | "guardrails" | "cache";

export default function KnowledgePage() {
    const queryClient = useQueryClient();
    const [activeTab, setActiveTab] = useState<TabType>("faqs");
    const [selectedBotId, setSelectedBotId] = useState<string | null>(null);
    const [searchTerm, setSearchTerm] = useState("");

    // Modal states
    const [isFAQModalOpen, setIsFAQModalOpen] = useState(false);
    const [isUseCaseModalOpen, setIsUseCaseModalOpen] = useState(false);
    const [isComparisonModalOpen, setIsComparisonModalOpen] = useState(false);
    const [isGuardrailModalOpen, setIsGuardrailModalOpen] = useState(false);

    // Form states
    const [faqForm, setFaqForm] = useState<Partial<FAQ>>({ question: "", answer: "", category: "General", priority: 0 });
    const [useCaseForm, setUseCaseForm] = useState<Partial<UseCase>>({ scenario: "", answer: "", offering_id: "", priority: 0 });
    const [comparisonForm, setComparisonForm] = useState<Partial<Comparison>>({ title: "", description: "", offering_ids: [], comparison_data: {} });
    const [guardrailForm, setGuardrailForm] = useState<Partial<Guardrail>>({ code: "", name: "", condition_expression: "", violation_action: "block", fallback_message: "", priority: 0, is_active: true });
    const [editingId, setEditingId] = useState<string | null>(null);

    // Queries
    const { data: bots = [], isLoading: isBotsLoading } = useQuery({
        queryKey: ["bots", "active"],
        queryFn: () => apiService.listBots({ status: "active" }),
    });

    // Domain lấy từ bot đang chọn (không hiển thị domain selector)
    const effectiveDomainId = selectedBotId ? bots.find((b: Bot) => b.id === selectedBotId)?.domain_id ?? null : null;

    const { data: faqs = [], isLoading: isLoadingFAQs } = useQuery({
        queryKey: ["faqs", effectiveDomainId],
        queryFn: () => apiService.listFAQs(effectiveDomainId || undefined),
    });

    const { data: useCases = [], isLoading: isLoadingUseCases } = useQuery({
        queryKey: ["usecases", effectiveDomainId],
        queryFn: () => apiService.listUseCases(undefined, effectiveDomainId || undefined),
    });

    const { data: comparisons = [], isLoading: isLoadingComparisons } = useQuery({
        queryKey: ["comparisons", effectiveDomainId],
        queryFn: () => apiService.listComparisons(effectiveDomainId || undefined),
    });

    const { data: guardrails = [], isLoading: isLoadingGuardrails } = useQuery({
        queryKey: ["guardrails"],
        queryFn: () => apiService.listGuardrails(),
    });

    const { data: cacheEntries = [] } = useQuery({
        queryKey: ["semantic-cache"],
        queryFn: () => apiService.listCache(),
        enabled: activeTab === "cache",
    });

    const { data: offerings = [] } = useQuery({
        queryKey: ["catalog-offerings-minimal"],
        queryFn: () => apiService.listOfferings(),
    });

    // Mutations
    const faqMutation = useMutation({
        mutationFn: (data: Partial<FAQ>) => editingId ? apiService.updateFAQ(editingId, data) : apiService.createFAQ({ ...data, domain_id: effectiveDomainId || undefined }),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["faqs"] });
            setIsFAQModalOpen(false);
            setFaqForm({ question: "", answer: "", category: "General", priority: 0 });
            setEditingId(null);
        }
    });

    const deleteFAQMutation = useMutation({
        mutationFn: (id: string) => apiService.deleteFAQ(id),
        onSuccess: () => queryClient.invalidateQueries({ queryKey: ["faqs"] })
    });

    const useCaseMutation = useMutation({
        mutationFn: (data: Partial<UseCase>) => {
            const payload = { ...data, domain_id: effectiveDomainId || undefined };
            if (payload.offering_id === "") payload.offering_id = undefined;
            return editingId ? apiService.updateUseCase(editingId, payload) : apiService.createUseCase(payload);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["usecases"] });
            setIsUseCaseModalOpen(false);
            setUseCaseForm({ scenario: "", answer: "", offering_id: "", priority: 0 });
            setEditingId(null);
        }
    });

    const deleteUseCaseMutation = useMutation({
        mutationFn: (id: string) => apiService.deleteUseCase(id),
        onSuccess: () => queryClient.invalidateQueries({ queryKey: ["usecases"] })
    });

    const comparisonMutation = useMutation({
        mutationFn: (data: Partial<Comparison>) => editingId ? apiService.updateComparison(editingId, data) : apiService.createComparison({ ...data, domain_id: effectiveDomainId || undefined }),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["comparisons"] });
            setIsComparisonModalOpen(false);
            setComparisonForm({ title: "", description: "", offering_ids: [], comparison_data: {} });
            setEditingId(null);
        }
    });

    const deleteComparisonMutation = useMutation({
        mutationFn: (id: string) => apiService.deleteComparison(id),
        onSuccess: () => queryClient.invalidateQueries({ queryKey: ["comparisons"] })
    });

    const guardrailMutation = useMutation({
        mutationFn: (data: Partial<Guardrail>) => editingId ? apiService.updateGuardrail(editingId, data) : apiService.createGuardrail(data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["guardrails"] });
            setIsGuardrailModalOpen(false);
            setGuardrailForm({ code: "", name: "", condition_expression: "", violation_action: "block", fallback_message: "", priority: 0, is_active: true });
            setEditingId(null);
        }
    });

    const deleteGuardrailMutation = useMutation({
        mutationFn: (id: string) => apiService.deleteGuardrail(id),
        onSuccess: () => queryClient.invalidateQueries({ queryKey: ["guardrails"] })
    });

    // Handlers
    const handleEditFAQ = (faq: FAQ) => {
        setFaqForm(faq);
        setEditingId(faq.id);
        setIsFAQModalOpen(true);
    };

    const handleEditUseCase = (uc: UseCase) => {
        setUseCaseForm(uc);
        setEditingId(uc.id);
        setIsUseCaseModalOpen(true);
    };

    const handleEditComparison = (comp: Comparison) => {
        setComparisonForm(comp);
        setEditingId(comp.id);
        setIsComparisonModalOpen(true);
    };

    const handleEditGuardrail = (g: Guardrail) => {
        setGuardrailForm(g);
        setEditingId(g.id);
        setIsGuardrailModalOpen(true);
    };

    const toggleComparisonOffering = (offeringId: string) => {
        const ids = comparisonForm.offering_ids || [];
        if (ids.includes(offeringId)) {
            setComparisonForm({ ...comparisonForm, offering_ids: ids.filter(id => id !== offeringId) });
        } else {
            setComparisonForm({ ...comparisonForm, offering_ids: [...ids, offeringId] });
        }
    };

    // Auto-select first bot when none selected (like Catalog)
    useEffect(() => {
        if (!selectedBotId && bots.length > 0) {
            setSelectedBotId(bots[0].id);
        }
    }, [bots, selectedBotId]);

    const filteredFAQs = faqs.filter(f => f.question.toLowerCase().includes(searchTerm.toLowerCase()) || f.answer.toLowerCase().includes(searchTerm.toLowerCase()));
    const filteredUseCases = useCases.filter(u => u.scenario.toLowerCase().includes(searchTerm.toLowerCase()) || u.answer.toLowerCase().includes(searchTerm.toLowerCase()));
    const filteredGuardrails = guardrails.filter(g => g.code.toLowerCase().includes(searchTerm.toLowerCase()) || g.name.toLowerCase().includes(searchTerm.toLowerCase()));

    return (
        <div className="h-full flex flex-col space-y-6 overflow-y-auto no-scrollbar pb-10">
            <div className="flex items-center justify-between">
                <div className="flex flex-col">
                    <h1 className="text-2xl font-black text-white">Knowledge Base</h1>
                    <p className="text-xs text-gray-500 font-bold uppercase tracking-[0.2em] mt-1">FAQ, Use Cases & AI Training</p>
                </div>
            </div>

            {/* Stats Summary */}
            <div className="grid grid-cols-4 gap-6">
                <div className="p-6 bg-white/5 rounded-3xl border border-white/5 flex items-center gap-6">
                    <div className="w-14 h-14 rounded-2xl bg-accent/20 flex items-center justify-center text-accent">
                        <BookOpen className="w-8 h-8" />
                    </div>
                    <div>
                        <div className="text-2xl font-black text-white">{faqs.length}</div>
                        <div className="text-[10px] font-bold text-gray-500 uppercase tracking-widest">FAQs</div>
                    </div>
                </div>
                <div className="p-6 bg-white/5 rounded-3xl border border-white/5 flex items-center gap-6">
                    <div className="w-14 h-14 rounded-2xl bg-purple-500/20 flex items-center justify-center text-purple-500">
                        <Layers className="w-8 h-8" />
                    </div>
                    <div>
                        <div className="text-2xl font-black text-white">{useCases.length}</div>
                        <div className="text-[10px] font-bold text-gray-500 uppercase tracking-widest">Use Cases</div>
                    </div>
                </div>
                <div className="p-6 bg-white/5 rounded-3xl border border-white/5 flex items-center gap-6">
                    <div className="w-14 h-14 rounded-2xl bg-orange-500/20 flex items-center justify-center text-orange-500">
                        <GitCompare className="w-8 h-8" />
                    </div>
                    <div>
                        <div className="text-2xl font-black text-white">{comparisons.length}</div>
                        <div className="text-[10px] font-bold text-gray-500 uppercase tracking-widest">Comparisons</div>
                    </div>
                </div>
                <div className="p-6 bg-white/5 rounded-3xl border border-white/5 flex items-center gap-6">
                    <div className="w-14 h-14 rounded-2xl bg-cyan-500/20 flex items-center justify-center text-cyan-500">
                        <Zap className="w-8 h-8" />
                    </div>
                    <div>
                        <div className="text-2xl font-black text-white">{cacheEntries.length || 0}</div>
                        <div className="text-[10px] font-bold text-gray-500 uppercase tracking-widest">Cache Hits</div>
                    </div>
                </div>
            </div>

            {/* Bot & Domain Selector - placed here (after Stats, before Main) like Catalog */}
            <GlassContainer className="w-full p-4 flex flex-col sm:flex-row sm:items-center gap-4 bg-white/5 border-white/5">
                <div className="flex items-center gap-4 flex-wrap">
                    <h3 className="text-[10px] font-black text-white uppercase tracking-widest border-r border-white/10 pr-4 py-1">Chọn Bot</h3>
                    <div className="flex gap-2 overflow-x-auto no-scrollbar py-1">
                        {isBotsLoading ? (
                            <div className="py-2"><div className="animate-spin rounded-full h-4 w-4 border-b-2 border-accent"></div></div>
                        ) : bots.map((bot: Bot) => (
                            <button
                                key={bot.id}
                                onClick={() => setSelectedBotId(bot.id)}
                                className={cn(
                                    "min-w-[120px] p-3 rounded-2xl flex items-center gap-3 group transition-all text-left",
                                    selectedBotId === bot.id ? "bg-accent/10 border border-accent/30" : "bg-white/5 border border-white/5 hover:bg-white/10"
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

            {/* Main Area */}
            <GlassContainer className="flex-1 p-8 flex flex-col bg-white/5 border-white/5 min-h-[500px]">
                <div className="flex items-center justify-between mb-8">
                    <div className="flex bg-white/5 p-1 rounded-xl">
                        <button
                            onClick={() => setActiveTab("faqs")}
                            className={cn(
                                "px-6 py-2 rounded-lg text-xs font-bold transition-all",
                                activeTab === "faqs" ? "bg-white/10 text-white shadow-sm" : "text-gray-500 hover:text-gray-300"
                            )}>FAQs</button>
                        <button
                            onClick={() => setActiveTab("usecases")}
                            className={cn(
                                "px-6 py-2 rounded-lg text-xs font-bold transition-all",
                                activeTab === "usecases" ? "bg-white/10 text-white shadow-sm" : "text-gray-500 hover:text-gray-300"
                            )}>Use Cases</button>
                        <button
                            onClick={() => setActiveTab("comparisons")}
                            className={cn(
                                "px-6 py-2 rounded-lg text-xs font-bold transition-all",
                                activeTab === "comparisons" ? "bg-white/10 text-white shadow-sm" : "text-gray-500 hover:text-gray-300"
                            )}>Comparisons</button>
                        <button
                            onClick={() => setActiveTab("guardrails")}
                            className={cn(
                                "px-6 py-2 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5",
                                activeTab === "guardrails" ? "bg-white/10 text-white shadow-sm" : "text-gray-500 hover:text-gray-300"
                            )}><ShieldCheck className="w-3.5 h-3.5" /> Quy tắc An toàn</button>
                        <button
                            onClick={() => setActiveTab("cache")}
                            className={cn(
                                "px-6 py-2 rounded-lg text-xs font-bold transition-all",
                                activeTab === "cache" ? "bg-white/10 text-white shadow-sm" : "text-gray-500 hover:text-gray-300"
                            )}>Semantic Cache</button>
                    </div>
                    <div className="flex gap-4">
                        <div className="relative">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                            <input
                                type="text"
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                placeholder="Search..."
                                className="bg-white/5 border border-white/10 rounded-xl py-2 pl-10 pr-4 text-xs focus:outline-none focus:border-accent/40 w-64 text-gray-300" />
                        </div>
                        {activeTab !== "cache" && (
                            <button
                                onClick={() => {
                                    setEditingId(null);
                                    if (activeTab === "faqs") {
                                        setFaqForm({ question: "", answer: "", category: "General", priority: 0 });
                                        setIsFAQModalOpen(true);
                                    } else if (activeTab === "usecases") {
                                        setUseCaseForm({ scenario: "", answer: "", offering_id: "", priority: 0 });
                                        setIsUseCaseModalOpen(true);
                                    } else if (activeTab === "guardrails") {
                                        setGuardrailForm({ code: "", name: "", condition_expression: "", violation_action: "block", fallback_message: "", priority: 0, is_active: true });
                                        setIsGuardrailModalOpen(true);
                                    } else if (activeTab === "comparisons") {
                                        setComparisonForm({ title: "", description: "", offering_ids: [], comparison_data: {} });
                                        setIsComparisonModalOpen(true);
                                    }
                                }}
                                className="px-4 py-2 premium-gradient rounded-xl text-xs font-bold text-white flex items-center gap-2">
                                <Plus className="w-4 h-4" /> Add New
                            </button>
                        )}
                    </div>
                </div>

                <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar">
                    {activeTab === "faqs" && (
                        <div className="space-y-3">
                            {isLoadingFAQs ? (
                                <div className="py-20 text-center text-gray-500 animate-pulse">Loading FAQs...</div>
                            ) : filteredFAQs.length === 0 ? (
                                <div className="py-20 text-center text-gray-500 italic">No FAQs found for this domain</div>
                            ) : (
                                filteredFAQs.map((faq) => (
                                    <div key={faq.id} className="p-4 bg-white/5 border border-white/5 rounded-2xl group hover:border-accent/40 transition-all">
                                        <div className="flex justify-between items-start mb-2">
                                            <div className="flex items-center gap-3">
                                                <span className="px-2 py-0.5 bg-accent/10 text-accent text-[9px] font-black uppercase rounded">{faq.category}</span>
                                                <div className="text-sm font-bold text-white">{faq.question}</div>
                                            </div>
                                            <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                                <button onClick={() => handleEditFAQ(faq)} className="p-1.5 hover:text-accent"><Edit3 className="w-3.5 h-3.5" /></button>
                                                <button onClick={() => { if (confirm("Delete this FAQ?")) deleteFAQMutation.mutate(faq.id) }} className="p-1.5 hover:text-red-500"><Trash2 className="w-3.5 h-3.5" /></button>
                                            </div>
                                        </div>
                                        <div className="text-xs text-gray-400 leading-relaxed pl-4 border-l-2 border-white/10">{faq.answer}</div>
                                    </div>
                                ))
                            )}
                        </div>
                    )}

                    {activeTab === "usecases" && (
                        <div className="space-y-4">
                            {isLoadingUseCases ? (
                                <div className="py-20 text-center text-gray-500 animate-pulse">Loading Use Cases...</div>
                            ) : filteredUseCases.length === 0 ? (
                                <div className="py-20 text-center text-gray-500 italic">No Use Cases found</div>
                            ) : (
                                filteredUseCases.map((uc) => (
                                    <div key={uc.id} className="p-5 bg-purple-500/5 border border-purple-500/10 rounded-2xl group hover:border-purple-500/40 transition-all">
                                        <div className="flex justify-between items-start mb-3">
                                            <div>
                                                <div className="text-[10px] font-black text-purple-500 uppercase tracking-widest mb-1">Scenario</div>
                                                <div className="text-xs font-bold text-white">{uc.scenario}</div>
                                            </div>
                                            <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                                <button onClick={() => handleEditUseCase(uc)} className="p-1.5 hover:text-purple-500"><Edit3 className="w-3.5 h-3.5" /></button>
                                                <button onClick={() => { if (confirm("Delete this Use Case?")) deleteUseCaseMutation.mutate(uc.id) }} className="p-1.5 hover:text-red-500"><Trash2 className="w-3.5 h-3.5" /></button>
                                            </div>
                                        </div>
                                        <div className="bg-black/20 p-3 rounded-xl">
                                            <div className="text-[10px] font-black text-purple-500 uppercase tracking-widest mb-1">Expected Response</div>
                                            <div className="text-xs text-gray-400 italic">{uc.answer}</div>
                                        </div>
                                        {uc.offering_id && (
                                            <div className="mt-3 flex items-center gap-2">
                                                <span className="text-[8px] font-bold text-gray-500 uppercase">Linked Offering:</span>
                                                <span className="text-[9px] text-gray-300 font-mono">{offerings.find(o => o.id === uc.offering_id)?.name || uc.offering_id}</span>
                                            </div>
                                        )}
                                    </div>
                                ))
                            )}
                        </div>
                    )}

                    {activeTab === "comparisons" && (
                        <div className="grid grid-cols-2 gap-4">
                            {isLoadingComparisons ? (
                                <div className="col-span-2 py-20 text-center text-gray-500 animate-pulse">Loading Comparisons...</div>
                            ) : comparisons.length === 0 ? (
                                <div className="col-span-2 py-20 text-center text-gray-500 italic">No comparison tables found</div>
                            ) : (
                                comparisons.map((comp) => (
                                    <div key={comp.id} className="p-5 bg-orange-500/5 border border-orange-500/10 rounded-2xl group hover:border-orange-500/40 transition-all">
                                        <div className="flex justify-between items-start mb-2">
                                            <h4 className="text-sm font-bold text-white">{comp.title}</h4>
                                            <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                                <button onClick={() => handleEditComparison(comp)} className="p-1.5 hover:text-orange-500"><Edit3 className="w-3.5 h-3.5" /></button>
                                                <button onClick={() => { if (confirm("Delete this comparison?")) deleteComparisonMutation.mutate(comp.id) }} className="p-1.5 hover:text-red-500"><Trash2 className="w-3.5 h-3.5" /></button>
                                            </div>
                                        </div>
                                        <p className="text-[10px] text-gray-500 mb-4 line-clamp-2">{comp.description}</p>
                                        <div className="flex flex-wrap gap-2">
                                            {comp.offering_ids.map(oid => (
                                                <span key={oid} className="px-2 py-0.5 bg-white/5 rounded text-[8px] text-gray-400 font-mono">
                                                    {offerings.find(o => o.id === oid)?.code || "Offering"}
                                                </span>
                                            ))}
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    )}

                    {activeTab === "guardrails" && (
                        <div className="space-y-3">
                            {isLoadingGuardrails ? (
                                <div className="py-20 text-center text-gray-500 animate-pulse">Loading Quy tắc An toàn...</div>
                            ) : filteredGuardrails.length === 0 ? (
                                <div className="py-20 text-center text-gray-500 italic">Chưa có quy tắc nào</div>
                            ) : (
                                filteredGuardrails.map((g) => (
                                    <div key={g.id} className="p-5 bg-emerald-500/5 border border-emerald-500/10 rounded-2xl group hover:border-emerald-500/40 transition-all">
                                        <div className="flex justify-between items-start mb-3">
                                            <div className="flex items-center gap-3">
                                                <span className="px-2 py-0.5 bg-emerald-500/20 text-emerald-400 text-[9px] font-black uppercase rounded">{g.code}</span>
                                                <div className="text-sm font-bold text-white">{g.name}</div>
                                                {!g.is_active && <span className="text-[9px] text-gray-500 italic">(Tắt)</span>}
                                            </div>
                                            <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                                <button onClick={() => handleEditGuardrail(g)} className="p-1.5 hover:text-emerald-500"><Edit3 className="w-3.5 h-3.5" /></button>
                                                <button onClick={() => { if (confirm("Xóa quy tắc này?")) deleteGuardrailMutation.mutate(g.id) }} className="p-1.5 hover:text-red-500"><Trash2 className="w-3.5 h-3.5" /></button>
                                            </div>
                                        </div>
                                        <div className="bg-black/20 p-3 rounded-xl space-y-2">
                                            <div><span className="text-[10px] font-black text-emerald-500 uppercase">Điều kiện:</span><p className="text-xs text-gray-400 font-mono mt-0.5">{g.condition_expression}</p></div>
                                            <div className="flex gap-4">
                                                <span className="text-[9px] text-gray-500">Action: <span className="text-gray-400">{g.violation_action}</span></span>
                                                <span className="text-[9px] text-gray-500">Ưu tiên: <span className="text-gray-400">{g.priority}</span></span>
                                            </div>
                                            {g.fallback_message && <p className="text-[10px] text-gray-500 italic">Fallback: {g.fallback_message}</p>}
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    )}

                    {activeTab === "cache" && (
                        <div className="space-y-2">
                            {cacheEntries.length === 0 ? (
                                <div className="py-20 text-center text-gray-500 italic">Semantic cache is empty</div>
                            ) : (
                                cacheEntries.map((entry, idx) => (
                                    <div key={idx} className="p-4 bg-white/5 border border-white/5 rounded-xl flex items-center justify-between group">
                                        <div className="flex-1">
                                            <div className="text-[10px] font-bold text-cyan-500 uppercase tracking-tighter mb-1 select-none">Query</div>
                                            <div className="text-xs text-white line-clamp-1">{entry.query_text}</div>
                                        </div>
                                        <div className="w-px h-8 bg-white/10 mx-6" />
                                        <div className="flex-1">
                                            <div className="text-[10px] font-bold text-cyan-500 uppercase tracking-tighter mb-1 select-none">Cached Response</div>
                                            <div className="text-xs text-gray-400 line-clamp-1">{entry.response_text}</div>
                                        </div>
                                        <button className="ml-4 p-2 opacity-0 group-hover:opacity-100 text-gray-500 hover:text-red-500 transition-all">
                                            <Trash2 className="w-3.5 h-3.5" />
                                        </button>
                                    </div>
                                ))
                            )}
                        </div>
                    )}
                </div>
            </GlassContainer>

            {/* Modals */}
            {isFAQModalOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
                    <GlassContainer className="w-full max-w-lg p-8 bg-[#0A0A0A] border-white/10 shadow-2xl">
                        <div className="flex items-center justify-between mb-6">
                            <h3 className="text-xl font-black text-white">{editingId ? "Edit FAQ" : "New FAQ Item"}</h3>
                            <button onClick={() => setIsFAQModalOpen(false)} className="text-gray-500 hover:text-white"><XCircle /></button>
                        </div>
                        <form onSubmit={(e) => { e.preventDefault(); faqMutation.mutate(faqForm) }} className="space-y-4">
                            <div>
                                <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest block mb-2">Question</label>
                                <input
                                    required
                                    value={faqForm.question}
                                    onChange={(e) => setFaqForm({ ...faqForm, question: e.target.value })}
                                    className="w-full bg-white/5 border border-white/10 rounded-xl p-3 text-sm text-white focus:outline-none focus:border-accent" />
                            </div>
                            <div>
                                <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest block mb-2">Answer</label>
                                <textarea
                                    required
                                    rows={4}
                                    value={faqForm.answer}
                                    onChange={(e) => setFaqForm({ ...faqForm, answer: e.target.value })}
                                    className="w-full bg-white/5 border border-white/10 rounded-xl p-3 text-sm text-white focus:outline-none focus:border-accent resize-none" />
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest block mb-2">Category</label>
                                    <input
                                        value={faqForm.category}
                                        onChange={(e) => setFaqForm({ ...faqForm, category: e.target.value })}
                                        className="w-full bg-white/5 border border-white/10 rounded-xl p-3 text-sm text-white focus:outline-none focus:border-accent" />
                                </div>
                                <div>
                                    <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest block mb-2">Priority</label>
                                    <input
                                        type="number"
                                        value={faqForm.priority}
                                        onChange={(e) => setFaqForm({ ...faqForm, priority: parseInt(e.target.value) })}
                                        className="w-full bg-white/5 border border-white/10 rounded-xl p-3 text-sm text-white focus:outline-none focus:border-accent" />
                                </div>
                            </div>
                            <button
                                disabled={faqMutation.isPending}
                                className="w-full py-4 premium-gradient rounded-xl text-sm font-black text-white shadow-lg mt-4 disabled:opacity-50">
                                {faqMutation.isPending ? "Saving..." : "Save FAQ Item"}
                            </button>
                        </form>
                    </GlassContainer>
                </div>
            )}

            {isUseCaseModalOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
                    <GlassContainer className="w-full max-w-lg p-8 bg-[#0A0A0A] border-white/10 shadow-2xl">
                        <div className="flex items-center justify-between mb-6">
                            <h3 className="text-xl font-black text-white">{editingId ? "Edit Use Case" : "New Use Case"}</h3>
                            <button onClick={() => setIsUseCaseModalOpen(false)} className="text-gray-500 hover:text-white"><XCircle /></button>
                        </div>
                        <form onSubmit={(e) => { e.preventDefault(); useCaseMutation.mutate(useCaseForm) }} className="space-y-4">
                            <div>
                                <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest block mb-2">Scenario / Question</label>
                                <textarea
                                    required
                                    rows={2}
                                    value={useCaseForm.scenario}
                                    onChange={(e) => setUseCaseForm({ ...useCaseForm, scenario: e.target.value })}
                                    className="w-full bg-white/5 border border-white/10 rounded-xl p-3 text-sm text-white focus:outline-none focus:border-accent resize-none" />
                            </div>
                            <div>
                                <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest block mb-2">Expected Response</label>
                                <textarea
                                    required
                                    rows={4}
                                    value={useCaseForm.answer}
                                    onChange={(e) => setUseCaseForm({ ...useCaseForm, answer: e.target.value })}
                                    className="w-full bg-white/5 border border-white/10 rounded-xl p-3 text-sm text-white focus:outline-none focus:border-accent resize-none" />
                            </div>
                            <div>
                                <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest block mb-2">Link with Offering (Optional)</label>
                                <select
                                    value={useCaseForm.offering_id}
                                    onChange={(e) => setUseCaseForm({ ...useCaseForm, offering_id: e.target.value })}
                                    className="w-full bg-white/5 border border-white/10 rounded-xl p-3 text-sm text-white focus:outline-none focus:border-accent appearance-none">
                                    <option value="">No Offering Link</option>
                                    {offerings.map((o) => (
                                        <option key={o.id} value={o.id}>{o.name} ({o.code})</option>
                                    ))}
                                </select>
                            </div>
                            <button
                                disabled={useCaseMutation.isPending}
                                className="w-full py-4 bg-purple-600 rounded-xl text-sm font-black text-white shadow-lg mt-4 disabled:opacity-50">
                                {useCaseMutation.isPending ? "Saving..." : "Save Use Case"}
                            </button>
                        </form>
                    </GlassContainer>
                </div>
            )}
            {isComparisonModalOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
                    <GlassContainer className="w-full max-w-2xl p-8 bg-[#0A0A0A] border-white/10 shadow-2xl overflow-y-auto max-h-[90vh]">
                        <div className="flex items-center justify-between mb-6">
                            <h3 className="text-xl font-black text-white">{editingId ? "Edit Comparison" : "New Comparison Table"}</h3>
                            <button onClick={() => setIsComparisonModalOpen(false)} className="text-gray-500 hover:text-white"><XCircle /></button>
                        </div>
                        <form onSubmit={(e) => { e.preventDefault(); comparisonMutation.mutate(comparisonForm) }} className="space-y-6">
                            <div className="grid grid-cols-2 gap-6">
                                <div className="space-y-4">
                                    <div>
                                        <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest block mb-2">Table Title</label>
                                        <input
                                            required
                                            value={comparisonForm.title}
                                            onChange={(e) => setComparisonForm({ ...comparisonForm, title: e.target.value })}
                                            className="w-full bg-white/5 border border-white/10 rounded-xl p-3 text-sm text-white focus:outline-none focus:border-orange-500" />
                                    </div>
                                    <div>
                                        <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest block mb-2">Description</label>
                                        <textarea
                                            rows={3}
                                            value={comparisonForm.description}
                                            onChange={(e) => setComparisonForm({ ...comparisonForm, description: e.target.value })}
                                            className="w-full bg-white/5 border border-white/10 rounded-xl p-3 text-sm text-white focus:outline-none focus:border-orange-500 resize-none" />
                                    </div>
                                </div>
                                <div>
                                    <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest block mb-2">Select Offerings (Max 3)</label>
                                    <div className="grid grid-cols-1 gap-2 max-h-48 overflow-y-auto pr-2 custom-scrollbar">
                                        {offerings.map(o => (
                                            <button
                                                key={o.id}
                                                type="button"
                                                onClick={() => toggleComparisonOffering(o.id)}
                                                className={cn(
                                                    "p-3 rounded-xl border text-[10px] font-bold text-left transition-all",
                                                    comparisonForm.offering_ids?.includes(o.id)
                                                        ? "bg-orange-500/20 border-orange-500/50 text-white"
                                                        : "bg-white/5 border-white/10 text-gray-500 hover:border-white/20"
                                                )}>
                                                {o.name} ({o.code})
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            </div>

                            <div>
                                <div className="flex items-center justify-between mb-4">
                                    <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest">Comparison Attributes</label>
                                    <button
                                        type="button"
                                        onClick={() => {
                                            const key = prompt("Enter attribute name (e.g. Battery, Price, screen):");
                                            if (key) setComparisonForm({ ...comparisonForm, comparison_data: { ...comparisonForm.comparison_data, [key]: "" } });
                                        }}
                                        className="text-[9px] font-black text-orange-500 uppercase hover:underline">+ Add Row</button>
                                </div>
                                <div className="space-y-2">
                                    {Object.entries(comparisonForm.comparison_data || {}).map(([key, val]) => (
                                        <div key={key} className="flex items-center gap-2">
                                            <div className="w-1/3 bg-black/40 p-3 rounded-xl text-[10px] font-black text-orange-500 uppercase">{key}</div>
                                            <input
                                                value={String(val)}
                                                onChange={(e) => setComparisonForm({ ...comparisonForm, comparison_data: { ...comparisonForm.comparison_data, [key]: e.target.value } })}
                                                className="flex-1 bg-white/5 border border-white/10 rounded-xl p-3 text-xs text-white focus:outline-none focus:border-orange-500" />
                                            <button
                                                type="button"
                                                onClick={() => {
                                                    const newData = { ...comparisonForm.comparison_data };
                                                    delete newData[key];
                                                    setComparisonForm({ ...comparisonForm, comparison_data: newData });
                                                }}
                                                className="p-2 text-gray-500 hover:text-red-500"><Trash2 className="w-4 h-4" /></button>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            <button
                                disabled={comparisonMutation.isPending}
                                className="w-full py-4 bg-orange-600 rounded-xl text-sm font-black text-white shadow-lg mt-4 disabled:opacity-50">
                                {comparisonMutation.isPending ? "Saving..." : "Save Comparison Table"}
                            </button>
                        </form>
                    </GlassContainer>
                </div>
            )}

            {isGuardrailModalOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
                    <GlassContainer className="w-full max-w-lg p-8 bg-[#0A0A0A] border-white/10 shadow-2xl">
                        <div className="flex items-center justify-between mb-6">
                            <h3 className="text-xl font-black text-white flex items-center gap-2"><ShieldCheck className="w-5 h-5 text-emerald-500" />{editingId ? "Chỉnh sửa Quy tắc" : "Thêm Quy tắc An toàn"}</h3>
                            <button onClick={() => setIsGuardrailModalOpen(false)} className="text-gray-500 hover:text-white"><XCircle /></button>
                        </div>
                        <form onSubmit={(e) => { e.preventDefault(); guardrailMutation.mutate(guardrailForm) }} className="space-y-4">
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest block mb-2">Code</label>
                                    <input
                                        required
                                        disabled={!!editingId}
                                        value={guardrailForm.code}
                                        onChange={(e) => setGuardrailForm({ ...guardrailForm, code: e.target.value })}
                                        placeholder="no_pii"
                                        className="w-full bg-white/5 border border-white/10 rounded-xl p-3 text-sm text-white focus:outline-none focus:border-emerald-500 disabled:opacity-60" />
                                </div>
                                <div>
                                    <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest block mb-2">Tên</label>
                                    <input
                                        required
                                        value={guardrailForm.name}
                                        onChange={(e) => setGuardrailForm({ ...guardrailForm, name: e.target.value })}
                                        placeholder="Cấm tiết lộ thông tin cá nhân"
                                        className="w-full bg-white/5 border border-white/10 rounded-xl p-3 text-sm text-white focus:outline-none focus:border-emerald-500" />
                                </div>
                            </div>
                            <div>
                                <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest block mb-2">Condition (Biểu thức điều kiện)</label>
                                <textarea
                                    required
                                    rows={3}
                                    value={guardrailForm.condition_expression}
                                    onChange={(e) => setGuardrailForm({ ...guardrailForm, condition_expression: e.target.value })}
                                    placeholder="contains_pii(response) hoặc regex..."
                                    className="w-full bg-white/5 border border-white/10 rounded-xl p-3 text-sm text-white font-mono focus:outline-none focus:border-emerald-500 resize-none" />
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest block mb-2">Violation Action</label>
                                    <select
                                        value={guardrailForm.violation_action}
                                        onChange={(e) => setGuardrailForm({ ...guardrailForm, violation_action: e.target.value })}
                                        className="w-full bg-white/5 border border-white/10 rounded-xl p-3 text-sm text-white focus:outline-none focus:border-emerald-500 appearance-none">
                                        <option value="block">Block</option>
                                        <option value="warn">Warn</option>
                                        <option value="fallback">Fallback</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest block mb-2">Priority</label>
                                    <input
                                        type="number"
                                        value={guardrailForm.priority}
                                        onChange={(e) => setGuardrailForm({ ...guardrailForm, priority: parseInt(e.target.value) || 0 })}
                                        className="w-full bg-white/5 border border-white/10 rounded-xl p-3 text-sm text-white focus:outline-none focus:border-emerald-500" />
                                </div>
                            </div>
                            <div>
                                <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest block mb-2">Fallback Message (tùy chọn)</label>
                                <input
                                    value={guardrailForm.fallback_message || ""}
                                    onChange={(e) => setGuardrailForm({ ...guardrailForm, fallback_message: e.target.value || undefined })}
                                    placeholder="Xin lỗi, tôi không thể trả lời câu hỏi này."
                                    className="w-full bg-white/5 border border-white/10 rounded-xl p-3 text-sm text-white focus:outline-none focus:border-emerald-500" />
                            </div>
                            <label className="flex items-center gap-2 cursor-pointer">
                                <input
                                    type="checkbox"
                                    checked={guardrailForm.is_active ?? true}
                                    onChange={(e) => setGuardrailForm({ ...guardrailForm, is_active: e.target.checked })}
                                    className="rounded bg-white/5 border-white/10" />
                                <span className="text-xs font-bold text-gray-400">Kích hoạt</span>
                            </label>
                            <button
                                disabled={guardrailMutation.isPending}
                                className="w-full py-4 bg-emerald-600 rounded-xl text-sm font-black text-white shadow-lg mt-4 disabled:opacity-50">
                                {guardrailMutation.isPending ? "Đang lưu..." : "Lưu Quy tắc"}
                            </button>
                        </form>
                    </GlassContainer>
                </div>
            )}
        </div>
    );
}

