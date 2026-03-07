"use client";

import { useState } from "react";
import {
  Community,
  CommunityType,
  createCommunity,
  updateCommunity,
  deleteCommunity,
  joinCommunity,
  cancelJoinRequest,
} from "@/lib/api";
import {
  Plus,
  Pencil,
  Trash2,
  Users,
  Lock,
  Globe,
  X,
  Check,
  Loader2,
  BookOpen,
  AlertCircle,
  LogIn,
  LogOut,
  Clock,
} from "lucide-react";
import { useAuth } from "@/lib/auth-context";

interface Props {
  collegeId: string;
  communities: Community[];
  onRefresh: () => Promise<void>;
}

interface ModalState {
  mode: "create" | "edit";
  community?: Community;
}

export default function CommunitiesTab({ collegeId, communities, onRefresh }: Props) {
  const { user } = useAuth();
  const [modal, setModal] = useState<ModalState | null>(null);
  const [deleting, setDeleting] = useState<string | null>(null);
  const [joining, setJoining] = useState<string | null>(null);
  const [error, setError] = useState("");

  async function handleDelete(id: string, name: string) {
    if (!confirm(`Delete "${name}"? This cannot be undone.`)) return;
    setDeleting(id);
    setError("");
    try {
      await deleteCommunity(id);
      await onRefresh();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Delete failed");
    } finally {
      setDeleting(null);
    }
  }

  async function handleJoin(id: string) {
    setJoining(id);
    setError("");
    try {
      await joinCommunity(id);
      await onRefresh();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Join failed");
    } finally {
      setJoining(null);
    }
  }

  async function handleCancel(id: string) {
    setJoining(id + "_cancel");
    setError("");
    try {
      await cancelJoinRequest(id);
      await onRefresh();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Cancel failed");
    } finally {
      setJoining(null);
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-base font-semibold text-slate-800">
          {communities.length} {communities.length === 1 ? "Community" : "Communities"}
        </h2>
        <button
          onClick={() => setModal({ mode: "create" })}
          className="flex items-center gap-1.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-3.5 py-2 rounded-lg transition"
        >
          <Plus size={15} />
          New community
        </button>
      </div>

      {error && (
        <div className="flex items-center gap-2 bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 mb-4 text-sm">
          <AlertCircle size={15} />
          {error}
        </div>
      )}

      {communities.length === 0 ? (
        <div className="text-center py-16 bg-white rounded-2xl border border-dashed border-slate-200">
          <BookOpen size={32} className="mx-auto text-slate-300 mb-3" />
          <p className="text-slate-500 text-sm">No communities yet. Create your first one.</p>
        </div>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {communities.map((c) => {
            const uid = user?.id ?? "";
            const isMember = c.member_users.includes(uid);
            const isPending = c.requested_users.includes(uid);
            return (
              <div
                key={c.id}
                className="bg-white rounded-xl border border-slate-200 p-4 hover:border-slate-300 transition flex flex-col gap-3"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    {c.type === "PUBLIC" ? (
                      <Globe size={15} className="text-emerald-500 shrink-0" />
                    ) : (
                      <Lock size={15} className="text-amber-500 shrink-0" />
                    )}
                    <h3 className="font-medium text-slate-900 text-sm leading-tight">{c.name}</h3>
                  </div>
                  <div className="flex items-center gap-1 ml-2 shrink-0">
                    <button
                      onClick={() => setModal({ mode: "edit", community: c })}
                      className="p-1.5 rounded-lg text-slate-400 hover:text-blue-600 hover:bg-blue-50 transition"
                      title="Edit"
                    >
                      <Pencil size={13} />
                    </button>
                    <button
                      onClick={() => handleDelete(c.id, c.name)}
                      disabled={deleting === c.id}
                      className="p-1.5 rounded-lg text-slate-400 hover:text-red-600 hover:bg-red-50 transition disabled:opacity-50"
                      title="Delete"
                    >
                      {deleting === c.id ? (
                        <Loader2 size={13} className="animate-spin" />
                      ) : (
                        <Trash2 size={13} />
                      )}
                    </button>
                  </div>
                </div>

                <div className="flex items-center justify-between text-xs text-slate-500">
                  <span className="flex items-center gap-1">
                    <Users size={11} />
                    {c.member_users.length} members
                  </span>
                  <span
                    className={`px-2 py-0.5 rounded-full font-medium ${
                      c.type === "PUBLIC"
                        ? "bg-emerald-50 text-emerald-700"
                        : "bg-amber-50 text-amber-700"
                    }`}
                  >
                    {c.type}
                  </span>
                </div>

                {c.type === "PRIVATE" && c.requested_users.length > 0 && (
                  <div className="text-xs text-amber-600 bg-amber-50 rounded-lg px-2 py-1">
                    {c.requested_users.length} pending request{c.requested_users.length > 1 ? "s" : ""}
                  </div>
                )}

                {/* Join / status controls */}
                {isMember ? (
                  <button
                    onClick={() => handleCancel(c.id)}
                    disabled={joining === c.id + "_cancel"}
                    className="flex items-center justify-center gap-1.5 w-full px-3 py-1.5 text-xs font-medium text-slate-500 bg-slate-100 hover:bg-red-50 hover:text-red-600 rounded-lg transition disabled:opacity-50"
                  >
                    {joining === c.id + "_cancel" ? <Loader2 size={11} className="animate-spin" /> : <LogOut size={11} />}
                    Leave
                  </button>
                ) : isPending ? (
                  <button
                    onClick={() => handleCancel(c.id)}
                    disabled={joining === c.id + "_cancel"}
                    className="flex items-center justify-center gap-1.5 w-full px-3 py-1.5 text-xs font-medium text-amber-700 bg-amber-50 hover:bg-red-50 hover:text-red-600 rounded-lg transition disabled:opacity-50"
                  >
                    {joining === c.id + "_cancel" ? <Loader2 size={11} className="animate-spin" /> : <Clock size={11} />}
                    Pending — Cancel
                  </button>
                ) : (
                  <button
                    onClick={() => handleJoin(c.id)}
                    disabled={joining === c.id}
                    className="flex items-center justify-center gap-1.5 w-full px-3 py-1.5 text-xs font-medium text-blue-700 bg-blue-50 hover:bg-blue-100 rounded-lg transition disabled:opacity-50"
                  >
                    {joining === c.id ? <Loader2 size={11} className="animate-spin" /> : <LogIn size={11} />}
                    {c.type === "PUBLIC" ? "Join" : "Request to Join"}
                  </button>
                )}
              </div>
            );
          })}
        </div>
      )}

      {modal && (
        <CommunityModal
          mode={modal.mode}
          community={modal.community}
          collegeId={collegeId}
          onClose={() => setModal(null)}
          onSaved={async () => {
            setModal(null);
            await onRefresh();
          }}
        />
      )}
    </div>
  );
}

// ── Modal ─────────────────────────────────────────────────────────────────────

function CommunityModal({
  mode,
  community,
  collegeId,
  onClose,
  onSaved,
}: {
  mode: "create" | "edit";
  community?: Community;
  collegeId: string;
  onClose: () => void;
  onSaved: () => Promise<void>;
}) {
  const [name, setName] = useState(community?.name ?? "");
  const [type, setType] = useState<CommunityType>(community?.type ?? "PUBLIC");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setSaving(true);
    try {
      if (mode === "create") {
        await createCommunity({ name, type, parent_colleges: [collegeId] });
      } else if (community) {
        await updateCommunity(community.id, { name, type });
      }
      await onSaved();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Save failed");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md">
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100">
          <h3 className="font-semibold text-slate-900">
            {mode === "create" ? "New community" : "Edit community"}
          </h3>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition"
          >
            <X size={16} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="flex items-center gap-2 bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 text-sm">
              <AlertCircle size={15} />
              {error}
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">Name</label>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              minLength={3}
              maxLength={100}
              placeholder="e.g. Computer Science Club"
              className="w-full px-3 py-2.5 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">Type</label>
            <div className="grid grid-cols-2 gap-2">
              {(["PUBLIC", "PRIVATE"] as CommunityType[]).map((t) => (
                <button
                  key={t}
                  type="button"
                  onClick={() => setType(t)}
                  className={`flex items-center gap-2 px-3 py-2.5 rounded-lg border text-sm font-medium transition ${
                    type === t
                      ? t === "PUBLIC"
                        ? "border-emerald-500 bg-emerald-50 text-emerald-700"
                        : "border-amber-500 bg-amber-50 text-amber-700"
                      : "border-slate-200 text-slate-500 hover:border-slate-300"
                  }`}
                >
                  {t === "PUBLIC" ? <Globe size={14} /> : <Lock size={14} />}
                  {t}
                </button>
              ))}
            </div>
            <p className="text-xs text-slate-400 mt-1.5">
              {type === "PUBLIC"
                ? "Anyone can join immediately."
                : "Users must request to join and be approved."}
            </p>
          </div>

          <div className="flex gap-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2.5 text-sm font-medium text-slate-600 bg-slate-100 hover:bg-slate-200 rounded-lg transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving}
              className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 rounded-lg transition"
            >
              {saving ? <Loader2 size={14} className="animate-spin" /> : <Check size={14} />}
              {saving ? "Saving…" : mode === "create" ? "Create" : "Save changes"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
