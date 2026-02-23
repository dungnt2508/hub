"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiService, TenantOffering } from "@/lib/apiService";
import { useState, useEffect } from "react";
import { useSearchParams } from "next/navigation";
import { toast } from "sonner";
import { Package } from "lucide-react";

import GlassContainer from "@/components/ui/GlassContainer";
import CatalogStats from "@/components/catalog/CatalogStats";
import BotSelector, { BOT_ID_ALL } from "@/components/catalog/BotSelector";
import OfferingList from "@/components/catalog/OfferingList";
import OfferingDetail from "@/components/catalog/OfferingDetail";

export default function CatalogPage() {
    const queryClient = useQueryClient();
    const searchParams = useSearchParams();

    // UI State
    const [searchTerm, setSearchTerm] = useState("");
    const [filter, setFilter] = useState<"all" | "active" | "draft" | "archived">("all");
    const [selectedChannel, setSelectedChannel] = useState("WEB");
    const [selectedBotId, setSelectedBotId] = useState<string | null>(null);

    // Selection State
    const [selectedOffering, setSelectedOffering] = useState<any | null>(null);
    const [selectedVersionId, setSelectedVersionId] = useState<string | null>(null);

    // Modals State
    const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
    const [isAttributeModalOpen, setIsAttributeModalOpen] = useState(false);
    const [isVariantModalOpen, setIsVariantModalOpen] = useState(false);
    const [isPriceModalOpen, setIsPriceModalOpen] = useState(false);
    const [editingVersion, setEditingVersion] = useState<any | null>(null);
    const [selectedVariantId, setSelectedVariantId] = useState<string | null>(null);
    const [editingVariantId, setEditingVariantId] = useState<string | null>(null);

    // Forms
    const [newOffering, setNewOffering] = useState({ code: "", name: "", description: "" });
    const [offeringForm, setOfferingForm] = useState({ code: "", name: "", description: "", status: "draft" });
    const [attributeForm, setAttributeForm] = useState({ attribute_key: "", attribute_value: "", value_type: "text", display_order: 0 });
    const [variantForm, setVariantForm] = useState({ sku: "", name: "" });
    const [inventoryForm, setInventoryForm] = useState({ sku: "", qty: 0, location_code: "" });
    const [priceForm, setPriceForm] = useState({ amount: 0, currency: "VND", compare_at: 0, price_list_id: "", price_type: "base" });
    const [versionForm, setVersionForm] = useState({ name: "", description: "" });

    // --- Queries ---

    const { data: bots = [], isLoading: isBotsLoading } = useQuery({
        queryKey: ["bots", "active"],
        queryFn: () => apiService.listBots({ status: "active" }),
    });

    const { data: offerings = [], isLoading: isOfferingsLoading } = useQuery({
        queryKey: ["catalog-offerings", selectedChannel, selectedBotId],
        queryFn: () => apiService.listCatalogOfferings(
            selectedChannel,
            selectedBotId && selectedBotId !== BOT_ID_ALL ? selectedBotId : undefined
        ),
        enabled: !!selectedBotId,
    });

    const { data: versions = [] } = useQuery({
        queryKey: ["offering-versions", selectedOffering?.id],
        queryFn: () => selectedOffering ? apiService.listOfferingVersions(selectedOffering.id) : Promise.resolve([]),
        enabled: !!selectedOffering,
    });

    // Effective version for display
    const currentVersionId = selectedVersionId || selectedOffering?.version_id;

    const { data: offeringAttributes = [] } = useQuery({
        queryKey: ["offering-attributes", currentVersionId],
        queryFn: () => currentVersionId ? apiService.listOfferingAttributes(currentVersionId) : Promise.resolve([]),
        enabled: !!currentVersionId,
    });

    // Fetch domain attribute definitions for the selected offering
    const { data: domainAttributes = [], isLoading: isAttrLoading, error: attrError } = useQuery({
        queryKey: ["domain-attributes", selectedOffering?.domain_id],
        queryFn: () => {
            console.log("[DEBUG] Fetching attributes for domain:", selectedOffering?.domain_id);
            return selectedOffering?.domain_id ? apiService.listDomainAttributes(selectedOffering.domain_id) : Promise.resolve([]);
        },
        enabled: !!selectedOffering?.domain_id,
    });

    // Log when attributes are fetched
    useEffect(() => {
        console.log("[DEBUG] Domain attributes loaded:", domainAttributes);
        if (attrError) {
            console.error("[DEBUG] Error loading attributes:", attrError);
        }
    }, [domainAttributes, attrError]);

    const { data: priceLists = [] } = useQuery({
        queryKey: ["price-lists"],
        queryFn: () => apiService.listPriceLists(),
    });

    const { data: channels = [] } = useQuery({
        queryKey: ["channels"],
        queryFn: () => apiService.listChannels(),
    });

    const { data: locations = [] } = useQuery({
        queryKey: ["locations"],
        queryFn: () => apiService.listLocations(),
    });

    // --- Effects ---

    // Sync selectedOffering with offerings list (e.g. after mutation or channel switch)
    useEffect(() => {
        if (selectedOffering) {
            const updated = offerings.find((o: any) => o.id === selectedOffering.id);
            if (updated && JSON.stringify(updated) !== JSON.stringify(selectedOffering)) {
                setSelectedOffering(updated);
            }
        }
    }, [offerings, selectedOffering?.id]);

    // Init selectedBotId: ưu tiên ?bot_id (từ Migration) > ?view=all > Bot đầu tiên
    const botIdFromUrl = searchParams.get("bot_id");
    const viewAll = searchParams.get("view") === "all";
    useEffect(() => {
        if (!bots.length) return;
        if (botIdFromUrl && bots.some((b: { id: string }) => b.id === botIdFromUrl)) {
            setSelectedBotId(botIdFromUrl);
        } else if (viewAll) {
            setSelectedBotId(BOT_ID_ALL);
        } else if (!selectedBotId) {
            setSelectedBotId(bots[0].id);
        }
    }, [bots, botIdFromUrl, viewAll]);

    // --- Computed ---

    const filteredOfferings = offerings.filter((o: any) => {
        const matchesSearch = o.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            o.code.toLowerCase().includes(searchTerm.toLowerCase());
        const matchesFilter = filter === "all" || o.status === filter;
        return matchesSearch && matchesFilter;
    });

    const stats = {
        total: offerings.length,
        active: offerings.filter((o: any) => o.status === "active").length,
        draft: offerings.filter((o: any) => o.status === "draft").length,
        archived: offerings.filter((o: any) => o.status === "archived").length,
    };

    // --- Mutations ---

    const createOfferingMutation = useMutation({
        mutationFn: (data: { code: string; name: string; description?: string; status?: string; bot_id: string }) =>
            apiService.createOffering(data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["catalog-offerings"] });
            setIsCreateModalOpen(false);
            setNewOffering({ code: "", name: "", description: "" });
            toast.success("Offering created successfully");
        },
        onError: (error: any) => toast.error(error.response?.data?.detail || "Error creating offering")
    });

    const updateOfferingMutation = useMutation({
        mutationFn: ({ id, data }: { id: string; data: Partial<TenantOffering> }) =>
            apiService.updateOffering(id, data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["catalog-offerings"] });
            if (selectedOffering) queryClient.invalidateQueries({ queryKey: ["offering", selectedOffering.id] });
            toast.success("Offering updated");
        },
        onError: (error: any) => toast.error(error.response?.data?.detail || "Error updating offering")
    });

    const deleteOfferingMutation = useMutation({
        mutationFn: (id: string) => apiService.deleteOffering(id),
        onSuccess: (_, id) => {
            queryClient.invalidateQueries({ queryKey: ["catalog-offerings"] });
            if (selectedOffering?.id === id) setSelectedOffering(null);
            toast.success("Offering deleted");
        },
    });

    // Version Mutations
    const createVersionMutation = useMutation({
        mutationFn: (offeringId: string) => apiService.createOfferingVersion(offeringId),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["offering-versions", selectedOffering?.id] });
            toast.success("New version draft created");
        },
    });

    const updateVersionMutation = useMutation({
        mutationFn: ({ versionId, data }: { versionId: string; data: { name?: string; description?: string } }) =>
            apiService.updateOfferingVersion(versionId, data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["offering-versions", selectedOffering?.id] });
            queryClient.invalidateQueries({ queryKey: ["catalog-offerings"] });
            setEditingVersion(null);
            toast.success("Version updated");
        },
    });

    const publishVersionMutation = useMutation({
        mutationFn: ({ offeringId, version }: { offeringId: string; version: number }) =>
            apiService.publishOfferingVersion(offeringId, version),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["catalog-offerings"] });
            queryClient.invalidateQueries({ queryKey: ["offering-versions", selectedOffering?.id] });
            toast.success("Version published");
        },
    });

    const deleteVersionMutation = useMutation({
        mutationFn: (versionId: string) => apiService.deleteOfferingVersion(versionId),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["offering-versions", selectedOffering?.id] });
            toast.success("Version deleted");
        },
    });

    // Attribute Mutations
    const createAttributeMutation = useMutation({
        mutationFn: ({ versionId, data }: { versionId: string; data: any }) =>
            apiService.createOfferingAttribute(versionId, data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["offering-attributes", currentVersionId] });
            setIsAttributeModalOpen(false);
            setAttributeForm({ attribute_key: "", attribute_value: "", value_type: "text", display_order: 0 });
            toast.success("Attribute added successfully");
        },
        onError: (error: any) => {
            const message = error.response?.data?.detail || error.message || "Failed to add attribute";
            toast.error(message);
        }
    });

    const deleteAttributeMutation = useMutation({
        mutationFn: ({ versionId, attributeId }: { versionId: string; attributeId: string }) =>
            apiService.deleteOfferingAttribute(versionId, attributeId),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["offering-attributes", currentVersionId] });
            toast.success("Attribute deleted");
        },
    });

    // Variant Mutations
    const createVariantMutation = useMutation({
        mutationFn: (data: { sku: string; name: string }) =>
            apiService.createVariant(selectedOffering.id, data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["catalog-offerings"] });
            setIsVariantModalOpen(false);
            setVariantForm({ sku: "", name: "" });
            toast.success("Variant created");
        },
        onError: (error: any) => toast.error(error.response?.data?.detail || "Error creating variant")
    });

    const updateVariantMutation = useMutation({
        mutationFn: async ({ variantId, data, inventory }: { variantId: string; data: { name?: string; status?: string }; inventory?: { sku: string; location_code: string; qty: number } }) => {
            await apiService.updateVariant(variantId, data);
            if (inventory && inventory.location_code) {
                await apiService.updateInventory(inventory.sku, inventory.location_code, inventory.qty);
            }
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["catalog-offerings"] });
            setIsVariantModalOpen(false);
            setEditingVariantId(null);
            setVariantForm({ sku: "", name: "" });
            setInventoryForm({ sku: "", qty: 0, location_code: "" });
            toast.success("Variant updated");
        },
        onError: (error: any) => toast.error(error.response?.data?.detail || "Error updating variant")
    });

    const deleteVariantMutation = useMutation({
        mutationFn: (variantId: string) => apiService.deleteVariant(variantId),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["catalog-offerings"] });
            toast.success("Variant deleted");
        }
    });

    const setVariantPriceMutation = useMutation({
        mutationFn: (data: { variantId: string; price_list_id: string; amount: number; currency: string; price_type: string; compare_at?: number }) =>
            apiService.setVariantPrice(data.variantId, {
                price_list_id: data.price_list_id,
                amount: data.amount,
                currency: data.currency,
                price_type: data.price_type,
                compare_at: data.compare_at
            }),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["catalog-offerings"] });
            setIsPriceModalOpen(false);
            toast.success("Price updated");
        },
        onError: (error: any) => toast.error(error.response?.data?.detail || "Error setting price")
    });


    // --- Handlers ---

    const handleSelectOffering = (offering: any) => {
        setSelectedOffering(offering);
        setSelectedVersionId(offering.version_id);
        setOfferingForm({
            code: offering.code,
            name: offering.name,
            description: offering.description || "",
            status: offering.status,
        });
    };

    const handleCreateOffering = (e: React.FormEvent) => {
        e.preventDefault();
        if (newOffering.code.trim() && newOffering.name.trim() && selectedBotId) {
            createOfferingMutation.mutate({
                code: newOffering.code.trim(),
                name: newOffering.name.trim(),
                description: newOffering.description.trim() || undefined,
                status: "draft",
                bot_id: selectedBotId,
            });
        }
    };

    const handleUpdateOffering = () => {
        if (selectedOffering) {
            updateOfferingMutation.mutate({
                id: selectedOffering.id,
                data: {
                    code: offeringForm.code.trim(),
                    status: offeringForm.status,
                },
            });

            if (currentVersionId) {
                updateVersionMutation.mutate({
                    versionId: currentVersionId,
                    data: {
                        name: offeringForm.name.trim(),
                        description: offeringForm.description.trim() || undefined
                    }
                });
            }
        }
    };

    const handleCreateAttribute = (e: React.FormEvent) => {
        e.preventDefault();
        if (selectedOffering?.version_id) {
            createAttributeMutation.mutate({
                versionId: selectedOffering.version_id,
                data: attributeForm
            });
        }
    };

    const handleUpdateVersion = (e: React.FormEvent) => {
        e.preventDefault();
        if (editingVersion && versionForm.name.trim()) {
            updateVersionMutation.mutate({
                versionId: editingVersion.id,
                data: versionForm
            });
        }
    };

    return (
        <div className="h-full flex flex-col space-y-4 overflow-y-auto pr-2 custom-scrollbar no-scrollbar p-2">
            <div className="flex items-center justify-between">
                <div className="flex flex-col">
                    <h1 className="text-2xl font-black text-white">Catalog Editor</h1>
                    <p className="text-xs text-gray-500 font-bold uppercase tracking-[0.2em] mt-1">Multi-Bot Content Hub</p>
                </div>
            </div>

            {/* Compact Header: Stats + Bot Select */}
            <div className="grid grid-cols-1 gap-4">
                <CatalogStats stats={stats} />
                <BotSelector
                    bots={bots}
                    selectedBotId={selectedBotId}
                    onSelectBot={setSelectedBotId}
                    isLoading={isBotsLoading}
                    showAllOption
                />
            </div>

            {/* Main Content Area */}
            <div className="flex-1 grid grid-cols-1 md:grid-cols-12 gap-4 min-h-0 overflow-hidden pb-20 md:pb-0">

                {/* Left Pane: List */}
                <OfferingList
                    offerings={filteredOfferings}
                    selectedOfferingId={selectedOffering?.id}
                    onSelectOffering={handleSelectOffering}
                    isLoading={isOfferingsLoading}
                    searchTerm={searchTerm}
                    onSearchChange={setSearchTerm}
                    filter={filter}
                    onFilterChange={setFilter}
                    selectedChannel={selectedChannel}
                    onChannelChange={setSelectedChannel}
                    onCreateOffering={() => {
                        setNewOffering({ code: "", name: "", description: "" });
                        setIsCreateModalOpen(true);
                    }}
                    hasSelectedBot={!!selectedBotId}
                    canCreate={selectedBotId !== BOT_ID_ALL}
                />

                {/* Right Pane: Detail */}
                <GlassContainer className="col-span-1 md:col-span-8 p-0 md:p-0 flex flex-col bg-white/5 border-white/5 overflow-hidden min-h-[600px] md:min-h-0">
                    {selectedOffering ? (
                        <OfferingDetail
                            offering={selectedOffering}
                            versions={versions}
                            currentVersionId={currentVersionId}
                            offeringAttributes={offeringAttributes}
                            onUpdateOffering={handleUpdateOffering}
                            onDeleteOffering={() => { if (confirm("Confirm Delete?")) deleteOfferingMutation.mutate(selectedOffering.id) }}
                            onArchiveOffering={(archive) => updateOfferingMutation.mutate({ id: selectedOffering.id, data: { status: archive ? "archived" : "active" } })}
                            onVersionChange={setSelectedVersionId}
                            offeringForm={offeringForm}
                            setOfferingForm={setOfferingForm}
                            selectedChannel={selectedChannel}
                            // Variants
                            onAddSku={() => {
                                setEditingVariantId(null);
                                setVariantForm({ sku: "", name: "" });
                                setIsVariantModalOpen(true);
                            }}
                            onEditSku={(id, sku, name, qty, loc) => {
                                setEditingVariantId(id);
                                setVariantForm({ sku, name });
                                setInventoryForm({ sku, qty, location_code: loc || locations[0]?.code });
                                setIsVariantModalOpen(true);
                            }}
                            onDeleteSku={(id) => { if (confirm("Delete SKU?")) deleteVariantMutation.mutate(id) }}
                            onSetPrice={(id, price) => {
                                setSelectedVariantId(id);
                                const activeChannelObj = channels.find((c: any) => c.code === selectedChannel);
                                const defaultPriceListId = priceLists.find((pl: any) => pl.channel_id === activeChannelObj?.id)?.id || priceLists[0]?.id || "";

                                setPriceForm({
                                    amount: price?.amount || 0,
                                    currency: price?.currency || "VND",
                                    compare_at: price?.compare_at || 0,
                                    price_list_id: price?.price_list_id || defaultPriceListId,
                                    price_type: price?.type || "base"
                                });
                                setIsPriceModalOpen(true);
                            }}
                            // Attributes
                            onAddAttribute={() => {
                                setAttributeForm({ attribute_key: "", attribute_value: "", value_type: "text", display_order: 0 });
                                setIsAttributeModalOpen(true);
                            }}
                            onDeleteAttribute={(id) => deleteAttributeMutation.mutate({ versionId: currentVersionId!, attributeId: id })}
                            // Versions
                            onCreateVersion={() => createVersionMutation.mutate(selectedOffering.id)}
                            onPublishVersion={(v) => publishVersionMutation.mutate({ offeringId: selectedOffering.id, version: v })}
                            onEditVersion={(v) => {
                                setEditingVersion(v);
                                setVersionForm({ name: v.name, description: v.description || "" });
                            }}
                            onDeleteVersion={(id: string) => deleteVersionMutation.mutate(id)}
                            isSaving={updateOfferingMutation.isPending || updateVersionMutation.isPending}
                        />
                    ) : (
                        <div className="flex-1 flex items-center justify-center p-8 text-center">
                            <div>
                                <Package className="w-16 h-16 text-gray-500 mx-auto mb-4 opacity-50" />
                                <p className="text-sm font-bold text-gray-500 uppercase tracking-widest">Select an offering to edit</p>
                            </div>
                        </div>
                    )}
                </GlassContainer>
            </div>

            {/* --- Modals (Simplified for brevity, but functional) --- */}

            {isCreateModalOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
                    <GlassContainer className="w-full max-w-md p-8 bg-white/10 border-white/10 shadow-2xl">
                        <h2 className="text-xl font-black text-white mb-4">Create Offering</h2>
                        <form onSubmit={handleCreateOffering} className="space-y-4">
                            <input value={newOffering.code} onChange={e => setNewOffering({ ...newOffering, code: e.target.value.toUpperCase().replace(/\s+/g, '-') })} placeholder="Code" className="w-full bg-white/5 border border-white/10 rounded-xl p-3 text-white" required />
                            <input value={newOffering.name} onChange={e => setNewOffering({ ...newOffering, name: e.target.value })} placeholder="Name" className="w-full bg-white/5 border border-white/10 rounded-xl p-3 text-white" required />
                            <div className="flex gap-2">
                                <button type="button" onClick={() => setIsCreateModalOpen(false)} className="flex-1 py-3 text-gray-400">Cancel</button>
                                <button type="submit" className="flex-1 bg-white text-black font-bold py-3 rounded-xl">Create</button>
                            </div>
                        </form>
                    </GlassContainer>
                </div>
            )}

            {/* ... Other modals would follow similar pattern or be extracted to component ... */}
            {/* For brevity in this refactor step, I will include just the core logic or placeholders if needed, 
                but to fully replicate functionality I should include them. 
                I will include the Variant Modal as it's critical. 
             */}

            {isVariantModalOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
                    <GlassContainer className="w-full max-w-md p-8 bg-white/10 border-white/10 shadow-2xl">
                        <h2 className="text-xl font-black text-white mb-4">{editingVariantId ? "Edit SKU" : "New SKU"}</h2>
                        <form onSubmit={(e) => {
                            e.preventDefault();
                            if (editingVariantId) {
                                updateVariantMutation.mutate({ variantId: editingVariantId, data: { name: variantForm.name }, inventory: inventoryForm });
                            } else {
                                createVariantMutation.mutate(variantForm);
                            }
                        }} className="space-y-4">
                            <input value={variantForm.sku} disabled={!!editingVariantId} onChange={e => setVariantForm({ ...variantForm, sku: e.target.value.toUpperCase() })} placeholder="SKU" className="w-full bg-white/5 border border-white/10 rounded-xl p-3 text-white" required />
                            <input value={variantForm.name} onChange={e => setVariantForm({ ...variantForm, name: e.target.value })} placeholder="Variant Name" className="w-full bg-white/5 border border-white/10 rounded-xl p-3 text-white" required />
                            {editingVariantId && (
                                <div className="p-3 bg-white/5 rounded-xl">
                                    <label className="text-[10px] text-gray-400 uppercase">Stock</label>
                                    <input type="number" value={inventoryForm.qty} onChange={e => setInventoryForm({ ...inventoryForm, qty: parseInt(e.target.value) })} className="w-full bg-transparent border-b border-white/10 text-white" />
                                </div>
                            )}
                            <div className="flex gap-2">
                                <button type="button" onClick={() => setIsVariantModalOpen(false)} className="flex-1 py-3 text-gray-400">Cancel</button>
                                <button type="submit" className="flex-1 bg-white text-black font-bold py-3 rounded-xl">Save</button>
                            </div>
                        </form>
                    </GlassContainer>
                </div>
            )}

            {/* Attribute Modal */}
            {isAttributeModalOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
                    <GlassContainer className="w-full max-w-md p-8 bg-white/10 border-white/10 shadow-2xl">
                        <h2 className="text-xl font-black text-white mb-4">Add Attribute</h2>
                        <form onSubmit={handleCreateAttribute} className="space-y-4">
                            {/* Attribute Key Dropdown */}
                            <div>
                                <label className="text-xs text-gray-400 font-bold uppercase">Attribute</label>
                                {selectedOffering?.domain_id ? (
                                    <select 
                                        value={attributeForm.attribute_key} 
                                        onChange={e => {
                                            const attrDef = domainAttributes.find((a: any) => a.key === e.target.value);
                                            setAttributeForm({ 
                                                ...attributeForm, 
                                                attribute_key: e.target.value,
                                                value_type: attrDef?.value_type || "text",
                                                attribute_value: ""
                                            });
                                        }} 
                                        className="w-full bg-white/5 border border-white/10 rounded-xl p-3 text-white bg-gray-900" 
                                        required
                                    >
                                        <option value="">
                                            {domainAttributes.length === 0 ? "Loading attributes..." : "Select Attribute"}
                                        </option>
                                        {domainAttributes.map((attr: any) => (
                                            <option key={attr.id} value={attr.key}>
                                                {attr.key} ({attr.value_type})
                                            </option>
                                        ))}
                                    </select>
                                ) : (
                                    <div className="w-full bg-white/5 border border-white/10 rounded-xl p-3 text-gray-500 text-sm">
                                        Select an offering first
                                    </div>
                                )}
                            </div>

                            {/* Value Type Display */}
                            {attributeForm.attribute_key && (
                                <div>
                                    <label className="text-xs text-gray-400 font-bold uppercase">Type</label>
                                    <div className="w-full bg-white/5 border border-white/10 rounded-xl p-3 text-white text-sm">
                                        {attributeForm.value_type}
                                    </div>
                                </div>
                            )}

                            {/* Value Input - adapt based on type */}
                            <div>
                                <label className="text-xs text-gray-400 font-bold uppercase">Value</label>
                                {attributeForm.value_type === "number" ? (
                                    <input 
                                        type="number" 
                                        value={attributeForm.attribute_value} 
                                        onChange={e => setAttributeForm({ ...attributeForm, attribute_value: e.target.value })} 
                                        placeholder="Enter number" 
                                        className="w-full bg-white/5 border border-white/10 rounded-xl p-3 text-white" 
                                        step="any"
                                        required 
                                    />
                                ) : attributeForm.value_type === "boolean" ? (
                                    <select 
                                        value={attributeForm.attribute_value} 
                                        onChange={e => setAttributeForm({ ...attributeForm, attribute_value: e.target.value })}
                                        className="w-full bg-white/5 border border-white/10 rounded-xl p-3 text-white bg-gray-900"
                                        required
                                    >
                                        <option value="">Select Value</option>
                                        <option value="true">True</option>
                                        <option value="false">False</option>
                                    </select>
                                ) : (
                                    <input 
                                        value={attributeForm.attribute_value} 
                                        onChange={e => setAttributeForm({ ...attributeForm, attribute_value: e.target.value })} 
                                        placeholder="Value" 
                                        className="w-full bg-white/5 border border-white/10 rounded-xl p-3 text-white" 
                                        required 
                                    />
                                )}
                            </div>

                            {/* Error Display */}
                            {createAttributeMutation.isPending && (
                                <div className="text-center text-sm text-yellow-400">Adding...</div>
                            )}

                            <div className="flex gap-2">
                                <button 
                                    type="button" 
                                    onClick={() => setIsAttributeModalOpen(false)} 
                                    className="flex-1 py-3 text-gray-400 hover:text-white transition"
                                    disabled={createAttributeMutation.isPending}
                                >
                                    Cancel
                                </button>
                                <button 
                                    type="submit" 
                                    className="flex-1 bg-white text-black font-bold py-3 rounded-xl hover:bg-gray-200 transition disabled:opacity-50"
                                    disabled={createAttributeMutation.isPending || !attributeForm.attribute_key || !attributeForm.attribute_value}
                                >
                                    Add
                                </button>
                            </div>
                        </form>
                    </GlassContainer>
                </div>
            )}

            {/* Price Modal */}
            {isPriceModalOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
                    <GlassContainer className="w-full max-w-md p-8 bg-white/10 border-white/10 shadow-2xl">
                        <h2 className="text-xl font-black text-white mb-4">Set Price</h2>
                        <form onSubmit={(e) => { e.preventDefault(); if (priceForm.price_list_id) setVariantPriceMutation.mutate({ variantId: selectedVariantId!, ...priceForm }) }} className="space-y-4">
                            <select
                                value={priceForm.price_list_id}
                                onChange={e => setPriceForm({ ...priceForm, price_list_id: e.target.value })}
                                className="w-full bg-white/5 border border-white/10 rounded-xl p-3 text-white bg-gray-900"
                                required
                            >
                                <option value="">Select Price List</option>
                                {priceLists
                                    .filter((pl: any) => {
                                        const activeChannelObj = channels.find((c: any) => c.code === selectedChannel);
                                        return !activeChannelObj || pl.channel_id === activeChannelObj.id;
                                    })
                                    .map((pl: any) => (
                                        <option key={pl.id} value={pl.id}>{pl.code}</option>
                                    ))
                                }
                            </select>
                            <div className="text-[9px] text-gray-500 font-bold uppercase tracking-widest px-1">
                                Showing Price Lists for Channel: {selectedChannel}
                            </div>
                            <input type="number" value={priceForm.amount} onChange={e => setPriceForm({ ...priceForm, amount: parseFloat(e.target.value) })} placeholder="Amount" className="w-full bg-white/5 border border-white/10 rounded-xl p-3 text-white" required />
                            <div className="flex gap-2">
                                <button type="button" onClick={() => setIsPriceModalOpen(false)} className="flex-1 py-3 text-gray-400">Cancel</button>
                                <button type="submit" className="flex-1 bg-white text-black font-bold py-3 rounded-xl">Save</button>
                            </div>
                        </form>
                    </GlassContainer>
                </div>
            )}

            {/* Edit Version Modal */}
            {editingVersion && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
                    <GlassContainer className="w-full max-w-md p-8 bg-white/10 border-white/10 shadow-2xl">
                        <h2 className="text-xl font-black text-white mb-4">Edit Version</h2>
                        <form onSubmit={handleUpdateVersion} className="space-y-4">
                            <input value={versionForm.name} onChange={e => setVersionForm({ ...versionForm, name: e.target.value })} placeholder="Version Name" className="w-full bg-white/5 border border-white/10 rounded-xl p-3 text-white" required />
                            <textarea value={versionForm.description} onChange={e => setVersionForm({ ...versionForm, description: e.target.value })} placeholder="Description" className="w-full bg-white/5 border border-white/10 rounded-xl p-3 text-white" />
                            <div className="flex gap-2">
                                <button type="button" onClick={() => setEditingVersion(null)} className="flex-1 py-3 text-gray-400">Cancel</button>
                                <button type="submit" className="flex-1 bg-white text-black font-bold py-3 rounded-xl">Save</button>
                            </div>
                        </form>
                    </GlassContainer>
                </div>
            )}

        </div>
    );
}
