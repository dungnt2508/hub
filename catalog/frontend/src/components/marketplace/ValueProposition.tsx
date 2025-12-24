'use client';

import { Clock, Lock, Zap } from 'lucide-react';

interface ValueProp {
  icon: React.ReactNode;
  title: string;
  description: string;
  highlights: string[];
}

export default function ValueProposition() {
  const valueProps: ValueProp[] = [
    {
      icon: <Clock className="h-10 w-10" />,
      title: 'Tiết Kiệm Thời Gian',
      description: 'Các workflow sẵn sàng plug-and-play',
      highlights: [
        '100+ workflows sẵn sàng',
        'Deploy trong phút',
        'Giảm 80% setup time',
      ],
    },
    {
      icon: <Lock className="h-10 w-10" />,
      title: 'Bảo Mật & Tuân Thủ',
      description: 'Quét bảo mật tự động cho mỗi workflow',
      highlights: [
        'Security scan bắt buộc',
        'Approved bởi team experts',
        'No credentials in code',
      ],
    },
    {
      icon: <Zap className="h-10 w-10" />,
      title: 'Hỗ Trợ 24/7 & Cộng Đồng',
      description: 'Team phát triển tích cực + seller support',
      highlights: [
        'Live support từ team',
        'Active community',
        'Regular updates & improvements',
      ],
    },
  ];

  return (
    <section className="py-20 px-4 bg-white dark:bg-[#0B0C10]">
      <div className="container mx-auto">
        {/* Header */}
        <div className="text-center mb-16">
          <h2 className="text-4xl font-bold text-gray-900 dark:text-white mb-4">
            Tại Sao Chọn n8n Workflows Của Chúng Tôi?
          </h2>
          <p className="text-lg text-gray-600 dark:text-slate-400 max-w-2xl mx-auto">
            Chúng tôi cung cấp giải pháp tự động hóa tiết kiệm chi phí, an toàn và dễ sử dụng
          </p>
        </div>

        {/* Value Props Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-16">
          {valueProps.map((prop, index) => (
            <div
              key={index}
              className="group bg-gradient-to-br from-white to-gray-50 dark:from-slate-900/50 dark:to-slate-800/30 border border-gray-200 dark:border-slate-800 rounded-2xl p-10 hover:shadow-lg hover:border-primary/50 dark:hover:border-primary/30 transition-all duration-300 hover:-translate-y-1"
            >
              {/* Icon */}
              <div className="inline-flex p-4 rounded-xl bg-primary/10 text-primary mb-6 group-hover:bg-primary group-hover:text-white group-hover:scale-110 transition-all duration-300">
                {prop.icon}
              </div>

              {/* Title & Description */}
              <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-3">
                {prop.title}
              </h3>
              <p className="text-gray-600 dark:text-slate-400 mb-6">
                {prop.description}
              </p>

              {/* Highlights */}
              <ul className="space-y-3">
                {prop.highlights.map((highlight, i) => (
                  <li
                    key={i}
                    className="flex items-start gap-3 text-gray-700 dark:text-slate-300"
                  >
                    <span className="inline-flex items-center justify-center h-5 w-5 rounded-full bg-primary/20 text-primary text-xs font-bold flex-shrink-0 mt-0.5">
                      ✓
                    </span>
                    <span>{highlight}</span>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Comparison Section */}
        <div className="bg-gray-50 dark:bg-slate-800/50 border border-gray-200 dark:border-slate-700 rounded-2xl p-8 md:p-12">
          <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-8 text-center">
            So Sánh Với Các Giải Pháp Khác
          </h3>

          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200 dark:border-slate-700">
                  <th className="text-left py-4 px-4 font-semibold text-gray-900 dark:text-white">
                    Tính Năng
                  </th>
                  <th className="text-center py-4 px-4 font-semibold text-primary">
                    gsnake
                  </th>
                  <th className="text-center py-4 px-4 font-semibold text-gray-600 dark:text-slate-400">
                    Competitors
                  </th>
                </tr>
              </thead>
              <tbody>
                {[
                  {
                    feature: 'Pre-built Workflows',
                    gsnake: true,
                    competitors: false,
                  },
                  {
                    feature: 'Security Scan',
                    gsnake: true,
                    competitors: false,
                  },
                  {
                    feature: 'Community Support',
                    gsnake: true,
                    competitors: true,
                  },
                  {
                    feature: 'Free Templates',
                    gsnake: true,
                    competitors: false,
                  },
                  {
                    feature: 'Premium Workflows',
                    gsnake: true,
                    competitors: true,
                  },
                  { feature: 'Lifetime Updates', gsnake: true, competitors: false },
                ].map((row, i) => (
                  <tr
                    key={i}
                    className="border-b border-gray-100 dark:border-slate-800 hover:bg-white dark:hover:bg-slate-900/30 transition-colors"
                  >
                    <td className="py-4 px-4 text-gray-700 dark:text-slate-300">
                      {row.feature}
                    </td>
                    <td className="py-4 px-4 text-center">
                      {row.gsnake ? (
                        <span className="inline-flex items-center justify-center h-6 w-6 rounded-full bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400">
                          ✓
                        </span>
                      ) : (
                        <span className="text-gray-400">—</span>
                      )}
                    </td>
                    <td className="py-4 px-4 text-center">
                      {row.competitors ? (
                        <span className="inline-flex items-center justify-center h-6 w-6 rounded-full bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400">
                          ✓
                        </span>
                      ) : (
                        <span className="text-gray-400">—</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Bottom CTA */}
        <div className="mt-16 text-center">
          <p className="text-gray-600 dark:text-slate-400 mb-6">
            Sẵn sàng nâng cấp quy trình tự động hóa của bạn?
          </p>
          <button className="inline-flex items-center gap-2 bg-primary hover:bg-[#FF8559] text-white px-8 py-4 rounded-full font-semibold transition-all duration-300 hover:shadow-lg hover:shadow-primary/30 hover:scale-105">
            <span>Khám Phá Workflows Ngay</span>
            <span>→</span>
          </button>
        </div>
      </div>
    </section>
  );
}

