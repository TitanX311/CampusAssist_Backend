"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { getAdminCollege, deleteAdminCollege, getCollegeCommunities } from "@/lib/api";
import type { CollegeResponse, CommunityResponse } from "@/types/api";

interface CollegeStats {
  admin_count: number;
  community_count: number;
  member_count: number;
}

export default function CollegeDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;
  const [college, setCollege] = useState<CollegeResponse | null>(null);
  const [stats, setStats] = useState<CollegeStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const collegeData = await getAdminCollege(id);
        setCollege(collegeData);
        const communitiesRes = await getCollegeCommunities(id, 1, 1000);
        const memberSet = new Set<string>();
        communitiesRes.items.forEach((community: CommunityResponse) => {
          community.member_users?.forEach((userId: string) => memberSet.add(userId));
        });
        setStats({
          admin_count: collegeData.admin_users?.length || 0,
          community_count: communitiesRes.total,
          member_count: memberSet.size,
        });
      } catch (e) {
        setError(e instanceof Error ? e.message : "Not found");
      } finally {
        setLoading(false);
      }
    })();
  }, [id]);

  async function handleDelete() {
    if (!college || !confirm(`Delete "${college.name}"? This cannot be undone.`)) return;
    try {
      await deleteAdminCollege(college.id);
      router.push("/colleges");
    } catch (e) {
      alert(e instanceof Error ? e.message : "Delete failed");
    }
  }

  if (loading) return <div className="state-loading">Loading…</div>;
  if (error) return <div className="state-error">{error}</div>;
  if (!college || !stats) return null;

  return (
    <>
      <Link href="/colleges" className="back-link">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
          <path d="M19 12H5M12 19l-7-7 7-7" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
        Colleges
      </Link>

      <div className="page-header">
        <h1 className="page-title">{college.name}</h1>
      </div>

      {/* Stat strip */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 10, marginBottom: 20 }}>
        {[
          { label: "Admins", value: stats.admin_count },
          { label: "Communities", value: stats.community_count },
          { label: "Members", value: stats.member_count },
        ].map(({ label, value }) => (
          <div key={label} style={{
            background: "var(--bg-surface)", border: "1px solid var(--border)",
            borderRadius: "var(--radius)", padding: "16px 20px",
          }}>
            <div style={{ fontSize: 11, fontWeight: 600, color: "var(--text-muted)", letterSpacing: "0.06em", textTransform: "uppercase", marginBottom: 6 }}>{label}</div>
            <div style={{ fontFamily: "'Lora', serif", fontSize: 28, fontWeight: 600, color: "var(--text-primary)", letterSpacing: "-0.04em" }}>{value.toLocaleString()}</div>
          </div>
        ))}
      </div>

      {/* Details */}
      <div className="detail-card">
        <div className="detail-row">
          <span className="detail-label">Contact email</span>
          <span className="detail-value">
            <a href={`mailto:${college.contact_email}`}>{college.contact_email}</a>
          </span>
        </div>
        <div className="detail-row">
          <span className="detail-label">Physical address</span>
          <span className="detail-value" style={{ color: college.physical_address ? "var(--text-primary)" : "var(--text-muted)" }}>
            {college.physical_address || "—"}
          </span>
        </div>
        <div className="detail-row">
          <span className="detail-label">Created</span>
          <span className="detail-value" style={{ color: "var(--text-secondary)" }}>
            {new Date(college.created_at).toLocaleString()}
          </span>
        </div>
        <div className="detail-row">
          <span className="detail-label">Last updated</span>
          <span className="detail-value" style={{ color: "var(--text-secondary)" }}>
            {new Date(college.updated_at).toLocaleString()}
          </span>
        </div>
      </div>

      <button type="button" className="btn btn-danger" onClick={handleDelete}>
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
          <path d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
        Delete college
      </button>
    </>
  );
}