"use client";

import { useState, useCallback } from "react";
import {
  Community,
  College,
  CommunityType,
  createCommunity,
  updateCommunity,
  deleteCommunity,
  joinCommunity,
  cancelJoinRequest,
} from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import {
  Plus,
  Pencil,
  Trash2,
  Loader2,
  AlertCircle,
  X,
  Globe,
  Lock,
  ShieldCheck,
  UserPlus,
  UserCheck,
  UserMinus,
  Clock,
} from "lucide-react";

interface Props {
  college: College;
  communities: Community[];
  onCommunitiesChange: (updated: Community[]) => void;
}

interface CommunityForm {
  name: string;
  type: CommunityType;
}

const EMPTY_FORM: CommunityForm = { name: "", type: "PUBLIC" };

export default function CommunitiesTab({ college, communities, onCommunitiesChange }: Props) {
  const { isCollegeAdmin } = useAuth();

  // Create/edit modal
  const [modalOpen, setModalOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState<CommunityForm>(EMPTY_FORM);
  const [modalLoading, setModalLoading] = useState(false);
  const [modalError, setModalError] = useState("");

  // Delete confirmation
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [deleteLoading, setDeleteLoading] = useState(false);

  // Join/leave per community
  const [actionLoading, setActionLoading] = useState<Record<string, boolean>>({});
  const [actionError, setActionError] = useState<Record<string, string>>({});

  function openCreate() {
    setEditingId(null);
    setForm(EMPTY_FORM);
    setModalError("");
    setModalOpen(true);
  }

  function openEdit(c: Community) {
    setEditingId(c.id);
    setForm({ name: c.name, type: c.type });
    setModalError("");
    setModalOpen(true);
  }

  async function submitModal(e: React.FormEvent) {
    e.preventDefault();
    setModalLoading(true);
    setModalError("");
    try {
      if (editingId) {
        const updated = await updateCommunity(editingId, { name: form.name, type: form.type });
        onCommunitiesChange(communities.map((c) => (c.id === editingId ? updated : c)));
      } else {
        const created = await createCommunity({
          name: form.name,
          type: form.type,
          parent_colleges: [college.id],
        });
        onCommunitiesChange([...communities, created]);
      }
      setModalOpen(false);
    } catch (e: unknown) {
      setModalError(e instanceof Error ? e.message : "Save failed");
    } finally {
      setModalLoading(false);
    }
  }

  async function confirmDelete() {
    if (!deletingId) return;
    setDeleteLoading(true);
    try {
      await deleteCommunity(deletingId);
      onCommunitiesChange(communities.filter((c) => c.id !== deletingId));
      setDeletingId(null);
    } catch {
      // keep dialog open so user sees nothing happened
    } finally {
      setDeleteLoading(false);
    }
  }

  const doAction = useCallback(async (community: Community, action: "join" | "cancel") => {
    setActionLoading((prev) => ({ ...prev, [community.id]: true }));
    setActionError((prev) => ({ ...prev, [community.id]: "" }));
    try {
      if (action === "join") {
        await joinCommunity(community.id);
        // Optimistically update state
        onCommunitiesChange(
          communities.map((c) =>
            c.id === community.id
              ? { ...c, is_requested: c.type === "PRIVATE" ? true : null, is_member: c.type === "PUBLIC" ? true : c.is_member }
              : c
          )
        );
      } else {
        await cancelJoinRequest(community.id);
        onCommunitiesChange(
          communities.map((c) =>
            c.id === community.id ? { ...c, is_requested: false, is_member: false } : c
          )
        );
      }
    } catch (e: unknown) {
      setActionError((prev) => ({
        ...prev,
        [community.id]: e instanceof Error ? e.message : "Action failed",
      }));
    } finally {
      setActionLoading((prev) => ({ ...prev, [community.id]: false }));
    }
  }, [communities, onCommunitiesChange]);

  if (communities.length === 0) {
    return (
      <div>
        <div className="flex justify-between items-center mb-4">
          <p className="text-sm text-text-3">No communities yet.</p>
          <button onClick={openCreate} className="flex items-center gap-1.5 text-sm bg-brand hover:bg-brand-hover text-white px-3 py-2 rounded-lg transition">
            <Plus size={14} /> New Community
          </button>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <p className="text-sm text-text-3">{communities.length} communities</p>
        <button
          onClick={openCreate}
          className="flex items-center gap-1.5 text-sm bg-brand hover:bg-brand-hover text-white px-3 py-2 rounded-lg transition"
        >
          <Plus size={14} />
          New Community
        </button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {communities.map((c) => (
          <CommunityCard
            key={c.id}
            community={c}
            isCollegeAdmin={isCollegeAdmin}
            actionLoading={actionLoading[c.id] ?? false}
            actionError={actionError[c.id] ?? ""}
            onEdit={() => openEdit(c)}
            onDelete={() => setDeletingId(c.id)}
            onAction={(action) => doAction(c, action)}
          />
        ))}
      </div>

      {/* Create / Edit Modal */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="bg-surface rounded-2xl shadow-2xl border border-divider w-full max-w-sm">
            <div className="flex items-center justify-between px-5 py-4 border-b border-divider">
              <h2 className="font-semibold text-text-1">{editingId ? "Edit Community" : "New Community"}</h2>
              <button onClick={() => setModalOpen(false)} className="text-text-3 hover:text-text-1">
                <X size={18} />
              </button>
            </div>
            <form onSubmit={submitModal} className="p-5 space-y-4">
              {modalError && (
                <div className="flex items-center gap-2 text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2 text-sm">
                  <AlertCircle size={14} />
                  {modalError}
                </div>
              )}
              <div>
                <label className="block text-sm font-medium text-text-1 mb-1">Name</label>
                <input
                  value={form.name}
                  onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                  required
                  placeholder="e.g. Computer Science Club"
                  className="w-full border border-divider rounded-lg px-3 py-2 text-sm text-text-1 bg-surface focus:outline-none focus:ring-2 focus:ring-brand-ring"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-text-1 mb-1">Type</label>
                <div className="flex gap-2">
                  {(["PUBLIC", "PRIVATE"] as CommunityType[]).map((t) => (
                    <button
                      key={t}
                      type="button"
                      onClick={() => setForm((f) => ({ ...f, type: t }))}
                      className={`flex-1 flex items-center justify-center gap-1.5 py-2 text-sm rounded-lg border transition ${
                        form.type === t
                          ? "border-brand bg-brand-light text-brand font-medium"
                          : "border-divider text-text-2 hover:border-brand"
                      }`}
                    >
                      {t === "PUBLIC" ? <Globe size={14} /> : <Lock size={14} />}
                      {t}
                    </button>
                  ))}
                </div>
              </div>
              <div className="flex justify-end gap-3 pt-1">
                <button type="button" onClick={() => setModalOpen(false)} className="px-4 py-2 text-sm text-text-2 border border-divider rounded-lg hover:bg-surface-2 transition">
                  Cancel
                </button>
                <button type="submit" disabled={modalLoading} className="flex items-center gap-2 px-4 py-2 text-sm bg-brand hover:bg-brand-hover disabled:bg-brand-disabled text-white rounded-lg transition">
                  {modalLoading && <Loader2 size={13} className="animate-spin" />}
                  {editingId ? "Save" : "Create"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete confirm */}
      {deletingId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="bg-surface rounded-2xl shadow-2xl border border-divider w-full max-w-sm p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-full bg-red-100 flex items-center justify-center text-red-600 shrink-0">
                <Trash2 size={18} />
              </div>
              <div>
                <p className="font-semibold text-text-1">Delete community?</p>
                <p className="text-sm text-text-3">This cannot be undone.</p>
              </div>
            </div>
            <div className="flex justify-end gap-3">
              <button onClick={() => setDeletingId(null)} className="px-4 py-2 text-sm border border-divider rounded-lg hover:bg-surface-2 transition">
                Cancel
              </button>
              <button
                onClick={confirmDelete}
                disabled={deleteLoading}
                className="flex items-center gap-2 px-4 py-2 text-sm bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white rounded-lg transition"
              >
                {deleteLoading && <Loader2 size={13} className="animate-spin" />}
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

interface CardProps {
  community: Community;
  isCollegeAdmin: boolean;
  actionLoading: boolean;
  actionError: string;
  onEdit: () => void;
  onDelete: () => void;
  onAction: (action: "join" | "cancel") => void;
}

function CommunityCard({ community: c, isCollegeAdmin, actionLoading, actionError, onEdit, onDelete, onAction }: CardProps) {
  return (
    <div className="bg-surface border border-divider rounded-xl p-4 flex flex-col gap-3">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="flex items-center gap-1.5 min-w-0">
            {c.type === "PRIVATE" ? (
              <Lock size={13} className="text-text-3 shrink-0" />
            ) : (
              <Globe size={13} className="text-text-3 shrink-0" />
            )}
            <h3 className="font-semibold text-text-1 text-sm truncate">{c.name}</h3>
          </div>
          <p className="text-xs text-text-3 mt-0.5">{c.member_count ?? 0} members · {c.post_count ?? 0} posts</p>
        </div>
        <div className="flex gap-1 shrink-0">
          <button onClick={onEdit} title="Edit" className="p-1.5 text-text-3 hover:text-brand hover:bg-brand-light rounded-md transition">
            <Pencil size={14} />
          </button>
          <button onClick={onDelete} title="Delete" className="p-1.5 text-text-3 hover:text-red-600 hover:bg-red-50 rounded-md transition">
            <Trash2 size={14} />
          </button>
        </div>
      </div>

      {actionError && (
        <p className="text-xs text-red-600 flex items-center gap-1">
          <AlertCircle size={12} /> {actionError}
        </p>
      )}

      {/* Membership action */}
      {isCollegeAdmin ? (
        <span className="inline-flex items-center gap-1 text-xs font-medium text-accent-dark bg-accent-light px-2 py-1 rounded-full self-start">
          <ShieldCheck size={12} /> Admin
        </span>
      ) : c.is_member === true ? (
        <button
          onClick={() => onAction("cancel")}
          disabled={actionLoading}
          className="flex items-center gap-1.5 text-xs text-text-2 border border-divider rounded-lg px-2 py-1.5 hover:border-red-400 hover:text-red-600 hover:bg-red-50 transition self-start"
        >
          {actionLoading ? <Loader2 size={12} className="animate-spin" /> : <UserMinus size={12} />}
          Leave
        </button>
      ) : c.is_requested === true ? (
        <button
          onClick={() => onAction("cancel")}
          disabled={actionLoading}
          className="flex items-center gap-1.5 text-xs text-amber-700 border border-amber-300 bg-amber-50 rounded-lg px-2 py-1.5 hover:bg-amber-100 transition self-start"
        >
          {actionLoading ? <Loader2 size={12} className="animate-spin" /> : <Clock size={12} />}
          Pending — Cancel
        </button>
      ) : (
        <button
          onClick={() => onAction("join")}
          disabled={actionLoading}
          className="flex items-center gap-1.5 text-xs text-brand border border-brand rounded-lg px-2 py-1.5 hover:bg-brand-light transition self-start"
        >
          {actionLoading ? <Loader2 size={12} className="animate-spin" /> : c.type === "PRIVATE" ? <UserCheck size={12} /> : <UserPlus size={12} />}
          {c.type === "PRIVATE" ? "Request to join" : "Join"}
        </button>
      )}
    </div>
  );
}
