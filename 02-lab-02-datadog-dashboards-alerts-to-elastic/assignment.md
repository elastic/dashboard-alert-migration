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
    ## Metrics path in this lab

    Same OTLP path as Lab 1:

    - Python OTLP emitters → **Grafana Alloy**
    - Alloy → **Elastic managed OTLP (mOTLP)**
    - Data lands in **`logs-*`**, **`metrics-*`**, **`traces-*`**
    - You work in **Kibana** (Elastic Serverless tab)
- type: text
  contents: |
    ## What this workshop covers

    1. **Metrics on Elastic** — same OTLP path as Lab 1
    2. **Prometheus / PromQL** — covered in Lab 1
    3. **Datadog metric IP** — **this lab:** dashboards + monitors → Kibana boards and alert drafts
    4. **Platform depth** — ES|QL + columnar metrics where Elastic wins
    5. **Agent Builder** — AI notes on live Datadog-migrated boards

    **This lab:** theme 3 (Datadog), plus platform depth and Agent Builder.
- type: text
  contents: |
    ## Why migrate dashboards instead of rebuilding?

    - **One operations UI** — stop pivoting between Datadog and Kibana during incidents
    - **Keep what you built** — Datadog monitors and metric boards are assets; migrate intent, don't redraw every chart
    - **Draft → approve** — alerts land as Kibana rule drafts before you enable them
    - **Less rebuild work** — bulk convert + API publish vs hand-recreating boards
- type: text
  contents: |
    ## This lab

    **Lab 2 — Datadog metric IP → Kibana** (dashboards + monitors as **drafts**).

    | Theme | What you prove |
    | --- | --- |
    | Metrics on Elastic | Same OTLP → **`metrics-*`** path as Lab 1 |
    | Datadog metric IP | **10** boards + **4** monitors via **`datadog-migrate`** |
    | Governance | Rules imported **disabled** — review queries before enable |
    | Agent Builder | **AI notes** on each board |

    Run **one command** in **Terminal** when the sandbox is ready.
- type: text
  contents: |
    ## While you wait — O11Y Survivors

    [Open full screen](https://poulsbopete.github.io/Vampire-Clone/) if the embed is cramped. **Controls:** arrows or WASD, space, click to start.

    <iframe src="https://poulsbopete.github.io/Vampire-Clone/" title="O11Y Survivors" width="100%" height="520" style="border:0;border-radius:8px;" allow="fullscreen" loading="lazy"></iframe>
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

# Lab 2 — Adopt Datadog metric views & monitors

Move **10 Datadog metric dashboards** and **4 monitors** onto Kibana with **one command** — same **OTLP → `metrics-*`** path as Lab 1. Monitors land as alert **drafts** (review before enable). **Agent Builder** AI notes guide what to validate next.

## What you'll prove

| Area | Outcome |
| --- | --- |
| **Metrics on Elastic** | Same OTLP path as Lab 1 — live `metrics-*` |
| **Datadog metric IP** | Dashboards + monitors via `datadog-migrate` |
| **Governance** | Rules imported **disabled** — review before enable |
| **Agent Builder** | AI notes on each live dashboard |

## How it works

| Step | What happens |
| --- | --- |
| **Source** | 10 boards + 4 monitors in `assets/datadog/` |
| **Migrate** | `datadog-migrate` checks OTLP, uploads dashboards, adds AI notes |
| **Result** | Kibana dashboards, rule drafts, and AI notes on live `metrics-*` |

## Run the migration

Open the **Terminal** tab and run:

```bash
bash /root/workshop/scripts/migrate_datadog_dashboards_to_serverless.sh
```

Expect **a few minutes**. The script:

1. Confirms **OTLP** → **`metrics-*`**
2. Runs **`datadog-migrate --upload`**
3. Publishes **4** monitor drafts (**disabled** — review before enable)
4. Seeds **Agent Builder AI notes** on each board

## Verify

Open the **Elastic Serverless** tab:

1. **Dashboards** — open e.g. **Service overview**; charts use live **`metrics-*`**
2. Scroll to the **bottom** for **AI notes** — what to validate next
3. **Observability → Rules** — **four** workshop rules (**disabled** until you enable them)

## Optional — integrations boards

Migrate **integrations-core** boards (NGINX, Postgres, RabbitMQ, …) and start sample OTLP metrics:

```bash
bash /root/workshop/scripts/migrate_datadog_integrations_to_serverless.sh
```

Wait ~1 minute, then open e.g. **NGINX - Overview** / **Postgres - Metrics**.

## Done

**Check** passes when **`build/mig-datadog/dashboards/yaml/`** has **10** `*.yaml` files and **`build/elastic-alerts/`** has **4** `monitor-*-elastic.json` files.
