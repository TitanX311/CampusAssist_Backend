"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/store/AuthContext";

const nav = [
  {
    href: "/dashboard",
    label: "Dashboard",
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
        <rect x="3" y="3" width="7" height="7" rx="1.5" stroke="currentColor" strokeWidth="1.75"/>
        <rect x="14" y="3" width="7" height="7" rx="1.5" stroke="currentColor" strokeWidth="1.75"/>
        <rect x="3" y="14" width="7" height="7" rx="1.5" stroke="currentColor" strokeWidth="1.75"/>
        <rect x="14" y="14" width="7" height="7" rx="1.5" stroke="currentColor" strokeWidth="1.75"/>
      </svg>
    ),
  },
  {
    href: "/users",
    label: "Users",
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
        <circle cx="9" cy="7" r="4" stroke="currentColor" strokeWidth="1.75"/>
        <path d="M3 21v-2a4 4 0 014-4h4a4 4 0 014 4v2" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round"/>
        <path d="M16 3.13a4 4 0 010 7.75M21 21v-2a4 4 0 00-3-3.87" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round"/>
      </svg>
    ),
  },
  {
    href: "/colleges",
    label: "Colleges",
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
        <path d="M3 21h18M3 10h18M5 6l7-3 7 3M4 10v11M20 10v11M8 14v3M12 14v3M16 14v3" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"/>
      </svg>
    ),
  },
  {
    href: "/communities",
    label: "Communities",
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
        <circle cx="12" cy="12" r="3" stroke="currentColor" strokeWidth="1.75"/>
        <circle cx="19" cy="5" r="2" stroke="currentColor" strokeWidth="1.75"/>
        <circle cx="5" cy="5" r="2" stroke="currentColor" strokeWidth="1.75"/>
        <circle cx="5" cy="19" r="2" stroke="currentColor" strokeWidth="1.75"/>
        <circle cx="19" cy="19" r="2" stroke="currentColor" strokeWidth="1.75"/>
        <path d="M14.5 9.5L17 7M9.5 9.5L7 7M9.5 14.5L7 17M14.5 14.5L17 17" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round"/>
      </svg>
    ),
  },
  {
    href: "/posts",
    label: "Posts",
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
        <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" stroke="currentColor" strokeWidth="1.75" strokeLinejoin="round"/>
        <path d="M14 2v6h6M16 13H8M16 17H8M10 9H8" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round"/>
      </svg>
    ),
  },
  {
    href: "/comments",
    label: "Comments",
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
        <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" stroke="currentColor" strokeWidth="1.75" strokeLinejoin="round"/>
      </svg>
    ),
  },
  {
    href: "/attachments",
    label: "Attachments",
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
        <path d="M21.44 11.05l-9.19 9.19a6 6 0 01-8.49-8.49l9.19-9.19a4 4 0 015.66 5.66l-9.2 9.19a2 2 0 01-2.83-2.83l8.49-8.48" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"/>
      </svg>
    ),
  },
];

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, loading, logout } = useAuth();

  if (loading) {
    return (
      <div style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "#0d0f14",
        fontFamily: "'Geist', sans-serif",
      }}>
        <div style={{ textAlign: "center" }}>
          <div style={{
            width: 32, height: 32,
            border: "2px solid rgba(255,255,255,0.1)",
            borderTopColor: "#3b82f6",
            borderRadius: "50%",
            animation: "spin 0.8s linear infinite",
            margin: "0 auto 12px",
          }} />
          <p style={{ color: "rgba(255,255,255,0.3)", fontSize: 13 }}>Loading…</p>
        </div>
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </div>
    );
  }

  if (!user || user.type !== "SUPER_ADMIN") {
    router.replace("/login");
    return null;
  }

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Geist:wght@300;400;500;600;700&family=Lora:ital,wght@0,600;1,400&display=swap');

        *, *::before, *::after {
          box-sizing: border-box;
          -webkit-font-smoothing: antialiased;
          -moz-osx-font-smoothing: grayscale;
        }

        :root {
          --bg-base: #0d0f14;
          --bg-surface: #13161d;
          --bg-elevated: #181c25;
          --bg-overlay: #1e2330;
          --border: rgba(255,255,255,0.07);
          --border-strong: rgba(255,255,255,0.12);
          --text-primary: #e8edf5;
          --text-secondary: rgba(255,255,255,0.5);
          --text-muted: rgba(255,255,255,0.28);
          --accent: #3b82f6;
          --accent-muted: rgba(59,130,246,0.12);
          --accent-border: rgba(59,130,246,0.3);
          --danger: #ef4444;
          --danger-muted: rgba(239,68,68,0.1);
          --success: #22c55e;
          --warning: #f59e0b;
          --sidebar-w: 240px;
          --header-h: 56px;
          --radius: 8px;
          --radius-sm: 6px;
        }

        body {
          margin: 0;
          background: var(--bg-base);
          color: var(--text-primary);
          font-family: 'Geist', -apple-system, sans-serif;
          font-size: 14px;
          line-height: 1.5;
        }

        /* SCROLLBAR */
        ::-webkit-scrollbar { width: 4px; height: 4px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.2); }

        /* LAYOUT */
        .al-shell { display: flex; flex-direction: column; min-height: 100vh; }

        /* HEADER */
        .al-header {
          position: sticky; top: 0; z-index: 50;
          height: var(--header-h);
          background: rgba(13,15,20,0.9);
          backdrop-filter: blur(16px);
          -webkit-backdrop-filter: blur(16px);
          border-bottom: 1px solid var(--border);
          display: flex; align-items: center;
          padding: 0 20px; gap: 16px;
        }

        .al-logo {
          display: flex; align-items: center; gap: 10px;
          text-decoration: none; flex-shrink: 0;
        }

        .al-logo-mark {
          width: 32px; height: 32px;
          background: linear-gradient(135deg, #2563eb, #1d4ed8);
          border-radius: var(--radius-sm);
          display: flex; align-items: center; justify-content: center;
          font-family: 'Lora', serif; font-size: 14px; font-weight: 600;
          color: #fff;
          box-shadow: 0 0 12px rgba(37,99,235,0.3);
          flex-shrink: 0;
        }

        .al-logo-text {
          display: flex; flex-direction: column; line-height: 1.15;
        }
        .al-logo-text span:first-child {
          font-size: 14px; font-weight: 600; color: var(--text-primary); letter-spacing: -0.01em;
        }
        .al-logo-text span:last-child {
          font-size: 10px; font-weight: 400; color: var(--text-muted); letter-spacing: 0.04em; text-transform: uppercase;
        }

        .al-header-sep { flex: 1; }

        .al-header-actions { display: flex; align-items: center; gap: 8px; }

        .al-user-chip {
          display: flex; align-items: center; gap: 8px;
          padding: 5px 10px 5px 5px;
          background: var(--bg-elevated);
          border: 1px solid var(--border);
          border-radius: 20px;
          cursor: default;
        }
        .al-user-avatar {
          width: 24px; height: 24px; border-radius: 50%;
          background: linear-gradient(135deg, #2563eb, #7c3aed);
          display: flex; align-items: center; justify-content: center;
          font-size: 10px; font-weight: 700; color: #fff;
          flex-shrink: 0;
        }
        .al-user-chip span {
          font-size: 12px; color: var(--text-secondary); max-width: 140px;
          overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
        }

        /* BODY */
        .al-body { display: flex; flex: 1; overflow: hidden; }

        /* SIDEBAR */
        .al-sidebar {
          width: var(--sidebar-w); flex-shrink: 0;
          background: var(--bg-surface);
          border-right: 1px solid var(--border);
          display: flex; flex-direction: column;
          position: sticky; top: var(--header-h);
          height: calc(100vh - var(--header-h));
          overflow-y: auto;
        }

        .al-nav { padding: 12px 10px; flex: 1; }

        .al-nav-section {
          font-size: 10px; font-weight: 600; letter-spacing: 0.08em;
          text-transform: uppercase; color: var(--text-muted);
          padding: 0 8px; margin: 16px 0 6px;
        }
        .al-nav-section:first-child { margin-top: 4px; }

        .al-nav-link {
          display: flex; align-items: center; gap: 10px;
          padding: 8px 10px; border-radius: var(--radius-sm);
          text-decoration: none; color: var(--text-secondary);
          font-size: 13.5px; font-weight: 500;
          transition: all 0.15s ease;
          position: relative;
          border: 1px solid transparent;
          margin-bottom: 2px;
        }
        .al-nav-link:hover {
          color: var(--text-primary);
          background: var(--bg-elevated);
        }
        .al-nav-link.active {
          color: #60a5fa;
          background: var(--accent-muted);
          border-color: var(--accent-border);
        }
        .al-nav-link.active .al-nav-icon { color: #60a5fa; }
        .al-nav-icon { color: var(--text-muted); transition: color 0.15s; flex-shrink: 0; }
        .al-nav-link:hover .al-nav-icon { color: var(--text-secondary); }

        /* SIDEBAR FOOTER */
        .al-sidebar-footer {
          padding: 12px 10px;
          border-top: 1px solid var(--border);
        }

        .al-user-block {
          background: var(--bg-elevated);
          border: 1px solid var(--border);
          border-radius: var(--radius);
          padding: 10px 12px;
          margin-bottom: 8px;
        }
        .al-user-label { font-size: 10px; color: var(--text-muted); letter-spacing: 0.04em; text-transform: uppercase; margin-bottom: 3px; }
        .al-user-email { font-size: 12.5px; font-weight: 500; color: var(--text-primary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        .al-user-role {
          display: inline-flex; align-items: center; gap: 4px;
          margin-top: 5px; padding: 2px 7px;
          background: rgba(59,130,246,0.12); border: 1px solid rgba(59,130,246,0.25);
          border-radius: 10px; font-size: 10px; font-weight: 600;
          color: #60a5fa; letter-spacing: 0.04em; text-transform: uppercase;
        }

        .al-logout {
          width: 100%; padding: 8px 12px;
          background: transparent; border: 1px solid var(--border);
          border-radius: var(--radius-sm); color: var(--text-secondary);
          font-family: 'Geist', sans-serif; font-size: 13px; font-weight: 500;
          cursor: pointer; transition: all 0.15s;
          display: flex; align-items: center; justify-content: center; gap: 6px;
        }
        .al-logout:hover { background: var(--danger-muted); border-color: rgba(239,68,68,0.3); color: #fca5a5; }

        /* MAIN */
        .al-main {
          flex: 1; overflow: auto;
          background: var(--bg-base);
        }
        .al-main-inner {
          max-width: 1200px; margin: 0 auto;
          padding: 28px 28px;
        }

        /* GLOBAL TABLE STYLES */
        .card {
          background: var(--bg-surface);
          border: 1px solid var(--border);
          border-radius: var(--radius);
          padding: 20px;
          margin-bottom: 16px;
        }

        .table-wrap {
          padding: 0; overflow-x: auto;
        }

        table {
          width: 100%; border-collapse: collapse;
          font-size: 13.5px;
        }

        thead tr {
          border-bottom: 1px solid var(--border);
        }

        th {
          padding: 11px 16px; text-align: left;
          font-size: 11px; font-weight: 600;
          letter-spacing: 0.06em; text-transform: uppercase;
          color: var(--text-muted);
          background: var(--bg-elevated);
        }
        th:first-child { border-radius: 0; }

        td {
          padding: 12px 16px;
          color: var(--text-primary);
          border-bottom: 1px solid rgba(255,255,255,0.04);
          vertical-align: middle;
        }

        tbody tr:last-child td { border-bottom: none; }

        tbody tr {
          transition: background 0.1s;
        }
        tbody tr:hover { background: var(--bg-elevated); }

        /* BUTTONS */
        .btn {
          display: inline-flex; align-items: center; justify-content: center; gap: 6px;
          padding: 7px 14px; border-radius: var(--radius-sm);
          font-family: 'Geist', sans-serif; font-size: 13px; font-weight: 500;
          cursor: pointer; border: 1px solid transparent;
          transition: all 0.15s; white-space: nowrap;
          text-decoration: none;
        }
        .btn:disabled { opacity: 0.45; cursor: not-allowed; }

        .btn-primary {
          background: #2563eb; border-color: #2563eb; color: #fff;
          box-shadow: 0 1px 3px rgba(37,99,235,0.3);
        }
        .btn-primary:hover:not(:disabled) { background: #1d4ed8; border-color: #1d4ed8; box-shadow: 0 4px 12px rgba(37,99,235,0.35); }

        .btn-ghost {
          background: transparent; border-color: var(--border-strong); color: var(--text-secondary);
        }
        .btn-ghost:hover:not(:disabled) { background: var(--bg-elevated); color: var(--text-primary); border-color: var(--border-strong); }

        .btn-danger {
          background: transparent; border-color: rgba(239,68,68,0.3); color: #f87171;
        }
        .btn-danger:hover:not(:disabled) { background: var(--danger-muted); border-color: rgba(239,68,68,0.5); color: #fca5a5; }

        /* BADGES */
        .badge {
          display: inline-flex; align-items: center; gap: 4px;
          padding: 2px 8px; border-radius: 10px;
          font-size: 11px; font-weight: 600; letter-spacing: 0.03em;
        }
        .badge-public { background: rgba(34,197,94,0.1); color: #4ade80; border: 1px solid rgba(34,197,94,0.2); }
        .badge-private { background: rgba(245,158,11,0.1); color: #fbbf24; border: 1px solid rgba(245,158,11,0.2); }
        .badge-super { background: rgba(167,139,250,0.1); color: #c4b5fd; border: 1px solid rgba(167,139,250,0.25); }
        .badge-college { background: rgba(56,189,248,0.1); color: #7dd3fc; border: 1px solid rgba(56,189,248,0.25); }
        .badge-user { background: rgba(255,255,255,0.06); color: var(--text-secondary); border: 1px solid var(--border); }
        .badge-active { background: rgba(34,197,94,0.1); color: #4ade80; border: 1px solid rgba(34,197,94,0.2); }
        .badge-inactive { background: rgba(255,255,255,0.04); color: var(--text-muted); border: 1px solid var(--border); }

        /* PAGE TITLES */
        .page-header {
          display: flex; align-items: center; justify-content: space-between;
          flex-wrap: wrap; gap: 12px;
          margin-bottom: 20px;
        }
        .page-title {
          font-family: 'Lora', serif;
          font-size: 24px; font-weight: 600; color: var(--text-primary);
          letter-spacing: -0.03em; line-height: 1.2;
        }

        /* PAGINATION */
        .pagination {
          display: flex; align-items: center; gap: 8px;
          margin-top: 16px;
        }
        .pagination-info {
          font-size: 12px; color: var(--text-muted);
          padding: 0 8px;
        }

        /* FORM INPUTS */
        input[type="text"],
        input[type="email"],
        input[type="password"],
        textarea,
        select {
          width: 100%; padding: 9px 12px;
          background: var(--bg-elevated);
          border: 1px solid var(--border-strong);
          border-radius: var(--radius-sm);
          color: var(--text-primary);
          font-family: 'Geist', sans-serif; font-size: 14px;
          outline: none; transition: border-color 0.2s, box-shadow 0.2s;
          margin-bottom: 4px;
        }
        input:focus, textarea:focus, select:focus {
          border-color: rgba(59,130,246,0.5);
          box-shadow: 0 0 0 3px rgba(59,130,246,0.12);
        }
        input::placeholder, textarea::placeholder { color: var(--text-muted); }

        label {
          display: block; font-size: 12px; font-weight: 500;
          color: var(--text-secondary); margin-bottom: 6px; letter-spacing: 0.01em;
        }

        /* LOADING / ERROR STATES */
        .state-loading, .state-error {
          display: flex; align-items: center; gap: 8px;
          padding: 16px; font-size: 13px;
        }
        .state-loading { color: var(--text-muted); }
        .state-error { color: #fca5a5; }

        /* LINKS */
        a { color: #60a5fa; }
        a:hover { color: #93c5fd; }

        /* BACK LINK */
        .back-link {
          display: inline-flex; align-items: center; gap: 5px;
          font-size: 13px; color: var(--text-muted); text-decoration: none;
          margin-bottom: 16px; transition: color 0.15s;
        }
        .back-link:hover { color: var(--text-secondary); }

        /* DETAIL CARD */
        .detail-card {
          background: var(--bg-surface);
          border: 1px solid var(--border);
          border-radius: var(--radius);
          overflow: hidden; margin-bottom: 16px;
        }
        .detail-row {
          display: flex; padding: 13px 20px;
          border-bottom: 1px solid rgba(255,255,255,0.04);
          align-items: baseline; gap: 12px;
        }
        .detail-row:last-child { border-bottom: none; }
        .detail-label {
          font-size: 12px; font-weight: 500; color: var(--text-muted);
          letter-spacing: 0.03em; flex-shrink: 0; min-width: 140px;
        }
        .detail-value {
          font-size: 13.5px; color: var(--text-primary);
        }

        /* SELECT OVERRIDE */
        select {
          margin-bottom: 0; width: auto; padding: 5px 8px; font-size: 12.5px;
          cursor: pointer;
        }

        @media (max-width: 768px) {
          .al-sidebar { display: none; }
          .al-main-inner { padding: 16px; }
        }
      `}</style>

      <div className="al-shell">
        {/* HEADER */}
        <header className="al-header">
          <Link href="/dashboard" className="al-logo">
            <div className="al-logo-mark">CA</div>
            <div className="al-logo-text">
              <span>Campus Assist</span>
              <span>Admin Portal</span>
            </div>
          </Link>

          <div className="al-header-sep" />

          <div className="al-header-actions">
            <div className="al-user-chip">
              <div className="al-user-avatar">
                {user.email?.[0]?.toUpperCase() ?? "A"}
              </div>
              <span>{user.email}</span>
            </div>
          </div>
        </header>

        <div className="al-body">
          {/* SIDEBAR */}
          <aside className="al-sidebar">
            <nav className="al-nav">
              <div className="al-nav-section">Navigation</div>
              {nav.map(({ href, label, icon }) => {
                const isActive = pathname === href || pathname.startsWith(href + "/");
                return (
                  <Link
                    key={href}
                    href={href}
                    className={`al-nav-link${isActive ? " active" : ""}`}
                  >
                    <span className="al-nav-icon">{icon}</span>
                    {label}
                  </Link>
                );
              })}
            </nav>

            <div className="al-sidebar-footer">
              <div className="al-user-block">
                <div className="al-user-label">Signed in as</div>
                <div className="al-user-email">{user.email}</div>
                <div className="al-user-role">
                  <svg width="8" height="8" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                  </svg>
                  {user.type}
                </div>
              </div>
              <button
                type="button"
                className="al-logout"
                onClick={() => logout().then(() => router.replace("/login"))}
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                  <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4M16 17l5-5-5-5M21 12H9" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
                Sign out
              </button>
            </div>
          </aside>

          {/* MAIN CONTENT */}
          <main className="al-main">
            <div className="al-main-inner">
              {children}
            </div>
          </main>
        </div>
      </div>
    </>
  );
}