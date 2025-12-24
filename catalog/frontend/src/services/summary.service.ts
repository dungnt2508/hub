import { apiClient } from '@/shared/api/client';

export interface Article {
    id: string;
    title: string;
    summary: string;
    source_type: 'url' | 'rss' | 'file';
    source_value: string;
    status: 'pending' | 'processing' | 'done' | 'failed';
    created_at: string;
}

export interface Summary {
    id: string;
    article_id: string;
    summary_text: string;
    insights_json: string[];
    data_points_json: string[];
    created_at: string;
}

export const summaryService = {
    processUrl: async (url: string) => {
        // apiClient.post() already unwraps response.data, so response is already the data
        const response = await apiClient.post('/sources/url', { url });
        return response;
    },

    processRss: async (url: string) => {
        // apiClient.post() already unwraps response.data, so response is already the data
        const response = await apiClient.post('/sources/rss', { url });
        return response;
    },

    processFile: async (file: File) => {
        const formData = new FormData();
        formData.append('file', file);
        // apiClient.post() already unwraps response.data, so response is already the data
        const response = await apiClient.post('/sources/file', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return response;
    },

    getSummaries: async (limit: number = 20, offset: number = 0) => {
        // apiClient.get() already unwraps response.data, so response is already the data
        const response = await apiClient.get('/summaries', {
            params: { limit, offset },
        });
        return response;
    },

    getSummary: async (id: string): Promise<{ article: Article; summary: Summary }> => {
        // apiClient.get() already unwraps response.data, so response is already the data
        const response = await apiClient.get<{ article: Article; summary: Summary }>(`/summaries/${id}`);
        return response;
    },
};
