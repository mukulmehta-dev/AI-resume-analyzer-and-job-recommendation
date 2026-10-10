import { Link } from "react-router";
import { BookOpen, Shield, Cpu, HelpCircle, ArrowRight } from "lucide-react";

export default function HelpPage() {
  return (
    <div className="max-w-4xl mx-auto py-8">
      <div className="mb-8">
        <h1 className="page-title text-4xl mb-3">User Documentation & SRS 2.6 Guide</h1>
        <p className="text-gray-600 text-lg">
          Complete guide to analyzing resumes, understanding scores, and leveraging AI recommendations.
        </p>
      </div>

      <div className="grid gap-6">
        <div className="form-div">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2.5 rounded-full bg-blue-50 text-blue-600">
              <BookOpen className="w-5 h-5" />
            </div>
            <h2 className="text-xl font-bold text-gray-900">1. Resume Analysis Process</h2>
          </div>
          <div className="space-y-3 text-sm text-gray-600 leading-relaxed">
            <p>
              Upload resumes in PDF or DOCX format (maximum 5MB). The system automatically parses textual
              structure, identifies canonical sections (Education, Experience, Projects, Certifications, and Skills),
              and cross-references detected capabilities against a dictionary of over 300 technical and soft skills.
            </p>
            <p>
              The composite resume score (0-100) measures balanced resume strength using predefined weighting:
              Skills (35%), Experience (20%), Education (15%), Projects (15%), Certifications (5%), and Document Structure (10%).
            </p>
          </div>
        </div>

        <div className="form-div">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2.5 rounded-full bg-purple-50 text-purple-600">
              <Cpu className="w-5 h-5" />
            </div>
            <h2 className="text-xl font-bold text-gray-900">2. Job Description Compatibility</h2>
          </div>
          <div className="space-y-3 text-sm text-gray-600 leading-relaxed">
            <p>
              When an optional target Job Description is provided, the engine computes a 0-100 compatibility score
              combining direct skill keyword overlap (60%) and semantic contextual similarity (40%).
            </p>
            <p>
              The breakdown displays detected matching skills in green and missing target skills in red to help candidates
              tailor their applications effectively.
            </p>
          </div>
        </div>

        <div className="form-div">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2.5 rounded-full bg-amber-50 text-amber-600">
              <Shield className="w-5 h-5" />
            </div>
            <h2 className="text-xl font-bold text-gray-900">3. Advisory Notice & Ethical AI</h2>
          </div>
          <div className="space-y-3 text-sm text-gray-600 leading-relaxed">
            <p className="font-semibold text-gray-800">
              All AI outputs and scoring recommendations are strictly advisory in nature.
            </p>
            <p>
              ResumeAI never presents automated output as definitive hiring or employment decisions. Recommendations
              highlight formatting gaps, phrasing opportunities, and key competencies to guide self-improvement.
            </p>
          </div>
        </div>

        <div className="text-center pt-4">
          <Link to="/upload" className="primary-button text-base px-8 py-3.5">
            <span>Start Resume Analysis</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </div>
    </div>
  );
}
