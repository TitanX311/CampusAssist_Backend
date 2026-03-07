"use client";

import { useEffect, useState } from "react";
import { getAdminStats, getAdminHealth } from "@/lib/api";
import type { StatsResponse, HealthResponse } from "@/types/api";

const statIcons: Record<string, React.ReactNode> = {
  Users: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
      <circle cx="9" cy="7" r="4" stroke="currentColor" strokeWidth="1.75"/>
      <path d="M3 21v-2a4 4 0 014-4h4a4 4 0 014 4v2" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round"/>
      <path d="M16 3.13a4 4 0 010 7.75M21 21v-2a4 4 0 00-3-3.87" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round"/>
    </svg>
  ),
  Colleges: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
      <path d="M3 21h18M3 10h18M5 6l7-3 7 3M4 10v11M20 10v11M8 14v3M12 14v3M16 14v3" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  ),
  Communities: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
      <circle cx="12" cy="12" r="3" stroke="currentColor" strokeWidth="1.75"/>
      <circle cx="19" cy="5" r="2" stroke="currentColor" strokeWidth="1.75"/>
      <circle cx="5" cy="5" r="2" stroke="currentColor" strokeWidth="1.75"/>
      <circle cx="5" cy="19" r="2" stroke="currentColor" strokeWidth="1.75"/>
      <circle cx="19" cy="19" r="2" stroke="currentColor" strokeWidth="1.75"/>
      <path d="M14.5 9.5L17 7M9.5 9.5L7 7M9.5 14.5L7 17M14.5 14.5L17 17" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round"/>
    </svg>
  ),
  Posts: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
      <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" stroke="currentColor" strokeWidth="1.75" strokeLinejoin="round"/>
      <path d="M14 2v6h6M16 13H8M16 17H8M10 9H8" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round"/>
    </svg>
  ),
  Comments: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
      <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" stroke="currentColor" strokeWidth="1.75" strokeLinejoin="round"/>
    </svg>
  ),
  Attachments: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
      <path d="M21.44 11.05l-9.19 9.19a6 6 0 01-8.49-8.49l9.19-9.19a4 4 0 015.66 5.66l-9.2 9.19a2 2 0 01-2.83-2.83l8.49-8.48" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  ),
};

const statColors: Record<string, string> = {
  Users: "#3b82f6",
  Colleges: "#8b5cf6",
  Communities: "#06b6d4",
  Posts: "#10b981",
  Comments: "#f59e0b",
  Attachments: "#f43f5e",
};

export default function DashboardPage() {
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [s, h] = await Promise.all([getAdminStats(), getAdminHealth()]);
        if (!cancelled) { setStats(s); setHealth(h); }
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "Failed to load");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  if (loading) return (
    <div className="state-loading">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" style={{animation:"spin 0.8s linear infinite"}}>
        <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" strokeDasharray="60" strokeDashoffset="20"/>
      </svg>
      Loading dashboard…
    </div>
  );
  if (error) return <div className="state-error">{error}</div>;

  const cards = stats ? [
    { label: "Users", value: stats.users, href: "/users" },
    { label: "Colleges", value: stats.colleges, href: "/colleges" },
    { label: "Communities", value: stats.communities, href: "/communities" },
    { label: "Posts", value: stats.posts, href: "/posts" },
    { label: "Comments", value: stats.comments, href: "/comments" },
    { label: "Attachments", value: stats.attachments, href: "/attachments" },
  ] : [];

  return (
    <>
      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
        @keyframes fadeUp {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .stat-card {
          background: var(--bg-surface);
          border: 1px solid var(--border);
          border-radius: var(--radius);
          padding: 20px;
          text-decoration: none;
          color: inherit;
          display: block;
          transition: border-color 0.2s, transform 0.15s, box-shadow 0.2s;
          animation: fadeUp 0.4s ease both;
          position: relative;
          overflow: hidden;
        }
        .stat-card::before {
          content: '';
          position: absolute; top: 0; left: 0; right: 0; height: 2px;
          background: var(--card-accent);
          opacity: 0; transition: opacity 0.2s;
        }
        .stat-card:hover {
          border-color: var(--card-accent-border);
          transform: translateY(-2px);
          box-shadow: 0 8px 24px rgba(0,0,0,0.3);
        }
        .stat-card:hover::before { opacity: 1; }
        .stat-icon {
          width: 36px; height: 36px; border-radius: 8px;
          display: flex; align-items: center; justify-content: center;
          margin-bottom: 14px;
          background: var(--card-icon-bg);
          color: var(--card-accent);
        }
        .stat-label {
          font-size: 11px; font-weight: 600; letter-spacing: 0.06em;
          text-transform: uppercase; color: var(--text-muted);
          margin-bottom: 6px;
        }
        .stat-value {
          font-family: 'Lora', serif;
          font-size: 30px; font-weight: 600; color: var(--text-primary);
          letter-spacing: -0.04em; line-height: 1;
        }
        .health-card {
          background: var(--bg-surface);
          border: 1px solid var(--border);
          border-radius: var(--radius);
          overflow: hidden; margin-bottom: 24px;
        }
        .health-header {
          display: flex; align-items: center; justify-content: space-between;
          padding: 14px 20px;
          border-bottom: 1px solid var(--border);
          background: var(--bg-elevated);
        }
        .health-title {
          font-size: 13px; font-weight: 600; color: var(--text-primary);
          display: flex; align-items: center; gap: 8px;
        }
        .health-status-dot {
          width: 7px; height: 7px; border-radius: 50%;
          background: var(--success); box-shadow: 0 0 6px var(--success);
          animation: pulse 2s ease-in-out infinite;
        }
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
        .health-status-dot.bad { background: var(--danger); box-shadow: 0 0 6px var(--danger); }
        .health-services {
          display: flex; flex-wrap: wrap; gap: 0;
        }
        .health-service {
          padding: 10px 20px;
          border-right: 1px solid var(--border);
          font-size: 12.5px;
        }
        .health-service:last-child { border-right: none; }
        .health-service-name { color: var(--text-muted); margin-bottom: 2px; }
        .health-service-val { color: var(--text-primary); font-weight: 500; }
        .health-service-val.ok { color: #4ade80; }
        .health-service-val.bad { color: #f87171; }
      `}</style>

      <div className="page-header">
        <h1 className="page-title">Overview</h1>
        {stats?.timestamp && (
          <span style={{ fontSize: 12, color: "var(--text-muted)" }}>
            Updated {new Date(stats.timestamp).toLocaleTimeString()}
          </span>
        )}
      </div>

      {/* Health */}
      {health && (
        <div className="health-card">
          <div className="health-header">
            <div className="health-title">
              <span className={`health-status-dot${health.status !== "ok" ? " bad" : ""}`} />
              System Health
            </div>
            <span style={{ fontSize: 12, color: health.status === "ok" ? "#4ade80" : "#f87171", fontWeight: 600 }}>
              {health.status?.toUpperCase()}
            </span>
          </div>
          {health.services && (
            <div className="health-services">
              {Object.entries(health.services).map(([name, s]) => (
                <div key={name} className="health-service">
                  <div className="health-service-name">{name}</div>
                  <div className={`health-service-val${s.status === "ok" ? " ok" : " bad"}`}>
                    {s.status}
                    {s.latency_ms != null && (
                      <span style={{ color: "var(--text-muted)", fontWeight: 400 }}> · {s.latency_ms}ms</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Stat Cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))", gap: 12 }}>
        {cards.map(({ label, value, href }, i) => {
          const color = statColors[label] ?? "#3b82f6";
          return (
            <a
              key={label}
              href={href}
              className="stat-card"
              style={{
                "--card-accent": color,
                "--card-accent-border": `${color}40`,
                "--card-icon-bg": `${color}18`,
                animationDelay: `${i * 0.05}s`,
              } as React.CSSProperties}
            >
              <div className="stat-icon">{statIcons[label]}</div>
              <div className="stat-label">{label}</div>
              <div className="stat-value">{value >= 0 ? value.toLocaleString() : "—"}</div>
            </a>
          );
        })}
      </div>
    </>
  );
}