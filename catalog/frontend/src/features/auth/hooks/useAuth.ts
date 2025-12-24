import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { LoginDto, RegisterDto, UserDto } from '@gsnake/shared-types';
import { apiClient } from '@/shared/api/client';
import { useEffect, useState } from 'react';

/**
 * Get current user
 * Chỉ gọi API khi có token để tránh spam log 401
 */
export function useMe() {
    const [hasToken, setHasToken] = useState(false);

    // Check token khi component mount và listen changes (client-side only)
    useEffect(() => {
        if (typeof window === 'undefined') return;

        const checkToken = () => {
            const token = localStorage.getItem('token');
            setHasToken(!!token);
        };

        // Check ngay lập tức
        checkToken();

        // Listen storage changes (khi login/logout từ tab khác)
        const handleStorageChange = (e: StorageEvent) => {
            if (e.key === 'token') {
                checkToken();
            }
        };
        window.addEventListener('storage', handleStorageChange);

        // Listen custom event (khi login/logout từ cùng tab)
        const handleTokenChange = () => checkToken();
        window.addEventListener('token-changed', handleTokenChange);

        return () => {
            window.removeEventListener('storage', handleStorageChange);
            window.removeEventListener('token-changed', handleTokenChange);
        };
    }, []);

    return useQuery({
        queryKey: ['auth', 'me'],
        queryFn: async () => {
            // apiClient.get() already unwraps response.data, so response is already the data
            const response = await apiClient.get<{ user: UserDto }>('/auth/me');
            return response?.user;
        },
        enabled: hasToken, // Chỉ gọi khi có token
        staleTime: 1000 * 60 * 5, // 5 minutes
        retry: false, // Don't retry on 401
        refetchOnWindowFocus: false, // Tắt refetch khi focus window
        refetchOnReconnect: false, // Tắt refetch khi reconnect network
        refetchInterval: false, // Tắt polling
    });
}

/**
 * Login mutation
 */
export function useLogin() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async (data: LoginDto) => {
            // apiClient.post() already unwraps response.data, so response is already the data
            const response = await apiClient.post<{ user: UserDto; token: string }>('/auth/login', data);
            const { token, user } = response;
            
            // Store token
            localStorage.setItem('token', token);
            
            // Dispatch event để useMe() biết token đã thay đổi
            if (typeof window !== 'undefined') {
                window.dispatchEvent(new Event('token-changed'));
            }
            
            return { user, token };
        },
        onSuccess: () => {
            // Invalidate and refetch user data
            queryClient.invalidateQueries({ queryKey: ['auth', 'me'] });
        },
    });
}

/**
 * Register mutation
 */
export function useRegister() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async (data: RegisterDto) => {
            // apiClient.post() already unwraps response.data, so response is already the data
            const response = await apiClient.post<{ user: UserDto; token: string }>('/auth/register', data);
            const { token, user } = response;
            
            // Store token
            localStorage.setItem('token', token);
            
            // Dispatch event để useMe() biết token đã thay đổi
            if (typeof window !== 'undefined') {
                window.dispatchEvent(new Event('token-changed'));
            }
            
            return { user, token };
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['auth', 'me'] });
        },
    });
}

/**
 * Logout mutation
 */
export function useLogout() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async () => {
            localStorage.removeItem('token');
            localStorage.removeItem('refresh_token');
            
            // Dispatch event để useMe() biết token đã bị xóa
            if (typeof window !== 'undefined') {
                window.dispatchEvent(new Event('token-changed'));
            }
        },
        onSuccess: () => {
            // Clear all queries
            queryClient.clear();
        },
    });
}

