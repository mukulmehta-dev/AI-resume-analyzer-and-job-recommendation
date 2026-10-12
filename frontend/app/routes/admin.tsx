import { useEffect, useState } from "react";
import { useNavigate } from "react-router";
import { useAuthStore } from "../store/auth";
import { api } from "../lib/api";
import { useToast } from "../components/Toast";
import type { AdminStats, AdminUsersResponse, User, UserRole } from "../types";
import {
  Shield,
  Users,
  FileText,
  Activity,
  AlertTriangle,
  Search,
  CheckCircle2,
  XCircle,
  RotateCcw,
  UserCheck,
  UserX,
  ChevronLeft,
  ChevronRight,
  TrendingUp,
} from "lucide-react";

export default function AdminPage() {
  const { user: currentUser, loading: authLoading, initialized } = useAuthStore();
  const navigate = useNavigate();
  const { addToast } = useToast();

  const [stats, setStats] = useState<AdminStats | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [totalUsers, setTotalUsers] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(10);
  const [search, setSearch] = useState("");
  const [loadingStats, setLoadingStats] = useState(true);
  const [loadingUsers, setLoadingUsers] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);

  const [confirmModal, setConfirmModal] = useState<{
    open: boolean;
    targetUser: User | null;
    actionType: "toggle_active" | "toggle_role";
    newActive?: boolean;
    newRole?: UserRole;
  }>({
    open: false,
    targetUser: null,
    actionType: "toggle_active",
  });

  useEffect(() => {
    if (initialized && !authLoading && (!currentUser || currentUser.role !== "admin")) {
      navigate("/");
    }
  }, [currentUser, authLoading, initialized, navigate]);

  const fetchStats = async () => {
    setLoadingStats(true);
    try {
      const { data } = await api.get<AdminStats>("/admin/stats");
      setStats(data);
    } catch (e: any) {
      addToast(e?.response?.data?.detail ?? "Failed to load admin stats.", "error");
    } finally {
      setLoadingStats(false);
    }
  };

  const fetchUsers = async () => {
    setLoadingUsers(true);
    try {
      const params: Record<string, any> = { page, page_size: pageSize };
      if (search.trim()) {
        params.search = search.trim();
      }
      const { data } = await api.get<AdminUsersResponse>("/admin/users", { params });
      setUsers(data.items);
      setTotalUsers(data.total);
    } catch (e: any) {
      addToast(e?.response?.data?.detail ?? "Failed to load users.", "error");
    } finally {
      setLoadingUsers(false);
    }
  };

  useEffect(() => {
    if (currentUser?.role === "admin") {
      fetchStats();
    }
  }, [currentUser]);

  useEffect(() => {
    if (currentUser?.role === "admin") {
      fetchUsers();
    }
  }, [page, currentUser]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchUsers();
  };

  const executeUserUpdate = async () => {
    if (!confirmModal.targetUser) return;
    setActionLoading(true);
    try {
      const payload: { is_active?: boolean; role?: UserRole } = {};
      if (confirmModal.actionType === "toggle_active") {
        payload.is_active = confirmModal.newActive;
      } else {
        payload.role = confirmModal.newRole;
      }

      await api.patch(`/admin/users/${confirmModal.targetUser.id}`, payload);
      addToast("User updated successfully.", "success");
      setConfirmModal({ open: false, targetUser: null, actionType: "toggle_active" });
      fetchUsers();
      fetchStats();
    } catch (e: any) {
      addToast(e?.response?.data?.detail ?? "Failed to update user.", "error");
    } finally {
      setActionLoading(false);
    }
  };

  if (authLoading || !currentUser || currentUser.role !== "admin") {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <RotateCcw className="w-8 h-8 text-indigo-600 animate-spin" />
      </div>
    );
  }

  const maxDailyCount = Math.max(
    1,
    ...(stats?.analyses_last_7_days.map((d) => d.count) || [1])
  );

  const totalPages = Math.ceil(totalUsers / pageSize) || 1;

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-10">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 flex items-center gap-3">
            <Shield className="w-7 h-7 text-indigo-600" /> System Administration
          </h1>
          <p className="text-xs sm:text-sm text-dark-200 mt-1">
            Global monitoring, user governance, and pipeline diagnostics.
          </p>
        </div>
        <button
          onClick={() => {
            fetchStats();
            fetchUsers();
          }}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-white hover:bg-slate-50 text-slate-700 text-xs font-semibold border border-slate-200 transition-colors shadow-sm self-start sm:self-auto"
        >
          <RotateCcw className={`w-3.5 h-3.5 ${loadingStats || loadingUsers ? "animate-spin" : ""}`} />
          Refresh Data
        </button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <div className="p-6 rounded-2xl bg-white gradient-border border border-slate-200 flex items-center justify-between shadow-sm">
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-dark-200">Total Users</span>
            <div className="text-3xl font-extrabold text-slate-900 mt-2">
              {stats?.users ?? 0}
            </div>
            <span className="text-[11px] text-slate-500 mt-0.5 block">Registered accounts</span>
          </div>
          <div className="w-12 h-12 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center border border-indigo-100">
            <Users className="w-6 h-6" />
          </div>
        </div>

        <div className="p-6 rounded-2xl bg-white gradient-border border border-slate-200 flex items-center justify-between shadow-sm">
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-dark-200">Total Resumes</span>
            <div className="text-3xl font-extrabold text-slate-900 mt-2">
              {stats?.resumes ?? 0}
            </div>
            <span className="text-[11px] text-slate-500 mt-0.5 block">Uploaded documents</span>
          </div>
          <div className="w-12 h-12 rounded-xl bg-sky-50 text-sky-600 flex items-center justify-center border border-sky-100">
            <FileText className="w-6 h-6" />
          </div>
        </div>

        <div className="p-6 rounded-2xl bg-white gradient-border border border-slate-200 flex items-center justify-between shadow-sm">
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-dark-200">Analyses Executed</span>
            <div className="text-3xl font-extrabold text-emerald-700 mt-2">
              {stats?.analyses ?? 0}
            </div>
            <span className="text-[11px] text-slate-500 mt-0.5 block">Pipeline executions</span>
          </div>
          <div className="w-12 h-12 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center border border-emerald-100">
            <Activity className="w-6 h-6" />
          </div>
        </div>

        <div className="p-6 rounded-2xl bg-white gradient-border border border-slate-200 flex items-center justify-between shadow-sm">
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-dark-200">Failed Analyses</span>
            <div className="text-3xl font-extrabold text-rose-700 mt-2">
              {stats?.failed_analyses ?? 0}
            </div>
            <span className="text-[11px] text-slate-500 mt-0.5 block">Exceptions or timeouts</span>
          </div>
          <div className="w-12 h-12 rounded-xl bg-rose-50 text-rose-600 flex items-center justify-center border border-rose-100">
            <AlertTriangle className="w-6 h-6" />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 p-6 rounded-2xl bg-white gradient-border border border-slate-200 space-y-6 shadow-sm">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div>
              <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-indigo-600" /> Analyses Volume (Last 7 Days)
              </h2>
              <p className="text-xs text-dark-200 mt-0.5">Daily completed and processed evaluations</p>
            </div>
          </div>

          <div className="h-48 flex items-end justify-between gap-2 sm:gap-4 pt-6 pb-2 px-2">
            {(stats?.analyses_last_7_days || []).map((day) => {
              const heightPct = Math.round((day.count / maxDailyCount) * 100);
              return (
                <div key={day.date} className="flex-1 flex flex-col items-center gap-2 group h-full justify-end">
                  <span className="text-[11px] font-bold text-indigo-700 opacity-90 group-hover:opacity-100 transition-opacity">
                    {day.count}
                  </span>
                  <div className="w-full max-w-[42px] bg-slate-100 rounded-t-lg overflow-hidden flex items-end h-32">
                    <div
                      className="w-full bg-gradient-to-t from-indigo-600 to-indigo-400 rounded-t-lg transition-all duration-700 ease-out group-hover:from-indigo-500 group-hover:to-indigo-300 shadow-md shadow-indigo-100"
                      style={{ height: `${Math.max(8, heightPct)}%` }}
                    />
                  </div>
                  <span className="text-[10px] font-semibold text-slate-500 group-hover:text-slate-700 transition-colors truncate max-w-full">
                    {day.date.slice(5)}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        <div className="p-6 rounded-2xl bg-white gradient-border border border-slate-200 space-y-4 flex flex-col justify-between shadow-sm">
          <div>
            <div className="flex items-center justify-between border-b border-slate-100 pb-3 mb-4">
              <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-rose-600" /> Recent Failures
              </h2>
            </div>

            <div className="space-y-3 max-h-52 overflow-y-auto pr-1">
              {(!stats?.recent_failures || stats.recent_failures.length === 0) ? (
                <div className="text-center py-8 text-xs text-dark-200 italic">
                  No recent failed analyses recorded.
                </div>
              ) : (
                stats.recent_failures.map((f) => (
                  <div
                    key={f.id}
                    className="p-3 rounded-xl bg-rose-50/60 border border-rose-200 space-y-1 text-xs"
                  >
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="font-semibold text-slate-900 truncate max-w-[140px]">
                        {f.resume_filename ?? "Unknown file"}
                      </span>
                      <span className="text-slate-500 text-[10px]">
                        {new Date(f.created_at).toLocaleDateString()}
                      </span>
                    </div>
                    <p className="text-rose-800 text-[11px] leading-tight line-clamp-2">
                      {f.error ?? "Pipeline execution failed"}
                    </p>
                  </div>
                ))
              )}
            </div>
          </div>
          <div className="pt-2 border-t border-slate-100 text-[11px] text-dark-200">
            Errors reflect parser rejects, timeouts, or unexpected crashes.
          </div>
        </div>
      </div>

      <div className="p-6 rounded-2xl bg-white gradient-border border border-slate-200 space-y-6 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-4">
          <div>
            <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <Users className="w-4 h-4 text-indigo-600" /> User Governance & Access Controls
            </h2>
            <p className="text-xs text-dark-200 mt-0.5">
              Manage account lifecycle, role privileges, and activity status.
            </p>
          </div>

          <form onSubmit={handleSearchSubmit} className="flex items-center gap-2 w-full sm:w-72">
            <div className="relative flex-1">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                placeholder="Search email..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-9 pr-3 py-1.5 rounded-xl bg-white border border-slate-200 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-indigo-600 shadow-sm"
              />
            </div>
            <button
              type="submit"
              className="px-3 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-sm transition-colors"
            >
              Search
            </button>
          </form>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-50 text-[11px] font-bold uppercase tracking-wider text-dark-200">
                <th className="py-3 px-4">User</th>
                <th className="py-3 px-4">Role</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Created</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loadingUsers ? (
                <tr>
                  <td colSpan={5} className="py-8 text-center text-dark-200">
                    Loading accounts...
                  </td>
                </tr>
              ) : users.length === 0 ? (
                <tr>
                  <td colSpan={5} className="py-8 text-center text-dark-200 italic">
                    No users matching criteria.
                  </td>
                </tr>
              ) : (
                users.map((u) => {
                  const isSelf = currentUser?.id === u.id;
                  return (
                    <tr key={u.id} className="hover:bg-slate-50 transition-colors">
                      <td className="py-3 px-4">
                        <div className="font-semibold text-slate-900">{u.name}</div>
                        <div className="text-dark-200 text-[11px]">{u.email}</div>
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider border ${
                            u.role === "admin"
                              ? "bg-purple-50 text-purple-800 border-purple-200"
                              : "bg-slate-100 text-slate-700 border-slate-200"
                          }`}
                        >
                          {u.role === "admin" && <Shield className="w-3 h-3" />}
                          {u.role}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold border ${
                            u.is_active
                              ? "bg-emerald-50 text-emerald-800 border-emerald-200"
                              : "bg-rose-50 text-rose-800 border-rose-200"
                          }`}
                        >
                          {u.is_active ? <CheckCircle2 className="w-3 h-3" /> : <XCircle className="w-3 h-3" />}
                          {u.is_active ? "Active" : "Deactivated"}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-dark-200 text-[11px]">
                        {new Date(u.created_at).toLocaleDateString()}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <div className="inline-flex items-center gap-2">
                          <button
                            disabled={isSelf}
                            onClick={() =>
                              setConfirmModal({
                                open: true,
                                targetUser: u,
                                actionType: "toggle_active",
                                newActive: !u.is_active,
                              })
                            }
                            className={`p-1.5 rounded-lg border text-[11px] font-semibold transition-colors ${
                              isSelf
                                ? "opacity-30 cursor-not-allowed border-slate-200 text-slate-400"
                                : u.is_active
                                ? "bg-rose-50 text-rose-700 border-rose-200 hover:bg-rose-100"
                                : "bg-emerald-50 text-emerald-700 border-emerald-200 hover:bg-emerald-100"
                            }`}
                            title={isSelf ? "Cannot deactivate yourself" : u.is_active ? "Deactivate User" : "Activate User"}
                          >
                            {u.is_active ? <UserX className="w-3.5 h-3.5" /> : <UserCheck className="w-3.5 h-3.5" />}
                          </button>

                          <button
                            disabled={isSelf}
                            onClick={() =>
                              setConfirmModal({
                                open: true,
                                targetUser: u,
                                actionType: "toggle_role",
                                newRole: u.role === "admin" ? "user" : "admin",
                              })
                            }
                            className={`px-2 py-1 rounded-lg border text-[11px] font-semibold transition-colors ${
                              isSelf
                                ? "opacity-30 cursor-not-allowed border-slate-200 text-slate-400"
                                : "bg-white hover:bg-slate-50 border-slate-200 text-slate-700"
                            }`}
                            title={isSelf ? "Cannot demote yourself" : "Change User Role"}
                          >
                            {u.role === "admin" ? "Make User" : "Make Admin"}
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        <div className="flex items-center justify-between text-xs text-dark-200 pt-2">
          <span>
            Showing {users.length} of {totalUsers} accounts
          </span>
          <div className="flex items-center gap-2">
            <button
              disabled={page <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              className="p-1.5 rounded-lg bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="font-semibold text-slate-900 px-2">
              Page {page} of {totalPages}
            </span>
            <button
              disabled={page >= totalPages}
              onClick={() => setPage((p) => p + 1)}
              className="p-1.5 rounded-lg bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {confirmModal.open && confirmModal.targetUser && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="w-full max-w-md p-6 rounded-2xl bg-white border border-slate-200 shadow-2xl space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center">
                <AlertTriangle className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-bold text-slate-900 text-base">Confirm Administrative Action</h3>
                <p className="text-xs text-dark-200">Account status modification</p>
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-xs space-y-1.5">
              <div>
                <span className="text-dark-200 font-medium">Target:</span>{" "}
                <span className="text-slate-900 font-semibold">{confirmModal.targetUser.name}</span> (
                {confirmModal.targetUser.email})
              </div>
              <div>
                <span className="text-dark-200 font-medium">Action:</span>{" "}
                <span className="text-amber-700 font-bold">
                  {confirmModal.actionType === "toggle_active"
                    ? confirmModal.newActive
                      ? "Activate Account"
                      : "Deactivate Account"
                    : `Change Role to ${confirmModal.newRole?.toUpperCase()}`}
                </span>
              </div>
            </div>

            <p className="text-xs text-dark-200 leading-relaxed">
              This action takes effect immediately and will affect the user's ability to sign in or perform actions.
            </p>

            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                disabled={actionLoading}
                onClick={() => setConfirmModal({ open: false, targetUser: null, actionType: "toggle_active" })}
                className="px-4 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold transition-colors"
              >
                Cancel
              </button>
              <button
                disabled={actionLoading}
                onClick={executeUserUpdate}
                className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold transition-colors shadow-md shadow-indigo-100 flex items-center gap-1.5"
              >
                {actionLoading && <RotateCcw className="w-3 h-3 animate-spin" />}
                Confirm Change
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
