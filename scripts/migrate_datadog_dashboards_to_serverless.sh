#!/usr/bin/env bash
# Lab 2 (Instruqt): OTLP (optional) → datadog-migrate → Kibana; monitors → legacy publisher.
# Default Kibana-only upload (no --es-url / --validate). WORKSHOP_MIG_ES_VALIDATE=1 enables --es-url + --validate.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
# shellcheck disable=SC1090
[[ -f /root/.bashrc ]] && source /root/.bashrc

MIG_VENV="${MIG_TO_KBN_VENV:-/opt/mig-to-kbn-venv}"
DD_MIGRATE="${MIG_VENV}/bin/datadog-migrate"
bash "${ROOT}/scripts/ensure_mig_to_kbn_install.sh" datadog-migrate

if [ -x /opt/workshop-venv/bin/python3 ]; then
  PY="${WORKSHOP_PYTHON:-/opt/workshop-venv/bin/python3}"
else
  PY="${WORKSHOP_PYTHON:-python3}"
fi

if [ -z "${KIBANA_URL:-}" ]; then
  echo "ERROR: KIBANA_URL is not set. Run: source ~/.bashrc" >&2
  exit 1
fi
if [ -z "${ES_URL:-}" ]; then
  echo "ERROR: ES_URL is not set. Run: source ~/.bashrc" >&2
  exit 1
fi
if [ -z "${ES_API_KEY:-}" ] && { [ -z "${ES_USERNAME:-}" ] || [ -z "${ES_PASSWORD:-}" ]; }; then
  echo "ERROR: Set ES_API_KEY (or ES_USERNAME + ES_PASSWORD). Run: source ~/.bashrc" >&2
  exit 1
fi

KIBANA_KEY="${KIBANA_API_KEY:-${ES_API_KEY:-}}"
if [ -z "${KIBANA_KEY}" ]; then
  echo "ERROR: Need KIBANA_API_KEY or ES_API_KEY for Kibana upload." >&2
  exit 1
fi

STAGE="${ROOT}/build/mig-datadog-stage"
OUT="${ROOT}/build/mig-datadog"
rm -rf "${STAGE}"
mkdir -p "${STAGE}/monitors"
cp "${ROOT}/assets/datadog/dashboards/"*.json "${STAGE}/"
for f in "${ROOT}/assets/datadog/monitor-"*.json; do
  [ -f "$f" ] || continue
  cp "$f" "${STAGE}/monitors/"
done

mkdir -p "${ROOT}/build/elastic-alerts"

WAIT_OTLP=0
if [ "${WORKSHOP_SKIP_OTEL:-0}" = "1" ]; then
  echo "==> [1/5] Skipping OTLP (WORKSHOP_SKIP_OTEL=1)."
elif [ "${WORKSHOP_FORCE_OTEL_RESTART:-0}" != "1" ] \
  && curl -sf --max-time 3 "http://127.0.0.1:12345/metrics" >/dev/null 2>&1 \
  && pgrep -f '[o]tel_workshop_fleet.py' >/dev/null 2>&1; then
  echo "==> [1/5] OTLP already running — skipping restart."
  WAIT_OTLP=45
else
  echo "==> [1/5] OpenTelemetry (Alloy → mOTLP) so Lens panels have data..."
  if ! "${ROOT}/scripts/start_workshop_otel.sh"; then
    echo "    WARN: start_workshop_otel.sh failed — publishes may still run; charts can be empty." >&2
  else
    WAIT_OTLP=45
  fi
fi
if [ "$WAIT_OTLP" -gt 0 ]; then
  echo "    Waiting ${WAIT_OTLP}s for OTLP documents..."
  sleep "$WAIT_OTLP"
fi

ES_ES_ARGS=(--es-url "" --es-api-key "")
if [ "${WORKSHOP_MIG_ES_VALIDATE:-0}" = "1" ]; then
  ES_ES_ARGS=(--es-url "${ES_URL}" --es-api-key "${ES_API_KEY}" --validate)
  echo "==> [2/5] datadog-migrate (… + live ES|QL validation: WORKSHOP_MIG_ES_VALIDATE=1) + monitor IR extract..."
else
  echo "==> [2/5] datadog-migrate (Kibana-only upload; ES_URL in env ignored for validation — WORKSHOP_MIG_ES_VALIDATE=1 to enable) + monitor IR extract..."
fi
"${DD_MIGRATE}" \
  --source files \
  --input-dir "${STAGE}" \
  --output-dir "${OUT}" \
  --field-profile otel \
  --logs-index "logs-*" \
  "${ES_ES_ARGS[@]}" \
  --upload \
  --kibana-url "${KIBANA_URL}" \
  --kibana-api-key "${KIBANA_KEY}" \
  --ensure-data-views \
  --fetch-monitors

if [ -d "${OUT}/dashboards/yaml" ]; then
  n_yaml="$(find "${OUT}/dashboards/yaml" -maxdepth 1 -name '*.yaml' 2>/dev/null | wc -l | tr -d ' ')"
  echo "    YAML dashboards: ${n_yaml} (under ${OUT}/dashboards/yaml/)"
else
  n_yaml="$(find "${OUT}/yaml" -maxdepth 1 -name '*.yaml' 2>/dev/null | wc -l | tr -d ' ')" || n_yaml=0
  echo "    YAML dashboards: ${n_yaml} (under ${OUT}/yaml/)"
fi

echo "==> [3/6] Converting 4 Datadog monitors → Kibana rule drafts (workshop publisher)..."
for f in "${ROOT}/assets/datadog/monitor-"*.json; do
  [ -f "$f" ] || continue
  base="$(basename "$f" .json)"
  "${PY}" "${ROOT}/tools/datadog_to_elastic_alert.py" "$f" -o "${ROOT}/build/elastic-alerts/${base}-elastic.json"
done
a="$(find "${ROOT}/build/elastic-alerts" -maxdepth 1 -name 'monitor-*-elastic.json' | wc -l | tr -d ' ')"
echo "    Alert draft files: ${a}"

echo "==> [4/6] Datadog dashboards already uploaded by datadog-migrate (skip legacy draft publisher)."

echo "==> [5/6] Publishing Datadog-derived rules to Kibana (disabled by default; no connectors)..."
"${PY}" "${ROOT}/tools/publish_datadog_alert_drafts_kibana.py" --alerts-dir "${ROOT}/build/elastic-alerts"

echo "==> [6/6] Agent Builder metrics-adoption notes (markdown panels + workflow)..."
if [ "${WORKSHOP_SKIP_AI_NOTES:-0}" = "1" ]; then
  echo "    Skipping (WORKSHOP_SKIP_AI_NOTES=1)."
else
  "${PY}" "${ROOT}/scripts/ensure_ai_recommendation_panels.py" --platform datadog --seed-now \
    || echo "    WARN: ensure_ai_recommendation_panels.py failed (dashboards still uploaded)." >&2
  "${PY}" "${ROOT}/scripts/deploy_workshop_workflows.py" metrics-adoption-recommendations.yaml \
    || echo "    WARN: deploy_workshop_workflows.py failed (AI notes panels may still work via --seed-now)." >&2
fi

echo "==> Done."
echo "    Dashboards: Elastic Serverless → search for migrated Datadog titles + **Metrics adoption — AI notes**"
echo "    Monitor IR summary: ${OUT}/alerts/monitor_migration_results.json (or monitor_migration_results.json) + published rules from build/elastic-alerts/"
echo "    Rules: Observability → Rules — workshop imports are created **disabled**; enable/edit queries in the UI."
echo "    AI notes: refresh **Metrics adoption — AI notes** or **Service overview**; Workflows schedule every 10m."
