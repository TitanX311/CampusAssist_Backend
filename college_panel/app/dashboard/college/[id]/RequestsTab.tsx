"use client";

import { useState, useCallback } from "react";
import {
  Community,
  UserProfile,
  getPendingRequests,
  approveJoinRequest,
  rejectJoinRequest,
  getUserProfile,
} from "@/lib/api";
import {
  ChevronDown,
  ChevronRight,
  Lock,
  Loader2,
  AlertCircle,
  UserCheck,
  UserX,
  Users,
} from "lucide-react";

interface Props {
  communities: Community[]; // already filtered to PRIVATE
}

export default function RequestsTab({ communities }: Props) {
  if (communities.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-text-3">
        <Lock size={36} className="mb-3 opacity-40" />
        <p className="text-text-2 font-medium">No private communities</p>
        <p className="text-sm mt-1">Join requests only apply to private communities.</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {communities.map((c) => (
        <CommunityRequests key={c.id} community={c} />
      ))}
    </div>
  );
}

function CommunityRequests({ community }: { community: Community }) {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [requests, setRequests] = useState<string[]>([]);
  const [total, setTotal] = useState(0);
  const [profiles, setProfiles] = useState<Record<string, UserProfile | null>>({});
  const [actionLoading, setActionLoading] = useState<Record<string, boolean>>({});
  const [fetched, setFetched] = useState(false);

  const fetchRequests = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const data = await getPendingRequests(community.id);
      const userIds = data.requested_users ?? [];
      setRequests(userIds);
      setTotal(data.total ?? 0);

      // Fetch all profiles fresh — no stale closure issues
      const results = await Promise.allSettled(
        userIds.map((id) => getUserProfile(id))
      );
      const map: Record<string, UserProfile | null> = {};
      userIds.forEach((id, i) => {
        const result = results[i];
        map[id] = result.status === "fulfilled" ? result.value : null;
      });
      setProfiles(map);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load requests");
    } finally {
      setLoading(false);
      setFetched(true);
    }
  }, [community.id]);

  function handleToggle() {
    const willOpen = !open;
    setOpen(willOpen);
    if (willOpen && !fetched) {
      fetchRequests();
    }
  }

  async function handleApprove(userId: string) {
    setActionLoading((prev) => ({ ...prev, [userId]: true }));
    try {
      await approveJoinRequest(community.id, userId);
      setRequests((prev) => prev.filter((id) => id !== userId));
      setTotal((prev) => Math.max(0, prev - 1));
    } catch {
      // no-op — keep user in list
    } finally {
      setActionLoading((prev) => ({ ...prev, [userId]: false }));
    }
  }

  async function handleReject(userId: string) {
    setActionLoading((prev) => ({ ...prev, [userId]: true }));
    try {
      await rejectJoinRequest(community.id, userId);
      setRequests((prev) => prev.filter((id) => id !== userId));
      setTotal((prev) => Math.max(0, prev - 1));
    } catch {
      // no-op
    } finally {
      setActionLoading((prev) => ({ ...prev, [userId]: false }));
    }
  }

  return (
    <div className="border border-divider rounded-xl overflow-hidden">
      {/* Accordion header */}
      <button
        onClick={handleToggle}
        className="w-full flex items-center justify-between px-4 py-3 bg-surface hover:bg-surface-2 transition text-left"
      >
        <div className="flex items-center gap-2 min-w-0">
          <Lock size={14} className="text-text-3 shrink-0" />
          <span className="font-medium text-text-1 text-sm truncate">{community.name}</span>
          {fetched && total > 0 && (
            <span className="shrink-0 text-xs bg-brand text-white px-1.5 py-0.5 rounded-full font-medium">
              {total}
            </span>
          )}
        </div>
        <div className="shrink-0 text-text-3">
          {open ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
        </div>
      </button>

      {/* Accordion body */}
      {open && (
        <div className="border-t border-divider bg-surface">
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 size={22} className="animate-spin text-brand" />
            </div>
          ) : error ? (
            <div className="flex items-center gap-2 text-red-600 text-sm p-4">
              <AlertCircle size={14} />
              {error}
              <button onClick={fetchRequests} className="underline hover:no-underline ml-2">
                Retry
              </button>
            </div>
          ) : requests.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8 text-text-3">
              <Users size={24} className="mb-2 opacity-40" />
              <p className="text-sm">No pending requests</p>
            </div>
          ) : (
            <ul className="divide-y divide-divider">
              {requests.map((userId) => {
                const p = profiles[userId];
                const busy = actionLoading[userId] ?? false;
                return (
                  <li key={userId} className="flex items-center justify-between gap-3 px-4 py-3">
                    <div className="flex items-center gap-3 min-w-0">
                      {p?.picture ? (
                        <img
                          src={p.picture}
                          alt={p.name ?? "User"}
                          className="w-9 h-9 rounded-full object-cover shrink-0 bg-surface-2"
                        />
                      ) : (
                        <div className="w-9 h-9 rounded-full bg-brand-light flex items-center justify-center text-brand font-bold text-sm shrink-0">
                          {(p?.name ?? "?")[0].toUpperCase()}
                        </div>
                      )}
                      <div className="min-w-0">
                        <p className="text-sm font-medium text-text-1 truncate">{p?.name ?? "Unknown user"}</p>
                        <p className="text-xs text-text-3 truncate">{p?.email ?? userId}</p>
                      </div>
                    </div>
                    <div className="flex gap-2 shrink-0">
                      <button
                        onClick={() => handleApprove(userId)}
                        disabled={busy}
                        title="Approve"
                        className="flex items-center gap-1 text-xs font-medium text-white bg-brand hover:bg-brand-hover disabled:bg-brand-disabled px-3 py-1.5 rounded-lg transition"
                      >
                        {busy ? <Loader2 size={12} className="animate-spin" /> : <UserCheck size={13} />}
                        Approve
                      </button>
                      <button
                        onClick={() => handleReject(userId)}
                        disabled={busy}
                        title="Reject"
                        className="flex items-center gap-1 text-xs font-medium text-red-600 border border-red-300 hover:bg-red-50 disabled:opacity-50 px-3 py-1.5 rounded-lg transition"
                      >
                        {busy ? <Loader2 size={12} className="animate-spin" /> : <UserX size={13} />}
                        Reject
                      </button>
                    </div>
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
