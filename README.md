# Campus Assist

A microservices-based campus social platform. Students connect through college-scoped communities, share posts and comments, and manage their profiles — all behind a unified API gateway.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Nginx Ingress                            │
│  /api/auth  /api/users  /api/college  /api/community  …        │
└────┬────────────┬──────────┬──────────┬──────────┬─────────────┘
     │            │          │          │          │
  auth-svc    user-svc  college-svc  community  post/comment
  (gRPC:50051) (HTTP)    (HTTP+gRPC)  -svc       -svc
     │            │          │
     └────────────┴──────────┘
          shared JWT validation
          (gRPC fan-out for stats)
```

**Infrastructure per service:** FastAPI · PostgreSQL · (Redis for feed/search) · MinIO for attachments · Kubernetes (kustomize)

---

## Services

| Service | Ingress Prefix | OpenAPI | Description |
|---|---|---|---|
| `auth_service` | `/api/auth` | `/api/auth/openapi.json` | Google OAuth + JWT session management. Source of truth for user identity. |
| `user_service` | `/api/users` | `/api/users/openapi.json` | User profiles with aggregated stats (posts, comments, communities). Caches via gRPC fan-out. |
| `college_service` | `/api/college` | `/api/college/openapi.json` | College CRUD, admin management, community/user listings per college. |
| `community_service` | `/api/community` | `/api/community/openapi.json` | Community creation, membership (join/leave/request/approve/reject), public/private modes. Responses include `is_member`, `is_requested`, `member_count`, `post_count` from join tables. |
| `post_service` | `/api/posts` | `/api/posts/openapi.json` | Post CRUD scoped to communities with attachment references. Responses include `liked_by_me` and `comment_count`. Like/unlike via `POST /posts/{id}/like` and `DELETE /posts/{id}/like`. |
| `comment_service` | `/api/comments` | `/api/comments/openapi.json` | Threaded comments on posts. Responses include `liked_by_me` and `reply_count`. Like/unlike via `POST /comments/{id}/like` and `DELETE /comments/{id}/like`. |
| `attachment_service` | `/api/attachments` | `/api/attachments/openapi.json` | File upload/download backed by MinIO object storage. |
| `feed_service` | `/api/feed` | `/api/feed/openapi.json` | Two feed modes: `GET /api/feed/my` (personalised, recency-first) and `GET /api/feed/india` (all-India, engagement-ranked, shared Redis cache). |
| `search_service` | `/api/search` | `/api/search/openapi.json` | Full-text search across posts, communities, and users. |
| `admin_service` | `/api/admin` | `/api/admin/openapi.json` | SUPER_ADMIN proxy — aggregates all services with live gRPC role verification. No database. |
| `docs_service` | `/api/docs` | — | Dev-only Swagger UI hub aggregating all service OpenAPI specs. |

---

## API Documentation

When running in dev mode, visit **`http://localhost:8080/api/docs`** for the aggregated Swagger UI.

Direct per-service docs (dev only):

| Service | Swagger UI |
|---|---|
| Auth | `/api/auth/docs` |
| User | `/api/users/docs` |
| College | `/api/college/docs` |
| Community | `/api/community/docs` |
| Post | `/api/posts/docs` |
| Comment | `/api/comments/docs` |
| Attachment | `/api/attachments/docs` |
| Feed | `/api/feed/docs` |
| Search | `/api/search/docs` |
| Admin | `/api/admin/docs` |

---

## Prerequisites

- **Docker / nerdctl** (for building images)
- **kubectl** + **minikube** (or any k8s cluster)
- **kustomize** (bundled with kubectl ≥ 1.14)
- **Node.js ≥ 18** (for the college panel frontend)
- **Python ≥ 3.11** + **venv** (for running scripts)

---

## Development Setup

### 1. Generate secrets

```bash
bash k8s/generate-secrets.sh dev
```

This creates the `secret.yaml` files (git-ignored) required by the dev overlay.

### 2. Build all service images

```bash
# Build every service
./build.sh auth community post comment attachment college admin search user feed docs

# Or build specific services
./build.sh auth user
```

### 3. Deploy to Kubernetes (dev)

```bash
kubectl apply -k k8s/overlays/dev

# Wait for all pods
kubectl rollout status deployment --all -n dev --timeout=180s
```

### 4. Expose the ingress locally

```bash
kubectl port-forward -n ingress-nginx svc/ingress-nginx-controller 8080:80 --address 0.0.0.0
```

The API is now reachable at `http://localhost:8080`.

### 5. (Optional) Seed test data

```bash
source venv/bin/activate
python scripts/seed_data.py
```

### 6. Run the college panel frontend

```bash
cd college_panel
npm install
npm run dev
# Opens at http://localhost:3000
```

---

## Rebuilding & Redeploying a Service

```bash
# Rebuild one or more services
./build.sh <service>   # e.g. ./build.sh college user

# Rolling restart
kubectl rollout restart deployment/<service>-service -n dev

# Watch status
kubectl rollout status deployment/<service>-service -n dev
```

---

## Teardown

```bash
kubectl delete -k k8s/overlays/dev
```

---

## User Roles

| Role | Access |
|---|---|
| `USER` | Standard account — can join communities, post, comment, manage own profile |
| `COLLEGE` | College-admin account — can manage the college they administer |
| `SUPER_ADMIN` | Full access via `/api/admin/*` — manage all users, colleges, communities, posts, attachments |

---

## Key Design Decisions

- **Auth via gRPC** — `auth_service` exposes a gRPC server (port 50051) so other services verify tokens without HTTP round-trips.
- **Stats caching** — `user_service` fans out to post/comment/community services to compute per-user stats, caching results for `STATS_CACHE_TTL_SECONDS` (default 300 s). A `SELECT … FOR UPDATE` lock prevents concurrent cache stampedes.
- **Admin bypass routes** — `college_service` exposes `/api/college/admin/*` routes gated by `require_super_admin` that skip the college-membership check, allowing `admin_service` to proxy CRUD operations for SUPER_ADMINs.
- **Join tables for engagement (ACID)** — Likes are tracked in dedicated join tables (`PostLike`, `CommentLike`) and membership in `CommunityMember` / `CommunityJoinRequest`. Inserts use `INSERT … ON CONFLICT DO NOTHING RETURNING` — idempotent by design with no lost-update risk. Counters are bumped/decremented only when a row is actually inserted/deleted, guarded by `func.greatest(count - 1, 0)`. All join rows carry `ON DELETE CASCADE` so cleanup is automatic.
- **Viewer-aware responses** — `liked_by_me: bool | None`, `reply_count`, `comment_count`, `is_member`, `is_requested`, `member_count`, and `post_count` are injected at the HTTP layer using a single batch query (`get_viewer_like_map`, `get_viewer_membership_map`) — no N+1 round-trips regardless of page size.
- **Idempotent community join** — `POST /api/community/{id}/join` is idempotent: backed by `CommunityMember` / `CommunityJoinRequest` join tables so duplicate calls never corrupt state.
- **Dual feed modes** — `GET /api/feed/my` returns a personalised recency-first feed from communities the viewer has joined. `GET /api/feed/india` returns an engagement-ranked feed across all PUBLIC communities, shared and cached in Redis (`INDIA_FEED_CACHE_TTL_SECONDS`, default 300 s) to avoid per-user fan-out.
- **Attachment streaming** — The attachments ingress disables nginx request buffering (`proxy-request-buffering: off`) so large uploads stream directly to the service without being held in memory.

---

## Proto Definitions

gRPC contracts live in [`proto/`](proto/):

| File | Used by |
|---|---|
| `auth.proto` | All services (token verification) |
| `post.proto` | `user_service`, `feed_service` (stats fan-out) |
| `community.proto` | `user_service`, `feed_service` |
| `attachment.proto` | `attachment_service` |
| `college.proto` | `college_service` |

Pre-generated stubs are in [`proto/generated/`](proto/generated/).
