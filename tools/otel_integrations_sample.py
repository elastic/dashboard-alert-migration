#!/usr/bin/env python3
"""
Synthetic OTLP metrics for optional Datadog **integrations-core** dashboards.

Emits gauges named for the otel field profile (``nginx.net.request_per_s`` →
``nginx_net_request_per_s``) so migrated NGINX / Postgres / RabbitMQ / Redis /
MySQL / Apache / Docker / Kubernetes boards can paint without real agents.

Redis Overview needs extra dimensions the Datadog board groups on:
``command`` / ``name`` (slowlog panels) and ``key`` (key-length + dashboard filter).

RabbitMQ Overview (OpenMetrics) groups Node Status by ``rabbitmq_node`` and filters
``queue`` / ``rabbitmq_conn_state`` — those attributes are set on the matching instruments.

Usage (workshop VM)::

  source ~/.bashrc
  # Alloy must already be up (start_workshop_otel.sh)
  python3 tools/otel_integrations_sample.py

Env:
  WORKSHOP_ALLOY_OTLP_HTTP — default http://127.0.0.1:4318
  WORKSHOP_METRIC_EXPORT_INTERVAL_MS — default 5000
"""
from __future__ import annotations

import json
import math
import os
import random
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets" / "datadog" / "integrations-core"


def discover_metric_instruments() -> list[str]:
    """Datadog dotted names → OTel instrument ids (dots → underscores)."""
    found: set[str] = set()
    if ASSETS.is_dir():
        for path in ASSETS.glob("*.json"):
            try:
                blob = json.dumps(json.loads(path.read_text(encoding="utf-8")))
            except (OSError, json.JSONDecodeError):
                continue
            for name in re.findall(r"(?:avg|sum|max|min|p\d+):([a-zA-Z0-9_.]+)\s*\{", blob):
                found.add(name.replace(".", "_"))
    # Always include core nginx/postgres set even if assets missing
    found.update(
        {
            "nginx_net_connections",
            "nginx_net_request_per_s",
            "nginx_net_reading",
            "nginx_net_writing",
            "nginx_net_waiting",
            "nginx_net_conn_dropped_per_s",
            "postgresql_connections",
            "postgresql_rows_fetched",
            "postgresql_rows_inserted",
            "postgresql_rows_returned",
            "postgresql_rows_updated",
        }
    )
    return sorted(found)


def _value_for(name: str, t: float, rng: random.Random) -> float:
    phase = t / 37.0 + (hash(name) % 97) * 0.07
    wave = 0.5 + 0.5 * math.sin(phase)
    n = name.lower()
    if any(x in n for x in ("_pct", "utilisation", "utilization", "ratio", "cpu_load")):
        return max(0.05, min(0.99, 0.35 + 0.45 * wave + rng.uniform(-0.05, 0.05)))
    if "bytes" in n or "mem_" in n or "memory" in n or "rss" in n or "cache" in n:
        base = 5e7 if "disk" in n or "available" in n or "maxmemory" in n else 2e6
        return max(1e3, base * (0.4 + 0.8 * wave) + rng.uniform(-base * 0.05, base * 0.05))
    if any(x in n for x in ("_per_s", "request", "commands", "hits", "misses", "ops")):
        return max(1.0, 40.0 + 220.0 * wave + rng.uniform(-15.0, 25.0))
    if "latency" in n or "micros" in n or "delay" in n:
        return max(0.2, 8.0 + 40.0 * wave + rng.uniform(-2.0, 4.0))
    if any(x in n for x in ("connections", "clients", "channels", "queues", "pods", "containers", "keys")):
        return max(1.0, 12.0 + 80.0 * wave + rng.uniform(-5.0, 8.0))
    if "uptime" in n:
        return 86_400.0 + (t % 10_000)
    if "limit" in n or "max_" in n or "maxmemory" in n:
        return 10_000.0
    if "restarts" in n or "oom" in n or "terminated" in n or "dropped" in n:
        return float(rng.randint(0, 4))
    if "ready" in n or "running" in n or "phase" in n:
        return float(rng.choice([0, 1]))
    return max(0.0, 10.0 + 50.0 * wave + rng.uniform(-5.0, 5.0))


def main() -> int:
    try:
        from opentelemetry import metrics
        from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
        from opentelemetry.metrics import Observation
        from opentelemetry.sdk.metrics import MeterProvider
        from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
        from opentelemetry.sdk.resources import Resource
    except ImportError:
        print(
            "ERROR: opentelemetry packages missing. On the VM use the workshop Alloy/venv "
            "or: pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp-proto-http",
            file=sys.stderr,
        )
        return 1

    base = (os.environ.get("WORKSHOP_ALLOY_OTLP_HTTP") or "http://127.0.0.1:4318").rstrip("/")
    export_ms = int((os.environ.get("WORKSHOP_METRIC_EXPORT_INTERVAL_MS") or "5000").strip() or "5000")
    export_ms = max(3_000, min(export_ms, 60_000))
    instruments = discover_metric_instruments()
    rng = random.Random(42)
    t0 = time.time()

    resource = Resource.create(
        {
            "service.name": "workshop-integrations",
            "service.version": "1.0.0",
            "deployment.environment": "instruqt",
            "host.name": "workshop-integrations-01",
            "host.type": "linux",
            "os.type": "linux",
            "telemetry.sdk.name": "opentelemetry",
            "telemetry.sdk.language": "python",
            "workshop.sample": "datadog-integrations-core",
        }
    )
    reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(endpoint=f"{base}/v1/metrics"),
        export_interval_millis=export_ms,
    )
    provider = MeterProvider(resource=resource, metric_readers=[reader])
    metrics.set_meter_provider(provider)
    meter = metrics.get_meter("workshop.integrations.sample", "1.0.0")

    hosts = ("workshop-integrations-01", "workshop-integrations-02")
    queues = ("orders", "notifications", "billing")
    rabbit_nodes = ("rabbit@workshop-rmq-1", "rabbit@workshop-rmq-2")
    rabbit_conn_states = ("running", "blocked", "blocking")
    pods = ("nginx-7f8d9", "postgres-0", "redis-master-0", "rabbitmq-0")
    redis_commands = (
        ("GET", "user:session"),
        ("SET", "cart:checkout"),
        ("HGET", "catalog:item"),
        ("ZADD", "leaderboard"),
        ("LPUSH", "jobs:queue"),
    )
    redis_keys = ("user:session", "cart:checkout", "catalog:item", "jobs:queue", "cache:homepage")

    def make_callback(instr: str):
        def _cb(_options: object):
            now = time.time() - t0
            # Multi-series for common group-bys on integration boards
            if instr.startswith("rabbitmq_queue_"):
                for node in rabbit_nodes:
                    for q in queues:
                        yield Observation(
                            _value_for(instr, now + hash(q) % 7, rng),
                            {
                                "queue": q,
                                "rabbitmq_queue": q,
                                "rabbitmq_node": node,
                                "host.name": hosts[0],
                                "host": hosts[0],
                            },
                        )
                return
            if instr.startswith("rabbitmq_connection_") or instr.startswith("rabbitmq_channel_"):
                for node in rabbit_nodes:
                    for state in rabbit_conn_states:
                        yield Observation(
                            _value_for(instr, now + hash(state) % 5, rng),
                            {
                                "rabbitmq_node": node,
                                "rabbitmq_conn_state": state,
                                "host.name": hosts[0],
                                "host": hosts[0],
                            },
                        )
                return
            if instr.startswith("rabbitmq_"):
                # Node Status panels: by {rabbitmq_node}; filters use rabbitmq_node / queue prefixes.
                for node in rabbit_nodes:
                    yield Observation(
                        _value_for(instr, now + hash(node) % 5, rng),
                        {
                            "rabbitmq_node": node,
                            "host.name": hosts[0],
                            "host": hosts[0],
                        },
                    )
                return
            if instr.startswith("kubernetes_") or instr.startswith("kubernetes_state_"):
                for pod in pods:
                    yield Observation(
                        _value_for(instr, now, rng),
                        {
                            "k8s.pod.name": pod,
                            "k8s.namespace.name": "default",
                            "kube_namespace": "default",
                            "pod_name": pod,
                            "host.name": hosts[0],
                            "host": hosts[0],
                        },
                    )
                return
            if instr.startswith("docker_"):
                for cname, image in (
                    ("nginx", "nginx:1.25"),
                    ("postgres", "postgres:16"),
                    ("redis", "redis:7"),
                    ("rabbitmq", "rabbitmq:3.13"),
                ):
                    yield Observation(
                        _value_for(instr, now, rng),
                        {
                            "container.name": cname,
                            "container_name": cname,
                            "docker_image": image,
                            "host.name": hosts[0],
                            "host": hosts[0],
                        },
                    )
                return
            # Redis Overview: slowlog by {name,command}; key length by {key}; host filters.
            if instr.startswith("redis_slowlog_"):
                for host in hosts:
                    for command, name in redis_commands:
                        yield Observation(
                            _value_for(instr, now + hash(command) % 9, rng),
                            {
                                "host.name": host,
                                "host": host,
                                "command": command,
                                "name": name,
                            },
                        )
                return
            if instr == "redis_key_length" or instr.startswith("redis_key_"):
                for host in hosts:
                    for key in redis_keys:
                        yield Observation(
                            _value_for(instr, now + hash(key) % 11, rng),
                            {
                                "host.name": host,
                                "host": host,
                                "key": key,
                            },
                        )
                return
            if instr.startswith("redis_"):
                for host in hosts:
                    yield Observation(
                        _value_for(instr, now, rng),
                        {"host.name": host, "host": host},
                    )
                return
            for host in hosts:
                yield Observation(
                    _value_for(instr, now, rng),
                    {"host.name": host, "host": host},
                )

        return _cb

    for instr in instruments:
        # Skip system_* already emitted by the main workshop fleet (avoid type fights).
        if instr.startswith("system_"):
            continue
        unit = "1"
        if "bytes" in instr:
            unit = "By"
        elif "latency" in instr or "micros" in instr:
            unit = "ms"
        meter.create_observable_gauge(
            instr,
            unit=unit,
            description=f"Workshop sample for integrations-core → {instr}",
            callbacks=[make_callback(instr)],
        )

    print(
        f"integrations sample emitter → {base}/v1/metrics "
        f"({len(instruments)} instruments discovered; system_* skipped)",
        flush=True,
    )
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        print("stopped", flush=True)
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
