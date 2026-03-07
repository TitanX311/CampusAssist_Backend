"use client";

import { useEffect, useState, useCallback } from "react";
import {
  adminGetStats,
  adminListUsers,
  adminUpdateUserType,
  adminUpdateUserActive,
  adminListColleges,
  adminDeleteCollege,
  adminListCommunities,
  adminDeleteCommunity,
  adminListPosts,
  adminDeletePost,
  adminListComments,
  adminDeleteComment,
  AdminStats,
  AdminUser,
  College,
  Community,
  Post,
  Comment,
  PagedResponse,
  PostListResponse,
  UserType,
} from "@/lib/api";
import {
  Users,
  Building2,
  BookOpen,
  FileText,
  MessageSquare,
  Paperclip,
  Loader2,
  AlertCircle,
  RefreshCw,
  Trash2,
  ChevronLeft,
  ChevronRight,
  ToggleLeft,
  ToggleRight,
  ShieldCheck,
} from "lucide-react";

type Tab = "users" | "colleges" | "communities" | "posts" | "comments";

// ── Stat Card ─────────────────────────────────────────────────────────────────

function StatCard({
  label,
  value,
  icon,
  color,
}: {
  label: string;
  value: number;
  icon: React.ReactNode;
  color: string;
}) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 flex items-center gap-4">
      <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${color}`}>
        {icon}
      </div>
      <div>
        <p className="text-2xl font-bold text-slate-900">
          {value < 0 ? <span className="text-red-400 text-lg">err</span> : value.toLocaleString()}
        </p>
        <p className="text-xs text-slate-500 mt-0.5">{label}</p>
      </div>
    </div>
  );
}

// ── Pagination bar ────────────────────────────────────────────────────────────

function Pagination({
  page,
  totalPages,
  total,
  onPrev,
  onNext,
}: {
  page: number;
  totalPages: number;
  total: number;
  onPrev: () => void;
  onNext: () => void;
}) {
  if (totalPages <= 1) return null;
  return (
    <div className="flex items-center justify-between mt-4 text-sm text-slate-600">
      <p className="text-xs text-slate-400">
        Page {page} of {totalPages} · {total} total
      </p>
      <div className="flex gap-2">
        <button
          onClick={onPrev}
          disabled={page === 1}
          className="flex items-center gap-1 px-3 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 disabled:opacity-40 transition"
        >
          <ChevronLeft size={14} /> Prev
        </button>
        <button
          onClick={onNext}
          disabled={page === totalPages}
          className="flex items-center gap-1 px-3 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 disabled:opacity-40 transition"
        >
          Next <ChevronRight size={14} />
        </button>
      </div>
    </div>
  );
}

// ── Users tab ─────────────────────────────────────────────────────────────────

function UsersTab() {
  const PAGE_SIZE = 20;
  const [data, setData] = useState<PagedResponse<AdminUser> | null>(null);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [inputSearch, setInputSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [actionId, setActionId] = useState<string | null>(null);

  const fetchUsers = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const r = await adminListUsers(page, PAGE_SIZE, search ? { search } : {});
      setData(r);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load users");
    } finally {
      setLoading(false);
    }
  }, [page, search]);

  useEffect(() => { fetchUsers(); }, [fetchUsers]);

  async function toggleActive(user: AdminUser) {
    setActionId(user.id);
    try {
      await adminUpdateUserActive(user.id, !user.is_active);
      await fetchUsers();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Action failed");
    } finally {
      setActionId(null);
    }
  }

  async function changeType(user: AdminUser, type: UserType) {
    setActionId(user.id + "_type");
    try {
      await adminUpdateUserType(user.id, type);
      await fetchUsers();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Action failed");
    } finally {
      setActionId(null);
    }
  }

  const totalPages = data ? Math.max(1, Math.ceil(data.total / PAGE_SIZE)) : 1;

  return (
    <div>
      {/* Search */}
      <form
        onSubmit={(e) => { e.preventDefault(); setPage(1); setSearch(inputSearch); }}
        className="flex gap-2 mb-4"
      >
        <input
          value={inputSearch}
          onChange={(e) => setInputSearch(e.target.value)}
          placeholder="Search by name or email…"
          className="flex-1 px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          type="submit"
          className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition"
        >
          Search
        </button>
        {search && (
          <button
            type="button"
            onClick={() => { setInputSearch(""); setSearch(""); setPage(1); }}
            className="px-4 py-2 bg-slate-100 text-slate-600 text-sm rounded-lg hover:bg-slate-200 transition"
          >
            Clear
          </button>
        )}
      </form>

      {error && (
        <div className="flex items-center gap-2 bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 mb-4 text-sm">
          <AlertCircle size={15} /> {error}
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center h-40">
          <Loader2 size={24} className="animate-spin text-blue-500" />
        </div>
      ) : !data || data.items.length === 0 ? (
        <div className="text-center py-16 text-slate-400">No users found.</div>
      ) : (
        <>
          <div className="bg-white rounded-xl border border-slate-200 overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-100 text-left text-xs text-slate-500 font-medium">
                  <th className="px-4 py-3">User</th>
                  <th className="px-4 py-3">Type</th>
                  <th className="px-4 py-3">Active</th>
                  <th className="px-4 py-3">Verified</th>
                  <th className="px-4 py-3">Joined</th>
                  <th className="px-4 py-3">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {data.items.map((u) => (
                  <tr key={u.id} className="hover:bg-slate-50 transition">
                    <td className="px-4 py-3">
                      <p className="font-medium text-slate-800 truncate max-w-[180px]">{u.name ?? "—"}</p>
                      <p className="text-xs text-slate-500 truncate max-w-[180px]">{u.email}</p>
                    </td>
                    <td className="px-4 py-3">
                      <select
                        value={u.type}
                        disabled={actionId === u.id + "_type"}
                        onChange={(e) => changeType(u, e.target.value as UserType)}
                        className="text-xs border border-slate-200 rounded-md px-2 py-1 focus:outline-none focus:ring-1 focus:ring-blue-400"
                      >
                        <option value="USER">USER</option>
                        <option value="COLLEGE">COLLEGE</option>
                        <option value="SUPER_ADMIN">SUPER_ADMIN</option>
                      </select>
                    </td>
                    <td className="px-4 py-3">
                      <button
                        onClick={() => toggleActive(u)}
                        disabled={actionId === u.id}
                        title={u.is_active ? "Deactivate" : "Activate"}
                        className="disabled:opacity-50"
                      >
                        {actionId === u.id ? (
                          <Loader2 size={16} className="animate-spin text-slate-400" />
                        ) : u.is_active ? (
                          <ToggleRight size={20} className="text-emerald-500" />
                        ) : (
                          <ToggleLeft size={20} className="text-slate-300" />
                        )}
                      </button>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${u.email_verified ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-slate-500"}`}>
                        {u.email_verified ? "yes" : "no"}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-xs text-slate-500">
                      {new Date(u.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-xs text-slate-400 font-mono">{u.id.slice(0, 8)}…</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pagination
            page={page}
            totalPages={totalPages}
            total={data.total}
            onPrev={() => setPage((p) => p - 1)}
            onNext={() => setPage((p) => p + 1)}
          />
        </>
      )}
    </div>
  );
}

// ── Colleges tab ──────────────────────────────────────────────────────────────

function CollegesTab() {
  const PAGE_SIZE = 20;
  const [data, setData] = useState<{ items: College[]; total: number } | null>(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const fetchColleges = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const r = await adminListColleges(page, PAGE_SIZE);
      setData(r);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load colleges");
    } finally {
      setLoading(false);
    }
  }, [page]);

  useEffect(() => { fetchColleges(); }, [fetchColleges]);

  async function handleDelete(id: string, name: string) {
    if (!confirm(`Delete "${name}"? This cannot be undone.`)) return;
    setDeletingId(id);
    try {
      await adminDeleteCollege(id);
      await fetchColleges();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Delete failed");
    } finally {
      setDeletingId(null);
    }
  }

  const totalPages = data ? Math.max(1, Math.ceil(data.total / PAGE_SIZE)) : 1;

  return (
    <div>
      {error && (
        <div className="flex items-center gap-2 bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 mb-4 text-sm">
          <AlertCircle size={15} /> {error}
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center h-40">
          <Loader2 size={24} className="animate-spin text-blue-500" />
        </div>
      ) : !data || data.items.length === 0 ? (
        <div className="text-center py-16 text-slate-400">No colleges found.</div>
      ) : (
        <>
          <div className="bg-white rounded-xl border border-slate-200 divide-y divide-slate-100">
            {data.items.map((c) => (
              <div key={c.id} className="flex items-center gap-3 px-4 py-3.5">
                <div className="w-9 h-9 rounded-xl bg-blue-50 flex items-center justify-center text-blue-600 shrink-0">
                  <Building2 size={16} />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-slate-800 truncate">{c.name}</p>
                  <p className="text-xs text-slate-500 truncate">{c.contact_email}</p>
                </div>
                <div className="text-xs text-slate-400 shrink-0 text-right hidden sm:block">
                  <p>{c.communities.length} communities</p>
                  <p>{c.admin_users.length} admins</p>
                </div>
                <button
                  onClick={() => handleDelete(c.id, c.name)}
                  disabled={deletingId === c.id}
                  className="p-1.5 rounded-lg text-slate-400 hover:text-red-600 hover:bg-red-50 transition disabled:opacity-50"
                  title="Delete college"
                >
                  {deletingId === c.id ? (
                    <Loader2 size={14} className="animate-spin" />
                  ) : (
                    <Trash2 size={14} />
                  )}
                </button>
              </div>
            ))}
          </div>
          <Pagination
            page={page}
            totalPages={totalPages}
            total={data.total}
            onPrev={() => setPage((p) => p - 1)}
            onNext={() => setPage((p) => p + 1)}
          />
        </>
      )}
    </div>
  );
}

// ── Communities tab ───────────────────────────────────────────────────────────

function CommunitiesTab() {
  const PAGE_SIZE = 20;
  const [data, setData] = useState<{ items: Community[]; total: number } | null>(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const fetchCommunities = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const r = await adminListCommunities(page, PAGE_SIZE);
      setData(r);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load communities");
    } finally {
      setLoading(false);
    }
  }, [page]);

  useEffect(() => { fetchCommunities(); }, [fetchCommunities]);

  async function handleDelete(id: string, name: string) {
    if (!confirm(`Delete "${name}"? This cannot be undone.`)) return;
    setDeletingId(id);
    try {
      await adminDeleteCommunity(id);
      await fetchCommunities();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Delete failed");
    } finally {
      setDeletingId(null);
    }
  }

  const totalPages = data ? Math.max(1, Math.ceil(data.total / PAGE_SIZE)) : 1;

  return (
    <div>
      {error && (
        <div className="flex items-center gap-2 bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 mb-4 text-sm">
          <AlertCircle size={15} /> {error}
        </div>
      )}
      {loading ? (
        <div className="flex items-center justify-center h-40">
          <Loader2 size={24} className="animate-spin text-blue-500" />
        </div>
      ) : !data || data.items.length === 0 ? (
        <div className="text-center py-16 text-slate-400">No communities found.</div>
      ) : (
        <>
          <div className="bg-white rounded-xl border border-slate-200 divide-y divide-slate-100">
            {data.items.map((c) => (
              <div key={c.id} className="flex items-center gap-3 px-4 py-3.5">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-slate-800 truncate">{c.name}</p>
                  <div className="flex items-center gap-2 mt-0.5">
                    <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${c.type === "PUBLIC" ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-700"}`}>
                      {c.type}
                    </span>
                    <span className="text-xs text-slate-400">{c.member_users.length} members</span>
                  </div>
                </div>
                <button
                  onClick={() => handleDelete(c.id, c.name)}
                  disabled={deletingId === c.id}
                  className="p-1.5 rounded-lg text-slate-400 hover:text-red-600 hover:bg-red-50 transition disabled:opacity-50"
                  title="Delete community"
                >
                  {deletingId === c.id ? (
                    <Loader2 size={14} className="animate-spin" />
                  ) : (
                    <Trash2 size={14} />
                  )}
                </button>
              </div>
            ))}
          </div>
          <Pagination
            page={page}
            totalPages={totalPages}
            total={data.total}
            onPrev={() => setPage((p) => p - 1)}
            onNext={() => setPage((p) => p + 1)}
          />
        </>
      )}
    </div>
  );
}

// ── Posts tab ─────────────────────────────────────────────────────────────────

function PostsTab() {
  const PAGE_SIZE = 20;
  const [data, setData] = useState<PostListResponse | null>(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const fetchPosts = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const r = await adminListPosts(page, PAGE_SIZE);
      setData(r);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load posts");
    } finally {
      setLoading(false);
    }
  }, [page]);

  useEffect(() => { fetchPosts(); }, [fetchPosts]);

  async function handleDelete(id: string) {
    if (!confirm("Delete this post? This cannot be undone.")) return;
    setDeletingId(id);
    try {
      await adminDeletePost(id);
      await fetchPosts();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Delete failed");
    } finally {
      setDeletingId(null);
    }
  }

  const totalPages = data ? Math.max(1, Math.ceil(data.total / PAGE_SIZE)) : 1;

  return (
    <div>
      {error && (
        <div className="flex items-center gap-2 bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 mb-4 text-sm">
          <AlertCircle size={15} /> {error}
        </div>
      )}
      {loading ? (
        <div className="flex items-center justify-center h-40">
          <Loader2 size={24} className="animate-spin text-blue-500" />
        </div>
      ) : !data || data.items.length === 0 ? (
        <div className="text-center py-16 text-slate-400">No posts found.</div>
      ) : (
        <>
          <div className="bg-white rounded-xl border border-slate-200 divide-y divide-slate-100">
            {data.items.map((p: Post) => (
              <div key={p.id} className="flex items-start gap-3 px-4 py-3.5">
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-slate-800 line-clamp-2">{p.content}</p>
                  <div className="flex items-center gap-3 mt-1 text-xs text-slate-400">
                    <span className="font-mono truncate max-w-[120px]">{p.user_id.slice(0, 8)}…</span>
                    <span>{new Date(p.created_at).toLocaleDateString()}</span>
                    <span>{p.likes} likes</span>
                    <span>{p.comments.length} comments</span>
                  </div>
                </div>
                <button
                  onClick={() => handleDelete(p.id)}
                  disabled={deletingId === p.id}
                  className="p-1.5 rounded-lg text-slate-400 hover:text-red-600 hover:bg-red-50 transition disabled:opacity-50 shrink-0"
                  title="Delete post"
                >
                  {deletingId === p.id ? (
                    <Loader2 size={14} className="animate-spin" />
                  ) : (
                    <Trash2 size={14} />
                  )}
                </button>
              </div>
            ))}
          </div>
          <Pagination
            page={page}
            totalPages={totalPages}
            total={data.total}
            onPrev={() => setPage((p) => p - 1)}
            onNext={() => setPage((p) => p + 1)}
          />
        </>
      )}
    </div>
  );
}

// ── Comments tab ──────────────────────────────────────────────────────────────

function CommentsTab() {
  const PAGE_SIZE = 20;
  const [data, setData] = useState<{ items: Comment[]; total: number } | null>(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const fetchComments = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const r = await adminListComments(page, PAGE_SIZE);
      setData(r);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load comments");
    } finally {
      setLoading(false);
    }
  }, [page]);

  useEffect(() => { fetchComments(); }, [fetchComments]);

  async function handleDelete(id: string) {
    if (!confirm("Delete this comment? This cannot be undone.")) return;
    setDeletingId(id);
    try {
      await adminDeleteComment(id);
      await fetchComments();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Delete failed");
    } finally {
      setDeletingId(null);
    }
  }

  const totalPages = data ? Math.max(1, Math.ceil(data.total / PAGE_SIZE)) : 1;

  return (
    <div>
      {error && (
        <div className="flex items-center gap-2 bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 mb-4 text-sm">
          <AlertCircle size={15} /> {error}
        </div>
      )}
      {loading ? (
        <div className="flex items-center justify-center h-40">
          <Loader2 size={24} className="animate-spin text-blue-500" />
        </div>
      ) : !data || data.items.length === 0 ? (
        <div className="text-center py-16 text-slate-400">No comments found.</div>
      ) : (
        <>
          <div className="bg-white rounded-xl border border-slate-200 divide-y divide-slate-100">
            {data.items.map((c: Comment) => (
              <div key={c.id} className="flex items-start gap-3 px-4 py-3.5">
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-slate-800 line-clamp-2">{c.content}</p>
                  <div className="flex items-center gap-3 mt-1 text-xs text-slate-400">
                    <span className="font-mono truncate max-w-[120px]">{c.user_id.slice(0, 8)}…</span>
                    <span>{new Date(c.created_at).toLocaleDateString()}</span>
                    <span className="font-mono text-slate-300 truncate max-w-[100px]">post:{c.post_id.slice(0, 6)}…</span>
                  </div>
                </div>
                <button
                  onClick={() => handleDelete(c.id)}
                  disabled={deletingId === c.id}
                  className="p-1.5 rounded-lg text-slate-400 hover:text-red-600 hover:bg-red-50 transition disabled:opacity-50 shrink-0"
                  title="Delete comment"
                >
                  {deletingId === c.id ? (
                    <Loader2 size={14} className="animate-spin" />
                  ) : (
                    <Trash2 size={14} />
                  )}
                </button>
              </div>
            ))}
          </div>
          <Pagination
            page={page}
            totalPages={totalPages}
            total={data.total}
            onPrev={() => setPage((p) => p - 1)}
            onNext={() => setPage((p) => p + 1)}
          />
        </>
      )}
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function AdminPage() {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [statsLoading, setStatsLoading] = useState(true);
  const [statsError, setStatsError] = useState("");
  const [tab, setTab] = useState<Tab>("users");

  const fetchStats = useCallback(async () => {
    setStatsLoading(true);
    setStatsError("");
    try {
      setStats(await adminGetStats());
    } catch (e: unknown) {
      setStatsError(e instanceof Error ? e.message : "Failed to load stats");
    } finally {
      setStatsLoading(false);
    }
  }, []);

  useEffect(() => { fetchStats(); }, [fetchStats]);

  const tabs: { id: Tab; label: string; icon: React.ReactNode }[] = [
    { id: "users",       label: "Users",       icon: <Users size={15} /> },
    { id: "colleges",    label: "Colleges",    icon: <Building2 size={15} /> },
    { id: "communities", label: "Communities", icon: <BookOpen size={15} /> },
    { id: "posts",       label: "Posts",       icon: <FileText size={15} /> },
    { id: "comments",    label: "Comments",    icon: <MessageSquare size={15} /> },
  ];

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
            <ShieldCheck size={22} className="text-purple-600" />
            Super Admin
          </h1>
          <p className="text-slate-500 text-sm mt-1">Platform-wide management dashboard.</p>
        </div>
        <button
          onClick={fetchStats}
          disabled={statsLoading}
          className="flex items-center gap-1.5 text-sm text-slate-500 hover:text-blue-600 px-3 py-1.5 rounded-lg hover:bg-blue-50 transition disabled:opacity-50"
        >
          <RefreshCw size={14} className={statsLoading ? "animate-spin" : ""} />
          Refresh
        </button>
      </div>

      {/* Stats cards */}
      {statsError && (
        <div className="flex items-center gap-2 bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 mb-4 text-sm">
          <AlertCircle size={15} /> {statsError}
        </div>
      )}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 mb-8">
        {statsLoading ? (
          Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="bg-white rounded-xl border border-slate-200 p-5 h-20 animate-pulse" />
          ))
        ) : stats ? (
          <>
            <StatCard label="Users"       value={stats.users}       icon={<Users size={18} />}         color="bg-blue-50 text-blue-600" />
            <StatCard label="Colleges"    value={stats.colleges}    icon={<Building2 size={18} />}     color="bg-indigo-50 text-indigo-600" />
            <StatCard label="Communities" value={stats.communities} icon={<BookOpen size={18} />}      color="bg-emerald-50 text-emerald-600" />
            <StatCard label="Posts"       value={stats.posts}       icon={<FileText size={18} />}      color="bg-violet-50 text-violet-600" />
            <StatCard label="Comments"    value={stats.comments}    icon={<MessageSquare size={18} />} color="bg-amber-50 text-amber-600" />
            <StatCard label="Attachments" value={stats.attachments} icon={<Paperclip size={18} />}    color="bg-rose-50 text-rose-600" />
          </>
        ) : null}
      </div>

      {/* Tabs */}
      <div className="border-b border-slate-200 mb-6">
        <div className="flex gap-0 -mb-px overflow-x-auto">
          {tabs.map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`flex items-center gap-1.5 px-4 py-3 text-sm font-medium border-b-2 transition whitespace-nowrap ${
                tab === t.id
                  ? "border-blue-600 text-blue-600"
                  : "border-transparent text-slate-500 hover:text-slate-700"
              }`}
            >
              {t.icon}
              {t.label}
            </button>
          ))}
        </div>
      </div>

      {tab === "users"       && <UsersTab />}
      {tab === "colleges"    && <CollegesTab />}
      {tab === "communities" && <CommunitiesTab />}
      {tab === "posts"       && <PostsTab />}
      {tab === "comments"    && <CommentsTab />}
    </div>
  );
}
