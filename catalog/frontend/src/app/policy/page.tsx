import Navbar from "@/components/marketplace/Navbar";
import Footer from "@/components/marketplace/Footer";
import { Shield, FileText, Lock, HelpCircle } from 'lucide-react';

export default function PolicyPage() {
  return (
    <div className="min-h-screen bg-white dark:bg-[#0B0C10] text-gray-900 dark:text-slate-200 font-sans">
      <Navbar />

      <main className="container mx-auto px-4 py-12">
        <div className="max-w-4xl mx-auto">
          <header className="text-center mb-12">
            <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-4">
              Điều khoản & Chính sách
            </h1>
            <p className="text-xl text-gray-600 dark:text-slate-400 max-w-2xl mx-auto">
              Mục này mô tả cách sử dụng workflow, quyền truy cập dữ liệu và phạm vi hỗ trợ của team
            </p>
          </header>

          <div className="space-y-6">
            <section className="bg-gray-50 dark:bg-[#111218] border border-gray-200 dark:border-slate-800 rounded-2xl p-8">
              <div className="flex items-center gap-3 mb-4">
                <div className="h-10 w-10 rounded-lg bg-primary/20 flex items-center justify-center">
                  <FileText className="h-5 w-5 text-primary" />
                </div>
                <h2 className="text-2xl font-semibold text-gray-900 dark:text-white">
                  1. Phạm vi sử dụng
                </h2>
              </div>
              <div className="text-gray-700 dark:text-slate-300 leading-relaxed space-y-3">
                <p>
                  Các workflow/tool trong catalog hiện được dùng cho mục đích nội bộ, phục vụ thử nghiệm và vận hành các use case cụ thể.
                </p>
                <p>
                  Người dùng được phép:
                </p>
                <ul className="list-disc list-inside space-y-2 ml-4">
                  <li>Tải về và sử dụng workflow/tool cho mục đích nội bộ</li>
                  <li>Chỉnh sửa và tùy biến theo nhu cầu cụ thể</li>
                  <li>Chia sẻ với các thành viên trong team</li>
                </ul>
                <p>
                  Người dùng không được phép:
                </p>
                <ul className="list-disc list-inside space-y-2 ml-4">
                  <li>Bán hoặc phân phối lại workflow/tool cho bên thứ ba</li>
                  <li>Sử dụng cho mục đích thương mại bên ngoài tổ chức</li>
                </ul>
              </div>
            </section>

            <section className="bg-gray-50 dark:bg-[#111218] border border-gray-200 dark:border-slate-800 rounded-2xl p-8">
              <div className="flex items-center gap-3 mb-4">
                <div className="h-10 w-10 rounded-lg bg-primary/20 flex items-center justify-center">
                  <Lock className="h-5 w-5 text-primary" />
                </div>
                <h2 className="text-2xl font-semibold text-gray-900 dark:text-white">
                  2. Dữ liệu & Bảo mật
                </h2>
              </div>
              <div className="text-gray-700 dark:text-slate-300 leading-relaxed space-y-3">
                <p>
                  Khi tích hợp với hệ thống thật (CRM, Email, Notion...), cần đảm bảo đã được cấp quyền và tuân thủ chính sách bảo mật của công ty/khách hàng.
                </p>
                <p>
                  Team cam kết:
                </p>
                <ul className="list-disc list-inside space-y-2 ml-4">
                  <li>Không lưu trữ dữ liệu nhạy cảm của người dùng</li>
                  <li>Tuân thủ các quy định về bảo mật và quyền riêng tư</li>
                  <li>Chỉ sử dụng dữ liệu cần thiết cho mục đích vận hành workflow</li>
                </ul>
                <p className="text-sm text-gray-600 dark:text-slate-400">
                  Người dùng chịu trách nhiệm về việc bảo vệ API keys, credentials và thông tin nhạy cảm khi sử dụng các workflow.
                </p>
              </div>
            </section>

            <section className="bg-gray-50 dark:bg-[#111218] border border-gray-200 dark:border-slate-800 rounded-2xl p-8">
              <div className="flex items-center gap-3 mb-4">
                <div className="h-10 w-10 rounded-lg bg-primary/20 flex items-center justify-center">
                  <HelpCircle className="h-5 w-5 text-primary" />
                </div>
                <h2 className="text-2xl font-semibold text-gray-900 dark:text-white">
                  3. Hỗ trợ kỹ thuật
                </h2>
              </div>
              <div className="text-gray-700 dark:text-slate-300 leading-relaxed space-y-3">
                <p>
                  Team hỗ trợ cài đặt cơ bản cho từng workflow/tool, phần tùy biến thêm sẽ được trao đổi riêng theo nhu cầu.
                </p>
                <p>
                  Phạm vi hỗ trợ bao gồm:
                </p>
                <ul className="list-disc list-inside space-y-2 ml-4">
                  <li>Hướng dẫn cài đặt và cấu hình ban đầu</li>
                  <li>Giải đáp thắc mắc về cách sử dụng workflow</li>
                  <li>Hỗ trợ xử lý lỗi cơ bản</li>
                  <li>Tư vấn về cách tùy biến workflow</li>
                </ul>
                <p>
                  Để nhận hỗ trợ, vui lòng liên hệ qua{' '}
                  <a href="/contact" className="text-primary hover:text-[#FF8559] transition-colors">
                    trang liên hệ
                  </a>
                  {' '}hoặc Telegram/Zalo.
                </p>
              </div>
            </section>

            <section className="bg-gray-50 dark:bg-[#111218] border border-gray-200 dark:border-slate-800 rounded-2xl p-8">
              <div className="flex items-center gap-3 mb-4">
                <div className="h-10 w-10 rounded-lg bg-primary/20 flex items-center justify-center">
                  <Shield className="h-5 w-5 text-primary" />
                </div>
                <h2 className="text-2xl font-semibold text-gray-900 dark:text-white">
                  4. Miễn trừ trách nhiệm
                </h2>
              </div>
              <div className="text-gray-700 dark:text-slate-300 leading-relaxed space-y-3">
                <p>
                  Các workflow/tool được cung cấp "như hiện tại" (as-is) và team không đảm bảo:
                </p>
                <ul className="list-disc list-inside space-y-2 ml-4">
                  <li>Workflow sẽ hoạt động hoàn hảo trong mọi trường hợp</li>
                  <li>Không có lỗi hoặc sự cố trong quá trình sử dụng</li>
                  <li>Tương thích với mọi phiên bản n8n hoặc hệ thống</li>
                </ul>
                <p>
                  Người dùng chịu trách nhiệm về việc kiểm tra và test workflow trước khi sử dụng trong môi trường production.
                </p>
              </div>
            </section>

            <section className="bg-gray-50 dark:bg-[#111218] border border-gray-200 dark:border-slate-800 rounded-2xl p-8">
              <h2 className="text-2xl font-semibold text-white mb-4">
                5. Cập nhật chính sách
              </h2>
              <p className="text-gray-700 dark:text-slate-300 leading-relaxed">
                Team có quyền cập nhật các điều khoản và chính sách này bất cứ lúc nào. Người dùng sẽ được thông báo về các thay đổi quan trọng. Việc tiếp tục sử dụng catalog sau khi có cập nhật được coi là chấp nhận các điều khoản mới.
              </p>
            </section>

            <div className="text-center pt-8">
              <p className="text-gray-600 dark:text-slate-400 text-sm mb-4">
                Có câu hỏi về điều khoản sử dụng?
              </p>
              <a
                href="/contact"
                className="inline-flex items-center gap-2 px-6 py-3 bg-primary hover:bg-[#FF8559] text-white font-semibold rounded-lg transition-colors"
              >
                Liên hệ team
              </a>
            </div>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
