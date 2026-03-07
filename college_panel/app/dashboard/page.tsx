"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { getMyColleges, College } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { Building2, Users, BookOpen, ArrowRight, Loader2, AlertCircle, GraduationCap } from "lucide-react";

export default function DashboardPage() {
  const { isSuperAdmin } = useAuth();
  const router = useRouter();
  const [colleges, setColleges] = useState<College[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (isSuperAdmin) {
      router.replace("/dashboard/admin");
      return;
    }
    getMyColleges()
      .then((r) => setColleges(r.items))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [isSuperAdmin, router]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="animate-spin text-blue-600" size={28} />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center gap-2 text-red-600 bg-red-50 border border-red-200 rounded-xl p-4">
        <AlertCircle size={18} />
        <p>{error}</p>
      </div>
    );
  }

  if (colleges.length === 0) {
    return (
      <div className="text-center py-20">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-slate-100 text-slate-400 mb-4">
          <GraduationCap size={32} />
        </div>
        <h2 className="text-lg font-semibold text-slate-700">No colleges assigned</h2>
        <p className="text-slate-500 text-sm mt-1">
          Your account is not listed as an admin for any college yet.
        </p>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-900">My Colleges</h1>
        <p className="text-slate-500 text-sm mt-1">Select a college to manage its communities.</p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {colleges.map((college) => (
          <Link
            key={college.id}
            href={`/dashboard/college/${college.id}`}
            className="group bg-white rounded-2xl border border-slate-200 p-5 hover:border-blue-300 hover:shadow-md transition-all"
          >
            <div className="flex items-start justify-between mb-4">
              <div className="w-10 h-10 rounded-xl bg-blue-50 flex items-center justify-center text-blue-600">
                <Building2 size={20} />
              </div>
              <ArrowRight
                size={16}
                className="text-slate-300 group-hover:text-blue-500 group-hover:translate-x-0.5 transition-all mt-1"
              />
            </div>

            <h3 className="font-semibold text-slate-900 mb-1 truncate">{college.name}</h3>
            <p className="text-xs text-slate-500 mb-4 truncate">{college.contact_email}</p>

            <div className="flex items-center gap-4 text-xs text-slate-500">
              <span className="flex items-center gap-1">
                <BookOpen size={12} />
                {college.communities.length} communities
              </span>
              <span className="flex items-center gap-1">
                <Users size={12} />
                {college.admin_users.length} admins
              </span>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
