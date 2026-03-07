// Typed API client for the campus-assist backend.
// All methods read the token from localStorage via getToken().
// Requests go to /api/* which is proxied by next.config.ts → backend.

const BASE = "";

export type CommunityType = "PUBLIC" | "PRIVATE";
export type UserType = "USER" | "COLLEGE" | "SUPER_ADMIN";

export interface Community {
  id: string;
  name: string;
  type: CommunityType;
  member_users: string[];
  requested_users: string[];
  parent_colleges: string[];
  posts: string[];
  created_at: string;
  updated_at: string;
}

export interface College {
  id: string;
  name: string;
  contact_email: string;
  physical_address: string;
  admin_users: string[];
  communities: string[];
  created_at: string;
  updated_at: string;
}

/** Enriched member — includes identity data from auth_service. */
export interface CollegeUser {
  college_id: string;
  user_id: string;
  joined_at: string;
  name: string | null;
  email: string | null;
  picture: string | null;
  user_type: string | null;
}

/** Full user profile returned by /api/users/{id} or /api/users/me. */
export interface UserProfile {
  user_id: string;
  email: string | null;
  name: string | null;
  picture: string | null;
  user_type: string;
  is_active: boolean;
  joined_at: string | null;
  stats: {
    post_count: number;
    comment_count: number;
    community_count: number;
  };
}

export interface CollegeStatsResponse {
  college_id: string;
  community_count: number;
  admin_count: number;
  member_count: number;
}

export interface PagedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface PendingRequestsResponse {
  community_id: string;
  requested_users: string[];
  total: number;
}

function getToken(): string {
  if (typeof window === "undefined") return "";
  return localStorage.getItem("token") ?? "";
}

async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getToken();
  const res = await fetch(`${BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers ?? {}),
    },
  });

  if (res.status === 401) {
    if (typeof window !== "undefined") {
      localStorage.removeItem("token");
      window.location.href = "/login";
    }
    throw new Error("Unauthorized");
  }

  const data = await res.json().catch(() => null);

  if (!res.ok) {
    const msg = data?.detail ?? `HTTP ${res.status}`;
    throw new Error(typeof msg === "string" ? msg : JSON.stringify(msg));
  }

  return data as T;
}

// ── Auth ─────────────────────────────────────────────────────────────────────

export async function login(email: string, password: string) {
  const data = await apiFetch<{
    access_token: string;
    user: { id: string; email: string; name: string };
  }>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  return data;
}

// ── College ───────────────────────────────────────────────────────────────────

export async function getMyColleges(page = 1, pageSize = 20) {
  return apiFetch<PagedResponse<College>>(
    `/api/college/my?page=${page}&page_size=${pageSize}`
  );
}

export async function getCollege(id: string) {
  return apiFetch<College>(`/api/college/${id}`);
}

export async function updateCollege(
  id: string,
  body: Partial<Pick<College, "name" | "contact_email" | "physical_address">>
) {
  return apiFetch<College>(`/api/college/${id}`, {
    method: "PATCH",
    body: JSON.stringify(body),
  });
}

/** SUPER_ADMIN update — bypasses college-admin membership check. */
export async function adminUpdateCollege(
  id: string,
  body: Partial<Pick<College, "name" | "contact_email" | "physical_address">>
) {
  return apiFetch<College>(`/api/admin/colleges/${id}`, {
    method: "PATCH",
    body: JSON.stringify(body),
  });
}

export async function getCollegeUsers(id: string, page = 1, pageSize = 20) {
  return apiFetch<PagedResponse<CollegeUser>>(
    `/api/college/${id}/users?page=${page}&page_size=${pageSize}`
  );
}

export async function addCollegeAdmin(collegeId: string, userId: string) {
  return apiFetch<{ message: string }>(
    `/api/college/${collegeId}/admins/${userId}`,
    { method: "POST" }
  );
}

export async function removeCollegeAdmin(collegeId: string, userId: string) {
  return apiFetch<{ message: string }>(
    `/api/college/${collegeId}/admins/${userId}`,
    { method: "DELETE" }
  );
}

// ── Community ─────────────────────────────────────────────────────────────────

export async function getCollegeCommunities(
  collegeId: string,
  page = 1,
  pageSize = 50
) {
  return apiFetch<PagedResponse<Community>>(
    `/api/community/college/${collegeId}?page=${page}&page_size=${pageSize}`
  );
}

export async function createCommunity(body: {
  name: string;
  type: CommunityType;
  parent_colleges: string[];
}) {
  return apiFetch<Community>("/api/community", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function updateCommunity(
  id: string,
  body: { name?: string; type?: CommunityType }
) {
  return apiFetch<Community>(`/api/community/${id}`, {
    method: "PATCH",
    body: JSON.stringify(body),
  });
}

export async function deleteCommunity(id: string) {
  return apiFetch<{ message: string }>(`/api/community/${id}`, {
    method: "DELETE",
  });
}

export async function getPendingRequests(communityId: string) {
  return apiFetch<PendingRequestsResponse>(
    `/api/community/${communityId}/requests`
  );
}

export async function approveJoinRequest(
  communityId: string,
  userId: string
) {
  return apiFetch<{ message: string }>(
    `/api/community/${communityId}/requests/${userId}/approve`,
    { method: "POST" }
  );
}

export async function rejectJoinRequest(
  communityId: string,
  userId: string
) {
  return apiFetch<{ message: string }>(
    `/api/community/${communityId}/requests/${userId}/reject`,
    { method: "DELETE" }
  );
}

export async function joinCommunity(communityId: string) {
  return apiFetch<{ community_id: string; status: string; message: string }>(
    `/api/community/${communityId}/join`,
    { method: "POST" }
  );
}

/** Cancel a pending join request (also works as "leave" for members). */
export async function cancelJoinRequest(communityId: string) {
  return apiFetch<{ community_id: string; message: string }>(
    `/api/community/${communityId}/leave`,
    { method: "DELETE" }
  );
}

// ── Posts ─────────────────────────────────────────────────────────────────────

export interface Post {
  id: string;
  user_id: string;
  community_id: string;
  content: string;
  likes: number;
  views: number;
  comment_count: number;
  attachments: string[];
  comments: string[];
  created_at: string;
  updated_at: string;
}

export interface PostListResponse {
  items: Post[];
  total: number;
  page: number;
  page_size: number;
}

export async function getCommunityPosts(
  communityId: string,
  page = 1,
  pageSize = 50
) {
  return apiFetch<PostListResponse>(
    `/api/posts/community/${communityId}?page=${page}&page_size=${pageSize}`
  );
}

export async function deletePost(postId: string) {
  return apiFetch<{ message: string }>(`/api/posts/${postId}`, {
    method: "DELETE",
  });
}

export async function updatePost(postId: string, content: string) {
  return apiFetch<Post>(`/api/posts/${postId}`, {
    method: "PATCH",
    body: JSON.stringify({ content }),
  });
}

// ── User Profiles ─────────────────────────────────────────────────────────────

export async function getMe() {
  return apiFetch<UserProfile>("/api/users/me");
}

export async function updateMe(body: { name?: string; picture?: string }) {
  return apiFetch<UserProfile>("/api/users/me", {
    method: "PATCH",
    body: JSON.stringify(body),
  });
}

export async function getUserProfile(userId: string) {
  return apiFetch<UserProfile>(`/api/users/${userId}`);
}

export async function getCollegeStats(collegeId: string) {
  return apiFetch<CollegeStatsResponse>(`/api/college/${collegeId}/stats`);
}

// ── Admin APIs ────────────────────────────────────────────────────────────────

export interface AdminUser {
  id: string;
  email: string;
  name: string | null;
  picture: string | null;
  type: string;
  is_active: boolean;
  email_verified: boolean;
  created_at: string;
  updated_at: string;
}

export async function adminListUsers(
  page = 1,
  pageSize = 20,
  opts?: { search?: string; user_type?: string; is_active?: boolean }
) {
  const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) });
  if (opts?.search) params.set("search", opts.search);
  if (opts?.user_type) params.set("user_type", opts.user_type);
  if (opts?.is_active !== undefined) params.set("is_active", String(opts.is_active));
  return apiFetch<PagedResponse<AdminUser>>(`/api/admin/users?${params}`);
}

export async function adminUpdateUserType(userId: string, type: UserType) {
  return apiFetch<AdminUser>(`/api/admin/users/${userId}/type`, {
    method: "PATCH",
    body: JSON.stringify({ type }),
  });
}

export async function adminUpdateUserActive(userId: string, is_active: boolean) {
  return apiFetch<AdminUser>(`/api/admin/users/${userId}/active`, {
    method: "PATCH",
    body: JSON.stringify({ is_active }),
  });
}

export async function adminUpdateUserProfile(
  userId: string,
  body: { name?: string; picture?: string }
) {
  return apiFetch<AdminUser>(`/api/admin/users/${userId}/profile`, {
    method: "PATCH",
    body: JSON.stringify(body),
  });
}

// ── Admin Stats ───────────────────────────────────────────────────────────────

export interface AdminStats {
  users: number;
  communities: number;
  posts: number;
  comments: number;
  colleges: number;
  attachments: number;
  timestamp: string;
}

export async function adminGetStats() {
  return apiFetch<AdminStats>("/api/admin/stats");
}

// ── Admin Colleges ────────────────────────────────────────────────────────────

export async function adminListColleges(page = 1, pageSize = 20) {
  return apiFetch<PagedResponse<College>>(
    `/api/admin/colleges?page=${page}&page_size=${pageSize}`
  );
}

export async function adminCreateCollege(body: {
  name: string;
  contact_email: string;
  physical_address: string;
  admin_users?: string[];
}) {
  return apiFetch<College>("/api/admin/colleges", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function adminDeleteCollege(id: string) {
  return apiFetch<{ college_id: string; message: string }>(
    `/api/admin/colleges/${id}`,
    { method: "DELETE" }
  );
}

// ── Admin Communities ─────────────────────────────────────────────────────────

export async function adminListCommunities(page = 1, pageSize = 20) {
  return apiFetch<PagedResponse<Community>>(
    `/api/admin/communities?page=${page}&page_size=${pageSize}`
  );
}

export async function adminDeleteCommunity(id: string) {
  return apiFetch<{ community_id: string; message: string }>(
    `/api/admin/communities/${id}`,
    { method: "DELETE" }
  );
}

// ── Admin Posts ───────────────────────────────────────────────────────────────

export async function adminListPosts(page = 1, pageSize = 20) {
  return apiFetch<PostListResponse>(
    `/api/admin/posts?page=${page}&page_size=${pageSize}`
  );
}

export async function adminDeletePost(id: string) {
  return apiFetch<{ message: string }>(`/api/admin/posts/${id}`, {
    method: "DELETE",
  });
}

// ── Admin Comments ────────────────────────────────────────────────────────────

export interface Comment {
  id: string;
  post_id: string;
  user_id: string;
  content: string;
  created_at: string;
  updated_at: string;
}

export interface CommentListResponse {
  items: Comment[];
  total: number;
  page: number;
  page_size: number;
}

export async function adminListComments(page = 1, pageSize = 20) {
  return apiFetch<CommentListResponse>(
    `/api/admin/comments?page=${page}&page_size=${pageSize}`
  );
}

export async function adminDeleteComment(id: string) {
  return apiFetch<{ message: string }>(`/api/admin/comments/${id}`, {
    method: "DELETE",
  });
}

// ── Admin Attachments ─────────────────────────────────────────────────────────

export interface Attachment {
  id: string;
  user_id: string;
  filename: string;
  content_type: string;
  size: number;
  created_at: string;
}

export interface AttachmentListResponse {
  items: Attachment[];
  total: number;
  page: number;
  page_size: number;
}

export async function adminListAttachments(page = 1, pageSize = 20) {
  return apiFetch<AttachmentListResponse>(
    `/api/admin/attachments?page=${page}&page_size=${pageSize}`
  );
}

export async function adminDeleteAttachment(id: string) {
  return apiFetch<{ message: string }>(`/api/admin/attachments/${id}`, {
    method: "DELETE",
  });
}
