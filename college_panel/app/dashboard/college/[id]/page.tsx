"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  getCollege,
  getCollegeCommunities,
  College,
  Community,
} from "@/lib/api";
import {
  Building2,
  BookOpen,
  Users,
  Bell,
  ChevronLeft,
  Loader2,
  AlertCircle,
  Shield,
  FileText,
} from "lucide-react";
import CommunitiesTab from "./CommunitiesTab";
import RequestsTab from "./RequestsTab";
import AdminsTab from "./AdminsTab";
import MembersTab from "./MembersTab";
import PostsTab from "./PostsTab";

type Tab = "communities" | "requests" | "admins" | "members" | "posts";

export default function CollegePage() {
  const { id } = useParams<{ id: string }>();
  const [college, setCollege] = useState<College | null>(null);
  const [communities, setCommunities] = useState<Community[]>([]);
  const [tab, setTab] = useState<Tab>("communities");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchCollege = useCallback(async () => {
    const [c, comms] = await Promise.all([
      getCollege(id),
      getCollegeCommunities(id),
    ]);
    setCollege(c);
    setCommunities(comms.items);
  }, [id]);

  useEffect(() => {
    setLoading(true);
    fetchCollege()
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [fetchCollege]);

  const privateCommunities = communities.filter((c) => c.type === "PRIVATE");
  const totalRequests = privateCommunities.reduce(
    (sum, c) => sum + (c.requested_users?.length ?? 0),
    0
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="animate-spin text-blue-600" size={28} />
      </div>
    );
  }

  if (error || !college) {
    return (
      <div className="flex items-center gap-2 text-red-600 bg-red-50 border border-red-200 rounded-xl p-4">
        <AlertCircle size={18} />
        <p>{error || "College not found."}</p>
      </div>
    );
  }

  const tabs: { id: Tab; label: string; icon: React.ReactNode; badge?: number }[] = [
    { id: "communities", label: "Communities", icon: <BookOpen size={15} />, badge: communities.length },
    {
      id: "requests",
      label: "Join Requests",
      icon: <Bell size={15} />,
      badge: totalRequests,
    },
    { id: "admins", label: "Admins", icon: <Shield size={15} />, badge: college.admin_users.length },
    { id: "members", label: "Members", icon: <Users size={15} /> },
    { id: "posts", label: "Posts", icon: <FileText size={15} /> },
  ];

  return (
    <div>
      {/* Breadcrumb */}
      <Link
        href="/dashboard"
        className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-blue-600 mb-5 transition"
      >
        <ChevronLeft size={15} />
        All colleges
      </Link>

      {/* College header */}
      <div className="bg-white rounded-2xl border border-slate-200 p-5 mb-6 flex items-center gap-4">
        <div className="w-12 h-12 rounded-xl bg-blue-50 flex items-center justify-center text-blue-600 shrink-0">
          <Building2 size={24} />
        </div>
        <div className="flex-1 min-w-0">
          <h1 className="text-xl font-bold text-slate-900 truncate">{college.name}</h1>
          <p className="text-sm text-slate-500 truncate">{college.physical_address}</p>
        </div>
        <div className="hidden sm:block text-right shrink-0">
          <p className="text-xs text-slate-400">Contact</p>
          <p className="text-sm text-slate-700">{college.contact_email}</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-slate-200 mb-6">
        <div className="flex gap-0 -mb-px overflow-x-auto">
          {tabs.map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`flex items-center gap-1.5 px-4 py-3 text-sm font-medium border-b-2 transition whitespace-nowrap ${
                tab === t.id
                  ? "border-blue-600 text-blue-600"
                  : "border-transparent text-slate-500 hover:text-slate-700"
              }`}
            >
              {t.icon}
              {t.label}
              {t.badge !== undefined && t.badge > 0 && (
                <span
                  className={`inline-flex items-center justify-center rounded-full text-xs px-1.5 min-w-[1.25rem] h-5 font-semibold ${
                    t.id === "requests"
                      ? "bg-amber-100 text-amber-700"
                      : "bg-slate-100 text-slate-600"
                  }`}
                >
                  {t.badge}
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Tab content */}
      {tab === "communities" && (
        <CommunitiesTab
          collegeId={id}
          communities={communities}
          onRefresh={fetchCollege}
        />
      )}
      {tab === "requests" && (
        <RequestsTab
          communities={privateCommunities}
          onRefresh={fetchCollege}
        />
      )}
      {tab === "admins" && (
        <AdminsTab
          college={college}
          onRefresh={fetchCollege}
        />
      )}
      {tab === "members" && <MembersTab collegeId={id} />}
      {tab === "posts" && (
        <PostsTab communities={communities} onRefresh={fetchCollege} />
      )}
    </div>
  );
}
