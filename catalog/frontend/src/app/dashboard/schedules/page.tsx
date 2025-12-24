'use client';

import { useState, useEffect } from 'react';
import { scheduleService, Schedule, CreateScheduleInput } from '@/services/schedule.service';
import toast from 'react-hot-toast';

export default function SchedulesPage() {
    const [schedules, setSchedules] = useState<Schedule[]>([]);
    const [loading, setLoading] = useState(true);
    const [showForm, setShowForm] = useState(false);
    const [formData, setFormData] = useState<CreateScheduleInput>({
        source_type: 'url',
        source_value: '',
        frequency: 'daily',
    });
    const [submitting, setSubmitting] = useState(false);

    useEffect(() => {
        fetchSchedules();
    }, []);

    const fetchSchedules = async () => {
        try {
            setLoading(true);
            const data = await scheduleService.getSchedules();
            setSchedules(data);
        } catch (error: any) {
            toast.error('Không thể tải danh sách lịch trình');
            console.error('Failed to fetch schedules:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!formData.source_value.trim()) {
            toast.error('Vui lòng nhập URL hoặc nguồn');
            return;
        }

        setSubmitting(true);
        try {
            await scheduleService.createSchedule(formData);
            toast.success('Đã tạo lịch trình mới!');
            setFormData({ source_type: 'url', source_value: '', frequency: 'daily' });
            setShowForm(false);
            fetchSchedules();
        } catch (error: any) {
            toast.error(error.response?.data?.message || 'Lỗi khi tạo lịch trình');
        } finally {
            setSubmitting(false);
        }
    };

    const handleDelete = async (id: string) => {
        if (!window.confirm('Bạn có chắc chắn muốn xóa lịch trình này?')) return;

        try {
            await scheduleService.deleteSchedule(id);
            toast.success('Đã xóa lịch trình');
            fetchSchedules();
        } catch (error: any) {
            toast.error(error.response?.data?.message || 'Lỗi khi xóa');
        }
    };

    const formatNextFetch = (dateString: string) => {
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = date.getTime() - now.getTime();
        const diffHours = Math.floor(diffMs / 3600000);
        const diffMins = Math.floor((diffMs % 3600000) / 60000);

        if (diffMs < 0) return 'Đã quá hạn';
        if (diffHours > 0) return `${diffHours}h ${diffMins}m nữa`;
        return `${diffMins} phút nữa`;
    };

    const frequencyLabels: Record<string, string> = {
        hourly: 'Mỗi giờ',
        daily: 'Hàng ngày',
        weekly: 'Hàng tuần',
        monthly: 'Hàng tháng',
    };

    const sourceTypeLabels: Record<string, string> = {
        url: 'URL',
        rss: 'RSS Feed',
        file: 'File',
    };

    return (
        <div className="space-y-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <h1 className="text-2xl font-bold text-gray-900 dark:text-white">⏰ Lịch trình tự động</h1>
                <button
                    onClick={() => setShowForm(!showForm)}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors whitespace-nowrap"
                >
                    {showForm ? 'Hủy' : '+ Tạo lịch trình mới'}
                </button>
            </div>

            {/* Create Form */}
            {showForm && (
                <div className="bg-white dark:bg-gray-900 p-6 rounded-xl shadow-sm border border-gray-200 dark:border-gray-800">
                    <h2 className="text-lg font-semibold mb-4">Tạo lịch trình mới</h2>
                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">
                                Loại nguồn
                            </label>
                            <select
                                value={formData.source_type}
                                onChange={(e) => setFormData({ ...formData, source_type: e.target.value as any })}
                                className="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 focus:ring-2 focus:ring-blue-500"
                            >
                                <option value="url">URL</option>
                                <option value="rss">RSS Feed</option>
                                <option value="file">File</option>
                            </select>
                        </div>

                        <div>
                            <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">
                                {formData.source_type === 'url' ? 'URL' : formData.source_type === 'rss' ? 'RSS Feed URL' : 'File Path'}
                            </label>
                            <input
                                type="text"
                                value={formData.source_value}
                                onChange={(e) => setFormData({ ...formData, source_value: e.target.value })}
                                placeholder={formData.source_type === 'url' ? 'https://example.com/article' : formData.source_type === 'rss' ? 'https://example.com/feed.xml' : '/path/to/file'}
                                className="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 focus:ring-2 focus:ring-blue-500"
                                required
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">
                                Tần suất
                            </label>
                            <select
                                value={formData.frequency}
                                onChange={(e) => setFormData({ ...formData, frequency: e.target.value as any })}
                                className="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 focus:ring-2 focus:ring-blue-500"
                            >
                                <option value="hourly">Mỗi giờ</option>
                                <option value="daily">Hàng ngày</option>
                                <option value="weekly">Hàng tuần</option>
                                <option value="monthly">Hàng tháng</option>
                            </select>
                        </div>

                        <div className="flex gap-3">
                            <button
                                type="submit"
                                disabled={submitting}
                                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                            >
                                {submitting ? 'Đang tạo...' : 'Tạo lịch trình'}
                            </button>
                            <button
                                type="button"
                                onClick={() => {
                                    setShowForm(false);
                                    setFormData({ source_type: 'url', source_value: '', frequency: 'daily' });
                                }}
                                className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600"
                            >
                                Hủy
                            </button>
                        </div>
                    </form>
                </div>
            )}

            {/* Schedules List */}
            <div className="space-y-4">
                {loading ? (
                    <div className="text-center py-12 text-gray-500">Đang tải...</div>
                ) : schedules.length === 0 ? (
                    <div className="text-center py-12 text-gray-500 bg-white dark:bg-gray-900 rounded-xl border border-dashed border-gray-300 dark:border-gray-700">
                        Chưa có lịch trình nào. Tạo lịch trình mới để bắt đầu!
                    </div>
                ) : (
                    schedules.map((schedule) => (
                        <div key={schedule.id} className="bg-white dark:bg-gray-900 p-6 rounded-xl shadow-sm border border-gray-200 dark:border-gray-800">
                            <div className="flex justify-between items-start mb-4">
                                <div className="flex-1">
                                    <div className="flex items-center gap-3 mb-2">
                                        <span className={`px-2 py-1 text-xs rounded-full ${
                                            schedule.active 
                                                ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' 
                                                : 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400'
                                        }`}>
                                            {schedule.active ? 'Đang hoạt động' : 'Tạm dừng'}
                                        </span>
                                        <span className="px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400">
                                            {sourceTypeLabels[schedule.source_type]}
                                        </span>
                                        <span className="px-2 py-1 text-xs rounded-full bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400">
                                            {frequencyLabels[schedule.frequency]}
                                        </span>
                                    </div>
                                    <p className="text-sm text-gray-600 dark:text-gray-400 break-all">
                                        {schedule.source_value}
                                    </p>
                                </div>
                                <button
                                    onClick={() => handleDelete(schedule.id)}
                                    className="ml-4 px-3 py-1 text-sm text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                                >
                                    Xóa
                                </button>
                            </div>

                            <div className="grid grid-cols-2 gap-4 text-sm">
                                <div>
                                    <span className="text-gray-500 dark:text-gray-400">Lần tới:</span>
                                    <p className="font-medium text-gray-900 dark:text-white">
                                        {formatNextFetch(schedule.next_fetch)}
                                    </p>
                                </div>
                                {schedule.last_fetched && (
                                    <div>
                                        <span className="text-gray-500 dark:text-gray-400">Lần cuối:</span>
                                        <p className="font-medium text-gray-900 dark:text-white">
                                            {new Date(schedule.last_fetched).toLocaleString('vi-VN')}
                                        </p>
                                    </div>
                                )}
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
}

