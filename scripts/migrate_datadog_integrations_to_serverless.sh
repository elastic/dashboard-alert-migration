#!/usr/bin/env bash
# Optional Lab 2 extension: migrate real Datadog integrations-core dashboards (BSD-licensed)
# and start synthetic OTLP sample metrics so charts can populate.
# Uses datadog-migrate with default field profile (otel: nginx.net.* → nginx_net_*).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
# shellcheck disable=SC1090
[[ -f /root/.bashrc ]] && source /root/.bashrc

SRC="${ROOT}/assets/datadog/integrations-core"
if [ ! -d "${SRC}" ] || [ -z "$(find "${SRC}" -maxdepth 1 -name '*.json' -print -quit 2>/dev/null)" ]; then
  echo "==> No integration dashboards under ${SRC}; fetching from GitHub..."
  bash "${ROOT}/scripts/update_datadog_integrations_dashboards.sh"
fi

echo "==> Starting sample OTLP metrics for integrations-core boards..."
bash "${ROOT}/scripts/start_workshop_integrations_otel.sh" \
  || echo "    WARN: integrations sample emitter failed — migrate will still upload; charts may be empty." >&2

MIG_VENV="${MIG_TO_KBN_VENV:-/opt/mig-to-kbn-venv}"
DD_MIGRATE="${MIG_VENV}/bin/datadog-migrate"
bash "${ROOT}/scripts/ensure_mig_to_kbn_install.sh" datadog-migrate

if [ -z "${KIBANA_URL:-}" ] || [ -z "${ES_URL:-}" ]; then
  echo "ERROR: source ~/.bashrc (KIBANA_URL, ES_URL required)." >&2
  exit 1
fi
KIBANA_KEY="${KIBANA_API_KEY:-${ES_API_KEY:-}}"
if [ -z "${KIBANA_KEY}" ]; then
  echo "ERROR: Need KIBANA_API_KEY or ES_API_KEY." >&2
  exit 1
fi

STAGE="${ROOT}/build/mig-datadog-integrations-stage"
OUT="${ROOT}/build/mig-datadog-integrations"
rm -rf "${STAGE}"
mkdir -p "${STAGE}"
cp "${SRC}/"*.json "${STAGE}/"

echo "==> datadog-migrate: integrations-core dashboards (${STAGE}) -> ${OUT}"
rm -rf "${OUT}"
mkdir -p "${OUT}"

MIG_ARGS=(
  --input-dir "${STAGE}"
  --output-dir "${OUT}"
  --field-profile otel
  --kibana-url "${KIBANA_URL}"
  --kibana-api-key "${KIBANA_KEY}"
  --upload
  --ensure-data-views
)

if [ "${WORKSHOP_MIG_ES_VALIDATE:-0}" = "1" ] && [ -n "${ES_API_KEY:-}" ]; then
  MIG_ARGS+=(--es-url "${ES_URL}" --es-api-key "${ES_API_KEY}" --validate)
fi

"${DD_MIGRATE}" "${MIG_ARGS[@]}"

echo "OK: integration dashboards migrated to ${OUT}/yaml/ (see migration_report.json)."
echo "    Sample data: tools/otel_integrations_sample.py → Alloy → metrics-* (nginx_*, postgresql_*, …)."
echo "    Re-start sample only: bash scripts/start_workshop_integrations_otel.sh"
