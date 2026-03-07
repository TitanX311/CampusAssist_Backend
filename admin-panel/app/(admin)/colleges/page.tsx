"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { getAdminColleges, deleteAdminCollege, getCollegeCommunities } from "@/lib/api";
import type { CollegeResponse } from "@/types/api";

const PAGE_SIZE = 20;

interface CollegeWithCommunityCount extends CollegeResponse {
  communityCount: number;
}

export default function CollegesPage() {
  const router = useRouter();
  const [data, setData] = useState<{ items: CollegeWithCommunityCount[]; total: number; page: number } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);

  const load = async () => {
    setLoading(true);
    try {
      const collegesRes = await getAdminColleges(page, PAGE_SIZE);
      const itemsWithCounts = await Promise.all(
        collegesRes.items.map(async (college) => {
          try {
            const res = await getCollegeCommunities(college.id, 1, 100);
            return { ...college, communityCount: res.total || res.items?.length || 0 };
          } catch {
            return { ...college, communityCount: 0 };
          }
        })
      );
      setData({ items: itemsWithCounts, total: collegesRes.total, page: collegesRes.page });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  };

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { load(); }, [page]);

  async function handleDelete(college: CollegeResponse) {
    if (!confirm(`Delete college "${college.name}"? This cannot be undone.`)) return;
    try {
      await deleteAdminCollege(college.id);
      setData((d) => d ? { ...d, items: d.items.filter((c) => c.id !== college.id), total: d.total - 1 } : null);
    } catch (e) {
      alert(e instanceof Error ? e.message : "Delete failed");
    }
  }

  if (loading && !data) return <div className="state-loading">Loading colleges…</div>;
  if (error) return <div className="state-error">{error}</div>;
  if (!data) return null;

  const totalPages = Math.ceil(data.total / PAGE_SIZE) || 1;

  return (
    <>
      <div className="page-header">
        <h1 className="page-title">Colleges</h1>
        <Link href="/colleges/new" className="btn btn-primary">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
            <path d="M12 5v14M5 12h14" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
          </svg>
          New College
        </Link>
      </div>

      <div className="card table-wrap">
        <table>
          <thead>
            <tr>
              <th>College</th>
              <th>Contact</th>
              <th>Admins</th>
              <th>Communities</th>
              <th>Created</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {data.items.map((c) => (
              <tr key={c.id} style={{ cursor: "pointer" }} onClick={() => router.push(`/colleges/${c.id}`)}>
                <td>
                  <div>
                    <div style={{ fontWeight: 600, fontSize: 13.5 }}>
                      <Link href={`/colleges/${c.id}`} onClick={(e) => e.stopPropagation()} style={{ color: "var(--text-primary)", textDecoration: "none" }}>
                        {c.name}
                      </Link>
                    </div>
                    {c.physical_address && (
                      <div style={{ fontSize: 11.5, color: "var(--text-muted)", marginTop: 2, maxWidth: 200, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                        {c.physical_address}
                      </div>
                    )}
                  </div>
                </td>
                <td style={{ fontSize: 12.5, color: "var(--text-secondary)" }}>{c.contact_email}</td>
                <td>
                  <span style={{ fontSize: 13.5, fontWeight: 600 }}>
                    {Array.isArray(c.admin_users) ? c.admin_users.length : 0}
                  </span>
                </td>
                <td>
                  <span style={{ fontSize: 13.5, fontWeight: 600 }}>{c.communityCount}</span>
                </td>
                <td style={{ fontSize: 12, color: "var(--text-muted)" }}>
                  {new Date(c.created_at).toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" })}
                </td>
                <td onClick={(e) => e.stopPropagation()}>
                  <div style={{ display: "flex", gap: 6 }}>
                    <Link href={`/colleges/${c.id}`} className="btn btn-ghost" style={{ padding: "5px 10px", fontSize: 12 }}>
                      View
                    </Link>
                    <button type="button" className="btn btn-danger" style={{ padding: "5px 10px", fontSize: 12 }} onClick={(e) => { e.stopPropagation(); handleDelete(c); }}>
                      Delete
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
          <span className="pagination-info">Page {page} of {totalPages} · {data.total} total</span>
          <button className="btn btn-ghost" style={{ padding: "6px 12px" }} disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>Next →</button>
        </div>
      )}
    </>
  );
}