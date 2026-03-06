"use client";

import { useEffect, useState, useCallback } from "react";
import {
  Community,
  Post,
  getCommunityPosts,
  deletePost,
  updatePost,
} from "@/lib/api";
import {
  FileText,
  Trash2,
  Loader2,
  AlertCircle,
  Heart,
  Eye,
  MessageSquare,
  ChevronDown,
  ChevronRight,
  Layers,
  Pencil,
  Check,
  X,
} from "lucide-react";

interface Props {
  communities: Community[];
  onRefresh: () => Promise<void>;
}

export default function PostsTab({ communities, onRefresh }: Props) {
  if (communities.length === 0) {
    return (
      <div className="text-center py-16 bg-white rounded-2xl border border-dashed border-slate-200">
        <Layers size={32} className="mx-auto text-slate-300 mb-3" />
        <p className="text-slate-500 text-sm">No communities yet.</p>
        <p className="text-xs text-slate-400 mt-1">
          Create a community first to manage its posts here.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {communities.map((c) => (
        <CommunityPosts key={c.id} community={c} onRefresh={onRefresh} />
      ))}
    </div>
  );
}

function CommunityPosts({
  community,
  onRefresh,
}: {
  community: Community;
  onRefresh: () => Promise<void>;
}) {
  const [open, setOpen] = useState(false);
  const [posts, setPosts] = useState<Post[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [confirmId, setConfirmId] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editContent, setEditContent] = useState("");
  const [savingId, setSavingId] = useState<string | null>(null);

  const fetchPosts = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const data = await getCommunityPosts(community.id);
      setPosts(data.items);
      setTotal(data.total);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load posts");
    } finally {
      setLoading(false);
    }
  }, [community.id]);

  useEffect(() => {
    if (open) fetchPosts();
  }, [open, fetchPosts]);

  async function handleDelete(postId: string) {
    setDeletingId(postId);
    setConfirmId(null);
    try {
      await deletePost(postId);
      setPosts((prev) => prev.filter((p) => p.id !== postId));
      setTotal((t) => t - 1);
      await onRefresh();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Delete failed");
    } finally {
      setDeletingId(null);
    }
  }

  function startEdit(post: Post) {
    setEditingId(post.id);
    setEditContent(post.content);
    setConfirmId(null);
  }

  async function handleSave(postId: string) {
    setSavingId(postId);
    try {
      const updated = await updatePost(postId, editContent);
      setPosts((prev) => prev.map((p) => (p.id === postId ? updated : p)));
      setEditingId(null);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Save failed");
    } finally {
      setSavingId(null);
    }
  }

  const postCount = community.posts?.length ?? 0;

  return (
    <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
      {/* Header row */}
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center justify-between px-4 py-3.5 text-sm hover:bg-slate-50 transition"
      >
        <div className="flex items-center gap-2 font-medium text-slate-800">
          <FileText size={14} className="text-blue-500" />
          {community.name}
          <span className="text-xs font-normal text-slate-400">
            ({community.type})
          </span>
          {postCount > 0 && (
            <span className="inline-flex items-center justify-center bg-blue-50 text-blue-600 text-xs font-semibold rounded-full px-1.5 min-w-[1.25rem] h-5">
              {postCount}
            </span>
          )}
        </div>
        {open ? (
          <ChevronDown size={15} className="text-slate-400" />
        ) : (
          <ChevronRight size={15} className="text-slate-400" />
        )}
      </button>

      {open && (
        <div className="border-t border-slate-100 px-4 py-3">
          {error && (
            <div className="flex items-center gap-2 bg-red-50 border border-red-200 text-red-700 rounded-lg px-3 py-2 mb-3 text-xs">
              <AlertCircle size={13} />
              {error}
            </div>
          )}

          {loading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 size={20} className="animate-spin text-blue-500" />
            </div>
          ) : posts.length === 0 ? (
            <div className="flex items-center justify-center gap-2 py-8 text-slate-400 text-sm">
              <FileText size={16} />
              No posts yet
            </div>
          ) : (
            <>
              <p className="text-xs text-slate-400 mb-3">
                {total} post{total !== 1 ? "s" : ""}
              </p>
              <ul className="space-y-2">
                {posts.map((post) => (
                  <li
                    key={post.id}
                    className="bg-slate-50 rounded-lg px-3 py-3 flex gap-3"
                  >
                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      {editingId === post.id ? (
                        <textarea
                          value={editContent}
                          onChange={(e) => setEditContent(e.target.value)}
                          rows={4}
                          className="w-full text-sm text-slate-800 border border-blue-300 rounded-lg px-2.5 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400 resize-y"
                          autoFocus
                        />
                      ) : (
                        <p className="text-sm text-slate-800 line-clamp-2 leading-snug">
                          {post.content}
                        </p>
                      )}
                      <div className="flex items-center gap-3 mt-2 text-xs text-slate-400 flex-wrap">
                        <span className="font-mono truncate max-w-[140px]" title={post.user_id}>
                          by {post.user_id.slice(0, 8)}…
                        </span>
                        <span className="flex items-center gap-1">
                          <Heart size={10} /> {post.likes}
                        </span>
                        <span className="flex items-center gap-1">
                          <Eye size={10} /> {post.views}
                        </span>
                        <span className="flex items-center gap-1">
                          <MessageSquare size={10} /> {post.comments.length}
                        </span>
                        <span>
                          {new Date(post.created_at).toLocaleDateString(
                            undefined,
                            { month: "short", day: "numeric", year: "numeric" }
                          )}
                        </span>
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="shrink-0 flex items-start gap-1">
                      {editingId === post.id ? (
                        // Save / Cancel
                        <>
                          <button
                            onClick={() => handleSave(post.id)}
                            disabled={!!savingId || editContent.trim() === ""}
                            className="p-1.5 text-emerald-600 hover:bg-emerald-50 rounded-lg transition disabled:opacity-40"
                            title="Save"
                          >
                            {savingId === post.id ? (
                              <Loader2 size={14} className="animate-spin" />
                            ) : (
                              <Check size={14} />
                            )}
                          </button>
                          <button
                            onClick={() => setEditingId(null)}
                            disabled={!!savingId}
                            className="p-1.5 text-slate-400 hover:bg-slate-200 rounded-lg transition disabled:opacity-40"
                            title="Cancel"
                          >
                            <X size={14} />
                          </button>
                        </>
                      ) : confirmId === post.id ? (
                        // Delete confirm
                        <div className="flex items-center gap-1.5">
                          <span className="text-xs text-slate-500">Sure?</span>
                          <button
                            onClick={() => handleDelete(post.id)}
                            disabled={!!deletingId}
                            className="text-xs px-2 py-1 bg-red-600 text-white rounded-md hover:bg-red-700 transition disabled:opacity-50"
                          >
                            {deletingId === post.id ? (
                              <Loader2 size={10} className="animate-spin" />
                            ) : (
                              "Yes"
                            )}
                          </button>
                          <button
                            onClick={() => setConfirmId(null)}
                            className="text-xs px-2 py-1 bg-slate-200 text-slate-600 rounded-md hover:bg-slate-300 transition"
                          >
                            No
                          </button>
                        </div>
                      ) : (
                        // Normal: edit + delete
                        <>
                          <button
                            onClick={() => startEdit(post)}
                            disabled={!!deletingId}
                            className="p-1.5 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition disabled:opacity-40"
                            title="Edit post"
                          >
                            <Pencil size={14} />
                          </button>
                          <button
                            onClick={() => setConfirmId(post.id)}
                            disabled={!!deletingId}
                            className="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition disabled:opacity-40"
                            title="Delete post"
                          >
                            <Trash2 size={14} />
                          </button>
                        </>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            </>
          )}
        </div>
      )}
    </div>
  );
}
