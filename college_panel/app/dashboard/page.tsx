"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { getMyColleges, College } from "@/lib/api";
import { Building2, Users, Network, Loader2, AlertCircle, GraduationCap } from "lucide-react";

export default function DashboardPage() {
  const { isSuperAdmin, loading: authLoading } = useAuth();
  const router = useRouter();
  const [colleges, setColleges] = useState<College[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (authLoading) return;
    if (isSuperAdmin) {
      router.replace("/dashboard/admin");
      return;
    }
    getMyColleges()
      .then((res) => setColleges(res.items ?? []))
      .catch((e: unknown) => setError(e instanceof Error ? e.message : "Failed to load colleges"))
      .finally(() => setLoading(false));
  }, [isSuperAdmin, authLoading, router]);

  if (authLoading || loading) {
    return (
      <div className="flex items-center justify-center py-32">
        <Loader2 size={28} className="animate-spin text-brand" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center gap-2 text-red-600 bg-red-50 border border-red-200 rounded-xl p-4">
        <AlertCircle size={18} />
        <span>{error}</span>
      </div>
    );
  }

  if (colleges.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-32 text-text-3">
        <GraduationCap size={48} className="mb-4 opacity-40" />
        <p className="text-lg font-medium text-text-2">No colleges assigned</p>
        <p className="text-sm mt-1">Contact a super-admin to be assigned to a college.</p>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-xl font-bold text-text-1">My Colleges</h1>
        <p className="text-sm text-text-3 mt-0.5">Select a college to manage it.</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {colleges.map((college) => (
          <Link
            key={college.id}
            href={`/dashboard/college/${college.id}`}
            className="block bg-surface border border-divider rounded-xl p-5 hover:border-brand hover:shadow-md transition group"
          >
            <div className="flex items-start gap-3">
              <div className="w-10 h-10 rounded-lg bg-brand-light flex items-center justify-center shrink-0">
                <Building2 size={20} className="text-brand" />
              </div>
              <div className="min-w-0">
                <h2 className="font-semibold text-text-1 group-hover:text-brand transition truncate text-base">
                  {college.name}
                </h2>
                <p className="text-xs text-text-3 truncate mt-0.5">{college.contact_email}</p>
              </div>
            </div>
            <div className="mt-4 flex items-center gap-4 text-xs text-text-3">
              <span className="flex items-center gap-1">
                <Network size={13} />
                {college.communities?.length ?? 0} communities
              </span>
              <span className="flex items-center gap-1">
                <Users size={13} />
                {college.admin_users?.length ?? 0} admins
              </span>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
