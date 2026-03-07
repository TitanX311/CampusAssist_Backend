"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/store/AuthContext";
import { ThemeToggle } from "@/components";

const nav = [
  { href: "/dashboard", label: "Dashboard", icon: "📊" },
  { href: "/users", label: "Users", icon: "👥" },
  { href: "/colleges", label: "Colleges", icon: "🏫" },
  { href: "/communities", label: "Communities", icon: "👫" },
  { href: "/posts", label: "Posts", icon: "📝" },
  { href: "/comments", label: "Comments", icon: "💬" },
  { href: "/attachments", label: "Attachments", icon: "📎" },
];

export default function AdminLayout({
  children,
}: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, loading, logout } = useAuth();

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-bg-secondary dark:bg-dark-bg-primary">
        <div className="text-center">
          <div className="animate-spin inline-block w-8 h-8 border-3 border-border-primary dark:border-dark-border-primary border-t-primary-600 rounded-full mb-3" />
          <p className="text-text-secondary dark:text-dark-text-secondary">Loading…</p>
        </div>
      </div>
    );
  }

  if (!user || user.type !== "SUPER_ADMIN") {
    router.replace("/login");
    return null;
  }

  return (
    <div className="flex flex-col min-h-screen bg-bg-secondary dark:bg-dark-bg-primary">
      {/* Header */}
      <header className="sticky top-0 z-40 border-b border-border-primary dark:border-dark-border-primary bg-bg-primary dark:bg-dark-bg-secondary shadow-elevation-1">
        <div className="px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">
          {/* Logo */}
          <Link href="/dashboard" className="flex items-center gap-2.5 group flex-shrink-0">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-primary-600 to-primary-700 flex items-center justify-center text-white font-bold text-base shadow-sm group-hover:shadow-md transition-shadow">
              CA
            </div>
            <div className="hidden sm:block">
              <div className="text-base font-bold leading-tight text-text-primary dark:text-dark-text-primary">
                Campus
              </div>
              <div className="text-xs text-text-tertiary dark:text-dark-text-tertiary font-medium">
                Control
              </div>
            </div>
          </Link>

          {/* Spacer */}
          <div className="flex-1" />

          {/* Theme Toggle */}
          <ThemeToggle />
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <aside className="w-64 border-r border-border-primary dark:border-dark-border-primary bg-bg-primary dark:bg-dark-bg-secondary overflow-y-auto shadow-elevation-1">
          <div className="p-6 border-b border-border-primary dark:border-dark-border-primary bg-bg-secondary dark:bg-dark-bg-tertiary">
            <h2 className="text-sm font-bold text-text-primary dark:text-dark-text-primary uppercase tracking-wide">
              Menu
            </h2>
            <p className="text-xs text-text-tertiary dark:text-dark-text-tertiary mt-1.5 font-medium">
              Super Admin Access
            </p>
          </div>

          {/* Navigation Links */}
          <nav className="flex flex-col p-3 space-y-1">
            {nav.map(({ href, label, icon }) => {
              const isActive = pathname === href;
              return (
                <Link
                  key={href}
                  href={href}
                  className={`px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200 flex items-center gap-3 ${
                    isActive
                      ? 'bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 border-l-2 border-primary-600 dark:border-primary-500 shadow-elevation-1'
                      : 'text-text-secondary dark:text-dark-text-secondary hover:bg-bg-tertiary dark:hover:bg-dark-bg-tertiary border-l-2 border-transparent'
                  }`}
                >
                  <span className="text-base">{icon}</span>
                  {label}
                </Link>
              );
            })}
          </nav>

          {/* User Section */}
          <div className="absolute bottom-0 left-0 right-0 w-64 p-4 border-t border-border-primary dark:border-dark-border-primary bg-bg-primary dark:bg-dark-bg-secondary">
            <div className="bg-bg-secondary dark:bg-dark-bg-tertiary rounded-lg p-3.5 mb-4 border border-border-primary dark:border-dark-border-primary">
              <p className="text-xs text-text-tertiary dark:text-dark-text-tertiary truncate font-medium">
                Logged in as
              </p>
              <p className="text-sm font-semibold text-text-primary dark:text-dark-text-primary mt-1 truncate">
                {user.email}
              </p>
              <p className="text-xs text-primary-600 dark:text-primary-400 font-medium mt-1">
                {user.type}
              </p>
            </div>
            <button
              type="button"
              onClick={() => logout().then(() => router.replace("/login"))}
              className="w-full px-4 py-2.5 text-sm font-medium text-text-primary dark:text-dark-text-primary bg-bg-secondary dark:bg-dark-bg-tertiary border border-border-primary dark:border-dark-border-primary rounded-lg hover:bg-error hover:text-white hover:border-error dark:hover:bg-error dark:hover:border-error transition-all duration-200"
            >
              Sign out
            </button>
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 overflow-auto bg-bg-secondary dark:bg-dark-bg-primary">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
