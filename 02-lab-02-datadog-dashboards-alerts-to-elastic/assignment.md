---
slug: lab-02-datadog-dashboards-alerts-to-elastic
id: berxl591tjk4
type: challenge
title: Lab 2 — Adopt Datadog metric views & monitors
teaser: One command brings 10 Datadog-shaped metric dashboards and four monitors onto
  Kibana.
notes:
- type: text
  contents: |
    ## Metrics adoption — telemetry workflow

    **Audience:** existing Elastic customers. **Purpose:** adopt **metrics** (same OTLP path as Lab 1 — Alloy → Elastic **mOTLP**):

    ```
                      ┌──────────────────────────────┐
                      │  Python OTLP (fleet, DD OTLP) │
                      └──────────────┬───────────────┘
                                     │ OTLP
    Prometheus :12345 ──► Grafana Alloy (:4317 / :4318)
                                     │
                          OTLP/HTTP + Authorization
                                     ▼
                        Elastic managed OTLP (mOTLP)
                                     ▼
                        Observability Serverless project
                                     ▼
                    logs-*    metrics-*    traces-*
                                     ▼
                           Kibana (proxied :8080)
    ```
- type: text
  contents: |
    ## Why migrate Grafana & Datadog dashboards and alerts?

    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px;margin:16px 0;">
    <div style="border:1px solid #334155;border-radius:12px;padding:14px;background:#0f172a;">
    <div style="font-size:1.75rem;font-weight:800;color:#60a5fa;">1 plane</div>
    <div style="font-size:0.85rem;margin-top:6px;color:#e2e8f0;"><b>One operations UI</b><br/>Stop pivoting Grafana/Datadog ↔ Kibana mid-incident.</div>
    </div>
    <div style="border:1px solid #334155;border-radius:12px;padding:14px;background:#0f172a;">
    <div style="font-size:1.75rem;font-weight:800;color:#60a5fa;">IP</div>
    <div style="font-size:0.85rem;margin-top:6px;color:#e2e8f0;"><b>Keep what you built</b><br/>PromQL panels & monitors are assets — migrate intent, don’t redraw every chart.</div>
    </div>
    <div style="border:1px solid #334155;border-radius:12px;padding:14px;background:#0f172a;">
    <div style="font-size:1.75rem;font-weight:800;color:#60a5fa;">Gov</div>
    <div style="font-size:0.85rem;margin-top:6px;color:#e2e8f0;"><b>Draft → approve</b><br/>Alerts land as Kibana rule drafts before enforcement.</div>
    </div>
    <div style="border:1px solid #334155;border-radius:12px;padding:14px;background:#0f172a;">
    <div style="font-size:1.75rem;font-weight:800;color:#60a5fa;">4–10×</div>
    <div style="font-size:0.85rem;margin-top:6px;color:#e2e8f0;"><b>Less rebuild work</b><br/>Bulk convert + API publish vs hand-recreating boards.</div>
    </div>
    </div>
- type: text
  contents: |
    ## Elastic Metrics — columnar engine

    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px;margin:16px 0;">
    <div style="border:1px solid #334155;border-radius:12px;padding:14px;background:#0f172a;text-align:center;">
    <div style="font-size:2rem;font-weight:800;color:#34d399;">30×</div>
    <div style="font-size:0.8rem;color:#cbd5e1;margin-top:4px;">Faster queries vs Prometheus*</div>
    </div>
    <div style="border:1px solid #334155;border-radius:12px;padding:14px;background:#0f172a;text-align:center;">
    <div style="font-size:2rem;font-weight:800;color:#34d399;">3.75 B</div>
    <div style="font-size:0.8rem;color:#cbd5e1;margin-top:4px;">Per OTel data point</div>
    </div>
    <div style="border:1px solid #334155;border-radius:12px;padding:14px;background:#0f172a;text-align:center;">
    <div style="font-size:2rem;font-weight:800;color:#34d399;">2.5×</div>
    <div style="font-size:0.8rem;color:#cbd5e1;margin-top:4px;">Better storage efficiency*</div>
    </div>
    <div style="border:1px solid #334155;border-radius:12px;padding:14px;background:#0f172a;text-align:center;">
    <div style="font-size:2rem;font-weight:800;color:#34d399;">ES|QL</div>
    <div style="font-size:0.8rem;color:#cbd5e1;margin-top:4px;">Metrics + logs + traces</div>
    </div>
    </div>

    *Competitive benchmarks vs Prometheus / Mimir / ClickHouse — [Elasticsearch Labs](https://www.elastic.co/search-labs/blog/elasticsearch-columnar-metrics-engine-30x-faster-prometheus).

    **Next slide:** what you will run in this lab.
- type: text
  contents: |
    ## This lab

    Accelerate metrics adoption: **10** Datadog-shaped metric dashboards (**`datadog-migrate`**) + **4** monitors → Kibana dashboards and alert **drafts**. Run **one command** in **Terminal** when the sandbox is ready.

    **Live OTLP:** **`./scripts/send_datadog_otel.sh`** (or **`tools/datadog_otel_to_elastic.py`**) — same pipeline as Lab 1.

    **Next slide:** mini-game while Lab 2 environments load.
- type: text
  contents: |
    ## While you wait — **O11Y Survivors**

    [Open full screen](https://poulsbopete.github.io/Vampire-Clone/) if the embed is cramped. **Controls:** arrows or WASD, space, click to start.

    <div style="width:100%;max-width:100%;height:min(82vh,920px);min-height:520px;margin:0 auto;">
    <iframe src="https://poulsbopete.github.io/Vampire-Clone/" title="O11Y Survivors (Vampire Clone)" width="100%" height="100%" style="border:0;border-radius:10px;background:#0a0a0a;display:block;" allow="fullscreen" loading="lazy"></iframe>
    </div>
tabs:
- id: fsizfoyfjtag
  title: Terminal
  type: terminal
  hostname: es3-api
  workdir: /root
- id: v9ea7agmywny
  title: Elastic Serverless
  type: service
  hostname: es3-api
  path: /
  port: 8080
  custom_request_headers:
  - key: Content-Security-Policy
    value: 'script-src ''self'' https://kibana.estccdn.com; worker-src blob: ''self'';
      style-src ''unsafe-inline'' ''self'' https://kibana.estccdn.com; style-src-elem
      ''unsafe-inline'' ''self'' https://kibana.estccdn.com'
  custom_response_headers:
  - key: Content-Security-Policy
    value: 'script-src ''self'' https://kibana.estccdn.com; worker-src blob: ''self'';
      style-src ''unsafe-inline'' ''self'' https://kibana.estccdn.com; style-src-elem
      ''unsafe-inline'' ''self'' https://kibana.estccdn.com'
difficulty: ""
enhanced_loading: null
---

**Lab goal:** move **10** Datadog-shaped metric dashboards **+ 4 monitors** onto Elastic with **one command** — Elastic’s published migration path (`datadog-migrate`), as Kibana dashboards and alert **drafts**.

<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:10px;margin:14px 0;align-items:stretch;">
<div style="border:1px solid #cbd5e1;border-radius:10px;padding:12px;background:#f8fafc;text-align:center;">
<div style="font-size:0.7rem;text-transform:uppercase;letter-spacing:0.04em;color:#64748b;">Source</div>
<div style="font-size:1.1rem;font-weight:700;margin-top:4px;color:#0f172a;">10 boards</div>
<div style="font-size:0.8rem;color:#475569;margin-top:2px;">+ 4 monitors<br/><code>assets/datadog/</code></div>
</div>
<div style="border:1px solid #93c5fd;border-radius:10px;padding:12px;background:#eff6ff;text-align:center;">
<div style="font-size:0.7rem;text-transform:uppercase;letter-spacing:0.04em;color:#64748b;">Migrate</div>
<div style="font-size:1.1rem;font-weight:700;margin-top:4px;color:#1d4ed8;">datadog-migrate</div>
<div style="font-size:0.8rem;color:#475569;margin-top:2px;">OTLP check → upload → AI notes</div>
</div>
<div style="border:1px solid #86efac;border-radius:10px;padding:12px;background:#f0fdf4;text-align:center;">
<div style="font-size:0.7rem;text-transform:uppercase;letter-spacing:0.04em;color:#64748b;">Result</div>
<div style="font-size:1.1rem;font-weight:700;margin-top:4px;color:#166534;">Kibana</div>
<div style="font-size:0.8rem;color:#475569;margin-top:2px;">Dashboards · rules · AI notes<br/>on live <code>metrics-*</code></div>
</div>
</div>

```bash
bash /root/workshop/scripts/migrate_datadog_dashboards_to_serverless.sh
```

Expect a few minutes. The script confirms OTLP is flowing, runs **`datadog-migrate --upload`**, publishes **4** monitor drafts (**disabled**), and seeds **AI notes** on each board.

## Verify

Open the **Elastic Serverless** tab:

1. **Dashboards** — e.g. **Service overview**; charts use **`metrics-*`**
2. Scroll to the **bottom** for **AI notes** (`workshop-ai-rec-datadog`)
3. **Observability → Rules** — **four** workshop rules (**disabled** until you enable them)

## Optional

Migrate **integrations-core** boards (NGINX, Postgres, RabbitMQ, …) and start sample OTLP metrics:

```bash
bash /root/workshop/scripts/migrate_datadog_integrations_to_serverless.sh
```

Wait ~1 minute, then open e.g. **NGINX - Overview** / **Postgres - Metrics**. Sample-only restart:

```bash
bash /root/workshop/scripts/start_workshop_integrations_otel.sh
```

## Done

**Check** passes when **`build/mig-datadog/dashboards/yaml/`** has **10** `*.yaml` files and **`build/elastic-alerts/`** has **4** `monitor-*-elastic.json` files.
