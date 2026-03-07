"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  getCollege,
  updateCollege,
  getCollegeCommunities,
  College,
  Community,
} from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import {
  ArrowLeft,
  Building2,
  Loader2,
  AlertCircle,
  Pencil,
  X,
  Check,
  Network,
  Users,
  ClipboardList,
  ShieldCheck,
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
  const router = useRouter();
  const { user } = useAuth();

  const [college, setCollege] = useState<College | null>(null);
  const [communities, setCommunities] = useState<Community[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [activeTab, setActiveTab] = useState<Tab>("communities");

  // Edit modal state
  const [editOpen, setEditOpen] = useState(false);
  const [editName, setEditName] = useState("");
  const [editEmail, setEditEmail] = useState("");
  const [editAddress, setEditAddress] = useState("");
  const [editLoading, setEditLoading] = useState(false);
  const [editError, setEditError] = useState("");

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [col, comm] = await Promise.all([
        getCollege(id),
        getCollegeCommunities(id),
      ]);
      setCollege(col);
      setCommunities(comm.items ?? []);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load college");
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    if (!user) { router.replace("/login"); return; }
    fetchData();
  }, [user, fetchData, router]);

  function openEdit() {
    if (!college) return;
    setEditName(college.name);
    setEditEmail(college.contact_email);
    setEditAddress(college.physical_address);
    setEditError("");
    setEditOpen(true);
  }

  async function saveEdit(e: React.FormEvent) {
    e.preventDefault();
    if (!college) return;
    setEditLoading(true);
    setEditError("");
    try {
      const updated = await updateCollege(college.id, {
        name: editName,
        contact_email: editEmail,
        physical_address: editAddress,
      });
      setCollege(updated);
      setEditOpen(false);
    } catch (e: unknown) {
      setEditError(e instanceof Error ? e.message : "Save failed");
    } finally {
      setEditLoading(false);
    }
  }

  const privateCommunities = communities.filter((c) => c.type === "PRIVATE");

  const tabs: { key: Tab; label: string; icon: React.ReactNode; badge?: number }[] = [
    { key: "communities", label: "Communities", icon: <Network size={15} />, badge: communities.length },
    { key: "requests", label: "Join Requests", icon: <ClipboardList size={15} /> },
    { key: "admins", label: "Admins", icon: <ShieldCheck size={15} />, badge: college?.admin_users?.length },
    { key: "members", label: "Members", icon: <Users size={15} /> },
    { key: "posts", label: "Posts", icon: <FileText size={15} /> },
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center py-32">
        <Loader2 size={28} className="animate-spin text-brand" />
      </div>
    );
  }

  if (error || !college) {
    return (
      <div className="flex items-center gap-2 text-red-600 bg-red-50 border border-red-200 rounded-xl p-4">
        <AlertCircle size={18} />
        <span>{error || "College not found"}</span>
      </div>
    );
  }

  return (
    <div>
      {/* Back link */}
      <Link href="/dashboard" className="inline-flex items-center gap-1 text-sm text-text-3 hover:text-brand mb-5 transition">
        <ArrowLeft size={15} />
        My Colleges
      </Link>

      {/* College header */}
      <div className="bg-surface border border-divider rounded-xl p-5 mb-6 flex items-start justify-between gap-4">
        <div className="flex items-start gap-4 min-w-0">
          <div className="w-12 h-12 rounded-xl bg-brand-light flex items-center justify-center shrink-0">
            <Building2 size={24} className="text-brand" />
          </div>
          <div className="min-w-0">
            <h1 className="text-xl font-bold text-text-1 truncate">{college.name}</h1>
            <p className="text-sm text-text-3 mt-0.5">{college.contact_email}</p>
            {college.physical_address && (
              <p className="text-xs text-text-3 mt-0.5">{college.physical_address}</p>
            )}
          </div>
        </div>
        <button
          onClick={openEdit}
          className="flex items-center gap-1.5 text-sm text-text-2 hover:text-brand border border-divider hover:border-brand rounded-lg px-3 py-2 transition shrink-0"
        >
          <Pencil size={14} />
          Edit
        </button>
      </div>

      {/* Tabs */}
      <div className="border-b border-divider mb-6 overflow-x-auto">
        <div className="flex gap-1 min-w-max">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`flex items-center gap-1.5 px-4 py-2.5 text-sm font-medium border-b-2 transition whitespace-nowrap ${
                activeTab === tab.key
                  ? "border-brand text-brand"
                  : "border-transparent text-text-3 hover:text-text-2"
              }`}
            >
              {tab.icon}
              {tab.label}
              {tab.badge !== undefined && tab.badge > 0 && (
                <span className={`ml-1 text-xs px-1.5 py-0.5 rounded-full font-medium ${
                  activeTab === tab.key
                    ? "bg-brand text-white"
                    : "bg-surface-2 text-text-2"
                }`}>
                  {tab.badge}
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Tab content */}
      <div>
        {activeTab === "communities" && (
          <CommunitiesTab
            college={college}
            communities={communities}
            onCommunitiesChange={setCommunities}
          />
        )}
        {activeTab === "requests" && (
          <RequestsTab communities={privateCommunities} />
        )}
        {activeTab === "admins" && (
          <AdminsTab college={college} onCollegeChange={setCollege} />
        )}
        {activeTab === "members" && (
          <MembersTab collegeId={college.id} />
        )}
        {activeTab === "posts" && (
          <PostsTab communities={communities} />
        )}
      </div>

      {/* Edit College Modal */}
      {editOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="bg-surface rounded-2xl shadow-2xl border border-divider w-full max-w-md">
            <div className="flex items-center justify-between px-6 py-4 border-b border-divider">
              <h2 className="font-semibold text-text-1">Edit College</h2>
              <button onClick={() => setEditOpen(false)} className="text-text-3 hover:text-text-1 transition">
                <X size={18} />
              </button>
            </div>
            <form onSubmit={saveEdit} className="p-6 space-y-4">
              {editError && (
                <div className="flex items-center gap-2 text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2 text-sm">
                  <AlertCircle size={14} />
                  {editError}
                </div>
              )}
              <div>
                <label className="block text-sm font-medium text-text-1 mb-1">College Name</label>
                <input
                  value={editName}
                  onChange={(e) => setEditName(e.target.value)}
                  required
                  className="w-full border border-divider rounded-lg px-3 py-2 text-sm text-text-1 bg-surface focus:outline-none focus:ring-2 focus:ring-brand-ring"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-text-1 mb-1">Contact Email</label>
                <input
                  type="email"
                  value={editEmail}
                  onChange={(e) => setEditEmail(e.target.value)}
                  required
                  className="w-full border border-divider rounded-lg px-3 py-2 text-sm text-text-1 bg-surface focus:outline-none focus:ring-2 focus:ring-brand-ring"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-text-1 mb-1">Physical Address</label>
                <input
                  value={editAddress}
                  onChange={(e) => setEditAddress(e.target.value)}
                  className="w-full border border-divider rounded-lg px-3 py-2 text-sm text-text-1 bg-surface focus:outline-none focus:ring-2 focus:ring-brand-ring"
                />
              </div>
              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setEditOpen(false)}
                  className="px-4 py-2 text-sm text-text-2 border border-divider rounded-lg hover:bg-surface-2 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={editLoading}
                  className="flex items-center gap-2 px-4 py-2 text-sm bg-brand hover:bg-brand-hover disabled:bg-brand-disabled text-white rounded-lg transition"
                >
                  {editLoading ? <Loader2 size={14} className="animate-spin" /> : <Check size={14} />}
                  {editLoading ? "Saving…" : "Save"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
