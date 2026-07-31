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

**Lab goal:** adopt Datadog-shaped **metric** boards and monitors onto Elastic with governance (rules imported **disabled** until you review).

When the sandbox is ready, open **Terminal** and run:

```bash
bash /root/workshop/scripts/migrate_datadog_dashboards_to_serverless.sh
```

That single script:

1. Starts (or reuses) the **OTLP** pipeline — Alloy → Elastic **mOTLP** (live **metrics**)
2. Runs **`datadog-migrate`** on **10** Datadog JSON files in **`assets/datadog/dashboards/`** (`--field-profile otel`, uploads to Kibana)
3. Converts **4** monitor JSON files under **`assets/datadog/`** and publishes **Rules** via **`publish_datadog_alert_drafts_kibana.py`** (imported **disabled**)

The script loads **`KIBANA_URL`** and **`ES_API_KEY`** from **`~/.bashrc`** — no **`cd`** or **`source`** needed first. Use the **absolute path** above so it works even if your shell left **`/root/workshop`**.

## Verify

Open the **Elastic Serverless** tab:

- **Dashboards** — titles from the Datadog exports; charts should populate from **`metrics-*`**
- **AI notes** — each board gets a bottom **Agent Builder** markdown strip (`workshop-ai-rec-datadog`) updated by the **Metrics adoption — AI dashboard notes** workflow (same dbmonitoring pattern)
- **Metrics adoption — AI notes** — Agent Builder markdown for Datadog-shaped metrics adoption (also on **Service overview** when attach succeeds)
- **Observability → Rules** — four workshop rules (imported **disabled**; enable in the UI to test)

Optional refresh: **Management → Workflows → Metrics adoption — AI dashboard notes**, or in **Terminal**:

```bash
source ~/.bashrc
cd /root/workshop && ./scripts/sync_workshop_from_git.sh
python3 /root/workshop/scripts/deploy_workshop_workflows.py
python3 /root/workshop/scripts/ensure_ai_recommendation_panels.py --platform datadog --seed-now
```

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| Empty charts | `bash /root/workshop/scripts/check_workshop_otel_pipeline.sh` then `bash /root/workshop/scripts/start_workshop_otel.sh` — wait ~1 min |
| Still empty after migrate | Re-run migrate after OTLP is healthy; `cd /root/workshop && ./scripts/sync_workshop_from_git.sh` if files are stale |
| Script not found | **Stop** → **Start** the track (wait for challenge to finish loading) |
| `latency_p95` compile warning | Other dashboards still upload; refresh workshop files and re-run migrate |

Optional pre-upload ES\|QL validation: `WORKSHOP_MIG_ES_VALIDATE=1 bash /root/workshop/scripts/migrate_datadog_dashboards_to_serverless.sh`

## Optional — integration dashboards

Migrate **eight** official Agent integration dashboards from [DataDog/integrations-core](https://github.com/DataDog/integrations-core) (see **`assets/datadog/integrations-core/ATTRIBUTION.md`**):

```bash
bash /root/workshop/scripts/migrate_datadog_integrations_to_serverless.sh
```

These use integration metric namespaces (`nginx.*`, `postgresql.*`, …), not the OTLP workshop fleet — expect many panels to need data mapping after migration.

## Done

**Check** passes when **`build/mig-datadog/dashboards/yaml/`** (or legacy **`yaml/`**) has **10** `*.yaml` files, **`migration_report.json`** under **`build/mig-datadog/dashboards/`** (or root), and **`build/elastic-alerts/`** has **4** `monitor-*-elastic.json` files.
