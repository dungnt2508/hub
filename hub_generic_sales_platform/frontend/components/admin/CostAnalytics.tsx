"use client";

import { cn } from "@/lib/utils";
import { TrendingUp, DollarSign, Cpu, Loader2 } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { apiService } from "@/lib/apiService";

interface StatItemProps {
    label: string;
    value: string;
    icon: any;
    subValue?: string;
    trend?: "up" | "down";
}

function StatCard({ label, value, icon: Icon, subValue, trend }: StatItemProps) {
    return (
        <div className="p-4 bg-white/5 rounded-2xl border border-white/5 hover:border-white/10 transition-all group">
            <div className="flex items-center justify-between mb-2">
                <div className="p-2 bg-white/5 rounded-lg text-gray-400 group-hover:text-accent transition-colors">
                    <Icon className="w-4 h-4" />
                </div>
                {trend && (
                    <span className={cn(
                        "text-[10px] font-bold px-1.5 py-0.5 rounded-full",
                        trend === "down" ? "bg-green-500/10 text-green-500" : "bg-red-500/10 text-red-500"
                    )}>
                        {trend === "down" ? "-12%" : "+5%"}
                    </span>
                )}
            </div>
            <div className="text-xl font-black text-gray-100">{value}</div>
            <div className="text-[10px] font-semibold text-gray-500 uppercase tracking-widest mt-1">{label}</div>
            {subValue && <div className="text-[10px] text-gray-400 mt-2">{subValue}</div>}
        </div>
    );
}

interface CostAnalyticsProps {
    sessionId?: string; // Optional: if provided, fetch stats for specific session
    useDashboardAnalytics?: boolean; // When true and no sessionId, fetch analytics dashboard
}

export default function CostAnalytics({ sessionId, useDashboardAnalytics }: CostAnalyticsProps = {}) {
    const { data: sessionStats, isLoading } = useQuery({
        queryKey: ["sessionStats", sessionId],
        queryFn: () => sessionId ? apiService.getSessionStats(sessionId) : null,
        enabled: !!sessionId,
    });

    const { data: dashboardAnalytics } = useQuery({
        queryKey: ["analytics-dashboard"],
        queryFn: () => apiService.getAnalytics(30),
        enabled: !!useDashboardAnalytics && !sessionId,
    });

    const estimatedCost = sessionStats?.summary?.total_cost
        || dashboardAnalytics?.summary?.total_savings
        || "$0.42";
    const tokenUsage = sessionStats?.summary?.total_turns 
        ? `${Math.round((sessionStats.summary.total_turns || 0) * 1.2)}k` 
        : "1.2k";
    
    const tierCounts = sessionStats?.timeline?.reduce((acc: any, item: any) => {
        acc[item.tier] = (acc[item.tier] || 0) + 1;
        return acc;
    }, {});
    
    const totalTurns: number = tierCounts ? (Object.values(tierCounts) as number[]).reduce((a, b) => a + b, 0) : 0;
    const fastPathPercent = totalTurns > 0 ? Math.round((tierCounts.fast_path || 0) / totalTurns * 100) : 85;
    const knowledgePathPercent = totalTurns > 0 ? Math.round((tierCounts.knowledge_path || 0) / totalTurns * 100) : 65;
    const agenticPathPercent = totalTurns > 0 ? Math.round((tierCounts.agentic_path || 0) / totalTurns * 100) : 15;
    if (isLoading && sessionId) {
        return (
            <div className="space-y-4 flex items-center justify-center py-8">
                <Loader2 className="w-6 h-6 text-accent animate-spin" />
            </div>
        );
    }

    return (
        <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
                <StatCard
                    label="Estimated Cost"
                    value={estimatedCost}
                    icon={DollarSign}
                    subValue={sessionStats ? `Total: ${sessionStats.summary?.total_turns || 0} turns` : "Avg. $0.005 / session"}
                    trend="down"
                />
                <StatCard
                    label="Token Usage"
                    value={tokenUsage}
                    icon={Cpu}
                    subValue={sessionStats ? `Avg latency: ${sessionStats.summary?.avg_latency_ms || 0}ms` : "Tier 3 active: 15%"}
                />
            </div>

            <div className="p-4 bg-accent/5 rounded-2xl border border-accent/10">
                <div className="flex items-center justify-between mb-4">
                    <h5 className="text-xs font-bold text-accent uppercase tracking-widest flex items-center gap-2">
                        <TrendingUp className="w-3 h-3" /> Tier Efficiency
                    </h5>
                    <span className="text-[10px] text-accent/60 font-medium">
                        {sessionStats ? `Total: ${totalTurns} turns` : "Monthly ROI: +82%"}
                    </span>
                </div>

                <div className="space-y-3">
                    {[
                        { label: "Fast Path", value: fastPathPercent, color: "bg-green-500" },
                        { label: "Knowledge", value: knowledgePathPercent, color: "bg-accent" },
                        { label: "Agentic", value: agenticPathPercent, color: "bg-orange-500" },
                    ].map((tier, idx) => (
                        <div key={idx} className="space-y-1">
                            <div className="flex justify-between text-[10px] font-bold text-gray-400 uppercase">
                                <span>{tier.label}</span>
                                <span>{tier.value}%</span>
                            </div>
                            <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                                <div
                                    className={cn("h-full transition-all duration-1000", tier.color)}
                                    style={{ width: `${tier.value}%` }}
                                ></div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
