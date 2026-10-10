export type UserRole = "user" | "admin";

export interface User {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

export interface Resume {
  id: string;
  user_id: string;
  filename: string;
  mime: string;
  size: number;
  extracted_text?: string;
  created_at: string;
}

export type AnalysisStatus = "pending" | "done" | "failed";

export interface RecommendationItem {
  title: string;
  detail: string;
  priority: "high" | "medium" | "low";
}

export interface SkillWithCategory {
  name: string;
  category: string;
}

export interface SectionSubScore {
  score: number;
  weight: number;
  explanation: string;
}

export interface Analysis {
  id: string;
  user_id: string;
  resume_id: string;
  resume_filename?: string | null;
  job_description: string | null;
  resume_score: number;
  compatibility_score: number | null;
  detected_skills: string[];
  detected_skills_with_category?: SkillWithCategory[];
  matching_skills: string[];
  missing_skills: string[];
  sections: Record<string, boolean | SectionSubScore>;
  strengths: string[];
  weaknesses: string[];
  recommendations: RecommendationItem[];
  summary_feedback: string | null;
  ai_unavailable: boolean;
  status: AnalysisStatus;
  error: string | null;
  created_at: string;
}

export interface AnalysisListResponse {
  items: Analysis[];
  total: number;
  page: number;
  page_size: number;
}

export interface PaginatedResumes {
  items: Resume[];
  total: number;
}

export interface AdminStats {
  users: number;
  resumes: number;
  analyses: number;
  failed_analyses: number;
  analyses_last_7_days: { date: string; count: number }[];
  recent_failures: {
    id: string;
    resume_id: string;
    resume_filename?: string | null;
    error: string | null;
    created_at: string;
  }[];
}

export interface AdminUsersResponse {
  items: User[];
  total: number;
  page: number;
  page_size: number;
}
