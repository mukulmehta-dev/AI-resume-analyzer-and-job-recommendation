import { useEffect, useRef, useState } from "react";
import { useParams, useNavigate, Link } from "react-router";
import { api } from "../lib/api";
import { useToast } from "../components/Toast";
import type { Analysis, SkillWithCategory } from "../types";
import {
  RotateCcw,
  ArrowLeft,
  AlertTriangle,
  Zap,
  CheckCircle2,
  XCircle,
  HelpCircle,
  FileText,
  Briefcase,
  Layers,
  Sparkles,
} from "lucide-react";

const POLL_INTERVAL = 2000;

const SECTION_EXPLANATIONS: Record<string, string> = {
  contact: "Direct contact info and portfolio links for recruiters",
  summary: "Professional summary introducing value proposition",
  experience: "Work history with roles, achievements, and impact",
  education: "Academic background and formal degrees",
  skills: "Technical proficiencies and competencies list",
  projects: "Hands-on projects and open-source initiatives",
  certifications: "Industry certifications and credentials",
  awards: "Honors and professional recognition",
  publications: "Research papers and published technical articles",
  languages: "Spoken and natural language competencies",
  volunteer: "Community engagement and leadership activities",
  interests: "Personal activities and relevant extracurriculars",
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
  subtitle?: string;
}) {
  const pct = Math.min(100, Math.max(0, Math.round((value / max) * 100)));
  const radius = 54;
  const circ = 2 * Math.PI * radius;
  const offset = circ - (pct / 100) * circ;
  const color =
    pct >= 70 ? "#10b981" : pct >= 40 ? "#f59e0b" : "#ef4444";

  return (
    <div className="flex flex-col items-center justify-center p-6 bg-slate-800/60 rounded-2xl border border-slate-700/60 shadow-lg">
      <div className="relative">
        <svg width="140" height="140" viewBox="0 0 140 140" className="transform -rotate-90">
          <circle
            cx="70"
            cy="70"
            r={radius}
            fill="none"
            stroke="#1e293b"
            strokeWidth="11"
          />
          <circle
            cx="70"
            cy="70"
            r={radius}
            fill="none"
            stroke={color}
            strokeWidth="11"
            strokeDasharray={circ}
            strokeDashoffset={offset}
            strokeLinecap="round"
            className="transition-all duration-1000 ease-out"
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-3xl font-extrabold text-white tracking-tight">{value}</span>
          <span className="text-xs font-medium text-slate-400">/ {max}</span>
        </div>
      </div>
      <span className="mt-3 font-semibold text-white text-base text-center">{label}</span>
      {subtitle && <span className="text-xs text-slate-400 mt-0.5 text-center">{subtitle}</span>}
    </div>
  );
}

function PriorityBadge({ priority }: { priority: string }) {
  const map: Record<string, string> = {
    high: "bg-rose-500/20 text-rose-300 border-rose-500/30",
    medium: "bg-amber-500/20 text-amber-300 border-amber-500/30",
    low: "bg-sky-500/20 text-sky-300 border-sky-500/30",
  };
  return (
    <span
      className={`text-[11px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full border ${
        map[priority.toLowerCase()] ?? map.low
      }`}
    >
      {priority} Priority
    </span>
  );
}

function StepProgressBar({ step }: { step: number }) {
  const steps = [
    { title: "Extract Structure", desc: "Parsing document & contact info" },
    { title: "Score & Match", desc: "Evaluating skills against benchmarks" },
    { title: "AI Advisory", desc: "Generating strategic guidance" },
  ];

  return (
    <div className="w-full max-w-xl mx-auto my-8">
      <div className="grid grid-cols-3 gap-2 sm:gap-4 relative">
        {steps.map((s, idx) => {
          const isDone = idx < step;
          const isActive = idx === step;
          return (
            <div key={s.title} className="flex flex-col items-center text-center">
              <div
                className={`w-9 h-9 rounded-full flex items-center justify-center font-bold text-xs mb-2 transition-all duration-500 ${
                  isDone
                    ? "bg-emerald-500 text-white shadow-lg shadow-emerald-500/30"
                    : isActive
                    ? "bg-indigo-600 text-white ring-4 ring-indigo-500/30 animate-pulse"
                    : "bg-slate-800 text-slate-500 border border-slate-700"
                }`}
              >
                {isDone ? <CheckCircle2 className="w-5 h-5" /> : idx + 1}
              </div>
              <span
                className={`text-xs font-semibold ${
                  isActive ? "text-indigo-400" : isDone ? "text-white" : "text-slate-500"
                }`}
              >
                {s.title}
              </span>
              <span className="text-[10px] text-slate-500 hidden sm:block mt-0.5">{s.desc}</span>
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
      if (data.status !== "pending") {
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
      setProgressStep((prev) => (prev < 2 ? prev + 1 : prev));
    }, 2500);

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
        job_description: analysis.job_description || undefined,
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
      <div className="max-w-2xl mx-auto py-24 text-center px-4">
        <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-rose-500/10 text-rose-400 flex items-center justify-center">
          <AlertTriangle className="w-8 h-8" />
        </div>
        <h2 className="text-2xl font-bold text-white mb-2">Analysis Unavailable</h2>
        <p className="text-slate-400 mb-6">{error}</p>
        <Link
          to="/"
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-slate-800 text-slate-200 hover:bg-slate-700 transition-colors text-sm font-medium"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Dashboard
        </Link>
      </div>
    );
  }

  if (!analysis || analysis.status === "pending") {
    return (
      <div className="max-w-3xl mx-auto px-4 py-20 text-center">
        <div className="relative w-24 h-24 mx-auto mb-6">
          <div className="absolute inset-0 rounded-full border-4 border-indigo-500/20 animate-ping" />
          <div className="absolute inset-2 rounded-full border-4 border-indigo-500/40 animate-pulse" />
          <div className="absolute inset-4 rounded-full bg-indigo-600/20 flex items-center justify-center text-indigo-400">
            <Sparkles className="w-8 h-8 animate-spin" />
          </div>
        </div>
        <h2 className="text-2xl font-bold text-white mb-2">Analyzing Resume</h2>
        <p className="text-slate-400 text-sm max-w-md mx-auto">
          Our rule-based engine and AI pipeline are examining structure, skills, and match alignment.
        </p>

        <StepProgressBar step={progressStep} />
      </div>
    );
  }

  if (analysis.status === "failed") {
    return (
      <div className="max-w-xl mx-auto py-20 px-4 text-center">
        <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-rose-500/10 text-rose-400 flex items-center justify-center">
          <XCircle className="w-8 h-8" />
        </div>
        <h2 className="text-2xl font-bold text-white mb-2">Analysis Failed</h2>
        <p className="text-slate-400 text-sm mb-6 max-w-md mx-auto">
          {analysis.error ?? "An unexpected error interrupted processing."}
        </p>
        <div className="flex items-center justify-center gap-4">
          <button
            onClick={handleRetry}
            disabled={retrying}
            className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-indigo-600 text-white font-medium hover:bg-indigo-500 transition-colors shadow-lg shadow-indigo-600/30 text-sm disabled:opacity-50"
          >
            <RotateCcw className={`w-4 h-4 ${retrying ? "animate-spin" : ""}`} />
            {retrying ? "Retrying..." : "Retry Analysis"}
          </button>
          <Link
            to="/"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-slate-800 text-slate-300 hover:bg-slate-700 transition-colors text-sm font-medium"
          >
            <ArrowLeft className="w-4 h-4" /> Dashboard
          </Link>
        </div>
      </div>
    );
  }

  const categoryGroups: Record<string, string[]> = {};
  if (analysis.detected_skills_with_category && analysis.detected_skills_with_category.length > 0) {
    analysis.detected_skills_with_category.forEach((item: SkillWithCategory) => {
      const cat = item.category || "general";
      if (!categoryGroups[cat]) categoryGroups[cat] = [];
      categoryGroups[cat].push(item.name);
    });
  } else {
    categoryGroups["general"] = analysis.detected_skills || [];
  }

  const sectionEntries = Object.entries(analysis.sections || {});

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 space-y-8">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <Link
            to="/history"
            className="text-slate-400 hover:text-indigo-400 text-xs font-semibold uppercase tracking-wider inline-flex items-center gap-1 mb-2 transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" /> Back to History
          </Link>
          <h1 className="text-3xl font-extrabold text-white tracking-tight flex items-center gap-3">
            <span>Resume Intelligence Report</span>
            {analysis.resume_filename && (
              <span className="text-sm font-normal text-slate-400 bg-slate-800/80 px-3 py-1 rounded-lg border border-slate-700">
                {analysis.resume_filename}
              </span>
            )}
          </h1>
          <p className="text-slate-400 text-xs mt-1">
            Generated on {new Date(analysis.created_at).toLocaleString()}
          </p>
        </div>

        {analysis.ai_unavailable ? (
          <div className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs font-medium">
            <Zap className="w-4 h-4 text-amber-400 shrink-0" />
            <span>AI unavailable — showing rule-based results</span>
          </div>
        ) : (
          <div className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-xs font-medium">
            <Sparkles className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>AI Enhanced Report</span>
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
          <div className="flex flex-col items-center justify-center p-6 bg-slate-800/60 rounded-2xl border border-slate-700/60 text-center">
            <Briefcase className="w-10 h-10 text-slate-600 mb-2" />
            <span className="font-semibold text-slate-300 text-base">No Job Description</span>
            <span className="text-xs text-slate-500 mt-1 max-w-xs">
              Upload with target job requirements to calculate compatibility percentage.
            </span>
          </div>
        )}

        <div className="p-6 bg-slate-800/60 rounded-2xl border border-slate-700/60 flex flex-col justify-between">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-4 block">
            Skills Overview
          </span>
          <div className="space-y-3">
            <div className="flex justify-between items-center text-sm">
              <span className="text-slate-400 flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-indigo-500" /> Detected Skills
              </span>
              <span className="font-bold text-white">{analysis.detected_skills.length}</span>
            </div>
            <div className="flex justify-between items-center text-sm">
              <span className="text-slate-400 flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" /> Matching Skills
              </span>
              <span className="font-bold text-emerald-400">{analysis.matching_skills.length}</span>
            </div>
            <div className="flex justify-between items-center text-sm">
              <span className="text-slate-400 flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-rose-500" /> Missing Skills
              </span>
              <span className="font-bold text-rose-400">{analysis.missing_skills.length}</span>
            </div>
          </div>
          <div className="pt-4 border-t border-slate-700/60 mt-4 text-[11px] text-slate-500">
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

      {analysis.summary_feedback && (
        <div className="p-6 rounded-2xl bg-indigo-950/30 border border-indigo-800/50 shadow-inner">
          <h2 className="text-base font-bold text-indigo-300 flex items-center gap-2 mb-2">
            <Sparkles className="w-4 h-4 text-indigo-400" /> Executive Overview
          </h2>
          <p className="text-slate-200 text-sm leading-relaxed whitespace-pre-line">
            {analysis.summary_feedback}
          </p>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="p-6 rounded-2xl bg-slate-800/60 border border-slate-700/60 space-y-4">
          <h2 className="text-base font-bold text-emerald-400 flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5" /> Key Strengths
          </h2>
          <ul className="space-y-2.5">
            {analysis.strengths.length === 0 ? (
              <li className="text-slate-500 text-sm italic">No specific strengths identified.</li>
            ) : (
              analysis.strengths.map((str, idx) => (
                <li key={idx} className="flex items-start gap-2.5 text-sm text-slate-300">
                  <span className="text-emerald-400 font-bold leading-none mt-0.5">•</span>
                  <span>{str}</span>
                </li>
              ))
            )}
          </ul>
        </div>

        <div className="p-6 rounded-2xl bg-slate-800/60 border border-slate-700/60 space-y-4">
          <h2 className="text-base font-bold text-rose-400 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5" /> Areas for Improvement
          </h2>
          <ul className="space-y-2.5">
            {analysis.weaknesses.length === 0 ? (
              <li className="text-slate-500 text-sm italic">No major weaknesses detected.</li>
            ) : (
              analysis.weaknesses.map((w, idx) => (
                <li key={idx} className="flex items-start gap-2.5 text-sm text-slate-300">
                  <span className="text-rose-400 font-bold leading-none mt-0.5">•</span>
                  <span>{w}</span>
                </li>
              ))
            )}
          </ul>
        </div>
      </div>

      <div className="p-6 rounded-2xl bg-slate-800/60 border border-slate-700/60 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-700/60">
          <div>
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-indigo-400" /> AI suggestions (advisory only)
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              These suggestions are automated advisory insights to optimize your resume and do not constitute an automated hiring or employment decision.
            </p>
          </div>
        </div>

        {analysis.recommendations.length === 0 ? (
          <p className="text-slate-500 text-sm py-4">No specific recommendations at this time.</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
            {analysis.recommendations.map((rec, idx) => (
              <div
                key={idx}
                className="p-4 rounded-xl bg-slate-900/50 border border-slate-700/50 flex flex-col justify-between space-y-2 hover:border-slate-600 transition-colors"
              >
                <div className="flex items-start justify-between gap-2">
                  <span className="font-semibold text-white text-sm">{rec.title}</span>
                  <PriorityBadge priority={rec.priority} />
                </div>
                <p className="text-xs text-slate-400 leading-relaxed">{rec.detail}</p>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="p-6 rounded-2xl bg-slate-800/60 border border-slate-700/60 space-y-6">
        <h2 className="text-base font-bold text-white flex items-center gap-2">
          <Layers className="w-5 h-5 text-indigo-400" /> Detected Skills by Category
        </h2>

        <div className="space-y-5">
          {Object.entries(categoryGroups).map(([cat, skills]) => (
            <div key={cat} className="space-y-2">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
                {cat} ({skills.length})
              </span>
              <div className="flex flex-wrap gap-2">
                {skills.map((skill) => {
                  const isMatch = analysis.matching_skills.includes(skill);
                  return (
                    <span
                      key={skill}
                      className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-semibold border ${
                        isMatch
                          ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/30"
                          : "bg-indigo-500/20 text-indigo-300 border-indigo-500/30"
                      }`}
                    >
                      {isMatch && <CheckCircle2 className="w-3 h-3 text-emerald-400" />}
                      {skill}
                    </span>
                  );
                })}
              </div>
            </div>
          ))}
        </div>

        {analysis.missing_skills.length > 0 && (
          <div className="pt-4 border-t border-slate-700/60 space-y-2">
            <span className="text-xs font-bold uppercase tracking-wider text-rose-400">
              Missing Skills from Job Requirements ({analysis.missing_skills.length})
            </span>
            <div className="flex flex-wrap gap-2">
              {analysis.missing_skills.map((skill) => (
                <span
                  key={skill}
                  className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-semibold bg-rose-500/20 text-rose-300 border border-rose-500/30"
                >
                  <XCircle className="w-3 h-3 text-rose-400" />
                  {skill}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {sectionEntries.length > 0 && (
        <div className="p-6 rounded-2xl bg-slate-800/60 border border-slate-700/60 space-y-4">
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <FileText className="w-5 h-5 text-indigo-400" /> Resume Section Breakdown & Explanations
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {sectionEntries.map(([name, present]) => {
              const explanation =
                SECTION_EXPLANATIONS[name.toLowerCase()] ??
                `Standard ${name.replace(/_/g, " ")} section in resume structure`;

              return (
                <div
                  key={name}
                  className="p-3.5 rounded-xl bg-slate-900/40 border border-slate-700/50 flex items-start justify-between gap-3"
                >
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-white text-sm capitalize">
                        {name.replace(/_/g, " ")}
                      </span>
                      <span
                        className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full ${
                          present
                            ? "bg-emerald-500/20 text-emerald-300"
                            : "bg-slate-700 text-slate-400"
                        }`}
                      >
                        {present ? "Present" : "Missing"}
                      </span>
                    </div>
                    <p className="text-xs text-slate-400 mt-1">{explanation}</p>
                  </div>
                  {present ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                  ) : (
                    <HelpCircle className="w-4 h-4 text-slate-500 shrink-0 mt-0.5" />
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {analysis.job_description && (
        <div className="p-6 rounded-2xl bg-slate-800/60 border border-slate-700/60 space-y-2">
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <Briefcase className="w-5 h-5 text-indigo-400" /> Target Job Description
          </h2>
          <p className="text-slate-300 text-xs whitespace-pre-wrap leading-relaxed max-h-48 overflow-y-auto bg-slate-900/50 p-4 rounded-xl border border-slate-700/40 font-mono">
            {analysis.job_description}
          </p>
        </div>
      )}
    </div>
  );
}
