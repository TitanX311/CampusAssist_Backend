#!/usr/bin/env bash
# build.sh — build service images using minikube image build
# Usage:
#   ./build.sh                  # build all services
#   ./build.sh auth feed user   # build specific services
#
# Images are built directly into minikube's k8s.io image store
# (no Docker daemon or manual import needed).

set -euo pipefail

TAG="${TAG:-dev}"
REGISTRY="darshanpanzade2006"
SERVICES_DIR="$(cd "$(dirname "$0")/services" && pwd)"

# Map: service_dir_name -> image_suffix
declare -A IMAGE_MAP=(
  [auth_service]="campus_assist_auth"
  [community_service]="campus_assist_community"
  [post_service]="campus_assist_post"
  [comment_service]="campus_assist_comment"
  [attachment_service]="campus_assist_attachment"
  [college_service]="campus_assist_college"
  [admin_service]="campus_assist_admin"
  [search_service]="campus_assist_search"
  [user_service]="campus_assist_user"
  [feed_service]="campus_assist_feed"
  [notification_service]="campus_assist_notification"
  [docs_service]="campus_assist_docs"
)

# Determine which services to build
if [[ $# -gt 0 ]]; then
  # Accept short names (e.g. "auth") or full names (e.g. "auth_service")
  TARGETS=()
  for arg in "$@"; do
    # Normalise: append _service if not already present
    [[ "$arg" == *_service ]] && TARGETS+=("$arg") || TARGETS+=("${arg}_service")
  done
else
  TARGETS=("${!IMAGE_MAP[@]}")
fi

echo "==> Building tag: ${TAG}"
echo "==> Targets: ${TARGETS[*]}"
echo ""

FAILED=()

for svc in "${TARGETS[@]}"; do
  if [[ -z "${IMAGE_MAP[$svc]+_}" ]]; then
    echo "⚠️  Unknown service '${svc}', skipping."
    continue
  fi

  IMAGE="${REGISTRY}/${IMAGE_MAP[$svc]}:${TAG}"
  CONTEXT="${SERVICES_DIR}/${svc}"

  if [[ ! -f "${CONTEXT}/Dockerfile" ]]; then
    echo "⚠️  No Dockerfile found at ${CONTEXT}/Dockerfile, skipping ${svc}."
    continue
  fi

  echo "──────────────────────────────────────────"
  echo "🔨  ${svc}  →  ${IMAGE}"
  echo "──────────────────────────────────────────"

  if minikube image build -t "${IMAGE}" "${CONTEXT}"; then
    echo "✅  ${svc} built successfully"
  else
    echo "❌  ${svc} FAILED"
    FAILED+=("$svc")
  fi
  echo ""
done

echo "=========================================="
if [[ ${#FAILED[@]} -eq 0 ]]; then
  echo "✅  All builds succeeded."
else
  echo "❌  Failed services: ${FAILED[*]}"
  exit 1
fi
