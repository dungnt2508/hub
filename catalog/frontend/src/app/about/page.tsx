import Navbar from "@/components/marketplace/Navbar";
import Footer from "@/components/marketplace/Footer";
import { Users, Code, Zap, Target } from 'lucide-react';

export default function AboutPage() {
  return (
    <div className="min-h-screen bg-white dark:bg-[#0B0C10] text-gray-900 dark:text-slate-200 font-sans">
      <Navbar />

      <main className="container mx-auto px-4 py-12">
        <div className="max-w-4xl mx-auto">
          <header className="text-center mb-12">
            <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-4">
              Về team & dự án
            </h1>
            <p className="text-xl text-gray-600 dark:text-slate-400 max-w-2xl mx-auto">
              Catalog nội bộ các workflow n8n, tool UI và integration pack được xây dựng để phục vụ các use case thực tế
            </p>
          </header>

          <section className="mb-12">
            <div className="bg-gray-50 dark:bg-[#111218] border border-gray-200 dark:border-slate-800 rounded-2xl p-8">
              <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-6 flex items-center gap-3">
                <Target className="h-6 w-6 text-primary" />
                Mục tiêu
              </h2>
              <p className="text-gray-700 dark:text-slate-300 leading-relaxed mb-4">
                Đây là catalog nội bộ các workflow n8n, tool UI và integration pack mà team xây dựng để phục vụ các use case thực tế: tóm tắt đa nguồn, cá nhân hoá bot, dashboard, và tự động hoá nghiệp vụ.
              </p>
              <p className="text-slate-300 leading-relaxed mb-4">
                Mục tiêu của catalog là giúp mọi người trong team (hoặc khách hàng nội bộ) có thể:
              </p>
              <ul className="list-disc list-inside space-y-2 text-gray-700 dark:text-slate-300 ml-4">
                <li>Dễ dàng tra cứu workflow đã có</li>
                <li>Hiểu nhanh giá trị, yêu cầu tích hợp, cách cài đặt cơ bản</li>
                <li>Đề xuất thêm workflow/tool mới nếu còn thiếu</li>
                <li>Tiết kiệm thời gian với các giải pháp plug-and-play</li>
              </ul>
            </div>
          </section>

          <section className="mb-12">
            <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-6 flex items-center gap-3">
              <Users className="h-6 w-6 text-primary" />
              Về team
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-gray-50 dark:bg-[#111218] border border-gray-200 dark:border-slate-800 rounded-2xl p-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">Kinh nghiệm</h3>
                <p className="text-gray-600 dark:text-slate-400 text-sm leading-relaxed">
                  Team có nhiều năm kinh nghiệm trong việc xây dựng và triển khai các giải pháp tự động hóa, tích hợp hệ thống và phát triển workflow n8n cho các doanh nghiệp.
                </p>
              </div>
              <div className="bg-gray-50 dark:bg-[#111218] border border-gray-200 dark:border-slate-800 rounded-2xl p-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">Công nghệ</h3>
                <p className="text-gray-600 dark:text-slate-400 text-sm leading-relaxed">
                  Chuyên về n8n workflow automation, Node.js, TypeScript, PostgreSQL, và các công nghệ hiện đại để xây dựng giải pháp mạnh mẽ và dễ mở rộng.
                </p>
              </div>
            </div>
          </section>

          <section className="mb-12">
            <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-6 flex items-center gap-3">
              <Zap className="h-6 text-primary" />
              Lợi thế cạnh tranh
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-gray-50 dark:bg-[#111218] border border-gray-200 dark:border-slate-800 rounded-2xl p-6">
                <div className="h-12 w-12 rounded-lg bg-primary/20 flex items-center justify-center mb-4">
                  <Code className="h-6 w-6 text-primary" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">Plug-and-Play</h3>
                <p className="text-gray-600 dark:text-slate-400 text-sm">
                  Các workflow và tool được thiết kế để dễ dàng tích hợp, không cần chỉnh sửa nhiều.
                </p>
              </div>
              <div className="bg-gray-50 dark:bg-[#111218] border border-gray-200 dark:border-slate-800 rounded-2xl p-6">
                <div className="h-12 w-12 rounded-lg bg-primary/20 flex items-center justify-center mb-4">
                  <Target className="h-6 w-6 text-primary" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">Tùy chỉnh</h3>
                <p className="text-gray-600 dark:text-slate-400 text-sm">
                  Mọi workflow đều có thể được tùy chỉnh theo yêu cầu cụ thể của từng dự án.
                </p>
              </div>
              <div className="bg-gray-50 dark:bg-[#111218] border border-gray-200 dark:border-slate-800 rounded-2xl p-6">
                <div className="h-12 w-12 rounded-lg bg-primary/20 flex items-center justify-center mb-4">
                  <Users className="h-6 w-6 text-primary" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">Hỗ trợ</h3>
                <p className="text-gray-600 dark:text-slate-400 text-sm">
                  Team hỗ trợ cài đặt và tư vấn miễn phí cho tất cả các workflow trong catalog.
                </p>
              </div>
            </div>
          </section>

          <section className="bg-gray-50 dark:bg-[#111218] border border-gray-200 dark:border-slate-800 rounded-2xl p-8">
            <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-4">Tương lai</h2>
            <p className="text-gray-700 dark:text-slate-300 leading-relaxed">
              Về lâu dài, cấu trúc này có thể nâng cấp thành marketplace (có seller, pricing, review) mà không cần thay đổi routing hay UI quá nhiều. Catalog hiện tại được thiết kế với tầm nhìn mở rộng, đảm bảo tính linh hoạt và khả năng phát triển trong tương lai.
            </p>
          </section>
        </div>
      </main>

      <Footer />
    </div>
  );
}
