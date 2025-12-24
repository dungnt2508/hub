import { apiClient } from '@/shared/api/client';

export interface Schedule {
    id: string;
    user_id: string;
    source_type: 'url' | 'rss' | 'file';
    source_value: string;
    frequency: 'hourly' | 'daily' | 'weekly' | 'monthly';
    last_fetched?: string;
    next_fetch: string;
    workflow_id?: string;
    active: boolean;
    created_at: string;
}

export interface CreateScheduleInput {
    source_type: 'url' | 'rss' | 'file';
    source_value: string;
    frequency: 'hourly' | 'daily' | 'weekly' | 'monthly';
}

export const scheduleService = {
    /**
     * Get all schedules for current user
     */
    async getSchedules(): Promise<Schedule[]> {
        // apiClient.get() already unwraps response.data, so response is already the data
        const response = await apiClient.get<{ schedules: Schedule[] }>('/schedules');
        return response?.schedules || [];
    },

    /**
     * Create a new schedule
     */
    async createSchedule(data: CreateScheduleInput): Promise<Schedule> {
        // apiClient.post() already unwraps response.data, so response is already the data
        const response = await apiClient.post<{ schedule: Schedule }>('/schedules', data);
        return response?.schedule;
    },

    /**
     * Update a schedule
     */
    async updateSchedule(id: string, data: Partial<CreateScheduleInput & { frequency: string }>): Promise<Schedule> {
        // apiClient.put() already unwraps response.data, so response is already the data
        const response = await apiClient.put<{ schedule: Schedule }>(`/schedules/${id}`, data);
        return response?.schedule;
    },

    /**
     * Delete a schedule
     */
    async deleteSchedule(id: string): Promise<void> {
        await apiClient.delete(`/schedules/${id}`);
    },
};

