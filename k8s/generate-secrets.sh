#!/usr/bin/env bash
# Generates k8s/auth_service/secret.yaml and k8s/postgres/secret.yaml
# from services/auth_service/.env
# Usage: bash k8s/generate-secrets.sh
# Output files are git-ignored — never commit them.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/../services/auth_service/.env"
OUT_FILE="$SCRIPT_DIR/auth_service/secret.yaml"
PG_OUT_FILE="$SCRIPT_DIR/postgres/secret.yaml"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "ERROR: .env file not found at $ENV_FILE"
  exit 1
fi

# Parse a value from .env safely:
#   - skips blank lines and comment-only lines
#   - strips surrounding double OR single quotes
#   - strips trailing inline comments (everything after unquoted ' #')
#   - trims leading/trailing whitespace from the value
parse_env() {
  local key="$1"
  grep -E "^${key}=" "$ENV_FILE" \
    | head -1 \
    | sed "s/^${key}=//" \
    | sed "s/[[:space:]]*#.*$//" \
    | sed "s/^[[:space:]]*//; s/[[:space:]]*$//" \
    | sed "s/^['\"]//; s/['\"]$//"
}

DATABASE_URL="$(parse_env DATABASE_URL)"
SECRET_KEY="$(parse_env SECRET_KEY)"
GOOGLE_CLIENT_ID="$(parse_env GOOGLE_CLIENT_ID)"

# ---- Validate required keys are present and non-empty ---------------
missing=0
for var in DATABASE_URL SECRET_KEY GOOGLE_CLIENT_ID; do
  if [[ -z "${!var}" ]]; then
    echo "ERROR: $var is missing or empty in $ENV_FILE"
    missing=1
  fi
done
[[ $missing -eq 1 ]] && exit 1

# ---- Derive Postgres credentials from DATABASE_URL ------------------
# Supports: postgresql://user:pass@host:port/db  and  postgres://...
_no_scheme="${DATABASE_URL#*://}"        # user:pass@host:port/db
_userinfo="${_no_scheme%%@*}"            # user:pass
PG_USER="${_userinfo%%:*}"              # user
PG_PASSWORD="${_userinfo#*:}"           # pass
_hostpath="${_no_scheme#*@}"            # host:port/db
PG_DB="${_hostpath##*/}"                # db (strip host:port)
PG_DB="${PG_DB%%\?*}"                   # strip optional query string

for var in PG_USER PG_PASSWORD PG_DB; do
  if [[ -z "${!var}" ]]; then
    echo "ERROR: Could not parse $var from DATABASE_URL."
    echo "       Ensure the URL is in the form: postgresql://user:password@host:5432/dbname"
    exit 1
  fi
done

# ---- Build the k8s DATABASE_URL -------------------------------------
# Replace localhost / 127.0.0.1 with the k8s service name.
K8S_DATABASE_URL="${DATABASE_URL//localhost/postgres-service}"
K8S_DATABASE_URL="${K8S_DATABASE_URL//127.0.0.1/postgres-service}"
# Normalise to postgresql+asyncpg:// (handle both common scheme variants).
# Process the longer prefix first so the shorter one can't double-rewrite it.
K8S_DATABASE_URL="${K8S_DATABASE_URL//postgresql:\/\//postgresql+asyncpg://}"
K8S_DATABASE_URL="${K8S_DATABASE_URL//postgres:\/\//postgresql+asyncpg://}"

# ---- Generate postgres/secret.yaml ----------------------------------
PG_OUT_FILE="$SCRIPT_DIR/postgres/secret.yaml"

cat > "$PG_OUT_FILE" <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: postgres-secret
  namespace: default
  labels:
    app: postgres
type: Opaque
stringData:
  POSTGRES_USER: "${PG_USER}"
  POSTGRES_PASSWORD: "${PG_PASSWORD}"
  POSTGRES_DB: "${PG_DB}"
EOF

echo "Generated: $PG_OUT_FILE"

cat > "$OUT_FILE" <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: auth-service-secret
  namespace: default
  labels:
    app: auth-service
type: Opaque
stringData:
  DATABASE_URL: "${K8S_DATABASE_URL}"
  SECRET_KEY: "${SECRET_KEY}"
  GOOGLE_CLIENT_ID: "${GOOGLE_CLIENT_ID}"
EOF

echo "Generated: $OUT_FILE"
