'use client';

import { useState } from 'react';
import Navbar from "@/components/marketplace/Navbar";
import Footer from "@/components/marketplace/Footer";
import TemplateCard from "@/components/marketplace/TemplateCard";
import { Search, X, ArrowLeft } from 'lucide-react';
import Link from 'next/link';

const MOCK_WORKFLOWS = [
  {
    id: 1,
    title: "Workflow: Tóm tắt đa nguồn (URL/RSS/File)",
    description:
      "Workflow n8n cho phép lấy nội dung từ nhiều nguồn, làm sạch, gửi qua LLM và lưu summary + insights.",
    price: "Miễn phí",
    author: "Team gsnake",
    downloads: 120,
    rating: 4.9,
    tags: ["Workflow", "Summarization"],
  },
  {
    id: 3,
    title: "Workflow: Tự động gửi email báo cáo",
    description:
      "Tự động tổng hợp dữ liệu và gửi email báo cáo định kỳ cho team.",
    price: "Miễn phí",
    author: "Team gsnake",
    downloads: 95,
    rating: 4.8,
    tags: ["Workflow", "Email"],
  },
  {
    id: 5,
    title: "Workflow: Đồng bộ dữ liệu Notion → Database",
    description:
      "Tự động đồng bộ dữ liệu từ Notion database vào PostgreSQL theo lịch trình.",
    price: "Miễn phí",
    author: "Team gsnake",
    downloads: 150,
    rating: 4.9,
    tags: ["Workflow", "Notion", "Database"],
  },
];

export default function WorkflowsPage() {
  const [searchQuery, setSearchQuery] = useState('');

  const filteredWorkflows = MOCK_WORKFLOWS.filter((workflow) => {
    const matchesSearch = 
      workflow.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      workflow.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      workflow.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()));
    
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
            Tất cả Workflow
          </h1>
          <p className="text-slate-400">
            Danh sách các workflow n8n có sẵn trong catalog
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
              placeholder="Tìm kiếm workflow..."
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
            Tìm thấy {filteredWorkflows.length} workflow
          </div>

          {filteredWorkflows.length === 0 ? (
            <div className="text-center py-12 bg-[#111218] border border-slate-800 rounded-2xl">
              <p className="text-slate-400 mb-2">Không tìm thấy workflow nào</p>
              <p className="text-sm text-slate-500">Thử thay đổi từ khóa tìm kiếm</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8">
              {filteredWorkflows.map((workflow) => (
                <TemplateCard
                  key={workflow.id}
                  id={workflow.id}
                  title={workflow.title}
                  description={workflow.description}
                  price={workflow.price}
                  author={workflow.author}
                  downloads={workflow.downloads}
                  rating={workflow.rating}
                  tags={workflow.tags}
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

