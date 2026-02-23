"use client";

import GlassContainer from "@/components/ui/GlassContainer";
import { Users, Plus, Search, Filter, Edit3, Trash2, Shield, CheckCircle, XCircle } from "lucide-react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiService, Tenant } from "@/lib/apiService";
import { cn } from "@/lib/utils";
import { useState } from "react";

export default function TenantsPage() {
    const queryClient = useQueryClient();
    const [searchTerm, setSearchTerm] = useState("");
    const [filter, setFilter] = useState<"all" | "active" | "suspended">("all");
    const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
    const [newTenantName, setNewTenantName] = useState("");

    // Fetch Tenants
    const { data: tenants = [], isLoading, error } = useQuery({
        queryKey: ["tenants"],
        queryFn: () => apiService.listTenants(),
    });

    // Create Mutation
    const createMutation = useMutation({
        mutationFn: (name: string) => apiService.createTenant(name),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["tenants"] });
            setIsCreateModalOpen(false);
            setNewTenantName("");
        },
    });

    // Delete Mutation
    const deleteMutation = useMutation({
        mutationFn: (id: string) => apiService.deleteTenant(id),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["tenants"] });
        },
    });

    // Status Mutation
    const statusMutation = useMutation({
        mutationFn: ({ id, status }: { id: string; status: string }) =>
            apiService.updateTenantStatus(id, status),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["tenants"] });
        },
    });

    const filteredTenants = tenants.filter(t => {
        const matchesSearch = t.name.toLowerCase().includes(searchTerm.toLowerCase());
        const matchesFilter = filter === "all" || t.status === filter;
        return matchesSearch && matchesFilter;
    });

    const handleDelete = (id: string, name: string) => {
        if (confirm(`Bạn có chắc chắn muốn xóa Tenant "${name}" không?`)) {
            deleteMutation.mutate(id);
        }
    };

    const toggleStatus = (id: string, currentStatus: string) => {
        const newStatus = currentStatus === "active" ? "suspended" : "active";
        statusMutation.mutate({ id, status: newStatus });
    };

    const handleCreateSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (newTenantName.trim()) {
            createMutation.mutate(newTenantName.trim());
        }
    };

    const stats = {
        total: tenants.length,
        active: tenants.filter(t => t.status === "active").length,
        suspended: tenants.filter(t => t.status === "suspended").length,
        enterprise: tenants.filter(t => t.plan === "enterprise").length,
    };

    return (
        <div className="h-full flex flex-col space-y-6">
            <div className="flex items-center justify-between">
                <div className="flex flex-col">
                    <h1 className="text-2xl font-black text-white">Tenant Management</h1>
                    <p className="text-xs text-gray-500 font-bold uppercase tracking-[0.2em] mt-1">Multi-tenant Isolation & Access Control</p>
                </div>
                <div className="flex gap-3">
                    <button className="flex items-center gap-2 px-4 py-2 bg-white/5 border border-white/10 rounded-xl text-xs font-bold text-gray-400 hover:bg-white/10 transition-all">
                        <Filter className="w-4 h-4" /> Filter
                    </button>
                    <button
                        onClick={() => setIsCreateModalOpen(true)}
                        className="flex items-center gap-2 px-6 py-2 premium-gradient rounded-xl text-xs font-bold text-white shadow-lg transition-all hover:scale-[1.02] active:scale-[0.98]">
                        <Plus className="w-4 h-4" /> New Tenant
                    </button>
                </div>
            </div>

            {/* Stats Summary */}
            <div className="grid grid-cols-4 gap-6">
                <div className="p-6 bg-white/5 rounded-3xl border border-white/5 flex items-center gap-6">
                    <div className="w-14 h-14 rounded-2xl bg-accent/20 flex items-center justify-center text-accent">
                        <Users className="w-8 h-8" />
                    </div>
                    <div>
                        <div className="text-2xl font-black text-white">{stats.total}</div>
                        <div className="text-[10px] font-bold text-gray-500 uppercase tracking-widest">Total Tenants</div>
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
                        <XCircle className="w-8 h-8" />
                    </div>
                    <div>
                        <div className="text-2xl font-black text-white">{stats.suspended}</div>
                        <div className="text-[10px] font-bold text-gray-500 uppercase tracking-widest">Suspended</div>
                    </div>
                </div>
                <div className="p-6 bg-white/5 rounded-3xl border border-white/5 flex items-center gap-6">
                    <div className="w-14 h-14 rounded-2xl bg-purple-500/20 flex items-center justify-center text-purple-500">
                        <Shield className="w-8 h-8" />
                    </div>
                    <div>
                        <div className="text-2xl font-black text-white">{stats.enterprise}</div>
                        <div className="text-[10px] font-bold text-gray-500 uppercase tracking-widest">Enterprise</div>
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
                            )}>All Tenants</button>
                        <button
                            onClick={() => setFilter("active")}
                            className={cn(
                                "px-6 py-2 rounded-lg text-xs font-bold transition-all",
                                filter === "active" ? "bg-white/10 text-white" : "text-gray-500 hover:text-gray-300"
                            )}>Active Only</button>
                        <button
                            onClick={() => setFilter("suspended")}
                            className={cn(
                                "px-6 py-2 rounded-lg text-xs font-bold transition-all",
                                filter === "suspended" ? "bg-white/10 text-white" : "text-gray-500 hover:text-gray-300"
                            )}>Suspended</button>
                    </div>
                    <div className="flex gap-4">
                        <div className="relative">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                            <input
                                type="text"
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                placeholder="Search tenants..."
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
                            Error loading tenants. Please try again.
                        </div>
                    ) : (
                        <table className="w-full text-left">
                            <thead>
                                <tr className="text-[10px] font-black text-gray-500 uppercase tracking-widest border-b border-white/5">
                                    <th className="pb-4 pl-4 font-black">Tenant Name</th>
                                    <th className="pb-4 font-black">Status</th>
                                    <th className="pb-4 font-black">Plan</th>
                                    <th className="pb-4 font-black">Created</th>
                                    <th className="pb-4 font-black text-right pr-4">Actions</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-white/5">
                                {filteredTenants.map((item) => (
                                    <tr key={item.id} className="group hover:bg-white/[0.02] transition-colors">
                                        <td className="py-4 pl-4">
                                            <div className="text-sm font-bold text-gray-200">{item.name}</div>
                                            <div className="text-[10px] text-gray-500 font-medium font-mono">ID: {item.id}</div>
                                        </td>
                                        <td className="py-4">
                                            <button
                                                onClick={() => toggleStatus(item.id, item.status)}
                                                className={cn(
                                                    "px-2 py-0.5 rounded-md border text-[9px] font-bold uppercase transition-all",
                                                    item.status === "active"
                                                        ? "bg-green-500/10 border-green-500/30 text-green-500"
                                                        : "bg-orange-500/10 border-orange-500/30 text-orange-500"
                                                )}>{item.status}</button>
                                        </td>
                                        <td className="py-4">
                                            <span className="px-2 py-0.5 rounded-md bg-white/5 border border-white/10 text-[9px] font-bold text-gray-400 uppercase">{(item as any).plan || 'pro'}</span>
                                        </td>
                                        <td className="py-4">
                                            <div className="text-sm font-medium text-gray-400">{new Date(item.created_at).toLocaleDateString()}</div>
                                        </td>
                                        <td className="py-4 text-right pr-4">
                                            <div className="flex justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                                <button className="p-2 bg-white/5 rounded-lg border border-white/10 text-gray-400 hover:text-accent hover:border-accent/40">
                                                    <Edit3 className="w-3.5 h-3.5" />
                                                </button>
                                                <button
                                                    onClick={() => handleDelete(item.id, item.name)}
                                                    className="p-2 bg-white/5 rounded-lg border border-white/10 text-gray-400 hover:text-red-500 hover:border-red-500/40">
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

            {/* Create Tenant Modal */}
            {isCreateModalOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
                    <GlassContainer className="w-full max-w-md p-8 bg-white/10 border-white/10 shadow-2xl animate-in fade-in zoom-in duration-200">
                        <div className="flex items-center justify-between mb-8">
                            <h2 className="text-xl font-black text-white">Create New Tenant</h2>
                            <button
                                onClick={() => setIsCreateModalOpen(false)}
                                className="text-gray-400 hover:text-white transition-colors">
                                <XCircle className="w-6 h-6" />
                            </button>
                        </div>

                        <form onSubmit={handleCreateSubmit} className="space-y-6">
                            <div className="space-y-2">
                                <label className="text-xs font-bold text-gray-400 uppercase tracking-widest block">Tenant Name</label>
                                <input
                                    type="text"
                                    value={newTenantName}
                                    onChange={(e) => setNewTenantName(e.target.value)}
                                    placeholder="e.g. Acme Corporation"
                                    className="w-full bg-white/5 border border-white/10 rounded-xl py-3 px-4 text-sm text-gray-200 focus:outline-none focus:border-accent/50 transition-all"
                                    required
                                    autoFocus
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
                                    disabled={createMutation.isPending || !newTenantName.trim()}
                                    className="flex-1 premium-gradient py-3 rounded-xl text-sm font-bold text-white shadow-lg transition-all hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50 disabled:scale-100">
                                    {createMutation.isPending ? "Creating..." : "Create Tenant"}
                                </button>
                            </div>
                        </form>
                    </GlassContainer>
                </div>
            )}
        </div>
    );
}
