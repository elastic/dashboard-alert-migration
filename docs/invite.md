# Workshop invite — Metrics adoption on Elastic Observability

**Audience:** Existing Elastic customers (logs/traces/security already on Elastic, or expanding Observability coverage).  
**Purpose:** Accelerate **metrics adoption** on Elastic Observability Serverless — ingest, dashboards, and alerting on live `metrics-*` data.  
**Format:** Guided Instruqt sandbox (~2–3 hours). No local install required.

---

## Suggested invite (email / calendar)

**Subject:** Workshop invite — Metrics adoption on Elastic Observability

Hi team,

You are invited to a hands-on workshop for **existing Elastic customers** focused on **metrics adoption**.

Many teams already run logs and traces on Elastic and still keep metrics (and metric dashboards) in Grafana, Datadog, or parallel Prometheus stacks. This session shows how to **standardize metrics on Elastic** — OpenTelemetry ingest into managed OTLP, reviewable Kibana dashboards and rules on live series, and a practical path to bring forward the metric views you already trust.

**What you will do**
1. Work in an Elastic Observability Serverless sandbox with live OTLP metrics.
2. Adopt PromQL-oriented metric dashboards onto Kibana (Grafana-shaped exports → Lens / ES|QL).
3. Adopt Datadog-shaped metric dashboards and monitors as Kibana dashboards and alert drafts.
4. Validate charts and rules against real `metrics-*` data — not screenshots.

**Who should attend**
Platform / SRE / observability owners at accounts already on Elastic who want broader **metrics** coverage, fewer silos, and a repeatable adoption path.

**What this is not**
Not a net-new customer pitch deck, and not a greenfield “build every chart by hand” lab. Grafana and Datadog assets in the labs are **adoption accelerators** (metric IP you may already own), not the primary audience story.

**Lab link:** https://play.instruqt.com/elastic/invite/fmt96ftdm41w  

Please join with a laptop and a modern browser. Sandbox provisioning can take a few minutes at the start of each lab.

—
Elastic Observability workshop team

---

## Short blurb (Slack / Teams)

**Metrics adoption workshop (existing Elastic customers)** — Live Serverless sandbox: OTLP metrics → Kibana dashboards & alert drafts, including bringing PromQL / Datadog metric views onto Elastic. Invite: https://play.instruqt.com/elastic/invite/fmt96ftdm41w

---

## Agenda (facilitator run-of-show)

| Block | Time | Focus |
| --- | --- | --- |
| Open + framing | 10–15 min | Purpose = metrics adoption; audience = existing Elastic customers; Grafana/Datadog = assets to accelerate adoption |
| Lab 1 | ~45–60 min | PromQL / Grafana-shaped metric dashboards → Kibana on live OTLP |
| Break | 5–10 min | |
| Lab 2 | ~45–60 min | Datadog-shaped metric dashboards + monitors → Kibana rules (drafts first) |
| Debrief | 15–20 min | First 30 days: ingest coverage, 3 canonical metric boards, 2 alert rules, governance |

Optional extensions (facilitator): dynamic ES|QL overview dashboard, Datadog integrations-core boards, Cursor + Agent Skills for refinement, **Agent Builder AI notes** on **Metrics adoption — AI notes** (Workflows → manual run).
