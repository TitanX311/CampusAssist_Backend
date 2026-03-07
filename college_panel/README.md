# Campus Assist — College Panel

Next.js admin/management frontend for the Campus Assist platform. Provides the UI for college administrators and super-admins to manage colleges, communities, users, and content.

---

## Features

- **Authentication** — Google OAuth login via `auth_service`; JWT stored in `localStorage`, auto-refreshed on expiry
- **Dashboard** — Overview of the college the signed-in admin manages
- **College Management** — Edit college details (name, contact email, physical address)
- **Community Browser** — View all communities in a college; join/leave or cancel a pending membership request
- **Members & Admins** — See college members and admins with profile pictures and contact info
- **Requests Tab** — Approve or reject pending join requests for private communities (shows user name + email)
- **Super-Admin panel** — Manage users (type, active status, profile) and all colleges across the platform

---

## Tech Stack

| Layer | Choice |
|---|---|
| Framework | [Next.js 15](https://nextjs.org) (App Router) |
| Styling | [Tailwind CSS](https://tailwindcss.com) |
| Language | TypeScript |
| HTTP client | `fetch` (via `lib/api.ts`) |
| Auth state | React Context (`lib/auth-context.tsx`) |

---

## Getting Started

### Prerequisites

- Node.js ≥ 18
- The backend services running and reachable (see root [README.md](../README.md))

### Install & run

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

### Environment variables

Create a `.env.local` file (not committed):

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8080
```

If `NEXT_PUBLIC_API_BASE_URL` is not set, `lib/api.ts` defaults to `http://localhost:8080`.

---

## Project Structure

```
app/
  layout.tsx          — root layout, AuthProvider wrapper
  page.tsx            — landing / redirect to dashboard
  login/
    page.tsx          — Google OAuth login page
  dashboard/
    layout.tsx        — sidebar + auth guard
    page.tsx          — dashboard home
    college/
      [id]/           — per-college pages (communities, members, admins, requests)
lib/
  api.ts              — typed fetch wrappers for every backend endpoint
  auth-context.tsx    — JWT storage, decode, refresh, logout
public/               — static assets
```

---

## API Layer (`lib/api.ts`)

All backend calls go through `lib/api.ts`. Key function groups:

| Group | Functions |
|---|---|
| Auth | `login()`, `refreshToken()`, `logout()` |
| Profile | `getMe()`, `updateMe()`, `getUserProfile()` |
| College | `listColleges()`, `getCollege()`, `createCollege()`, `updateCollege()`, `deleteCollege()` |
| Community | `listCommunities()`, `getCommunity()`, `joinCommunity()`, `cancelJoinRequest()`, `leaveCommunity()` |
| Admin — Users | `adminListUsers()`, `adminUpdateUserType()`, `adminUpdateUserActive()`, `adminUpdateUserProfile()` |
| Admin — Stats | `adminGetStats()` |

---

## Building for Production

```bash
npm run build
npm start
```
