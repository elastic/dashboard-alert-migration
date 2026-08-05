#!/usr/bin/env python3
"""
Emit OpenTelemetry (traces, metrics, logs) with Datadog-style service/tags into local Grafana Alloy,
which forwards to Elastic Observability **managed OTLP** (mOTLP).

Use this in the Datadog→Elastic migration narrative: same OTLP you would dual-ship or migrate toward,
landing in Elastic’s managed collector instead of Datadog intake.

Log fields are shaped for the workshop **Log error spike** board after ``datadog-migrate
--field-profile otel``:

  status:error|warn  → log.level == "error"|"warn"   (lowercase severity_text)
  @http.url… / http.url → http.url
  kube_namespace     → k8s.namespace.name
  source:security|apache|nginx → service.name

Env:
  WORKSHOP_ALLOY_OTLP_HTTP — default http://127.0.0.1:4318 (Alloy HTTP OTLP receiver)
  WORKSHOP_DD_OTEL_INTERVAL_SEC — seconds between ticks (default 12)
"""
from __future__ import annotations

import os
import random
import sys
import time
from typing import Any

from opentelemetry import metrics, trace
from opentelemetry._logs import SeverityNumber, set_logger_provider
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.sdk._logs._internal import LogRecord
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# (service.name, k8s.namespace.name, host.name) — source:* panels map source → service.name
_LOG_SOURCES: list[tuple[str, str, str]] = [
    ("shopist-checkout", "shopist", "workshop-node-07"),
    ("security", "security", "workshop-node-07"),
    ("apache", "web", "workshop-node-03"),
    ("nginx", "ingress", "workshop-node-02"),
]

_ROUTES = [("/api/cart", "GET"), ("/api/checkout", "POST"), ("/api/orders", "GET")]

_LEVEL_TO_SEVERITY = {
    "error": SeverityNumber.ERROR,
    "warn": SeverityNumber.WARN,
    "info": SeverityNumber.INFO,
}


def _resource(*, service: str, namespace: str, host: str) -> Resource:
    # Datadog Agent / OTLP mapping–friendly resource (service, env, version, host, k8s).
    return Resource.create(
        {
            "service.name": service,
            "deployment.environment": (os.environ.get("DD_ENV") or "staging"),
            "service.version": (os.environ.get("DD_VERSION") or "2.7.0"),
            "host.name": host,
            "k8s.namespace.name": namespace,
            # Also set ECS-style name used by the elastic_agent field profile.
            "kubernetes.namespace": namespace,
            "telemetry.sdk.name": "opentelemetry",
            "telemetry.sdk.language": "python",
        }
    )


def _emit_log(
    logger: Any,
    *,
    level: str,
    body: str,
    route: str,
    method: str,
    status: int,
    duration_ms: float,
    service: str,
    env: str,
) -> None:
    """Emit a log with ECS/OTel attributes the migrated Log error spike panels expect."""
    # Lowercase severity_text so Elastic → log.level matches Datadog status:error|warn.
    logger.emit(
        LogRecord(
            timestamp=time.time_ns(),
            observed_timestamp=time.time_ns(),
            severity_text=level,
            severity_number=_LEVEL_TO_SEVERITY[level],
            body=body,
            attributes={
                "http.url": route,
                "http.route": route,
                "http.request.method": method,
                "http.response.status_code": status,
                "http.status_code": status,
                "duration_ms": duration_ms,
                "log.level": level,
                "dd.service": service,
                "dd.env": env,
            },
        )
    )


def main() -> int:
    base = (os.environ.get("WORKSHOP_ALLOY_OTLP_HTTP") or "http://127.0.0.1:4318").rstrip("/")
    interval = float((os.environ.get("WORKSHOP_DD_OTEL_INTERVAL_SEC") or "12").strip() or "12")

    primary_service = os.environ.get("DD_SERVICE") or "shopist-checkout"
    primary_host = os.environ.get("DD_HOSTNAME") or "workshop-node-07"
    primary_ns = "shopist"
    primary = _resource(service=primary_service, namespace=primary_ns, host=primary_host)

    trace_provider = TracerProvider(resource=primary)
    trace_provider.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint=f"{base}/v1/traces"))
    )
    trace.set_tracer_provider(trace_provider)

    reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(endpoint=f"{base}/v1/metrics"),
        export_interval_millis=max(5_000, int(interval * 1000)),
    )
    metrics.set_meter_provider(MeterProvider(resource=primary, metric_readers=[reader]))
    meter = metrics.get_meter(__name__, "1.0.0")

    checkout_counter = meter.create_counter(
        "dd.checkout.completed",
        description="Datadog-style custom counter (maps to custom metric in Elastic)",
    )
    latency_hist = meter.create_histogram(
        "dd.http.server.request.duration",
        unit="ms",
        description="Request duration (Datadog-style naming; OTel histogram)",
    )

    # One LoggerProvider per source service so resource.service.name matches source:* panels.
    log_providers: list[LoggerProvider] = []
    loggers: dict[str, Any] = {}
    for service, namespace, host in _LOG_SOURCES:
        if service == "shopist-checkout":
            res = primary
        else:
            res = _resource(service=service, namespace=namespace, host=host)
        provider = LoggerProvider(resource=res)
        provider.add_log_record_processor(
            BatchLogRecordProcessor(OTLPLogExporter(endpoint=f"{base}/v1/logs"))
        )
        log_providers.append(provider)
        loggers[service] = provider.get_logger("datadog_otel_to_elastic", "1.0.0")
    # Keep a provider registered for any SDK helpers that look up the global.
    set_logger_provider(log_providers[0])

    tracer = trace.get_tracer(__name__, "1.0.0")
    rng = random.Random(7)
    env = str(primary.attributes.get("deployment.environment") or "staging")

    print(
        f"Datadog-style OTLP → {base} "
        f"(services={[s for s, _, _ in _LOG_SOURCES]}, every {interval}s)",
        flush=True,
    )

    n = 0
    while True:
        n += 1
        route, method = _ROUTES[n % len(_ROUTES)]
        status = rng.choice([200, 200, 201, 404, 500])
        duration_ms = round(rng.uniform(5, 180), 2)

        with tracer.start_as_current_span("dd.http.server.request") as span:
            span.set_attribute("http.request.method", method)
            span.set_attribute("http.route", route)
            span.set_attribute("http.url", route)
            span.set_attribute("http.response.status_code", status)
            span.set_attribute("net.host.name", primary_host)
            span.set_attribute("dd.service", primary_service)
            span.set_attribute("dd.env", env)
            span.set_attribute("dd.span_type", "web")
            span.set_attribute("k8s.namespace.name", primary_ns)
            span.set_attribute("workshop.sequence", n)

            checkout_counter.add(
                1,
                {
                    "env": env,
                    "service": primary_service,
                    "http.route": route,
                    "http.url": route,
                    "http.status_code": str(status),
                },
            )
            latency_hist.record(
                duration_ms,
                {
                    "http.route": route,
                    "http.url": route,
                    "http.request.method": method,
                },
            )

        # Primary checkout service: mix info/warn/error so status:* panels have rows.
        if status >= 500 or rng.random() < 0.22:
            level, body = "error", "checkout pipeline failure (workshop synthetic)"
        elif rng.random() < 0.28:
            level, body = "warn", "checkout pipeline degraded (workshop synthetic)"
        else:
            level, body = "info", "checkout pipeline event (Datadog-style log → OTLP → Elastic)"
        _emit_log(
            loggers["shopist-checkout"],
            level=level,
            body=body,
            route=route,
            method=method,
            status=status,
            duration_ms=duration_ms,
            service=primary_service,
            env=env,
        )

        # Extra source:* rows every few ticks so Security / Apache / Nginx panels light up.
        if n % 2 == 0:
            _emit_log(
                loggers["security"],
                level="error" if rng.random() < 0.4 else "warn",
                body="security proxy denied request (workshop synthetic)",
                route=route,
                method=method,
                status=403 if status < 500 else status,
                duration_ms=duration_ms,
                service="security",
                env=env,
            )
        if n % 3 == 0:
            _emit_log(
                loggers["apache"],
                level="error" if status >= 500 else "info",
                body="apache access/error (workshop synthetic)",
                route=route,
                method=method,
                status=status,
                duration_ms=duration_ms,
                service="apache",
                env=env,
            )
        if n % 2 == 1:
            _emit_log(
                loggers["nginx"],
                level="info" if status < 500 else "error",
                body="nginx access (workshop synthetic)",
                route=route,
                method=method,
                status=status,
                duration_ms=duration_ms,
                service="nginx",
                env=env,
            )

        time.sleep(interval)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        sys.exit(0)
