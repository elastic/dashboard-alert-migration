#!/usr/bin/env bash
# Re-apply workshop patches to vendored mig-to-kbn (pending upstream merge).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MIG="${MIG_TO_KBN_DIR:-${ROOT}/mig-to-kbn}"
PATCH_DIR="${ROOT}/scripts/patches"

if [ ! -f "${MIG}/pyproject.toml" ]; then
  echo "WARN: ${MIG}/pyproject.toml missing; skipping workshop patches." >&2
  exit 0
fi

applied=0
for patch in "${PATCH_DIR}"/*.patch; do
  [ -f "$patch" ] || continue
  echo "==> Applying workshop patch: $(basename "$patch")"
  if patch -p1 -d "$MIG" -N --forward <"$patch"; then
    applied=$((applied + 1))
  else
    ec=$?
    if [ "$ec" -eq 1 ]; then
      echo "    (already applied or hunk failed — check ${patch})" >&2
    else
      exit "$ec"
    fi
  fi
done

if [ "$applied" -gt 0 ]; then
  echo "OK: applied ${applied} workshop patch(es) under ${MIG}"
fi
