"use client";

import GlassContainer from "@/components/ui/GlassContainer";
import { cn } from "@/lib/utils";
import { CheckCircle2, AlertCircle, Zap, Search } from "lucide-react";

interface DecisionStep {
    tier: string;
    type: string;
    reason: string;
    status: "success" | "pending" | "failed";
    latency?: number;
}

interface DecisionVisualizerProps {
    steps: DecisionStep[];
}

export default function DecisionVisualizer({ steps }: DecisionVisualizerProps) {
    return (
        <div className="space-y-6 relative">
            {/* Connecting Line */}
            <div className="absolute left-6 top-8 bottom-8 w-0.5 bg-white/5 z-0"></div>

            {steps.map((step, idx) => (
                <div key={idx} className="flex gap-6 relative z-10 transition-all duration-500 hover:translate-x-1">
                    {/* Icon Node */}
                    <div className={cn(
                        "w-12 h-12 rounded-2xl flex items-center justify-center border shadow-lg transition-colors",
                        step.status === "success"
                            ? "bg-accent/20 border-accent/40 text-accent"
                            : "bg-white/5 border-white/5 text-gray-500"
                    )}>
                        {step.tier === "fast_path" && <Zap className="w-6 h-6" />}
                        {step.tier === "knowledge_path" && <Search className="w-6 h-6" />}
                        {step.tier === "agentic_path" && <SparklesIcon className="w-6 h-6" />}
                    </div>

                    <div className="flex-1">
                        <div className="flex items-center justify-between mb-1">
                            <span className="text-[10px] font-black uppercase tracking-widest text-gray-500">Tier {idx + 1}: {step.tier.replace("_", " ")}</span>
                            {step.latency && <span className="text-[10px] text-gray-400">{step.latency}ms</span>}
                        </div>

                        <GlassContainer className={cn(
                            "p-3 bg-white/5 border-white/5 transition-all",
                            step.status === "success" && "border-accent/30 bg-accent/5"
                        )}>
                            <div className="flex items-center gap-3">
                                {step.status === "success" ? (
                                    <CheckCircle2 className="w-4 h-4 text-green-500 shrink-0" />
                                ) : step.status === "failed" ? (
                                    <AlertCircle className="w-4 h-4 text-red-500 shrink-0" />
                                ) : (
                                    <div className="w-4 h-4 rounded-full border border-gray-600 border-t-white animate-spin"></div>
                                )}
                                <div>
                                    <div className="text-sm font-semibold text-gray-200">{step.type}</div>
                                    <p className="text-xs text-gray-500 line-clamp-1">{step.reason}</p>
                                </div>
                            </div>
                        </GlassContainer>
                    </div>
                </div>
            ))}
        </div>
    );
}

function SparklesIcon({ className }: { className?: string }) {
    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className={className}
        >
            <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z" />
            <path d="M5 3v4" />
            <path d="M19 17v4" />
            <path d="M3 5h4" />
            <path d="M17 19h4" />
        </svg>
    );
}
