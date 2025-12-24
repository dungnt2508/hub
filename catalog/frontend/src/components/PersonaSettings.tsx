'use client';

import { useState, useEffect } from 'react';
import { apiClient } from '@/shared/api/client';
import { Persona } from '@/types';

export default function PersonaSettings() {
    const [persona, setPersona] = useState<Persona | null>(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [message, setMessage] = useState('');

    // Form state
    const [tone, setTone] = useState('');
    const [style, setStyle] = useState('');
    const [topics, setTopics] = useState<string[]>([]);
    const [newTopic, setNewTopic] = useState('');

    useEffect(() => {
        fetchPersona();
    }, []);

    const fetchPersona = async () => {
        try {
            const res = await apiClient.get('/personas');
            const p = res.data?.persona;
            setPersona(p);
            setTone(p.tone);
            setStyle(p.language_style);
            setTopics(p.topics_interest || []);
        } catch (err) {
            // Persona might not exist yet
            console.log('No persona found or error fetching');
        } finally {
            setLoading(false);
        }
    };

    const handleSave = async (e: React.FormEvent) => {
        e.preventDefault();
        setSaving(true);
        setMessage('');

        try {
            const payload = {
                tone,
                language_style: style,
                topics_interest: topics,
            };

            if (persona) {
                await apiClient.put('/personas', payload);
            } else {
                await apiClient.post('/personas', payload);
            }
            setMessage('Lưu Persona thành công! 🎉');
            fetchPersona(); // Refresh
        } catch (err: any) {
            // apiClient formats errors as ErrorResponse, so err.message is available directly
            setMessage('Lỗi khi lưu: ' + (err.message || err.response?.data?.message || 'Unknown error'));
        } finally {
            setSaving(false);
        }
    };

    const addTopic = () => {
        if (newTopic && !topics.includes(newTopic)) {
            setTopics([...topics, newTopic]);
            setNewTopic('');
        }
    };

    const removeTopic = (t: string) => {
        setTopics(topics.filter((topic) => topic !== t));
    };

    if (loading) return <div>Đang tải persona...</div>;

    return (
        <div className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Form Section */}
                <div className="lg:col-span-2 bg-white dark:bg-gray-900 p-6 rounded-xl shadow-sm border border-gray-200 dark:border-gray-800">
                    <form onSubmit={handleSave} className="space-y-6">
                        <div>
                            <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">Giọng điệu (Tone)</label>
                            <select
                                value={tone}
                                onChange={(e) => setTone(e.target.value)}
                                className="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 focus:ring-2 focus:ring-blue-500"
                            >
                                <option value="">Chọn giọng điệu...</option>
                                <option value="professional">Chuyên nghiệp (Professional)</option>
                                <option value="casual">Thoải mái (Casual)</option>
                                <option value="witty">Hóm hỉnh (Witty)</option>
                                <option value="friendly">Thân thiện (Friendly)</option>
                                <option value="academic">Học thuật (Academic)</option>
                                <option value="sarcastic">Châm biếm (Sarcastic)</option>
                            </select>
                        </div>

                        <div>
                            <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">Phong cách ngôn ngữ</label>
                            <select
                                value={style}
                                onChange={(e) => setStyle(e.target.value)}
                                className="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 focus:ring-2 focus:ring-blue-500"
                            >
                                <option value="">Chọn phong cách...</option>
                                <option value="concise">Ngắn gọn (Concise)</option>
                                <option value="detailed">Chi tiết (Detailed)</option>
                                <option value="simple">Đơn giản (Simple/ELI5)</option>
                                <option value="technical">Kỹ thuật (Technical)</option>
                                <option value="storytelling">Kể chuyện (Storytelling)</option>
                            </select>
                        </div>

                        <div>
                            <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">Chủ đề quan tâm</label>
                            <div className="flex gap-2 mb-3">
                                <input
                                    type="text"
                                    value={newTopic}
                                    onChange={(e) => setNewTopic(e.target.value)}
                                    onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addTopic())}
                                    placeholder="Thêm chủ đề (VD: AI, Crypto)..."
                                    className="flex-1 px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 focus:ring-2 focus:ring-blue-500"
                                />
                                <button
                                    type="button"
                                    onClick={addTopic}
                                    className="px-4 py-2 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg font-medium"
                                >
                                    Thêm
                                </button>
                            </div>
                            <div className="flex flex-wrap gap-2">
                                {topics.map((t) => (
                                    <span key={t} className="px-3 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded-full text-sm flex items-center gap-2">
                                        {t}
                                        <button type="button" onClick={() => removeTopic(t)} className="hover:text-blue-900 dark:hover:text-blue-100">×</button>
                                    </span>
                                ))}
                            </div>
                        </div>

                        {message && (
                            <div className={`p-3 rounded-lg ${message.includes('Lỗi') ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}`}>
                                {message}
                            </div>
                        )}

                        <button
                            type="submit"
                            disabled={saving}
                            className="w-full py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition-colors disabled:opacity-50"
                        >
                            {saving ? 'Đang lưu...' : 'Lưu Persona'}
                        </button>
                    </form>
                </div>

                {/* Live Preview Section */}
                <div className="bg-gradient-to-br from-indigo-500 to-purple-600 p-6 rounded-xl shadow-lg text-white h-fit sticky top-6">
                    <h3 className="text-lg font-bold mb-4">✨ Xem trước (Live Preview)</h3>
                    <p className="text-white/80 text-sm mb-6">
                        Đây là cách bot sẽ tự giới thiệu dựa trên cài đặt của bạn:
                    </p>

                    <div className="bg-white/10 backdrop-blur-md p-4 rounded-lg border border-white/20">
                        <div className="flex items-start gap-3">
                            <div className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center text-lg">🤖</div>
                            <div className="flex-1">
                                <p className="text-sm leading-relaxed">
                                    {tone === 'witty' && "Chào đằng ấy! Sẵn sàng chinh phục thế giới hay chỉ debug code thôi đây? 😉"}
                                    {tone === 'professional' && "Xin chào. Tôi sẵn sàng hỗ trợ bạn thực hiện các tác vụ một cách hiệu quả nhất."}
                                    {tone === 'casual' && "Yo! Có gì hot không? Triển khai công việc thôi nào."}
                                    {!tone && "Xin chào! Hãy cấu hình giọng điệu để thấy sự thay đổi của tôi."}
                                </p>
                                {topics.length > 0 && (
                                    <p className="text-xs mt-3 text-white/60">
                                        Chuyên gia về: {topics.slice(0, 3).join(', ')}{topics.length > 3 && '...'}
                                    </p>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
