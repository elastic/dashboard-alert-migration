# Workshop design — Metrics adoption for existing customers

## Intent

| | |
| --- | --- |
| **Purpose** | Metrics adoption on Elastic Observability — aligned with Elastic’s **metrics push** (Prometheus / PromQL, OTLP, columnar query) |
| **Audience** | Existing Elastic customers |
| **Outcome** | Teams leave able to ingest metrics via OTLP, run **Prometheus-class** operational views on `metrics-*`, land dashboards/alerts without a full redraw, and use Agent Builder notes to guide adoption |

Earlier “Grafana customer / Datadog customer migration” framing was **placeholder positioning**. **Prometheus / PromQL** is a first-class story. Grafana and Datadog remain in the hands-on path as **common sources of metric dashboard IP**, not as the primary competitive narrative.

## Why this design (vs a greenfield metrics lab)

For accounts already on Elastic, the adoption bottleneck is rarely “can Kibana draw a chart?” It is:

1. **Ingest confidence** — metrics land in `metrics-*` with dimensions teams recognize (OTLP / Prometheus-shaped)  
2. **Prometheus continuity** — PromQL intent and existing boards accelerate adoption instead of a blank Lens canvas  
3. **Time-to-value** — replace months of hand-rebuild with reviewable automation  
4. **Platform depth** — ES|QL + columnar metrics where Elastic differentiates; PromQL where teams already live  
5. **Governance** — dashboards and alerts as drafts → human approve → enforce  

This track already exercises these with a production Instruqt + Serverless + mOTLP spine. Reframing keeps that engine and changes the **story, invite, and facilitator language**.

## Lab map (learner-facing)

| Lab | Adoption job | Mechanic (unchanged) |
| --- | --- | --- |
| **Lab 1** | Adopt **Prometheus / PromQL**-oriented metric views onto Elastic | `migrate_grafana_dashboards_to_serverless.sh` (20 boards + alert drafts) |
| **Lab 2** | Adopt Datadog-oriented metric views + monitors (accelerator) | `migrate_datadog_dashboards_to_serverless.sh` (10 boards + 4 rules) |

Both labs validate on **live OTLP** (`metrics-*` / `logs-*` / `traces-*`), the same path customers use with Elastic managed OTLP.

## Invite principles

- Lead with **metrics adoption**, **Prometheus / PromQL**, and **existing Elastic customers**  
- Position Grafana/Datadog as **accelerators** (metric IP you may already have)  
- Call out **columnar metrics** + Agent Builder in framing and follow-up email  
- Do not market the session as “leave Grafana/Datadog day-one” unless the account asks for that narrative  
- Copy lives in [`docs/invite.md`](invite.md); Instruqt CTA remains the shared invite URL in slides

## Agent Builder AI notes (dbmonitoring pattern)

| Piece | Path / name |
| --- | --- |
| Kibana Workflow | `workflows/metrics-adoption-recommendations.yaml` |
| Deploy | `scripts/deploy_workshop_workflows.py` |
| Panels + seed | `scripts/ensure_ai_recommendation_panels.py` (`--seed-now`) |
| Index | `metrics-adoption-recommendations` |
| Markdown SOs | `workshop-ai-rec-grafana`, `workshop-ai-rec-datadog` |
| Dashboard | **Metrics adoption — AI notes** (+ attach to Traffic overview / Service overview) |

Skip with `WORKSHOP_SKIP_AI_NOTES=1` on migrate scripts.

## Out of scope (for now)

- Replacing Lab 1/2 scripts with a from-scratch Lens-only curriculum  
- A third required Instruqt challenge (dynamic dashboard / SLO) — keep as facilitator optional  
- Renaming the Instruqt track **slug** (`elastic-serverless-migration-lab`) — title/teaser/tags update; slug change needs Instruqt ops coordination  

## Success criteria

Learners can answer:

1. How do metrics reach Elastic in this workshop (OTLP / mOTLP), and how does that relate to a **Prometheus-era** metrics practice?  
2. How do I get **PromQL-oriented** boards into Kibana without rebuilding every panel?  
3. Where does Elastic differentiate (ES|QL, columnar metrics) vs continuity (PromQL / existing dashboard IP)?  
4. How do monitors become Kibana rule **drafts**, and why are they disabled on import?  
5. What is my first 30-day metrics adoption checklist back at the account?  
6. Where do Agent Builder metrics-adoption notes land, and how do you refresh them?  
