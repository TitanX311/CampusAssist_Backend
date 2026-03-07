"use client";

import { useEffect, useState, useCallback } from "react";
import { getCollegeUsers, CollegeUser } from "@/lib/api";
import { Users, Loader2, AlertCircle, ChevronLeft, ChevronRight, Mail } from "lucide-react";

interface Props {
  collegeId: string;
}

function Avatar({ name, picture }: { name: string | null; picture: string | null }) {
  if (picture) {
    return (
      <img
        src={picture}
        alt={name ?? "User"}
        className="w-9 h-9 rounded-full object-cover shrink-0"
      />
    );
  }
  const initials = name
    ? name.split(" ").map((p) => p[0]).slice(0, 2).join("").toUpperCase()
    : "?";
  return (
    <div className="w-9 h-9 rounded-full bg-blue-100 flex items-center justify-center text-blue-700 text-xs font-bold shrink-0 select-none">
      {initials}
    </div>
  );
}

export default function MembersTab({ collegeId }: Props) {
  const [users, setUsers] = useState<CollegeUser[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const PAGE_SIZE = 20;
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchUsers = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const data = await getCollegeUsers(collegeId, page, PAGE_SIZE);
      setUsers(data.items);
      setTotal(data.total);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load members");
    } finally {
      setLoading(false);
    }
  }, [collegeId, page]);

  useEffect(() => { fetchUsers(); }, [fetchUsers]);

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-base font-semibold text-slate-800">
          {total} Member{total !== 1 ? "s" : ""}
        </h2>
      </div>

      {error && (
        <div className="flex items-center gap-2 bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 mb-4 text-sm">
          <AlertCircle size={15} />
          {error}
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center h-40">
          <Loader2 size={24} className="animate-spin text-blue-500" />
        </div>
      ) : users.length === 0 ? (
        <div className="text-center py-16 bg-white rounded-2xl border border-dashed border-slate-200">
          <Users size={32} className="mx-auto text-slate-300 mb-3" />
          <p className="text-slate-500 text-sm">No members yet.</p>
          <p className="text-xs text-slate-400 mt-1">
            Users who join a community in this college will appear here.
          </p>
        </div>
      ) : (
        <>
          <div className="bg-white rounded-xl border border-slate-200 divide-y divide-slate-100">
            {users.map((u) => (
              <div key={u.user_id} className="flex items-center gap-3 px-4 py-3">
                <Avatar name={u.name} picture={u.picture} />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-slate-800 truncate">
                    {u.name ?? <span className="text-slate-400 italic">Unknown User</span>}
                  </p>
                  {u.email && (
                    <p className="text-xs text-slate-500 flex items-center gap-1 mt-0.5 truncate">
                      <Mail size={10} />
                      {u.email}
                    </p>
                  )}
                  {!u.email && (
                    <p className="text-xs text-slate-400 font-mono truncate mt-0.5">
                      {u.user_id}
                    </p>
                  )}
                </div>
                <div className="flex flex-col items-end gap-1 shrink-0">
                  {u.user_type && (
                    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                      u.user_type === "SUPER_ADMIN"
                        ? "bg-purple-50 text-purple-700"
                        : u.user_type === "COLLEGE"
                        ? "bg-blue-50 text-blue-700"
                        : "bg-slate-100 text-slate-600"
                    }`}>
                      {u.user_type}
                    </span>
                  )}
                  <p className="text-xs text-slate-400">
                    Joined {new Date(u.joined_at).toLocaleDateString()}
                  </p>
                </div>
              </div>
            ))}
          </div>

          {totalPages > 1 && (
            <div className="flex items-center justify-between mt-4 text-sm text-slate-600">
              <p className="text-xs text-slate-400">
                Page {page} of {totalPages} · {total} total
              </p>
              <div className="flex gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="flex items-center gap-1 px-3 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 disabled:opacity-40 transition"
                >
                  <ChevronLeft size={14} />
                  Prev
                </button>
                <button
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                  className="flex items-center gap-1 px-3 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 disabled:opacity-40 transition"
                >
                  Next
                  <ChevronRight size={14} />
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
