import type {
  TokenResponse,
  UserResponse,
  AdminUserListResponse,
  StatsResponse,
  HealthResponse,
  CollegeListResponse,
  CollegeResponse,
  CommunityListResponse,
  CommunityResponse,
  PostListResponse,
  PostResponse,
  CommentListResponse,
  CommentResponse,
  AttachmentListResponse,
  AttachmentResponse,
  AdminUserResponse,
} from "@/types/api";

const BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "";

/** In browser use same-origin proxy to avoid CORS; on server call API directly. */
function apiUrl(path: string): string {
  if (typeof window !== "undefined") {
    return `/api/proxy${path.startsWith("/") ? path : `/${path}`}`;
  }
  return `${BASE}${path.startsWith("/") ? path : `/${path}`}`;
}

function getStoredTokens(): { access: string; refresh: string } | null {
  if (typeof window === "undefined") {
    console.log(`[getStoredTokens] Running on server, no localStorage`);
    return null;
  }
  const access = localStorage.getItem("access_token");
  const refresh = localStorage.getItem("refresh_token");
  console.log(`[getStoredTokens] Access token exists: ${!!access}, Refresh token exists: ${!!refresh}`, {
    accessLength: access?.length,
    refreshLength: refresh?.length,
  });
  if (!access || !refresh) return null;
  return { access, refresh };
}

function setStoredTokens(access: string, refresh: string) {
  if (typeof window === "undefined") return;
  localStorage.setItem("access_token", access);
  localStorage.setItem("refresh_token", refresh);
  document.cookie = "admin_authenticated=1; path=/; max-age=86400; samesite=lax";
}

function clearStoredTokens() {
  if (typeof window === "undefined") return;
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  localStorage.removeItem("user");
  document.cookie = "admin_authenticated=; path=/; max-age=0";
}

async function refreshTokens(): Promise<TokenResponse | null> {
  const tokens = getStoredTokens();
  if (!tokens) return null;
  const res = await fetch(apiUrl("/api/auth/refresh"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: tokens.refresh }),
  });
  if (!res.ok) return null;
  const data: TokenResponse = await res.json();
  setStoredTokens(data.access_token, data.refresh_token);
  if (typeof window !== "undefined") {
    localStorage.setItem("user", JSON.stringify(data.user));
  }
  return data;
}

async function fetchWithAuth(
  path: string,
  options: RequestInit = {},
  retried = false
): Promise<Response> {
  const tokens = getStoredTokens();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...((options.headers as Record<string, string>) || {}),
  };
  if (tokens) headers.Authorization = `Bearer ${tokens.access}`;

  const fullUrl = apiUrl(path);
  console.log(`[API] ${options.method || 'GET'} ${fullUrl}`, {
    hasToken: !!tokens,
    tokenPrefix: tokens ? tokens.access.substring(0, 20) + '...' : 'none',
  });

  const res = await fetch(fullUrl, { ...options, headers });
  
  console.log(`[API RESPONSE] ${fullUrl} -> ${res.status} ${res.statusText}`);

  if (res.status === 401 && !retried) {
    console.log(`[API] Token expired, refreshing...`);
    const refreshed = await refreshTokens();
    if (refreshed) {
      console.log(`[API] Token refreshed, retrying...`);
      return fetchWithAuth(path, options, true);
    }
  }
  return res;
}

// —— Auth ——
export async function login(email: string, password: string): Promise<TokenResponse> {
  const res = await fetch(apiUrl("/api/auth/login"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    const detail = (err as { detail?: string | { msg?: string }[] }).detail;
    const message =
      typeof detail === "string"
        ? detail
        : Array.isArray(detail) && detail[0]?.msg
          ? detail[0].msg
          : "Login failed";
    throw new Error(message);
  }
  return res.json();
}

export async function logout(refreshToken: string): Promise<void> {
  try {
    await fetch(apiUrl("/api/auth/logout"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
  } finally {
    clearStoredTokens();
  }
}

export async function getMe(): Promise<UserResponse> {
  const res = await fetchWithAuth("/api/auth/me");
  if (!res.ok) throw new Error("Not authenticated");
  return res.json();
}

// —— Admin unified (SUPER_ADMIN) ——
export async function getAdminHealth(): Promise<HealthResponse> {
  const res = await fetch(apiUrl("/api/admin/health"));
  if (!res.ok) throw new Error("Health check failed");
  return res.json();
}

export async function getAdminStats(): Promise<StatsResponse> {
  const res = await fetchWithAuth("/api/admin/stats");
  if (!res.ok) throw new Error("Failed to load stats");
  return res.json();
}

export async function getAdminUsers(page = 1, pageSize = 20): Promise<AdminUserListResponse> {
  const res = await fetchWithAuth(
    `/api/auth/admin/users?page=${page}&page_size=${pageSize}`
  );
  if (!res.ok) throw new Error("Failed to load users");
  const data = await res.json();
  return {
    items: data.items ?? [],
    total: data.total ?? 0,
    page: data.page ?? page,
    page_size: data.page_size ?? pageSize,
  };
}

export async function getAdminUser(userId: string): Promise<AdminUserResponse> {
  const res = await fetchWithAuth(`/api/auth/admin/users/${userId}`);
  if (!res.ok) throw new Error("User not found");
  return res.json();
}

export async function updateUserType(userId: string, type: "USER" | "COLLEGE" | "SUPER_ADMIN"): Promise<AdminUserResponse> {
  const res = await fetchWithAuth(`/api/auth/admin/users/${userId}/type`, {
    method: "PATCH",
    body: JSON.stringify({ type }),
  });
  if (!res.ok) throw new Error("Failed to update user type");
  return res.json();
}

export async function updateUserActive(userId: string, isActive: boolean): Promise<AdminUserResponse> {
  const res = await fetchWithAuth(`/api/auth/admin/users/${userId}/active`, {
    method: "PATCH",
    body: JSON.stringify({ is_active: isActive }),
  });
  if (!res.ok) throw new Error("Failed to update user");
  return res.json();
}

export async function getAdminColleges(page = 1, pageSize = 20): Promise<CollegeListResponse> {
  const res = await fetchWithAuth(
    `/api/college/admin/list?page=${page}&page_size=${pageSize}`
  );
  if (!res.ok) throw new Error("Failed to load colleges");
  const data = await res.json();
  return {
    items: data.items ?? [],
    total: data.total ?? 0,
    page: data.page ?? page,
    page_size: data.page_size ?? pageSize,
  };
}

export async function getAdminCollege(collegeId: string): Promise<CollegeResponse> {
  const res = await fetchWithAuth(`/api/college/${collegeId}`);
  if (!res.ok) throw new Error("College not found");
  return res.json();
}

export async function deleteAdminCollege(collegeId: string): Promise<void> {
  const res = await fetchWithAuth(`/api/college/admin/${collegeId}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to delete college");
}

export async function getAdminCommunities(page = 1, pageSize = 20): Promise<CommunityListResponse> {
  console.log(`[getAdminCommunities] Fetching page=${page}, pageSize=${pageSize}`);
  console.log(`[getAdminCommunities] Using service-specific endpoint: /api/community/admin/list`);
  
  // Use service-specific endpoint instead of incomplete admin service endpoint
  const res = await fetchWithAuth(
    `/api/community/admin/list?page=${page}&page_size=${pageSize}`
  );
  
  console.log(`[getAdminCommunities] Response status: ${res.status}`);
  
  if (!res.ok) {
    const errorText = await res.text();
    console.error(`[getAdminCommunities] Error response body:`, errorText);
    
    let errorData: Record<string, unknown> = {};
    try {
      errorData = JSON.parse(errorText);
    } catch (err) {
      console.error(`[getAdminCommunities] Could not parse error response as JSON`);
      console.error(err);
    }
    
    const errorMsg = (errorData as { detail?: string }).detail || errorText || `HTTP ${res.status}`;
    console.error(`[getAdminCommunities] Final error message:`, errorMsg);
    throw new Error(`Failed to load communities: ${errorMsg}`);
  }
  
  const data = await res.json();
  console.log(`[getAdminCommunities] Success response:`, data);
  
  // Handle both array and paginated responses
  if (Array.isArray(data)) {
    console.log(`[getAdminCommunities] Response is array with ${data.length} items`);
    return {
      items: data,
      total: data.length,
      page: page,
      page_size: pageSize,
    };
  }
  
  const result = {
    items: data.items ?? [],
    total: data.total ?? (data.items?.length ?? 0),
    page: data.page ?? page,
    page_size: data.page_size ?? pageSize,
  };
  console.log(`[getAdminCommunities] Returning:`, result);
  return result;
}

export async function getAdminCommunity(communityId: string): Promise<CommunityResponse> {
  const res = await fetchWithAuth(`/api/community/${communityId}`);
  if (!res.ok) throw new Error("Community not found");
  return res.json();
}

export async function deleteAdminCommunity(communityId: string): Promise<void> {
  const res = await fetchWithAuth(`/api/community/admin/${communityId}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to delete community");
}

export async function getAdminPosts(page = 1, pageSize = 20): Promise<PostListResponse> {
  const res = await fetchWithAuth(
    `/api/posts/admin/list?page=${page}&page_size=${pageSize}`
  );
  if (!res.ok) throw new Error("Failed to load posts");
  const data = await res.json();
  return {
    items: data.items ?? [],
    total: data.total ?? 0,
    page: data.page ?? page,
    page_size: data.page_size ?? pageSize,
  };
}

export async function getAdminPost(postId: string): Promise<PostResponse> {
  const res = await fetchWithAuth(`/api/posts/admin/${postId}`);
  if (!res.ok) throw new Error("Post not found");
  return res.json();
}

export async function deleteAdminPost(postId: string): Promise<void> {
  const res = await fetchWithAuth(`/api/posts/admin/${postId}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to delete post");
}

export async function getAdminComments(page = 1, pageSize = 20): Promise<CommentListResponse> {
  const res = await fetchWithAuth(
    `/api/comments/admin/list?page=${page}&page_size=${pageSize}`
  );
  if (!res.ok) throw new Error("Failed to load comments");
  const data = await res.json();
  return {
    items: data.items ?? [],
    total: data.total ?? 0,
    page: data.page ?? page,
    page_size: data.page_size ?? pageSize,
  };
}

export async function getAdminComment(commentId: string): Promise<CommentResponse> {
  const res = await fetchWithAuth(`/api/comments/admin/${commentId}`);
  if (!res.ok) throw new Error("Comment not found");
  return res.json();
}

export async function deleteAdminComment(commentId: string): Promise<void> {
  const res = await fetchWithAuth(`/api/comments/admin/${commentId}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to delete comment");
}

export async function getAdminAttachments(page = 1, pageSize = 20): Promise<AttachmentListResponse> {
  const res = await fetchWithAuth(
    `/api/attachments/admin/list?page=${page}&page_size=${pageSize}`
  );
  if (!res.ok) throw new Error("Failed to load attachments");
  const data = await res.json();
  return {
    items: data.items ?? [],
    total: data.total ?? 0,
    page: data.page ?? page,
    page_size: data.page_size ?? pageSize,
  };
}

export async function getAdminAttachment(attachmentId: string): Promise<AttachmentResponse> {
  const res = await fetchWithAuth(`/api/attachments/admin/${attachmentId}`);
  if (!res.ok) throw new Error("Attachment not found");
  return res.json();
}

export async function deleteAdminAttachment(attachmentId: string): Promise<void> {
  const res = await fetchWithAuth(`/api/attachments/admin/${attachmentId}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to delete attachment");
}

/** Returns the raw response for streaming download (call .blob() or .arrayBuffer() in the client). */
export async function getAttachmentDownloadResponse(attachmentId: string): Promise<Response> {
  return fetchWithAuth(`/api/attachments/${attachmentId}/download`);
}

// College service: create / update (SUPER_ADMIN can do these)
export async function createCollege(body: {
  name: string;
  contact_email: string;
  physical_address: string;
  admin_users?: string[];
}): Promise<CollegeResponse> {
  const res = await fetchWithAuth("/api/college", {
    method: "POST",
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail || "Failed to create college");
  }
  return res.json();
}

export async function updateCollege(
  collegeId: string,
  body: Partial<{ name: string; contact_email: string; physical_address: string; admin_users: string[] }>
): Promise<CollegeResponse> {
  const res = await fetchWithAuth(`/api/college/${collegeId}`, {
    method: "PATCH",
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail || "Failed to update college");
  }
  return res.json();
}

export async function getCollegeCommunities(collegeId: string, page = 1, pageSize = 20): Promise<CommunityListResponse> {
  const res = await fetchWithAuth(`/api/college/${collegeId}/communities?page=${page}&page_size=${pageSize}`);
  if (!res.ok) throw new Error("Failed to load college communities");
  const data = await res.json();
  
  // Handle both paginated response and direct array response
  if (Array.isArray(data)) {
    return {
      items: data,
      total: data.length,
      page: page,
      page_size: pageSize,
    };
  }
  
  return {
    items: data.items ?? [],
    total: data.total ?? (data.items?.length ?? 0),
    page: data.page ?? page,
    page_size: data.page_size ?? pageSize,
  };
}

export { getStoredTokens, setStoredTokens, clearStoredTokens };
