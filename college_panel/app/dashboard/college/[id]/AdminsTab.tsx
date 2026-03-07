"use client";

import { useEffect, useState } from "react";
import { College, UserProfile, addCollegeAdmin, removeCollegeAdmin, getUserProfile } from "@/lib/api";
import {
  Shield,
  Plus,
  Trash2,
  Loader2,
  AlertCircle,
  Check,
  X,
  Crown,
  Mail,
} from "lucide-react";
import { useAuth } from "@/lib/auth-context";

interface Props {
  college: College;
  onRefresh: () => Promise<void>;
}

function AdminAvatar({ profile, isFirst }: { profile: UserProfile | null; isFirst: boolean }) {
  if (profile?.picture) {
    return (
      <img
        src={profile.picture}
        alt={profile.name ?? "Admin"}
        className="w-9 h-9 rounded-full object-cover shrink-0"
      />
    );
  }
  if (isFirst) {
    return (
      <div className="w-9 h-9 rounded-full bg-amber-100 flex items-center justify-center text-amber-600 shrink-0">
        <Crown size={14} />
      </div>
    );
  }
  const initials = profile?.name
    ? profile.name.split(" ").map((p) => p[0]).slice(0, 2).join("").toUpperCase()
    : "?";
  return (
    <div className="w-9 h-9 rounded-full bg-blue-100 flex items-center justify-center text-blue-700 text-xs font-bold shrink-0 select-none">
      {initials}
    </div>
  );
}

export default function AdminsTab({ college, onRefresh }: Props) {
  const { user } = useAuth();
  const [profiles, setProfiles] = useState<Record<string, UserProfile | null>>({});
  const [addMode, setAddMode] = useState(false);
  const [newUserId, setNewUserId] = useState("");
  const [saving, setSaving] = useState(false);
  const [removing, setRemoving] = useState<string | null>(null);
  const [error, setError] = useState("");

  // Fetch user profiles for all admin UUIDs
  useEffect(() => {
    const missing = college.admin_users.filter((id) => !(id in profiles));
    if (missing.length === 0) return;
    Promise.all(
      missing.map((id) =>
        getUserProfile(id)
          .then((p) => ({ id, profile: p }))
          .catch(() => ({ id, profile: null }))
      )
    ).then((results) => {
      setProfiles((prev) => {
        const next = { ...prev };
        for (const { id, profile } of results) next[id] = profile;
        return next;
      });
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [college.admin_users]);

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setSaving(true);
    try {
      await addCollegeAdmin(college.id, newUserId.trim());
      setNewUserId("");
      setAddMode(false);
      await onRefresh();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to add admin");
    } finally {
      setSaving(false);
    }
  }

  async function handleRemove(userId: string) {
    if (!confirm("Remove this admin?")) return;
    setRemoving(userId);
    setError("");
    try {
      await removeCollegeAdmin(college.id, userId);
      await onRefresh();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to remove admin");
    } finally {
      setRemoving(null);
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-base font-semibold text-slate-800">
          {college.admin_users.length} Admin{college.admin_users.length !== 1 ? "s" : ""}
        </h2>
        {!addMode && (
          <button
            onClick={() => setAddMode(true)}
            className="flex items-center gap-1.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-3.5 py-2 rounded-lg transition"
          >
            <Plus size={15} />
            Add admin
          </button>
        )}
      </div>

      {error && (
        <div className="flex items-center gap-2 bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 mb-4 text-sm">
          <AlertCircle size={15} />
          {error}
        </div>
      )}

      {/* Add admin form */}
      {addMode && (
        <form
          onSubmit={handleAdd}
          className="bg-blue-50 border border-blue-200 rounded-xl p-4 mb-4"
        >
          <label className="block text-sm font-medium text-slate-700 mb-2">
            User ID to add as admin
          </label>
          <div className="flex gap-2">
            <input
              value={newUserId}
              onChange={(e) => setNewUserId(e.target.value)}
              required
              placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
              className="flex-1 px-3 py-2 border border-slate-200 rounded-lg text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
            />
            <button
              type="submit"
              disabled={saving}
              className="flex items-center gap-1 px-3 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition disabled:bg-blue-400"
            >
              {saving ? <Loader2 size={14} className="animate-spin" /> : <Check size={14} />}
            </button>
            <button
              type="button"
              onClick={() => { setAddMode(false); setNewUserId(""); setError(""); }}
              className="px-3 py-2 text-sm text-slate-600 bg-white border border-slate-200 hover:bg-slate-50 rounded-lg transition"
            >
              <X size={14} />
            </button>
          </div>
          <p className="text-xs text-slate-500 mt-2">
            Enter the exact UUID of the user to promote to college admin.
          </p>
        </form>
      )}

      {college.admin_users.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-2xl border border-dashed border-slate-200">
          <Shield size={28} className="mx-auto text-slate-300 mb-2" />
          <p className="text-slate-500 text-sm">No admins found.</p>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 divide-y divide-slate-100">
          {college.admin_users.map((adminId, idx) => {
            const isSelf = user?.id === adminId;
            const profile = profiles[adminId] ?? null;
            return (
              <div key={adminId} className="flex items-center gap-3 px-4 py-3.5">
                <AdminAvatar profile={profile} isFirst={idx === 0} />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-slate-800 flex items-center gap-1.5 truncate">
                    {profile?.name ?? <span className="text-slate-400 italic">Loading…</span>}
                    {isSelf && (
                      <span className="text-xs bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded-full font-medium shrink-0">
                        you
                      </span>
                    )}
                  </p>
                  {profile?.email ? (
                    <p className="text-xs text-slate-500 flex items-center gap-1 mt-0.5 truncate">
                      <Mail size={10} />
                      {profile.email}
                    </p>
                  ) : (
                    <p className="text-xs text-slate-400 font-mono truncate mt-0.5">{adminId}</p>
                  )}
                </div>
                <button
                  onClick={() => handleRemove(adminId)}
                  disabled={!!removing}
                  className="p-1.5 rounded-lg text-slate-400 hover:text-red-600 hover:bg-red-50 transition disabled:opacity-50"
                  title="Remove admin"
                >
                  {removing === adminId ? (
                    <Loader2 size={14} className="animate-spin" />
                  ) : (
                    <Trash2 size={14} />
                  )}
                </button>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
