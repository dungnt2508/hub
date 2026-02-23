import { QueryClient } from '@tanstack/react-query';

/**
 * React Query client configuration
 */
export const queryClient = new QueryClient({
    defaultOptions: {
        queries: {
            staleTime: 1000 * 60 * 5, // 5 minutes
            gcTime: 1000 * 60 * 30, // 30 minutes (formerly cacheTime)
            retry: 1,
            refetchOnWindowFocus: false,
            refetchOnMount: true,
        },
        mutations: {
            retry: 0,
        },
    },
});

