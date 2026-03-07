"use client";

import { useEffect, useState, useCallback } from "react";
import {
  Community,
  PendingRequestsResponse,
  UserProfile,
  getPendingRequests,
  approveJoinRequest,
  rejectJoinRequest,
  getUserProfile,
} from "@/lib/api";
import {
  Bell,
  UserCheck,
  UserX,
  Loader2,
  AlertCircle,
  Lock,
  ChevronDown,
  ChevronRight,
  Mail,
} from "lucide-react";

interface Props {
  communities: Community[]; // already filtered to PRIVATE
  onRefresh: () => Promise<void>;
}

function RequestorAvatar({ profile }: { profile: UserProfile | null | undefined }) {
  if (profile?.picture) {
    return (
      <img
        src={profile.picture}
        alt={profile.name ?? "User"}
        className="w-8 h-8 rounded-full object-cover shrink-0"
      />
    );
  }
  const initials = profile?.name
    ? profile.name.split(" ").map((p) => p[0]).slice(0, 2).join("").toUpperCase()
    : profile?.email?.slice(0, 2).toUpperCase() ?? "?";
  return (
    <div className="w-8 h-8 rounded-full bg-slate-200 flex items-center justify-center text-slate-600 text-xs font-bold shrink-0 select-none">
      {initials}
    </div>
  );
}

export default function RequestsTab({ communities, onRefresh }: Props) {
  if (communities.length === 0) {
    return (
      <div className="text-center py-16 bg-white rounded-2xl border border-dashed border-slate-200">
        <Lock size={32} className="mx-auto text-slate-300 mb-3" />
        <p className="text-slate-500 text-sm">No private communities in this college.</p>
        <p className="text-xs text-slate-400 mt-1">
          Create a PRIVATE community to see join requests here.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {communities.map((c) => (
        <CommunityRequests key={c.id} community={c} onRefresh={onRefresh} />
      ))}
    </div>
  );
}

function CommunityRequests({
  community,
  onRefresh,
}: {
  community: Community;
  onRefresh: () => Promise<void>;
}) {
  const [open, setOpen] = useState(community.requested_users.length > 0);
  const [requests, setRequests] = useState<PendingRequestsResponse | null>(null);
  const [profiles, setProfiles] = useState<Record<string, UserProfile | null>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const fetchRequests = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const data = await getPendingRequests(community.id);
      setRequests(data);
      // Fetch profiles for any UUIDs we don't have yet
      const missing = data.requested_users.filter((id) => !(id in profiles));
      if (missing.length > 0) {
        const results = await Promise.all(
          missing.map((id) =>
            getUserProfile(id)
              .then((p) => ({ id, profile: p }))
              .catch(() => ({ id, profile: null }))
          )
        );
        setProfiles((prev) => {
          const next = { ...prev };
          for (const { id, profile } of results) next[id] = profile;
          return next;
        });
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load requests");
    } finally {
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [community.id]);

  useEffect(() => {
    if (open) fetchRequests();
  }, [open, fetchRequests]);

  async function handleApprove(userId: string) {
    setActionLoading(userId);
    try {
      await approveJoinRequest(community.id, userId);
      await fetchRequests();
      await onRefresh();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Action failed");
    } finally {
      setActionLoading(null);
    }
  }

  async function handleReject(userId: string) {
    setActionLoading(userId + "_reject");
    try {
      await rejectJoinRequest(community.id, userId);
      await fetchRequests();
      await onRefresh();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Action failed");
    } finally {
      setActionLoading(null);
    }
  }

  const pendingCount = community.requested_users.length;

  return (
    <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center justify-between px-4 py-3.5 text-sm hover:bg-slate-50 transition"
      >
        <div className="flex items-center gap-2 font-medium text-slate-800">
          <Lock size={14} className="text-amber-500" />
          {community.name}
          {pendingCount > 0 && (
            <span className="inline-flex items-center justify-center bg-amber-100 text-amber-700 text-xs font-semibold rounded-full px-1.5 min-w-[1.25rem] h-5">
              {pendingCount}
            </span>
          )}
        </div>
        {open ? <ChevronDown size={15} className="text-slate-400" /> : <ChevronRight size={15} className="text-slate-400" />}
      </button>

      {open && (
        <div className="border-t border-slate-100 px-4 py-3">
          {error && (
            <div className="flex items-center gap-2 bg-red-50 border border-red-200 text-red-700 rounded-lg px-3 py-2 mb-3 text-xs">
              <AlertCircle size={13} />
              {error}
            </div>
          )}

          {loading ? (
            <div className="flex items-center justify-center py-6">
              <Loader2 size={20} className="animate-spin text-blue-500" />
            </div>
          ) : requests && requests.requested_users.length > 0 ? (
            <ul className="space-y-2">
              {requests.requested_users.map((userId) => {
                const profile = profiles[userId];
                return (
                  <li
                    key={userId}
                    className="flex items-center justify-between gap-2 bg-slate-50 rounded-lg px-3 py-2.5"
                  >
                    <div className="flex items-center gap-2 min-w-0">
                      <RequestorAvatar profile={profile} />
                      <div className="min-w-0">
                        <p className="text-xs font-medium text-slate-800 truncate">
                          {profile?.name ?? (
                            <span className="text-slate-400 italic">Loading…</span>
                          )}
                        </p>
                        {profile?.email ? (
                          <p className="text-xs text-slate-500 flex items-center gap-0.5 truncate">
                            <Mail size={9} />
                            {profile.email}
                          </p>
                        ) : (
                          <p className="text-xs text-slate-400 font-mono truncate">{userId}</p>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center gap-1.5 shrink-0">
                      <button
                        onClick={() => handleApprove(userId)}
                        disabled={!!actionLoading}
                        className="flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium text-emerald-700 bg-emerald-50 hover:bg-emerald-100 rounded-lg transition disabled:opacity-50"
                      >
                        {actionLoading === userId ? (
                          <Loader2 size={11} className="animate-spin" />
                        ) : (
                          <UserCheck size={11} />
                        )}
                        Approve
                      </button>
                      <button
                        onClick={() => handleReject(userId)}
                        disabled={!!actionLoading}
                        className="flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium text-red-700 bg-red-50 hover:bg-red-100 rounded-lg transition disabled:opacity-50"
                      >
                        {actionLoading === userId + "_reject" ? (
                          <Loader2 size={11} className="animate-spin" />
                        ) : (
                          <UserX size={11} />
                        )}
                        Reject
                      </button>
                    </div>
                  </li>
                );
              })}
            </ul>
          ) : (
            <div className="flex items-center justify-center gap-2 py-6 text-slate-400 text-sm">
              <Bell size={16} />
              No pending requests
            </div>
          )}
        </div>
      )}
    </div>
  );
}
