"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { GraduationCap, Lock, Mail, AlertCircle, Loader2 } from "lucide-react";

export default function LoginPage() {
  const { signIn } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await signIn(email, password);
      router.replace("/dashboard");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Login failed. Check your credentials.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-brand-light via-white to-[#EEF0FF] flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-brand text-white mb-4 shadow-lg">
            <GraduationCap size={32} />
          </div>
          <h1 className="text-2xl font-bold text-text-1">Campus Assist</h1>
          <p className="text-text-2 mt-1">College Admin Panel</p>
        </div>

        <div className="bg-surface rounded-2xl shadow-xl border border-divider p-8">
          <h2 className="text-xl font-semibold text-text-1 mb-6">Sign in</h2>

          {error && (
            <div className="flex items-center gap-2 bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 mb-5 text-sm">
              <AlertCircle size={16} className="shrink-0" />
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-text-1 mb-1.5">Email address</label>
              <div className="relative">
                <Mail size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-3" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@college.edu"
                  required
                  autoComplete="email"
                  className="w-full pl-10 pr-4 py-2.5 border border-divider rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-ring focus:border-transparent bg-surface text-text-1 placeholder:text-text-3"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-text-1 mb-1.5">Password</label>
              <div className="relative">
                <Lock size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-3" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  autoComplete="current-password"
                  className="w-full pl-10 pr-4 py-2.5 border border-divider rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-ring focus:border-transparent bg-surface text-text-1 placeholder:text-text-3"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 bg-brand hover:bg-brand-hover disabled:bg-brand-disabled text-white font-medium py-2.5 rounded-lg transition text-sm"
            >
              {loading && <Loader2 size={16} className="animate-spin" />}
              {loading ? "Signing in…" : "Sign in"}
            </button>
          </form>
        </div>

        <p className="text-center text-xs text-text-3 mt-6">
          Only college admin and super-admin accounts can access this panel.
        </p>
      </div>
    </div>
  );
}
