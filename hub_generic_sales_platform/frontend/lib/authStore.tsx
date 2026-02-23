"use client";

import { create } from "zustand";
import { apiService, User } from "./apiService";
import { useUIStore } from "./store";

interface AuthState {
    user: User | null;
    isAuthenticated: boolean;
    isLoading: boolean;
    login: (email: string, password: string) => Promise<void>;
    logout: () => void;
    checkAuth: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
    user: null,
    isAuthenticated: false,
    isLoading: false,

    login: async (email, password) => {
        set({ isLoading: true });
        try {
            const response = await apiService.login({ email, password });

            localStorage.setItem("auth_token", response.access_token);
            localStorage.setItem("iris_user", JSON.stringify(response.user));
            localStorage.setItem("tenant_id", response.user.tenant_id);
            useUIStore.getState().setCurrentTenantId(response.user.tenant_id);

            set({ user: response.user, isAuthenticated: true, isLoading: false });
        } catch (err: any) {
            set({ isLoading: false });
            throw new Error(err.response?.data?.detail || "Đăng nhập thất bại. Vui lòng kiểm tra lại email và mật khẩu.");
        }
    },

    logout: () => {
        localStorage.removeItem("auth_token");
        localStorage.removeItem("iris_user");
        localStorage.removeItem("tenant_id");
        useUIStore.getState().setCurrentTenantId(null);
        set({ user: null, isAuthenticated: false });
    },

    checkAuth: async () => {
        const token = localStorage.getItem("auth_token");
        if (!token) {
            set({ user: null, isAuthenticated: false, isLoading: false });
            return;
        }

        set({ isLoading: true });
        try {
            const user = await apiService.getCurrentUser();
            localStorage.setItem("tenant_id", user.tenant_id);
            useUIStore.getState().setCurrentTenantId(user.tenant_id);
            set({ user, isAuthenticated: true, isLoading: false });
        } catch (err) {
            // Token might be expired or invalid
            localStorage.removeItem("auth_token");
            localStorage.removeItem("iris_user");
            localStorage.removeItem("tenant_id");
            useUIStore.getState().setCurrentTenantId(null);
            set({ user: null, isAuthenticated: false, isLoading: false });
        } finally {
            set({ isLoading: false });
        }
    }
}));
