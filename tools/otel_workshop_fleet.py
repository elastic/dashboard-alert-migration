#!/usr/bin/env python3
"""
Multiple synthetic microservices → OTLP → local Grafana Alloy → Elastic mOTLP.

Launches one Python subprocess per service (each has distinct service.name + host.name) so
**Applications**, **Infrastructure**, and **Hosts** in Observability show multiple entities.

Also emits **OpenTelemetry semantic attributes** on HTTP metrics (``http.route``, ``http.request.method``,
``http.response.status_code``) plus **resource** ``service.name`` / ``host.name``. HTTP **instrument names**
match workshop Grafana / **native PROMQL**: ``http_requests_total`` (counter) and ``http_request_duration_seconds``
(histogram, seconds). Labels use dotted keys (``service.name``, etc.), not legacy ``http_route`` spellings.

- **workshop.entity_id** on the resource plus **entity_id** on metric attributes (logical id; breakdowns use ``service.name`` in PromQL).
- **operation_errors_total** — counter with **reason** (mirrors ``operation_errors_total{reason=...}``).
- **Datadog rate-shaped infra metrics** (net/disk/container bytes & ops) and **APM proxy metrics**
  (``trace_http_request_hits``, errors, DNS/HTTP duration) are emitted as **gauges** (per-tick
  rate/value proxies), not OTel counters/histograms. ``datadog-migrate`` often approximates
  ``.as_rate()`` / ``.as_count()`` with ``MAX``/``MIN``/``SUM``, which ES|QL rejects on
  ``counter_long``, and ``AVG`` rejects histogram-typed fields (see
  elastic/observability-migration-platform#148). Gauge typing keeps those workshop panels green.

Parent process only supervises; workers are spawned with this same file + "worker" + JSON spec
so `pkill -f otel_workshop_fleet.py` stops the whole fleet.

Env:
  WORKSHOP_ALLOY_OTLP_HTTP — default http://127.0.0.1:4318
  WORKSHOP_EMIT_INTERVAL_SEC — base sleep between trace ticks per worker (default 5)
  WORKSHOP_REQUEST_BURST — synchronous HTTP counter/histogram records per tick (default 4) for denser TS in mOTLP
  WORKSHOP_ERROR_EMIT_PROB — probability [0,1] to emit one operation error per tick (default 0.18)
  WORKSHOP_METRIC_EXPORT_INTERVAL_MS — OTLP metric reader export interval (default 5000, clamp 3000–60000)
  For historical **metrics-*** lines in Discover over multi-day ranges, run **tools/seed_workshop_telemetry.py --metrics-time-series** (bulk; optional).
"""
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

# entity_id is a metric attribute; Grafana assets use sum by (service.name) for ES native PROMQL parity.
FLEET: list[dict[str, str]] = [
    {
        "service": "checkout-api",
        "entity_id": "shoplist-checkout",
        "host": "workshop-node-01",
        "version": "1.4.2",
        "lang": "python",
    },
    {
        "service": "inventory-api",
        "entity_id": "shoplist-inventory",
        "host": "workshop-node-02",
        "version": "2.0.1",
        "lang": "python",
    },
    {
        "service": "notifications-worker",
        "entity_id": "shoplist-notify",
        "host": "workshop-node-03",
        "version": "0.9.8",
        "lang": "go",
    },
    {
        "service": "frontend-web",
        "entity_id": "shoplist-web",
        "host": "workshop-node-04",
        "version": "3.2.0",
        "lang": "nodejs",
    },
    {
        "service": "pricing-api",
        "entity_id": "shoplist-pricing",
        "host": "workshop-node-05",
        "version": "1.1.0",
        "lang": "python",
    },
    {
        "service": "auth-service",
        "entity_id": "shoplist-auth",
        "host": "workshop-node-06",
        "version": "4.0.0",
        "lang": "python",
    },
]

# Mirrors Grafana ``operation_errors_total`` breakdown by reason (not HTTP status alone).
_OPERATION_ERROR_REASONS: tuple[str, ...] = (
    "timeout",
    "validation_failed",
    "rate_limited",
    "downstream_5xx",
    "circuit_open",
    "internal",
)


def _run_worker(spec: dict[str, str]) -> int:
    import math
    import random

    from opentelemetry import metrics, trace
    from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.metrics import Observation
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    base = (os.environ.get("WORKSHOP_ALLOY_OTLP_HTTP") or "http://127.0.0.1:4318").rstrip("/")
    service = spec["service"]
    entity_id = (spec.get("entity_id") or service).strip()
    host = spec["host"]
    version = spec["version"]
    lang = spec["lang"]
    seed = hash(service) % (2**32)
    rng = random.Random(seed)
    t0 = time.time()

    resource = Resource.create(
        {
            "service.name": service,
            "service.version": version,
            "deployment.environment": "instruqt",
            "host.name": host,
            "host.type": "linux",
            "os.type": "linux",
            "telemetry.sdk.name": "opentelemetry",
            "telemetry.sdk.language": lang,
            "cloud.provider": "aws",
            "cloud.region": "us-east-1",
            "cloud.availability_zone": "us-east-1a",
            # Custom resource attr — may appear as labels.workshop.entity_id / workshop.entity_id in ES
            "workshop.entity_id": entity_id,
        }
    )

    trace_provider = TracerProvider(resource=resource)
    trace_provider.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint=f"{base}/v1/traces"))
    )
    trace.set_tracer_provider(trace_provider)
    tracer = trace.get_tracer(__name__, version)

    def cpu_obs(_options: object):
        phase = (time.time() - t0) / 42.0 + (seed % 5)
        v = 0.22 + 0.38 * math.sin(phase) + rng.uniform(-0.06, 0.06)
        yield Observation(max(0.06, min(0.94, v)))

    def mem_obs(_options: object):
        phase = (time.time() - t0) / 55.0
        v = 0.38 + 0.28 * math.sin(phase * 0.85) + rng.uniform(-0.05, 0.05)
        yield Observation(max(0.18, min(0.93, v)))

    export_ms = int((os.environ.get("WORKSHOP_METRIC_EXPORT_INTERVAL_MS") or "5000").strip() or "5000")
    export_ms = max(3_000, min(export_ms, 60_000))
    reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(endpoint=f"{base}/v1/metrics"),
        export_interval_millis=export_ms,
    )
    metrics.set_meter_provider(MeterProvider(resource=resource, metric_readers=[reader]))
    meter = metrics.get_meter(__name__, version)

    meter.create_observable_gauge(
        "system.cpu.utilization",
        unit="1",
        description="CPU utilization (0–1) for host correlation",
        callbacks=[cpu_obs],
    )
    meter.create_observable_gauge(
        "system.memory.utilization",
        unit="1",
        description="Memory utilization (0–1) for host correlation",
        callbacks=[mem_obs],
    )

    duration_hist = meter.create_histogram(
        "http_request_duration_seconds",
        unit="s",
        description="HTTP latency (Prometheus histogram family for Grafana http_request_duration_seconds_*)",
    )
    req_counter = meter.create_counter(
        "http_requests_total",
        unit="1",
        description="HTTP requests (Prometheus-style counter for Grafana / PROMQL)",
    )
    # Name matches Grafana ``operation_errors_total`` so Elastic / mOTLP can surface a familiar metric.
    operation_errors = meter.create_counter(
        "operation_errors_total",
        unit="1",
        description="Synthetic operation errors (workshop) with Prometheus-style name for dashboard parity",
    )

    # Datadog-style metric *names* for mig-to-kbn ``otel`` profile (``.`` → ``_`` in ES|QL), so migrated
    # ``assets/datadog/dashboards/*.json`` panels resolve fields under ``metrics-generic.otel-*``.
    # Gauges (not counters/histograms): SUM/AVG from datadog-migrate fail on counter_long / histogram.
    trace_hits = meter.create_gauge(
        "trace_http_request_hits",
        unit="1",
        description="Datadog trace.http.request.hits → trace_http_request_hits (gauge count proxy)",
    )
    trace_errors = meter.create_gauge(
        "trace_http_request_errors",
        unit="1",
        description="Datadog trace.http.request.errors → trace_http_request_errors (gauge count proxy)",
    )
    trace_dur_ms = meter.create_gauge(
        "trace_http_request_duration",
        unit="ms",
        description="Datadog trace.http.request.duration (ms) gauge proxy for avg/pXX panels",
    )
    trace_client_errors = meter.create_gauge(
        "trace_http_client_errors",
        unit="1",
        description="Datadog trace.http.client_errors → trace_http_client_errors (gauge count proxy)",
    )
    trace_spans = meter.create_gauge(
        "trace_spans_finished",
        unit="1",
        description="Datadog trace.spans.finished → trace_spans_finished (gauge count proxy)",
    )
    trace_dns = meter.create_gauge(
        "trace_dns_lookup_duration",
        unit="ms",
        description="Datadog trace.dns.lookup.duration (ms) → trace_dns_lookup_duration (gauge)",
    )
    # Datadog ``.as_rate()`` panels → mig often emits MAX/MIN; emit as gauges for workshop smoke.
    def ctx_switches_obs(_options: object):
        yield Observation(float(rng.randint(1_200, 48_000)))

    meter.create_observable_gauge(
        "system_cpu_context_switches",
        unit="1",
        description="Datadog system.cpu.context_switches (gauge rate proxy for workshop)",
        callbacks=[ctx_switches_obs],
    )

    def _net_ifaces():
        return ("eth0", "ens5", "ens6")

    def _disk_devs():
        return ("/dev/xvda", "/dev/nvme0n1", "/dev/sda")

    def net_bytes_sent_obs(_options: object):
        for iface in _net_ifaces():
            yield Observation(float(rng.uniform(80_000, 5_000_000)), {"interface": iface})

    def net_bytes_rcvd_obs(_options: object):
        for iface in _net_ifaces():
            yield Observation(float(rng.uniform(120_000, 6_000_000)), {"interface": iface})

    def net_retrans_obs(_options: object):
        yield Observation(float(rng.randint(0, 8)))

    def net_udp_err_obs(_options: object):
        yield Observation(float(rng.randint(0, 3)))

    def net_pkt_in_obs(_options: object):
        for iface in _net_ifaces():
            yield Observation(float(rng.uniform(2_000, 90_000)), {"interface": iface})

    def net_pkt_out_obs(_options: object):
        for iface in _net_ifaces():
            yield Observation(float(rng.uniform(2_200, 95_000)), {"interface": iface})

    def net_listen_ovf_obs(_options: object):
        yield Observation(float(rng.randint(0, 2)))

    def net_err_in_obs(_options: object):
        for iface in _net_ifaces():
            yield Observation(float(rng.randint(0, 4)), {"interface": iface})

    def net_err_out_obs(_options: object):
        for iface in _net_ifaces():
            yield Observation(float(rng.randint(0, 3)), {"interface": iface})

    meter.create_observable_gauge(
        "system_net_bytes_sent", unit="By", description="system.net.bytes_sent (gauge rate proxy)", callbacks=[net_bytes_sent_obs]
    )
    meter.create_observable_gauge(
        "system_net_bytes_rcvd", unit="By", description="system.net.bytes_rcvd (gauge rate proxy)", callbacks=[net_bytes_rcvd_obs]
    )
    meter.create_observable_gauge(
        "system_net_tcp_retrans_segs",
        unit="1",
        description="system.net.tcp.retrans_segs (gauge rate proxy)",
        callbacks=[net_retrans_obs],
    )
    meter.create_observable_gauge(
        "system_net_udp_in_errors",
        unit="1",
        description="system.net.udp.in_errors (gauge rate proxy)",
        callbacks=[net_udp_err_obs],
    )
    meter.create_observable_gauge(
        "system_net_packets_in_count",
        unit="1",
        description="system.net.packets_in.count (gauge rate proxy)",
        callbacks=[net_pkt_in_obs],
    )
    meter.create_observable_gauge(
        "system_net_packets_out_count",
        unit="1",
        description="system.net.packets_out.count (gauge rate proxy)",
        callbacks=[net_pkt_out_obs],
    )
    meter.create_observable_gauge(
        "system_net_tcp_listen_overflows",
        unit="1",
        description="system.net.tcp.listen_overflows (gauge rate proxy)",
        callbacks=[net_listen_ovf_obs],
    )
    meter.create_observable_gauge(
        "system_net_errors_in", unit="1", description="system.net.errors_in (gauge rate proxy)", callbacks=[net_err_in_obs]
    )
    meter.create_observable_gauge(
        "system_net_errors_out", unit="1", description="system.net.errors_out (gauge rate proxy)", callbacks=[net_err_out_obs]
    )

    def disk_rb_obs(_options: object):
        for dev in _disk_devs():
            yield Observation(float(rng.uniform(50_000, 2_800_000)), {"device": dev})

    def disk_wb_obs(_options: object):
        for dev in _disk_devs():
            yield Observation(float(rng.uniform(40_000, 2_200_000)), {"device": dev})

    def disk_rop_obs(_options: object):
        for dev in _disk_devs():
            yield Observation(float(rng.uniform(20, 900)), {"device": dev})

    def disk_wop_obs(_options: object):
        for dev in _disk_devs():
            yield Observation(float(rng.uniform(25, 950)), {"device": dev})

    meter.create_observable_gauge(
        "system_disk_read_bytes", unit="By", description="system.disk.read_bytes (gauge rate proxy)", callbacks=[disk_rb_obs]
    )
    meter.create_observable_gauge(
        "system_disk_write_bytes", unit="By", description="system.disk.write_bytes (gauge rate proxy)", callbacks=[disk_wb_obs]
    )
    meter.create_observable_gauge(
        "system_disk_read_ops", unit="1", description="system.disk.read_ops (gauge rate proxy)", callbacks=[disk_rop_obs]
    )
    meter.create_observable_gauge(
        "system_disk_write_ops", unit="1", description="system.disk.write_ops (gauge rate proxy)", callbacks=[disk_wop_obs]
    )

    def tcp_conn_obs(_options: object):
        phase = (time.time() - t0) / 19.0 + (seed % 7) * 0.31
        v = 90.0 + 220.0 * (0.5 + 0.5 * math.sin(phase)) + rng.uniform(-18.0, 22.0)
        yield Observation(max(25.0, min(920.0, v)))

    meter.create_observable_gauge(
        "system_net_tcp_connections",
        unit="1",
        description="Datadog system.net.tcp.connections → system_net_tcp_connections",
        callbacks=[tcp_conn_obs],
    )

    def cpu_user_obs(_options: object):
        phase = (time.time() - t0) / 42.0 + (seed % 5)
        u = max(0.08, min(0.88, 0.22 + 0.38 * math.sin(phase) + rng.uniform(-0.04, 0.04)))
        yield Observation(u * 100.0)

    def cpu_sys_obs(_options: object):
        phase = (time.time() - t0) / 42.0 + (seed % 5)
        u = max(0.08, min(0.88, 0.22 + 0.38 * math.sin(phase)))
        sys_f = max(0.02, (1.0 - u) * 0.28)
        yield Observation(sys_f * 100.0)

    def cpu_idle_obs(_options: object):
        phase = (time.time() - t0) / 42.0 + (seed % 5)
        u = max(0.08, min(0.88, 0.22 + 0.38 * math.sin(phase)))
        idle = max(0.05, (1.0 - u) * 0.62)
        yield Observation(idle * 100.0)

    def cpu_iow_obs(_options: object):
        phase = (time.time() - t0) / 42.0 + (seed % 5)
        u = max(0.08, min(0.88, 0.22 + 0.38 * math.sin(phase)))
        iow = max(0.01, (1.0 - u) * 0.10)
        yield Observation(iow * 100.0)

    meter.create_observable_gauge(
        "system_cpu_user",
        unit="%",
        description="Datadog system.cpu.user → system_cpu_user",
        callbacks=[cpu_user_obs],
    )
    meter.create_observable_gauge(
        "system_cpu_system",
        unit="%",
        description="Datadog system.cpu.system → system_cpu_system",
        callbacks=[cpu_sys_obs],
    )
    meter.create_observable_gauge(
        "system_cpu_idle",
        unit="%",
        description="Datadog system.cpu.idle → system_cpu_idle",
        callbacks=[cpu_idle_obs],
    )
    meter.create_observable_gauge(
        "system_cpu_iowait",
        unit="%",
        description="Datadog system.cpu.iowait → system_cpu_iowait",
        callbacks=[cpu_iow_obs],
    )

    def cpu_nice_obs(_options: object):
        phase = (time.time() - t0) / 60.0 + (seed % 7) * 0.11
        yield Observation(max(0.5, min(4.0, 1.5 + 1.2 * math.sin(phase) + rng.uniform(-0.1, 0.1))))

    meter.create_observable_gauge(
        "system_cpu_nice",
        unit="%",
        description="Datadog system.cpu.nice → system_cpu_nice",
        callbacks=[cpu_nice_obs],
    )

    def cpu_stolen_obs(_options: object):
        phase = (time.time() - t0) / 80.0 + (seed % 9) * 0.07
        yield Observation(max(0.1, min(2.0, 0.6 + 0.5 * math.sin(phase) + rng.uniform(-0.05, 0.05))))

    meter.create_observable_gauge(
        "system_cpu_stolen",
        unit="%",
        description="Datadog system.cpu.stolen → system_cpu_stolen",
        callbacks=[cpu_stolen_obs],
    )

    def cpu_guest_obs(_options: object):
        phase = (time.time() - t0) / 95.0 + (seed % 11) * 0.09
        yield Observation(max(0.0, min(1.5, 0.4 + 0.4 * math.sin(phase) + rng.uniform(-0.03, 0.03))))

    meter.create_observable_gauge(
        "system_cpu_guest",
        unit="%",
        description="Datadog system.cpu.guest → system_cpu_guest",
        callbacks=[cpu_guest_obs],
    )

    def cpu_interrupt_obs(_options: object):
        phase = (time.time() - t0) / 8.0 + (seed % 13) * 0.13
        yield Observation(max(0.2, min(3.0, 0.8 + 0.7 * abs(math.sin(phase)) + rng.uniform(-0.1, 0.1))))

    meter.create_observable_gauge(
        "system_cpu_interrupt",
        unit="%",
        description="Datadog system.cpu.interrupt → system_cpu_interrupt",
        callbacks=[cpu_interrupt_obs],
    )

    def load1_obs(_options: object):
        phase = (time.time() - t0) / 28.0 + seed * 0.02
        yield Observation(max(0.15, min(14.0, 2.2 + 4.5 * math.sin(phase) + rng.uniform(-0.4, 0.4))))

    def load5_obs(_options: object):
        phase = (time.time() - t0) / 31.0 + seed * 0.02
        yield Observation(max(0.12, min(12.0, 2.0 + 3.8 * math.sin(phase * 0.9) + rng.uniform(-0.35, 0.35))))

    def load15_obs(_options: object):
        phase = (time.time() - t0) / 40.0 + seed * 0.02
        yield Observation(max(0.1, min(10.0, 1.8 + 3.2 * math.sin(phase * 0.85) + rng.uniform(-0.3, 0.3))))

    meter.create_observable_gauge("system_load_1", unit="1", callbacks=[load1_obs])
    meter.create_observable_gauge("system_load_5", unit="1", callbacks=[load5_obs])
    meter.create_observable_gauge("system_load_15", unit="1", callbacks=[load15_obs])

    def mem_pct_usable_obs(_options: object):
        phase = (time.time() - t0) / 55.0
        util = 0.38 + 0.28 * math.sin(phase * 0.85) + rng.uniform(-0.05, 0.05)
        util = max(0.12, min(0.88, util))
        yield Observation((1.0 - util) * 100.0)

    def mem_used_obs(_options: object):
        phase = (time.time() - t0) / 55.0
        util = 0.38 + 0.28 * math.sin(phase * 0.85)
        util = max(0.12, min(0.88, util))
        yield Observation((8e9 * util) + rng.uniform(-2e8, 2e8))

    def mem_free_obs(_options: object):
        phase = (time.time() - t0) / 55.0
        util = 0.38 + 0.28 * math.sin(phase * 0.85)
        util = max(0.12, min(0.88, util))
        yield Observation((16e9 * (1.0 - util)) + rng.uniform(-3e8, 3e8))

    def mem_total_obs(_options: object):
        yield Observation(16e9 + rng.uniform(-1e7, 1e7))

    meter.create_observable_gauge(
        "system_mem_pct_usable", unit="%", description="system.mem.pct_usable proxy", callbacks=[mem_pct_usable_obs]
    )
    meter.create_observable_gauge(
        "system_mem_used", unit="By", description="system.mem.used proxy", callbacks=[mem_used_obs]
    )
    meter.create_observable_gauge(
        "system_mem_free", unit="By", description="system.mem.free proxy", callbacks=[mem_free_obs]
    )
    meter.create_observable_gauge(
        "system_mem_total", unit="By", description="system.mem.total proxy", callbacks=[mem_total_obs]
    )

    def mem_cached_obs(_options: object):
        phase = (time.time() - t0) / 55.0
        yield Observation(max(0.8e9, 16e9 * 0.15 * (1.0 + 0.3 * math.sin(phase)) + rng.uniform(-1e8, 1e8)))

    meter.create_observable_gauge(
        "system_mem_cached", unit="By", description="system.mem.cached → system_mem_cached", callbacks=[mem_cached_obs]
    )

    def mem_usable_obs(_options: object):
        phase = (time.time() - t0) / 55.0
        util = max(0.12, min(0.88, 0.38 + 0.28 * math.sin(phase * 0.85)))
        yield Observation((16e9 * (1.0 - util)) + rng.uniform(-3e8, 3e8))

    meter.create_observable_gauge(
        "system_mem_usable", unit="By", description="system.mem.usable → system_mem_usable", callbacks=[mem_usable_obs]
    )

    def mem_buffered_obs(_options: object):
        phase = (time.time() - t0) / 55.0
        yield Observation(max(2e8, 16e9 * 0.055 * (1.0 + 0.2 * math.sin(phase * 0.6)) + rng.uniform(-5e7, 5e7)))

    meter.create_observable_gauge(
        "system_mem_buffered",
        unit="By",
        description="system.mem.buffered → system_mem_buffered",
        callbacks=[mem_buffered_obs],
    )

    def mem_slab_obs(_options: object):
        phase = (time.time() - t0) / 55.0
        yield Observation(max(1e8, 16e9 * 0.035 * (1.0 + 0.15 * math.sin(phase * 0.4)) + rng.uniform(-3e7, 3e7)))

    meter.create_observable_gauge(
        "system_mem_slab", unit="By", description="system.mem.slab → system_mem_slab", callbacks=[mem_slab_obs]
    )

    def mem_commit_limit_obs(_options: object):
        yield Observation(24e9 + rng.uniform(-1e7, 1e7))

    meter.create_observable_gauge(
        "system_mem_commit_limit",
        unit="By",
        description="system.mem.commit_limit → system_mem_commit_limit",
        callbacks=[mem_commit_limit_obs],
    )

    def swap_used_obs(_options: object):
        phase = (time.time() - t0) / 90.0 + seed * 0.01
        yield Observation(max(0.5e9, min(3e9, 1.5e9 + 1.2e9 * math.sin(phase) + rng.uniform(-1e8, 1e8))))

    meter.create_observable_gauge(
        "system_swap_used", unit="By", description="system.swap.used → system_swap_used", callbacks=[swap_used_obs]
    )

    def swap_pct_free_obs(_options: object):
        phase = (time.time() - t0) / 90.0 + seed * 0.01
        swap_used = max(0.5e9, min(3e9, 1.5e9 + 1.2e9 * math.sin(phase)))
        yield Observation(max(0.0, min(100.0, (4e9 - swap_used) / 4e9 * 100.0)))

    meter.create_observable_gauge(
        "system_swap_pct_free",
        unit="%",
        description="system.swap.pct_free → system_swap_pct_free",
        callbacks=[swap_pct_free_obs],
    )

    mem_page_faults = meter.create_counter(
        "system_mem_page_faults",
        unit="1",
        description="system.mem.page_faults → system_mem_page_faults",
    )

    def disk_io_obs(_options: object):
        phase = (time.time() - t0) / 23.0 + seed * 0.05
        yield Observation(max(1.0, min(98.0, 35.0 + 40.0 * math.sin(phase) + rng.uniform(-6.0, 6.0))))

    meter.create_observable_gauge(
        "system_disk_io", unit="%", description="system.disk.io proxy", callbacks=[disk_io_obs]
    )

    _DISK_DEVICES = ("/dev/xvda", "/dev/nvme0n1", "/dev/sda")

    def disk_free_obs(_options: object):
        phase = (time.time() - t0) / 77.0 + seed * 0.03
        for dev_name in _DISK_DEVICES:
            yield Observation(
                max(20e9, min(180e9, 100e9 + 60e9 * math.sin(phase) + rng.uniform(-5e9, 5e9))),
                {"device": dev_name},
            )

    meter.create_observable_gauge(
        "system_disk_free", unit="By", description="system.disk.free → system_disk_free", callbacks=[disk_free_obs]
    )

    def disk_in_use_obs(_options: object):
        phase = (time.time() - t0) / 77.0 + seed * 0.03
        for dev_name in _DISK_DEVICES:
            free = max(20e9, min(180e9, 100e9 + 60e9 * math.sin(phase)))
            yield Observation(max(5.0, min(95.0, (200e9 - free) / 200e9 * 100.0)), {"device": dev_name})

    meter.create_observable_gauge(
        "system_disk_in_use",
        unit="%",
        description="system.disk.in_use → system_disk_in_use",
        callbacks=[disk_in_use_obs],
    )

    def disk_queue_obs(_options: object):
        phase = (time.time() - t0) / 23.0 + seed * 0.05
        for dev_name in _DISK_DEVICES:
            yield Observation(
                max(0.0, min(8.0, 2.0 + 4.0 * abs(math.sin(phase)) + rng.uniform(-0.5, 0.5))),
                {"device": dev_name},
            )

    meter.create_observable_gauge(
        "system_disk_queue_size",
        unit="1",
        description="system.disk.queue_size → system_disk_queue_size",
        callbacks=[disk_queue_obs],
    )

    def disk_read_time_obs(_options: object):
        phase = (time.time() - t0) / 23.0 + seed * 0.05
        for dev_name in _DISK_DEVICES:
            yield Observation(
                max(1.0, min(40.0, 12.0 + 18.0 * abs(math.sin(phase)) + rng.uniform(-1.0, 1.0))),
                {"device": dev_name},
            )

    meter.create_observable_gauge(
        "system_disk_read_time_pct",
        unit="%",
        description="system.disk.read_time_pct → system_disk_read_time_pct",
        callbacks=[disk_read_time_obs],
    )

    def disk_write_time_obs(_options: object):
        phase = (time.time() - t0) / 23.0 + seed * 0.05 + 1.1
        for dev_name in _DISK_DEVICES:
            yield Observation(
                max(0.5, min(25.0, 7.0 + 12.0 * abs(math.sin(phase)) + rng.uniform(-0.5, 0.5))),
                {"device": dev_name},
            )

    meter.create_observable_gauge(
        "system_disk_write_time_pct",
        unit="%",
        description="system.disk.write_time_pct → system_disk_write_time_pct",
        callbacks=[disk_write_time_obs],
    )

    def disk_io_util_obs(_options: object):
        phase = (time.time() - t0) / 23.0 + seed * 0.05
        for dev_name in _DISK_DEVICES:
            yield Observation(
                max(1.0, min(98.0, 35.0 + 40.0 * math.sin(phase) + rng.uniform(-6.0, 6.0))),
                {"device": dev_name},
            )

    meter.create_observable_gauge(
        "system_io_util", unit="%", description="system.io.util → system_io_util", callbacks=[disk_io_util_obs]
    )

    def apdex_obs(_options: object):
        phase = (time.time() - t0) / 67.0 + (seed % 11) * 0.09
        yield Observation(max(0.55, min(0.995, 0.82 + 0.14 * math.sin(phase))))

    meter.create_observable_gauge("app_apdex_score", unit="1", description="app.apdex.score proxy", callbacks=[apdex_obs])

    def container_cpu_obs(_options: object):
        yield Observation(
            max(3.0, min(92.0, 18.0 + rng.uniform(0, 55.0))),
            {"container.name": f"{service}-main"},
        )
        yield Observation(
            max(2.0, min(40.0, 8.0 + rng.uniform(0, 22.0))),
            {"container.name": f"{service}-sidecar"},
        )

    meter.create_observable_gauge(
        "container_cpu_usage",
        unit="%",
        description="container.cpu.usage proxy (by container.name)",
        callbacks=[container_cpu_obs],
    )
    container_throttled = meter.create_counter(
        "container_cpu_throttled",
        unit="1",
        description="container.cpu.throttled proxy",
    )

    def container_mem_usage_obs(_options: object):
        # Datadog container.memory.usage → container_memory_usage (Container CPU throttle board).
        phase = (time.time() - t0) / 55.0 + (seed % 7) * 0.11
        for cname, base in ((f"{service}-main", 512e6), (f"{service}-sidecar", 128e6)):
            v = base + base * 0.35 * (0.5 + 0.5 * math.sin(phase)) + rng.uniform(-8e6, 8e6)
            yield Observation(max(32e6, v), {"container.name": cname})

    def container_mem_limit_obs(_options: object):
        # Datadog container.memory.limit → container_memory_limit.
        yield Observation(1024e6, {"container.name": f"{service}-main"})
        yield Observation(256e6, {"container.name": f"{service}-sidecar"})

    meter.create_observable_gauge(
        "container_memory_usage",
        unit="By",
        description="Datadog container.memory.usage → container_memory_usage",
        callbacks=[container_mem_usage_obs],
    )
    meter.create_observable_gauge(
        "container_memory_limit",
        unit="By",
        description="Datadog container.memory.limit → container_memory_limit",
        callbacks=[container_mem_limit_obs],
    )

    def container_net_rcvd_obs(_options: object):
        for cname in (f"{service}-main", f"{service}-sidecar"):
            yield Observation(float(rng.uniform(8_000, 420_000)), {"container.name": cname})

    def container_net_sent_obs(_options: object):
        for cname in (f"{service}-main", f"{service}-sidecar"):
            yield Observation(float(rng.uniform(9_000, 480_000)), {"container.name": cname})

    meter.create_observable_gauge(
        "container_net_rcvd",
        unit="By",
        description="container.net.rcvd (gauge rate proxy)",
        callbacks=[container_net_rcvd_obs],
    )
    meter.create_observable_gauge(
        "container_net_sent",
        unit="By",
        description="container.net.sent (gauge rate proxy)",
        callbacks=[container_net_sent_obs],
    )

    def container_cpu_user_obs(_options):
        phase = (time.time() - t0) / 42.0 + (seed % 5)
        for cname, scale in ((f"{service}-main", 1.0), (f"{service}-sidecar", 0.4)):
            u = max(5.0, min(60.0, (0.22 + 0.38 * math.sin(phase)) * 100.0 * scale + rng.uniform(-2.0, 2.0)))
            yield Observation(u, {"container.name": cname})

    meter.create_observable_gauge(
        "container_cpu_user",
        unit="%",
        description="Datadog container.cpu.user → container_cpu_user (per container)",
        callbacks=[container_cpu_user_obs],
    )

    def container_cpu_system_obs(_options):
        phase = (time.time() - t0) / 42.0 + (seed % 5)
        for cname, scale in ((f"{service}-main", 1.0), (f"{service}-sidecar", 0.4)):
            u = max(0.08, min(0.88, 0.22 + 0.38 * math.sin(phase)))
            sys_f = max(1.0, min(20.0, (1.0 - u) * 0.28 * 100.0 * scale + rng.uniform(-0.5, 0.5)))
            yield Observation(sys_f, {"container.name": cname})

    meter.create_observable_gauge(
        "container_cpu_system",
        unit="%",
        description="Datadog container.cpu.system → container_cpu_system (per container)",
        callbacks=[container_cpu_system_obs],
    )

    def container_cpu_shares_obs(_options):
        yield Observation(512.0, {"container.name": f"{service}-main"})
        yield Observation(256.0, {"container.name": f"{service}-sidecar"})

    meter.create_observable_gauge(
        "container_cpu_shares",
        unit="1",
        description="Datadog container.cpu.shares → container_cpu_shares",
        callbacks=[container_cpu_shares_obs],
    )

    def container_fs_usage_obs(_options):
        phase = (time.time() - t0) / 120.0 + (seed % 3) * 0.7
        for cname, base in ((f"{service}-main", 4e9), (f"{service}-sidecar", 1.5e9)):
            v = base + 2e9 * (0.5 + 0.5 * math.sin(phase)) + rng.uniform(-1e8, 1e8)
            yield Observation(max(0.5e9, v), {"container.name": cname})

    meter.create_observable_gauge(
        "container_filesystem_usage",
        unit="By",
        description="Datadog container.fs.usage → container_filesystem_usage (per container)",
        callbacks=[container_fs_usage_obs],
    )

    # K8s-semantic proxy — gauge values so SUM/MAX panels from datadog-migrate render
    def container_restarts_obs(_options: object):
        for cname in (f"{service}-main", f"{service}-sidecar"):
            yield Observation(float(rng.randint(0, 3)), {"container.name": cname})

    def container_oom_obs(_options: object):
        for cname in (f"{service}-main", f"{service}-sidecar"):
            yield Observation(float(rng.randint(0, 1)), {"container.name": cname})

    meter.create_observable_gauge(
        "container_restarts",
        unit="1",
        description="Datadog kubernetes.containers.restarts (gauge proxy)",
        callbacks=[container_restarts_obs],
    )
    meter.create_observable_gauge(
        "container_oom_events",
        unit="1",
        description="Datadog kubernetes.containers.oom_killed (gauge proxy)",
        callbacks=[container_oom_obs],
    )

    routes = ["/health", "/api/v1/orders", "/api/v1/users", "/api/v1/cart", "/readyz"]
    interval = float((os.environ.get("WORKSHOP_EMIT_INTERVAL_SEC") or "5").strip() or "5")
    try:
        burst = int((os.environ.get("WORKSHOP_REQUEST_BURST") or "4").strip() or "4")
    except ValueError:
        burst = 4
    burst = max(1, min(burst, 64))
    try:
        err_prob = float((os.environ.get("WORKSHOP_ERROR_EMIT_PROB") or "0.18").strip() or "0.18")
    except ValueError:
        err_prob = 0.18
    err_prob = max(0.0, min(1.0, err_prob))

    print(f"fleet worker {service} @ {host} → {base}", flush=True)
    n = 0
    while True:
        n += 1
        route = routes[n % len(routes)]
        status = rng.choice([200, 200, 200, 201, 204, 429, 500])
        method = "GET" if n % 3 else "POST"
        span_name = f"{method} {route}"
        base_attrs = {
            "http.route": route,
            "http.request.method": method,
            "http.response.status_code": str(status),
            "entity_id": entity_id,
        }
        with tracer.start_as_current_span(span_name) as span:
            span.set_attribute("http.request.method", method)
            span.set_attribute("http.route", route)
            span.set_attribute("http.response.status_code", status)
            span.set_attribute("url.scheme", "http")
            span.set_attribute("server.address", host)
            span.set_attribute("entity_id", entity_id)

        dd_trace_attrs = {
            "service.name": service,
            "resource_name": route,
            "http.route": route,
        }
        # Gauge proxies: set last-tick values (SUM/AVG-friendly; not counter_long / histogram).
        trace_hits.set(float(burst), dd_trace_attrs)
        trace_dur_ms.set(round(rng.uniform(6.0, 220.0), 2), dd_trace_attrs)
        err_n = float(burst if status >= 500 else (1 if status == 429 or rng.random() < 0.09 else 0))
        trace_errors.set(err_n, {**dd_trace_attrs, "http.status_code": str(status)})
        trace_spans.set(float(burst), {"service.name": service})
        trace_client_errors.set(
            1.0 if (status >= 500 or status == 429 or rng.random() < 0.09) else 0.0,
            {"service.name": service, "http.route": route},
        )
        trace_dns.set(round(rng.uniform(0.5, 80.0), 2), {"service.name": service})

        for _ in range(burst):
            duration_s = round(rng.uniform(0.006, 0.42), 4)
            duration_hist.record(duration_s, base_attrs)
            req_counter.add(1, base_attrs)

        mem_page_faults.add(rng.randint(50, 4_000), {})

        # Net/disk/container rate proxies are observable gauges (callbacks above).

        container_throttled.add(rng.randint(0, 4), {"container.name": f"{service}-main"})
        container_throttled.add(rng.randint(0, 2), {"container.name": f"{service}-sidecar"})

        if status >= 500 or rng.random() < err_prob:
            reason = (
                "http_5xx"
                if status >= 500
                else rng.choice(_OPERATION_ERROR_REASONS)
            )
            operation_errors.add(
                1,
                {
                    "reason": reason,
                    "entity_id": entity_id,
                    "http.route": route,
                },
            )

        time.sleep(max(2.0, interval + rng.uniform(-1.0, 2.0)))


def _supervise() -> int:
    myself = str(Path(__file__).resolve())
    repo_root = str(Path(__file__).resolve().parent.parent)
    exe = sys.executable
    children: list[subprocess.Popen[str]] = []
    log_path = os.environ.get("WORKSHOP_FLEET_LOG") or "/tmp/workshop-fleet.log"
    log_f = open(log_path, "a", encoding="utf-8", buffering=1)

    for spec in FLEET:
        cmd = [exe, myself, "worker", json.dumps(spec)]
        children.append(
            subprocess.Popen(
                cmd,
                stdout=log_f,
                stderr=subprocess.STDOUT,
                cwd=repo_root,
            )
        )

    print(
        f"otel_workshop_fleet: started {len(children)} workers → Alloy :4318 (log {log_path})",
        flush=True,
    )

    def _terminate_children() -> None:
        for c in children:
            if c.poll() is None:
                c.terminate()
        deadline = time.time() + 12
        for c in children:
            remaining = max(0.1, deadline - time.time())
            try:
                c.wait(timeout=remaining)
            except subprocess.TimeoutExpired:
                c.kill()
        try:
            log_f.close()
        except OSError:
            pass

    def _on_signal(_sig: int | None = None, _frame: object | None = None) -> None:
        _terminate_children()
        sys.exit(0)

    signal.signal(signal.SIGTERM, _on_signal)
    signal.signal(signal.SIGINT, _on_signal)

    try:
        while True:
            time.sleep(5)
            for c in children:
                if c.poll() is not None:
                    print(f"WARN: fleet worker exited code={c.returncode}, stopping fleet", flush=True)
                    _terminate_children()
                    sys.exit(1)
    except KeyboardInterrupt:
        _terminate_children()
        sys.exit(0)


def main() -> int:
    if len(sys.argv) >= 3 and sys.argv[1] == "worker":
        _run_worker(json.loads(sys.argv[2]))
        return 0
    return _supervise()


if __name__ == "__main__":
    raise SystemExit(main())
