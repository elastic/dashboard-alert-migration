# Lab 1 — Adopt PromQL metric views (facilitator)

**Audience:** **existing Elastic customers** adopting **metrics** on Observability Serverless.  
**Lab job:** accelerate adoption by bringing **Grafana-shaped / PromQL metric dashboards** onto Kibana (not a competitive-only pitch).

Learners run **one command**:

```bash
bash /root/workshop/scripts/migrate_grafana_dashboards_to_serverless.sh
```

That script: OTLP → **`grafana-migrate`** (20 dashboards + **`--fetch-alerts`**) → **`publish_grafana_alert_drafts_kibana.py`**.

**Framing tip:** Open with “metrics already flow via OTLP; this lab gets trusted metric views onto Elastic fast.” Grafana is the **asset format**, metrics adoption is the **purpose**.

After migrate, learners should also open **Metrics adoption — AI notes** (Agent Builder → library Markdown panels). Workflow: **`workflows/metrics-adoption-recommendations.yaml`**.

**Optional extensions (not in assignment):**

- **Laptop + Cursor:** clone repo, paste VM **`export`** lines from **`grep … ~/.bashrc`**, run the same migrate script or raw **`grafana-migrate`** (see **`scripts/migrate_grafana_dashboards_to_serverless.sh`**).
- **Legacy Path B:** **`grafana_to_elastic.py`** + **`publish_grafana_drafts_kibana.py`** for `*-elastic-draft.json` flows.
- **Any grafana.com dashboard:** export JSON → **`grafana_to_elastic.py`** → **`publish_grafana_drafts_kibana.py`**.
- **Dynamic metrics overview:** **`scripts/generate_dynamic_o11y_dashboard.sh`** (discovery-style adoption without source JSON).
- **Re-seed AI notes only:** **`python3 scripts/ensure_ai_recommendation_panels.py --seed-now`**

**Invite copy:** **`docs/invite.md`**. **Agent Skills:** **`kibana-dashboards`**, **`agent-skills/workshop-grafana-to-elastic/SKILL.md`**.
