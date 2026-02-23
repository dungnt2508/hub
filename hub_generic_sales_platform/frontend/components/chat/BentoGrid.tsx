"use client";

import GlassContainer from "@/components/ui/GlassContainer";
import { ChevronRight, ExternalLink, ShoppingCart } from "lucide-react";
import { cn } from "@/lib/utils";

export interface BentoGridItem {
    id: string;
    name: string;
    price: string;
    image?: string;
    score?: number;
    tags?: string[];
}

interface BentoGridProps {
    /** Support both API formats: products (legacy) or offerings */
    products?: BentoGridItem[];
    offerings?: BentoGridItem[];
    title?: string;
}

/** Normalize products or offerings to unified list */
function toBentoItems(products?: BentoGridItem[], offerings?: BentoGridItem[]): BentoGridItem[] {
    const items = products?.length ? products : offerings;
    return items ?? [];
}

export default function BentoGrid({ products, offerings, title = "Generative Product Comparison" }: BentoGridProps) {
    const items = toBentoItems(products, offerings);
    return (
        <GlassContainer className="p-4 bg-white/5 border-accent/20 border my-4" glow>
            <div className="flex items-center justify-between mb-4">
                <h4 className="text-sm font-semibold text-gray-200 uppercase tracking-widest">{title}</h4>
                <div className="flex gap-2">
                    <div className="w-2 h-2 rounded-full bg-accent animate-pulse"></div>
                    <div className="w-2 h-2 rounded-full bg-secondary animate-pulse delay-75"></div>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {items.map((product, idx) => (
                    <div
                        key={product.id}
                        className={cn(
                            "group relative bg-white/5 border border-white/5 rounded-2xl p-4 transition-all duration-300 hover:border-accent/40 hover:bg-white/10 hover:-translate-y-1 overflow-hidden",
                            idx === 0 && "md:col-span-2 lg:col-span-1" // Make first one more prominent if needed
                        )}
                    >
                        {/* Background Glow */}
                        <div className="absolute -top-10 -right-10 w-24 h-24 bg-accent/20 blur-3xl group-hover:bg-accent/30 transition-all"></div>

                        <div className="flex flex-col h-full space-y-3">
                            <div className="aspect-video bg-gradient-to-br from-white/10 to-transparent rounded-xl flex items-center justify-center border border-white/5 overflow-hidden">
                                {product.image ? (
                                    <img src={product.image} alt={product.name} className="w-full h-full object-cover" />
                                ) : (
                                    <div className="premium-gradient w-12 h-12 rounded-lg opacity-20 group-hover:opacity-40 transition-opacity"></div>
                                )}
                            </div>

                            <div className="flex-1">
                                <h5 className="font-bold text-gray-100 group-hover:text-white transition-colors">{product.name}</h5>
                                <div className="text-lg font-black text-accent mt-1">{product.price}</div>
                                {product.tags && (
                                    <div className="flex flex-wrap gap-2 mt-2">
                                        {product.tags.map(tag => (
                                            <span key={tag} className="text-[10px] px-2 py-0.5 rounded-full bg-white/5 border border-white/5 text-gray-400 uppercase tracking-tighter">
                                                {tag}
                                            </span>
                                        ))}
                                    </div>
                                )}
                            </div>

                            <div className="flex items-center gap-2 pt-2">
                                <button className="flex-1 flex items-center justify-center gap-2 py-2 glass-effect rounded-xl text-xs font-semibold hover:bg-white/10 transition-colors">
                                    <ExternalLink className="w-3 h-3" /> Details
                                </button>
                                <button className="premium-gradient p-2 rounded-xl shadow-lg hover:brightness-110 transition-all">
                                    <ShoppingCart className="text-white w-4 h-4" />
                                </button>
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            <button className="w-full mt-4 flex items-center justify-center gap-2 py-3 border border-white/5 rounded-xl text-xs font-bold text-gray-400 hover:text-white hover:bg-white/5 transition-all">
                View Comparison Table <ChevronRight className="w-4 h-4 text-accent" />
            </button>
        </GlassContainer>
    );
}
