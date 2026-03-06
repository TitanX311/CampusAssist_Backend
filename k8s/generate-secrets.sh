#!/usr/bin/env bash
# Generates k8s secrets from .env files and writes them into the correct overlay.
#
# Usage:
#   bash k8s/generate-secrets.sh [dev|prod]   (default: dev)
#
# Dev  -> reads services/**/.env         -> writes k8s/overlays/dev/**/secret.yaml
# Prod -> reads services/**/.env.prod    -> writes k8s/overlays/prod/**/secret.yaml
#
# Output files are git-ignored — never commit them.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV="${1:-dev}"

case "$ENV" in
  dev)
    AUTH_ENV_FILE="$SCRIPT_DIR/../services/auth_service/.env"
    COMMUNITY_ENV_FILE="$SCRIPT_DIR/../services/community_service/.env"
    POST_ENV_FILE="$SCRIPT_DIR/../services/post_service/.env"
    COMMENT_ENV_FILE="$SCRIPT_DIR/../services/comment_service/.env"
    ATTACHMENT_ENV_FILE="$SCRIPT_DIR/../services/attachment_service/.env"
    COLLEGE_ENV_FILE="$SCRIPT_DIR/../services/college_service/.env"
    ADMIN_ENV_FILE="$SCRIPT_DIR/../services/admin_service/.env"
    SEARCH_ENV_FILE="$SCRIPT_DIR/../services/search_service/.env"
    OVERLAY_DIR="$SCRIPT_DIR/overlays/dev"
    PG_SERVICE="postgres-service"
    COMMUNITY_PG_SERVICE="community-postgres-service"
    POST_PG_SERVICE="post-postgres-service"
    COMMENT_PG_SERVICE="comment-postgres-service"
    ATTACHMENT_PG_SERVICE="attachment-postgres-service"
    COLLEGE_PG_SERVICE="college-postgres-service"
    SEARCH_PG_SERVICE="search-postgres-service"
    ;;
  prod)
    AUTH_ENV_FILE="$SCRIPT_DIR/../services/auth_service/.env.prod"
    COMMUNITY_ENV_FILE="$SCRIPT_DIR/../services/community_service/.env.prod"
    POST_ENV_FILE="$SCRIPT_DIR/../services/post_service/.env.prod"
    COMMENT_ENV_FILE="$SCRIPT_DIR/../services/comment_service/.env.prod"
    ATTACHMENT_ENV_FILE="$SCRIPT_DIR/../services/attachment_service/.env.prod"
    COLLEGE_ENV_FILE="$SCRIPT_DIR/../services/college_service/.env.prod"
    ADMIN_ENV_FILE="$SCRIPT_DIR/../services/admin_service/.env.prod"
    SEARCH_ENV_FILE="$SCRIPT_DIR/../services/search_service/.env.prod"
    OVERLAY_DIR="$SCRIPT_DIR/overlays/prod"
    PG_SERVICE="postgres-service"
    COMMUNITY_PG_SERVICE="community-postgres-service"
    POST_PG_SERVICE="post-postgres-service"
    COMMENT_PG_SERVICE="comment-postgres-service"
    ATTACHMENT_PG_SERVICE="attachment-postgres-service"
    COLLEGE_PG_SERVICE="college-postgres-service"
    SEARCH_PG_SERVICE="search-postgres-service"
    ;;
  *)
    echo "ERROR: Unknown environment '$ENV'. Use 'dev' or 'prod'."
    exit 1
    ;;
esac

echo "Generating secrets for environment: $ENV"
echo "  Auth .env       : $AUTH_ENV_FILE"
echo "  Community .env  : $COMMUNITY_ENV_FILE"
echo "  Post .env       : $POST_ENV_FILE"
echo "  Output dir      : $OVERLAY_DIR"
echo ""

# ---------------------------------------------------------------------------
# Helper: parse a key=value from an .env file.
#   - Strips surrounding single OR double quotes
#   - Strips trailing inline comments  (# ...)
#   - Trims leading/trailing whitespace
# ---------------------------------------------------------------------------
parse_env() {
  local file="$1"
  local key="$2"
  grep -E "^${key}=" "$file" \
    | head -1 \
    | sed "s/^${key}=//" \
    | sed "s/[[:space:]]*#.*$//" \
    | sed "s/^[[:space:]]*//; s/[[:space:]]*$//" \
    | sed "s/^['\"]//; s/['\"]$//"
}

# ---------------------------------------------------------------------------
# Helper: parse credentials out of a DATABASE_URL.
# Populates PG_USER, PG_PASSWORD, PG_DB in caller scope.
# ---------------------------------------------------------------------------
parse_db_url() {
  local url="$1"
  local _no_scheme="${url#*://}"
  local _userinfo="${_no_scheme%%@*}"
  PG_USER="${_userinfo%%:*}"
  PG_PASSWORD="${_userinfo#*:}"
  local _hostpath="${_no_scheme#*@}"
  PG_DB="${_hostpath##*/}"
  PG_DB="${PG_DB%%\?*}"
}

# ---------------------------------------------------------------------------
# Helper: rewrite localhost/127.0.0.1 -> k8s service name and normalise scheme.
# ---------------------------------------------------------------------------
k8s_db_url() {
  local url="$1"
  local svc="$2"
  url="${url//localhost/$svc}"
  url="${url//127.0.0.1/$svc}"
  url="${url//postgresql:\/\//postgresql+asyncpg://}"
  url="${url//postgres:\/\//postgresql+asyncpg://}"
  echo "$url"
}

# ===========================================================================
# AUTH SERVICE + AUTH POSTGRES
# ===========================================================================
if [[ ! -f "$AUTH_ENV_FILE" ]]; then
  echo "ERROR: .env file not found: $AUTH_ENV_FILE"
  exit 1
fi

DATABASE_URL="$(parse_env "$AUTH_ENV_FILE" DATABASE_URL)"
SECRET_KEY="$(parse_env "$AUTH_ENV_FILE" SECRET_KEY)"
GOOGLE_CLIENT_ID="$(parse_env "$AUTH_ENV_FILE" GOOGLE_CLIENT_ID)"

missing=0
for var in DATABASE_URL SECRET_KEY GOOGLE_CLIENT_ID; do
  if [[ -z "${!var}" ]]; then
    echo "ERROR: $var is missing or empty in $AUTH_ENV_FILE"
    missing=1
  fi
done
[[ $missing -eq 1 ]] && exit 1

parse_db_url "$DATABASE_URL"
for var in PG_USER PG_PASSWORD PG_DB; do
  if [[ -z "${!var}" ]]; then
    echo "ERROR: Could not parse $var from DATABASE_URL in $AUTH_ENV_FILE"
    exit 1
  fi
done

K8S_DATABASE_URL="$(k8s_db_url "$DATABASE_URL" "$PG_SERVICE")"

mkdir -p "$OVERLAY_DIR/postgres"
cat > "$OVERLAY_DIR/postgres/secret.yaml" <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: postgres-secret
  labels:
    app: postgres
type: Opaque
stringData:
  POSTGRES_USER: "${PG_USER}"
  POSTGRES_PASSWORD: "${PG_PASSWORD}"
  POSTGRES_DB: "${PG_DB}"
EOF
echo "Generated: $OVERLAY_DIR/postgres/secret.yaml"

mkdir -p "$OVERLAY_DIR/auth_service"
cat > "$OVERLAY_DIR/auth_service/secret.yaml" <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: auth-service-secret
  labels:
    app: auth-service
type: Opaque
stringData:
  DATABASE_URL: "${K8S_DATABASE_URL}"
  SECRET_KEY: "${SECRET_KEY}"
  GOOGLE_CLIENT_ID: "${GOOGLE_CLIENT_ID}"
EOF
echo "Generated: $OVERLAY_DIR/auth_service/secret.yaml"

# ===========================================================================
# COMMUNITY SERVICE + COMMUNITY POSTGRES
# ===========================================================================
if [[ ! -f "$COMMUNITY_ENV_FILE" ]]; then
  echo "ERROR: .env file not found: $COMMUNITY_ENV_FILE"
  exit 1
fi

COMMUNITY_DATABASE_URL="$(parse_env "$COMMUNITY_ENV_FILE" DATABASE_URL)"
COMMUNITY_SECRET_KEY="$(parse_env "$COMMUNITY_ENV_FILE" SECRET_KEY)"

missing=0
for var in COMMUNITY_DATABASE_URL COMMUNITY_SECRET_KEY; do
  if [[ -z "${!var}" ]]; then
    echo "ERROR: $var is missing or empty in $COMMUNITY_ENV_FILE"
    missing=1
  fi
done
[[ $missing -eq 1 ]] && exit 1

parse_db_url "$COMMUNITY_DATABASE_URL"
for var in PG_USER PG_PASSWORD PG_DB; do
  if [[ -z "${!var}" ]]; then
    echo "ERROR: Could not parse $var from DATABASE_URL in $COMMUNITY_ENV_FILE"
    exit 1
  fi
done
COMMUNITY_PG_USER="$PG_USER"
COMMUNITY_PG_PASSWORD="$PG_PASSWORD"
COMMUNITY_PG_DB="$PG_DB"

COMMUNITY_K8S_DATABASE_URL="$(k8s_db_url "$COMMUNITY_DATABASE_URL" "$COMMUNITY_PG_SERVICE")"

mkdir -p "$OVERLAY_DIR/community_postgres"
cat > "$OVERLAY_DIR/community_postgres/secret.yaml" <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: community-postgres-secret
  labels:
    app: community-postgres
type: Opaque
stringData:
  POSTGRES_USER: "${COMMUNITY_PG_USER}"
  POSTGRES_PASSWORD: "${COMMUNITY_PG_PASSWORD}"
  POSTGRES_DB: "${COMMUNITY_PG_DB}"
EOF
echo "Generated: $OVERLAY_DIR/community_postgres/secret.yaml"

mkdir -p "$OVERLAY_DIR/community_service"
cat > "$OVERLAY_DIR/community_service/secret.yaml" <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: community-service-secret
  labels:
    app: community-service
type: Opaque
stringData:
  DATABASE_URL: "${COMMUNITY_K8S_DATABASE_URL}"
  SECRET_KEY: "${COMMUNITY_SECRET_KEY}"
EOF
echo "Generated: $OVERLAY_DIR/community_service/secret.yaml"

# ===========================================================================
# POST SERVICE + POST POSTGRES
# ===========================================================================
if [[ ! -f "$POST_ENV_FILE" ]]; then
  echo "ERROR: .env file not found: $POST_ENV_FILE"
  exit 1
fi

POST_DATABASE_URL="$(parse_env "$POST_ENV_FILE" DATABASE_URL)"
POST_SECRET_KEY="$(parse_env "$POST_ENV_FILE" SECRET_KEY)"

missing=0
for var in POST_DATABASE_URL POST_SECRET_KEY; do
  if [[ -z "${!var}" ]]; then
    echo "ERROR: $var is missing or empty in $POST_ENV_FILE"
    missing=1
  fi
done
[[ $missing -eq 1 ]] && exit 1

parse_db_url "$POST_DATABASE_URL"
for var in PG_USER PG_PASSWORD PG_DB; do
  if [[ -z "${!var}" ]]; then
    echo "ERROR: Could not parse $var from DATABASE_URL in $POST_ENV_FILE"
    exit 1
  fi
done
POST_PG_USER="$PG_USER"
POST_PG_PASSWORD="$PG_PASSWORD"
POST_PG_DB="$PG_DB"

POST_K8S_DATABASE_URL="$(k8s_db_url "$POST_DATABASE_URL" "$POST_PG_SERVICE")"

mkdir -p "$OVERLAY_DIR/post_postgres"
cat > "$OVERLAY_DIR/post_postgres/secret.yaml" <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: post-postgres-secret
  labels:
    app: post-postgres
type: Opaque
stringData:
  POSTGRES_USER: "${POST_PG_USER}"
  POSTGRES_PASSWORD: "${POST_PG_PASSWORD}"
  POSTGRES_DB: "${POST_PG_DB}"
EOF
echo "Generated: $OVERLAY_DIR/post_postgres/secret.yaml"

mkdir -p "$OVERLAY_DIR/post_service"
cat > "$OVERLAY_DIR/post_service/secret.yaml" <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: post-service-secret
  labels:
    app: post-service
type: Opaque
stringData:
  DATABASE_URL: "${POST_K8S_DATABASE_URL}"
  SECRET_KEY: "${POST_SECRET_KEY}"
EOF
echo "Generated: $OVERLAY_DIR/post_service/secret.yaml"

# ===========================================================================
# COMMENT SERVICE + COMMENT POSTGRES
# ===========================================================================
COMMENT_PG_SERVICE="comment-postgres-service"

if [[ ! -f "$COMMENT_ENV_FILE" ]]; then
  echo "ERROR: .env file not found: $COMMENT_ENV_FILE"
  exit 1
fi

COMMENT_DATABASE_URL="$(parse_env "$COMMENT_ENV_FILE" DATABASE_URL)"
COMMENT_SECRET_KEY="$(parse_env "$COMMENT_ENV_FILE" SECRET_KEY)"

missing=0
for var in COMMENT_DATABASE_URL COMMENT_SECRET_KEY; do
  if [[ -z "${!var}" ]]; then
    echo "ERROR: $var is missing or empty in $COMMENT_ENV_FILE"
    missing=1
  fi
done
[[ $missing -eq 1 ]] && exit 1

parse_db_url "$COMMENT_DATABASE_URL"
for var in PG_USER PG_PASSWORD PG_DB; do
  if [[ -z "${!var}" ]]; then
    echo "ERROR: Could not parse $var from DATABASE_URL in $COMMENT_ENV_FILE"
    exit 1
  fi
done
COMMENT_PG_USER="$PG_USER"
COMMENT_PG_PASSWORD="$PG_PASSWORD"
COMMENT_PG_DB="$PG_DB"

COMMENT_K8S_DATABASE_URL="$(k8s_db_url "$COMMENT_DATABASE_URL" "$COMMENT_PG_SERVICE")"

mkdir -p "$OVERLAY_DIR/comment_postgres"
cat > "$OVERLAY_DIR/comment_postgres/secret.yaml" <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: comment-postgres-secret
  labels:
    app: comment-postgres
type: Opaque
stringData:
  POSTGRES_USER: "${COMMENT_PG_USER}"
  POSTGRES_PASSWORD: "${COMMENT_PG_PASSWORD}"
  POSTGRES_DB: "${COMMENT_PG_DB}"
EOF
echo "Generated: $OVERLAY_DIR/comment_postgres/secret.yaml"

mkdir -p "$OVERLAY_DIR/comment_service"
cat > "$OVERLAY_DIR/comment_service/secret.yaml" <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: comment-service-secret
  labels:
    app: comment-service
type: Opaque
stringData:
  DATABASE_URL: "${COMMENT_K8S_DATABASE_URL}"
  SECRET_KEY: "${COMMENT_SECRET_KEY}"
EOF
echo "Generated: $OVERLAY_DIR/comment_service/secret.yaml"

# ===========================================================================
# ATTACHMENT SERVICE + ATTACHMENT POSTGRES + MINIO
# ===========================================================================
if [[ ! -f "$ATTACHMENT_ENV_FILE" ]]; then
  echo "ERROR: .env file not found: $ATTACHMENT_ENV_FILE"
  exit 1
fi

ATTACHMENT_DATABASE_URL="$(parse_env "$ATTACHMENT_ENV_FILE" DATABASE_URL)"
ATTACHMENT_SECRET_KEY="$(parse_env "$ATTACHMENT_ENV_FILE" SECRET_KEY)"
ATTACHMENT_MINIO_ACCESS_KEY="$(parse_env "$ATTACHMENT_ENV_FILE" MINIO_ACCESS_KEY)"
ATTACHMENT_MINIO_SECRET_KEY="$(parse_env "$ATTACHMENT_ENV_FILE" MINIO_SECRET_KEY)"

missing=0
for var in ATTACHMENT_DATABASE_URL ATTACHMENT_SECRET_KEY ATTACHMENT_MINIO_ACCESS_KEY ATTACHMENT_MINIO_SECRET_KEY; do
  if [[ -z "${!var}" ]]; then
    echo "ERROR: $var is missing or empty in $ATTACHMENT_ENV_FILE"
    missing=1
  fi
done
[[ $missing -eq 1 ]] && exit 1

parse_db_url "$ATTACHMENT_DATABASE_URL"
for var in PG_USER PG_PASSWORD PG_DB; do
  if [[ -z "${!var}" ]]; then
    echo "ERROR: Could not parse $var from DATABASE_URL in $ATTACHMENT_ENV_FILE"
    exit 1
  fi
done
ATTACHMENT_PG_USER="$PG_USER"
ATTACHMENT_PG_PASSWORD="$PG_PASSWORD"
ATTACHMENT_PG_DB="$PG_DB"

ATTACHMENT_K8S_DATABASE_URL="$(k8s_db_url "$ATTACHMENT_DATABASE_URL" "$ATTACHMENT_PG_SERVICE")"

mkdir -p "$OVERLAY_DIR/attachment_postgres"
cat > "$OVERLAY_DIR/attachment_postgres/secret.yaml" <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: attachment-postgres-secret
  labels:
    app: attachment-postgres
type: Opaque
stringData:
  POSTGRES_USER: "${ATTACHMENT_PG_USER}"
  POSTGRES_PASSWORD: "${ATTACHMENT_PG_PASSWORD}"
  POSTGRES_DB: "${ATTACHMENT_PG_DB}"
EOF
echo "Generated: $OVERLAY_DIR/attachment_postgres/secret.yaml"

mkdir -p "$OVERLAY_DIR/attachment_service"
cat > "$OVERLAY_DIR/attachment_service/secret.yaml" <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: attachment-service-secret
  labels:
    app: attachment-service
type: Opaque
stringData:
  DATABASE_URL: "${ATTACHMENT_K8S_DATABASE_URL}"
  SECRET_KEY: "${ATTACHMENT_SECRET_KEY}"
  MINIO_ACCESS_KEY: "${ATTACHMENT_MINIO_ACCESS_KEY}"
  MINIO_SECRET_KEY: "${ATTACHMENT_MINIO_SECRET_KEY}"
EOF
echo "Generated: $OVERLAY_DIR/attachment_service/secret.yaml"

# MinIO root credentials mirror the attachment service MinIO access credentials
mkdir -p "$OVERLAY_DIR/minio"
cat > "$OVERLAY_DIR/minio/secret.yaml" <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: minio-secret
  labels:
    app: minio
type: Opaque
stringData:
  MINIO_ROOT_USER: "${ATTACHMENT_MINIO_ACCESS_KEY}"
  MINIO_ROOT_PASSWORD: "${ATTACHMENT_MINIO_SECRET_KEY}"
EOF
echo "Generated: $OVERLAY_DIR/minio/secret.yaml"

# ===========================================================================
# COLLEGE SERVICE + COLLEGE POSTGRES
# ===========================================================================
if [[ ! -f "$COLLEGE_ENV_FILE" ]]; then
  echo "ERROR: .env file not found: $COLLEGE_ENV_FILE"
  exit 1
fi

COLLEGE_DATABASE_URL="$(parse_env "$COLLEGE_ENV_FILE" DATABASE_URL)"
COLLEGE_SECRET_KEY="$(parse_env "$COLLEGE_ENV_FILE" SECRET_KEY)"

missing=0
for var in COLLEGE_DATABASE_URL COLLEGE_SECRET_KEY; do
  if [[ -z "${!var}" ]]; then
    echo "ERROR: $var is missing or empty in $COLLEGE_ENV_FILE"
    missing=1
  fi
done
[[ $missing -eq 1 ]] && exit 1

parse_db_url "$COLLEGE_DATABASE_URL"
for var in PG_USER PG_PASSWORD PG_DB; do
  if [[ -z "${!var}" ]]; then
    echo "ERROR: Could not parse $var from DATABASE_URL in $COLLEGE_ENV_FILE"
    exit 1
  fi
done
COLLEGE_PG_USER="$PG_USER"
COLLEGE_PG_PASSWORD="$PG_PASSWORD"
COLLEGE_PG_DB="$PG_DB"

COLLEGE_K8S_DATABASE_URL="$(k8s_db_url "$COLLEGE_DATABASE_URL" "$COLLEGE_PG_SERVICE")"

mkdir -p "$OVERLAY_DIR/college_postgres"
cat > "$OVERLAY_DIR/college_postgres/secret.yaml" <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: college-postgres-secret
  labels:
    app: college-postgres
type: Opaque
stringData:
  POSTGRES_USER: "${COLLEGE_PG_USER}"
  POSTGRES_PASSWORD: "${COLLEGE_PG_PASSWORD}"
  POSTGRES_DB: "${COLLEGE_PG_DB}"
EOF
echo "Generated: $OVERLAY_DIR/college_postgres/secret.yaml"

mkdir -p "$OVERLAY_DIR/college_service"
cat > "$OVERLAY_DIR/college_service/secret.yaml" <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: college-service-secret
  labels:
    app: college-service
type: Opaque
stringData:
  DATABASE_URL: "${COLLEGE_K8S_DATABASE_URL}"
  SECRET_KEY: "${COLLEGE_SECRET_KEY}"
EOF
echo "Generated: $OVERLAY_DIR/college_service/secret.yaml"

echo ""
echo "Done. Apply with:"
echo "  kubectl apply -k k8s/overlays/$ENV"

# ===========================================================================
# ADMIN SERVICE  (no DB — only needs SECRET_KEY)
# ===========================================================================
if [[ ! -f "$ADMIN_ENV_FILE" ]]; then
  echo "WARNING: Admin .env file not found: $ADMIN_ENV_FILE"
  echo "  Skipping admin_service secret generation."
  echo "  Create $ADMIN_ENV_FILE with SECRET_KEY=<same-as-auth-service>"
else
  ADMIN_SECRET_KEY="$(parse_env "$ADMIN_ENV_FILE" SECRET_KEY)"
  if [[ -z "$ADMIN_SECRET_KEY" ]]; then
    echo "ERROR: SECRET_KEY is missing or empty in $ADMIN_ENV_FILE"
    exit 1
  fi

  mkdir -p "$OVERLAY_DIR/admin_service"
  cat > "$OVERLAY_DIR/admin_service/secret.yaml" <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: admin-service-secret
  labels:
    app: admin-service
type: Opaque
stringData:
  SECRET_KEY: "${ADMIN_SECRET_KEY}"
EOF
  echo "Generated: $OVERLAY_DIR/admin_service/secret.yaml"
fi

# ===========================================================================
# SEARCH SERVICE + SEARCH POSTGRES
# ===========================================================================
if [[ ! -f "$SEARCH_ENV_FILE" ]]; then
  echo "WARNING: Search .env file not found: $SEARCH_ENV_FILE"
  echo "  Skipping search_service secret generation."
  echo "  Create $SEARCH_ENV_FILE with DATABASE_URL and SECRET_KEY."
else
  SEARCH_DATABASE_URL="$(parse_env "$SEARCH_ENV_FILE" DATABASE_URL)"
  SEARCH_SECRET_KEY="$(parse_env "$SEARCH_ENV_FILE" SECRET_KEY)"

  missing=0
  for var in SEARCH_DATABASE_URL SEARCH_SECRET_KEY; do
    if [[ -z "${!var}" ]]; then
      echo "ERROR: $var is missing or empty in $SEARCH_ENV_FILE"
      missing=1
    fi
  done
  [[ $missing -eq 1 ]] && exit 1

  parse_db_url "$SEARCH_DATABASE_URL"
  for var in PG_USER PG_PASSWORD PG_DB; do
    if [[ -z "${!var}" ]]; then
      echo "ERROR: Could not parse $var from DATABASE_URL in $SEARCH_ENV_FILE"
      exit 1
    fi
  done
  SEARCH_PG_USER="$PG_USER"
  SEARCH_PG_PASSWORD="$PG_PASSWORD"
  SEARCH_PG_DB="$PG_DB"

  SEARCH_K8S_DATABASE_URL="$(k8s_db_url "$SEARCH_DATABASE_URL" "$SEARCH_PG_SERVICE")"

  mkdir -p "$OVERLAY_DIR/search_postgres"
  cat > "$OVERLAY_DIR/search_postgres/secret.yaml" <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: search-postgres-secret
  labels:
    app: search-postgres
type: Opaque
stringData:
  POSTGRES_USER: "${SEARCH_PG_USER}"
  POSTGRES_PASSWORD: "${SEARCH_PG_PASSWORD}"
  POSTGRES_DB: "${SEARCH_PG_DB}"
EOF
  echo "Generated: $OVERLAY_DIR/search_postgres/secret.yaml"

  mkdir -p "$OVERLAY_DIR/search_service"
  cat > "$OVERLAY_DIR/search_service/secret.yaml" <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: search-service-secret
  labels:
    app: search-service
type: Opaque
stringData:
  DATABASE_URL: "${SEARCH_K8S_DATABASE_URL}"
  SECRET_KEY: "${SEARCH_SECRET_KEY}"
EOF
  echo "Generated: $OVERLAY_DIR/search_service/secret.yaml"
fi
