"use client";

import { useEffect, useState } from "react";
import { getAdminUsers, updateUserType, updateUserActive } from "@/lib/api";
import type { AdminUserResponse } from "@/types/api";

const PAGE_SIZE = 20;

function UserAvatar({ email, name }: { email: string; name?: string | null }) {
  const initial = (name?.[0] ?? email[0]).toUpperCase();
  const colors = ["#3b82f6","#8b5cf6","#06b6d4","#10b981","#f59e0b","#f43f5e","#ec4899"];
  const color = colors[initial.charCodeAt(0) % colors.length];
  return (
    <div style={{
      width: 28, height: 28, borderRadius: "50%",
      background: `${color}22`, border: `1px solid ${color}44`,
      display: "flex", alignItems: "center", justifyContent: "center",
      fontSize: 11, fontWeight: 700, color, flexShrink: 0,
    }}>
      {initial}
    </div>
  );
}

export default function UsersPage() {
  const [data, setData] = useState<{ items: AdminUserResponse[]; total: number; page: number } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [updating, setUpdating] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    getAdminUsers(page, PAGE_SIZE)
      .then((res) => { if (!cancelled) setData({ items: res.items, total: res.total, page: res.page }); })
      .catch((e) => { if (!cancelled) setError(e instanceof Error ? e.message : "Failed to load"); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [page]);

  async function handleTypeChange(userId: string, type: "USER" | "COLLEGE" | "SUPER_ADMIN") {
    setUpdating(userId);
    try {
      await updateUserType(userId, type);
      if (data) setData({ ...data, items: data.items.map((u) => u.id === userId ? { ...u, type } : u) });
    } catch (e) {
      alert(e instanceof Error ? e.message : "Update failed");
    } finally {
      setUpdating(null);
    }
  }

  async function handleActiveChange(userId: string, isActive: boolean) {
    setUpdating(userId);
    try {
      await updateUserActive(userId, isActive);
      if (data) setData({ ...data, items: data.items.map((u) => u.id === userId ? { ...u, is_active: isActive } : u) });
    } catch (e) {
      alert(e instanceof Error ? e.message : "Update failed");
    } finally {
      setUpdating(null);
    }
  }

  if (loading && !data) return <div className="state-loading">Loading users…</div>;
  if (error) return <div className="state-error">{error}</div>;
  if (!data) return null;

  const totalPages = Math.ceil(data.total / PAGE_SIZE) || 1;

  return (
    <>
      <div className="page-header">
        <h1 className="page-title">Users</h1>
        <span style={{ fontSize: 12, color: "var(--text-muted)" }}>{data.total.toLocaleString()} total</span>
      </div>

      <div className="card table-wrap">
        <table>
          <thead>
            <tr>
              <th>User</th>
              <th>Role</th>
              <th>Status</th>
              <th>Joined</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {data.items.map((u) => (
              <tr key={u.id} style={{ opacity: updating === u.id ? 0.5 : 1, transition: "opacity 0.2s" }}>
                <td>
                  <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                    <UserAvatar email={u.email} name={u.name} />
                    <div>
                      <div style={{ fontWeight: 500, fontSize: 13.5 }}>{u.name ?? u.email}</div>
                      {u.name && <div style={{ fontSize: 11.5, color: "var(--text-muted)" }}>{u.email}</div>}
                    </div>
                  </div>
                </td>
                <td>
                  <span className={`badge badge-${u.type === "SUPER_ADMIN" ? "super" : u.type === "COLLEGE" ? "college" : "user"}`}>
                    {u.type === "SUPER_ADMIN" ? "Super Admin" : u.type === "COLLEGE" ? "College" : "User"}
                  </span>
                </td>
                <td>
                  <span className={u.is_active ? "badge badge-active" : "badge badge-inactive"}>
                    {u.is_active ? "Active" : "Inactive"}
                  </span>
                </td>
                <td style={{ fontSize: 12.5, color: "var(--text-muted)" }}>
                  {new Date(u.created_at).toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" })}
                </td>
                <td>
                  <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                    <select
                      value={u.type}
                      onChange={(e) => handleTypeChange(u.id, e.target.value as "USER" | "COLLEGE" | "SUPER_ADMIN")}
                      disabled={updating === u.id}
                    >
                      <option value="USER">User</option>
                      <option value="COLLEGE">College</option>
                      <option value="SUPER_ADMIN">Super Admin</option>
                    </select>
                    <button
                      type="button"
                      className={`btn ${u.is_active ? "btn-danger" : "btn-ghost"}`}
                      style={{ padding: "5px 10px", fontSize: 12 }}
                      onClick={() => handleActiveChange(u.id, !u.is_active)}
                      disabled={updating === u.id}
                    >
                      {u.is_active ? "Deactivate" : "Activate"}
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="pagination">
          <button className="btn btn-ghost" style={{ padding: "6px 12px" }} disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>← Prev</button>
          <span className="pagination-info">Page {page} of {totalPages}</span>
          <button className="btn btn-ghost" style={{ padding: "6px 12px" }} disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>Next →</button>
        </div>
      )}
    </>
  );
}