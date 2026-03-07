"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/store/AuthContext";

export default function LoginPage() {
  const { user, login } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  if (user?.type === "SUPER_ADMIN") {
    router.replace("/dashboard");
    return null;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await login(email, password);
      router.replace("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400;0,600;1,400;1,600&family=Geist:wght@300;400;500;600&display=swap');

        /*
          TYPE SYSTEM
          Display / headings  → Lora (serif, optical character, italic contrast)
          UI / body / labels  → Geist (clean, optically-balanced, modern)

          Scale (Major Third — 1.25x):
            xs:   11px  (badges, legal)
            sm:   13px  (labels, captions)
            base: 15px  (body, inputs)
            md:   18px  (sub-headings)
            lg:   24px  (section titles)
            xl:   32px  (form title)
            2xl:  48px  (hero headline)

          Line heights:
            tight   1.1  — display text
            snug    1.35 — headings
            normal  1.55 — body
            relaxed 1.75 — long descriptions

          Letter-spacing:
            display  -0.03em  — large headings feel tighter
            heading  -0.02em
            body      0
            caps     +0.08em  — uppercase labels/badges need breathing room
        */

        *, *::before, *::after {
          -webkit-font-smoothing: antialiased;
          -moz-osx-font-smoothing: grayscale;
          text-rendering: optimizeLegibility;
        }

        .ca-root {
          min-height: 100vh;
          display: grid;
          grid-template-columns: 1fr 1fr;
          font-family: 'Geist', -apple-system, BlinkMacSystemFont, sans-serif;
          font-size: 15px;
          background: #08090c;
        }

        /* ── LEFT PANEL ── */
        .ca-left {
          position: relative;
          display: flex;
          flex-direction: column;
          justify-content: space-between;
          padding: 48px 56px;
          overflow: hidden;
          background: #08090c;
          border-right: 1px solid #161820;
        }

        .ca-left-bg {
          position: absolute;
          inset: 0;
          background:
            radial-gradient(ellipse 70% 50% at 20% 40%, rgba(99,179,237,0.07) 0%, transparent 60%),
            radial-gradient(ellipse 50% 60% at 80% 80%, rgba(56,139,253,0.05) 0%, transparent 55%);
          pointer-events: none;
        }

        .ca-grid-lines {
          position: absolute;
          inset: 0;
          background-image:
            linear-gradient(rgba(255,255,255,0.018) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255,255,255,0.018) 1px, transparent 1px);
          background-size: 56px 56px;
          pointer-events: none;
        }

        .ca-logo {
          position: relative;
          display: flex;
          align-items: center;
          gap: 12px;
          z-index: 1;
        }

        .ca-logo-mark {
          width: 36px;
          height: 36px;
          background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
          border-radius: 10px;
          display: flex;
          align-items: center;
          justify-content: center;
          box-shadow: 0 0 20px rgba(59,130,246,0.3);
          flex-shrink: 0;
        }

        .ca-logo-text {
          font-family: 'Geist', sans-serif;
          font-size: 15px;
          font-weight: 600;
          color: rgba(255,255,255,0.9);
          letter-spacing: -0.01em;
        }

        .ca-hero {
          position: relative;
          z-index: 1;
        }

        .ca-eyebrow {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          padding: 5px 12px;
          background: rgba(59,130,246,0.1);
          border: 1px solid rgba(59,130,246,0.2);
          border-radius: 20px;
          font-family: 'Geist', sans-serif;
          font-size: 11px;
          font-weight: 500;
          color: #60a5fa;
          letter-spacing: 0.08em;
          text-transform: uppercase;
          margin-bottom: 24px;
        }

        .ca-eyebrow-dot {
          width: 5px;
          height: 5px;
          background: #3b82f6;
          border-radius: 50%;
          animation: pulse 2s ease-in-out infinite;
        }

        @keyframes pulse {
          0%, 100% { opacity: 1; transform: scale(1); }
          50% { opacity: 0.5; transform: scale(0.8); }
        }

        .ca-headline {
          font-family: 'Lora', Georgia, serif;
          font-size: clamp(38px, 4vw, 52px);
          font-weight: 600;
          line-height: 1.1;
          letter-spacing: -0.03em;
          color: #f0f4f8;
          margin-bottom: 20px;
        }

        .ca-headline em {
          font-style: italic;
          font-weight: 400;
          color: #60a5fa;
        }

        .ca-desc {
          font-family: 'Geist', sans-serif;
          font-size: 15px;
          font-weight: 300;
          color: rgba(255,255,255,0.38);
          line-height: 1.75;
          max-width: 340px;
          letter-spacing: 0.01em;
        }

        .ca-stats {
          position: relative;
          z-index: 1;
          display: flex;
          gap: 32px;
        }

        .ca-stat-item {
          display: flex;
          flex-direction: column;
          gap: 4px;
        }

        .ca-stat-num {
          font-family: 'Lora', Georgia, serif;
          font-size: 28px;
          font-weight: 600;
          color: #f0f4f8;
          letter-spacing: -0.04em;
          line-height: 1;
        }

        .ca-stat-label {
          font-family: 'Geist', sans-serif;
          font-size: 11px;
          font-weight: 400;
          color: rgba(255,255,255,0.28);
          letter-spacing: 0.08em;
          text-transform: uppercase;
        }

        .ca-stat-divider {
          width: 1px;
          background: rgba(255,255,255,0.06);
          align-self: stretch;
        }

        /* ── RIGHT PANEL ── */
        .ca-right {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: 48px 56px;
          background: #0d0f14;
        }

        .ca-form-wrap {
          width: 100%;
          max-width: 360px;
          animation: slideUp 0.5s cubic-bezier(0.16,1,0.3,1) both;
        }

        @keyframes slideUp {
          from { opacity: 0; transform: translateY(20px); }
          to { opacity: 1; transform: translateY(0); }
        }

        .ca-form-header {
          margin-bottom: 36px;
        }

        .ca-badge {
          display: inline-flex;
          align-items: center;
          gap: 5px;
          padding: 4px 10px;
          background: rgba(255,255,255,0.04);
          border: 1px solid rgba(255,255,255,0.07);
          border-radius: 4px;
          font-family: 'Geist', sans-serif;
          font-size: 10px;
          font-weight: 500;
          color: rgba(255,255,255,0.32);
          letter-spacing: 0.1em;
          text-transform: uppercase;
          margin-bottom: 20px;
        }

        .ca-form-title {
          font-family: 'Lora', Georgia, serif;
          font-size: 34px;
          font-weight: 600;
          color: #f0f4f8;
          letter-spacing: -0.03em;
          margin-bottom: 8px;
          line-height: 1.1;
        }

        .ca-form-sub {
          font-family: 'Geist', sans-serif;
          font-size: 14px;
          font-weight: 300;
          color: rgba(255,255,255,0.32);
          line-height: 1.55;
          letter-spacing: 0.005em;
        }

        /* ── FIELDS ── */
        .ca-field {
          margin-bottom: 18px;
        }

        .ca-label {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 8px;
        }

        .ca-label-text {
          font-family: 'Geist', sans-serif;
          font-size: 13px;
          font-weight: 500;
          color: rgba(255,255,255,0.5);
          letter-spacing: 0.01em;
        }

        .ca-input-wrap {
          position: relative;
        }

        .ca-input-icon {
          position: absolute;
          left: 14px;
          top: 50%;
          transform: translateY(-50%);
          color: rgba(255,255,255,0.2);
          pointer-events: none;
          display: flex;
        }

        .ca-input {
          width: 100%;
          padding: 13px 14px 13px 42px;
          background: rgba(255,255,255,0.04);
          border: 1px solid rgba(255,255,255,0.08);
          border-radius: 10px;
          color: #f0f4f8;
          font-family: 'Geist', sans-serif;
          font-size: 14px;
          font-weight: 400;
          letter-spacing: 0.01em;
          outline: none;
          transition: border-color 0.2s, background 0.2s, box-shadow 0.2s;
        }

        .ca-input::placeholder {
          color: rgba(255,255,255,0.15);
          font-weight: 300;
          letter-spacing: 0.01em;
        }

        .ca-input-has-toggle {
          padding-right: 44px;
        }

        .ca-input:focus {
          border-color: rgba(59,130,246,0.5);
          background: rgba(59,130,246,0.05);
          box-shadow: 0 0 0 3px rgba(59,130,246,0.12);
        }

        .ca-toggle-btn {
          position: absolute;
          right: 14px;
          top: 50%;
          transform: translateY(-50%);
          background: none;
          border: none;
          cursor: pointer;
          color: rgba(255,255,255,0.2);
          padding: 0;
          display: flex;
          transition: color 0.2s;
        }

        .ca-toggle-btn:hover {
          color: rgba(255,255,255,0.5);
        }

        /* ── ERROR ── */
        .ca-error {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 11px 14px;
          background: rgba(239,68,68,0.08);
          border: 1px solid rgba(239,68,68,0.2);
          border-radius: 8px;
          margin-bottom: 18px;
          font-family: 'Geist', sans-serif;
          font-size: 13px;
          font-weight: 400;
          line-height: 1.45;
          color: #fca5a5;
          letter-spacing: 0.01em;
          animation: shake 0.4s cubic-bezier(0.36,0.07,0.19,0.97);
        }

        @keyframes shake {
          0%, 100% { transform: translateX(0); }
          20%, 60% { transform: translateX(-4px); }
          40%, 80% { transform: translateX(4px); }
        }

        /* ── SUBMIT ── */
        .ca-submit {
          width: 100%;
          padding: 14px 20px;
          background: #2563eb;
          border: 1px solid #3b82f6;
          border-radius: 10px;
          color: #fff;
          font-family: 'Geist', sans-serif;
          font-size: 14px;
          font-weight: 600;
          letter-spacing: 0.01em;
          cursor: pointer;
          transition: background 0.2s, transform 0.1s, box-shadow 0.2s, opacity 0.2s;
          box-shadow: 0 4px 20px rgba(37,99,235,0.3), inset 0 1px 0 rgba(255,255,255,0.1);
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          position: relative;
          overflow: hidden;
        }

        .ca-submit::before {
          content: '';
          position: absolute;
          inset: 0;
          background: linear-gradient(180deg, rgba(255,255,255,0.08) 0%, transparent 100%);
        }

        .ca-submit:hover:not(:disabled) {
          background: #1d4ed8;
          box-shadow: 0 6px 28px rgba(37,99,235,0.45);
        }

        .ca-submit:active:not(:disabled) {
          transform: scale(0.99);
        }

        .ca-submit:disabled {
          opacity: 0.55;
          cursor: not-allowed;
        }

        .ca-spinner {
          width: 16px;
          height: 16px;
          border: 2px solid rgba(255,255,255,0.25);
          border-top-color: #fff;
          border-radius: 50%;
          animation: spin 0.7s linear infinite;
          flex-shrink: 0;
        }

        @keyframes spin {
          to { transform: rotate(360deg); }
        }

        /* ── FOOTER ── */
        .ca-form-footer {
          margin-top: 28px;
          padding-top: 20px;
          border-top: 1px solid rgba(255,255,255,0.05);
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 6px;
          font-family: 'Geist', sans-serif;
          font-size: 11px;
          font-weight: 400;
          color: rgba(255,255,255,0.2);
          letter-spacing: 0.02em;
        }

        .ca-form-footer svg {
          color: rgba(255,255,255,0.15);
        }

        /* ── RESPONSIVE ── */
        @media (max-width: 768px) {
          .ca-root {
            grid-template-columns: 1fr;
          }
          .ca-left {
            display: none;
          }
          .ca-right {
            padding: 32px 24px;
          }
        }
      `}</style>

      <div className="ca-root">
        {/* ── LEFT PANEL ── */}
        <div className="ca-left">
          <div className="ca-left-bg" />
          <div className="ca-grid-lines" />

          <div className="ca-logo">
            <div className="ca-logo-mark">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </div>
            <span className="ca-logo-text">Campus Assist</span>
          </div>

          <div className="ca-hero">
            <div className="ca-eyebrow">
              <span className="ca-eyebrow-dot" />
              Admin Portal
            </div>
            <h1 className="ca-headline">
              Manage your<br />campus <em>smarter.</em>
            </h1>
            <p className="ca-desc">
              A unified admin panel for overseeing students, staff, resources and operations — all in one place.
            </p>
          </div>

          <div className="ca-stats">
            <div className="ca-stat-item">
              <span className="ca-stat-num">12k+</span>
              <span className="ca-stat-label">Students</span>
            </div>
            <div className="ca-stat-divider" />
            <div className="ca-stat-item">
              <span className="ca-stat-num">340+</span>
              <span className="ca-stat-label">Staff</span>
            </div>
            <div className="ca-stat-divider" />
            <div className="ca-stat-item">
              <span className="ca-stat-num">99.9%</span>
              <span className="ca-stat-label">Uptime</span>
            </div>
          </div>
        </div>

        {/* ── RIGHT PANEL ── */}
        <div className="ca-right">
          <div className="ca-form-wrap">
            <div className="ca-form-header">
              <div className="ca-badge">
                <svg width="10" height="10" viewBox="0 0 24 24" fill="none">
                  <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" fill="currentColor"/>
                </svg>
                Super Admin
              </div>
              <h2 className="ca-form-title">Welcome back.</h2>
              <p className="ca-form-sub">Sign in to access your admin dashboard.</p>
            </div>

            <form onSubmit={handleSubmit}>
              {/* Email */}
              <div className="ca-field">
                <div className="ca-label">
                  <span className="ca-label-text">Email address</span>
                </div>
                <div className="ca-input-wrap">
                  <span className="ca-input-icon">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                      <rect x="2" y="4" width="20" height="16" rx="2" stroke="currentColor" strokeWidth="1.8"/>
                      <path d="M2 7l10 7 10-7" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/>
                    </svg>
                  </span>
                  <input
                    type="email"
                    className="ca-input"
                    placeholder="admin@campus.edu"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    autoComplete="email"
                  />
                </div>
              </div>

              {/* Password */}
              <div className="ca-field">
                <div className="ca-label">
                  <span className="ca-label-text">Password</span>
                </div>
                <div className="ca-input-wrap">
                  <span className="ca-input-icon">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                      <rect x="3" y="11" width="18" height="11" rx="2" stroke="currentColor" strokeWidth="1.8"/>
                      <path d="M7 11V7a5 5 0 0110 0v4" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/>
                    </svg>
                  </span>
                  <input
                    type={showPassword ? "text" : "password"}
                    className="ca-input ca-input-has-toggle"
                    placeholder="••••••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    autoComplete="current-password"
                  />
                  <button
                    type="button"
                    className="ca-toggle-btn"
                    onClick={() => setShowPassword(!showPassword)}
                    aria-label={showPassword ? "Hide password" : "Show password"}
                  >
                    {showPassword ? (
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                        <path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19m-6.72-1.07a3 3 0 11-4.24-4.24" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/>
                        <line x1="1" y1="1" x2="23" y2="23" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/>
                      </svg>
                    ) : (
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" stroke="currentColor" strokeWidth="1.8"/>
                        <circle cx="12" cy="12" r="3" stroke="currentColor" strokeWidth="1.8"/>
                      </svg>
                    )}
                  </button>
                </div>
              </div>

              {/* Error */}
              {error && (
                <div className="ca-error">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" style={{flexShrink:0}}>
                    <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="1.8"/>
                    <line x1="12" y1="8" x2="12" y2="12" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/>
                    <line x1="12" y1="16" x2="12.01" y2="16" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                  </svg>
                  {error}
                </div>
              )}

              {/* Submit */}
              <button type="submit" disabled={submitting} className="ca-submit">
                {submitting ? (
                  <>
                    <span className="ca-spinner" />
                    Signing in…
                  </>
                ) : (
                  <>
                    Sign in to Dashboard
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                      <path d="M5 12h14M12 5l7 7-7 7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                  </>
                )}
              </button>
            </form>

            <div className="ca-form-footer">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none">
                <rect x="3" y="11" width="18" height="11" rx="2" stroke="currentColor" strokeWidth="1.8"/>
                <path d="M7 11V7a5 5 0 0110 0v4" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/>
              </svg>
              Access restricted to authorized super admins only
            </div>
          </div>
        </div>
      </div>
    </>
  );
}