# Lab 2 — Adopt Datadog metric views & monitors (facilitator)

**Audience:** **existing Elastic customers** adopting **metrics** on Observability Serverless (pairs with Lab 1).  
**Lab job:** accelerate adoption with **Datadog-shaped metric dashboards and monitors** → Kibana dashboards + alert **drafts**.

Learners run **one command**:

```bash
bash /root/workshop/scripts/migrate_datadog_dashboards_to_serverless.sh
```

That script: OTLP → **`datadog-migrate`** (10 dashboards + **`--fetch-monitors`**) → **`publish_datadog_alert_drafts_kibana.py`**.

Ten dashboards under `assets/datadog/dashboards/`; four `monitor-*.json` → `build/elastic-alerts/`. OTLP: **`send_datadog_otel.sh`** or Alloy on the VM → Elastic **managed OTLP**.

**Framing tip:** Emphasize **drafts first** (imported disabled) — governance is part of metrics adoption for existing accounts. Also point at **Metrics adoption — AI notes** (Agent Builder).

**Optional extensions (not in assignment):**

- **Laptop + Cursor:** clone repo, paste VM **`export`** lines from **`grep … ~/.bashrc`**, run the same migrate script or raw **`datadog-migrate`** (see **`scripts/migrate_datadog_dashboards_to_serverless.sh`**).
- **Legacy draft JSON:** **`datadog_dashboard_to_elastic.py`** + **`publish_grafana_drafts_kibana.py`** for `*-elastic-draft.json` flows.
- **Integration dashboards:** **`migrate_datadog_integrations_to_serverless.sh`** (eight integrations-core exports).
- **Re-seed AI notes only:** **`python3 scripts/ensure_ai_recommendation_panels.py --platform datadog --seed-now`**

**Invite copy:** **`docs/invite.md`**. **Agent Skills:** **`kibana-dashboards`**, **`agent-skills/workshop-datadog-dashboards-to-elastic/SKILL.md`**, **`workshop-datadog-to-elastic-alerts`**.
