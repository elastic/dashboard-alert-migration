---
slug: lab-01-grafana-to-elastic
id: 7xffw36spadb
type: challenge
title: Lab 1 — Adopt PromQL metric views on Elastic
teaser: One command brings 20 PromQL/Grafana-shaped metric dashboards and alerts onto
  Kibana.
notes:
- type: text
  contents: |
    ## Metrics adoption — telemetry workflow

    **Audience:** existing Elastic customers. **Purpose:** adopt **metrics** on Observability Serverless.

    **Live workshop metrics** flow like this (same path customers use with OTLP → Elastic):

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

    Track **bootstrap** creates the project, wires **nginx → Kibana**, and starts **Alloy + emitters** when **mOTLP** and an **API key** are available.
- type: text
  contents: |
    ## This lab

    Accelerate metrics adoption: **20** Grafana-shaped / PromQL metric dashboards + **workshop alerts** → **[observability-migration-platform](https://github.com/elastic/observability-migration-platform)** **`grafana-migrate`** → Kibana on live **`metrics-*`**. Run **one command** in **Terminal** when the sandbox is ready.

    **Next slide:** mini-game while the sandbox finishes provisioning.
- type: text
  contents: |
    ## While you wait — **O11Y Survivors**

    [Open full screen](https://poulsbopete.github.io/Vampire-Clone/) if the embed is cramped. **Controls:** arrows or WASD, space, click to start.

    <div style="width:100%;max-width:100%;height:min(82vh,920px);min-height:520px;margin:0 auto;">
    <iframe src="https://poulsbopete.github.io/Vampire-Clone/" title="O11Y Survivors (Vampire Clone)" width="100%" height="100%" style="border:0;border-radius:10px;background:#0a0a0a;display:block;" allow="fullscreen" loading="lazy"></iframe>
    </div>
tabs:
- id: lypopaehfkah
  title: Terminal
  type: terminal
  hostname: es3-api
  workdir: /root
- id: blxkp1sz0kzz
  title: Elastic Serverless
  type: service
  hostname: es3-api
  path: /app/dashboards#/list?_g=(filters:!(),refreshInterval:(pause:!f,value:30000),time:(from:now-30m,to:now))
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

**Lab goal:** get trusted **metric** views onto Elastic quickly — Grafana JSON here is an adoption accelerator for PromQL-shaped boards you may already own.

When the sandbox is ready, open **Terminal** and run:

```bash
bash /root/workshop/scripts/migrate_grafana_dashboards_to_serverless.sh
```

That single script:

1. Starts (or reuses) the **OTLP** pipeline — Alloy → Elastic **mOTLP** (live **metrics**)
2. Runs **`grafana-migrate`** on **20** Grafana JSON files in **`assets/grafana/`** (`--native-promql`, uploads to Kibana)
3. Fetches workshop alerts from **`assets/grafana/alerts/`**
4. Publishes **Rules** to Kibana via **`publish_grafana_alert_drafts_kibana.py`** (drafts first)

The script loads **`KIBANA_URL`** and **`ES_API_KEY`** from **`~/.bashrc`** — no **`cd`** or **`source`** needed first. Use the **absolute path** above so it works even if your shell left **`/root/workshop`**.

## Verify

Open the **Elastic Serverless** tab:

- **Dashboards** — titles should match the Grafana exports; charts should populate from **`metrics-*`**
- **What & why** — each board opens with a markdown strip (**What this dashboard shows** / **Why it matters for metrics adoption**) migrated from the Grafana text panel
- **Metrics adoption — AI notes** — Agent Builder markdown for PromQL/Grafana-shaped metrics adoption (also appended to **Traffic overview** when attach succeeds)
- **Observability → Rules** — two workshop rules (imported **disabled**; enable in the UI to test)

Optional refresh: **Management → Workflows → Metrics adoption — AI dashboard notes** (manual run), or in **Terminal**:

```bash
source ~/.bashrc
# Sync latest workshop files if Workflows is still empty / scripts missing:
cd /root/workshop && ./scripts/sync_workshop_from_git.sh
python3 /root/workshop/scripts/deploy_workshop_workflows.py
python3 /root/workshop/scripts/ensure_ai_recommendation_panels.py --platform grafana --seed-now
```

Then open **Workflows** and run **Metrics adoption — AI dashboard notes**, or open **Metrics adoption — AI notes** under Dashboards.

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| Empty charts | `bash /root/workshop/scripts/check_workshop_otel_pipeline.sh` then `bash /root/workshop/scripts/start_workshop_otel.sh` — wait ~1 min |
| Still empty after migrate | `WORKSHOP_FORCE_OTEL_RESTART=1 bash /root/workshop/scripts/migrate_grafana_dashboards_to_serverless.sh` |
| Script not found | **Stop** → **Start** the track (wait for challenge to finish loading) |
| Stale workshop files | `cd /root/workshop && ./scripts/sync_workshop_from_git.sh` |

Optional pre-upload ES\|QL validation: `WORKSHOP_MIG_ES_VALIDATE=1 bash /root/workshop/scripts/migrate_grafana_dashboards_to_serverless.sh`

## Done

**Check** passes when **`build/mig-grafana/dashboards/yaml/`** (or legacy **`yaml/`**) has **20** `*.yaml` files, **`migration_report.json`** under **`build/mig-grafana/dashboards/`** (or **`build/mig-grafana/`**), and alert comparison output under **`build/mig-grafana/alerts/`** (or root) lists the workshop Grafana rules.
