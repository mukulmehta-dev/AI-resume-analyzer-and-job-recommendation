import { useEffect, useState, useCallback } from "react";
import { Link, useNavigate } from "react-router";
import { api } from "../lib/api";
import { useToast } from "../components/Toast";
import type { Analysis, AnalysisListResponse } from "../types";
import {
  Search,
  Trash2,
  ExternalLink,
  FileText,
  AlertTriangle,
  ChevronLeft,
  ChevronRight,
  Plus,
  Zap,
} from "lucide-react";

const PAGE_SIZE = 10;

function ScoreBadge({ score }: { score: number }) {
  const badgeClass =
    score >= 70
      ? "score-badge-green"
      : score >= 40
      ? "score-badge-yellow"
      : "score-badge-red";
  return (
    <span className={`score-badge ${badgeClass}`}>
      {score}
    </span>
  );
}

function StatusPill({ status }: { status: string }) {
  const map: Record<string, string> = {
    done: "score-badge-green",
    pending: "score-badge-yellow",
    failed: "score-badge-red",
  };
  return (
    <span
      className={`score-badge capitalize ${map[status] ?? "score-badge-yellow"}`}
    >
      {status}
    </span>
  );
}

export default function HistoryPage() {
  const navigate = useNavigate();
  const { addToast } = useToast();
  const [items, setItems] = useState<Analysis[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [hasJD, setHasJD] = useState<"all" | "yes" | "no">("all");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => {
      setDebouncedSearch(search);
      setPage(1);
    }, 350);
    return () => clearTimeout(t);
  }, [search]);

  const fetchHistory = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, string | number> = {
        page,
        page_size: PAGE_SIZE,
      };
      if (debouncedSearch) params.search = debouncedSearch;
      if (hasJD === "yes") params.has_job_description = "true";
      if (hasJD === "no") params.has_job_description = "false";

      const { data } = await api.get<AnalysisListResponse>("/analyses", { params });
      setItems(data.items);
      setTotal(data.total);
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? "Failed to load history.");
    } finally {
      setLoading(false);
    }
  }, [page, debouncedSearch, hasJD]);

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  const handleDeleteConfirm = async () => {
    if (!deletingId) return;
    setIsDeleting(true);
    try {
      await api.delete(`/analyses/${deletingId}`);
      addToast("Analysis record deleted successfully.", "success");
      setDeletingId(null);
      fetchHistory();
    } catch (e: any) {
      addToast(e?.response?.data?.detail ?? "Failed to delete analysis.", "error");
    } finally {
      setIsDeleting(false);
    }
  };

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">Analysis History</h1>
          <p className="text-dark-200 text-sm mt-1">
            Browse, search, and review all previous resume evaluations ({total} total)
          </p>
        </div>
        <Link
          to="/upload"
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-indigo-600 text-white font-medium hover:bg-indigo-700 transition-colors shadow-md shadow-indigo-100 text-sm"
        >
          <Plus className="w-4 h-4" /> New Analysis
        </Link>
      </div>

      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            id="history-search"
            type="text"
            placeholder="Search by resume filename..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-white border border-slate-200 rounded-xl pl-10 pr-4 py-2.5 text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:border-indigo-600 focus:ring-1 focus:ring-indigo-600 shadow-sm"
          />
        </div>

        <select
          id="history-jd-filter"
          value={hasJD}
          onChange={(e) => {
            setHasJD(e.target.value as "all" | "yes" | "no");
            setPage(1);
          }}
          className="bg-white border border-slate-200 rounded-xl px-4 py-2.5 text-sm text-slate-900 focus:outline-none focus:border-indigo-600 shadow-sm"
        >
          <option value="all">All Analyses</option>
          <option value="yes">With Job Description</option>
          <option value="no">Without Job Description</option>
        </select>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-sm flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0 text-rose-600" />
          <span>{error}</span>
        </div>
      )}

      {loading ? (
        <div className="flex flex-col items-center justify-center py-24 space-y-3">
          <div className="w-8 h-8 rounded-full border-2 border-indigo-600 border-t-transparent animate-spin" />
          <span className="text-xs text-dark-200">Loading analysis records...</span>
        </div>
      ) : items.length === 0 ? (
        <div className="p-12 text-center rounded-2xl bg-white gradient-border border border-slate-200 shadow-sm">
          <FileText className="w-12 h-12 text-slate-300 mx-auto mb-3" />
          <h2 className="text-lg font-bold text-slate-900 mb-1">No Analyses Found</h2>
          <p className="text-dark-200 text-sm mb-6 max-w-sm mx-auto">
            {search || hasJD !== "all"
              ? "No analysis records match your active search and filter criteria."
              : "Upload and analyze your first resume to view ATS diagnostic histories."}
          </p>
          <Link
            to="/upload"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-indigo-600 text-white font-medium hover:bg-indigo-700 transition-colors text-sm"
          >
            <Plus className="w-4 h-4" /> Analyze Resume
          </Link>
        </div>
      ) : (
        <div className="bg-white gradient-border rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50 text-[11px] font-bold uppercase tracking-wider text-dark-200">
                  <th className="py-3.5 px-4">Resume / Target</th>
                  <th className="py-3.5 px-4">Date</th>
                  <th className="py-3.5 px-4">Score</th>
                  <th className="py-3.5 px-4">Compatibility</th>
                  <th className="py-3.5 px-4">Job Desc</th>
                  <th className="py-3.5 px-4">Status</th>
                  <th className="py-3.5 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-sm">
                {items.map((analysis) => {
                  const dateStr = new Date(analysis.created_at).toLocaleDateString(undefined, {
                    month: "short",
                    day: "numeric",
                    year: "numeric",
                  });
                  const timeStr = new Date(analysis.created_at).toLocaleTimeString(undefined, {
                    hour: "2-digit",
                    minute: "2-digit",
                  });

                  return (
                    <tr
                      key={analysis.id}
                      className="hover:bg-slate-50/80 transition-colors cursor-pointer group"
                      onClick={() => navigate(`/analysis/${analysis.id}`)}
                    >
                      <td className="py-4 px-4 font-medium text-slate-900 max-w-xs truncate">
                        <div className="flex items-center gap-2">
                          <FileText className="w-4 h-4 text-indigo-600 shrink-0" />
                          <span className="truncate group-hover:text-indigo-600 transition-colors">
                            {analysis.resume_filename || "Resume Evaluation"}
                          </span>
                          {analysis.ai_unavailable && (
                            <span
                              title="Rule-based score only"
                              className="text-[10px] text-amber-800 bg-amber-50 px-1.5 py-0.5 rounded border border-amber-200 shrink-0 inline-flex items-center gap-0.5"
                            >
                              <Zap className="w-3 h-3 text-amber-600" /> Rule
                            </span>
                          )}
                        </div>
                      </td>

                      <td className="py-4 px-4 text-xs text-dark-200 whitespace-nowrap">
                        <div>{dateStr}</div>
                        <div className="text-slate-400 text-[11px]">{timeStr}</div>
                      </td>

                      <td className="py-4 px-4">
                        <ScoreBadge score={analysis.resume_score} />
                      </td>

                      <td className="py-4 px-4">
                        {analysis.compatibility_score !== null ? (
                          <span className="text-xs font-semibold text-emerald-700">
                            {analysis.compatibility_score}%
                          </span>
                        ) : (
                          <span className="text-xs text-slate-400">-</span>
                        )}
                      </td>

                      <td className="py-4 px-4">
                        <span
                          className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                            analysis.job_description
                              ? "bg-indigo-50 text-indigo-800 border border-indigo-200"
                              : "bg-slate-100 text-slate-700 border border-slate-200"
                          }`}
                        >
                          {analysis.job_description ? "Yes" : "No"}
                        </span>
                      </td>

                      <td className="py-4 px-4">
                        <StatusPill status={analysis.status} />
                      </td>

                      <td
                        className="py-4 px-4 text-right whitespace-nowrap"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <div className="inline-flex items-center gap-2">
                          <Link
                            to={`/analysis/${analysis.id}`}
                            className="p-1.5 rounded-lg text-dark-200 hover:text-indigo-600 hover:bg-slate-100 transition-colors"
                            title="Open Analysis"
                          >
                            <ExternalLink className="w-4 h-4" />
                          </Link>
                          <button
                            type="button"
                            onClick={() => setDeletingId(analysis.id)}
                            className="p-1.5 rounded-lg text-dark-200 hover:text-rose-600 hover:bg-rose-50 transition-colors"
                            title="Delete Analysis"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {totalPages > 1 && (
            <div className="flex items-center justify-between px-4 py-3 bg-slate-50 border-t border-slate-200">
              <span className="text-xs text-dark-200">
                Page {page} of {totalPages}
              </span>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-semibold bg-white border border-slate-200 text-slate-700 hover:bg-slate-100 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                >
                  <ChevronLeft className="w-3.5 h-3.5" /> Previous
                </button>
                <button
                  type="button"
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                  className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-semibold bg-white border border-slate-200 text-slate-700 hover:bg-slate-100 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                >
                  Next <ChevronRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {deletingId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm animate-in fade-in">
          <div className="w-full max-w-md bg-white border border-slate-200 rounded-2xl p-6 shadow-2xl space-y-4">
            <div className="flex items-center gap-3 text-rose-600">
              <div className="p-2.5 rounded-xl bg-rose-50">
                <AlertTriangle className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-slate-900">Delete Analysis?</h3>
            </div>
            <p className="text-dark-200 text-sm leading-relaxed">
              Are you sure you want to permanently delete this resume analysis report? This action cannot be undone.
            </p>
            <div className="flex justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => setDeletingId(null)}
                disabled={isDeleting}
                className="px-4 py-2 rounded-xl text-sm font-semibold bg-slate-100 text-slate-700 hover:bg-slate-200 transition-colors"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleDeleteConfirm}
                disabled={isDeleting}
                className="px-5 py-2 rounded-xl text-sm font-semibold bg-rose-600 text-white hover:bg-rose-700 transition-colors shadow-md shadow-rose-100 flex items-center gap-2 disabled:opacity-50"
              >
                <Trash2 className="w-4 h-4" />
                {isDeleting ? "Deleting..." : "Confirm Delete"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
