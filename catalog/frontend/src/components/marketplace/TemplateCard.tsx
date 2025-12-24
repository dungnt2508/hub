import Link from 'next/link';
import { Star, Download, User, ArrowUpRight } from 'lucide-react';

interface TemplateCardProps {
    id: number | string;
    title: string;
    description: string;
    price: number | string;
    author: string;
    downloads: number;
    rating: number;
    tags: string[];
    color?: string;
}

export default function TemplateCard({ id, title, description, price, author, downloads, rating, tags, color = 'from-blue-600 to-purple-600' }: TemplateCardProps) {
    return (
        <Link href={`/product/${id}`} className="group relative flex flex-col overflow-hidden rounded-2xl border border-gray-200 dark:border-slate-800 bg-white dark:bg-[#111218] hover:border-gray-300 dark:hover:border-slate-700 transition-all hover:shadow-2xl hover:shadow-primary/5 hover:-translate-y-1">
                <div className="aspect-[16/9] w-full bg-gray-100 dark:bg-slate-900 relative overflow-hidden">
                {/* Gradient Background as placeholder */}
                <div className={`absolute inset-0 bg-gradient-to-br ${color} opacity-80 group-hover:opacity-100 transition-opacity duration-500`}></div>

                {/* Pattern overlay */}
                <div className="absolute inset-0 bg-[url('/grid.svg')] opacity-30 bg-center"></div>

                <div className="absolute inset-0 flex items-center justify-center">
                    <div className="bg-white/10 backdrop-blur-md p-4 rounded-xl border border-white/20 shadow-xl group-hover:scale-110 transition-transform duration-500">
                        <div className="w-12 h-12 rounded-lg bg-white/20 flex items-center justify-center">
                            <ArrowUpRight className="text-white h-6 w-6" />
                        </div>
                    </div>
                </div>

                <div className="absolute top-3 right-3 rounded-full bg-black/60 px-3 py-1 text-xs font-bold text-white backdrop-blur-md border border-white/10">
                    {typeof price === 'number' ? `$${price}` : price}
                </div>
            </div>

            <div className="flex flex-1 flex-col p-5">
                <div className="flex gap-2 mb-3 flex-wrap">
                    {tags.slice(0, 2).map(tag => (
                        <span key={tag} className="text-[10px] uppercase tracking-wider font-bold text-gray-600 dark:text-slate-400 bg-gray-100 dark:bg-slate-800/50 px-2 py-1 rounded-md border border-gray-200 dark:border-slate-800">
                            {tag}
                        </span>
                    ))}
                </div>

                <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2 line-clamp-1 group-hover:text-primary transition-colors">
                    {title}
                </h3>

                <p className="text-sm text-gray-600 dark:text-slate-400 mb-5 line-clamp-2 flex-1 leading-relaxed">
                    {description}
                </p>

                <div className="mt-auto flex items-center justify-between border-t border-gray-200 dark:border-slate-800/50 pt-4">
                    <div className="flex items-center gap-2">
                        <div className="h-6 w-6 rounded-full bg-gradient-to-r from-gray-300 to-gray-400 dark:from-slate-700 dark:to-slate-600 flex items-center justify-center ring-2 ring-white dark:ring-[#111218]">
                            <User className="h-3 w-3 text-gray-700 dark:text-slate-300" />
                        </div>
                        <span className="text-xs font-medium text-gray-700 dark:text-slate-300 hover:text-gray-900 dark:hover:text-white cursor-pointer transition-colors">{author}</span>
                    </div>

                    <div className="flex items-center gap-3 text-xs text-gray-500 dark:text-slate-500">
                        <div className="flex items-center gap-1">
                            <Download className="h-3 w-3" />
                            {downloads}
                        </div>
                        <div className="flex items-center gap-1">
                            <Star className="h-3 w-3 text-yellow-500 fill-yellow-500" />
                            {rating}
                        </div>
                    </div>
                </div>
            </div>
        </Link>
    );
}
