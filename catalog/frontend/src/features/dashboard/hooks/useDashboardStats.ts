import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/shared/api/client';

interface DashboardStats {
    articles: {
        total: number;
        newThisWeek: number;
    };
    tools: {
        total: number;
        processing: number;
    };
    schedules: {
        total: number;
        nextFetch?: string;
    };
    persona?: {
        tone?: string;
        language_style?: string;
    };
}

/**
 * Get dashboard statistics
 * Uses parallel queries for better performance
 */
export function useDashboardStats() {
    // Fetch all data in parallel
    const articles = useQuery({
        queryKey: ['articles', { limit: 100 }],
        queryFn: async () => {
            // apiClient.get() already unwraps response.data, so response is already the data
            const response = await apiClient.get<{ articles: any[] }>('/articles?limit=100');
            return response?.articles || [];
        },
        staleTime: 1000 * 60 * 2, // 2 minutes
    });

    const tools = useQuery({
        queryKey: ['tools', { limit: 100 }],
        queryFn: async () => {
            // apiClient.get() already unwraps response.data, so response is already the data
            const response = await apiClient.get<{ tools: any[] }>('/tools?limit=100');
            return response?.tools || [];
        },
        staleTime: 1000 * 60 * 2,
    });

    const schedules = useQuery({
        queryKey: ['schedules'],
        queryFn: async () => {
            // apiClient.get() already unwraps response.data, so response is already the data
            const response = await apiClient.get<{ schedules: any[] }>('/schedules');
            return response?.schedules || [];
        },
        staleTime: 1000 * 60 * 2,
    });

    // Persona query - Ẩn tạm thời, tập trung vào marketplace mini
    // const persona = useQuery({
    //     queryKey: ['persona'],
    //     queryFn: async () => {
    //         try {
    //             // apiClient.get() already unwraps response.data, so response is already the data
    //             const response = await apiClient.get<{ persona: any }>('/personas');
    //             return response?.persona || {};
    //         } catch {
    //             return {};
    //         }
    //     },
    //     staleTime: 1000 * 60 * 5,
    //     retry: false, // Don't retry if persona doesn't exist
    // });

    // Calculate stats (không cần persona data)
    const stats: DashboardStats | undefined = articles.data && tools.data && schedules.data
        ? {
            articles: {
                total: articles.data.length,
                newThisWeek: articles.data.filter((a: any) => {
                    const oneWeekAgo = new Date();
                    oneWeekAgo.setDate(oneWeekAgo.getDate() - 7);
                    return new Date(a.created_at) > oneWeekAgo;
                }).length,
            },
            tools: {
                total: tools.data.length,
                processing: tools.data.filter((t: any) =>
                    t.status === 'processing' || t.status === 'pending'
                ).length,
            },
            schedules: {
                total: schedules.data.length,
                nextFetch: schedules.data
                    .filter((s: any) => s.active)
                    .sort((a: any, b: any) =>
                        new Date(a.next_fetch).getTime() - new Date(b.next_fetch).getTime()
                    )[0]?.next_fetch,
            },
            persona: {}, // Empty persona object for compatibility
        }
        : undefined;

    return {
        stats,
        isLoading: articles.isLoading || tools.isLoading || schedules.isLoading,
        isError: articles.isError || tools.isError || schedules.isError,
        error: articles.error || tools.error || schedules.error,
    };
}

