#!/usr/bin/env bash
# Start (or restart) synthetic OTLP metrics for optional Datadog integrations-core boards.
# Requires Alloy already listening on WORKSHOP_ALLOY_OTLP_HTTP (see start_workshop_otel.sh).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
# shellcheck disable=SC1090
[[ -f /root/.bashrc ]] && source /root/.bashrc

ALLOY_HTTP="${WORKSHOP_ALLOY_OTLP_HTTP:-http://127.0.0.1:4318}"
export WORKSHOP_ALLOY_OTLP_HTTP="${ALLOY_HTTP}"

PYTHON="${WORKSHOP_PYTHON:-}"
if [ -z "$PYTHON" ]; then
  if [ -x /opt/workshop-venv/bin/python3 ]; then
    PYTHON=/opt/workshop-venv/bin/python3
  elif [ -x /opt/mig-to-kbn-venv/bin/python ] \
    && /opt/mig-to-kbn-venv/bin/python -c "import opentelemetry" 2>/dev/null; then
    PYTHON=/opt/mig-to-kbn-venv/bin/python
  else
    PYTHON=python3
  fi
fi
export WORKSHOP_PYTHON="$PYTHON"

# Ensure Alloy is up for OTLP
if ! curl -sf -o /dev/null --connect-timeout 2 "${ALLOY_HTTP%/}/v1/metrics" 2>/dev/null \
  && ! curl -sf -o /dev/null --connect-timeout 2 "http://127.0.0.1:4318/v1/metrics" 2>/dev/null; then
  echo "==> Alloy OTLP not reachable at ${ALLOY_HTTP}; starting workshop OTLP pipeline..."
  bash "${ROOT}/scripts/start_workshop_otel.sh" || true
fi

pkill -f "otel_integrations_sample.py" 2>/dev/null || true
sleep 1

LOG="${WORKSHOP_INTEGRATIONS_SAMPLE_LOG:-/tmp/workshop-integrations-sample.log}"
nohup "$PYTHON" "${ROOT}/tools/otel_integrations_sample.py" >>"${LOG}" 2>&1 &
echo $! >/tmp/workshop-integrations-sample.pid
echo "==> integrations sample emitter started (pid $(cat /tmp/workshop-integrations-sample.pid))"
echo "    log: ${LOG}"
echo "    wait ~30–60s for metrics-* to show nginx_* / postgresql_* / rabbitmq_* …"
