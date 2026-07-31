# Workshop design — Metrics adoption for existing customers

## Intent

| | |
| --- | --- |
| **Purpose** | Metrics adoption on Elastic Observability |
| **Audience** | Existing Elastic customers |
| **Outcome** | Teams leave able to ingest metrics via OTLP, land operational dashboards/alerts on `metrics-*`, and reuse metric dashboards they already maintain elsewhere |

Earlier “Grafana customer / Datadog customer migration” framing was **placeholder positioning**. Grafana and Datadog remain in the hands-on path because they are the **most common sources of existing metric dashboard IP** — not because the invite audience is competitive displacement only.

## Why this design (vs a greenfield metrics lab)

For accounts already on Elastic, the adoption bottleneck is rarely “can Kibana draw a chart?” It is:

1. **Ingest confidence** — metrics land in `metrics-*` with dimensions teams recognize  
2. **Time-to-value** — replace months of hand-rebuild with reviewable automation  
3. **Governance** — dashboards and alerts as drafts → human approve → enforce  
4. **Continuity** — keep PromQL / Datadog query intent visible while ES|QL runs at query time  

This track already exercises all four with a production Instruqt + Serverless + mOTLP spine. Reframing keeps that engine and changes the **story, invite, and facilitator language**.

## Lab map (learner-facing)

| Lab | Adoption job | Mechanic (unchanged) |
| --- | --- | --- |
| **Lab 1** | Adopt PromQL-oriented metric views onto Elastic | `migrate_grafana_dashboards_to_serverless.sh` (20 boards + alert drafts) |
| **Lab 2** | Adopt Datadog-oriented metric views + monitors | `migrate_datadog_dashboards_to_serverless.sh` (10 boards + 4 rules) |

Both labs validate on **live OTLP** (`metrics-*` / `logs-*` / `traces-*`), the same path customers use with Elastic managed OTLP.

## Invite principles

- Lead with **metrics adoption** and **existing Elastic customers**  
- Mention Grafana/Datadog as **optional accelerators** (bring metric assets you already have)  
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

1. How do metrics reach Elastic in this workshop (and in production OTLP terms)?  
2. How do I get a reviewable wave of metric dashboards into Kibana without rebuilding every panel?  
3. How do monitors become Kibana rule **drafts**, and why are they disabled on import?  
4. What is my first 30-day metrics adoption checklist back at the account?  
5. Where do Agent Builder metrics-adoption notes land, and how do you refresh them?  
