"use client";

import { create } from "zustand";

interface UIState {
    isSidebarCollapsed: boolean;
    setSidebarCollapsed: (collapsed: boolean) => void;
    currentTenantId: string | null;
    setCurrentTenantId: (tenantId: string | null) => void;
}

export const useUIStore = create<UIState>((set) => ({
    isSidebarCollapsed: false,
    setSidebarCollapsed: (collapsed) => set({ isSidebarCollapsed: collapsed }),
    currentTenantId: null,
    setCurrentTenantId: (tenantId) => set({ currentTenantId: tenantId }),
}));
