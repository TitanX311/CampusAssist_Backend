'use client';

import React from 'react';
import Link from 'next/link';

interface AdminLayoutProps {
  children: React.ReactNode;
}

export const AdminLayout: React.FC<AdminLayoutProps> = ({ children }) => {
  return (
    <div className="flex flex-col min-h-screen bg-bg-secondary dark:bg-dark-bg-primary text-text-primary dark:text-dark-text-primary">
      {/* Header */}
      <header className="sticky top-0 z-40 border-b border-border-primary dark:border-dark-border-primary bg-bg-primary dark:bg-dark-bg-secondary shadow-elevation-1 dark:shadow-elevation-2">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16 gap-4">
            {/* Logo */}
            <div className="flex items-center gap-3 flex-shrink-0">
              <Link href="/" className="flex items-center gap-2.5 group">
                <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-primary-600 to-primary-700 flex items-center justify-center text-white font-bold text-base shadow-sm group-hover:shadow-md transition-shadow">
                  CA
                </div>
                <div className="hidden sm:block">
                  <div className="text-base font-bold leading-tight text-text-primary dark:text-dark-text-primary">
                    Campus
                  </div>
                  <div className="text-xs text-text-tertiary dark:text-dark-text-tertiary font-medium">
                    Admin
                  </div>
                </div>
              </Link>
            </div>

            {/* Navigation */}
            <nav className="hidden md:flex items-center gap-0.5 flex-1 mx-6">
              {[
                { href: '/dashboard', label: 'Dashboard' },
                { href: '/colleges', label: 'Colleges' },
                { href: '/communities', label: 'Communities' },
                { href: '/users', label: 'Users' },
              ].map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className="px-3.5 py-2 text-sm font-medium text-text-secondary dark:text-dark-text-secondary hover:text-primary-600 dark:hover:text-primary-400 hover:bg-bg-secondary dark:hover:bg-dark-bg-tertiary transition-all duration-200 rounded-md"
                >
                  {item.label}
                </Link>
              ))}
            </nav>

          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>

      {/* Footer */}
      <footer className="border-t border-border-primary dark:border-dark-border-primary bg-bg-primary dark:bg-dark-bg-secondary mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-12 mb-8">
            <div>
              <h3 className="text-base font-bold text-text-primary dark:text-dark-text-primary mb-2">
                Campus Assist
              </h3>
              <p className="text-text-secondary dark:text-dark-text-secondary text-sm leading-relaxed">
                A unified platform for managing college communities, content, and engagement.
              </p>
            </div>
            <div>
              <h4 className="text-sm font-bold text-text-primary dark:text-dark-text-primary mb-4 uppercase tracking-wide">
                Admin
              </h4>
              <ul className="space-y-2.5 text-sm">
                <li>
                  <Link
                    href="/dashboard"
                    className="text-text-secondary dark:text-dark-text-secondary hover:text-primary-600 dark:hover:text-primary-400 transition-colors duration-200"
                  >
                    Dashboard
                  </Link>
                </li>
                <li>
                  <Link
                    href="/analytics"
                    className="text-text-secondary dark:text-dark-text-secondary hover:text-primary-600 dark:hover:text-primary-400 transition-colors duration-200"
                  >
                    Analytics
                  </Link>
                </li>
                <li>
                  <Link
                    href="/settings"
                    className="text-text-secondary dark:text-dark-text-secondary hover:text-primary-600 dark:hover:text-primary-400 transition-colors duration-200"
                  >
                    Settings
                  </Link>
                </li>
              </ul>
            </div>
            <div>
              <h4 className="text-sm font-bold text-text-primary dark:text-dark-text-primary mb-4 uppercase tracking-wide">
                Support
              </h4>
              <ul className="space-y-2.5 text-sm">
                <li>
                  <a
                    href="#"
                    className="text-text-secondary dark:text-dark-text-secondary hover:text-primary-600 dark:hover:text-primary-400 transition-colors duration-200"
                  >
                    Help Center
                  </a>
                </li>
                <li>
                  <a
                    href="#"
                    className="text-text-secondary dark:text-dark-text-secondary hover:text-primary-600 dark:hover:text-primary-400 transition-colors duration-200"
                  >
                    API Docs
                  </a>
                </li>
                <li>
                  <a
                    href="#"
                    className="text-text-secondary dark:text-dark-text-secondary hover:text-primary-600 dark:hover:text-primary-400 transition-colors duration-200"
                  >
                    Contact
                  </a>
                </li>
              </ul>
            </div>
          </div>
          <div className="border-t border-border-primary dark:border-dark-border-primary pt-8 text-center text-sm text-text-tertiary dark:text-dark-text-tertiary">
            <p>&copy; 2026 Campus Assist. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
};
