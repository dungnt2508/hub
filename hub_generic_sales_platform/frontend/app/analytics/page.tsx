"use client";

import GlassContainer from "@/components/ui/GlassContainer";
import { BarChart3, TrendingUp, Cpu, Users, Calendar, Download, ArrowUpRight, Loader2 } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { apiService } from "@/lib/apiService";

export default function AnalyticsPage() {
    const { data: analytics, isLoading } = useQuery({
        queryKey: ["analytics-dashboard"],
        queryFn: () => apiService.getAnalytics(),
    });

    if (isLoading) {
        return (
            <div className="h-full flex items-center justify-center">
                <Loader2 className="w-8 h-8 animate-spin text-accent" />
            </div>
        );
    }

    const { summary, usage_mix, volume_history, efficiency_trend } = analytics || {
        summary: { total_savings: "...", automation_rate: 0, avg_latency: "...", projected_growth: "..." },
        usage_mix: [],
        volume_history: [],
        efficiency_trend: []
    };

    return (
        <div className="h-full flex flex-col space-y-6 overflow-y-auto no-scrollbar pr-2">
            <div className="flex items-center justify-between">
                <div className="flex flex-col">
                    <h1 className="text-2xl font-black text-white italic">Commercial Intelligence</h1>
                    <p className="text-xs text-secondary font-bold uppercase tracking-[0.3em] mt-1 pr-2">Deep Performance & ROI Insights</p>
                </div>
                <div className="flex gap-3">
                    <div className="bg-white/5 border border-white/10 rounded-xl px-4 py-2 flex items-center gap-2 text-xs font-bold text-gray-400">
                        <Calendar className="w-4 h-4" /> Mar 1 - Mar 31, 2026
                    </div>
                    <button className="flex items-center gap-2 px-6 py-2 glass-effect rounded-xl text-xs font-bold text-white hover:bg-white/10 transition-all">
                        <Download className="w-4 h-4" /> Export JSON
                    </button>
                </div>
            </div>

            <div className="grid grid-cols-12 gap-6">
                {/* Main Chart Placeholder */}
                <GlassContainer className="col-span-8 p-8 min-h-[450px] flex flex-col bg-white/5 border-white/5">
                    <div className="flex justify-between items-start mb-12">
                        <div>
                            <h3 className="text-lg font-black text-white">Token Injection & Efficiency</h3>
                            <p className="text-xs text-gray-500 font-medium">Measuring processing cost vs human hand-off savings.</p>
                        </div>
                        <div className="flex items-center gap-6">
                            <div className="flex items-center gap-2">
                                <div className="w-3 h-3 rounded bg-accent"></div>
                                <span className="text-[10px] font-black uppercase text-gray-400">IRIS (AI)</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <div className="w-3 h-3 rounded bg-gray-700"></div>
                                <span className="text-[10px] font-black uppercase text-gray-400">Baseline</span>
                            </div>
                        </div>
                    </div>

                    <div className="flex-1 flex items-end gap-3 px-4 relative">
                        {/* Grid lines */}
                        {[0, 25, 50, 75, 100].map(v => (
                            <div key={v} className="absolute left-0 right-0 border-t border-white/[0.03] h-0" style={{ bottom: `${v}%` }}></div>
                        ))}

                        {efficiency_trend.map((v, i) => (
                            <div key={i} className="flex-1 flex flex-col items-center gap-2 group cursor-pointer">
                                <div
                                    className="w-full bg-gradient-to-t from-accent/20 to-accent rounded-t-lg transition-all duration-700 group-hover:brightness-125"
                                    style={{ height: `${v}%` }}
                                ></div>
                                <span className="text-[8px] font-bold text-gray-600 transition-colors group-hover:text-gray-400">W{i + 1}</span>
                            </div>
                        ))}
                    </div>
                </GlassContainer>

                {/* ROI Sidebar */}
                <div className="col-span-4 flex flex-col gap-6">
                    <GlassContainer className="p-6 flex-1 border-accent/20 bg-accent/5">
                        <h3 className="text-[10px] font-black uppercase text-accent tracking-widest mb-6">Commercial Value ROI</h3>
                        <div className="space-y-6">
                            <div>
                                <div className="text-3xl font-black text-white">{summary.total_savings}</div>
                                <div className="text-[10px] text-gray-500 font-bold uppercase mt-1">Total Savings via T1 & T2</div>
                            </div>
                            <div className="h-[2px] w-full bg-white/5"></div>
                            <div>
                                <div className="text-xl font-bold text-gray-300">{summary.automation_rate}%</div>
                                <div className="text-[10px] text-gray-500 font-bold uppercase mt-1">Automation Rate</div>
                            </div>
                            <div>
                                <div className="text-xl font-bold text-gray-300">{summary.avg_latency}</div>
                                <div className="text-[10px] text-gray-500 font-bold uppercase mt-1">P95 Response Latency</div>
                            </div>
                        </div>
                    </GlassContainer>

                    <button className="w-full py-4 glass-effect rounded-2xl font-black text-xs uppercase tracking-widest hover:bg-white/10 transition-all border border-white/5 active:scale-95">
                        Build Custom Report <ArrowUpRight className="w-4 h-4 ml-2 inline" />
                    </button>
                </div>
            </div>

            <div className="grid grid-cols-3 gap-6">
                <GlassContainer className="p-6 bg-white/5 border-white/5">
                    <div className="flex items-center gap-3 mb-4">
                        <Cpu className="text-orange-500 w-5 h-5" />
                        <h4 className="text-xs font-black text-gray-200">Model Usage Mix</h4>
                    </div>
                    <div className="space-y-3">
                        {usage_mix.map((item, idx) => (
                            <div key={idx}>
                                <div className="flex justify-between text-[10px] font-bold">
                                    <span className="text-gray-400">{item.model}</span>
                                    <span className="text-white">{item.percentage}%</span>
                                </div>
                                <div className="h-1 bg-white/5 rounded-full mt-1">
                                    <div className={`h-full bg-${item.color} rounded-full`} style={{ width: `${item.percentage}%` }}></div>
                                </div>
                            </div>
                        ))}
                    </div>
                </GlassContainer>

                <GlassContainer className="p-6 bg-white/5 border-white/5">
                    <div className="flex items-center gap-3 mb-4">
                        <Users className="text-cyan-500 w-5 h-5" />
                        <h4 className="text-xs font-black text-gray-200">Session Volume</h4>
                    </div>
                    <div className="flex items-end gap-1 h-12">
                        {volume_history.map((v, i) => (
                            <div key={i} className="flex-1 bg-cyan-500/20 rounded-sm" style={{ height: `${v}%` }}></div>
                        ))}
                    </div>
                </GlassContainer>

                <GlassContainer className="p-6 border-white/5 bg-accent/10">
                    <div className="h-full flex flex-col justify-center text-center">
                        <TrendingUp className="w-8 h-8 text-accent mx-auto mb-3" />
                        <div className="text-sm font-black text-white">Projected Growth</div>
                        <p className="text-[10px] text-gray-500 mt-1 uppercase tracking-tighter">{summary.projected_growth}</p>
                    </div>
                </GlassContainer>
            </div>
        </div>
    );
}
