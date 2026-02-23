"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiService, MigrationJob } from "@/lib/apiService";
import { useState, useEffect, useMemo } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { Upload, Search, ArrowUpDown } from "lucide-react";
import { cn } from "@/lib/utils";

import GlassContainer from "@/components/ui/GlassContainer";
import MigrationInputForm from "@/components/migration/MigrationInputForm";
import MigrationJobList from "@/components/migration/MigrationJobList";
import MigrationPreviewModal from "@/components/migration/MigrationPreviewModal";

const POLL_INTERVAL_MS = 2000;
type StatusFilter = "all" | "pending" | "processing" | "staged" | "completed" | "failed";
type SortOrder = "newest" | "oldest";

export default function MigrationPage() {
    const queryClient = useQueryClient();
    const router = useRouter();

    const [url, setUrl] = useState("");
    const [selectedBotId, setSelectedBotId] = useState<string | null>(null);
    const [previewJob, setPreviewJob] = useState<MigrationJob | null>(null);
    const [searchTerm, setSearchTerm] = useState("");
    const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
    const [sortOrder, setSortOrder] = useState<SortOrder>("newest");

    // Queries
    const { data: bots = [], isLoading: isBotsLoading } = useQuery({
        queryKey: ["bots", "active"],
        queryFn: () => apiService.listBots({ status: "active" }),
    });

    const { data: jobs = [], isLoading: isJobsLoading } = useQuery({
        queryKey: ["migration-jobs"],
        queryFn: () => apiService.listMigrationJobs(),
        refetchInterval: (query) => {
            const data = query.state.data as MigrationJob[] | undefined;
            const hasProcessing = data?.some(
                (j) => j.status === "processing" || j.status === "pending"
            );
            return hasProcessing ? POLL_INTERVAL_MS : false;
        },
    });

    // Mutations
    const startScrapeMutation = useMutation({
        mutationFn: (data: { url: string; bot_id?: string }) =>
            apiService.startScrape({ url: data.url, bot_id: data.bot_id }),
        onSuccess: (res) => {
            queryClient.invalidateQueries({ queryKey: ["migration-jobs"] });
            toast.success(`Bắt đầu cào: ${res.job_id?.slice(0, 8)}...`);
        },
        onError: (err: any) =>
            toast.error(err.response?.data?.detail || "Lỗi khi bắt đầu cào"),
    });

    const confirmMigrationMutation = useMutation({
        mutationFn: ({ jobId }: { jobId: string; botId?: string | null }) =>
            apiService.confirmMigration(jobId),
        onSuccess: (_data, variables) => {
            queryClient.invalidateQueries({ queryKey: ["migration-jobs"] });
            queryClient.invalidateQueries({ queryKey: ["catalog-offerings"] });
            setPreviewJob(null);
            toast.success("Đã lưu vào Catalog!");
            // Navigate đến Catalog với đúng Bot đã dùng khi migrate (nhất quán domain)
            const botId = variables.botId;
            if (botId) {
                router.push(`/catalog?bot_id=${encodeURIComponent(botId)}`);
            }
        },
        onError: (err: any) =>
            toast.error(err.response?.data?.detail || "Lỗi khi commit"),
    });

    useEffect(() => {
        if (!selectedBotId && bots.length > 0) {
            setSelectedBotId(bots[0].id);
        }
    }, [bots, selectedBotId]);

    const handleStartScrape = () => {
        if (!selectedBotId || !url.trim()) return;
        startScrapeMutation.mutate({ url: url.trim(), bot_id: selectedBotId });
    };

    const handleConfirm = (job: MigrationJob) => {
        confirmMigrationMutation.mutate({ jobId: job.id, botId: job.bot_id });
    };

    const stats = {
        total: jobs.length,
        staged: jobs.filter((j: MigrationJob) => j.status === "staged").length,
        completed: jobs.filter((j: MigrationJob) => j.status === "completed").length,
        failed: jobs.filter((j: MigrationJob) => j.status === "failed").length,
    };

    const filteredAndSortedJobs = useMemo(() => {
        let result = [...jobs];
        if (searchTerm.trim()) {
            const term = searchTerm.toLowerCase().trim();
            result = result.filter(
                (j) =>
                    (j.metadata?.url || "").toLowerCase().includes(term) ||
                    (j.metadata?.filename || "").toLowerCase().includes(term) ||
                    (j.id || "").toLowerCase().includes(term)
            );
        }
        if (statusFilter !== "all") {
            result = result.filter((j) => j.status === statusFilter);
        }
        result.sort((a, b) => {
            const da = new Date(a.created_at).getTime();
            const db = new Date(b.created_at).getTime();
            return sortOrder === "newest" ? db - da : da - db;
        });
        return result;
    }, [jobs, searchTerm, statusFilter, sortOrder]);

    return (
        <div className="h-full flex flex-col space-y-6 overflow-y-auto no-scrollbar pb-10">
            <div className="flex items-center justify-between">
                <div className="flex flex-col">
                    <h1 className="text-2xl font-black text-white">Migration Center</h1>
                    <p className="text-xs text-gray-500 font-bold uppercase tracking-[0.2em] mt-1">
                        Import dữ liệu từ Web, Excel
                    </p>
                </div>
            </div>

            {/* Input Form - đặt trước Stats để user thấy ngay chỗ nhập URL */}
            <MigrationInputForm
                url={url}
                onUrlChange={setUrl}
                bots={bots}
                selectedBotId={selectedBotId}
                onSelectBot={setSelectedBotId}
                onStartScrape={handleStartScrape}
                isBotsLoading={isBotsLoading}
                isScraping={startScrapeMutation.isPending}
                hasSelectedBot={!!selectedBotId}
            />

            {/* Stats */}
            <div className="grid grid-cols-4 gap-4">
                <div className="p-4 bg-white/5 rounded-3xl border border-white/5 flex items-center gap-4">
                    <div className="w-12 h-12 rounded-2xl bg-accent/20 flex items-center justify-center text-accent">
                        <Upload className="w-6 h-6" />
                    </div>
                    <div>
                        <div className="text-2xl font-black text-white">{stats.total}</div>
                        <div className="text-[10px] font-bold text-gray-500 uppercase tracking-widest">Tổng Jobs</div>
                    </div>
                </div>
                <div className="p-4 bg-white/5 rounded-3xl border border-white/5 flex items-center gap-4">
                    <div className="w-12 h-12 rounded-2xl bg-green-500/20 flex items-center justify-center text-green-500">
                        <Upload className="w-6 h-6" />
                    </div>
                    <div>
                        <div className="text-2xl font-black text-white">{stats.staged}</div>
                        <div className="text-[10px] font-bold text-gray-500 uppercase tracking-widest">Staged</div>
                    </div>
                </div>
                <div className="p-4 bg-white/5 rounded-3xl border border-white/5 flex items-center gap-4">
                    <div className="w-12 h-12 rounded-2xl bg-gray-500/20 flex items-center justify-center text-gray-500">
                        <Upload className="w-6 h-6" />
                    </div>
                    <div>
                        <div className="text-2xl font-black text-white">{stats.completed}</div>
                        <div className="text-[10px] font-bold text-gray-500 uppercase tracking-widest">Completed</div>
                    </div>
                </div>
                <div className="p-4 bg-white/5 rounded-3xl border border-white/5 flex items-center gap-4">
                    <div className="w-12 h-12 rounded-2xl bg-red-500/20 flex items-center justify-center text-red-500">
                        <Upload className="w-6 h-6" />
                    </div>
                    <div>
                        <div className="text-2xl font-black text-white">{stats.failed}</div>
                        <div className="text-[10px] font-bold text-gray-500 uppercase tracking-widest">Failed</div>
                    </div>
                </div>
            </div>

            {/* Job List */}
            <GlassContainer className="flex-1 p-6 bg-white/5 border-white/10 min-h-[300px]">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
                    <h3 className="text-[10px] font-black text-white uppercase tracking-widest">Lịch sử Jobs</h3>
                    <div className="flex flex-wrap items-center gap-3">
                        <div className="relative">
                            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                            <input
                                type="text"
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                placeholder="Tìm theo URL, ID..."
                                className="bg-white/5 border border-white/10 rounded-xl py-2 pl-9 pr-3 text-xs focus:outline-none focus:border-accent/40 w-48 text-gray-300"
                            />
                        </div>
                        <div className="flex bg-white/5 p-1 rounded-xl">
                            {(["all", "pending", "processing", "staged", "completed", "failed"] as StatusFilter[]).map((s) => (
                                <button
                                    key={s}
                                    onClick={() => setStatusFilter(s)}
                                    className={cn(
                                        "px-3 py-1.5 rounded-lg text-[10px] font-bold transition-all",
                                        statusFilter === s ? "bg-accent/20 text-accent" : "text-gray-500 hover:text-gray-300"
                                    )}
                                >
                                    {s === "all" ? "Tất cả" : s}
                                </button>
                            ))}
                        </div>
                        <button
                            onClick={() => setSortOrder((o) => (o === "newest" ? "oldest" : "newest"))}
                            className={cn(
                                "flex items-center gap-1.5 px-3 py-2 rounded-xl text-[10px] font-bold transition-all",
                                "bg-white/5 border border-white/10 hover:bg-white/10"
                            )}
                            title={sortOrder === "newest" ? "Mới nhất trước (click đổi)" : "Cũ nhất trước (click đổi)"}
                        >
                            <ArrowUpDown className="w-3.5 h-3.5" />
                            {sortOrder === "newest" ? "Mới nhất" : "Cũ nhất"}
                        </button>
                    </div>
                </div>
                <MigrationJobList
                    jobs={filteredAndSortedJobs}
                    isLoading={isJobsLoading}
                    onViewPreview={setPreviewJob}
                    onConfirm={handleConfirm}
                />
            </GlassContainer>

            {/* Preview Modal */}
            <MigrationPreviewModal
                job={previewJob}
                onClose={() => setPreviewJob(null)}
                onConfirm={handleConfirm}
                isConfirming={confirmMigrationMutation.isPending}
            />
        </div>
    );
}
