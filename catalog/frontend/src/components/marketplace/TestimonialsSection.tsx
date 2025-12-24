'use client';

import { Star, Quote } from 'lucide-react';
import { useState, useEffect } from 'react';

interface Testimonial {
  id: string;
  author: string;
  role: string;
  company: string;
  avatar: string;
  content: string;
  rating: number;
  metric: string;
}

export default function TestimonialsSection() {
  const [testimonials, setTestimonials] = useState<Testimonial[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const mockTestimonials: Testimonial[] = [
      {
        id: '1',
        author: 'Nguyễn Văn A',
        role: 'Marketing Manager',
        company: 'TechStartup VN',
        avatar: '👨‍💼',
        content:
          'Workflow email marketing này giúp chúng tôi tiết kiệm 20 giờ mỗi tuần. Setup dễ dàng, support team rất tuyệt vời!',
        rating: 5,
        metric: 'Giảm 80% thời gian setup email campaign',
      },
      {
        id: '2',
        author: 'Trần Thị B',
        role: 'CRM Specialist',
        company: 'E-commerce Solutions',
        avatar: '👩‍💻',
        content:
          'CRM Sync automation này đã giải quyết vấn đề đồng bộ dữ liệu của chúng tôi. Hiệu suất tăng 300% sau khi sử dụng.',
        rating: 5,
        metric: 'Tăng 300% CRM efficiency',
      },
      {
        id: '3',
        author: 'Lê Hoàng C',
        role: 'Operations Director',
        company: 'Digital Agency',
        avatar: '👨‍🔬',
        content:
          'Chúng tôi đã thử nhiều tool khác nhưng workflows ở đây đơn giản nhất và mạnh mẽ nhất. Highly recommended!',
        rating: 5,
        metric: 'Deploy thành công 15 workflows',
      },
      {
        id: '4',
        author: 'Phạm Minh D',
        role: 'Growth Lead',
        company: 'SaaS Company',
        avatar: '👩‍🚀',
        content:
          'Các template sẵn có giúp team chúng tôi nhanh chóng xây dựng automation pipelines. Đúng như description!',
        rating: 4,
        metric: 'Tăng 150% lead processing speed',
      },
    ];

    setTestimonials(mockTestimonials);
    setLoading(false);
  }, []);

  if (loading) {
    return (
      <div className="flex justify-center items-center py-20">
        <div className="h-8 w-8 border-2 border-primary/30 border-t-primary rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <section className="py-20 px-4 bg-gray-50 dark:bg-slate-900/30">
      <div className="container mx-auto">
        {/* Header */}
        <div className="text-center mb-16">
          <h2 className="text-4xl font-bold text-gray-900 dark:text-white mb-4">
            Câu Chuyện Thành Công Của Khách Hàng
          </h2>
          <p className="text-lg text-gray-600 dark:text-slate-400 max-w-2xl mx-auto">
            Hàng trăm doanh nghiệp đã nâng cao hiệu suất hoạt động nhờ workflows của chúng tôi
          </p>
        </div>

        {/* Testimonials Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-12">
          {testimonials.map((testimonial) => (
            <div
              key={testimonial.id}
              className="bg-white dark:bg-slate-800/50 border border-gray-200 dark:border-slate-700 rounded-2xl p-8 hover:shadow-lg transition-all duration-300 hover:border-primary/50 dark:hover:border-primary/30"
            >
              {/* Quote Icon */}
              <Quote className="h-8 w-8 text-primary/30 mb-4" />

              {/* Rating */}
              <div className="flex gap-1 mb-4">
                {[...Array(testimonial.rating)].map((_, i) => (
                  <Star
                    key={i}
                    className="h-5 w-5 fill-yellow-400 text-yellow-400"
                  />
                ))}
                {[...Array(5 - testimonial.rating)].map((_, i) => (
                  <Star
                    key={i}
                    className="h-5 w-5 text-gray-300 dark:text-slate-600"
                  />
                ))}
              </div>

              {/* Content */}
              <p className="text-gray-700 dark:text-slate-300 mb-6 text-lg leading-relaxed italic">
                "{testimonial.content}"
              </p>

              {/* Metric */}
              <div className="mb-6 p-3 bg-primary/10 dark:bg-primary/5 border border-primary/20 rounded-lg">
                <p className="text-sm font-semibold text-primary">
                  ✨ {testimonial.metric}
                </p>
              </div>

              {/* Author */}
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-full bg-gradient-to-br from-primary to-orange-600 flex items-center justify-center text-2xl">
                  {testimonial.avatar}
                </div>
                <div>
                  <h4 className="font-bold text-gray-900 dark:text-white">
                    {testimonial.author}
                  </h4>
                  <p className="text-sm text-gray-600 dark:text-slate-400">
                    {testimonial.role} at <span className="font-medium">{testimonial.company}</span>
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Stats Bar */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 py-12 border-t border-gray-200 dark:border-slate-700">
          <div className="text-center">
            <p className="text-4xl font-bold text-primary mb-2">500+</p>
            <p className="text-gray-600 dark:text-slate-400">Khách hàng hài lòng</p>
          </div>
          <div className="text-center">
            <p className="text-4xl font-bold text-primary mb-2">4.8/5</p>
            <p className="text-gray-600 dark:text-slate-400">Điểm đánh giá trung bình</p>
          </div>
          <div className="text-center">
            <p className="text-4xl font-bold text-primary mb-2">10K+</p>
            <p className="text-gray-600 dark:text-slate-400">Workflows deployed</p>
          </div>
        </div>
      </div>
    </section>
  );
}

