"use client";

import { create } from "zustand";
import { Message } from "@/components/chat/ChatMessage";

interface Session {
    id: string;
    botId: string;
    messages: Message[];
    createdAt: number;
}

interface ChatState {
    sessions: Record<string, Session>;
    activeSessionId: string | null;
    createSession: (sessionId: string, botId: string) => void;
    setActiveSession: (sessionId: string) => void;
    addMessage: (sessionId: string, message: Message) => void;
    getSession: (sessionId: string) => Session | undefined;
}

export const useChatStore = create<ChatState>((set, get) => ({
    sessions: {},
    activeSessionId: null,
    createSession: (sessionId, botId) => {
        set((state) => ({
            sessions: {
                ...state.sessions,
                [sessionId]: {
                    id: sessionId,
                    botId,
                    messages: [],
                    createdAt: Date.now(),
                },
            },
        }));
    },
    setActiveSession: (sessionId) => {
        set({ activeSessionId: sessionId });
    },
    addMessage: (sessionId, message) => {
        set((state) => {
            const session = state.sessions[sessionId];
            if (!session) return state;
            return {
                sessions: {
                    ...state.sessions,
                    [sessionId]: {
                        ...session,
                        messages: [...session.messages, message],
                    },
                },
            };
        });
    },
    getSession: (sessionId) => {
        return get().sessions[sessionId];
    },
}));
