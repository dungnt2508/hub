import { Save, Archive, RotateCcw, Trash2, Layers, FileText, Tag, Edit3, Plus } from "lucide-react";
import { cn } from "@/lib/utils";
import GlassContainer from "@/components/ui/GlassContainer";
import { TenantOffering } from "@/lib/apiService";
import { useState } from "react";
import VariantManager from "./VariantManager";

interface OfferingDetailProps {
    offering: TenantOffering;
    versions: any[];
    currentVersionId: string | null;
    offeringAttributes: any[];

    // Actions
    onUpdateOffering: () => void;
    onDeleteOffering: () => void;
    onArchiveOffering: (archive: boolean) => void;
    onVersionChange: (versionId: string) => void;

    // Form Linkage
    offeringForm: any;
    setOfferingForm: (f: any) => void;

    // Variant Actions
    selectedChannel: string;
    onAddSku: () => void;
    onEditSku: (id: string, sku: string, name: string, qty: number, loc: string) => void;
    onDeleteSku: (id: string) => void;
    onSetPrice: (id: string, price: any) => void;

    // Attrib Actions
    onAddAttribute: () => void;
    onDeleteAttribute: (id: string) => void;

    // Version Actions
    onCreateVersion: () => void;
    onPublishVersion: (version: number) => void;
    onEditVersion: (v: any) => void;
    onDeleteVersion: (id: string) => void;

    isSaving: boolean;
}

type TabType = "overview" | "variants" | "attributes" | "history";

export default function OfferingDetail({
    offering,
    versions,
    currentVersionId,
    offeringAttributes,
    onUpdateOffering,
    onDeleteOffering,
    onArchiveOffering,
    onVersionChange,
    offeringForm,
    setOfferingForm,
    selectedChannel,
    onAddSku,
    onEditSku,
    onDeleteSku,
    onSetPrice,
    onAddAttribute,
    onDeleteAttribute,
    onCreateVersion,
    onPublishVersion,
    onEditVersion,
    onDeleteVersion,
    isSaving
}: OfferingDetailProps) {
    const [activeTab, setActiveTab] = useState<TabType>("overview");

    const filteredVersions = versions.sort((a: any, b: any) => b.version - a.version);
    const currentVersion = versions.find(v => v.id === currentVersionId);

    return (
        <GlassContainer className="col-span-1 md:col-span-8 p-6 md:p-8 flex flex-col bg-white/5 border-white/5 overflow-hidden min-h-[600px] md:min-h-0">
            <div className="flex flex-col min-h-0 flex-1">
                {/* Header Actions */}
                <div className="flex items-center justify-between mb-6">
                    <div>
                        <h3 className="text-lg font-black text-white mb-1">{offering.name}</h3>
                        <div className="flex items-center gap-2">
                            <span className={cn(
                                "text-[9px] px-1.5 py-0.5 rounded font-black uppercase tracking-wider",
                                offering.status === "active" ? "bg-green-500/20 text-green-500" :
                                    offering.status === "draft" ? "bg-orange-500/20 text-orange-500" :
                                        "bg-gray-500/20 text-gray-500"
                            )}>{offering.status}</span>
                            <span className="text-[10px] text-gray-500 font-mono">{offering.code}</span>
                        </div>
                    </div>
                    <div className="flex gap-2">
                        <button
                            onClick={onUpdateOffering}
                            disabled={isSaving}
                            className="px-4 py-2 premium-gradient rounded-xl text-xs font-bold text-white shadow-lg disabled:opacity-50 transition-all active:scale-95">
                            <Save className="w-4 h-4 inline mr-1" /> {isSaving ? "Saving..." : "Save"}
                        </button>
                        {offering.status === "archived" ? (
                            <button
                                onClick={() => onArchiveOffering(false)}
                                className="px-4 py-2 bg-blue-500/10 border border-blue-500/20 rounded-xl text-xs font-bold text-blue-400 hover:bg-blue-500/20 transition-all">
                                <RotateCcw className="w-4 h-4 inline mr-1" /> Restore
                            </button>
                        ) : (
                            <button
                                onClick={() => onArchiveOffering(true)}
                                className="px-4 py-2 bg-white/5 border border-white/10 rounded-xl text-xs font-bold text-gray-400 hover:bg-white/10 transition-all">
                                <Archive className="w-4 h-4 inline mr-1" /> Archive
                            </button>
                        )}
                        <button
                            onClick={onDeleteOffering}
                            className="px-4 py-2 bg-red-500/10 border border-red-500/20 rounded-xl text-xs font-bold text-red-500 hover:bg-red-500/20 transition-all">
                            <Trash2 className="w-4 h-4 inline mr-1" /> Delete
                        </button>
                    </div>
                </div>

                {/* Tabs */}
                <div className="flex border-b border-white/10 mb-6 gap-6">
                    <button
                        onClick={() => setActiveTab("overview")}
                        className={cn("pb-3 text-xs font-bold uppercase tracking-widest transition-colors border-b-2", activeTab === "overview" ? "text-accent border-accent" : "text-gray-500 border-transparent hover:text-white")}>
                        Overview
                    </button>
                    <button
                        onClick={() => setActiveTab("variants")}
                        className={cn("pb-3 text-xs font-bold uppercase tracking-widest transition-colors border-b-2", activeTab === "variants" ? "text-accent border-accent" : "text-gray-500 border-transparent hover:text-white")}>
                        Variants
                    </button>
                    <button
                        onClick={() => setActiveTab("attributes")}
                        className={cn("pb-3 text-xs font-bold uppercase tracking-widest transition-colors border-b-2", activeTab === "attributes" ? "text-accent border-accent" : "text-gray-500 border-transparent hover:text-white")}>
                        Attributes
                    </button>
                    <button
                        onClick={() => setActiveTab("history")}
                        className={cn("pb-3 text-xs font-bold uppercase tracking-widest transition-colors border-b-2", activeTab === "history" ? "text-accent border-accent" : "text-gray-500 border-transparent hover:text-white")}>
                        Version History
                    </button>
                </div>

                {/* Tab Content */}
                <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar">
                    {/* Tab: Overview */}
                    {activeTab === "overview" && (
                        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-300">
                            {/* Version Selector In-Context */}
                            <div className="flex items-center justify-between p-4 bg-accent/5 border border-accent/20 rounded-2xl mb-4">
                                <div className="flex items-center gap-3">
                                    <Layers className="w-5 h-5 text-accent" />
                                    <div>
                                        <div className="text-[10px] font-black text-accent uppercase tracking-widest">Editing Content Version</div>
                                        <div className="text-xs font-bold text-white">
                                            {currentVersion?.name || `v${currentVersion?.version || '?'}`}
                                        </div>
                                    </div>
                                </div>
                                <select
                                    value={currentVersionId || ""}
                                    onChange={(e) => onVersionChange(e.target.value)}
                                    className="bg-white/5 border border-white/10 rounded-xl px-4 py-2 text-xs font-bold text-gray-300 focus:outline-none focus:border-accent/40">
                                    {filteredVersions.map((v: any) => (
                                        <option key={v.id} value={v.id}>
                                            v{v.version} - {v.status.toUpperCase()} ({v.name})
                                        </option>
                                    ))}
                                </select>
                            </div>

                            <div className="grid grid-cols-1 gap-6">
                                <div>
                                    <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest block mb-2">Display Name (Versioned)</label>
                                    <input
                                        type="text"
                                        value={offeringForm.name}
                                        onChange={(e) => setOfferingForm({ ...offeringForm, name: e.target.value })}
                                        className="w-full bg-white/5 border border-white/10 rounded-xl p-3 text-sm text-gray-300 focus:outline-none focus:border-accent/40"
                                    />
                                </div>
                                <div>
                                    <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest block mb-2">Description (Versioned)</label>
                                    <textarea
                                        rows={6}
                                        value={offeringForm.description}
                                        onChange={(e) => setOfferingForm({ ...offeringForm, description: e.target.value })}
                                        className="w-full bg-white/5 border border-white/10 rounded-xl p-3 text-sm text-gray-300 focus:outline-none focus:border-accent/40 resize-none"
                                        placeholder="Enter offering description..."
                                    />
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Tab: Variants */}
                    {activeTab === "variants" && (
                        <div className="animate-in fade-in slide-in-from-bottom-2 duration-300">
                            <VariantManager
                                offering={offering}
                                selectedChannel={selectedChannel}
                                onAddSku={onAddSku}
                                onEditSku={onEditSku}
                                onDeleteSku={onDeleteSku}
                                onSetPrice={onSetPrice}
                            />
                        </div>
                    )}

                    {/* Tab: Attributes */}
                    {activeTab === "attributes" && (
                        <div className="animate-in fade-in slide-in-from-bottom-2 duration-300 space-y-4">
                            <div className="flex items-center justify-between">
                                <h4 className="text-sm font-bold text-white">Product Specs & Details</h4>
                                <button
                                    onClick={onAddAttribute}
                                    className="text-[10px] font-bold text-accent hover:underline flex items-center gap-1">
                                    <Plus className="w-3 h-3" /> Add Attribute
                                </button>
                            </div>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                {offeringAttributes.length === 0 ? (
                                    <div className="col-span-2 py-8 text-center text-[10px] text-gray-600 font-bold uppercase tracking-widest bg-white/2 rounded-xl border border-white/5 border-dashed">
                                        No attributes for this version
                                    </div>
                                ) : (
                                    offeringAttributes.map((attr: any) => (
                                        <div key={attr.id} className="p-3 bg-white/5 border border-white/5 rounded-xl flex items-center justify-between group hover:border-white/10 transition-all">
                                            <div className="flex-1 min-w-0">
                                                <div className="text-[8px] font-black text-accent uppercase tracking-[0.2em] mb-0.5 truncate" title={attr.attribute_key}>{attr.attribute_key}</div>
                                                <div className="text-[11px] font-bold text-gray-300 truncate" title={attr.attribute_value}>{attr.attribute_value}</div>
                                            </div>
                                            <button
                                                onClick={(e) => { e.stopPropagation(); onDeleteAttribute(attr.id); }}
                                                className="p-2 text-gray-500 hover:text-red-500 transition-colors opacity-0 group-hover:opacity-100 focus:opacity-100">
                                                <Trash2 className="w-3.5 h-3.5" />
                                            </button>
                                        </div>
                                    ))
                                )}
                            </div>
                        </div>
                    )}

                    {/* Tab: History */}
                    {activeTab === "history" && (
                        <div className="animate-in fade-in slide-in-from-bottom-2 duration-300 space-y-4">
                            <div className="flex items-center justify-between mb-4">
                                <h4 className="text-sm font-bold text-white flex items-center gap-2 italic">
                                    <Layers className="w-4 h-4" /> Version History
                                </h4>
                                <button
                                    onClick={onCreateVersion}
                                    className="px-3 py-1 bg-accent/10 border border-accent/20 rounded-lg text-[10px] font-bold text-accent hover:bg-accent/20 transition-all">
                                    Create New Draft
                                </button>
                            </div>

                            <div className="space-y-3">
                                {filteredVersions.map((v: any) => (
                                    <div
                                        key={v.id}
                                        className={cn(
                                            "p-4 bg-white/5 border rounded-2xl flex items-center justify-between group transition-all",
                                            v.status === "active" ? "border-green-500/30 bg-green-500/5" : "border-white/10"
                                        )}>
                                        <div className="flex items-center gap-4">
                                            <div className={cn(
                                                "w-10 h-10 rounded-xl flex items-center justify-center font-black text-xs",
                                                v.status === "active" ? "bg-green-500/20 text-green-500" : "bg-white/10 text-gray-400"
                                            )}>
                                                v{v.version}
                                            </div>
                                            <div>
                                                <div className="text-xs font-bold text-white flex items-center gap-2">
                                                    {v.name || "Unnamed Version"}
                                                    {v.status === "active" && (
                                                        <span className="bg-green-500/20 text-green-500 px-1.5 py-0.5 rounded text-[8px] uppercase font-black tracking-tighter">Active</span>
                                                    )}
                                                </div>
                                                <div className="text-[10px] text-gray-500 mt-0.5">
                                                    {v.status === "draft" ? "Draft • Edited recently" : `Published on ${new Date(v.created_at).toLocaleDateString()}`}
                                                </div>
                                            </div>
                                        </div>
                                        <div className="flex gap-2">
                                            {v.status !== "active" && (
                                                <button
                                                    onClick={() => onPublishVersion(v.version)}
                                                    className={cn(
                                                        "px-3 py-1.5 rounded-lg text-[10px] font-bold text-white shadow-lg hover:scale-105 active:scale-95 transition-all",
                                                        v.status === "draft" ? "premium-gradient" : "bg-blue-500/20 text-blue-400 border border-blue-500/30 hover:bg-blue-500/40"
                                                    )}>
                                                    {v.status === "draft" ? "Publish" : "Reactivate"}
                                                </button>
                                            )}
                                            <button
                                                onClick={() => onEditVersion(v)}
                                                className="p-2 bg-white/5 rounded-lg border border-white/10 text-gray-400 hover:text-white transition-all">
                                                <Edit3 className="w-3.5 h-3.5" />
                                            </button>
                                            {v.status !== "active" && (
                                                <button
                                                    onClick={() => { if (confirm("Are you sure?")) onDeleteVersion(v.id); }}
                                                    className="p-2 bg-white/5 rounded-lg border border-white/10 text-gray-400 hover:text-red-500 transition-all">
                                                    <Trash2 className="w-3.5 h-3.5" />
                                                </button>
                                            )}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </GlassContainer>
    );
}
