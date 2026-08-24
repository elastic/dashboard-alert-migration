#!/usr/bin/env bash
# Refresh /root/workshop from GitHub (Instruqt clones often track an old main).
# Usage:
#   cd /root/workshop && source ~/.bashrc && ./scripts/sync_workshop_from_git.sh
#   WORKSHOP_GIT_REF=main ./scripts/sync_workshop_from_git.sh   # after PR merge
set -euo pipefail
ROOT="$(readlink -f /root/workshop 2>/dev/null || echo /root/workshop)"
cd "$ROOT"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "ERROR: $ROOT is not a git repo. Re-provision the sandbox or push the latest track." >&2
  exit 1
fi

# Prefer the Elastic org remote (poulsbopete redirects, but branch availability can lag).
_desired_url="${WORKSHOP_GIT_URL:-https://github.com/elastic/dashboard-alert-migration.git}"
_cur="$(git remote get-url origin 2>/dev/null || true)"
if [[ -n "$_cur" && "$_cur" != *"elastic/dashboard-alert-migration"* ]]; then
  echo "Updating origin remote → ${_desired_url}"
  git remote set-url origin "$_desired_url"
fi

# Feature branch until metrics-adoption lands on main; override with WORKSHOP_GIT_REF.
REF="${WORKSHOP_GIT_REF:-metrics-adoption-workshop}"
echo "Updating from origin ($REF)..."
if ! git fetch --depth 1 origin "$REF"; then
  echo "WARN: fetch $REF failed; trying main..."
  REF=main
  git fetch --depth 1 origin "$REF"
fi

if ! git rev-parse --verify "FETCH_HEAD" >/dev/null 2>&1 && ! git rev-parse --verify "origin/$REF" >/dev/null 2>&1; then
  echo "ERROR: could not fetch origin/$REF" >&2
  exit 1
fi

git reset --hard "origin/$REF" 2>/dev/null || git reset --hard FETCH_HEAD

# If mig-to-kbn is a submodule, pull its commit after the parent reset (shallow-friendly).
if [ -f .gitmodules ] && git config -f .gitmodules --get submodule.mig-to-kbn.path >/dev/null 2>&1; then
  echo "Updating submodule mig-to-kbn..."
  git submodule update --init --recursive --depth 1 2>/dev/null || git submodule update --init --recursive
fi

chmod +x scripts/*.sh scripts/*.py 2>/dev/null || true
echo "OK: $(git log -1 --oneline)"
if [[ ! -f scripts/deploy_workshop_workflows.py ]]; then
  echo "WARN: scripts/deploy_workshop_workflows.py still missing — wrong branch or incomplete tree." >&2
  echo "      Try: WORKSHOP_GIT_REF=metrics-adoption-workshop $0" >&2
else
  echo "Next (Agent Builder / Workflows):"
  echo "  python3 scripts/deploy_workshop_workflows.py"
  echo "  python3 scripts/ensure_ai_recommendation_panels.py --seed-now"
fi
echo "OTLP: ./scripts/check_workshop_otel_pipeline.sh  OR  ./scripts/start_workshop_otel.sh"
if [ -d mig-to-kbn/.git ] && [ ! -f .gitmodules ]; then
  echo "      Standalone mig-to-kbn clone: ./scripts/update_mig_to_kbn.sh && sudo bash scripts/install_workshop_mig_to_kbn.sh"
fi
