"use client";

import { useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { GraduationCap, LogOut, ShieldCheck, Loader2 } from "lucide-react";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { user, signOut, loading, isSuperAdmin } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!loading && !user) {
      router.replace("/login");
    }
  }, [user, loading, router]);

  if (loading || !user) {
    return (
      <div className="min-h-screen bg-app-bg flex items-center justify-center">
        <Loader2 size={28} className="animate-spin text-brand" />
      </div>
    );
  }

  function handleSignOut() {
    signOut();
    router.replace("/login");
  }

  const isAdminRoute = pathname.startsWith("/dashboard/admin");

  return (
    <div className="min-h-screen bg-app-bg flex flex-col">
      {/* Top Nav */}
      <header className="bg-surface border-b border-divider sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between gap-4">
          <Link href="/dashboard" className="flex items-center gap-2 text-brand font-semibold text-base shrink-0">
            <GraduationCap size={22} />
            <span>Campus Assist</span>
          </Link>

          <div className="flex items-center gap-3">
            {isSuperAdmin && !isAdminRoute && (
              <Link
                href="/dashboard/admin"
                className="hidden sm:flex items-center gap-1.5 text-xs font-medium bg-accent-light text-accent-dark px-3 py-1.5 rounded-full hover:opacity-80 transition"
              >
                <ShieldCheck size={14} />
                Super Admin
              </Link>
            )}
            {isSuperAdmin && isAdminRoute && (
              <Link
                href="/dashboard"
                className="hidden sm:flex items-center gap-1.5 text-xs font-medium bg-brand-light text-brand px-3 py-1.5 rounded-full hover:opacity-80 transition"
              >
                My Colleges
              </Link>
            )}
            <div className="hidden sm:flex flex-col items-end text-right leading-tight">
              <span className="text-xs font-medium text-text-1 truncate max-w-[160px]">{user.name ?? "Admin"}</span>
              <span className="text-[11px] text-text-3 truncate max-w-[160px]">{user.email}</span>
            </div>
            <button
              onClick={handleSignOut}
              title="Sign out"
              className="flex items-center gap-1.5 text-xs text-text-2 hover:text-red-600 transition px-2 py-1.5 rounded-lg hover:bg-red-50"
            >
              <LogOut size={15} />
              <span className="hidden sm:inline">Sign out</span>
            </button>
          </div>
        </div>
      </header>

      {/* Page content */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-6">
        {children}
      </main>
    </div>
  );
}
