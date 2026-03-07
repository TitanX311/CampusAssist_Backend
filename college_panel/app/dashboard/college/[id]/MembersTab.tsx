"use client";

import { useEffect, useState, useCallback } from "react";
import { getCollegeUsers, CollegeUser } from "@/lib/api";
import {
  Users,
  ChevronLeft,
  ChevronRight,
  Loader2,
  AlertCircle,
} from "lucide-react";

const PAGE_SIZE = 20;

interface Props {
  collegeId: string;
}

const TYPE_LABELS: Record<string, string> = {
  USER: "User",
  COLLEGE: "College Admin",
  SUPER_ADMIN: "Super Admin",
};

const TYPE_STYLES: Record<string, string> = {
  USER: "bg-surface-2 text-text-2",
  COLLEGE: "bg-brand-light text-brand",
  SUPER_ADMIN: "bg-accent-light text-accent-dark",
};

export default function MembersTab({ collegeId }: Props) {
  const [members, setMembers] = useState<CollegeUser[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  const fetchPage = useCallback(async (p: number) => {
    setLoading(true);
    setError("");
    try {
      const res = await getCollegeUsers(collegeId, p, PAGE_SIZE);
      setMembers(res.items ?? []);
      setTotal(res.total ?? 0);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load members");
    } finally {
      setLoading(false);
    }
  }, [collegeId]);

  useEffect(() => {
    fetchPage(page);
  }, [fetchPage, page]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <Loader2 size={26} className="animate-spin text-brand" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center gap-2 text-red-600 bg-red-50 border border-red-200 rounded-xl p-4">
        <AlertCircle size={16} />
        {error}
        <button onClick={() => fetchPage(page)} className="ml-2 underline hover:no-underline text-sm">
          Retry
        </button>
      </div>
    );
  }

  if (members.length === 0 && page === 1) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-text-3">
        <Users size={36} className="mb-3 opacity-40" />
        <p className="text-text-2 font-medium">No members yet</p>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <p className="text-sm text-text-3">{total} total member{total !== 1 ? "s" : ""}</p>
      </div>

      <div className="border border-divider rounded-xl overflow-hidden">
        <ul className="divide-y divide-divider">
          {members.map((m) => {
            const typeLabel = m.user_type ? (TYPE_LABELS[m.user_type] ?? m.user_type) : null;
            const typeStyle = m.user_type ? (TYPE_STYLES[m.user_type] ?? "bg-surface-2 text-text-2") : "";
            return (
              <li key={m.user_id} className="flex items-center justify-between gap-3 px-4 py-3 bg-surface">
                <div className="flex items-center gap-3 min-w-0">
                  {m.picture ? (
                    <img
                      src={m.picture}
                      alt={m.name ?? "Member"}
                      className="w-9 h-9 rounded-full object-cover shrink-0 bg-surface-2"
                    />
                  ) : (
                    <div className="w-9 h-9 rounded-full bg-brand-light flex items-center justify-center text-brand font-bold text-sm shrink-0">
                      {(m.name ?? "?")[0].toUpperCase()}
                    </div>
                  )}
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-text-1 truncate">{m.name ?? "Unknown"}</p>
                    <p className="text-xs text-text-3 truncate">{m.email ?? m.user_id}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  {typeLabel && (
                    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${typeStyle}`}>
                      {typeLabel}
                    </span>
                  )}
                  <span className="text-xs text-text-3 hidden sm:block">
                    {m.joined_at ? new Date(m.joined_at).toLocaleDateString() : ""}
                  </span>
                </div>
              </li>
            );
          })}
        </ul>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between mt-4">
          <button
            disabled={page <= 1}
            onClick={() => setPage((p) => p - 1)}
            className="flex items-center gap-1 text-sm text-text-2 border border-divider rounded-lg px-3 py-1.5 hover:bg-surface-2 disabled:opacity-40 disabled:cursor-not-allowed transition"
          >
            <ChevronLeft size={14} /> Prev
          </button>
          <span className="text-sm text-text-3">
            Page {page} of {totalPages}
          </span>
          <button
            disabled={page >= totalPages}
            onClick={() => setPage((p) => p + 1)}
            className="flex items-center gap-1 text-sm text-text-2 border border-divider rounded-lg px-3 py-1.5 hover:bg-surface-2 disabled:opacity-40 disabled:cursor-not-allowed transition"
          >
            Next <ChevronRight size={14} />
          </button>
        </div>
      )}
    </div>
  );
}
