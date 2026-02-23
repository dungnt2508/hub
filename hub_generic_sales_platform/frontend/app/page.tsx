"use client";

import GlassContainer from "@/components/ui/GlassContainer";
import { TrendingUp, Users, Zap, DollarSign, Activity, ArrowUpRight, BarChart as BarChartIcon, Settings } from "lucide-react";
import CostAnalytics from "@/components/admin/CostAnalytics";
import { cn } from "@/lib/utils";
import { useQuery } from "@tanstack/react-query";
import { apiService } from "@/lib/apiService";

export default function Dashboard() {
  const { data: bots } = useQuery({ queryKey: ["bots"], queryFn: () => apiService.listBots() });
  const { data: tenants } = useQuery({ queryKey: ["tenants"], queryFn: () => apiService.listTenants() });
  const { data: analytics } = useQuery({ queryKey: ["analytics-dashboard"], queryFn: () => apiService.getAnalytics(30) });

  const activeBots = bots?.filter(b => b.status === 'active').length || 0;
  const avgLatency = analytics?.summary?.avg_latency || "~0.10s";
  const automationRate = analytics?.summary?.automation_rate ?? 0;
  const totalSavings = analytics?.summary?.total_savings || "$0.00";
  const projectedGrowth = analytics?.summary?.projected_growth || "—";
  const activeSessions = analytics?.summary?.active_sessions ?? 0;
  const tierDist = analytics?.tier_distribution ?? [];

  // Derive trends from analytics (P3: bỏ hardcode)
  const eff = analytics?.efficiency_trend ?? [];
  const vol = analytics?.volume_history ?? [];
  const latencyTrend = eff.length >= 2
    ? (eff[eff.length - 2] - eff[eff.length - 1]) / (eff[eff.length - 2] || 1) * 100
    : undefined;
  const volumeTrend = vol.length >= 2
    ? (vol[vol.length - 1] - vol[vol.length - 2]) / (vol[vol.length - 2] || 1) * 100
    : undefined;

  return (
    <div className="h-full flex flex-col space-y-6 overflow-y-auto pr-2 custom-scrollbar no-scrollbar">
      {/* Welcome Header */}
      <div className="flex flex-col">
        <h1 className="text-3xl font-black tracking-tighter text-white">Commercial Dashboard</h1>
        <p className="text-gray-500 font-medium">Monitoring IRIS Hub v4 Performance & Cost ROI</p>
      </div>

      {/* Bento Grid Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        <StatCard
          label="Active Bots"
          value={String(activeBots)}
          trend={volumeTrend != null ? `${volumeTrend >= 0 ? "+" : ""}${volumeTrend.toFixed(0)}%` : undefined}
          icon={Activity}
          color="text-green-500"
        />
        <StatCard
          label="Active Sessions (24h)"
          value={String(activeSessions)}
          icon={Users}
          color="text-blue-500"
        />
        <StatCard
          label="Total Tenants"
          value={String(tenants?.length || 0)}
          icon={Zap}
          color="text-accent"
        />
        <StatCard
          label="Avg. Latency"
          value={typeof avgLatency === "string" ? avgLatency : `${avgLatency}ms`}
          trend={latencyTrend != null ? `${latencyTrend >= 0 ? "+" : "-"}${Math.abs(latencyTrend).toFixed(0)}%` : undefined}
          icon={BarChartIcon}
          color="text-cyan-500"
        />
        <StatCard
          label="Automation Rate"
          value={`${automationRate}%`}
          icon={Settings}
          color="text-purple-500"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Main Cost Analysis */}
        <GlassContainer className="lg:col-span-8 p-8 flex flex-col min-h-[400px]">
          <div className="flex items-center justify-between mb-8">
            <h3 className="font-bold text-lg text-white flex items-center gap-3">
              <TrendingUp className="text-accent w-5 h-5" /> Efficiency & Cost Matrix (Monthly)
            </h3>
            <button className="text-xs font-bold text-accent hover:underline flex items-center gap-1">
              Full Report <ArrowUpRight className="w-3 h-3" />
            </button>
          </div>
          <CostAnalytics useDashboardAnalytics />
        </GlassContainer>

        {/* Secondary Stats */}
        <div className="lg:col-span-4 flex flex-col gap-6">
          <GlassContainer className="p-6 flex-1 bg-accent/5 border-accent/20">
            <h4 className="text-[10px] font-black uppercase text-accent tracking-widest mb-4">Tier Mix (thực)</h4>
            <div className="space-y-3">
              {tierDist.length > 0 ? (
                tierDist.map((t: { tier: string; count: number; percent: number }) => (
                  <div key={t.tier} className="flex items-center justify-between gap-2">
                    <span className="text-[10px] font-bold text-gray-400 capitalize">{t.tier.replace("_", " ")}</span>
                    <div className="flex-1 h-2 bg-white/5 rounded-full overflow-hidden">
                      <div
                        className={cn(
                          "h-full rounded-full transition-all",
                          t.tier === "fast_path" && "bg-green-500",
                          t.tier === "knowledge_path" && "bg-cyan-500",
                          t.tier === "agentic_path" && "bg-orange-500",
                          !["fast_path", "knowledge_path", "agentic_path"].includes(t.tier) && "bg-gray-500"
                        )}
                        style={{ width: `${t.percent}%` }}
                      />
                    </div>
                    <span className="text-[10px] font-black text-white w-12 text-right">{t.percent}%</span>
                  </div>
                ))
              ) : (
                <div className="text-center py-8 text-gray-500 text-[10px]">Chưa có data tier</div>
              )}
            </div>
          </GlassContainer>

          <GlassContainer className="p-6 bg-white/5 flex flex-col justify-center">
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-xl bg-orange-500/10 text-orange-500">
                <DollarSign className="w-6 h-6" />
              </div>
              <div>
                <div className="text-sm font-bold text-gray-200">Total Savings (30d)</div>
                <div className="text-lg font-black text-white">{totalSavings}</div>
                <div className="text-[9px] text-gray-500 mt-1">{projectedGrowth}</div>
              </div>
            </div>
          </GlassContainer>
        </div>
      </div>
    </div>
  );
}

function StatCard({ label, value, trend, icon: Icon, color }: any) {
  return (
    <GlassContainer className="p-6 bg-white/5 border-white/5 group hover:border-white/10 transition-all">
      <div className="flex justify-between items-start mb-4">
        <div className={cn("p-2 rounded-xl bg-white/5", color)}>
          <Icon className="w-5 h-5" />
        </div>
        {trend && (
          <span className={cn(
            "text-[10px] font-bold px-2 py-0.5 rounded-full inline-flex items-center gap-1",
            trend.startsWith('+') ? "bg-green-500/10 text-green-500" : "bg-red-500/10 text-red-500"
          )}>
            {trend}
          </span>
        )}
      </div>
      <div className="text-2xl font-black text-white group-hover:scale-105 transition-transform origin-left">{value}</div>
      <div className="text-[10px] font-bold text-gray-500 uppercase tracking-widest mt-1">{label}</div>
    </GlassContainer>
  );
}

function BarChart({ className }: { className?: string }) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <path d="M3 3v18h18" /><path d="M18 17V9" /><path d="M13 17V5" /><path d="M8 17v-3" />
    </svg>
  );
}
