# Workshop invite — Metrics adoption on Elastic Observability

**Audience:** Existing Elastic customers (logs/traces/security already on Elastic, or expanding Observability coverage).  
**Purpose:** Accelerate **metrics adoption** on Elastic Observability — Prometheus / PromQL continuity, OTLP ingest, dashboards, and alerting on live `metrics-*`.  
**Format:** Guided Instruqt sandbox (~2–3 hours). No local install required.

---

## Suggested invite (email / calendar)

**Subject:** Workshop invite — Metrics adoption on Elastic Observability (Prometheus + OTLP)

Hi team,

You are invited to a hands-on workshop for **existing Elastic customers** focused on **Elastic’s metrics push** — make Observability Serverless the system of record for metrics, including **Prometheus / PromQL** workflows teams already know.

Many accounts already run logs and traces on Elastic while metrics stay in Prometheus, Grafana, Datadog, or parallel TSDB stacks. This session shows how to **standardize metrics on Elastic**: OpenTelemetry → managed OTLP, native PromQL-oriented boards on live series, reviewable Kibana dashboards and alert drafts, plus Agent Builder notes that help teams validate adoption — not a greenfield redraw of every chart.

**What you will do**
1. Work in an Elastic Observability Serverless sandbox with live OTLP metrics (`metrics-*`).
2. Land **PromQL / Prometheus-shaped** metric dashboards on Kibana (Grafana exports → Lens / ES|QL, with PromQL intent preserved where the path supports it).
3. Optionally accelerate with **Datadog-shaped** metric dashboards and monitors as Kibana dashboards and alert **drafts**.
4. See **Agent Builder** metrics-adoption notes on live boards, and validate against real series — not screenshots.

**Who should attend**
Platform / SRE / observability owners at accounts already on Elastic who want **Prometheus-class metrics** on the same platform as logs and traces — fewer silos, columnar query performance, and a repeatable adoption path.

**What this is not**
Not a net-new logo pitch deck, and not “build every Lens panel by hand.” Grafana / Datadog assets are **metric IP accelerators**. The north star is **metrics on Elastic**, with Prometheus / PromQL as a first-class adoption story.

**Lab link:** https://play.instruqt.com/elastic/invite/fmt96ftdm41w  

Please join with a laptop and a modern browser. Sandbox provisioning can take a few minutes at the start of each lab.

—
Elastic Observability workshop team

---

## Short blurb (Slack / Teams)

**Metrics adoption workshop** — Elastic’s metrics push for existing customers: OTLP → `metrics-*`, **Prometheus / PromQL** boards onto Kibana, Datadog metric IP as an accelerator, Agent Builder notes, alert drafts. Invite: https://play.instruqt.com/elastic/invite/fmt96ftdm41w

---

## Follow-up email bullets (post-session)

Use after the live workshop (Amena-style follow-up):

1. **Metrics on Elastic** — OTLP ingest and live `metrics-*` as the path to standardize metrics with logs/traces  
2. **Prometheus / PromQL continuity** — bring PromQL-oriented dashboards onto Kibana quickly (reviewable automation, not a full redraw)  
3. **Best-in-class metrics platform** — native PromQL where it fits, ES|QL + **columnar metrics engine** where Elastic wins on query/storage  
4. **AI-assisted adoption** — Agent Builder notes on live dashboards (what to validate next)  
5. **Governance** — monitors → Kibana rule drafts (disabled until you approve)  
6. Live Q&A / session recording (as available)

---

## Agenda (facilitator run-of-show)

| Block | Time | Focus |
| --- | --- | --- |
| Open + framing | 10–15 min | **Metrics push**: Prometheus + OTLP on Elastic; audience = existing customers; Grafana/Datadog = accelerators |
| Metrics story | 5–10 min | Columnar engine / PromQL + ES|QL (slides); why one metrics plane |
| Lab 1 | ~45–60 min | **Prometheus / PromQL** boards → Kibana on live OTLP (+ Agent Builder notes) |
| Break | 5–10 min |
| Lab 2 | ~45–60 min | Datadog-shaped metric dashboards + monitors → Kibana drafts (optional integrations) |
| Debrief | 15–20 min | 30-day checklist: Prometheus/OTLP coverage, 3 canonical boards, 2 rules, Agent Builder refresh |

Optional extensions (facilitator): integrations-core boards + sample metrics, Cursor + Agent Skills / dashboards-as-code aside, Workflows manual run for AI notes, MCP demo for Elastic-internal audiences only.
