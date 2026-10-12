import { useState } from "react";
import { useNavigate } from "react-router";
import { api } from "../lib/api";
import { useAuthStore } from "../store/auth";
import type { User } from "../types";
import { Lock, Mail, User as UserIcon, ArrowRight, AlertCircle, CheckCircle } from "lucide-react";

export default function AuthPage() {
  const [tab, setTab] = useState<"login" | "register">("login");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [serverError, setServerError] = useState("");
  const [loading, setLoading] = useState(false);
  const [successMessage, setSuccessMessage] = useState("");

  const { setUser } = useAuthStore();
  const navigate = useNavigate();

  const validate = () => {
    const errs: Record<string, string> = {};
    if (tab === "register") {
      if (!name.trim()) {
        errs.name = "Full name is required";
      } else if (name.trim().length < 2) {
        errs.name = "Name must be at least 2 characters";
      }
    }

    if (!email.trim()) {
      errs.email = "Email address is required";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) {
      errs.email = "Enter a valid email address";
    }

    if (!password) {
      errs.password = "Password is required";
    } else if (password.length < 6) {
      errs.password = "Password must be at least 6 characters";
    }

    if (tab === "register" && password !== confirmPassword) {
      errs.confirmPassword = "Passwords do not match";
    }

    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setServerError("");
    setSuccessMessage("");

    if (!validate()) return;

    setLoading(true);
    try {
      if (tab === "login") {
        const res = await api.post<User>("/auth/login", {
          email: email.trim().toLowerCase(),
          password,
        });
        setUser(res.data);
        navigate("/");
      } else {
        const res = await api.post<User>("/auth/register", {
          name: name.trim(),
          email: email.trim().toLowerCase(),
          password,
        });
        setUser(res.data);
        setSuccessMessage("Account created successfully!");
        setTimeout(() => {
          navigate("/");
        }, 500);
      }
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      if (typeof detail === "string") {
        setServerError(detail);
      } else if (Array.isArray(detail)) {
        setServerError(detail.map((d: any) => d.msg).join(", "));
      } else {
        setServerError("Authentication failed. Please check your credentials.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-gradient text-4xl sm:text-5xl font-extrabold tracking-tight">
            ResumeAI
          </h1>
          <p className="mt-2 text-sm text-gray-600 font-medium">
            AI-powered resume analysis and job fit intelligence
          </p>
        </div>

        <div className="form-div shadow-xl">
          <div className="flex rounded-full bg-gray-100 p-1 mb-8">
            <button
              type="button"
              onClick={() => {
                setTab("login");
                setErrors({});
                setServerError("");
              }}
              className={`flex-1 py-2 text-sm font-semibold rounded-full transition-all ${
                tab === "login"
                  ? "bg-white text-gray-900 shadow-sm"
                  : "text-gray-700 hover:text-gray-900"
              }`}
            >
              Sign In
            </button>
            <button
              type="button"
              onClick={() => {
                setTab("register");
                setErrors({});
                setServerError("");
              }}
              className={`flex-1 py-2 text-sm font-semibold rounded-full transition-all ${
                tab === "register"
                  ? "bg-white text-gray-900 shadow-sm"
                  : "text-gray-700 hover:text-gray-900"
              }`}
            >
              Register
            </button>
          </div>

          {serverError && (
            <div className="mb-6 p-4 rounded-2xl score-badge-red flex items-start gap-2.5 text-sm">
              <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5 text-red-600" />
              <span>{serverError}</span>
            </div>
          )}

          {successMessage && (
            <div className="mb-6 p-4 rounded-2xl score-badge-green flex items-start gap-2.5 text-sm">
              <CheckCircle className="w-5 h-5 flex-shrink-0 mt-0.5 text-green-600" />
              <span>{successMessage}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {tab === "register" && (
              <div>
                <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1.5">
                  Full Name
                </label>
                <div className="relative">
                  <UserIcon className="w-5 h-5 absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" />
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Jane Doe"
                    className="form-input pl-11"
                  />
                </div>
                {errors.name && (
                  <p className="mt-1 text-xs text-red-600 font-medium">{errors.name}</p>
                )}
              </div>
            )}

            <div>
              <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1.5">
                Email Address
              </label>
              <div className="relative">
                <Mail className="w-5 h-5 absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="jane@example.com"
                  className="form-input pl-11"
                />
              </div>
              {errors.email && (
                <p className="mt-1 text-xs text-red-600 font-medium">{errors.email}</p>
              )}
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1.5">
                Password
              </label>
              <div className="relative">
                <Lock className="w-5 h-5 absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="form-input pl-11"
                />
              </div>
              {errors.password && (
                <p className="mt-1 text-xs text-red-600 font-medium">{errors.password}</p>
              )}
            </div>

            {tab === "register" && (
              <div>
                <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1.5">
                  Confirm Password
                </label>
                <div className="relative">
                  <Lock className="w-5 h-5 absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" />
                  <input
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="••••••••"
                    className="form-input pl-11"
                  />
                </div>
                {errors.confirmPassword && (
                  <p className="mt-1 text-xs text-red-600 font-medium">{errors.confirmPassword}</p>
                )}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="primary-button w-full mt-6 py-3.5 text-base flex justify-center items-center gap-2"
            >
              <span>{loading ? "Processing..." : tab === "login" ? "Sign In" : "Create Account"}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
