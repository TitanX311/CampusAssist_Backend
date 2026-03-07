"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { createCollege } from "@/lib/api";

export default function NewCollegePage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [contactEmail, setContactEmail] = useState("");
  const [physicalAddress, setPhysicalAddress] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const college = await createCollege({
        name: name.trim(),
        contact_email: contactEmail.trim(),
        physical_address: physicalAddress.trim(),
      });
      router.push(`/colleges/${college.id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to create college");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <>
      <Link href="/colleges" className="back-link">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
          <path d="M19 12H5M12 19l-7-7 7-7" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
        Colleges
      </Link>

      <div className="page-header">
        <h1 className="page-title">New College</h1>
      </div>

      <div style={{ maxWidth: 480 }}>
        <div className="card">
          <form onSubmit={handleSubmit}>
            <div style={{ marginBottom: 18 }}>
              <label>
                Name <span style={{ color: "var(--text-muted)" }}>*</span>
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                placeholder="e.g. MIT"
                style={{ marginBottom: 0 }}
              />
            </div>

            <div style={{ marginBottom: 18 }}>
              <label>
                Contact email <span style={{ color: "var(--text-muted)" }}>*</span>
              </label>
              <input
                type="email"
                value={contactEmail}
                onChange={(e) => setContactEmail(e.target.value)}
                required
                placeholder="admin@college.edu"
                style={{ marginBottom: 0 }}
              />
            </div>

            <div style={{ marginBottom: 20 }}>
              <label>Physical address</label>
              <textarea
                value={physicalAddress}
                onChange={(e) => setPhysicalAddress(e.target.value)}
                placeholder="Street, city, state"
                rows={3}
                style={{ marginBottom: 0, resize: "vertical" }}
              />
            </div>

            {error && (
              <div style={{
                display: "flex", alignItems: "center", gap: 8,
                padding: "10px 14px",
                background: "rgba(239,68,68,0.08)", border: "1px solid rgba(239,68,68,0.2)",
                borderRadius: "var(--radius-sm)",
                fontSize: 13, color: "#fca5a5", marginBottom: 16,
              }}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" style={{ flexShrink: 0 }}>
                  <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="1.75"/>
                  <path d="M12 8v4M12 16h.01" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round"/>
                </svg>
                {error}
              </div>
            )}

            <div style={{ display: "flex", gap: 8 }}>
              <button type="submit" disabled={submitting} className="btn btn-primary">
                {submitting ? (
                  <>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" style={{ animation: "spin 0.8s linear infinite" }}>
                      <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2.5" strokeDasharray="60" strokeDashoffset="20"/>
                    </svg>
                    Creating…
                  </>
                ) : "Create college"}
              </button>
              <Link href="/colleges" className="btn btn-ghost">Cancel</Link>
            </div>
          </form>
        </div>
      </div>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </>
  );
}