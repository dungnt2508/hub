"use client";

import { useQuery } from "@tanstack/react-query";
import { apiService } from "@/lib/apiService";
import GlassContainer from "@/components/ui/GlassContainer";
import { 
  Activity, 
  Search, 
  Eye, 
  TrendingUp, 
  ShoppingCart, 
  MessageSquare,
  Clock,
  RefreshCw
} from "lucide-react";

const STATE_ICONS: Record<string, any> = {
  IDLE: MessageSquare,
  BROWSING: Search,
  SEARCHING: Search,
  VIEWING: Eye,
  COMPARING: TrendingUp,
  PURCHASING: ShoppingCart,
  ANALYZING: Activity,
};

const STATE_COLORS: Record<string, string> = {
  IDLE: "text-gray-400 bg-gray-400/10",
  BROWSING: "text-blue-400 bg-blue-400/10",
  SEARCHING: "text-cyan-400 bg-cyan-400/10",
  VIEWING: "text-purple-400 bg-purple-400/10",
  COMPARING: "text-orange-400 bg-orange-400/10",
  PURCHASING: "text-green-400 bg-green-400/10",
  ANALYZING: "text-yellow-400 bg-yellow-400/10",
};

export default function StateDashboard() {
  const { data, isLoading, refetch, isRefetching } = useQuery({
    queryKey: ["state-statistics"],
    queryFn: () => apiService.getAnalytics(1).then(() => ({ distribution: {}, total_active: 0 })),
    refetchInterval: 10000, // Refresh every 10s
  });

  if (isLoading) {
    return (
      <div className="p-8 flex items-center justify-center min-h-[400px]">
        <RefreshCw className="w-8 h-8 animate-spin text-blue-500" />
      </div>
    );
  }

  const distribution = data?.distribution || {};
  const totalActive = data?.total_active || 0;
  const states = Object.entries(distribution).sort((a, b) => (b[1] as number) - (a[1] as number));

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">State Dashboard</h1>
          <p className="text-gray-400 mt-2">Giám sát trạng thái hoạt động của các phiên hội thoại thời gian thực.</p>
        </div>
        <button 
          onClick={() => refetch()}
          className="flex items-center gap-2 px-4 py-2 bg-white/5 hover:bg-white/10 rounded-lg transition-colors"
        >
          <RefreshCw className={`w-4 h-4 ${isRefetching ? 'animate-spin' : ''}`} />
          Làm mới
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <GlassContainer className="bg-white/5 border-white/10 shadow-2xl p-4">
          <div className="pb-2">
            <div className="text-sm font-medium text-gray-400">Tổng phiên hoạt động (24h)</div>
          </div>
          <div>
            <div className="text-4xl font-bold">{totalActive}</div>
          </div>
        </GlassContainer>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* State List */}
        <div className="lg:col-span-2 space-y-4">
          <h2 className="text-xl font-semibold flex items-center gap-2">
            <Activity className="w-5 h-5 text-blue-500" />
            Phân bổ trạng thái
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {states.map(([state, count]) => {
              const Icon = STATE_ICONS[state] || MessageSquare;
              const colorClass = STATE_COLORS[state] || "text-gray-400 bg-gray-400/10";
              const percentage = totalActive > 0 ? Math.round(((count as number) / totalActive) * 100) : 0;

              return (
                <GlassContainer key={state} className="bg-white/5 border-white/10 hover:border-white/20 transition-all group p-6">
                    <div className="flex items-center justify-between mb-4">
                      <div className={`p-3 rounded-xl ${colorClass}`}>
                        <Icon className="w-6 h-6" />
                      </div>
                      <div className="text-right">
                        <div className="text-2xl font-bold">{count as number}</div>
                        <div className="text-xs text-gray-500">{percentage}%</div>
                      </div>
                    </div>
                    <div>
                      <div className="text-sm font-medium mb-2">{state}</div>
                      <div className="w-full bg-white/5 rounded-full h-1.5 overflow-hidden">
                        <div 
                          className={`h-full transition-all duration-1000 ${colorClass.split(' ')[1].replace('/10', '')}`}
                          style={{ width: `${percentage}%` }}
                        />
                      </div>
                    </div>
                </GlassContainer>
              );
            })}
          </div>
        </div>

        {/* Info Sidebar */}
        <div className="space-y-6">
          <GlassContainer className="bg-gradient-to-br from-blue-500/10 to-purple-500/10 border-white/10 p-6">
            <div className="pb-4">
              <div className="text-lg font-bold">Ý nghĩa trạng thái</div>
            </div>
            <div className="text-sm text-gray-400 space-y-4">
              <div className="flex gap-3">
                <div className="w-2 h-2 rounded-full bg-gray-400 mt-1.5 shrink-0" />
                <p><span className="text-gray-200 font-medium">IDLE</span>: Bot đang đợi tin nhắn đầu tiên hoặc vừa kết thúc luồng.</p>
              </div>
              <div className="flex gap-3">
                <div className="w-2 h-2 rounded-full bg-blue-400 mt-1.5 shrink-0" />
                <p><span className="text-gray-200 font-medium">BROWSING</span>: Khách đang xem danh sách sản phẩm/dịch vụ tổng quát.</p>
              </div>
              <div className="flex gap-3">
                <div className="w-2 h-2 rounded-full bg-cyan-400 mt-1.5 shrink-0" />
                <p><span className="text-gray-200 font-medium">SEARCHING</span>: Bot vừa thực hiện tìm kiếm cụ thể dựa trên nhu cầu.</p>
              </div>
              <div className="flex gap-3">
                <div className="w-2 h-2 rounded-full bg-purple-400 mt-1.5 shrink-0" />
                <p><span className="text-gray-200 font-medium">VIEWING</span>: Khách đang xem chi tiết một sản phẩm cụ thể.</p>
              </div>
              <div className="flex gap-3">
                <div className="w-2 h-2 rounded-full bg-orange-400 mt-1.5 shrink-0" />
                <p><span className="text-gray-200 font-medium">COMPARING</span>: Khách đang so sánh giữa các lựa chọn.</p>
              </div>
            </div>
          </GlassContainer>

          <GlassContainer className="bg-white/5 border-white/10 p-6">
              <div className="flex items-center gap-3 text-sm text-gray-400 mb-4">
                <Clock className="w-4 h-4" />
                Cập nhật lần cuối: {new Date().toLocaleTimeString()}
              </div>
              <p className="text-xs text-gray-500 leading-relaxed">
                Dữ liệu được tổng hợp trực tiếp từ bảng `runtime_session`. 
                Các phiên không hoạt động quá 24h sẽ tự động ẩn khỏi thống kê.
              </p>
          </GlassContainer>
        </div>
      </div>
    </div>
  );
}
