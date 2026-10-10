import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router";
import { useAuthStore } from "../store/auth";
import { api } from "../lib/api";
import { useToast } from "../components/Toast";
import type { Resume } from "../types";
import {
  FileText,
  Clock,
  Eye,
  Download,
  Trash2,
  Sparkles,
  Upload,
  X,
  AlertTriangle,
  FileCheck2,
} from "lucide-react";

interface ResumeItem extends Resume {
  latest_score?: number | null;
  analyses_count?: number;
}

export default function ResumesPage() {
  const { user, initialized } = useAuthStore();
  const navigate = useNavigate();
  const { addToast } = useToast();

  const [resumes, setResumes] = useState<ResumeItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [previewResume, setPreviewResume] = useState<ResumeItem | null>(null);
  const [previewText, setPreviewText] = useState<string | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<ResumeItem | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    if (initialized && !user) {
      navigate("/auth");
      return;
    }

    if (user) {
      fetchResumes();
    }
  }, [user, initialized, navigate]);

  const fetchResumes = async () => {
    setLoading(true);
    try {
      const res = await api.get<ResumeItem[]>("/resumes");
      setResumes(res.data);
    } catch {
      addToast("Failed to fetch resume list.", "error");
    } finally {
      setLoading(false);
    }
  };

  const handleOpenPreview = async (item: ResumeItem) => {
    setPreviewResume(item);
    setPreviewText(null);
    setPreviewLoading(true);

    try {
      const res = await api.get<{ extracted_text: string }>(`/resumes/${item.id}`);
      setPreviewText(res.data.extracted_text);
    } catch {
      addToast("Failed to load resume details.", "error");
    } finally {
      setPreviewLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    setIsDeleting(true);

    try {
      await api.delete(`/resumes/${deleteTarget.id}`);
      setResumes((prev) => prev.filter((r) => r.id !== deleteTarget.id));
      addToast("Resume deleted successfully.", "success");
      setDeleteTarget(null);
    } catch {
      addToast("Failed to delete resume.", "error");
    } finally {
      setIsDeleting(false);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  const getScoreBadge = (score?: number | null) => {
    if (score === undefined || score === null) {
      return <span className="score-badge score-badge-blue">Not analyzed</span>;
    }
    if (score >= 70) {
      return <span className="score-badge score-badge-green">{score}/100</span>;
    }
    if (score >= 50) {
      return <span className="score-badge score-badge-yellow">{score}/100</span>;
    }
    return <span className="score-badge score-badge-red">{score}/100</span>;
  };

  return (
    <div className="max-w-5xl mx-auto py-8">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="page-title text-4xl mb-2">My Resumes</h1>
          <p className="text-gray-600 text-sm">
            Manage your uploaded resumes, preview contents, inspect evaluations, and re-run evaluations.
          </p>
        </div>
        <Link to="/upload" className="primary-button text-sm px-6 py-3 self-start sm:self-auto">
          <Upload className="w-4 h-4" />
          <span>Upload Resume</span>
        </Link>
      </div>

      {loading ? (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="resume-card animate-pulse flex items-center justify-between">
              <div className="space-y-2 w-1/3">
                <div className="h-4 bg-gray-200 rounded w-full" />
                <div className="h-3 bg-gray-100 rounded w-1/2" />
              </div>
              <div className="h-8 bg-gray-200 rounded-full w-24" />
            </div>
          ))}
        </div>
      ) : resumes.length === 0 ? (
        <div className="form-div text-center py-16">
          <div className="w-14 h-14 mx-auto rounded-full bg-indigo-50 text-indigo-600 flex items-center justify-center mb-4">
            <FileText className="w-7 h-7" />
          </div>
          <h2 className="text-xl font-bold text-gray-900 mb-2">No resumes uploaded yet</h2>
          <p className="text-gray-500 text-sm max-w-md mx-auto mb-6">
            Upload your resume in PDF or DOCX format to inspect skills, extract text, and receive actionable insights.
          </p>
          <Link to="/upload" className="primary-button text-sm">
            <Upload className="w-4 h-4" />
            <span>Upload Your First Resume</span>
          </Link>
        </div>
      ) : (
        <div className="space-y-4">
          {resumes.map((item) => (
            <div key={item.id} className="resume-card">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div className="flex items-start gap-4">
                  <div className="p-3 rounded-2xl bg-indigo-50 text-indigo-600 flex-shrink-0 mt-0.5">
                    <FileText className="w-6 h-6" />
                  </div>
                  <div>
                    <h3 className="font-bold text-gray-900 text-base">{item.filename}</h3>
                    <div className="flex flex-wrap items-center gap-3 text-xs text-gray-500 mt-1">
                      <span className="flex items-center gap-1">
                        <Clock className="w-3.5 h-3.5" />
                        {new Date(item.created_at).toLocaleDateString()}
                      </span>
                      <span>•</span>
                      <span>{formatFileSize(item.size)}</span>
                      <span>•</span>
                      <span className="uppercase text-[10px] font-semibold tracking-wider px-2 py-0.5 rounded-full bg-gray-100 text-gray-600">
                        {item.mime.includes("pdf") ? "PDF" : "DOCX"}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex flex-wrap items-center justify-between md:justify-end gap-3 pt-3 md:pt-0 border-t md:border-t-0 border-gray-100">
                  <div className="flex items-center gap-2 mr-2">
                    <span className="text-xs text-gray-400 font-medium hidden sm:inline">Score:</span>
                    {getScoreBadge(item.latest_score)}
                  </div>

                  <div className="flex items-center gap-1.5">
                    <button
                      onClick={() => handleOpenPreview(item)}
                      className="back-button text-xs py-1.5 px-3"
                      title="Preview Resume"
                    >
                      <Eye className="w-3.5 h-3.5 text-gray-600" />
                      <span className="hidden sm:inline">Preview</span>
                    </button>

                    <a
                      href={`/api/resumes/${item.id}/file`}
                      download={item.filename}
                      target="_blank"
                      rel="noreferrer"
                      className="back-button text-xs py-1.5 px-3"
                      title="Download File"
                    >
                      <Download className="w-3.5 h-3.5 text-gray-600" />
                      <span className="hidden sm:inline">Download</span>
                    </a>

                    <Link
                      to={`/upload`}
                      className="primary-button text-xs py-1.5 px-3.5"
                      title="Analyze Resume"
                    >
                      <Sparkles className="w-3.5 h-3.5" />
                      <span className="hidden sm:inline">Analyze</span>
                    </Link>

                    <button
                      onClick={() => setDeleteTarget(item)}
                      className="p-2 rounded-full text-gray-400 hover:text-red-600 hover:bg-red-50 transition-colors ml-1"
                      title="Delete Resume"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {previewResume && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl max-w-3xl w-full max-h-[85vh] flex flex-col shadow-2xl overflow-hidden animate-in fade-in zoom-in-95">
            <div className="p-5 border-b border-gray-100 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-xl bg-indigo-50 text-indigo-600">
                  <FileText className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-bold text-gray-900 text-base">{previewResume.filename}</h3>
                  <p className="text-xs text-gray-500">{formatFileSize(previewResume.size)}</p>
                </div>
              </div>
              <button
                onClick={() => setPreviewResume(null)}
                className="p-1.5 rounded-full hover:bg-gray-100 text-gray-400 hover:text-gray-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-6">
              {previewLoading ? (
                <div className="h-64 flex items-center justify-center">
                  <div className="w-8 h-8 rounded-full border-4 border-indigo-200 border-t-indigo-600 animate-spin" />
                </div>
              ) : previewResume.mime.includes("pdf") ? (
                <div className="space-y-4">
                  <object
                    data={`/api/resumes/${previewResume.id}/file`}
                    type="application/pdf"
                    className="w-full h-[520px] rounded-2xl border border-gray-200"
                  >
                    <div className="p-6 text-center text-sm text-gray-500">
                      PDF preview not supported by your browser.{" "}
                      <a
                        href={`/api/resumes/${previewResume.id}/file`}
                        target="_blank"
                        rel="noreferrer"
                        className="text-indigo-600 underline font-medium"
                      >
                        Download PDF directly
                      </a>
                    </div>
                  </object>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-gray-500">
                    <FileCheck2 className="w-4 h-4 text-emerald-600" />
                    <span>Extracted Text Content</span>
                  </div>
                  <pre className="p-4 rounded-2xl bg-gray-50 border border-gray-200 text-xs sm:text-sm font-mono text-gray-800 whitespace-pre-wrap leading-relaxed max-h-[500px] overflow-y-auto">
                    {previewText || "No text available"}
                  </pre>
                </div>
              )}
            </div>

            <div className="p-4 border-t border-gray-100 bg-gray-50 flex justify-end gap-3">
              <a
                href={`/api/resumes/${previewResume.id}/file`}
                download={previewResume.filename}
                target="_blank"
                rel="noreferrer"
                className="back-button text-xs py-2 px-4"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Download File</span>
              </a>
              <button
                onClick={() => setPreviewResume(null)}
                className="primary-button text-xs py-2 px-5"
              >
                Close Preview
              </button>
            </div>
          </div>
        </div>
      )}

      {deleteTarget && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl max-w-md w-full p-6 shadow-2xl animate-in fade-in zoom-in-95">
            <div className="w-12 h-12 rounded-full bg-red-50 text-red-600 flex items-center justify-center mb-4">
              <AlertTriangle className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-gray-900 mb-2">Delete Resume?</h3>
            <p className="text-sm text-gray-600 mb-6 leading-relaxed">
              Are you sure you want to delete <span className="font-semibold text-gray-900">{deleteTarget.filename}</span>?
              This will remove the file from storage and delete all associated analyses. This action cannot be undone.
            </p>
            <div className="flex items-center justify-end gap-3">
              <button
                disabled={isDeleting}
                onClick={() => setDeleteTarget(null)}
                className="back-button text-xs py-2 px-4"
              >
                Cancel
              </button>
              <button
                disabled={isDeleting}
                onClick={handleDelete}
                className="px-5 py-2 rounded-full bg-red-600 hover:bg-red-700 text-white font-semibold text-xs transition-colors flex items-center gap-1.5 disabled:opacity-50"
              >
                <Trash2 className="w-3.5 h-3.5" />
                <span>{isDeleting ? "Deleting..." : "Confirm Delete"}</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
