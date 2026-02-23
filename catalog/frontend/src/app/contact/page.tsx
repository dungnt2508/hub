'use client';

import { useState } from 'react';
import Navbar from "@/components/marketplace/Navbar";
import Footer from "@/components/marketplace/Footer";
import { Mail, MessageCircle, Send, CheckCircle, AlertCircle } from 'lucide-react';
import Link from 'next/link';
import toast from 'react-hot-toast';

export default function ContactPage() {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    need: '',
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const validate = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Vui lòng nhập tên của bạn';
    }

    if (!formData.email.trim()) {
      newErrors.email = 'Vui lòng nhập email';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Email không hợp lệ';
    }

    if (!formData.need.trim()) {
      newErrors.need = 'Vui lòng mô tả nhu cầu của bạn';
    } else if (formData.need.trim().length < 10) {
      newErrors.need = 'Vui lòng mô tả chi tiết hơn (ít nhất 10 ký tự)';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validate()) {
      return;
    }

    setLoading(true);
    
    try {
      // TODO: Replace with actual API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      toast.success('Gửi yêu cầu thành công! Team sẽ liên hệ với bạn sớm nhất.');
      setSubmitted(true);
      setFormData({ name: '', email: '', need: '' });
    } catch (error) {
      toast.error('Có lỗi xảy ra. Vui lòng thử lại sau.');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  return (
    <div className="min-h-screen bg-white dark:bg-[#0B0C10] text-gray-900 dark:text-slate-200 font-sans">
      <Navbar />

      <main className="container mx-auto px-4 py-12">
        <div className="max-w-2xl mx-auto">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-3">
              Liên hệ team
            </h1>
            <p className="text-gray-600 dark:text-slate-400">
              Mô tả nhanh nhu cầu của bạn, team sẽ hỗ trợ tư vấn và cài đặt workflow/tool phù hợp.
            </p>
          </div>

          {submitted ? (
            <div className="bg-gray-50 dark:bg-[#111218] border border-gray-200 dark:border-slate-800 rounded-2xl p-8 text-center">
              <CheckCircle className="h-16 w-16 text-primary mx-auto mb-4" />
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                Cảm ơn bạn đã liên hệ!
              </h2>
              <p className="text-gray-600 dark:text-slate-400 mb-6">
                Team sẽ xem xét yêu cầu và phản hồi trong thời gian sớm nhất.
              </p>
              <button
                onClick={() => setSubmitted(false)}
                className="text-primary hover:text-[#FF8559] transition-colors"
              >
                Gửi yêu cầu khác
              </button>
            </div>
          ) : (
            <>
              <form onSubmit={handleSubmit} className="space-y-5 bg-gray-50 dark:bg-[#111218] border border-gray-200 dark:border-slate-800 rounded-2xl p-6 mb-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-slate-200 mb-2">
                    Tên <span className="text-red-400">*</span>
                  </label>
                  <input
                    type="text"
                    name="name"
                    value={formData.name}
                    onChange={handleChange}
                    className={`w-full rounded-lg border ${
                      errors.name ? 'border-red-500' : 'border-gray-200 dark:border-slate-700'
                    } bg-white dark:bg-slate-900/40 px-4 py-3 text-gray-900 dark:text-white placeholder:text-gray-400 dark:placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all`}
                    placeholder="Tên của bạn"
                  />
                  {errors.name && (
                    <p className="mt-1 text-sm text-red-400 flex items-center gap-1">
                      <AlertCircle className="h-3 w-3" />
                      {errors.name}
                    </p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-slate-200 mb-2">
                    Email <span className="text-red-400">*</span>
                  </label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400 dark:text-slate-500" />
                    <input
                      type="email"
                      name="email"
                      value={formData.email}
                      onChange={handleChange}
                      className={`w-full pl-10 pr-4 py-3 rounded-lg border ${
                        errors.email ? 'border-red-500' : 'border-gray-200 dark:border-slate-700'
                      } bg-white dark:bg-slate-900/40 text-gray-900 dark:text-white placeholder:text-gray-400 dark:placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all`}
                      placeholder="you@example.com"
                    />
                  </div>
                  {errors.email && (
                    <p className="mt-1 text-sm text-red-400 flex items-center gap-1">
                      <AlertCircle className="h-3 w-3" />
                      {errors.email}
                    </p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-slate-200 mb-2">
                    Nhu cầu <span className="text-red-400">*</span>
                  </label>
                  <textarea
                    name="need"
                    value={formData.need}
                    onChange={handleChange}
                    rows={5}
                    className={`w-full rounded-lg border ${
                      errors.need ? 'border-red-500' : 'border-gray-200 dark:border-slate-700'
                    } bg-white dark:bg-slate-900/40 px-4 py-3 text-gray-900 dark:text-white placeholder:text-gray-400 dark:placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all resize-none`}
                    placeholder="Bạn muốn tự động hoá quy trình nào? Đang dùng Notion, Telegram, Email hay hệ thống khác? Mô tả chi tiết nhu cầu của bạn..."
                  />
                  {errors.need && (
                    <p className="mt-1 text-sm text-red-400 flex items-center gap-1">
                      <AlertCircle className="h-3 w-3" />
                      {errors.need}
                    </p>
                  )}
                  <p className="mt-1 text-xs text-gray-500 dark:text-slate-500">
                    {formData.need.length}/10 ký tự tối thiểu
                  </p>
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-primary hover:bg-[#FF8559] text-white font-semibold py-3 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  {loading ? (
                    <>
                      <div className="h-4 w-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                      <span>Đang gửi...</span>
                    </>
                  ) : (
                    <>
                      <Send className="h-4 w-4" />
                      <span>Gửi yêu cầu</span>
                    </>
                  )}
                </button>
              </form>

              <div className="bg-gray-50 dark:bg-[#111218] border border-gray-200 dark:border-slate-800 rounded-2xl p-6">
                <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                  <MessageCircle className="h-4 w-4 text-primary" />
                  Liên hệ trực tiếp
                </h3>
                <p className="text-sm text-gray-600 dark:text-slate-400 mb-4">
                  Nếu cần trao đổi nhanh, bạn có thể liên hệ trực tiếp qua:
                </p>
                <div className="flex flex-wrap gap-3">
                  <a
                    href="https://t.me/gsnake6789"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 px-4 py-2 bg-gray-100 dark:bg-slate-900/50 border border-gray-200 dark:border-slate-800 rounded-lg text-gray-700 dark:text-slate-300 hover:bg-gray-200 dark:hover:bg-slate-800/50 hover:text-gray-900 dark:hover:text-white transition-colors"
                  >
                    <MessageCircle className="h-4 w-4" />
                    Telegram
                  </a>
                  <a
                    href="https://zalo.me/0937974444"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 px-4 py-2 bg-gray-100 dark:bg-slate-900/50 border border-gray-200 dark:border-slate-800 rounded-lg text-gray-700 dark:text-slate-300 hover:bg-gray-200 dark:hover:bg-slate-800/50 hover:text-gray-900 dark:hover:text-white transition-colors"
                  >
                    <MessageCircle className="h-4 w-4" />
                    Zalo
                  </a>
                  <a
                    href="mailto:gsnake6789@gmail.com"
                    className="inline-flex items-center gap-2 px-4 py-2 bg-gray-100 dark:bg-slate-900/50 border border-gray-200 dark:border-slate-800 rounded-lg text-gray-700 dark:text-slate-300 hover:bg-gray-200 dark:hover:bg-slate-800/50 hover:text-gray-900 dark:hover:text-white transition-colors"
                  >
                    <Mail className="h-4 w-4" />
                    Email
                  </a>
                </div>
                <p className="text-xs text-gray-500 dark:text-slate-500 mt-4">
                  Team hỗ trợ cài đặt và tư vấn miễn phí cho các workflow/tool trong catalog.
                </p>
              </div>
            </>
          )}
        </div>
      </main>

      <Footer />
    </div>
  );
}
