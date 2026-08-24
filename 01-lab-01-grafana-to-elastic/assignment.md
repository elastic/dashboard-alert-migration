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
    ## Metrics path in this lab

    OpenTelemetry metrics flow into Elastic the same way you would in production:

    - Python OTLP emitters and Prometheus scrape → **Grafana Alloy**
    - Alloy → **Elastic managed OTLP (mOTLP)**
    - Data lands in **`logs-*`**, **`metrics-*`**, **`traces-*`**
    - You work in **Kibana** (Elastic Serverless tab)

    Track bootstrap creates the project, starts Alloy + emitters, and proxies Kibana on port 8080.
- type: text
  contents: |
    ## What this workshop covers

    1. **Metrics on Elastic** — OTLP → live `metrics-*` next to logs and traces
    2. **Prometheus / PromQL** — bring Grafana-shaped boards onto Kibana without redrawing every panel
    3. **Datadog metric IP** — Lab 2 (dashboards + monitors as drafts)
    4. **Platform depth** — PromQL where you already live; ES|QL + columnar metrics where Elastic wins
    5. **Agent Builder** — AI notes on live dashboards tell you what to validate next

    **This lab:** themes 1, 2, 4, and 5.
- type: text
  contents: |
    ## Why migrate dashboards instead of rebuilding?

    - **One operations UI** — stop pivoting between Grafana and Kibana during incidents
    - **Keep what you built** — PromQL panels and monitors are assets; migrate intent, don't redraw every chart
    - **Draft → approve** — alerts land as Kibana rule drafts before you enable them
    - **Less rebuild work** — bulk convert + API publish vs hand-recreating boards
- type: text
  contents: |
    ## This lab

    **Lab 1 — Prometheus / PromQL → Kibana** on live OTLP metrics.

    | Theme | What you prove |
    | --- | --- |
    | Metrics on Elastic | Charts query live **`metrics-*`** (same project as logs/traces) |
    | PromQL / Grafana | **20** boards via **`grafana-migrate`** — no hand-redraw |
    | Platform depth | Migrated panels land as Lens / **ES|QL** on Elastic's columnar metrics store |
    | Agent Builder | **AI notes** at the bottom of each board |

    Run **one command** in **Terminal** when the sandbox is ready.
- type: text
  contents: |
    ## While you wait — O11Y Survivors

    [Open full screen](https://poulsbopete.github.io/Vampire-Clone/) if the embed is cramped. **Controls:** arrows or WASD, space, click to start.

    <iframe src="https://poulsbopete.github.io/Vampire-Clone/" title="O11Y Survivors" width="100%" height="520" style="border:0;border-radius:8px;" allow="fullscreen" loading="lazy"></iframe>
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

# Lab 1 — Adopt PromQL metric views on Elastic

Move **20 Grafana-shaped metric dashboards** and **alert drafts** onto Kibana with **one command** — charts run on live OTLP **`metrics-*`**, not hand-redrawn panels. **Agent Builder** AI notes at the bottom of each board tell you what to validate next.

## What you'll prove

| Area | Outcome |
| --- | --- |
| **Metrics on Elastic** | OTLP flows into `metrics-*` alongside logs and traces |
| **PromQL / Grafana** | Migrate existing boards with `grafana-migrate` — don't redraw |
| **Platform depth** | ES\|QL and columnar metrics on Elastic's metrics store |
| **Agent Builder** | AI notes on each live dashboard |

## How it works

| Step | What happens |
| --- | --- |
| **Source** | 20 boards + alert drafts in `assets/grafana/` |
| **Migrate** | `grafana-migrate` checks OTLP, uploads dashboards, adds AI notes |
| **Result** | Kibana dashboards, rule drafts, and AI notes on live `metrics-*` |

## Run the migration

Open the **Terminal** tab and run:

```bash
bash /root/workshop/scripts/migrate_grafana_dashboards_to_serverless.sh
```

Expect **~1–2 minutes**. The script:

1. Confirms **OTLP** is flowing into **`metrics-*`**
2. Runs **`grafana-migrate --upload`** (PromQL/Grafana → Kibana)
3. Publishes workshop alert drafts (**disabled** — review before enable)
4. Seeds **Agent Builder AI notes** on each board

## Verify

Open the **Elastic Serverless** tab:

1. **Dashboards** — open e.g. **Traffic overview**; charts use live **`metrics-*`**
2. Open a panel — note **ES|QL** / Lens on Elastic metrics
3. Scroll to the **bottom** for **AI notes** — what to validate next
4. **Observability → Rules** — **two** workshop rules (**disabled** until you enable them)

## Done

**Check** passes when **`build/mig-grafana/dashboards/yaml/`** has **20** `*.yaml` files and alert comparison output lists the workshop Grafana rules.
