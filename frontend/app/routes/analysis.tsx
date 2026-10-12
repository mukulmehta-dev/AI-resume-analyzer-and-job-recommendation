import { useEffect, useState, useRef } from "react";
import { useParams, Link, useNavigate } from "react-router";
import { api } from "../lib/api";
import { useToast } from "../components/Toast";
import type { Analysis, SectionSubScore } from "../types";
import {
  CheckCircle2,
  AlertTriangle,
  Sparkles,
  ArrowLeft,
  Briefcase,
  FileText,
  Clock,
  Layers,
  Zap,
  RotateCcw,
  XCircle,
} from "lucide-react";

const POLL_INTERVAL = 2000;

const SKILL_CATEGORIES: { key: string; label: string; aliases: string[] }[] = [
  { key: "languages", label: "Programming Languages", aliases: ["languages", "programming languages", "language"] },
  { key: "frameworks", label: "Frameworks & Libraries", aliases: ["frameworks", "libraries", "framework"] },
  { key: "databases", label: "Databases & Storage", aliases: ["databases", "database", "storage"] },
  { key: "cloud_devops", label: "Cloud & DevOps", aliases: ["cloud_devops", "cloud", "devops", "infrastructure"] },
  { key: "tools_platforms", label: "Tools & Platforms", aliases: ["tools_platforms", "tools", "platforms", "tool"] },
];

const SECTION_EXPLANATIONS: Record<string, string> = {
  contact_info: "Evaluates completeness and professional formatting of candidate contact channels.",
  work_experience: "Measures employment timeline depth, role titles, and quantifiable project contributions.",
  education: "Assesses university credentials, field of study, and academic achievements.",
  skills: "Scans for verified technical proficiencies, modern software stacks, and relevant domain tools.",
  projects: "Analyzes demonstrable open-source, production, or portfolio software implementations.",
  certifications: "Validates accredited industry licenses, vendor specializations, and professional exams.",
};

function ScoreGauge({
  value,
  max = 100,
  label,
  subtitle,
}: {
  value: number;
  max?: number;
  label: string;
  subtitle: string;
}) {
  const pct = Math.min(100, Math.max(0, Math.round((value / max) * 100)));
  const radius = 54;
  const circ = 2 * Math.PI * radius;
  const offset = circ - (pct / 100) * circ;

  const strokeColor =
    pct >= 70 ? "#10b981" : pct >= 40 ? "#f59e0b" : "#ef4444";
  const badgeClass =
    pct >= 70
      ? "score-badge-green"
      : pct >= 40
      ? "score-badge-yellow"
      : "score-badge-red";

  return (
    <div className="bg-white gradient-border rounded-2xl p-6 flex flex-col items-center text-center shadow-sm">
      <div className="relative w-36 h-36 flex items-center justify-center my-2">
        <svg className="w-full h-full -rotate-90" viewBox="0 0 128 128">
          <circle
            cx="64"
            cy="64"
            r={radius}
            className="stroke-slate-100"
            strokeWidth="12"
            fill="transparent"
          />
          <circle
            cx="64"
            cy="64"
            r={radius}
            stroke={strokeColor}
            strokeWidth="12"
            strokeDasharray={circ}
            strokeDashoffset={offset}
            strokeLinecap="round"
            fill="transparent"
            style={{ transition: "stroke-dashoffset 1s ease-in-out" }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-3xl font-extrabold text-slate-900 tracking-tight">
            {pct}
          </span>
          <span className="text-[10px] text-slate-500 font-semibold tracking-wider uppercase">
            / {max}
          </span>
        </div>
      </div>
      <div className="mt-2">
        <span className={`score-badge ${badgeClass} mb-2`}>{label}</span>
        <p className="text-xs text-dark-200 mt-1 max-w-[200px] leading-relaxed">
          {subtitle}
        </p>
      </div>
    </div>
  );
}

function PriorityBadge({ priority }: { priority: string }) {
  const map: Record<string, { bg: string; text: string }> = {
    high: { bg: "bg-rose-50 border-rose-200", text: "text-rose-800" },
    medium: { bg: "bg-amber-50 border-amber-200", text: "text-amber-800" },
    low: { bg: "bg-blue-50 border-blue-200", text: "text-blue-800" },
  };
  const cfg = map[priority.toLowerCase()] || map.medium;
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider border ${cfg.bg} ${cfg.text}`}
    >
      {priority}
    </span>
  );
}

function StepProgressBar({ step }: { step: number }) {
  const steps = [
    { num: 1, label: "Extracting Text" },
    { num: 2, label: "Parsing Sections" },
    { num: 3, label: "Scoring Structure" },
    { num: 4, label: "AI Insights" },
  ];

  return (
    <div className="w-full max-w-lg mx-auto py-6">
      <div className="flex items-center justify-between relative">
        <div className="absolute top-1/2 left-0 right-0 h-0.5 bg-slate-200 -translate-y-1/2 z-0" />
        <div
          className="absolute top-1/2 left-0 h-0.5 bg-indigo-600 -translate-y-1/2 z-0 transition-all duration-700 ease-out"
          style={{ width: `${((step - 1) / (steps.length - 1)) * 100}%` }}
        />

        {steps.map((s, idx) => {
          const isDone = idx < step;
          const isActive = idx === step;
          return (
            <div key={s.num} className="flex flex-col items-center relative z-10">
              <div
                className={`w-9 h-9 rounded-full flex items-center justify-center font-bold text-xs transition-all duration-300 ${
                  isDone
                    ? "bg-indigo-600 text-white shadow-md shadow-indigo-200"
                    : isActive
                    ? "bg-white text-indigo-600 border-2 border-indigo-600 ring-4 ring-indigo-50"
                    : "bg-white text-slate-400 border border-slate-300"
                }`}
              >
                {isDone ? <CheckCircle2 className="w-4 h-4" /> : s.num}
              </div>
              <span
                className={`text-[11px] font-medium mt-2 whitespace-nowrap ${
                  isDone || isActive ? "text-indigo-900 font-semibold" : "text-slate-400"
                }`}
              >
                {s.label}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default function AnalysisPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { addToast } = useToast();
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [retrying, setRetrying] = useState(false);
  const [progressStep, setProgressStep] = useState(1);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchAnalysis = async () => {
    try {
      const { data } = await api.get<Analysis>(`/analyses/${id}`);
      setAnalysis(data);

      if (data.status === "done" || data.status === "failed") {
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
          intervalRef.current = null;
        }
      }
    } catch (e: any) {
      const msg = e?.response?.data?.detail ?? "Failed to load analysis.";
      setError(msg);
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    }
  };

  useEffect(() => {
    fetchAnalysis();
    intervalRef.current = setInterval(fetchAnalysis, POLL_INTERVAL);

    const stepTimer = setInterval(() => {
      setProgressStep((prev) => (prev < 4 ? prev + 1 : prev));
    }, 1800);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
      clearInterval(stepTimer);
    };
  }, [id]);

  const handleRetry = async () => {
    if (!analysis) return;
    setRetrying(true);
    try {
      const resp = await api.post<{ id: string }>("/analyses", {
        resume_id: analysis.resume_id,
        job_description: analysis.job_description,
      });
      addToast("Analysis restarted.", "success");
      navigate(`/analysis/${resp.data.id}`);
    } catch (e: any) {
      const msg = e?.response?.data?.detail ?? "Failed to restart analysis.";
      addToast(msg, "error");
    } finally {
      setRetrying(false);
    }
  };

  if (error) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-16 text-center space-y-4">
        <div className="inline-flex p-3 rounded-full bg-rose-50 text-rose-600 mb-2">
          <AlertTriangle className="w-8 h-8" />
        </div>
        <h1 className="text-2xl font-bold text-slate-900">Analysis Unavailable</h1>
        <p className="text-sm text-dark-200">{error}</p>
        <Link
          to="/history"
          className="inline-flex items-center gap-2 mt-4 px-4 py-2 rounded-xl bg-indigo-600 text-white font-medium text-sm hover:bg-indigo-700 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" /> Back to History
        </Link>
      </div>
    );
  }

  if (!analysis || analysis.status === "pending") {
    return (
      <div className="max-w-3xl mx-auto px-4 py-16 text-center space-y-8">
        <div className="space-y-3">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-indigo-50 border border-indigo-100 text-indigo-700 text-xs font-semibold tracking-wide uppercase">
            <Clock className="w-3.5 h-3.5 animate-spin" /> Pipeline Processing
          </div>
          <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">
            Analyzing Resume
          </h1>
          <p className="text-sm text-dark-200 max-w-md mx-auto">
            Extracting text structure, computing weighted ATS heuristics, and generating comprehensive insights.
          </p>
        </div>

        <div className="bg-white gradient-border rounded-2xl p-8 shadow-sm">
          <StepProgressBar step={progressStep} />
          <div className="flex items-center justify-center gap-3 mt-6 text-sm text-dark-200">
            <span className="w-2.5 h-2.5 rounded-full bg-indigo-600 animate-ping" />
            <span>Checking execution status every 2 seconds...</span>
          </div>
        </div>
      </div>
    );
  }

  if (analysis.status === "failed") {
    return (
      <div className="max-w-2xl mx-auto px-4 py-16 text-center space-y-6">
        <div className="inline-flex p-3 rounded-full bg-rose-50 text-rose-600 mb-2">
          <AlertTriangle className="w-10 h-10" />
        </div>
        <h1 className="text-3xl font-extrabold text-slate-900">Analysis Failed</h1>
        <p className="text-sm text-dark-200 max-w-md mx-auto">
          {analysis.error || "The processing pipeline encountered an unexpected error while evaluating this resume."}
        </p>

        <div className="flex items-center justify-center gap-4 pt-2">
          <button
            onClick={handleRetry}
            disabled={retrying}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-sm transition-all shadow-md shadow-indigo-100 disabled:opacity-50"
          >
            <RotateCcw className={`w-4 h-4 ${retrying ? "animate-spin" : ""}`} />
            {retrying ? "Restarting..." : "Try Again"}
          </button>
          <Link
            to="/history"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 font-semibold text-sm transition-all"
          >
            <ArrowLeft className="w-4 h-4" /> Return to History
          </Link>
        </div>
      </div>
    );
  }

  const categoryMap: Record<string, string[]> = {
    languages: [],
    frameworks: [],
    databases: [],
    cloud_devops: [],
    tools_platforms: [],
    other: [],
  };

  if (analysis.detected_skills_with_category && analysis.detected_skills_with_category.length > 0) {
    analysis.detected_skills_with_category.forEach((item) => {
      const rawCat = (item.category || "").toLowerCase().trim();
      const matched = SKILL_CATEGORIES.find(
        (c) => c.key === rawCat || c.aliases.includes(rawCat)
      );
      if (matched) {
        if (!categoryMap[matched.key].includes(item.name)) {
          categoryMap[matched.key].push(item.name);
        }
      } else {
        if (!categoryMap.other.includes(item.name)) {
          categoryMap.other.push(item.name);
        }
      }
    });
  } else {
    categoryMap.other = [...analysis.detected_skills];
  }

  const sectionEntries = Object.entries(analysis.sections || {});
  const hasAiOutput = !analysis.ai_unavailable && Boolean(analysis.ai_model || analysis.ai_insights);

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 space-y-8">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <Link
            to="/history"
            className="text-dark-200 hover:text-indigo-600 text-xs font-semibold uppercase tracking-wider inline-flex items-center gap-1 mb-2 transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" /> Back to History
          </Link>
          <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight flex items-center gap-3 flex-wrap">
            <span>Resume Intelligence Report</span>
            {analysis.resume_filename && (
              <span className="text-sm font-normal text-slate-700 bg-slate-100 px-3 py-1 rounded-lg border border-slate-200">
                {analysis.resume_filename}
              </span>
            )}
          </h1>
          <p className="text-dark-200 text-xs mt-1">
            Generated on {new Date(analysis.created_at).toLocaleString()}
          </p>
        </div>

        {!analysis.ai_unavailable && analysis.ai_model ? (
          <div className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-semibold">
            <Sparkles className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>AI Enhanced Report</span>
          </div>
        ) : (
          <div className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-amber-50 border border-amber-200 text-amber-800 text-xs font-semibold">
            <Zap className="w-4 h-4 text-amber-600 shrink-0" />
            <span>Rule-based assessment</span>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        <ScoreGauge
          value={analysis.resume_score}
          label="Resume Health Score"
          subtitle="Based on format, clarity, achievements & structure"
        />

        {analysis.compatibility_score !== null ? (
          <ScoreGauge
            value={analysis.compatibility_score}
            label="Job Compatibility"
            subtitle="Alignment with submitted job requirements"
          />
        ) : (
          <div className="bg-white gradient-border rounded-2xl p-6 flex flex-col items-center justify-center text-center shadow-sm">
            <Briefcase className="w-10 h-10 text-slate-300 mb-2" />
            <span className="font-semibold text-slate-800 text-base">No Job Description</span>
            <span className="text-xs text-dark-200 mt-1 max-w-xs">
              Upload with target job requirements to calculate compatibility percentage.
            </span>
          </div>
        )}

        <div className="bg-white gradient-border rounded-2xl p-6 flex flex-col justify-between shadow-sm">
          <span className="text-xs font-bold uppercase tracking-wider text-dark-200 mb-4 block">
            Skills Overview
          </span>
          <div className="space-y-3">
            <div className="flex justify-between items-center text-sm">
              <span className="text-dark-200 flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-indigo-500" /> Detected Skills
              </span>
              <span className="font-bold text-slate-900">{analysis.detected_skills.length}</span>
            </div>
            <div className="flex justify-between items-center text-sm">
              <span className="text-dark-200 flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" /> Matching Skills
              </span>
              <span className="font-bold text-emerald-600">{analysis.matching_skills.length}</span>
            </div>
            <div className="flex justify-between items-center text-sm">
              <span className="text-dark-200 flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-rose-500" /> Missing Skills
              </span>
              <span className="font-bold text-rose-600">{analysis.missing_skills.length}</span>
            </div>
          </div>
          <div className="pt-4 border-t border-slate-100 mt-4 text-[11px] text-dark-200">
            {analysis.matching_skills.length > 0
              ? `${Math.round(
                  (analysis.matching_skills.length /
                    (analysis.matching_skills.length + analysis.missing_skills.length || 1)) *
                    100
                )}% skill overlap with job requisites`
              : "Direct competency breakdown"}
          </div>
        </div>
      </div>

      {analysis.job_skills && analysis.job_skills.length > 0 && (
        <div className="bg-white gradient-border rounded-2xl p-6 space-y-4 shadow-sm">
          <div className="flex items-center justify-between pb-2 border-b border-slate-100">
            <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <Briefcase className="w-5 h-5 text-indigo-600" /> Skills required by the job
            </h2>
            <span className="text-xs font-semibold text-dark-200">
              {analysis.job_skills.length} required/preferred competencies
            </span>
          </div>
          <div className="flex flex-wrap gap-2">
            {analysis.job_skills.map((skill, idx) => {
              const isMatched = analysis.matching_skills.includes(skill.name);
              return (
                <span
                  key={idx}
                  className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold border ${
                    skill.type === "required"
                      ? isMatched
                        ? "bg-emerald-50 text-emerald-800 border-emerald-200"
                        : "bg-rose-50 text-rose-800 border-rose-200"
                      : isMatched
                      ? "bg-emerald-50 text-emerald-800 border-emerald-200"
                      : "bg-blue-50 text-blue-800 border-blue-200"
                  }`}
                >
                  {isMatched && <CheckCircle2 className="w-3 h-3 text-emerald-600" />}
                  <span>{skill.name}</span>
                  <span className="text-[10px] font-semibold uppercase text-emerald-900">
                    ({skill.type})
                  </span>
                </span>
              );
            })}
          </div>
        </div>
      )}

      {hasAiOutput ? (
        <div className="bg-white gradient-border rounded-2xl p-6 space-y-5 shadow-sm">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-100">
            <div>
              <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-indigo-600" /> AI suggestions (advisory only)
              </h2>
              <p className="text-xs text-dark-200 mt-0.5">
                Automated advisory recommendations designed to enhance candidate positioning.
              </p>
            </div>
            {analysis.ai_model && (
              <span className="text-xs font-mono text-dark-200 bg-slate-100 px-2.5 py-1 rounded-lg border border-slate-200">
                Model: {analysis.ai_model}
              </span>
            )}
          </div>

          {analysis.summary_feedback && (
            <div className="p-4 rounded-xl bg-indigo-50/50 border border-indigo-100">
              <h3 className="text-xs font-bold uppercase tracking-wider text-indigo-900 mb-1">
                Executive Assessment
              </h3>
              <p className="text-sm text-slate-800 leading-relaxed whitespace-pre-line">
                {analysis.summary_feedback}
              </p>
            </div>
          )}

          {analysis.job_tailored_tips && analysis.job_tailored_tips.length > 0 && (
            <div className="p-4 rounded-xl bg-blue-50/50 border border-blue-100 space-y-2">
              <h3 className="text-xs font-bold uppercase tracking-wider text-blue-900">
                Job-Tailored Tips
              </h3>
              <ul className="space-y-1.5">
                {analysis.job_tailored_tips.map((tip, idx) => (
                  <li key={idx} className="flex items-start gap-2 text-xs text-slate-800">
                    <span className="text-blue-600 font-bold leading-none mt-0.5">•</span>
                    <span>{tip}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {analysis.ai_insights?.recommendations && analysis.ai_insights.recommendations.length > 0 && (
            <div className="space-y-3 pt-2">
              <h3 className="text-xs font-bold uppercase tracking-wider text-dark-200">
                Actionable AI Action Items
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {analysis.ai_insights.recommendations.map((rec, idx) => (
                  <div
                    key={idx}
                    className="p-4 rounded-xl bg-slate-50 border border-slate-200 flex flex-col justify-between space-y-2"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <span className="font-semibold text-slate-900 text-sm">{rec.title}</span>
                      <PriorityBadge priority={rec.priority} />
                    </div>
                    <p className="text-xs text-dark-200 leading-relaxed">{rec.detail}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="bg-white gradient-border rounded-2xl p-6 space-y-4 shadow-sm">
          <div className="pb-3 border-b border-slate-100">
            <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <FileText className="w-5 h-5 text-indigo-600" /> Suggestions (rule-based)
            </h2>
            <p className="text-xs text-dark-200 mt-0.5">
              Deterministic rule-based recommendations extracted from standard ATS evaluation heuristics.
            </p>
          </div>

          {analysis.recommendations.length === 0 ? (
            <p className="text-dark-200 text-sm py-4">No specific recommendations at this time.</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
              {analysis.recommendations.map((rec, idx) => (
                <div
                  key={idx}
                  className="p-4 rounded-xl bg-slate-50 border border-slate-200 flex flex-col justify-between space-y-2"
                >
                  <div className="flex items-start justify-between gap-2">
                    <span className="font-semibold text-slate-900 text-sm">{rec.title}</span>
                    <PriorityBadge priority={rec.priority} />
                  </div>
                  <p className="text-xs text-dark-200 leading-relaxed">{rec.detail}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white gradient-border rounded-2xl p-6 space-y-4 shadow-sm">
          <h2 className="text-base font-bold text-emerald-800 flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5 text-emerald-600" /> Key Strengths (rule-based)
          </h2>
          <ul className="space-y-2.5">
            {analysis.strengths.length === 0 ? (
              <li className="text-dark-200 text-sm italic">No specific strengths identified.</li>
            ) : (
              analysis.strengths.map((str, idx) => (
                <li key={idx} className="flex items-start gap-2.5 text-sm text-slate-800">
                  <span className="text-emerald-600 font-bold leading-none mt-0.5">•</span>
                  <span>{str}</span>
                </li>
              ))
            )}
          </ul>
        </div>

        <div className="bg-white gradient-border rounded-2xl p-6 space-y-4 shadow-sm">
          <h2 className="text-base font-bold text-rose-800 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-rose-600" /> Areas for Improvement (rule-based)
          </h2>
          <ul className="space-y-2.5">
            {analysis.weaknesses.length === 0 ? (
              <li className="text-dark-200 text-sm italic">No major weaknesses detected.</li>
            ) : (
              analysis.weaknesses.map((w, idx) => (
                <li key={idx} className="flex items-start gap-2.5 text-sm text-slate-800">
                  <span className="text-rose-600 font-bold leading-none mt-0.5">•</span>
                  <span>{w}</span>
                </li>
              ))
            )}
          </ul>
        </div>
      </div>

      <div className="bg-white gradient-border rounded-2xl p-6 space-y-6 shadow-sm">
        <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
          <Layers className="w-5 h-5 text-indigo-600" /> Detected Skills by Category
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {SKILL_CATEGORIES.map((cat) => {
            const skills = categoryMap[cat.key] || [];
            return (
              <div
                key={cat.key}
                className="p-4 rounded-xl bg-slate-50 border border-slate-200 flex flex-col justify-between space-y-3"
              >
                <div className="flex items-center justify-between pb-2 border-b border-slate-200">
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-800">
                    {cat.label}
                  </span>
                  <span
                    className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                      skills.length > 0
                        ? "bg-indigo-100 text-indigo-800"
                        : "bg-slate-200 text-slate-600"
                    }`}
                  >
                    {skills.length}
                  </span>
                </div>
                <div className="flex flex-wrap gap-1.5 min-h-[32px] items-center">
                  {skills.length === 0 ? (
                    <span className="text-xs text-dark-200 italic">None detected</span>
                  ) : (
                    skills.map((skill) => {
                      const isMatch = analysis.matching_skills.includes(skill);
                      return (
                        <span
                          key={skill}
                          className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium border ${
                            isMatch
                              ? "bg-emerald-50 text-emerald-800 border-emerald-200"
                              : "bg-indigo-50 text-indigo-800 border-indigo-200"
                          }`}
                        >
                          {isMatch && <CheckCircle2 className="w-3 h-3 text-emerald-600" />}
                          {skill}
                        </span>
                      );
                    })
                  )}
                </div>
              </div>
            );
          })}
          {categoryMap.other.length > 0 && (
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 flex flex-col justify-between space-y-3">
              <div className="flex items-center justify-between pb-2 border-b border-slate-200">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-800">
                  Other / Uncategorized
                </span>
                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-200 text-slate-700">
                  {categoryMap.other.length}
                </span>
              </div>
              <div className="flex flex-wrap gap-1.5 min-h-[32px] items-center">
                {categoryMap.other.map((skill) => {
                  const isMatch = analysis.matching_skills.includes(skill);
                  return (
                    <span
                      key={skill}
                      className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium border ${
                        isMatch
                          ? "bg-emerald-50 text-emerald-800 border-emerald-200"
                          : "bg-slate-100 text-slate-800 border-slate-300"
                      }`}
                    >
                      {isMatch && <CheckCircle2 className="w-3 h-3 text-emerald-600" />}
                      {skill}
                    </span>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        {analysis.missing_skills.length > 0 && (
          <div className="pt-4 border-t border-slate-100 space-y-2">
            <span className="text-xs font-bold uppercase tracking-wider text-rose-800">
              Missing Skills from Job Requirements ({analysis.missing_skills.length})
            </span>
            <div className="flex flex-wrap gap-2">
              {analysis.missing_skills.map((skill) => (
                <span
                  key={skill}
                  className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-semibold bg-rose-50 text-rose-800 border border-rose-200"
                >
                  <XCircle className="w-3 h-3 text-rose-600" />
                  {skill}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {sectionEntries.length > 0 && (
        <div className="bg-white gradient-border rounded-2xl p-6 space-y-5 shadow-sm">
          <div className="flex items-center justify-between pb-2 border-b border-slate-100">
            <div>
              <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <FileText className="w-5 h-5 text-indigo-600" /> Section Sub-Scores & Structural Breakdown
              </h2>
              <p className="text-xs text-dark-200 mt-0.5">
                Evaluated against structural benchmarks with weighted contribution to final score.
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {sectionEntries.map(([name, rawVal]) => {
              const isObj = typeof rawVal === "object" && rawVal !== null;
              const subObj = isObj ? (rawVal as SectionSubScore) : null;
              const score = subObj ? subObj.score : rawVal ? 100 : 0;
              const weightPct = subObj && subObj.weight ? Math.round(subObj.weight * 100) : null;
              const explanation =
                subObj?.explanation ??
                SECTION_EXPLANATIONS[name.toLowerCase()] ??
                `Standard ${name.replace(/_/g, " ")} section in resume structure`;

              const barColor =
                score >= 70 ? "bg-emerald-500" : score >= 40 ? "bg-amber-500" : "bg-rose-500";
              const scoreColor =
                score >= 70 ? "text-emerald-700" : score >= 40 ? "text-amber-700" : "text-rose-700";

              return (
                <div
                  key={name}
                  className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3 flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-center justify-between gap-2 mb-2">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-slate-900 text-sm capitalize">
                          {name.replace(/_/g, " ")}
                        </span>
                        {weightPct !== null && (
                          <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-200 text-slate-700">
                            Weight: {weightPct}%
                          </span>
                        )}
                      </div>
                      <span className={`text-xs font-extrabold ${scoreColor}`}>
                        {score} / 100
                      </span>
                    </div>

                    <div className="w-full bg-slate-200 rounded-full h-2.5 overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all duration-700 ease-out ${barColor}`}
                        style={{ width: `${Math.min(100, Math.max(0, score))}%` }}
                      />
                    </div>
                  </div>

                  <p className="text-xs text-dark-200 leading-relaxed pt-1">
                    {explanation}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {analysis.job_description && (
        <div className="bg-white gradient-border rounded-2xl p-6 space-y-2 shadow-sm">
          <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <Briefcase className="w-5 h-5 text-indigo-600" /> Target Job Description
          </h2>
          <p className="text-slate-800 text-xs whitespace-pre-wrap leading-relaxed max-h-48 overflow-y-auto bg-slate-50 p-4 rounded-xl border border-slate-200 font-mono">
            {analysis.job_description}
          </p>
        </div>
      )}
    </div>
  );
}
