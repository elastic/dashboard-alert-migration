#!/usr/bin/env python3
"""Generate sample Datadog dashboard JSON (many widgets with `q` queries) for the workshop.

Each dashboard has twelve timeseries widgets. Agent Builder AI notes are attached post-migrate
(``scripts/ensure_ai_recommendation_panels.py``), not as static note widgets. mig-to-kbn
``parse_metric_query`` expects ``by {tags}`` *before* ``.as_rate()`` / ``.as_count()``.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "datadog" / "dashboards"

_DD_FN_THEN_BY = re.compile(
    r"^(.+?\{[^}]*\})\.(as_rate|as_count)\(\)\s+by\s+(\{[^}]+\})\s*$"
)


def normalize_datadog_q_for_mig_parser(q: str) -> str:
    """Rewrite ``{*}.as_rate() by {x}`` → ``{*} by {x}.as_rate()`` (same for as_count)."""
    q = q.strip()
    m = _DD_FN_THEN_BY.match(q)
    if m:
        return f"{m.group(1)} by {m.group(3)}.{m.group(2)}()"
    return q


# filename, title, what, why, optional note, list of (widget_title, query)
# what/why/note are author documentation only (not emitted into JSON).
DASHBOARDS: list[tuple[str, str, str, str, str, list[tuple[str, str]]]] = [
    (
        "01-service-overview.json",
        "Service overview",
        "Service-level HTTP duration, hits, errors, Apdex-style score, plus host CPU/memory proxies and a few dependency spans (client, servlet, gRPC, DB).",
        "The first board Datadog shops open for metrics adoption — prove OTel-mapped service metrics land on Elastic and owners can still see golden signals in one place.",
        "Queries use Datadog-style names; workshop migrate uses `--field-profile otel`.",
        [
            ("HTTP duration by service", "avg:trace.http.request.duration{*} by {service}"),
            ("HTTP hits (count)", "avg:trace.http.request.hits{*}"),
            ("HTTP errors", "avg:trace.http.request.errors{*}"),
            ("Duration p95 by resource", "p95:trace.http.request.duration{*} by {resource_name}"),
            ("Hits by resource", "avg:trace.http.request.hits{*} by {resource_name}"),
            ("Apdex-style score", "avg:app.apdex.score{*} by {service}"),
            ("Client request duration", "avg:trace.http.client.duration{*} by {service}"),
            ("Servlet hits", "sum:trace.servlet.request.hits{*}.as_count() by {service}"),
            ("RPC latency", "avg:trace.grpc.client.duration{*} by {service}"),
            ("DB statement duration", "avg:trace.postgres.query.duration{*} by {service}"),
            ("CPU user (host proxy)", "avg:system.cpu.user{*} by {host}"),
            ("Memory usable %", "avg:system.mem.pct_usable{*} by {host}"),
        ],
    ),
    (
        "02-error-budget.json",
        "Error budget view",
        "Error and hit volume, breakdowns by service/resource/status, burn-style hit series, and latency alongside errors.",
        "Error-budget thinking is a common metrics-adoption goal; this board shows how Datadog-shaped monitors and charts can drive the same conversation on Elastic.",
        "",
        [
            ("HTTP errors total", "avg:trace.http.request.errors{*}"),
            ("HTTP hits total", "avg:trace.http.request.hits{*}"),
            ("Errors by service", "avg:trace.http.request.errors{*} by {service}"),
            ("Errors by resource", "avg:trace.http.request.errors{*} by {resource_name}"),
            ("5xx rate proxy", "avg:trace.http.request.errors{*} by {http.status_code}"),
            ("Client errors", "avg:trace.http.client.errors{*} by {service}"),
            ("Failed spans", "avg:trace.spans.finished{*} by {service}"),
            ("Error budget burn (hits)", "avg:trace.http.request.hits{*} by {service}"),
            ("Latency on errors", "avg:trace.http.request.duration{*} by {service}"),
            ("Apdex", "avg:app.apdex.score{*} by {service}"),
            ("Log-style error spike", "avg:trace.http.request.errors{*} by {host}"),
            ("Availability proxy — hits", "avg:trace.http.request.hits{*} by {host}"),
        ],
    ),
    (
        "03-latency-p95.json",
        "Latency p95",
        "Percentile and average HTTP durations by resource/service/host, plus client, DB, and gRPC latency companions.",
        "Latency percentiles are a core Datadog APM habit; migrating them teaches field-profile mapping and review of ES|QL approximations on Elastic.",
        "",
        [
            ("p95 by resource", "p95:trace.http.request.duration{*} by {resource_name}"),
            ("p99 by service", "p99:trace.http.request.duration{*} by {service}"),
            ("p50 duration", "p50:trace.http.request.duration{*} by {service}"),
            ("p75 duration", "p75:trace.http.request.duration{*} by {service}"),
            ("Avg duration", "avg:trace.http.request.duration{*} by {service}"),
            ("Max duration", "max:trace.http.request.duration{*} by {resource_name}"),
            ("Client p95", "p95:trace.http.client.duration{*} by {service}"),
            ("DB query p95", "p95:trace.postgres.query.duration{*} by {service}"),
            ("gRPC p95", "p95:trace.grpc.client.duration{*} by {service}"),
            ("Hits weighted latency", "avg:trace.http.request.duration{*} by {http.method}"),
            ("Duration by host", "avg:trace.http.request.duration{*} by {host}"),
            ("Servlet latency", "avg:trace.servlet.request.duration{*} by {service}"),
        ],
    ),
    (
        "04-apdex-style.json",
        "Apdex-style satisfaction",
        "Apdex score and satisfied/tolerating/frustrated counts alongside HTTP duration, hits, and errors.",
        "Satisfaction metrics are executive-friendly; adopting them on Elastic keeps product conversations on the same observability platform as logs/traces.",
        "",
        [
            ("Apdex by service", "avg:app.apdex.score{*} by {service}"),
            ("Satisfied count", "sum:app.apdex.satisfied{*}.as_count() by {service}"),
            ("Tolerating", "sum:app.apdex.tolerating{*}.as_count() by {service}"),
            ("Frustrated", "sum:app.apdex.frustrated{*}.as_count() by {service}"),
            ("HTTP duration vs apdex", "avg:trace.http.request.duration{*} by {service}"),
            ("Hits for context", "avg:trace.http.request.hits{*} by {service}"),
            ("Errors vs satisfaction", "avg:trace.http.request.errors{*} by {service}"),
            ("Apdex by host", "avg:app.apdex.score{*} by {host}"),
            ("Request rate", "avg:trace.http.request.hits{*} by {service}"),
            ("p95 alongside apdex", "p95:trace.http.request.duration{*} by {service}"),
            ("Client apdex proxy", "avg:trace.http.client.duration{*} by {service}"),
            ("Resource apdex", "avg:app.apdex.score{*} by {resource_name}"),
        ],
    ),
    (
        "05-host-cpu.json",
        "Host CPU",
        "Host CPU user/system/idle/iowait/steal/nice/guest, load averages, context switches, and interrupts.",
        "Infra metrics adoption often starts with CPU; this board validates host-scoped system metrics after OTel field mapping.",
        "",
        [
            ("CPU user %", "avg:system.cpu.user{*} by {host}"),
            ("CPU system %", "avg:system.cpu.system{*} by {host}"),
            ("CPU idle %", "avg:system.cpu.idle{*} by {host}"),
            ("CPU iowait %", "avg:system.cpu.iowait{*} by {host}"),
            ("Load avg 1m", "avg:system.load.1{*} by {host}"),
            ("Load avg 5m", "avg:system.load.5{*} by {host}"),
            ("Load avg 15m", "avg:system.load.15{*} by {host}"),
            ("CPU steal", "avg:system.cpu.stolen{*} by {host}"),
            ("Nice CPU", "avg:system.cpu.nice{*} by {host}"),
            ("Guest CPU", "avg:system.cpu.guest{*} by {host}"),
            ("Context switches", "sum:system.cpu.context_switches{*}.as_rate() by {host}"),
            ("Interrupts", "sum:system.cpu.interrupt{*}.as_rate() by {host}"),
        ],
    ),
    (
        "06-host-memory.json",
        "Host memory",
        "Usable/used/free memory, swap, slab, page faults, buffers/cache, and commit limit proxies by host.",
        "Memory pressure boards are a must-have for infra metrics on Elastic once hosts emit OTel system metrics.",
        "",
        [
            ("Mem pct usable", "avg:system.mem.pct_usable{*} by {host}"),
            ("Mem used", "avg:system.mem.used{*} by {host}"),
            ("Mem free", "avg:system.mem.free{*} by {host}"),
            ("Swap used", "avg:system.swap.used{*} by {host}"),
            ("Swap pct", "avg:system.swap.pct_free{*} by {host}"),
            ("Slab", "avg:system.mem.slab{*} by {host}"),
            ("Page faults", "sum:system.mem.page_faults{*}.as_rate() by {host}"),
            ("Buffers", "avg:system.mem.buffered{*} by {host}"),
            ("Cached", "avg:system.mem.cached{*} by {host}"),
            ("Total memory", "avg:system.mem.total{*} by {host}"),
            ("Usable bytes", "avg:system.mem.usable{*} by {host}"),
            ("Commit limit proxy", "avg:system.mem.commit_limit{*} by {host}"),
        ],
    ),
    (
        "07-disk-io.json",
        "Disk I/O",
        "Disk utilization, read/write bytes and ops, queue length, and filesystem free/inode proxies by device/host.",
        "Storage metrics complete the host triad (CPU/mem/disk) for metrics adoption and capacity planning on Elastic.",
        "",
        [
            ("Disk IO avg", "avg:system.disk.io{*} by {device}"),
            ("Disk in use", "avg:system.disk.in_use{*} by {device}"),
            ("Read bytes", "sum:system.disk.read_bytes{*}.as_rate() by {device}"),
            ("Write bytes", "sum:system.disk.write_bytes{*}.as_rate() by {device}"),
            ("Read time", "avg:system.disk.read_time_pct{*} by {device}"),
            ("Write time", "avg:system.disk.write_time_pct{*} by {device}"),
            ("Queue length", "avg:system.disk.queue_size{*} by {device}"),
            ("IOPS read", "sum:system.disk.read_ops{*}.as_rate() by {device}"),
            ("IOPS write", "sum:system.disk.write_ops{*}.as_rate() by {device}"),
            ("Filesystem free %", "avg:system.disk.free{*} by {device}"),
            ("Inode usage", "avg:system.disk.in_use{*} by {host}"),
            ("IO utilization", "avg:system.io.util{*} by {device}"),
        ],
    ),
    (
        "08-network-bytes.json",
        "Network bytes",
        "Interface byte/packet rates, TCP retransmits, UDP/errors, connection counts, plus HTTP/DNS traffic context.",
        "Network metrics explain many app symptoms; adopting them on Elastic closes the gap between host and service views.",
        "",
        [
            ("Bytes sent rate", "sum:system.net.bytes_sent{*}.as_rate() by {interface}"),
            ("Bytes rcvd rate", "sum:system.net.bytes_rcvd{*}.as_rate() by {interface}"),
            ("TCP retransmits", "sum:system.net.tcp.retrans_segs{*}.as_rate() by {host}"),
            ("UDP errors", "sum:system.net.udp.in_errors{*}.as_rate() by {host}"),
            ("Packets in", "sum:system.net.packets_in.count{*}.as_rate() by {interface}"),
            ("Packets out", "sum:system.net.packets_out.count{*}.as_rate() by {interface}"),
            ("Connection count", "avg:system.net.tcp.connections{*} by {host}"),
            ("Listen overflows", "sum:system.net.tcp.listen_overflows{*}.as_rate() by {host}"),
            ("HTTP traffic proxy", "avg:trace.http.request.hits{*} by {service}"),
            ("DNS latency proxy", "avg:trace.dns.lookup.duration{*} by {service}"),
            ("Net errors in", "sum:system.net.errors_in{*}.as_rate() by {interface}"),
            ("Net errors out", "sum:system.net.errors_out{*}.as_rate() by {interface}"),
        ],
    ),
    (
        "09-container-throttle.json",
        "Container CPU throttle",
        "Container CPU throttle/usage, memory, network, restarts, OOM, and filesystem usage by container name.",
        "Container saturation is a modern metrics-adoption priority; this board exercises container_* series after OTel mapping.",
        "",
        [
            ("CPU throttled", "avg:container.cpu.throttled{*} by {container_name}"),
            ("CPU usage", "avg:container.cpu.usage{*} by {container_name}"),
            ("CPU user", "avg:container.cpu.user{*} by {container_name}"),
            ("CPU system", "avg:container.cpu.system{*} by {container_name}"),
            ("Mem usage", "avg:container.memory.usage{*} by {container_name}"),
            ("Mem limit", "avg:container.memory.limit{*} by {container_name}"),
            # Gauge rate proxies in otel_workshop_fleet — avoid .as_rate()/.as_count() (MAX/MIN on counters).
            ("Network RX", "avg:container.net.rcvd{*} by {container_name}"),
            ("Network TX", "avg:container.net.sent{*} by {container_name}"),
            ("Restarts", "avg:container.restarts{*} by {container_name}"),
            ("CPU shares", "avg:container.cpu.shares{*} by {container_name}"),
            ("OOM kills", "avg:container.oom_events{*} by {container_name}"),
            ("Filesystem usage", "avg:container.filesystem.usage{*} by {container_name}"),
        ],
    ),
    (
        "10-log-error-spike.json",
        "Log error spike",
        "Log-query widgets for error/warn spikes by path/service/namespace plus related trace and disk context metrics.",
        "Shows metrics+logs together — a key adoption story for customers already shipping logs to Elastic who want metrics and log signals on one board.",
        "Log widgets may need index/field tuning after migrate; metric widgets use the OTLP fleet.",
        [
            ("Errors by path", 'logs("status:error").index("*").rollup("count").by("@http.url_details.path")'),
            ("Errors by service", 'logs("status:error").index("*").rollup("count").by("service")'),
            ("All levels by service", 'logs("*").index("*").rollup("count").by("service")'),
            ("Warn + error", 'logs("status:warn OR status:error").index("*").rollup("count").by("service")'),
            ("By kube namespace", 'logs("*").index("*").rollup("count").by("kube_namespace")'),
            ("Security proxy", 'logs("source:security").index("*").rollup("count").by("service")'),
            ("Apache errors", 'logs("source:apache").index("*").rollup("count").by("host")'),
            ("Nginx access proxy", 'logs("source:nginx").index("*").rollup("count").by("http.url")'),
            ("Trace errors", "avg:trace.http.request.errors{*} by {service}"),
            ("HTTP hits context", "avg:trace.http.request.hits{*} by {service}"),
            ("Duration during spikes", "avg:trace.http.request.duration{*} by {service}"),
            ("Disk IO proxy", "avg:system.disk.io{*} by {host}"),
        ],
    ),
]


def widget_timeseries(title: str, q: str) -> dict:
    q = normalize_datadog_q_for_mig_parser(q)
    return {
        "definition": {
            "type": "timeseries",
            "title": title,
            "requests": [{"q": q, "display_type": "line"}],
        },
    }


def apply_grid_layout(widgets: list[dict], *, col_width: int = 6, row_height: int = 4, y_offset: int = 0) -> None:
    """Two columns (6+6 on a 12-wide DD layout), optionally shifted down for a note strip."""
    for i, w in enumerate(widgets):
        row, col = divmod(i, 2)
        w["layout"] = {
            "x": col * col_width,
            "y": y_offset + row * row_height,
            "width": col_width,
            "height": row_height,
        }


def build_dashboard(
    title: str,
    what: str,
    why: str,
    note: str,
    entries: list[tuple[str, str]],
) -> dict:
    del what, why, note  # author notes only; AI analysis is attached after migrate
    timeseries = [widget_timeseries(panel_title, q) for panel_title, q in entries]
    apply_grid_layout(timeseries, y_offset=0)
    return {
        "title": title,
        "description": f"{title} — metrics adoption workshop board (AI notes attached after migrate).",
        "widgets": timeseries,
        "template_variables": [{"name": "env", "default": "*", "prefix": "env"}],
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for filename, title, what, why, note, entries in DASHBOARDS:
        path = OUT / filename
        path.write_text(
            json.dumps(build_dashboard(title, what, why, note, entries), indent=2) + "\n",
            encoding="utf-8",
        )
        print("wrote", path, f"({len(entries)} timeseries)")


if __name__ == "__main__":
    main()
