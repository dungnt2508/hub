import { Search, ArrowRight, Zap, Globe, Shield, Cpu } from 'lucide-react';

export default function Hero() {
    return (
        <div className="relative overflow-hidden bg-white dark:bg-[#0B0C10] py-20 sm:py-32">
            {/* Background Effects */}
            <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1000px] h-[500px] bg-purple-600/20 rounded-full blur-[120px] opacity-50 pointer-events-none"></div>
            <div className="absolute bottom-0 right-0 w-[800px] h-[400px] bg-orange-600/10 rounded-full blur-[100px] opacity-30 pointer-events-none"></div>

            <div className="relative container mx-auto px-4 text-center z-10">
                <div className="inline-flex items-center rounded-full border border-orange-500/20 bg-orange-500/10 px-4 py-1.5 text-sm font-medium text-orange-400 mb-8 backdrop-blur-sm animate-fade-in-up">
                    <span className="flex h-2 w-2 rounded-full bg-orange-500 mr-2 animate-pulse"></span>
                        Cung cấp giải pháp tự động hóa cho doanh nghiệp 🔥
                    <ArrowRight className="ml-2 h-4 w-4" />
                </div>

                <h1 className="mx-auto max-w-5xl text-5xl font-bold tracking-tight text-gray-900 dark:text-white sm:text-7xl mb-8 leading-tight">
                    Tự động hóa công việc với <br />
                    <span className="text-transparent bg-clip-text bg-gradient-to-r from-orange-400 via-pink-500 to-purple-600">
                        n8n workflows chuyên nghiệp
                    </span>
                </h1>

                <p className="mx-auto max-w-2xl text-lg text-gray-600 dark:text-slate-400 mb-12 leading-relaxed">
                    Cung cấp giải pháp tự động hóa hàng đầu cho n8n workflows.   <br />
                    Khám phá hàng trăm giải pháp tự động hóa được tối ưu sẵn, 
                    giúp doanh nghiệp tiết kiệm hàng giờ làm việc mỗi ngày và tăng năng suất lên 10x.                
                </p>

                <div className="mx-auto max-w-2xl relative mb-12 group">
                    <div className="flex items-center gap-2 bg-white dark:bg-slate-900/80 backdrop-blur-xl rounded-2xl border border-gray-200/80 dark:border-slate-700/50 shadow-2xl shadow-black/10 dark:shadow-black/50 ring-1 ring-inset ring-gray-200/50 dark:ring-slate-700/30 p-2 transition-all duration-300 group-hover:shadow-2xl group-hover:shadow-primary/10 group-focus-within:ring-2 group-focus-within:ring-primary/50 group-focus-within:border-primary/30">
                        <div className="flex items-center justify-center px-4 pointer-events-none">
                            <Search className="h-5 w-5 text-gray-400 dark:text-slate-500 group-focus-within:text-primary transition-colors duration-300" />
                        </div>
                        <input
                            type="text"
                            className="flex-1 bg-transparent border-0 outline-none text-gray-900 dark:text-white placeholder:text-gray-400 dark:placeholder:text-slate-500 sm:text-lg py-3 pr-2"
                            placeholder="Tìm kiếm: 'Tự động hóa Instagram', 'Marketing Email', 'CRM Sync', 'SEO Content'..."
                        />
                        <button className="bg-primary hover:bg-[#FF8559] text-white px-6 py-3 rounded-xl text-sm font-semibold transition-all duration-300 shadow-lg shadow-primary/25 hover:shadow-xl hover:shadow-primary/40 hover:scale-[1.02] active:scale-[0.98] whitespace-nowrap">
                            Tìm kiếm
                        </button>
                    </div>
                </div>

                <div className="flex flex-wrap justify-center gap-3">
                    {[
                        { name: 'Marketing & Social Media', icon: Zap },
                        { name: 'Sales & CRM', icon: Globe },
                        { name: 'AI & Tự Động Hóa', icon: Cpu },
                        { name: 'Bảo Mật & Tích Hợp', icon: Shield },
                    ].map((category) => (
                        <button key={category.name} className="flex items-center gap-2 rounded-full border border-gray-200 dark:border-slate-800 bg-gray-50 dark:bg-slate-900/40 px-5 py-2 text-sm font-medium text-gray-700 dark:text-slate-300 hover:border-primary/50 hover:text-primary dark:hover:bg-slate-800/60 transition-all">
                            <category.icon className="h-4 w-4" />
                            {category.name}
                        </button>
                    ))}
                </div>
            </div>
        </div>
    );
}
