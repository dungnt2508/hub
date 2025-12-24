import Link from 'next/link';
import { Twitter, Github, Linkedin, Mail } from 'lucide-react';

export default function Footer() {
    return (
        <footer className="bg-gray-50 dark:bg-[#050608] border-t border-gray-200 dark:border-slate-900 pt-16 pb-8">
            <div className="container mx-auto px-4">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-12 mb-16">
                    <div className="lg:col-span-2">
                        <div className="flex items-center gap-2 mb-6">
                            <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-orange-500 to-pink-600 flex items-center justify-center">
                                <span className="font-bold text-white">n8n</span>
                            </div>
                            <span className="text-xl font-bold text-gray-900 dark:text-white">Market</span>
                        </div>
                        <p className="text-gray-600 dark:text-slate-400 mb-6 max-w-sm leading-relaxed">
                            Marketplace hàng đầu cho n8n workflows. Khám phá hàng trăm giải pháp tự động hóa được tối ưu sẵn, 
                            giúp doanh nghiệp tiết kiệm thời gian và tăng năng suất đáng kể.
                        </p>
                        <div className="flex gap-4">
                            <Link href="#" className="h-10 w-10 rounded-full bg-gray-200 dark:bg-slate-900 flex items-center justify-center text-gray-600 dark:text-slate-400 hover:bg-primary hover:text-white transition-all">
                                <Twitter className="h-5 w-5" />
                            </Link>
                            <Link href="#" className="h-10 w-10 rounded-full bg-gray-200 dark:bg-slate-900 flex items-center justify-center text-gray-600 dark:text-slate-400 hover:bg-primary hover:text-white transition-all">
                                <Github className="h-5 w-5" />
                            </Link>
                            <Link href="#" className="h-10 w-10 rounded-full bg-gray-200 dark:bg-slate-900 flex items-center justify-center text-gray-600 dark:text-slate-400 hover:bg-primary hover:text-white transition-all">
                                <Linkedin className="h-5 w-5" />
                            </Link>
                        </div>
                    </div>

                    <div>
                        <h4 className="text-gray-900 dark:text-white font-bold mb-6">Tài nguyên</h4>
                        <ul className="space-y-4 text-sm text-gray-600 dark:text-slate-400">
                            <li><Link href="#" className="hover:text-primary transition-colors">Tài liệu</Link></li>
                            <li><Link href="#" className="hover:text-primary transition-colors">Blog</Link></li>
                            <li><Link href="#" className="hover:text-primary transition-colors">Cộng đồng</Link></li>
                            <li><Link href="#" className="hover:text-primary transition-colors">Trung tâm hỗ trợ</Link></li>
                        </ul>
                    </div>

                    <div>
                        <h4 className="text-gray-900 dark:text-white font-bold mb-6">Công ty</h4>
                        <ul className="space-y-4 text-sm text-gray-600 dark:text-slate-400">
                            <li><Link href="#" className="hover:text-primary transition-colors">Giới thiệu</Link></li>
                            <li><Link href="#" className="hover:text-primary transition-colors">Tuyển dụng</Link></li>
                            <li><Link href="#" className="hover:text-primary transition-colors">Chính sách riêng tư</Link></li>
                            <li><Link href="#" className="hover:text-primary transition-colors">Điều khoản sử dụng</Link></li>
                        </ul>
                    </div>

                    <div>
                        <h4 className="text-gray-900 dark:text-white font-bold mb-6">Đăng ký nhận tin</h4>
                        <p className="text-sm text-gray-600 dark:text-slate-400 mb-4">Đăng ký để nhận thông tin mới nhất về chúng tôi.</p>
                        <div className="flex gap-2 bg-white dark:bg-slate-900/80 border border-gray-200/80 dark:border-slate-700/50 rounded-lg p-1 shadow-sm ring-1 ring-inset ring-gray-200/50 dark:ring-slate-700/30 focus-within:ring-2 focus-within:ring-primary/50 focus-within:border-primary/30 transition-all duration-300">
                            <input
                                type="email"
                                placeholder="Nhập email của bạn"
                                className="flex-1 bg-transparent border-0 outline-none px-3 py-2 text-sm text-gray-900 dark:text-white placeholder:text-gray-400 dark:placeholder:text-slate-500"
                            />
                            <button className="bg-primary hover:bg-[#FF8559] text-white px-4 py-2 rounded-md text-sm font-semibold transition-all duration-300 shadow-md shadow-primary/25 hover:shadow-lg hover:shadow-primary/40 hover:scale-[1.02] active:scale-[0.98] whitespace-nowrap">
                                Đăng ký
                            </button>
                        </div>
                    </div>
                </div>

                <div className="border-t border-gray-200 dark:border-slate-900 pt-8 flex flex-col md:flex-row justify-between items-center gap-4">
                    <p className="text-gray-500 dark:text-slate-500 text-sm">© 2026 workflows market. all rights reserved.</p>
                    <div className="flex gap-6 text-sm text-gray-500 dark:text-slate-500">
                        <span>developed by gsnake team</span>
                    </div>
                </div>
            </div>
        </footer>
    );
}
