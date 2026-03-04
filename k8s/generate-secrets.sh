#!/usr/bin/env bash
# Generates k8s/auth_service/secret.yaml from services/auth_service/.env
# Usage: bash k8s/generate-secrets.sh
# The output file is git-ignored — never commit it.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/../services/auth_service/.env"
OUT_FILE="$SCRIPT_DIR/auth_service/secret.yaml"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "ERROR: .env file not found at $ENV_FILE"
  exit 1
fi

# Parse .env safely (handles unquoted values with spaces, skips comments/blanks)
parse_env() {
  local key="$1"
  grep -E "^${key}=" "$ENV_FILE" | head -1 | sed "s/^${key}=//" | sed 's/^"//' | sed 's/"$//'
}

DATABASE_URL="$(parse_env DATABASE_URL)"
SECRET_KEY="$(parse_env SECRET_KEY)"
GOOGLE_CLIENT_ID="$(parse_env GOOGLE_CLIENT_ID)"

# Override DATABASE_URL for Kubernetes:
# - replace localhost with the k8s service name
# - ensure asyncpg driver prefix
K8S_DATABASE_URL="${DATABASE_URL//localhost/postgres-service}"
K8S_DATABASE_URL="${K8S_DATABASE_URL//postgresql:\/\//postgresql+asyncpg://}"

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
  POSTGRES_USER: "campus_assist"
  POSTGRES_PASSWORD: "campus_assist"
  POSTGRES_DB: "campus_assist_db"
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
