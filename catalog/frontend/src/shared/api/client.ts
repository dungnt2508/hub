import axios, { AxiosError } from 'axios';
import { ErrorResponse } from '@gsnake/shared-types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3001/api';

/**
 * Enhanced API client with better error handling
 */
class ApiClient {
    private client = axios.create({
        baseURL: API_BASE_URL,
        headers: {
            'Content-Type': 'application/json',
        },
    });

    private refreshingToken: Promise<string> | null = null;

    private async refreshAccessToken(): Promise<string> {
        const refreshToken = localStorage.getItem('refresh_token');
        if (!refreshToken) {
            throw new Error('Missing refresh token');
        }

        // RULE: Use secure auth endpoint POST /auth/refresh
        const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
            refresh_token: refreshToken,
            audience: 'catalog-frontend', // Target service audience
        }, {
            headers: { 'Content-Type': 'application/json' },
        });

        // Response format: { success: true, data: { access_token, refresh_token, ... } }
        const data: any = response.data?.data || response.data;
        const newAccess = data?.access_token || data?.token; // Support both formats
        const newRefresh = data?.refresh_token || data?.refreshToken; // Support both formats
        
        if (!newAccess) {
            throw new Error('No access token returned');
        }
        
        // RULE: Store tokens in localStorage
        localStorage.setItem('token', newAccess);
        if (newRefresh) {
            localStorage.setItem('refresh_token', newRefresh);
        }
        return newAccess;
    }

    constructor() {
        this.setupInterceptors();
    }

    private setupInterceptors() {
        // Request interceptor
        this.client.interceptors.request.use(
            (config) => {
                const token = localStorage.getItem('token');
                if (token) {
                    config.headers.Authorization = `Bearer ${token}`;
                }
                return config;
            },
            (error) => Promise.reject(error)
        );

        // Response interceptor
        this.client.interceptors.response.use(
            (response) => response,
            async (error: AxiosError<{ success?: boolean; data?: any; message?: string }>) => {
                const originalRequest = error.config as any;

                // Handle 401
                if (error.response?.status === 401 && originalRequest && !originalRequest._retry) {
                    originalRequest._retry = true;

                    const msg = (error.response.data as any)?.message || '';
                    const soft401 = [
                        'Seller role required',
                        'Approved seller access required',
                        'Seller',
                        'role required',
                    ];

                    // Nếu là lỗi quyền seller (không phải token hết hạn) thì trả lỗi cho UI tự xử lý
                    const isSellerGate = soft401.some((s) => msg.toLowerCase().includes(s.toLowerCase()));
                    if (isSellerGate) {
                        return Promise.reject(error);
                    }

                    // Token hết hạn/không hợp lệ → thử refresh
                    if (!this.refreshingToken) {
                        this.refreshingToken = this.refreshAccessToken().finally(() => {
                            this.refreshingToken = null;
                        });
                    }
                    try {
                        const newToken = await this.refreshingToken;
                        if (newToken && originalRequest.headers) {
                            originalRequest.headers.Authorization = `Bearer ${newToken}`;
                        }
                        return this.client(originalRequest);
                    } catch (refreshErr) {
                        localStorage.removeItem('token');
                        localStorage.removeItem('refresh_token');
                        if (typeof window !== 'undefined') {
                            window.location.href = '/login';
                        }
                        return Promise.reject(refreshErr);
                    }
                }

                // Format error response
                const errorResponse = {
                    error: true,
                    code: (error.response?.data as any)?.code || 'UNKNOWN_ERROR',
                    message: (error.response?.data as any)?.message || 'An error occurred',
                    ...(process.env.NODE_ENV === 'development' && { details: (error.response?.data as any)?.details }),
                    requestId: (error.response?.data as any)?.requestId,
                };
                return Promise.reject(errorResponse);
            }
        );
    }

    async get<T>(url: string, config?: any): Promise<T> {
        const response = await this.client.get<{ success?: boolean; data?: T; message?: string }>(url, config);
        // Backend returns { success: true, data: {...} } or { error: true, ... }
        // Unwrap to return just the data
        if (response.data.success && response.data.data !== undefined) {
            return response.data.data as T;
        }
        // Fallback: assume response.data is already the data
        return response.data as T;
    }

    async post<T>(url: string, data?: any, config?: any): Promise<T> {
        const response = await this.client.post<{ success?: boolean; data?: T; message?: string }>(url, data, config);
        if (response.data.success && response.data.data !== undefined) {
            return response.data.data as T;
        }
        return response.data as T;
    }

    async put<T>(url: string, data?: any, config?: any): Promise<T> {
        const response = await this.client.put<{ success?: boolean; data?: T; message?: string }>(url, data, config);
        if (response.data.success && response.data.data !== undefined) {
            return response.data.data as T;
        }
        return response.data as T;
    }

    async delete<T>(url: string, config?: any): Promise<T> {
        const response = await this.client.delete<{ success?: boolean; data?: T; message?: string }>(url, config);
        if (response.data.success && response.data.data !== undefined) {
            return response.data.data as T;
        }
        return response.data as T;
    }
}

export const apiClient = new ApiClient();

