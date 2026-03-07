"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import {
  AdminStats,
  AdminUser,
  College,
  Community,
  Post,
  Comment,
  PagedResponse,
  PostListResponse,
  CommentListResponse,
  UserType,
  adminGetStats,
  adminListUsers,
  adminUpdateUserType,
  adminUpdateUserActive,
  adminListColleges,
  adminCreateCollege,
  adminDeleteCollege,
  adminListCommunities,
  adminDeleteCommunity,
  adminListPosts,
  adminDeletePost,
  adminListComments,
  adminDeleteComment,
} from "@/lib/api";
import {
  Users,
  Building2,
  Network,
  FileText,
  MessageSquare,
  Paperclip,
  Loader2,
  AlertCircle,
  ShieldCheck,
  Trash2,
  ChevronLeft,
  ChevronRight,
  Search,
  Plus,
  X,
  Check,
  ToggleLeft,
  ToggleRight,
  Globe,
  Lock,
} from "lucide-react";

type Tab = "users" | "colleges" | "communities" | "posts" | "comments";

const PAGE_SIZE = 20;

// ─── Helpers ─────────────────────────────────────────────────────────────────

function StatCard({ label, value, icon, color }: { label: string; value: number; icon: React.ReactNode; color: string }) {
  return (
    <div className="bg-surface border border-divider rounded-xl p-4 flex items-center gap-3">
      <div className={`w-10 h-10 rounded-lg flex items-center justify-center shrink-0 ${color}`}>{icon}</div>
      <div>
        <p className="text-2xl font-bold text-text-1">{value.toLocaleString()}</p>
        <p className="text-xs text-text-3">{label}</p>
      </div>
    </div>
  );
}

function Pagination({
  page,
  totalPages,
  onChange,
}: {
  page: number;
  totalPages: number;
  onChange: (p: number) => void;
}) {
  if (totalPages <= 1) return null;
  return (
    <div className="flex items-center justify-between mt-4">
      <button
        disabled={page <= 1}
        onClick={() => onChange(page - 1)}
        className="flex items-center gap-1 text-sm border border-divider rounded-lg px-3 py-1.5 hover:bg-surface-2 disabled:opacity-40 disabled:cursor-not-allowed transition"
      >
        <ChevronLeft size={14} /> Prev
      </button>
      <span className="text-sm text-text-3">Page {page} of {totalPages}</span>
      <button
        disabled={page >= totalPages}
        onClick={() => onChange(page + 1)}
        className="flex items-center gap-1 text-sm border border-divider rounded-lg px-3 py-1.5 hover:bg-surface-2 disabled:opacity-40 disabled:cursor-not-allowed transition"
      >
        Next <ChevronRight size={14} />
      </button>
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function AdminPage() {
  const { user, loading: authLoading, isSuperAdmin } = useAuth();
  const router = useRouter();
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [statsLoading, setStatsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<Tab>("users");

  useEffect(() => {
    if (!authLoading && (!user || !isSuperAdmin)) {
      router.replace("/dashboard");
    }
  }, [user, authLoading, isSuperAdmin, router]);

  useEffect(() => {
    adminGetStats()
      .then(setStats)
      .catch(() => {})
      .finally(() => setStatsLoading(false));
  }, []);

  if (authLoading) {
    return (
      <div className="flex items-center justify-center py-32">
        <Loader2 size={28} className="animate-spin text-brand" />
      </div>
    );
  }

  const tabs: { key: Tab; label: string; icon: React.ReactNode }[] = [
    { key: "users", label: "Users", icon: <Users size={15} /> },
    { key: "colleges", label: "Colleges", icon: <Building2 size={15} /> },
    { key: "communities", label: "Communities", icon: <Network size={15} /> },
    { key: "posts", label: "Posts", icon: <FileText size={15} /> },
    { key: "comments", label: "Comments", icon: <MessageSquare size={15} /> },
  ];

  return (
    <div>
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-xl bg-accent-light flex items-center justify-center">
          <ShieldCheck size={22} className="text-accent-dark" />
        </div>
        <div>
          <h1 className="text-xl font-bold text-text-1">Super Admin Dashboard</h1>
          <p className="text-sm text-text-3">Platform-wide management</p>
        </div>
      </div>

      {/* Stats */}
      {!statsLoading && stats && (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 mb-7">
          <StatCard label="Users" value={stats.users} icon={<Users size={18} className="text-brand" />} color="bg-brand-light" />
          <StatCard label="Colleges" value={stats.colleges} icon={<Building2 size={18} className="text-community-dark" />} color="bg-community-light" />
          <StatCard label="Communities" value={stats.communities} icon={<Network size={18} className="text-accent-dark" />} color="bg-accent-light" />
          <StatCard label="Posts" value={stats.posts} icon={<FileText size={18} className="text-brand" />} color="bg-brand-light" />
          <StatCard label="Comments" value={stats.comments} icon={<MessageSquare size={18} className="text-text-2" />} color="bg-surface-2" />
          <StatCard label="Attachments" value={stats.attachments} icon={<Paperclip size={18} className="text-text-2" />} color="bg-surface-2" />
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-divider mb-6 overflow-x-auto">
        <div className="flex gap-1 min-w-max">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`flex items-center gap-1.5 px-4 py-2.5 text-sm font-medium border-b-2 transition whitespace-nowrap ${
                activeTab === tab.key
                  ? "border-brand text-brand"
                  : "border-transparent text-text-3 hover:text-text-2"
              }`}
            >
              {tab.icon}
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      <div>
        {activeTab === "users" && <UsersTab />}
        {activeTab === "colleges" && <CollegesTab />}
        {activeTab === "communities" && <CommunitiesTab />}
        {activeTab === "posts" && <PostsTab />}
        {activeTab === "comments" && <CommentsTab />}
      </div>
    </div>
  );
}

// ─── Users Tab ────────────────────────────────────────────────────────────────

function UsersTab() {
  const [data, setData] = useState<PagedResponse<AdminUser> | null>(null);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [typeLoading, setTypeLoading] = useState<Record<string, boolean>>({});
  const [activeLoading, setActiveLoading] = useState<Record<string, boolean>>({});

  const load = useCallback(async (p: number, s: string) => {
    setLoading(true);
    setError("");
    try {
      const res = await adminListUsers(p, PAGE_SIZE, s ? { search: s } : {});
      setData(res);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load users");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(page, search); }, [load, page, search]);

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    setPage(1);
    setSearch(searchInput);
  }

  async function handleTypeChange(user: AdminUser, type: UserType) {
    setTypeLoading((prev) => ({ ...prev, [user.id]: true }));
    try {
      const updated = await adminUpdateUserType(user.id, type);
      setData((prev) => prev ? {
        ...prev,
        items: prev.items.map((u) => u.id === updated.id ? updated : u),
      } : prev);
    } catch { /* no-op */ }
    finally { setTypeLoading((prev) => ({ ...prev, [user.id]: false })); }
  }

  async function handleToggleActive(user: AdminUser) {
    setActiveLoading((prev) => ({ ...prev, [user.id]: true }));
    try {
      const updated = await adminUpdateUserActive(user.id, !user.is_active);
      setData((prev) => prev ? {
        ...prev,
        items: prev.items.map((u) => u.id === updated.id ? updated : u),
      } : prev);
    } catch { /* no-op */ }
    finally { setActiveLoading((prev) => ({ ...prev, [user.id]: false })); }
  }

  const totalPages = data ? Math.max(1, Math.ceil(data.total / PAGE_SIZE)) : 1;

  return (
    <div>
      <form onSubmit={handleSearch} className="flex gap-2 mb-4">
        <div className="relative flex-1">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-3" />
          <input
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="Search by name or email…"
            className="w-full pl-9 pr-3 py-2 text-sm border border-divider rounded-lg bg-surface text-text-1 focus:outline-none focus:ring-2 focus:ring-brand-ring"
          />
        </div>
        <button type="submit" className="px-4 py-2 text-sm bg-brand hover:bg-brand-hover text-white rounded-lg transition">
          Search
        </button>
        {search && (
          <button type="button" onClick={() => { setSearchInput(""); setSearch(""); setPage(1); }} className="px-3 py-2 text-sm border border-divider rounded-lg hover:bg-surface-2 transition">
            <X size={14} />
          </button>
        )}
      </form>

      {loading ? (
        <div className="flex items-center justify-center py-16"><Loader2 size={24} className="animate-spin text-brand" /></div>
      ) : error ? (
        <div className="flex items-center gap-2 text-red-600 bg-red-50 border border-red-200 rounded-xl p-4 text-sm">
          <AlertCircle size={15} /> {error}
        </div>
      ) : (
        <>
          <div className="border border-divider rounded-xl overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-surface-2 text-text-3 text-xs">
                  <tr>
                    <th className="text-left px-4 py-2.5 font-medium">User</th>
                    <th className="text-left px-4 py-2.5 font-medium">Type</th>
                    <th className="text-left px-4 py-2.5 font-medium">Status</th>
                    <th className="text-left px-4 py-2.5 font-medium hidden sm:table-cell">Joined</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-divider">
                  {data?.items.map((u) => (
                    <tr key={u.id} className="bg-surface hover:bg-surface-2 transition">
                      <td className="px-4 py-3">
                        <div>
                          <p className="font-medium text-text-1 truncate max-w-[180px]">{u.name ?? "—"}</p>
                          <p className="text-xs text-text-3 truncate max-w-[180px]">{u.email}</p>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <select
                          value={u.type}
                          disabled={typeLoading[u.id]}
                          onChange={(e) => handleTypeChange(u, e.target.value as UserType)}
                          className="text-xs border border-divider rounded-md px-2 py-1 bg-surface text-text-1 focus:outline-none focus:ring-1 focus:ring-brand-ring"
                        >
                          <option value="USER">USER</option>
                          <option value="COLLEGE">COLLEGE</option>
                          <option value="SUPER_ADMIN">SUPER_ADMIN</option>
                        </select>
                      </td>
                      <td className="px-4 py-3">
                        <button
                          onClick={() => handleToggleActive(u)}
                          disabled={activeLoading[u.id]}
                          title={u.is_active ? "Deactivate" : "Activate"}
                          className="flex items-center gap-1 text-xs transition"
                        >
                          {activeLoading[u.id] ? (
                            <Loader2 size={16} className="animate-spin text-text-3" />
                          ) : u.is_active ? (
                            <ToggleRight size={20} className="text-brand" />
                          ) : (
                            <ToggleLeft size={20} className="text-text-3" />
                          )}
                          <span className={u.is_active ? "text-brand" : "text-text-3"}>
                            {u.is_active ? "Active" : "Inactive"}
                          </span>
                        </button>
                      </td>
                      <td className="px-4 py-3 text-xs text-text-3 hidden sm:table-cell">
                        {u.created_at ? new Date(u.created_at).toLocaleDateString() : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
          <Pagination page={page} totalPages={totalPages} onChange={(p) => setPage(p)} />
        </>
      )}
    </div>
  );
}

// ─── Colleges Tab ─────────────────────────────────────────────────────────────

function CollegesTab() {
  const [data, setData] = useState<PagedResponse<College> | null>(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [deleteLoading, setDeleteLoading] = useState(false);

  // Create modal
  const [createOpen, setCreateOpen] = useState(false);
  const [createForm, setCreateForm] = useState({ name: "", contact_email: "", physical_address: "" });
  const [createLoading, setCreateLoading] = useState(false);
  const [createError, setCreateError] = useState("");

  const load = useCallback(async (p: number) => {
    setLoading(true);
    setError("");
    try {
      const res = await adminListColleges(p, PAGE_SIZE);
      setData(res);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load colleges");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(page); }, [load, page]);

  async function handleDelete() {
    if (!deletingId) return;
    setDeleteLoading(true);
    try {
      await adminDeleteCollege(deletingId);
      setDeletingId(null);
      load(page);
    } catch { /* no-op */ }
    finally { setDeleteLoading(false); }
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setCreateLoading(true);
    setCreateError("");
    try {
      await adminCreateCollege(createForm);
      setCreateOpen(false);
      setCreateForm({ name: "", contact_email: "", physical_address: "" });
      load(1);
      setPage(1);
    } catch (e: unknown) {
      setCreateError(e instanceof Error ? e.message : "Failed to create college");
    } finally {
      setCreateLoading(false);
    }
  }

  const totalPages = data ? Math.max(1, Math.ceil(data.total / PAGE_SIZE)) : 1;

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <p className="text-sm text-text-3">{data?.total ?? 0} colleges</p>
        <button
          onClick={() => { setCreateOpen(true); setCreateError(""); }}
          className="flex items-center gap-1.5 text-sm bg-brand hover:bg-brand-hover text-white px-3 py-2 rounded-lg transition"
        >
          <Plus size={14} /> New College
        </button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-16"><Loader2 size={24} className="animate-spin text-brand" /></div>
      ) : error ? (
        <div className="flex items-center gap-2 text-red-600 bg-red-50 border border-red-200 rounded-xl p-4 text-sm"><AlertCircle size={15} /> {error}</div>
      ) : (
        <>
          <ul className="divide-y divide-divider border border-divider rounded-xl overflow-hidden">
            {data?.items.map((c) => (
              <li key={c.id} className="flex items-center justify-between gap-3 px-4 py-3 bg-surface hover:bg-surface-2 transition">
                <div className="flex items-center gap-3 min-w-0">
                  <div className="w-8 h-8 rounded-lg bg-community-light flex items-center justify-center shrink-0">
                    <Building2 size={15} className="text-community-dark" />
                  </div>
                  <div className="min-w-0">
                    <p className="font-medium text-text-1 text-sm truncate">{c.name}</p>
                    <p className="text-xs text-text-3 truncate">{c.contact_email}</p>
                  </div>
                </div>
                <button
                  onClick={() => setDeletingId(c.id)}
                  className="p-1.5 text-text-3 hover:text-red-600 hover:bg-red-50 rounded-md transition shrink-0"
                >
                  <Trash2 size={14} />
                </button>
              </li>
            ))}
          </ul>
          <Pagination page={page} totalPages={totalPages} onChange={(p) => setPage(p)} />
        </>
      )}

      {/* Create College Modal */}
      {createOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="bg-surface rounded-2xl shadow-2xl border border-divider w-full max-w-md">
            <div className="flex items-center justify-between px-5 py-4 border-b border-divider">
              <h2 className="font-semibold text-text-1">New College</h2>
              <button onClick={() => setCreateOpen(false)} className="text-text-3 hover:text-text-1"><X size={18} /></button>
            </div>
            <form onSubmit={handleCreate} className="p-5 space-y-4">
              {createError && (
                <div className="flex items-center gap-2 text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2 text-sm">
                  <AlertCircle size={14} /> {createError}
                </div>
              )}
              <div>
                <label className="block text-sm font-medium text-text-1 mb-1">College Name</label>
                <input
                  value={createForm.name}
                  onChange={(e) => setCreateForm((f) => ({ ...f, name: e.target.value }))}
                  required
                  className="w-full border border-divider rounded-lg px-3 py-2 text-sm bg-surface text-text-1 focus:outline-none focus:ring-2 focus:ring-brand-ring"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-text-1 mb-1">Contact Email</label>
                <input
                  type="email"
                  value={createForm.contact_email}
                  onChange={(e) => setCreateForm((f) => ({ ...f, contact_email: e.target.value }))}
                  required
                  className="w-full border border-divider rounded-lg px-3 py-2 text-sm bg-surface text-text-1 focus:outline-none focus:ring-2 focus:ring-brand-ring"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-text-1 mb-1">Physical Address</label>
                <input
                  value={createForm.physical_address}
                  onChange={(e) => setCreateForm((f) => ({ ...f, physical_address: e.target.value }))}
                  className="w-full border border-divider rounded-lg px-3 py-2 text-sm bg-surface text-text-1 focus:outline-none focus:ring-2 focus:ring-brand-ring"
                />
              </div>
              <div className="flex justify-end gap-3 pt-1">
                <button type="button" onClick={() => setCreateOpen(false)} className="px-4 py-2 text-sm border border-divider rounded-lg hover:bg-surface-2 transition">Cancel</button>
                <button type="submit" disabled={createLoading} className="flex items-center gap-2 px-4 py-2 text-sm bg-brand hover:bg-brand-hover disabled:bg-brand-disabled text-white rounded-lg transition">
                  {createLoading && <Loader2 size={13} className="animate-spin" />}
                  <Check size={13} /> Create
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete confirm */}
      {deletingId && (
        <ConfirmDeleteModal
          onConfirm={handleDelete}
          onCancel={() => setDeletingId(null)}
          loading={deleteLoading}
        />
      )}
    </div>
  );
}

// ─── Communities Tab ──────────────────────────────────────────────────────────

function CommunitiesTab() {
  const [data, setData] = useState<PagedResponse<Community> | null>(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [deleteLoading, setDeleteLoading] = useState(false);

  const load = useCallback(async (p: number) => {
    setLoading(true);
    setError("");
    try {
      const res = await adminListCommunities(p, PAGE_SIZE);
      setData(res);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load communities");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(page); }, [load, page]);

  async function handleDelete() {
    if (!deletingId) return;
    setDeleteLoading(true);
    try {
      await adminDeleteCommunity(deletingId);
      setDeletingId(null);
      load(page);
    } catch { /* no-op */ }
    finally { setDeleteLoading(false); }
  }

  const totalPages = data ? Math.max(1, Math.ceil(data.total / PAGE_SIZE)) : 1;

  return (
    <div>
      {loading ? (
        <div className="flex items-center justify-center py-16"><Loader2 size={24} className="animate-spin text-brand" /></div>
      ) : error ? (
        <div className="flex items-center gap-2 text-red-600 bg-red-50 border border-red-200 rounded-xl p-4 text-sm"><AlertCircle size={15} /> {error}</div>
      ) : (
        <>
          <ul className="divide-y divide-divider border border-divider rounded-xl overflow-hidden mb-4">
            {data?.items.map((c) => (
              <li key={c.id} className="flex items-center justify-between gap-3 px-4 py-3 bg-surface hover:bg-surface-2 transition">
                <div className="flex items-center gap-3 min-w-0">
                  <div className="shrink-0">
                    {c.type === "PRIVATE" ? (
                      <Lock size={15} className="text-text-3" />
                    ) : (
                      <Globe size={15} className="text-text-3" />
                    )}
                  </div>
                  <div className="min-w-0">
                    <p className="font-medium text-text-1 text-sm truncate">{c.name}</p>
                    <p className="text-xs text-text-3">{c.member_count ?? 0} members · {c.post_count ?? 0} posts</p>
                  </div>
                </div>
                <button onClick={() => setDeletingId(c.id)} className="p-1.5 text-text-3 hover:text-red-600 hover:bg-red-50 rounded-md transition shrink-0">
                  <Trash2 size={14} />
                </button>
              </li>
            ))}
          </ul>
          <Pagination page={page} totalPages={totalPages} onChange={(p) => setPage(p)} />
        </>
      )}
      {deletingId && (
        <ConfirmDeleteModal onConfirm={handleDelete} onCancel={() => setDeletingId(null)} loading={deleteLoading} />
      )}
    </div>
  );
}

// ─── Posts Tab ────────────────────────────────────────────────────────────────

function PostsTab() {
  const [data, setData] = useState<PostListResponse | null>(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [deleteLoading, setDeleteLoading] = useState(false);

  const load = useCallback(async (p: number) => {
    setLoading(true);
    setError("");
    try {
      const res = await adminListPosts(p, PAGE_SIZE);
      setData(res);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load posts");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(page); }, [load, page]);

  async function handleDelete() {
    if (!deletingId) return;
    setDeleteLoading(true);
    try {
      await adminDeletePost(deletingId);
      setDeletingId(null);
      load(page);
    } catch { /* no-op */ }
    finally { setDeleteLoading(false); }
  }

  const totalPages = data ? Math.max(1, Math.ceil(data.total / PAGE_SIZE)) : 1;

  return (
    <div>
      {loading ? (
        <div className="flex items-center justify-center py-16"><Loader2 size={24} className="animate-spin text-brand" /></div>
      ) : error ? (
        <div className="flex items-center gap-2 text-red-600 bg-red-50 border border-red-200 rounded-xl p-4 text-sm"><AlertCircle size={15} /> {error}</div>
      ) : (
        <>
          <ul className="divide-y divide-divider border border-divider rounded-xl overflow-hidden mb-4">
            {data?.items.map((p: Post) => (
              <li key={p.id} className="flex items-start justify-between gap-3 px-4 py-3 bg-surface hover:bg-surface-2 transition">
                <div className="min-w-0">
                  <p className="text-sm text-text-1 line-clamp-2 break-words">{p.content}</p>
                  <p className="text-xs text-text-3 mt-1">{p.created_at ? new Date(p.created_at).toLocaleDateString() : ""}</p>
                </div>
                <button onClick={() => setDeletingId(p.id)} className="p-1.5 text-text-3 hover:text-red-600 hover:bg-red-50 rounded-md transition shrink-0">
                  <Trash2 size={14} />
                </button>
              </li>
            ))}
          </ul>
          <Pagination page={page} totalPages={totalPages} onChange={(p) => setPage(p)} />
        </>
      )}
      {deletingId && (
        <ConfirmDeleteModal onConfirm={handleDelete} onCancel={() => setDeletingId(null)} loading={deleteLoading} />
      )}
    </div>
  );
}

// ─── Comments Tab ─────────────────────────────────────────────────────────────

function CommentsTab() {
  const [data, setData] = useState<CommentListResponse | null>(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [deleteLoading, setDeleteLoading] = useState(false);

  const load = useCallback(async (p: number) => {
    setLoading(true);
    setError("");
    try {
      const res = await adminListComments(p, PAGE_SIZE);
      setData(res);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load comments");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(page); }, [load, page]);

  async function handleDelete() {
    if (!deletingId) return;
    setDeleteLoading(true);
    try {
      await adminDeleteComment(deletingId);
      setDeletingId(null);
      load(page);
    } catch { /* no-op */ }
    finally { setDeleteLoading(false); }
  }

  const totalPages = data ? Math.max(1, Math.ceil(data.total / PAGE_SIZE)) : 1;

  return (
    <div>
      {loading ? (
        <div className="flex items-center justify-center py-16"><Loader2 size={24} className="animate-spin text-brand" /></div>
      ) : error ? (
        <div className="flex items-center gap-2 text-red-600 bg-red-50 border border-red-200 rounded-xl p-4 text-sm"><AlertCircle size={15} /> {error}</div>
      ) : (
        <>
          <ul className="divide-y divide-divider border border-divider rounded-xl overflow-hidden mb-4">
            {data?.items.map((c: Comment) => (
              <li key={c.id} className="flex items-start justify-between gap-3 px-4 py-3 bg-surface hover:bg-surface-2 transition">
                <div className="min-w-0">
                  <p className="text-sm text-text-1 line-clamp-2 break-words">{c.content}</p>
                  <p className="text-xs text-text-3 mt-1">{c.created_at ? new Date(c.created_at).toLocaleDateString() : ""}</p>
                </div>
                <button onClick={() => setDeletingId(c.id)} className="p-1.5 text-text-3 hover:text-red-600 hover:bg-red-50 rounded-md transition shrink-0">
                  <Trash2 size={14} />
                </button>
              </li>
            ))}
          </ul>
          <Pagination page={page} totalPages={totalPages} onChange={(p) => setPage(p)} />
        </>
      )}
      {deletingId && (
        <ConfirmDeleteModal onConfirm={handleDelete} onCancel={() => setDeletingId(null)} loading={deleteLoading} />
      )}
    </div>
  );
}

// ─── Shared Delete Modal ──────────────────────────────────────────────────────

function ConfirmDeleteModal({
  onConfirm,
  onCancel,
  loading,
}: {
  onConfirm: () => void;
  onCancel: () => void;
  loading: boolean;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="bg-surface rounded-2xl shadow-2xl border border-divider w-full max-w-sm p-6">
        <div className="flex items-center gap-3 mb-5">
          <div className="w-10 h-10 rounded-full bg-red-100 flex items-center justify-center text-red-600 shrink-0">
            <Trash2 size={18} />
          </div>
          <div>
            <p className="font-semibold text-text-1">Confirm delete</p>
            <p className="text-sm text-text-3">This action cannot be undone.</p>
          </div>
        </div>
        <div className="flex justify-end gap-3">
          <button onClick={onCancel} className="px-4 py-2 text-sm border border-divider rounded-lg hover:bg-surface-2 transition">
            Cancel
          </button>
          <button
            onClick={onConfirm}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 text-sm bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white rounded-lg transition"
          >
            {loading && <Loader2 size={13} className="animate-spin" />}
            Delete
          </button>
        </div>
      </div>
    </div>
  );
}
