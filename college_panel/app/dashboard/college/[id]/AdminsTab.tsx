"use client";

import { useEffect, useState } from "react";
import {
  College,
  UserProfile,
  getUserProfile,
  addCollegeAdmin,
  removeCollegeAdmin,
} from "@/lib/api";
import {
  ShieldCheck,
  UserPlus,
  UserMinus,
  Loader2,
  AlertCircle,
  X,
  Plus,
} from "lucide-react";

interface Props {
  college: College;
  onCollegeChange: (updated: College) => void;
}

export default function AdminsTab({ college, onCollegeChange }: Props) {
  const [profiles, setProfiles] = useState<Record<string, UserProfile | null>>({});
  const [profilesLoading, setProfilesLoading] = useState(false);

  // Add admin form
  const [addOpen, setAddOpen] = useState(false);
  const [newAdminId, setNewAdminId] = useState("");
  const [addLoading, setAddLoading] = useState(false);
  const [addError, setAddError] = useState("");

  // Remove per user
  const [removeLoading, setRemoveLoading] = useState<Record<string, boolean>>({});

  // Fetch profiles whenever admin list changes
  useEffect(() => {
    if (college.admin_users.length === 0) return;
    setProfilesLoading(true);
    Promise.allSettled(college.admin_users.map((id) => getUserProfile(id)))
      .then((results) => {
        const map: Record<string, UserProfile | null> = {};
        college.admin_users.forEach((id, i) => {
          const r = results[i];
          map[id] = r.status === "fulfilled" ? r.value : null;
        });
        setProfiles(map);
      })
      .finally(() => setProfilesLoading(false));
    // Re-run only when the list of IDs changes
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [college.admin_users.join(",")]);

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault();
    const uid = newAdminId.trim();
    if (!uid) return;
    setAddLoading(true);
    setAddError("");
    try {
      await addCollegeAdmin(college.id, uid);
      onCollegeChange({ ...college, admin_users: [...college.admin_users, uid] });
      setNewAdminId("");
      setAddOpen(false);
    } catch (e: unknown) {
      setAddError(e instanceof Error ? e.message : "Failed to add admin");
    } finally {
      setAddLoading(false);
    }
  }

  async function handleRemove(userId: string) {
    setRemoveLoading((prev) => ({ ...prev, [userId]: true }));
    try {
      await removeCollegeAdmin(college.id, userId);
      onCollegeChange({ ...college, admin_users: college.admin_users.filter((id) => id !== userId) });
    } catch {
      // no-op
    } finally {
      setRemoveLoading((prev) => ({ ...prev, [userId]: false }));
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <p className="text-sm text-text-3">{college.admin_users.length} admin{college.admin_users.length !== 1 ? "s" : ""}</p>
        <button
          onClick={() => { setAddOpen(true); setAddError(""); setNewAdminId(""); }}
          className="flex items-center gap-1.5 text-sm bg-brand hover:bg-brand-hover text-white px-3 py-2 rounded-lg transition"
        >
          <Plus size={14} />
          Add Admin
        </button>
      </div>

      {college.admin_users.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-text-3">
          <ShieldCheck size={36} className="mb-3 opacity-40" />
          <p className="text-text-2 font-medium">No admins assigned</p>
        </div>
      ) : profilesLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 size={24} className="animate-spin text-brand" />
        </div>
      ) : (
        <ul className="divide-y divide-divider border border-divider rounded-xl overflow-hidden">
          {college.admin_users.map((userId) => {
            const p = profiles[userId];
            const busy = removeLoading[userId] ?? false;
            return (
              <li key={userId} className="flex items-center justify-between gap-3 px-4 py-3 bg-surface">
                <div className="flex items-center gap-3 min-w-0">
                  {p?.picture ? (
                    <img
                      src={p.picture}
                      alt={p.name ?? "Admin"}
                      className="w-9 h-9 rounded-full object-cover shrink-0 bg-surface-2"
                    />
                  ) : (
                    <div className="w-9 h-9 rounded-full bg-accent-light flex items-center justify-center text-accent-dark font-bold text-sm shrink-0">
                      {(p?.name ?? "?")[0].toUpperCase()}
                    </div>
                  )}
                  <div className="min-w-0">
                    <div className="flex items-center gap-1.5">
                      <p className="text-sm font-medium text-text-1 truncate">{p?.name ?? "Unknown user"}</p>
                      <ShieldCheck size={13} className="text-accent-dark shrink-0" />
                    </div>
                    <p className="text-xs text-text-3 truncate">{p?.email ?? userId}</p>
                  </div>
                </div>
                <button
                  onClick={() => handleRemove(userId)}
                  disabled={busy}
                  title="Remove admin"
                  className="flex items-center gap-1 text-xs text-red-600 border border-red-200 hover:bg-red-50 disabled:opacity-50 px-2.5 py-1.5 rounded-lg transition shrink-0"
                >
                  {busy ? <Loader2 size={12} className="animate-spin" /> : <UserMinus size={12} />}
                  Remove
                </button>
              </li>
            );
          })}
        </ul>
      )}

      {/* Add Admin Modal */}
      {addOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="bg-surface rounded-2xl shadow-2xl border border-divider w-full max-w-sm">
            <div className="flex items-center justify-between px-5 py-4 border-b border-divider">
              <div className="flex items-center gap-2">
                <UserPlus size={16} className="text-brand" />
                <h2 className="font-semibold text-text-1">Add Admin</h2>
              </div>
              <button onClick={() => setAddOpen(false)} className="text-text-3 hover:text-text-1">
                <X size={18} />
              </button>
            </div>
            <form onSubmit={handleAdd} className="p-5 space-y-4">
              {addError && (
                <div className="flex items-center gap-2 text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2 text-sm">
                  <AlertCircle size={14} />
                  {addError}
                </div>
              )}
              <div>
                <label className="block text-sm font-medium text-text-1 mb-1">User ID</label>
                <input
                  value={newAdminId}
                  onChange={(e) => setNewAdminId(e.target.value)}
                  placeholder="Paste user UUID here"
                  required
                  className="w-full border border-divider rounded-lg px-3 py-2 text-sm text-text-1 bg-surface focus:outline-none focus:ring-2 focus:ring-brand-ring font-mono"
                />
                <p className="text-xs text-text-3 mt-1">The user must already have a campus account.</p>
              </div>
              <div className="flex justify-end gap-3 pt-1">
                <button type="button" onClick={() => setAddOpen(false)} className="px-4 py-2 text-sm text-text-2 border border-divider rounded-lg hover:bg-surface-2 transition">
                  Cancel
                </button>
                <button type="submit" disabled={addLoading} className="flex items-center gap-2 px-4 py-2 text-sm bg-brand hover:bg-brand-hover disabled:bg-brand-disabled text-white rounded-lg transition">
                  {addLoading && <Loader2 size={13} className="animate-spin" />}
                  Add
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
