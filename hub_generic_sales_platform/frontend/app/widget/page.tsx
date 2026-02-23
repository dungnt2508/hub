"use client";

import { useState, useEffect, useCallback } from "react";
import { useSearchParams } from "next/navigation";
import { apiService } from "@/lib/apiService";
import { Message } from "@/components/chat/ChatMessage";
import ChatWidget from "@/components/chat/ChatWidget";
import { Send, Loader2 } from "lucide-react";

/**
 * Web Widget page - embed trên website bên ngoài qua iframe.
 * URL: /widget?tenant_id=xxx&bot_id=yyy
 */
export default function WidgetPage() {
    const searchParams = useSearchParams();
    const tenantId = searchParams.get("tenant_id") || "";
    const botId = searchParams.get("bot_id") || "";

    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState("");
    const [sessionId, setSessionId] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleSend = useCallback(async () => {
        if (!input.trim() || !tenantId || !botId) return;
        const text = input.trim();
        setInput("");
        setIsLoading(true);
        setError(null);

        setMessages((prev) => [...prev, { role: "user", content: text, metadata: {} }]);

        try {
            const res = await apiService.sendWidgetMessage(tenantId, botId, text, sessionId || undefined);
            setSessionId(res.session_id);
            setMessages((prev) => [...prev, { role: "assistant", content: res.response, metadata: res.metadata || {} }]);
        } catch (e: any) {
            setError(e?.message || "Lỗi kết nối");
            setMessages((prev) => [
                ...prev,
                { role: "assistant", content: "Xin lỗi, tôi không thể xử lý. Vui lòng thử lại sau.", metadata: {} },
            ]);
        } finally {
            setIsLoading(false);
        }
    }, [input, tenantId, botId, sessionId]);

    if (!tenantId || !botId) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-900/95 p-4">
                <p className="text-gray-400 text-sm">Thiếu tenant_id hoặc bot_id trong URL. Ví dụ: /widget?tenant_id=xxx&bot_id=yyy</p>
            </div>
        );
    }

    return (
        <div className="h-screen flex flex-col bg-gray-900/95 text-white">
            <div className="p-4 border-b border-white/10">
                <h2 className="text-sm font-bold">Chat với chúng tôi</h2>
                <p className="text-[10px] text-gray-500">Hỗ trợ 24/7</p>
            </div>
            <div className="flex-1 overflow-hidden">
                <ChatWidget messages={messages} />
            </div>
            {error && <p className="text-red-400 text-[10px] px-4 py-1">{error}</p>}
            <div className="p-4 border-t border-white/10 flex gap-2">
                <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleSend()}
                    placeholder="Nhập tin nhắn..."
                    className="flex-1 bg-white/5 border border-white/10 rounded-xl py-2 px-4 text-sm focus:outline-none focus:border-accent"
                    disabled={isLoading}
                />
                <button
                    onClick={handleSend}
                    disabled={isLoading || !input.trim()}
                    className="p-2 bg-accent rounded-xl hover:brightness-110 disabled:opacity-50"
                >
                    {isLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
                </button>
            </div>
        </div>
    );
}
