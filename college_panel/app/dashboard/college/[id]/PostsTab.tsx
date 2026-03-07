"use client";

import { useState, useCallback } from "react";
import {
  Community,
  Post,
  getCommunityPosts,
  deletePost,
  updatePost,
} from "@/lib/api";
import {
  ChevronDown,
  ChevronRight,
  FileText,
  Loader2,
  AlertCircle,
  Heart,
  Eye,
  MessageSquare,
  Pencil,
  Trash2,
  Check,
  X,
} from "lucide-react";

interface Props {
  communities: Community[];
}

export default function PostsTab({ communities }: Props) {
  if (communities.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-text-3">
        <FileText size={36} className="mb-3 opacity-40" />
        <p className="text-text-2 font-medium">No communities yet</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {communities.map((c) => (
        <CommunityPosts key={c.id} community={c} />
      ))}
    </div>
  );
}

function CommunityPosts({ community }: { community: Community }) {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [posts, setPosts] = useState<Post[]>([]);
  const [fetched, setFetched] = useState(false);

  const fetchPosts = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const res = await getCommunityPosts(community.id);
      setPosts(res.items ?? []);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load posts");
    } finally {
      setLoading(false);
      setFetched(true);
    }
  }, [community.id]);

  function handleToggle() {
    const willOpen = !open;
    setOpen(willOpen);
    if (willOpen && !fetched) fetchPosts();
  }

  function handleDelete(postId: string) {
    setPosts((prev) => prev.filter((p) => p.id !== postId));
  }

  function handleUpdate(updated: Post) {
    setPosts((prev) => prev.map((p) => (p.id === updated.id ? updated : p)));
  }

  const postCount = community.post_count ?? 0;

  return (
    <div className="border border-divider rounded-xl overflow-hidden">
      <button
        onClick={handleToggle}
        className="w-full flex items-center justify-between px-4 py-3 bg-surface hover:bg-surface-2 transition text-left"
      >
        <div className="flex items-center gap-2 min-w-0">
          <FileText size={14} className="text-text-3 shrink-0" />
          <span className="font-medium text-text-1 text-sm truncate">{community.name}</span>
          {postCount > 0 && (
            <span className="shrink-0 text-xs bg-surface-2 text-text-2 px-1.5 py-0.5 rounded-full font-medium">
              {postCount}
            </span>
          )}
        </div>
        <div className="shrink-0 text-text-3">
          {open ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
        </div>
      </button>

      {open && (
        <div className="border-t border-divider">
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 size={22} className="animate-spin text-brand" />
            </div>
          ) : error ? (
            <div className="flex items-center gap-2 text-red-600 text-sm p-4">
              <AlertCircle size={14} />
              {error}
              <button onClick={fetchPosts} className="underline ml-2">Retry</button>
            </div>
          ) : posts.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8 text-text-3">
              <FileText size={24} className="mb-2 opacity-40" />
              <p className="text-sm">No posts in this community</p>
            </div>
          ) : (
            <ul className="divide-y divide-divider">
              {posts.map((post) => (
                <PostRow
                  key={post.id}
                  communityId={community.id}
                  post={post}
                  onDelete={handleDelete}
                  onUpdate={handleUpdate}
                />
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}

interface PostRowProps {
  communityId: string;
  post: Post;
  onDelete: (id: string) => void;
  onUpdate: (updated: Post) => void;
}

function PostRow({ post, onDelete, onUpdate }: PostRowProps) {
  const [editing, setEditing] = useState(false);
  const [editContent, setEditContent] = useState(post.content);
  const [editLoading, setEditLoading] = useState(false);
  const [editError, setEditError] = useState("");

  const [confirmDelete, setConfirmDelete] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState(false);

  async function handleSave() {
    setEditLoading(true);
    setEditError("");
    try {
      const updated = await updatePost(post.id, editContent);
      onUpdate(updated);
      setEditing(false);
    } catch (e: unknown) {
      setEditError(e instanceof Error ? e.message : "Save failed");
    } finally {
      setEditLoading(false);
    }
  }

  async function handleDelete() {
    setDeleteLoading(true);
    try {
      await deletePost(post.id);
      onDelete(post.id);
    } catch {
      setConfirmDelete(false);
    } finally {
      setDeleteLoading(false);
    }
  }

  return (
    <li className="px-4 py-3 bg-surface">
      {editing ? (
        <div className="space-y-2">
          <textarea
            value={editContent}
            onChange={(e) => setEditContent(e.target.value)}
            rows={3}
            className="w-full border border-divider rounded-lg px-3 py-2 text-sm text-text-1 bg-surface focus:outline-none focus:ring-2 focus:ring-brand-ring resize-none"
          />
          {editError && (
            <p className="text-xs text-red-600 flex items-center gap-1">
              <AlertCircle size={12} /> {editError}
            </p>
          )}
          <div className="flex gap-2">
            <button
              onClick={handleSave}
              disabled={editLoading}
              className="flex items-center gap-1 text-xs bg-brand hover:bg-brand-hover disabled:bg-brand-disabled text-white px-3 py-1.5 rounded-lg transition"
            >
              {editLoading ? <Loader2 size={12} className="animate-spin" /> : <Check size={12} />}
              Save
            </button>
            <button
              onClick={() => { setEditing(false); setEditContent(post.content); setEditError(""); }}
              className="flex items-center gap-1 text-xs border border-divider px-3 py-1.5 rounded-lg hover:bg-surface-2 transition"
            >
              <X size={12} /> Cancel
            </button>
          </div>
        </div>
      ) : (
        <div>
          <p className="text-sm text-text-1 whitespace-pre-wrap break-words">{post.content}</p>
          <div className="flex items-center justify-between mt-2 gap-2">
            <div className="flex items-center gap-3 text-xs text-text-3">
              <span className="flex items-center gap-1"><Heart size={11} />{post.likes ?? 0}</span>
              <span className="flex items-center gap-1"><Eye size={11} />{post.views ?? 0}</span>
              <span className="flex items-center gap-1"><MessageSquare size={11} />{post.comment_count ?? post.comments?.length ?? 0}</span>
              <span>{post.created_at ? new Date(post.created_at).toLocaleDateString() : ""}</span>
            </div>
            <div className="flex items-center gap-1 shrink-0">
              {confirmDelete ? (
                <>
                  <span className="text-xs text-red-600 mr-1">Delete?</span>
                  <button
                    onClick={handleDelete}
                    disabled={deleteLoading}
                    className="text-xs text-white bg-red-600 hover:bg-red-700 disabled:opacity-50 px-2 py-1 rounded-md transition"
                  >
                    {deleteLoading ? <Loader2 size={11} className="animate-spin" /> : "Yes"}
                  </button>
                  <button onClick={() => setConfirmDelete(false)} className="text-xs border border-divider px-2 py-1 rounded-md hover:bg-surface-2 transition">
                    No
                  </button>
                </>
              ) : (
                <>
                  <button
                    onClick={() => { setEditing(true); setEditContent(post.content); }}
                    title="Edit post"
                    className="p-1.5 text-text-3 hover:text-brand hover:bg-brand-light rounded-md transition"
                  >
                    <Pencil size={13} />
                  </button>
                  <button
                    onClick={() => setConfirmDelete(true)}
                    title="Delete post"
                    className="p-1.5 text-text-3 hover:text-red-600 hover:bg-red-50 rounded-md transition"
                  >
                    <Trash2 size={13} />
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </li>
  );
}
