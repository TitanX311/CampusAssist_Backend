"""
Dummy-data seeder for Campus Assist.

Seeds:
  • 3 colleges  (IIT Bombay, Delhi University, BITS Pilani)
  • 3 communities per college (9 total)
  • 5 posts per community (45 total)

Auth flow:
  1. Login as super-admin  → get SUPER_ADMIN token
  2. Register 3 college-admin users, promote each to COLLEGE type
  3. Each college-admin creates their college  (POST /api/college)
  4. Super-admin creates communities linked to each college
     (POST /api/community)
  5. Regular users (college-admins reused for brevity) join communities
  6. Those users create posts inside the communities

Run:
  python scripts/seed_data.py [--base-url http://<minikube-ip>]
"""

import argparse
import json
import sys
import time

import requests

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

SUPER_ADMIN_EMAIL    = "superadmin@campus-assist.dev"
SUPER_ADMIN_PASSWORD = "SuperAdmin@123"

COLLEGE_USERS = [
    {"email": "iit.admin@seed.dev",   "password": "CollegePass@1", "name": "IIT Admin"},
    {"email": "du.admin@seed.dev",    "password": "CollegePass@2", "name": "DU Admin"},
    {"email": "bits.admin@seed.dev",  "password": "CollegePass@3", "name": "BITS Admin"},
]

COLLEGES = [
    {
        "name": "IIT Bombay",
        "contact_email": "contact@iitb.ac.in",
        "physical_address": "Powai, Mumbai, Maharashtra 400076",
    },
    {
        "name": "Delhi University",
        "contact_email": "contact@du.ac.in",
        "physical_address": "University Rd, Delhi 110007",
    },
    {
        "name": "BITS Pilani",
        "contact_email": "contact@bits-pilani.ac.in",
        "physical_address": "Vidya Vihar, Pilani, Rajasthan 333031",
    },
]

# 3 communities per college
COMMUNITIES_TEMPLATE = [
    {"name_tpl": "{college} — Computer Science",  "type": "PUBLIC"},
    {"name_tpl": "{college} — Sports Club",       "type": "PUBLIC"},
    {"name_tpl": "{college} — Research & Dev",    "type": "PRIVATE"},
]

COLLEGE_ABBREVS = ["IITB", "DU", "BITS"]

POSTS_TEMPLATE = [
    "Hey everyone! Excited to be part of this community 🎉",
    "Does anyone have good resources for competitive programming?",
    "Upcoming hackathon next weekend — who's participating?",
    "Just completed my first open-source contribution. Here's what I learned:",
    "Study group forming for the upcoming semester exams — DM to join!",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _h(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def post(base: str, path: str, body: dict, token: str | None = None) -> dict:
    headers = _h(token) if token else {"Content-Type": "application/json"}
    r = requests.post(f"{base}{path}", json=body, headers=headers, timeout=15)
    if not r.ok:
        print(f"  ✗  POST {path}  →  {r.status_code}  {r.text[:200]}")
        return {}
    return r.json()


def patch(base: str, path: str, body: dict, token: str) -> dict:
    r = requests.patch(f"{base}{path}", json=body, headers=_h(token), timeout=15)
    if not r.ok:
        print(f"  ✗  PATCH {path}  →  {r.status_code}  {r.text[:200]}")
        return {}
    return r.json()


def login(base: str, email: str, password: str) -> str:
    data = post(base, "/api/auth/login", {"email": email, "password": password})
    token = data.get("access_token", "")
    if not token:
        print(f"  ✗  Login failed for {email}")
        sys.exit(1)
    print(f"  ✓  Logged in as {email}")
    return token


def register(base: str, email: str, password: str, name: str) -> str:
    data = post(base, "/api/auth/register", {"email": email, "password": password, "name": name})
    if not data:
        # Already registered — just log in
        return login(base, email, password)
    token = data.get("access_token", "")
    user_id = data.get("user", {}).get("id", "")
    print(f"  ✓  Registered {email}  (id={user_id})")
    return token, user_id


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(base_url: str) -> None:
    print(f"\n🌱  Campus Assist Seeder  →  {base_url}\n")

    # ── 1. Super-admin login ───────────────────────────────────────────────
    print("── Step 1: Super-admin login")
    sa_token = login(base_url, SUPER_ADMIN_EMAIL, SUPER_ADMIN_PASSWORD)

    # ── 2. Register college-admin users + promote to COLLEGE type ──────────
    print("\n── Step 2: Register college-admin users")
    college_tokens: list[str] = []
    college_user_ids: list[str] = []
    for cu in COLLEGE_USERS:
        result = post(base_url, "/api/auth/register",
                      {"email": cu["email"], "password": cu["password"], "name": cu["name"]})
        if result:
            token = result["access_token"]
            uid   = result["user"]["id"]
            print(f"  ✓  Registered {cu['email']}  (id={uid})")
        else:
            # Already registered — log in
            token = login(base_url, cu["email"], cu["password"])
            # fetch user id via admin route
            r = requests.get(f"{base_url}/api/auth/admin/users",
                             headers=_h(sa_token), timeout=15)
            users = r.json().get("items", []) if r.ok else []
            uid = next((u["id"] for u in users if u["email"] == cu["email"]), None)
        college_tokens.append(token)
        college_user_ids.append(uid)

        # Promote to COLLEGE type
        promo = patch(base_url, f"/api/auth/admin/users/{uid}/type",
                      {"type": "COLLEGE"}, sa_token)
        if promo:
            print(f"  ✓  Promoted {cu['email']} → COLLEGE")

        # Re-login to get a fresh token (type is now in the JWT payload via gRPC)
        college_tokens[-1] = login(base_url, cu["email"], cu["password"])

    # ── 3. Create colleges ─────────────────────────────────────────────────
    print("\n── Step 3: Create colleges")
    college_ids: list[str] = []
    for idx, college_def in enumerate(COLLEGES):
        body = {**college_def, "admin_users": [college_user_ids[idx]]}
        res = post(base_url, "/api/college", body, college_tokens[idx])
        if res:
            cid = res["id"]
            college_ids.append(cid)
            print(f"  ✓  College '{res['name']}'  (id={cid})")
        else:
            # Already exists — fetch id via admin list
            r = requests.get(f"{base_url}/api/college", headers=_h(college_tokens[idx]), timeout=15)
            items = r.json().get("items", []) if r.ok else []
            match = next((c for c in items if c["name"] == college_def["name"]), None)
            if match:
                college_ids.append(match["id"])
                print(f"  ✓  College '{college_def['name']}' already exists  (id={match['id']})")
            else:
                print(f"  ✗  Could not find/create college '{college_def['name']}'")
                college_ids.append(None)

    # ── 4. Create communities ──────────────────────────────────────────────
    print("\n── Step 4: Create communities")
    community_ids: list[str] = []   # flat list of all community IDs
    # community_matrix[i] = list of community IDs belonging to college i
    community_matrix: list[list[str]] = [[] for _ in COLLEGES]

    for c_idx, (college_id, abbrev) in enumerate(zip(college_ids, COLLEGE_ABBREVS)):
        if not college_id:
            continue
        for tmpl in COMMUNITIES_TEMPLATE:
            name = tmpl["name_tpl"].format(college=abbrev)
            body = {
                "name": name,
                "type": tmpl["type"],
                "parent_colleges": [college_id],
            }
            res = post(base_url, "/api/community", body, sa_token)
            if res:
                cid = res["id"]
                community_ids.append(cid)
                community_matrix[c_idx].append(cid)
                print(f"  ✓  Community '{name}'  ({tmpl['type']}, id={cid})")
            else:
                # Already exists — fetch via admin list
                r = requests.get(f"{base_url}/api/community/admin/list",
                                 headers=_h(sa_token), timeout=15)
                items = r.json().get("items", []) if r.ok else []
                match = next((cm for cm in items if cm["name"] == name), None)
                if match:
                    community_ids.append(match["id"])
                    community_matrix[c_idx].append(match["id"])
                    print(f"  ✓  Community '{name}' already exists  (id={match['id']})")

    # ── 5. Seed users join PUBLIC communities ─────────────────────────────
    print("\n── Step 5: College admins join their communities")
    for c_idx, token in enumerate(college_tokens):
        for cid in community_matrix[c_idx]:
            res = post(base_url, f"/api/community/{cid}/join", {}, token)
            if res:
                print(f"  ✓  Joined community {cid}  (status={res.get('status')})")

    # ── 6. Create posts — only in communities the user is a full member of ─
    print("\n── Step 6: Create posts")
    post_count = 0
    for c_idx, token in enumerate(college_tokens):
        for cid in community_matrix[c_idx]:
            # Re-fetch community to check membership (PUBLIC = creator joined, PRIVATE = only requested)
            r = requests.get(
                f"{base_url}/api/community/{cid}",
                headers=_h(token), timeout=10,
            )
            if not r.ok:
                continue
            community_data = r.json()
            # Only post if this user is an actual member (not just a requester)
            college_uid = college_user_ids[c_idx]
            import uuid as _uuid
            member_uuids = [str(_uuid.UUID(m)) for m in community_data.get("member_users", [])]
            if str(_uuid.UUID(college_uid)) not in member_uuids:
                print(f"  ↷  Skipping PRIVATE community {cid} (user only has join request)")
                continue
            for content in POSTS_TEMPLATE:
                body = {"community_id": cid, "content": content, "attachments": []}
                res = post(base_url, "/api/posts", body, token)
                if res:
                    post_count += 1

    print(f"\n  ✓  Created {post_count} posts")

    # ── Summary ────────────────────────────────────────────────────────────
    print("\n" + "─" * 60)
    print(f"✅  Seeding complete!")
    print(f"   Colleges    : {len([c for c in college_ids if c])}")
    print(f"   Communities : {len(community_ids)}")
    print(f"   Posts       : {post_count}")
    print("─" * 60 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Campus Assist data seeder")
    parser.add_argument(
        "--base-url",
        default=None,
        help="Base URL of the API gateway (e.g. http://192.168.39.101)",
    )
    args = parser.parse_args()

    if args.base_url:
        base = args.base_url.rstrip("/")
    else:
        import subprocess
        ip = subprocess.check_output(["minikube", "ip"]).decode().strip()
        base = f"http://{ip}"
        print(f"Auto-detected minikube IP: {ip}")

    main(base)
