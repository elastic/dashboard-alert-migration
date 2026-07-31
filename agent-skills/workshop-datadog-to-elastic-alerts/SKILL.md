---
name: workshop-datadog-to-elastic-alerts
description: >
  Workshop skill for metrics adoption on Elastic Observability Serverless (existing customers):
  convert Datadog-style monitor JSON into Kibana alerting rule drafts; complements Elastic Agent Skills for alerting APIs.
metadata:
  author: workshop
  version: 0.1.1
---

# Datadog-style monitors → Elastic alerts (workshop)

## When to use

Use when adopting **metrics alerting** on Elastic: translate `assets/datadog/monitor-*.json` into **Kibana
alerting** JSON skeletons, then tune for live indices and rules APIs.

## Workflow

```bash
python3 tools/datadog_to_elastic_alert.py assets/datadog/<monitor>.json -o build/elastic-alerts/<name>-elastic.json
```

Then refine `params` (index patterns, query DSL, thresholds) using Kibana or the alerting APIs described in upstream
[Elastic Agent Skills](https://github.com/elastic/agent-skills).

## Notes

- Datadog exports vary; validate fields (`type`, `query`, `options.thresholds`).
- Anomaly monitors map conceptually to **Elastic ML** jobs + anomaly rules when ML is available.
