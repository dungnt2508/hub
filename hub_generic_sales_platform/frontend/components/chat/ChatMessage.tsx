"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Sparkles, User } from "lucide-react";
import { cn } from "@/lib/utils";
import BentoGrid from "./BentoGrid";

export interface Message {
    role: "user" | "assistant" | "system";
    content: string;
    metadata?: {
        tier?: string;
        cost?: string;
        latency_ms?: number;
        lifecycle_state?: string;
        tool_calls?: Array<{ name: string; args: Record<string, unknown>; success: boolean; elapsed_ms: number }>;
        g_ui?: {
            type: "bento_grid";
            data: any;
        };
    };
}

interface ChatMessageProps {
    message: Message;
}

export default function ChatMessage({ message }: ChatMessageProps) {
    const isAssistant = message.role === "assistant";

    return (
        <div className={cn("flex gap-4 w-full", isAssistant ? "justify-start" : "justify-end")}>
            {isAssistant && (
                <div className="w-8 h-8 premium-gradient rounded-lg flex items-center justify-center shrink-0 shadow-lg mt-1">
                    <Sparkles className="text-white w-5 h-5" />
                </div>
            )}

            <div className={cn("max-w-[85%] flex flex-col", isAssistant ? "items-start" : "items-end")}>
                <div className={cn(
                    "p-4 rounded-2xl border backdrop-blur-md transition-all duration-300",
                    isAssistant
                        ? "bg-white/5 rounded-tl-none border-white/10 hover:bg-white/[0.07]"
                        : "bg-white/10 rounded-tr-none border-white/5 hover:bg-white/[0.12]"
                )}>
                    <div className="prose prose-invert prose-sm max-w-none text-gray-200">
                        <ReactMarkdown
                            remarkPlugins={[remarkGfm]}
                        >
                            {message.content}
                        </ReactMarkdown>
                    </div>
                </div>

                {/* Generative UI Component - support both products and offerings from API */}
                {message.metadata?.g_ui?.type === "bento_grid" && (() => {
                    const d = message.metadata.g_ui.data;
                    return <BentoGrid
                        products={d?.products}
                        offerings={d?.offerings}
                        title={d?.title}
                    />;
                })()}

                {/* Tool Calls (Debug) */}
                {isAssistant && message.metadata?.tool_calls && message.metadata.tool_calls.length > 0 && (
                    <div className="mt-2 p-2 bg-black/20 rounded-lg border border-white/5">
                        <div className="text-[9px] font-bold text-gray-500 uppercase mb-1">Tool Calls</div>
                        <div className="space-y-1">
                            {message.metadata.tool_calls.map((tc, i) => (
                                <div key={i} className="text-[10px] flex items-center gap-2">
                                    <span className={tc.success ? "text-green-500" : "text-red-500"}>
                                        {tc.success ? "✓" : "✗"}
                                    </span>
                                    <span className="text-accent font-mono">{tc.name}</span>
                                    <span className="text-gray-500">{tc.elapsed_ms}ms</span>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
                {/* Metadata Badges */}
                {isAssistant && message.metadata && (
                    <div className="flex flex-wrap gap-2 mt-2 opacity-40 hover:opacity-100 transition-opacity">
                        <span className="text-[10px] px-2 py-0.5 rounded-md bg-white/5 border border-white/5 text-gray-500 uppercase">
                            {message.metadata.tier}
                        </span>
                        {message.metadata.lifecycle_state && (
                            <span className="text-[10px] px-2 py-0.5 rounded-md bg-accent/10 border border-accent/20 text-accent uppercase">
                                {message.metadata.lifecycle_state}
                            </span>
                        )}
                        <span className="text-[10px] px-2 py-0.5 rounded-md bg-white/5 border border-white/5 text-gray-500 uppercase">
                            {message.metadata.latency_ms}ms
                        </span>
                        <span className="text-[10px] px-2 py-0.5 rounded-md bg-white/5 border border-white/5 text-gray-500 uppercase">
                            {message.metadata.cost}
                        </span>
                    </div>
                )}
            </div>

            {!isAssistant && (
                <div className="w-8 h-8 bg-white/10 rounded-lg flex items-center justify-center shrink-0 border border-white/5 mt-1">
                    <User className="text-gray-400 w-5 h-5" />
                </div>
            )}
        </div>
    );
}
