import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router";
import { useAuthStore } from "../store/auth";
import { api } from "../lib/api";
import type { Analysis, AnalysisListResponse, Resume } from "../types";
import {
  FileUp,
  Sparkles,
  ArrowRight,
  Clock,
  Award,
  Target,
  FileText,
  FolderGit2,
  History,
} from "lucide-react";

interface ResumeItem extends Resume {
  latest_score?: number | null;
  analyses_count?: number;
}

export default function HomePage() {
  const { user, initialized, loading: authLoading } = useAuthStore();
  const navigate = useNavigate();
  const [analyses, setAnalyses] = useState<Analysis[]>([]);
  const [resumes, setResumes] = useState<ResumeItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (initialized && !user) {
      navigate("/auth");
      return;
    }

    if (user) {
      Promise.all([
        api.get<AnalysisListResponse>("/analyses", { params: { page: 1, page_size: 5 } }).catch(() => ({ data: { items: [], total: 0, page: 1, page_size: 5 } })),
        api.get<ResumeItem[]>("/resumes").catch(() => ({ data: [] })),
      ])
        .then(([analysesRes, resumesRes]) => {
          setAnalyses(analysesRes.data?.items || []);
          setResumes(resumesRes.data || []);
        })
        .finally(() => setLoading(false));
    }
  }, [user, initialized, navigate]);

  if (authLoading || (!initialized && !user)) {
    return (
      <div className="min-h-[50vh] flex items-center justify-center">
        <div className="w-8 h-8 rounded-full border-4 border-indigo-200 border-t-indigo-600 animate-spin" />
      </div>
    );
  }

  const latestAnalysis = analyses.length > 0 ? analyses[0] : null;

  const getScoreBadgeClass = (score?: number | null) => {
    if (score === undefined || score === null) return "score-badge score-badge-blue";
    if (score >= 70) return "score-badge score-badge-green";
    if (score >= 50) return "score-badge score-badge-yellow";
    return "score-badge score-badge-red";
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  return (
    <div className="space-y-12">
      <section className="text-center pt-8 pb-4">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-blue-50 border border-blue-200 text-blue-700 text-xs font-semibold mb-6">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Next-Generation Resume Intelligence</span>
        </div>
        <h1 className="page-title max-w-4xl mx-auto mb-4">
          Elevate Your Career with AI Precision
        </h1>
        <p className="text-gray-600 text-lg sm:text-xl max-w-2xl mx-auto mb-8 font-normal leading-relaxed">
          Comprehensive resume scoring, automated skill gap diagnostics, and contextual job fit alignment.
        </p>
        <div className="flex flex-wrap items-center justify-center gap-4">
          <Link to="/upload" className="primary-button text-base px-7 py-3.5 shadow-lg">
            <FileUp className="w-5 h-5" />
            <span>Upload Resume</span>
          </Link>
          <Link to="/resumes" className="back-button text-base px-6 py-3.5">
            <FolderGit2 className="w-4 h-4 text-gray-500" />
            <span>My Resumes</span>
          </Link>
          <Link to="/help" className="back-button text-base px-6 py-3.5">
            <span>Documentation</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </section>

      {latestAnalysis && latestAnalysis.status === "done" && (
        <section className="form-div max-w-4xl mx-auto">
          <div className="flex items-center justify-between pb-6 border-b border-gray-100">
            <div>
              <span className="text-xs uppercase tracking-wider font-semibold text-gray-400">
                Latest Evaluation
              </span>
              <h2 className="text-2xl font-bold text-gray-900 mt-1">
                Overview & Compatibility
              </h2>
            </div>
            <Link
              to={`/analysis/${latestAnalysis.id}`}
              className="text-sm font-semibold text-indigo-600 hover:text-indigo-800 flex items-center gap-1"
            >
              <span>View Full Report</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 py-8">
            <div className="flex flex-col items-center justify-center p-6 rounded-2xl bg-gray-50 border border-gray-100">
              <div className="relative w-36 h-36 flex items-center justify-center">
                <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
                  <circle
                    cx="50"
                    cy="50"
                    r="40"
                    fill="transparent"
                    stroke="#e2e8f0"
                    strokeWidth="8"
                  />
                  <circle
                    cx="50"
                    cy="50"
                    r="40"
                    fill="transparent"
                    stroke="#606beb"
                    strokeWidth="8"
                    strokeDasharray={251.2}
                    strokeDashoffset={251.2 - (251.2 * latestAnalysis.resume_score) / 100}
                    strokeLinecap="round"
                  />
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <span className="text-3xl font-extrabold text-gray-900">
                    {latestAnalysis.resume_score}
                  </span>
                  <span className="text-xs font-semibold text-gray-500 uppercase">Score</span>
                </div>
              </div>
              <div className="mt-4 text-center">
                <div className="flex items-center gap-1.5 justify-center font-semibold text-gray-800">
                  <Award className="w-4 h-4 text-indigo-600" />
                  <span>Resume Strength</span>
                </div>
                <div className="mt-2">
                  <span className={getScoreBadgeClass(latestAnalysis.resume_score)}>
                    {latestAnalysis.resume_score >= 70
                      ? "Strong Candidate"
                      : latestAnalysis.resume_score >= 50
                      ? "Moderate Impact"
                      : "Needs Improvement"}
                  </span>
                </div>
              </div>
            </div>

            <div className="flex flex-col items-center justify-center p-6 rounded-2xl bg-gray-50 border border-gray-100">
              <div className="relative w-36 h-36 flex items-center justify-center">
                <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
                  <circle
                    cx="50"
                    cy="50"
                    r="40"
                    fill="transparent"
                    stroke="#e2e8f0"
                    strokeWidth="8"
                  />
                  <circle
                    cx="50"
                    cy="50"
                    r="40"
                    fill="transparent"
                    stroke="#10b981"
                    strokeWidth="8"
                    strokeDasharray={251.2}
                    strokeDashoffset={
                      latestAnalysis.compatibility_score !== null
                        ? 251.2 - (251.2 * latestAnalysis.compatibility_score) / 100
                        : 251.2
                    }
                    strokeLinecap="round"
                  />
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <span className="text-3xl font-extrabold text-gray-900">
                    {latestAnalysis.compatibility_score !== null
                      ? latestAnalysis.compatibility_score
                      : "N/A"}
                  </span>
                  <span className="text-xs font-semibold text-gray-500 uppercase">Fit</span>
                </div>
              </div>
              <div className="mt-4 text-center">
                <div className="flex items-center gap-1.5 justify-center font-semibold text-gray-800">
                  <Target className="w-4 h-4 text-emerald-600" />
                  <span>Job Fit Match</span>
                </div>
                <div className="mt-2">
                  {latestAnalysis.compatibility_score !== null ? (
                    <span className={getScoreBadgeClass(latestAnalysis.compatibility_score)}>
                      {latestAnalysis.compatibility_score >= 70
                        ? "High Alignment"
                        : latestAnalysis.compatibility_score >= 50
                        ? "Moderate Fit"
                        : "Low Alignment"}
                    </span>
                  ) : (
                    <span className="score-badge score-badge-blue">No JD Provided</span>
                  )}
                </div>
              </div>
            </div>
          </div>
          {latestAnalysis.ai_unavailable && (
            <div className="mt-4 px-4 py-2 rounded-lg bg-amber-50 border border-amber-200 text-amber-700 text-xs">
              ⚡ AI unavailable — scores are rule-based estimates.
            </div>
          )}
        </section>
      )}

      {analyses.length > 0 && (
        <section className="max-w-4xl mx-auto">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="section-title text-xl font-bold flex items-center gap-2">
                <History className="w-5 h-5 text-indigo-500" />
                Recent Analyses
              </h2>
            </div>
            <Link to="/history" className="text-sm font-semibold text-indigo-600 hover:text-indigo-800 flex items-center gap-1">
              <span>View All</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
          <div className="space-y-2">
            {analyses.map((a) => (
              <Link
                key={a.id}
                to={`/analysis/${a.id}`}
                className="flex items-center justify-between px-4 py-3 rounded-xl bg-white gradient-border hover:shadow-md transition-all duration-150 group"
              >
                <div className="flex items-center gap-3 min-w-0">
                  <div className={`w-2.5 h-2.5 rounded-full shrink-0 ${
                    a.status === "done" ? "bg-emerald-500" :
                    a.status === "failed" ? "bg-rose-500" : "bg-amber-500 animate-pulse"
                  }`} />
                  <span className="text-sm text-slate-900 font-medium group-hover:text-indigo-600 transition-colors truncate">
                    {a.job_description ? a.job_description.slice(0, 60) + (a.job_description.length > 60 ? "…" : "") : "General Analysis"}
                  </span>
                </div>
                <div className="flex items-center gap-3 shrink-0">
                  {a.status === "done" && (
                    <span className={`score-badge ${
                      a.resume_score >= 70 ? "score-badge-green" :
                      a.resume_score >= 40 ? "score-badge-yellow" :
                      "score-badge-red"
                    }`}>{a.resume_score}</span>
                  )}
                  <span className="text-xs text-slate-600 font-medium">{new Date(a.created_at).toLocaleDateString()}</span>
                </div>
              </Link>
            ))}
          </div>
        </section>
      )}

      <section className="max-w-4xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="section-title text-2xl font-bold">Latest Resumes</h2>
            <p className="text-xs text-gray-500 mt-0.5">Your 4 most recently uploaded documents</p>
          </div>
          {resumes.length > 0 && (
            <Link to="/resumes" className="text-sm font-semibold text-indigo-600 hover:text-indigo-800 flex items-center gap-1">
              <span>View All ({resumes.length})</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          )}
        </div>

        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="resume-card animate-pulse space-y-3">
                <div className="h-5 bg-gray-200 rounded w-2/3" />
                <div className="h-4 bg-gray-100 rounded w-1/3" />
              </div>
            ))}
          </div>
        ) : resumes.length === 0 ? (
          <div className="form-div text-center py-12">
            <div className="w-12 h-12 mx-auto rounded-full bg-blue-50 text-blue-600 flex items-center justify-center mb-4">
              <FileUp className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-gray-900 mb-1">No resumes uploaded yet</h3>
            <p className="text-sm text-gray-500 mb-6 max-w-sm mx-auto">
              Upload your resume in PDF or DOCX format to inspect skills, extract text, and receive actionable insights.
            </p>
            <Link to="/upload" className="primary-button text-sm">
              <FileUp className="w-4 h-4" />
              <span>Upload Resume</span>
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {resumes.slice(0, 4).map((item) => (
              <div
                key={item.id}
                className="resume-card flex flex-col justify-between hover:shadow-lg transition-shadow"
              >
                <div>
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <div className="flex items-center gap-2.5">
                      <div className="p-2 rounded-xl bg-indigo-50 text-indigo-600">
                        <FileText className="w-5 h-5" />
                      </div>
                      <span className="font-bold text-gray-900 text-sm truncate max-w-[180px]">
                        {item.filename}
                      </span>
                    </div>
                    {item.latest_score !== undefined && item.latest_score !== null ? (
                      <span className={getScoreBadgeClass(item.latest_score)}>
                        {item.latest_score}/100
                      </span>
                    ) : (
                      <span className="score-badge score-badge-blue text-xs">New</span>
                    )}
                  </div>

                  <div className="flex items-center gap-3 text-xs text-gray-500 mt-3">
                    <span className="flex items-center gap-1">
                      <Clock className="w-3.5 h-3.5" />
                      {new Date(item.created_at).toLocaleDateString()}
                    </span>
                    <span>•</span>
                    <span>{formatFileSize(item.size)}</span>
                  </div>
                </div>

                <div className="pt-4 mt-4 border-t border-gray-100 flex items-center justify-between">
                  <Link
                    to="/resumes"
                    className="text-xs font-semibold text-indigo-600 hover:text-indigo-800"
                  >
                    View Details
                  </Link>
                  <Link
                    to="/upload"
                    className="primary-button text-xs py-1.5 px-3 flex items-center gap-1"
                  >
                    <Sparkles className="w-3 h-3" />
                    <span>Analyze</span>
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
