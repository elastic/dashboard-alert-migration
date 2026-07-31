#!/usr/bin/env python3
"""Generate sample Grafana dashboard JSON files (Prometheus datasource) for the workshop.

Each dashboard is a small "mini-operations" view: a stat KPI, two time series (aggregate +
dimensional breakdown), and a table snapshot. Agent Builder AI notes are attached post-migrate
(``scripts/ensure_ai_recommendation_panels.py``), not as static text panels. PromQL avoids
``topk`` / ``bottomk`` so mig-to-kbn native PROMQL translation can migrate every panel (those
aggregates are not supported by the ES PROMQL bridge — see mig-to-kbn panels.py).

**PromQL label keys** must match **Elasticsearch column names** for native ``PROMQL`` on
Serverless. The OTLP fleet sets OpenTelemetry semantic attributes (``http.request.method``, …),
which appear as dotted fields (not ``http.request.method`` / ``http.route``). Use
``service.name`` for per-service breakdown (same cardinality as workshop ``entity_id``).

**Multi-label ``sum by (a, b, ...)``** is avoided for non-histogram panels: Kibana Lens with
native **PROMQL** can error with ``unresolved_exception`` / ``?label`` when more than one
breakdown column is expected (Elasticsearch 9.x). Use one grouping label per chart; compare
dimensions across panels instead.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "grafana"


def what_why_md(*, what: str, why: str, note: str = "") -> str:
    """Legacy helper kept so DASH_SPECS tuples stay readable; content is not emitted into JSON."""
    parts = [what.strip(), why.strip()]
    if note.strip():
        parts.append(note.strip())
    return "\n".join(parts)


# (filename, title, _unused_intro, stat_title, stat_expr, ts1_title, ts1_expr, ts2_title, ts2_expr, table_title, table_expr)
# Intro strings document intent for authors; AI analysis is attached in Kibana after migrate.
DASH_SPECS: list[tuple[str, str, str, str, str, str, str, str, str, str, str]] = [
    (
        "01-overview.json",
        "Traffic overview",
        what_why_md(
            what="End-to-end HTTP request volume from the workshop OTLP emitters: a headline rate KPI, method and status splits, and an instant status snapshot.",
            why="Gives existing Elastic customers a first **metrics** board that proves live `metrics-*` ingest and golden-signal traffic before diving into latency or errors.",
        ),
        "Requests/sec (total)",
        "sum(rate(http_requests_total[5m]))",
        "Total request rate",
        "sum(rate(http_requests_total[5m]))",
        "By HTTP method",
        "sum by (http.request.method) (rate(http_requests_total[5m]))",
        "By status code (instant)",
        "sum by (http.response.status_code) (rate(http_requests_total[5m]))",
    ),
    (
        "02-request-rate.json",
        "Request rate by service",
        what_why_md(
            what="Per-service HTTP throughput plus **single-label** splits by route and status (multi-label `sum by` is avoided so native PromQL migrates cleanly).",
            why="Service-scoped rate is the usual first metrics adoption check: confirm `service.name` cardinality and that teams can find *their* traffic on Elastic.",
        ),
        "Requests/sec (all)",
        "sum(rate(http_requests_total[5m]))",
        "Rate by service",
        "sum by (service.name) (rate(http_requests_total[5m]))",
        "Rate by route",
        "sum by (http.route) (rate(http_requests_total[5m]))",
        "By status code (instant)",
        "sum by (http.response.status_code) (rate(http_requests_total[5m]))",
    ),
    (
        "03-latency-p95.json",
        "Latency p95",
        what_why_md(
            what="Mean request duration by `service.name` (histogram sum/count) and observation rate for contrast. Serverless ES|QL has no `histogram_quantile`, so this is the stable p95-style proxy.",
            why="Latency is a core SLO input; adopting metrics on Elastic means trusting duration charts against the same OTLP series apps already emit.",
            note="Title keeps a familiar p95 framing; values are mean(sum/count), not true histogram quantiles.",
        ),
        "Duration samples/sec",
        "sum(rate(http_request_duration_seconds_count[5m]))",
        "Mean latency by service",
        "(sum by (service.name) (rate(http_request_duration_seconds_sum[5m]))) / (sum by (service.name) (rate(http_request_duration_seconds_count[5m])))",
        "Observation rate by service",
        "sum by (service.name) (rate(http_request_duration_seconds_count[5m]))",
        "Mean latency (sum/count)",
        "(sum by (service.name) (rate(http_request_duration_seconds_sum[5m]))) / (sum by (service.name) (rate(http_request_duration_seconds_count[5m])))",
    ),
    (
        "04-error-rate.json",
        "Error rate",
        what_why_md(
            what="5xx share of HTTP traffic and raw server-error rate, with an instant status breakdown.",
            why="Error rate is the fastest way to validate that migrated PromQL error panels land on live Elastic metrics and support alert drafts.",
        ),
        "5xx share",
        "sum(rate(http_requests_total{http.response.status_code=~\"5..\"}[5m])) / sum(rate(http_requests_total[5m]))",
        "Error ratio",
        "sum(rate(http_requests_total{http.response.status_code=~\"5..\"}[5m])) / sum(rate(http_requests_total[5m]))",
        "5xx requests/sec",
        "sum(rate(http_requests_total{http.response.status_code=~\"5..\"}[5m]))",
        "Errors by status (instant)",
        "sum by (http.response.status_code) (rate(http_requests_total[5m]))",
    ),
    (
        "05-operation-errors.json",
        "Operation errors by reason",
        what_why_md(
            what="Business/application `operation_errors_total` by `reason` and by `service.name`.",
            why="Shows metrics beyond HTTP counters — domain error reasons teams already track in PromQL can adopt onto Elastic without rebuilding taxonomy.",
        ),
        "Operation errors/sec",
        "sum(rate(operation_errors_total[5m]))",
        "By reason",
        "sum by (reason) (rate(operation_errors_total[5m]))",
        "Errors by service",
        "sum by (service.name) (rate(operation_errors_total[5m]))",
        "Reason snapshot",
        "sum by (reason) (rate(operation_errors_total[5m]))",
    ),
    (
        "06-top-entities.json",
        "Top services by traffic",
        what_why_md(
            what="Service ranking via rate by `service.name` (and method). Grafana `topk` is omitted so migration stays on the supported PromQL subset.",
            why="Platform teams adopt metrics when they can answer “who is hottest right now?” on Elastic; Lens Top Values / `LIMIT` cover strict top-N after import.",
        ),
        "Total requests/sec",
        "sum(rate(http_requests_total[5m]))",
        "Rate by service",
        "sum by (service.name) (rate(http_requests_total[5m]))",
        "Rate by HTTP method",
        "sum by (http.request.method) (rate(http_requests_total[5m]))",
        "Service snapshot (instant)",
        "sum by (service.name) (rate(http_requests_total[5m]))",
    ),
    (
        "07-post-path.json",
        "POST /api/v1/orders volume",
        what_why_md(
            what="Hot route focus: `POST /api/v1/orders` (fleet-emitted) versus all POST traffic, plus POST-by-route snapshot.",
            why="Route-scoped metrics prove that filters (`http.route`, method) survive migration — critical for app-owner dashboards during metrics adoption.",
        ),
        "POST /api/v1/orders rps",
        "sum(rate(http_requests_total{http.route=\"/api/v1/orders\",http.request.method=\"POST\"}[5m]))",
        "Orders POST rate",
        "sum(rate(http_requests_total{http.route=\"/api/v1/orders\",http.request.method=\"POST\"}[5m]))",
        "All POST traffic",
        "sum(rate(http_requests_total{http.request.method=\"POST\"}[5m]))",
        "POST by route (instant)",
        "sum by (http.route) (rate(http_requests_total{http.request.method=\"POST\"}[5m]))",
    ),
    (
        "08-latency-by-path.json",
        "Latency by path",
        what_why_md(
            what="Mean request duration per `http.route` from `http_request_duration_seconds_*` sum/count, plus observation rate.",
            why="Path latency is how SRE teams adopt endpoint SLOs on Elastic when true histogram quantiles are not available in ES|QL.",
            note="No `histogram_quantile` on Serverless ES|QL — mean(sum/count) is the intentional proxy.",
        ),
        "Request count/sec",
        "sum(rate(http_request_duration_seconds_count[5m]))",
        "Mean latency by path",
        "(sum by (http.route) (rate(http_request_duration_seconds_sum[5m]))) / (sum by (http.route) (rate(http_request_duration_seconds_count[5m])))",
        "Observation rate by path",
        "sum by (http.route) (rate(http_request_duration_seconds_count[5m]))",
        "Mean latency (instant)",
        "(sum by (http.route) (rate(http_request_duration_seconds_sum[5m]))) / (sum by (http.route) (rate(http_request_duration_seconds_count[5m])))",
    ),
    (
        "09-status-codes.json",
        "Status codes",
        what_why_md(
            what="HTTP status mix: rates by status code and by method, with an instant status snapshot.",
            why="Status breakdowns are the bridge from traffic metrics to error budgets — a standard board when expanding metrics coverage on Elastic.",
        ),
        "All responses/sec",
        "sum(rate(http_requests_total[5m]))",
        "By status",
        "sum by (http.response.status_code) (rate(http_requests_total[5m]))",
        "By method",
        "sum by (http.request.method) (rate(http_requests_total[5m]))",
        "Status snapshot (instant)",
        "sum by (http.response.status_code) (rate(http_requests_total[5m]))",
    ),
    (
        "10-slo-burn.json",
        "SLO-style availability",
        what_why_md(
            what="1h availability-style ratio (1 − 5xx/total) plus component 5xx and total traffic series.",
            why="Shows how metrics adoption supports SLO conversations on Elastic using the same PromQL intent teams already document for burn rates.",
        ),
        "Availability (1h)",
        "1 - (sum(rate(http_requests_total{http.response.status_code=~\"5..\"}[1h])) / sum(rate(http_requests_total[1h])))",
        "Availability",
        "1 - (sum(rate(http_requests_total{http.response.status_code=~\"5..\"}[1h])) / sum(rate(http_requests_total[1h])))",
        "5xx volume (1h rate)",
        "sum(rate(http_requests_total{http.response.status_code=~\"5..\"}[1h]))",
        "Total traffic (1h rate)",
        "sum(rate(http_requests_total[1h]))",
    ),
    (
        "11-entity-errors.json",
        "Errors by service",
        what_why_md(
            what="Operation errors and HTTP 5xx side-by-side by `service.name`.",
            why="Correlating app and HTTP errors on one metrics board is a typical adoption win versus keeping those signals in separate tools.",
        ),
        "Op errors/sec",
        "sum(rate(operation_errors_total[5m]))",
        "Op errors by service",
        "sum by (service.name) (rate(operation_errors_total[5m]))",
        "HTTP 5xx by service",
        "sum by (service.name) (rate(http_requests_total{http.response.status_code=~\"5..\"}[5m]))",
        "Service error snapshot",
        "sum by (service.name) (rate(operation_errors_total[5m]))",
    ),
    (
        "12-heatmap-style.json",
        "Request mix",
        what_why_md(
            what="Service volume plus method and status as **separate** single-label charts (multi-label PromQL avoided for Lens).",
            why="Teaches the metrics-adoption pattern of comparable breakdowns across panels when one chart cannot carry every dimension.",
        ),
        "Requests/sec",
        "sum(rate(http_requests_total[5m]))",
        "Requests by service",
        "sum by (service.name) (rate(http_requests_total[5m]))",
        "By method",
        "sum by (http.request.method) (rate(http_requests_total[5m]))",
        "By status",
        "sum by (http.response.status_code) (rate(http_requests_total[5m]))",
    ),
    (
        "13-cpu-saturation.json",
        "Throughput by host",
        what_why_md(
            what="HTTP request rate by `host.name` and by service — a saturation/load proxy.",
            why="Infra-shaped views from PromQL still matter for metrics adoption; this board maps host dimensions onto Elastic without requiring process CPU counters.",
            note="Workshop OTLP has no `process_cpu_seconds_total`; host throughput is the intentional stand-in.",
        ),
        "Requests/sec (total)",
        "sum(rate(http_requests_total[5m]))",
        "Request rate by host",
        "sum by (host.name) (rate(http_requests_total[5m]))",
        "Request rate by service",
        "sum by (service.name) (rate(http_requests_total[5m]))",
        "By host (instant)",
        "sum by (host.name) (rate(http_requests_total[5m]))",
    ),
    (
        "14-memory-working-set.json",
        "Workload mix",
        what_why_md(
            what="HTTP traffic plus operation errors (volume and by service/reason) as a workload mix view.",
            why="When memory metrics are not yet on Elastic, this board still teaches mixed-signal dashboards while teams expand infra metric coverage.",
            note="No `process_resident_memory_bytes` in workshop OTLP.",
        ),
        "Requests/sec",
        "sum(rate(http_requests_total[5m]))",
        "Operation errors/sec",
        "sum(rate(operation_errors_total[5m]))",
        "Errors by service",
        "sum by (service.name) (rate(operation_errors_total[5m]))",
        "Errors by reason (instant)",
        "sum by (reason) (rate(operation_errors_total[5m]))",
    ),
    (
        "15-gc-pause-rate.json",
        "GC pause indicator",
        what_why_md(
            what="Runtime-pressure story using fleet **counter** metrics (`http_requests_total`, `operation_errors_total`) by host and service.",
            why="Illustrates honest metrics adoption: prefer queries that work on Elastic field types over importing PromQL that cannot run (e.g. RATE on gauge GC histograms).",
            note=(
                "`go_gc_duration_seconds_*` often lands as double gauges; ES|QL RATE needs counters. "
                "This board keeps the GC/runtime narrative with counter-backed proxies."
            ),
        ),
        "HTTP requests/sec",
        "sum(rate(http_requests_total[5m]))",
        "Request burst by host",
        "sum by (host.name) (rate(http_requests_total[5m]))",
        "Operation errors/sec",
        "sum(rate(operation_errors_total[5m]))",
        "Requests by service (instant)",
        "sum by (service.name) (rate(http_requests_total[5m]))",
    ),
    (
        "16-dependency-latency.json",
        "Downstream latency p90",
        what_why_md(
            what="Server mean latency by `http.route` (sum/count) as a downstream/dependency stand-in.",
            why="Dependency latency boards are high-value for adoption; this shows the same proxy pattern as path latency when client histograms are not in the fleet.",
            note="No outbound `http_client_duration_*` in workshop OTLP; no `histogram_quantile` on Serverless ES|QL.",
        ),
        "Request count/sec",
        "sum(rate(http_request_duration_seconds_count[5m]))",
        "Mean latency by route",
        "(sum by (http.route) (rate(http_request_duration_seconds_sum[5m]))) / (sum by (http.route) (rate(http_request_duration_seconds_count[5m])))",
        "Observation rate by route",
        "sum by (http.route) (rate(http_request_duration_seconds_count[5m]))",
        "Mean latency (instant)",
        "(sum by (http.route) (rate(http_request_duration_seconds_sum[5m]))) / (sum by (http.route) (rate(http_request_duration_seconds_count[5m])))",
    ),
    (
        "17-queue-depth.json",
        "Queue depth stand-in",
        what_why_md(
            what="Request **rate** by route and service as a queue/backlog stand-in.",
            why="Many shops adopt metrics with backlog proxies before true queue gauges exist on Elastic — this board models that incremental path.",
            note="No `workqueue_depth` in workshop OTLP.",
        ),
        "Total requests/sec",
        "sum(rate(http_requests_total[5m]))",
        "Rate by route",
        "sum by (http.route) (rate(http_requests_total[5m]))",
        "Rate by service",
        "sum by (service.name) (rate(http_requests_total[5m]))",
        "Route snapshot (instant)",
        "sum by (http.route) (rate(http_requests_total[5m]))",
    ),
    (
        "18-cache-hit-ratio.json",
        "Success share (2xx)",
        what_why_md(
            what="2xx share of traffic and absolute 2xx vs non-2xx rates.",
            why="Success-ratio boards are a lightweight availability metric teams can adopt early while richer cache/hit metrics are still being instrumented.",
            note="No `cache_*` counters in workshop OTLP; 2xx share is the intentional proxy.",
        ),
        "2xx share",
        "sum(rate(http_requests_total{http.response.status_code=~\"2..\"}[5m])) / sum(rate(http_requests_total[5m]))",
        "2xx share",
        "sum(rate(http_requests_total{http.response.status_code=~\"2..\"}[5m])) / sum(rate(http_requests_total[5m]))",
        "2xx requests/sec",
        "sum(rate(http_requests_total{http.response.status_code=~\"2..\"}[5m]))",
        "Non-2xx requests/sec",
        "sum(rate(http_requests_total{http.response.status_code!~\"2..\"}[5m]))",
    ),
    (
        "19-pod-restarts.json",
        "Error churn",
        what_why_md(
            what="Operation error rates by reason and service as a churn/restart stand-in.",
            why="Demonstrates adopting stability metrics on Elastic even when Kubernetes restart series are not yet ingested.",
            note="No Kubernetes metrics in workshop OTLP.",
        ),
        "Operation errors/sec",
        "sum(rate(operation_errors_total[5m]))",
        "Errors by reason",
        "sum by (reason) (rate(operation_errors_total[5m]))",
        "Errors by service",
        "sum by (service.name) (rate(operation_errors_total[5m]))",
        "Reason snapshot (instant)",
        "sum by (reason) (rate(operation_errors_total[5m]))",
    ),
    (
        "20-endpoint-slo.json",
        "Endpoint availability",
        what_why_md(
            what="Non-5xx success fraction over 30m with successful vs total rps.",
            why="A compact endpoint SLO-style metrics board for stakeholders reviewing Elastic as the system of record for availability.",
        ),
        "Success ratio (30m)",
        "sum(rate(http_requests_total{http.response.status_code!~\"5..\"}[30m])) / sum(rate(http_requests_total[30m]))",
        "Success ratio",
        "sum(rate(http_requests_total{http.response.status_code!~\"5..\"}[30m])) / sum(rate(http_requests_total[30m]))",
        "Successful rps",
        "sum(rate(http_requests_total{http.response.status_code!~\"5..\"}[30m]))",
        "Total rps",
        "sum(rate(http_requests_total[30m]))",
    ),
]


def _ds() -> dict:
    return {"type": "prometheus", "uid": "${datasource}"}


def _templating() -> dict:
    return {
        "list": [
            {
                "name": "datasource",
                "type": "datasource",
                "query": "prometheus",
                "current": {"selected": True, "text": "Prometheus", "value": "Prometheus"},
            }
        ]
    }


def panel_stat(title: str, expr: str, x: int, y: int, w: int, h: int) -> dict:
    return {
        "type": "stat",
        "title": title,
        "gridPos": {"h": h, "w": w, "x": x, "y": y},
        "datasource": _ds(),
        "targets": [{"expr": expr, "legendFormat": "", "refId": "A"}],
        "fieldConfig": {"defaults": {"unit": "short", "decimals": 3}, "overrides": []},
        "options": {
            "reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False},
            "orientation": "auto",
            "textMode": "auto",
            "colorMode": "value",
            "graphMode": "area",
        },
    }


def panel_timeseries(title: str, expr: str, x: int, y: int, w: int, h: int, legend: str = "") -> dict:
    return {
        "type": "timeseries",
        "title": title,
        "gridPos": {"h": h, "w": w, "x": x, "y": y},
        "datasource": _ds(),
        "targets": [{"expr": expr, "legendFormat": legend, "refId": "A"}],
        "fieldConfig": {"defaults": {"unit": "short"}, "overrides": []},
        "options": {"legend": {"displayMode": "list", "placement": "bottom"}},
    }


def panel_table(title: str, expr: str, x: int, y: int, w: int, h: int) -> dict:
    return {
        "type": "table",
        "title": title,
        "gridPos": {"h": h, "w": w, "x": x, "y": y},
        "datasource": _ds(),
        "targets": [
            {
                "expr": expr,
                "format": "table",
                "instant": True,
                "refId": "A",
            }
        ],
        "fieldConfig": {
            "defaults": {"unit": "short", "custom": {"align": "auto", "displayMode": "auto"}},
            "overrides": [],
        },
        "options": {"showHeader": True},
    }


def build_dashboard(uid: str, spec: tuple[str, str, str, str, str, str, str, str, str, str, str]) -> dict:
    (
        _fn,
        title,
        _intro,
        stat_title,
        stat_expr,
        ts1_title,
        ts1_expr,
        ts2_title,
        ts2_expr,
        tbl_title,
        tbl_expr,
    ) = spec
    y1 = 0
    h_row1 = 8
    y2 = y1 + h_row1
    h_row2 = 8
    panels: list[dict] = [
        panel_stat(stat_title, stat_expr, x=0, y=y1, w=6, h=h_row1),
        panel_timeseries(ts1_title, ts1_expr, x=6, y=y1, w=18, h=h_row1),
        panel_timeseries(ts2_title, ts2_expr, x=0, y=y2, w=12, h=h_row2),
        panel_table(tbl_title, tbl_expr, x=12, y=y2, w=12, h=h_row2),
    ]
    return {
        "uid": uid,
        "title": title,
        "description": f"{title} — metrics adoption workshop board (AI notes attached after migrate).",
        "timezone": "browser",
        "schemaVersion": 39,
        "version": 1,
        "refresh": "10s",
        "time": {"from": "now-1h", "to": "now"},
        "templating": _templating(),
        "panels": panels,
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for spec in DASH_SPECS:
        filename = spec[0]
        uid = filename.replace(".json", "").replace("/", "-")
        path = OUT / filename
        path.write_text(json.dumps(build_dashboard(uid, spec), indent=2) + "\n", encoding="utf-8")
        print("wrote", path)


if __name__ == "__main__":
    main()
