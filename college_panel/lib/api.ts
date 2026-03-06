// Typed API client for the campus-assist backend.
// All methods read the token from localStorage via getToken().
// Requests go to /api/* which is proxied by next.config.ts → backend.

const BASE = "";

export type CommunityType = "PUBLIC" | "PRIVATE";

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

export interface CollegeUser {
  college_id: string;
  user_id: string;
  joined_at: string;
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

// ── Posts ─────────────────────────────────────────────────────────────────────

export interface Post {
  id: string;
  user_id: string;
  community_id: string;
  content: string;
  likes: number;
  views: number;
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
