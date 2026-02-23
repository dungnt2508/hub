import { Package, Plus, Edit3, Trash2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { TenantOffering } from "@/lib/apiService";

interface VariantManagerProps {
    offering: TenantOffering; // We need the full offering to get inventory
    selectedChannel: string;
    onAddSku: () => void;
    onEditSku: (variantId: string, sku: string, name: string, qty: number, location: string) => void;
    onDeleteSku: (variantId: string) => void;
    onSetPrice: (variantId: string, currentPrice?: any) => void;
}

export default function VariantManager({
    offering,
    selectedChannel,
    onAddSku,
    onEditSku,
    onDeleteSku,
    onSetPrice
}: VariantManagerProps) {
    const inventory = offering.inventory || [];

    // Helper to find location - in a real app better to pass this map or look it up
    // For now we just pass the raw strings we get from the "inventory" object on the offering
    // The parent component reshaped the data to include "inventory" on the offering object in the original code? 
    // Actually the original code `selectedOffering` had `inventory` property.

    return (
        <div className="space-y-4 pt-4">
            <div className="flex items-center justify-between mb-4">
                <div className="flex flex-col">
                    <h4 className="text-sm font-bold text-white flex items-center gap-2">
                        <Package className="w-4 h-4" /> Commercial Variants (SKUs)
                    </h4>
                    <p className="text-[10px] text-gray-500 font-bold uppercase tracking-widest mt-1">Pricing for Channel: {selectedChannel}</p>
                </div>
                <button
                    onClick={(e) => { e.stopPropagation(); onAddSku(); }}
                    className="flex items-center gap-1 px-3 py-1.5 bg-accent/10 border border-accent/20 rounded-lg text-[10px] font-bold text-accent hover:bg-accent/20 transition-colors">
                    <Plus className="w-3 h-3" /> Add SKU
                </button>
            </div>

            <div className="overflow-hidden bg-white/5 border border-white/10 rounded-2xl">
                <table className="w-full text-left border-collapse">
                    <thead>
                        <tr className="bg-white/5">
                            <th className="p-4 text-[10px] font-black text-gray-500 uppercase tracking-widest">SKU / Name</th>
                            <th className="p-4 text-[10px] font-black text-gray-500 uppercase tracking-widest">Price ({selectedChannel})</th>
                            <th className="p-4 text-[10px] font-black text-gray-500 uppercase tracking-widest text-center">Stock</th>
                            <th className="p-4 text-[10px] font-black text-gray-500 uppercase tracking-widest text-right">Actions</th>
                        </tr>
                    </thead>
                    <tbody className="text-[11px] text-gray-300">
                        {inventory.length === 0 ? (
                            <tr>
                                <td colSpan={4} className="p-12 text-center text-gray-500 italic uppercase font-bold tracking-widest">No SKUs defined. Create a variant to start selling.</td>
                            </tr>
                        ) : (
                            inventory.map((inv: any, idx: number) => (
                                <tr key={idx} className="border-t border-white/5 hover:bg-white/10 transition-colors group">
                                    <td className="p-4">
                                        <div className="font-bold text-white mb-0.5">{inv.variant_name || "Standard Edition"}</div>
                                        <div className="font-mono text-[9px] opacity-40 uppercase tracking-tighter">SKU: {inv.sku}</div>
                                    </td>
                                    <td className="p-4">
                                        <div className="flex flex-col">
                                            {inv.price?.type === "promo" ? (
                                                <>
                                                    <div className="font-black text-green-500 tabular-nums">
                                                        {inv.price.amount.toLocaleString()} {inv.price.currency}
                                                    </div>
                                                    <div className="text-[9px] text-gray-500 line-through opacity-60 tabular-nums">
                                                        {inv.price.compare_at?.toLocaleString()} {inv.price.currency}
                                                    </div>
                                                </>
                                            ) : (
                                                <div className="font-black text-white tabular-nums">
                                                    {inv.price ?
                                                        `${inv.price.amount.toLocaleString()} ${inv.price.currency}` :
                                                        (offering.price ? `${offering.price.amount.toLocaleString()} ${offering.price.currency}` : "NOT SET")
                                                    }
                                                </div>
                                            )}
                                        </div>
                                        <div
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                onSetPrice(inv.id, inv.price);
                                            }}
                                            className="text-[8px] text-accent font-bold uppercase mt-1 cursor-pointer hover:underline">Set Price</div>
                                    </td>
                                    <td className="p-4 text-center">
                                        <div className="font-black text-white tabular-nums text-sm mb-1">{inv.aggregate_qty}</div>
                                        <span className={cn(
                                            "px-1.5 py-0.5 rounded text-[8px] font-black uppercase tracking-tighter",
                                            inv.stock_status === "in_stock" ? "bg-green-500/20 text-green-500" :
                                                inv.stock_status === "low_stock" ? "bg-orange-500/20 text-orange-500" :
                                                    "bg-red-500/20 text-red-500"
                                        )}>
                                            {inv.stock_status?.replace("_", " ") || "Out of Stock"}
                                        </span>
                                    </td>
                                    <td className="p-4 text-right">
                                        <div className="flex gap-2 justify-end opacity-0 group-hover:opacity-100 transition-opacity">
                                            <button
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    // Pass data to parent to populate form
                                                    onEditSku(inv.id, inv.sku, inv.variant_name, inv.aggregate_qty, "");
                                                }}
                                                className="p-1.5 bg-white/5 rounded-lg border border-white/10 text-gray-400 hover:text-accent">
                                                <Edit3 className="w-3.5 h-3.5" />
                                            </button>
                                            <button
                                                onClick={(e) => { e.stopPropagation(); onDeleteSku(inv.id); }}
                                                className="p-1.5 bg-white/5 rounded-lg border border-white/10 text-gray-400 hover:text-red-500">
                                                <Trash2 className="w-3.5 h-3.5" />
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
