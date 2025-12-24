'use client';

import Navbar from '@/components/marketplace/Navbar';
import Footer from '@/components/marketplace/Footer';
import { Check, Star, Download, Shield, Clock, ArrowLeft } from 'lucide-react';
import Link from 'next/link';
import { useParams } from 'next/navigation';

// Mock data - in a real app this would come from an API based on the ID
const MOCK_TEMPLATE = {
    id: 1,
    title: 'Advanced SEO Article Generator',
    description: 'Generate SEO-optimized articles with keyword research, outlining, and writing using GPT-4 and Google Search. This workflow automates the entire content creation process from keyword to final draft.',
    longDescription: `
    <p>Stop spending hours writing SEO content manually. This n8n workflow automates the entire process of creating high-ranking articles.</p>
    <br/>
    <h3>How it works:</h3>
    <ul class="list-disc pl-5 space-y-2 mt-2">
      <li><strong>Keyword Research:</strong> It starts by analyzing your target keyword using Google Search results to understand search intent.</li>
      <li><strong>Outlining:</strong> GPT-4 generates a comprehensive outline based on the top-ranking competitors.</li>
      <li><strong>Drafting:</strong> The workflow writes the article section by section to ensure depth and quality.</li>
      <li><strong>Optimization:</strong> Finally, it reviews the content for SEO best practices and keyword density.</li>
    </ul>
    <br/>
    <p>Perfect for agencies, bloggers, and content marketing teams looking to scale their production.</p>
  `,
    price: 29,
    author: 'SEO Master',
    downloads: 1240,
    rating: 4.9,
    reviews: 128,
    lastUpdated: '2 days ago',
    version: '2.1.0',
    features: [
        'GPT-4 Turbo Integration',
        'Google Search Console API',
        'WordPress Auto-Posting',
        'Plagiarism Check',
        'SEO Scoring'
    ],
    requirements: [
        'n8n version 1.0+',
        'OpenAI API Key',
        'Google Custom Search API'
    ]
};

export default function TemplateDetail() {
    const params = useParams();
    // In a real app, fetch data using params.id

    return (
        <div className="min-h-screen bg-[#0B0C10] text-slate-200 font-sans selection:bg-orange-500/30">
            <Navbar />

            <main className="container mx-auto px-4 py-12">
                <Link href="/" className="inline-flex items-center text-slate-400 hover:text-white mb-8 transition-colors">
                    <ArrowLeft className="h-4 w-4 mr-2" />
                    Back to Marketplace
                </Link>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
                    {/* Main Content */}
                    <div className="lg:col-span-2">
                        <div className="bg-[#111218] rounded-2xl border border-slate-800 overflow-hidden mb-8">
                            <div className="aspect-video bg-gradient-to-br from-orange-900/20 to-purple-900/20 flex items-center justify-center relative">
                                <div className="absolute inset-0 bg-[url('/grid.svg')] opacity-20"></div>
                                <div className="text-center p-8">
                                    <h1 className="text-4xl md:text-5xl font-bold text-white mb-4">{MOCK_TEMPLATE.title}</h1>
                                    <p className="text-xl text-slate-400">Workflow Preview</p>
                                </div>
                            </div>
                        </div>

                        <div className="prose prose-invert max-w-none">
                            <h2 className="text-2xl font-bold text-white mb-4">Description</h2>
                            <div className="text-slate-300 leading-relaxed" dangerouslySetInnerHTML={{ __html: MOCK_TEMPLATE.longDescription }} />
                        </div>

                        <div className="mt-12">
                            <h2 className="text-2xl font-bold text-white mb-6">Features</h2>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                {MOCK_TEMPLATE.features.map((feature, idx) => (
                                    <div key={idx} className="flex items-center gap-3 bg-slate-900/50 p-4 rounded-xl border border-slate-800">
                                        <Check className="h-5 w-5 text-green-500" />
                                        <span className="text-slate-200">{feature}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>

                    {/* Sidebar */}
                    <div className="lg:col-span-1">
                        <div className="sticky top-24 space-y-6">
                            <div className="bg-[#111218] rounded-2xl border border-slate-800 p-6 shadow-xl shadow-black/20">
                                <div className="flex items-baseline justify-between mb-6">
                                    <span className="text-3xl font-bold text-white">${MOCK_TEMPLATE.price}</span>
                                    <span className="text-slate-400 text-sm">One-time purchase</span>
                                </div>

                                <button className="w-full bg-orange-600 hover:bg-orange-500 text-white font-bold py-4 rounded-xl transition-all shadow-lg shadow-orange-500/20 mb-4">
                                    Get this Workflow
                                </button>

                                <div className="flex items-center justify-center gap-2 text-sm text-slate-400 mb-6">
                                    <Shield className="h-4 w-4 text-green-500" />
                                    <span>Verified by n8n Market</span>
                                </div>

                                <div className="space-y-4 border-t border-slate-800 pt-6">
                                    <div className="flex justify-between text-sm">
                                        <span className="text-slate-400">Author</span>
                                        <span className="text-white font-medium">{MOCK_TEMPLATE.author}</span>
                                    </div>
                                    <div className="flex justify-between text-sm">
                                        <span className="text-slate-400">Downloads</span>
                                        <span className="text-white font-medium">{MOCK_TEMPLATE.downloads}</span>
                                    </div>
                                    <div className="flex justify-between text-sm">
                                        <span className="text-slate-400">Rating</span>
                                        <div className="flex items-center gap-1 text-white font-medium">
                                            <Star className="h-3 w-3 text-yellow-500 fill-yellow-500" />
                                            {MOCK_TEMPLATE.rating} ({MOCK_TEMPLATE.reviews})
                                        </div>
                                    </div>
                                    <div className="flex justify-between text-sm">
                                        <span className="text-slate-400">Last Updated</span>
                                        <span className="text-white font-medium">{MOCK_TEMPLATE.lastUpdated}</span>
                                    </div>
                                    <div className="flex justify-between text-sm">
                                        <span className="text-slate-400">Version</span>
                                        <span className="text-white font-medium">{MOCK_TEMPLATE.version}</span>
                                    </div>
                                </div>
                            </div>

                            <div className="bg-[#111218] rounded-2xl border border-slate-800 p-6">
                                <h3 className="font-bold text-white mb-4">Requirements</h3>
                                <ul className="space-y-3">
                                    {MOCK_TEMPLATE.requirements.map((req, idx) => (
                                        <li key={idx} className="flex items-start gap-3 text-sm text-slate-300">
                                            <div className="h-1.5 w-1.5 rounded-full bg-orange-500 mt-2"></div>
                                            {req}
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>
            </main>

            <Footer />
        </div>
    );
}
