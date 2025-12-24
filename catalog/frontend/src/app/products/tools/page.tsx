'use client';

import { useState } from 'react';
import Navbar from "@/components/marketplace/Navbar";
import Footer from "@/components/marketplace/Footer";
import TemplateCard from "@/components/marketplace/TemplateCard";
import { Search, X, ArrowLeft } from 'lucide-react';
import Link from 'next/link';

const MOCK_TOOLS = [
  {
    id: 2,
    title: "Tool: Dashboard xem lịch tóm tắt",
    description:
      "UI dashboard để xem danh sách bài đã tóm tắt theo user, filter theo nguồn và thời gian.",
    price: "Miễn phí",
    author: "Team gsnake",
    downloads: 80,
    rating: 4.7,
    tags: ["Tool", "Dashboard"],
  },
  {
    id: 6,
    title: "Tool: Quản lý persona user",
    description:
      "Giao diện quản lý và chỉnh sửa persona cho từng user, bao gồm tone, style, topics.",
    price: "Miễn phí",
    author: "Team gsnake",
    downloads: 65,
    rating: 4.6,
    tags: ["Tool", "UI", "Persona"],
  },
];

export default function ToolsPage() {
  const [searchQuery, setSearchQuery] = useState('');

  const filteredTools = MOCK_TOOLS.filter((tool) => {
    const matchesSearch = 
      tool.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      tool.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      tool.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()));
    
    return matchesSearch;
  });

  return (
    <div className="min-h-screen bg-[#0B0C10] text-slate-200 font-sans">
      <Navbar />

      <main className="container mx-auto px-4 py-12">
        <Link
          href="/products"
          className="inline-flex items-center text-slate-400 hover:text-white mb-6 transition-colors"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Quay lại danh sách sản phẩm
        </Link>

        <header className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">
            Tất cả Tool
          </h1>
          <p className="text-slate-400">
            Danh sách các tool UI và dashboard có sẵn trong catalog
          </p>
        </header>

        {/* Search */}
        <section className="mb-8">
          <div className="relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-500" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Tìm kiếm tool..."
              className="w-full pl-12 pr-4 py-3 bg-slate-900/50 border border-slate-800 rounded-lg text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-500 hover:text-white transition-colors"
              >
                <X className="h-5 w-5" />
              </button>
            )}
          </div>
        </section>

        {/* Results */}
        <section>
          <div className="mb-4 text-sm text-slate-400">
            Tìm thấy {filteredTools.length} tool
          </div>

          {filteredTools.length === 0 ? (
            <div className="text-center py-12 bg-[#111218] border border-slate-800 rounded-2xl">
              <p className="text-slate-400 mb-2">Không tìm thấy tool nào</p>
              <p className="text-sm text-slate-500">Thử thay đổi từ khóa tìm kiếm</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8">
              {filteredTools.map((tool) => (
                <TemplateCard
                  key={tool.id}
                  id={tool.id}
                  title={tool.title}
                  description={tool.description}
                  price={tool.price}
                  author={tool.author}
                  downloads={tool.downloads}
                  rating={tool.rating}
                  tags={tool.tags}
                />
              ))}
            </div>
          )}
        </section>
      </main>

      <Footer />
    </div>
  );
}

