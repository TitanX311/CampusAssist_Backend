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
    OVERLAY_DIR="$SCRIPT_DIR/overlays/dev"
    PG_SERVICE="postgres-service"
    COMMUNITY_PG_SERVICE="community-postgres-service"
    ;;
  prod)
    AUTH_ENV_FILE="$SCRIPT_DIR/../services/auth_service/.env.prod"
    COMMUNITY_ENV_FILE="$SCRIPT_DIR/../services/community_service/.env.prod"
    OVERLAY_DIR="$SCRIPT_DIR/overlays/prod"
    PG_SERVICE="postgres-service"
    COMMUNITY_PG_SERVICE="community-postgres-service"
    ;;
  *)
    echo "ERROR: Unknown environment '$ENV'. Use 'dev' or 'prod'."
    exit 1
    ;;
esac

echo "Generating secrets for environment: $ENV"
echo "  Auth .env       : $AUTH_ENV_FILE"
echo "  Community .env  : $COMMUNITY_ENV_FILE"
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

echo ""
echo "Done. Apply with:"
echo "  kubectl apply -k k8s/overlays/$ENV"
