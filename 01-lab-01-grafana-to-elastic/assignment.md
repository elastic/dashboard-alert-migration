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
    ## Agenda — five adoption themes

    <div style="display:grid;grid-template-columns:1fr;gap:10px;margin:12px 0;">
    <div style="border-left:4px solid #60a5fa;padding:10px 14px;background:#0f172a;border-radius:0 10px 10px 0;">
    <b style="color:#93c5fd;">1. Metrics on Elastic</b><br/>
    <span style="color:#cbd5e1;font-size:0.9rem;">OTLP → managed OTLP → live <code>metrics-*</code> next to <code>logs-*</code> / <code>traces-*</code> — one Observability plane.</span>
    </div>
    <div style="border-left:4px solid #34d399;padding:10px 14px;background:#0f172a;border-radius:0 10px 10px 0;">
    <b style="color:#6ee7b7;">2. Prometheus / PromQL</b><br/>
    <span style="color:#cbd5e1;font-size:0.9rem;">Bring PromQL-oriented (Grafana) dashboards onto Kibana — migrate intent, don’t redraw every panel.</span>
    </div>
    <div style="border-left:4px solid #fbbf24;padding:10px 14px;background:#0f172a;border-radius:0 10px 10px 0;">
    <b style="color:#fcd34d;">3. Datadog metric IP</b><br/>
    <span style="color:#cbd5e1;font-size:0.9rem;">Dashboards + monitors → Kibana boards and <b>alert drafts</b> (review before enable). Lab 2.</span>
    </div>
    <div style="border-left:4px solid #a78bfa;padding:10px 14px;background:#0f172a;border-radius:0 10px 10px 0;">
    <b style="color:#c4b5fd;">4. Platform depth</b><br/>
    <span style="color:#cbd5e1;font-size:0.9rem;">PromQL where you already live; <b>ES|QL + columnar metrics</b> where Elastic wins on query &amp; storage.</span>
    </div>
    <div style="border-left:4px solid #f472b6;padding:10px 14px;background:#0f172a;border-radius:0 10px 10px 0;">
    <b style="color:#f9a8d4;">5. Agent Builder</b><br/>
    <span style="color:#cbd5e1;font-size:0.9rem;">AI notes on <b>live</b> dashboards — what to validate next after migrate.</span>
    </div>
    </div>

    **This lab (Lab 1)** emphasizes themes **1, 2, 4, and 5**. Lab 2 adds **Datadog metric IP** (theme 3).
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

    **Lab 1 — Prometheus / PromQL → Kibana** on live OTLP metrics.

    | Theme | What you prove |
    | --- | --- |
    | Metrics on Elastic | Charts query live **`metrics-*`** (same project as logs/traces) |
    | PromQL / Grafana | **20** boards via **`grafana-migrate`** — no hand-redraw |
    | Platform depth | Migrated panels land as Lens / **ES|QL** on Elastic’s columnar metrics store |
    | Agent Builder | **AI notes** at the bottom of each board (`workshop-ai-rec-grafana`) |

    Run **one command** in **Terminal** when the sandbox is ready.

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

**Lab goal:** prove **metrics on Elastic** with **Prometheus / PromQL** continuity — move **20** Grafana-shaped metric dashboards **+ alert drafts** onto Kibana with **one command** (`grafana-migrate`), not hand-rebuilding panels. Charts run on live OTLP **`metrics-*`**; **Agent Builder** AI notes tell you what to validate next.

<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(100px,1fr));gap:8px;margin:12px 0;">
<div style="border:1px solid #cbd5e1;border-radius:8px;padding:8px;background:#f8fafc;font-size:0.75rem;text-align:center;"><b>OTLP → metrics-*</b><br/>alongside logs/traces</div>
<div style="border:1px solid #bbf7d0;border-radius:8px;padding:8px;background:#f0fdf4;font-size:0.75rem;text-align:center;"><b>PromQL / Grafana</b><br/>migrate, don’t redraw</div>
<div style="border:1px solid #ddd6fe;border-radius:8px;padding:8px;background:#f5f3ff;font-size:0.75rem;text-align:center;"><b>ES|QL + columnar</b><br/>where Elastic wins</div>
<div style="border:1px solid #fbcfe8;border-radius:8px;padding:8px;background:#fdf2f8;font-size:0.75rem;text-align:center;"><b>Agent Builder</b><br/>AI notes on live boards</div>
</div>

<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:10px;margin:14px 0;align-items:stretch;">
<div style="border:1px solid #cbd5e1;border-radius:10px;padding:12px;background:#f8fafc;text-align:center;">
<div style="font-size:0.7rem;text-transform:uppercase;letter-spacing:0.04em;color:#64748b;">Source</div>
<div style="font-size:1.1rem;font-weight:700;margin-top:4px;color:#0f172a;">20 boards</div>
<div style="font-size:0.8rem;color:#475569;margin-top:2px;">+ alert drafts<br/><code>assets/grafana/</code></div>
</div>
<div style="border:1px solid #93c5fd;border-radius:10px;padding:12px;background:#eff6ff;text-align:center;">
<div style="font-size:0.7rem;text-transform:uppercase;letter-spacing:0.04em;color:#64748b;">Migrate</div>
<div style="font-size:1.1rem;font-weight:700;margin-top:4px;color:#1d4ed8;">grafana-migrate</div>
<div style="font-size:0.8rem;color:#475569;margin-top:2px;">OTLP check → upload → AI notes</div>
</div>
<div style="border:1px solid #86efac;border-radius:10px;padding:12px;background:#f0fdf4;text-align:center;">
<div style="font-size:0.7rem;text-transform:uppercase;letter-spacing:0.04em;color:#64748b;">Result</div>
<div style="font-size:1.1rem;font-weight:700;margin-top:4px;color:#166534;">Kibana</div>
<div style="font-size:0.8rem;color:#475569;margin-top:2px;">Dashboards · rules · AI notes<br/>on live <code>metrics-*</code></div>
</div>
</div>

```bash
bash /root/workshop/scripts/migrate_grafana_dashboards_to_serverless.sh
```

Expect ~1–2 minutes. The script confirms **OTLP** is flowing into **`metrics-*`**, runs **`grafana-migrate --upload`** (PromQL/Grafana → Kibana), publishes workshop alert drafts (**disabled** — review before enable), and seeds **Agent Builder AI notes** on each board.

## Verify

Open the **Elastic Serverless** tab:

1. **Dashboards** — e.g. **Traffic overview**; charts use live **`metrics-*`** (OTLP path from the slides)
2. Open a panel / Explore — note **ES|QL** / Lens on Elastic metrics (platform depth vs redrawing Grafana)
3. Scroll to the **bottom** for **AI notes** (`workshop-ai-rec-grafana`) — what to validate next
4. **Observability → Rules** — **two** workshop rules (**disabled** until you enable them)

## Done

**Check** passes when **`build/mig-grafana/dashboards/yaml/`** has **20** `*.yaml` files and alert comparison output lists the workshop Grafana rules.
