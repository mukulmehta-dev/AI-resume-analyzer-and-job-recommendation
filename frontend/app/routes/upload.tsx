import { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router";
import { useAuthStore } from "../store/auth";
import { api } from "../lib/api";
import { useToast } from "../components/Toast";
import type { Resume } from "../types";
import {
  UploadCloud,
  FileText,
  CheckCircle,
  X,
  AlertCircle,
  Sparkles,
  ArrowRight,
  FileCheck2,
} from "lucide-react";

export default function UploadPage() {
  const { user, initialized } = useAuthStore();
  const navigate = useNavigate();
  const { addToast } = useToast();

  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadedResume, setUploadedResume] = useState<Resume | null>(null);
  const [jobDescription, setJobDescription] = useState("");
  const [uploadProgress, setUploadProgress] = useState<number | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (initialized && !user) {
      navigate("/auth");
    }
  }, [user, initialized, navigate]);

  const validateAndSetFile = (file: File) => {
    setValidationError(null);
    const validExtensions = [".pdf", ".docx"];
    const ext = "." + file.name.split(".").pop()?.toLowerCase();

    if (!validExtensions.includes(ext)) {
      setValidationError("Invalid file type. Please upload a PDF (.pdf) or Word document (.docx).");
      addToast("Only PDF and DOCX documents are accepted.", "error");
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      setValidationError("File is too large. Maximum allowed size is 5MB.");
      addToast("File exceeds 5MB limit.", "error");
      return;
    }

    setSelectedFile(file);
    handleUpload(file);
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const handleUpload = async (file: File) => {
    setIsUploading(true);
    setUploadProgress(0);
    setValidationError(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await api.post<Resume>("/resumes", formData, {
        headers: { "Content-Type": "multipart/form-data" },
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            setUploadProgress(percent);
          }
        },
      });

      setUploadedResume(response.data);
      addToast("Resume uploaded and text extracted successfully!", "success");
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      const message = typeof detail === "string" ? detail : "Failed to upload and parse resume.";
      setValidationError(message);
      addToast(message, "error");
      setSelectedFile(null);
      setUploadedResume(null);
    } finally {
      setIsUploading(false);
      setUploadProgress(null);
    }
  };

  const handleAnalyze = async () => {
    if (!uploadedResume) return;

    try {
      const response = await api.post<{ id: string }>("/analyses", {
        resume_id: uploadedResume.id,
        job_description: jobDescription.trim() || undefined,
      });
      navigate(`/analysis/${response.data.id}`);
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      const message = typeof detail === "string" ? detail : "Failed to initiate analysis.";
      addToast(message, "error");
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  const clearSelected = () => {
    setSelectedFile(null);
    setUploadedResume(null);
    setValidationError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  return (
    <div className="max-w-3xl mx-auto py-8">
      <div className="text-center mb-8">
        <h1 className="page-title text-4xl mb-3">Upload Your Resume</h1>
        <p className="text-gray-600 text-base max-w-xl mx-auto">
          Upload your resume in PDF or DOCX format to extract skills, evaluate structural health, and compute job alignment.
        </p>
      </div>

      <div className="form-div space-y-6">
        <div>
          <label className="block text-sm font-bold text-gray-900 mb-2">
            Resume Document <span className="text-red-500">*</span>
          </label>

          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            onChange={handleFileChange}
            className="hidden"
          />

          {!selectedFile ? (
            <div
              onDragEnter={handleDrag}
              onDragOver={handleDrag}
              onDragLeave={handleDrag}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`uploader-drag-area ${dragActive ? "active ring-2 ring-indigo-500" : ""}`}
            >
              <div className="w-14 h-14 mx-auto rounded-full bg-indigo-50 text-indigo-600 flex items-center justify-center mb-4 shadow-sm">
                <UploadCloud className="w-7 h-7" />
              </div>
              <p className="text-base font-semibold text-gray-900 mb-1">
                Drag and drop your resume here, or{" "}
                <span className="text-indigo-600 underline">browse files</span>
              </p>
              <p className="text-xs text-gray-500">
                PDF or DOCX format (maximum 5MB)
              </p>
            </div>
          ) : (
            <div className="uploader-selected-file">
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-xl bg-indigo-50 text-indigo-600">
                  {uploadedResume ? (
                    <FileCheck2 className="w-6 h-6 text-emerald-600" />
                  ) : (
                    <FileText className="w-6 h-6" />
                  )}
                </div>
                <div>
                  <p className="font-semibold text-gray-900 text-sm">{selectedFile.name}</p>
                  <p className="text-xs text-gray-500">
                    {formatFileSize(selectedFile.size)}
                    {uploadedResume && (
                      <span className="ml-2 text-emerald-600 font-medium">
                        • Extracted & Ready
                      </span>
                    )}
                  </p>
                </div>
              </div>

              {!isUploading && (
                <button
                  type="button"
                  onClick={clearSelected}
                  className="p-1.5 rounded-full hover:bg-gray-100 text-gray-400 hover:text-gray-600 transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>
          )}

          {isUploading && uploadProgress !== null && (
            <div className="mt-4 space-y-1.5">
              <div className="flex justify-between text-xs font-semibold text-gray-600">
                <span>Uploading & parsing document...</span>
                <span>{uploadProgress}%</span>
              </div>
              <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-indigo-500 to-indigo-600 transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
            </div>
          )}

          {validationError && (
            <div className="mt-3 p-3.5 rounded-xl score-badge-red flex items-start gap-2.5 text-xs">
              <AlertCircle className="w-4 h-4 flex-shrink-0 text-red-600 mt-0.5" />
              <span>{validationError}</span>
            </div>
          )}
        </div>

        <div>
          <label className="block text-sm font-bold text-gray-900 mb-1">
            Job Description <span className="text-xs font-normal text-gray-500">(Optional)</span>
          </label>
          <p className="text-xs text-gray-500 mb-2">
            Paste target job requirements to calculate compatibility percentage and identify missing skills.
          </p>
          <textarea
            value={jobDescription}
            onChange={(e) => setJobDescription(e.target.value)}
            rows={5}
            placeholder="Paste role responsibilities, required qualifications, and technical prerequisites..."
            className="form-textarea"
          />
        </div>

        <div className="pt-2 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-xs text-gray-500">
            {uploadedResume
              ? "Document ready for intelligence pipeline."
              : "Upload a document to proceed with analysis."}
          </p>

          <button
            type="button"
            disabled={!uploadedResume || isUploading}
            onClick={handleAnalyze}
            className="primary-button w-full sm:w-auto px-8 py-3.5 text-sm flex items-center justify-center gap-2"
          >
            <Sparkles className="w-4 h-4" />
            <span>Analyze Resume</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
