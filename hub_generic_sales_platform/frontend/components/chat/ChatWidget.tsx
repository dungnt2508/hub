"use client";

import { Message } from "./ChatMessage";

interface ChatWidgetProps {
    messages: Message[];
}

export default function ChatWidget({ messages }: ChatWidgetProps) {
    return (
        <div className="flex-1 overflow-y-auto p-8 space-y-8 scroll-smooth custom-scrollbar">
            {messages.map((msg, idx) => (
                <ChatMessage key={idx} message={msg} />
            ))}

            {/* Decorative pulse for session start */}
            {messages.length === 0 && (
                <div className="h-full flex flex-col items-center justify-center opacity-20">
                    <div className="w-16 h-16 premium-gradient rounded-full blur-xl animate-pulse mb-4"></div>
                    <p className="text-gray-400 font-medium">Start a conversation with IRIS Hub</p>
                </div>
            )}
        </div>
    );
}

import ChatMessage from "./ChatMessage";
