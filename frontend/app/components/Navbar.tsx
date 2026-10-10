import { Link, useNavigate, useLocation } from "react-router";
import { useAuthStore } from "../store/auth";
import { Sparkles, FileText, History, Shield, LogOut, LogIn, HelpCircle, FolderGit2 } from "lucide-react";

export function Navbar() {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = async () => {
    await logout();
    navigate("/auth");
  };

  const isActive = (path: string) => location.pathname === path;

  return (
    <header className="sticky top-4 z-50 px-4 mb-8">
      <nav className="navbar px-6 py-3 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2 font-bold text-xl tracking-tight text-gray-900">
          <div className="w-9 h-9 rounded-full primary-gradient flex items-center justify-center shadow-sm">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <span className="text-gradient font-extrabold tracking-tight">ResumeAI</span>
        </Link>

        <div className="hidden md:flex items-center gap-1 font-medium text-sm text-gray-600">
          <Link
            to="/"
            className={`px-4 py-2 rounded-full transition-colors ${
              isActive("/") ? "bg-gray-100 text-gray-900 font-semibold" : "hover:text-gray-900 hover:bg-gray-50"
            }`}
          >
            Dashboard
          </Link>
          <Link
            to="/upload"
            className={`px-4 py-2 rounded-full transition-colors flex items-center gap-1.5 ${
              isActive("/upload") ? "bg-gray-100 text-gray-900 font-semibold" : "hover:text-gray-900 hover:bg-gray-50"
            }`}
          >
            <FileText className="w-4 h-4" />
            Upload
          </Link>
          <Link
            to="/resumes"
            className={`px-4 py-2 rounded-full transition-colors flex items-center gap-1.5 ${
              isActive("/resumes") ? "bg-gray-100 text-gray-900 font-semibold" : "hover:text-gray-900 hover:bg-gray-50"
            }`}
          >
            <FolderGit2 className="w-4 h-4" />
            Resumes
          </Link>
          <Link
            to="/history"
            className={`px-4 py-2 rounded-full transition-colors flex items-center gap-1.5 ${
              isActive("/history") ? "bg-gray-100 text-gray-900 font-semibold" : "hover:text-gray-900 hover:bg-gray-50"
            }`}
          >
            <History className="w-4 h-4" />
            History
          </Link>
          {user?.role === "admin" && (
            <Link
              to="/admin"
              className={`px-4 py-2 rounded-full transition-colors flex items-center gap-1.5 ${
                isActive("/admin") ? "bg-purple-100 text-purple-900 font-semibold" : "text-purple-700 hover:bg-purple-50"
              }`}
            >
              <Shield className="w-4 h-4" />
              Admin
            </Link>
          )}
          <Link
            to="/help"
            className={`px-3 py-2 rounded-full transition-colors flex items-center gap-1 text-gray-500 ${
              isActive("/help") ? "bg-gray-100 text-gray-900" : "hover:text-gray-900 hover:bg-gray-50"
            }`}
            title="Help & Documentation"
          >
            <HelpCircle className="w-4 h-4" />
          </Link>
        </div>

        <div className="flex items-center gap-3">
          {user ? (
            <div className="flex items-center gap-3">
              <span className="hidden sm:inline-block text-xs font-semibold px-2.5 py-1 rounded-full bg-blue-50 text-blue-700 border border-blue-200">
                {user.name} ({user.role})
              </span>
              <button
                onClick={handleLogout}
                className="back-button text-xs py-1.5 px-3 hover:text-red-600 hover:border-red-200"
                title="Logout"
              >
                <LogOut className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">Logout</span>
              </button>
            </div>
          ) : (
            <Link to="/auth" className="primary-button text-sm py-2 px-5">
              <LogIn className="w-4 h-4" />
              Sign In
            </Link>
          )}
        </div>
      </nav>
    </header>
  );
}
