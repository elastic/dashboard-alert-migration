# Metrics adoption on Elastic Observability (Instruqt track)

**GitHub:** [github.com/elastic/dashboard-alert-migration](https://github.com/elastic/dashboard-alert-migration)

**Instruqt (Elastic team):** [play.instruqt.com/manage/elastic/tracks/elastic-serverless-migration-lab](https://play.instruqt.com/manage/elastic/tracks/elastic-serverless-migration-lab)

**Purpose:** **Metrics adoption** on Elastic Observability Serverless.  
**Audience:** **Existing Elastic customers** deepening metrics coverage (often alongside logs/traces already on Elastic).

**Goal:** Train teams to land **metrics** in Elastic via **OTLP → managed OTLP (mOTLP)**, publish reviewable **Kibana dashboards and alert drafts** on live **`metrics-*`** data, and **accelerate adoption** by bringing forward PromQL / Datadog-shaped metric assets they may already own (via **`grafana-migrate`** / **`datadog-migrate`**).

**Invite & design:** [`docs/invite.md`](docs/invite.md) · [`docs/workshop-design.md`](docs/workshop-design.md)

**Primary migration engine:** **[elastic/observability-migration-platform](https://github.com/elastic/observability-migration-platform)** (`obs-migrate`, `grafana-migrate`, `datadog-migrate`; formerly **elastic/mig-to-kbn**). Upstream docs: [architecture](https://github.com/elastic/observability-migration-platform/blob/main/docs/architecture.md), [Grafana sources](https://github.com/elastic/observability-migration-platform/blob/main/docs/sources/grafana.md), [Datadog sources](https://github.com/elastic/observability-migration-platform/blob/main/docs/sources/datadog.md).

**Agent Builder AI notes (dbmonitoring pattern):** After each lab migrate, the scripts call **`scripts/ensure_ai_recommendation_panels.py --seed-now`** and deploy **`workflows/metrics-adoption-recommendations.yaml`**. That workflow uses native **`ai.agent`** steps (Agent Builder), indexes into **`metrics-adoption-recommendations`**, and refreshes library Markdown **`workshop-ai-rec-*`** on the **Metrics adoption — AI notes** dashboard (and optionally **Traffic overview** / **Service overview**). Skip with **`WORKSHOP_SKIP_AI_NOTES=1`**.

This repo **vendors** an **unmodified copy** of upstream under **`mig-to-kbn/`** (directory name kept for scripts). The pinned commit is recorded in **`mig-to-kbn-upstream.lock`**. **Refresh:** **`./scripts/update_mig_to_kbn.sh`** · **Verify:** **`./scripts/verify_mig_to_kbn_upstream.sh`**. On **Instruqt**, bootstrap installs from the vendored tree when present; otherwise it clones **`https://github.com/elastic/observability-migration-platform.git`** (override with **`WORKSHOP_MIG_TO_KBN_GIT_URL`** / **`WORKSHOP_MIG_TO_KBN_GIT_REF`**). **`scripts/install_workshop_mig_to_kbn.sh`** uses **`uv`** + **Python 3.12** at **`/opt/mig-to-kbn-venv`**; compile/upload uses **`uvx kb-dashboard-cli`**.

### Upstream boundary — do not fork `mig-to-kbn/` in this repo

**[observability-migration-platform](https://github.com/elastic/observability-migration-platform)** owns translators, CLIs, and the Kibana compile/upload path. **Do not** patch vendored code for lab-only behavior.

| Put it here (workshop) | Put it upstream (engine) |
| --- | --- |
| `assets/`, `scripts/`, `track_scripts/`, lab **`assignment.md`**, legacy **`tools/`**, **`agent-skills/`**, **`track.yml`** | CLI flags, panel translators, PromQL/Datadog fixes, new asset types |
| **`tools/otel_workshop_fleet.py`** — synthetic OTLP fields for panel smoke tests | **`grafana-migrate` / `datadog-migrate`** behavior |

Engine fixes → **[Issues](https://github.com/elastic/observability-migration-platform/issues)** / **[PRs](https://github.com/elastic/observability-migration-platform/pulls)**, then **`./scripts/update_mig_to_kbn.sh`** and commit the vendored bump.

## Two labs (Path A — primary)

| Lab | Adoption focus | Assets | Script | Target indices (typical) |
| --- | --- | --- | --- | --- |
| **Lab 1 — PromQL metric views** | Adopt Grafana-shaped metric dashboards onto Elastic | **20** dashboard JSON + **2** alert rules (`assets/grafana/alerts/`); each board has a **What & why** text panel | **`bash /root/workshop/scripts/migrate_grafana_dashboards_to_serverless.sh`** | **`metrics-*`**, **`logs-*`**, **`traces-*`**; **`grafana-migrate --native-promql`** |
| **Lab 2 — Datadog metric views** | Adopt Datadog-shaped metric dashboards + monitors | **10** workshop dashboards + **4** monitors; each board has a **What & why** note widget | **`bash /root/workshop/scripts/migrate_datadog_dashboards_to_serverless.sh`** | **`metrics-*`**, **`logs-*`** via upstream **`datadog-migrate --field-profile otel`** (built-in default) |

**Optional Lab 2 extension:** **`scripts/migrate_datadog_integrations_to_serverless.sh`** — **8** real dashboards from [DataDog/integrations-core](https://github.com/DataDog/integrations-core) under **`assets/datadog/integrations-core/`** (refresh with **`scripts/update_datadog_integrations_dashboards.sh`**).

Each migrate script **sources `~/.bashrc`**. Use the **absolute path** above so **`$PWD`** does not matter.

**Refresh an existing sandbox** (same VM, no new play):

```bash
cd /root/workshop && source ~/.bashrc && ./scripts/sync_workshop_from_git.sh
bash scripts/install_workshop_mig_to_kbn.sh   # if mig-to-kbn/ changed
```

**Laptop + Cursor:** clone this repo, **`./scripts/install_workshop_mig_to_kbn.sh`** (set **`MIG_TO_KBN_VENV`** to a user-writable path on macOS), copy **`export`** lines from **`serverless_creds.env.example`** or your Instruqt **`~/.bashrc`**, run the same migrate scripts.

## Telemetry on the workshop VM

Sandbox image: **`elastic/es3-api-v2`**. **`track_scripts/setup-es3-api`** creates an **Observability Serverless** project per play, proxies **Kibana on :8080**, and starts:

```
Python OTLP (fleet + datadog_otel) → Grafana Alloy (:4317/:4318) → mOTLP → logs-* / metrics-* / traces-*
```

Same pattern as **[elastic-autonomous-observability](https://play.instruqt.com/manage/elastic/tracks/elastic-autonomous-observability/sandbox)**. Default path is **real OTLP ingest**, not bulk JSON. Legacy bulk seed runs only if **`WORKSHOP_ALLOW_BULK_SEED=1`** on bootstrap.

| Component | Role |
| --- | --- |
| **`assets/alloy/workshop.alloy`** | OTLP receiver + optional Prometheus self-scrape → **mOTLP** export |
| **`tools/otel_workshop_fleet.py`** | **Six** worker subprocesses (**`service.name`** + **`host.name`**) emitting Grafana-style **`http_requests_total`** / **`http_request_duration_seconds`** plus **Datadog-style** names for Lab 2 (`trace_*`, `system_*`, `container_*`, disk/swap/cpu minor metrics — **28** names added for common migrated panel fields) |
| **`tools/datadog_otel_to_elastic.py`** | Extra **Datadog-style** OTLP traces/metrics/logs (**shopist-checkout** on **`workshop-node-07`**) |
| **`scripts/start_workshop_otel.sh`** | Restart Alloy + emitters; **`WORKSHOP_OTLP_ENDPOINT`** from **`~/.bashrc`** or derived from **`ES_URL`** (`.es.`→`.ingest.`) / **`KIBANA_URL`** (`.kb.`→`.ingest.`) |
| **`scripts/check_workshop_otel_pipeline.sh`** | Alloy **`:12345/metrics`**, ports **4317/4318**, process checks |

Regression check for fleet metric names: **`tests/test_workshop_fleet_metrics.py`**.

### Path A migrate behavior (defaults)

Both lab scripts call upstream **`grafana-migrate`** / **`datadog-migrate`** console scripts from the vendored package (same code as **`obs-migrate migrate --source …`**). Workshop wrappers only handle Instruqt env (**`~/.bashrc`**), OTLP startup, and legacy alert publishers — they do **not** patch the engine.

1. Start or reuse OTLP (**`start_workshop_otel.sh`**, ~45s wait).
2. Run upstream migrate CLI with **`--upload`** (flags match upstream docs — no vendored forks).
3. Publish workshop monitor/alert JSON via legacy **`tools/publish_*_alert_drafts_kibana.py`** where the lab still uses them.

**Output layout (current mig-to-kbn):** Grafana/Datadog artifacts live under **`build/mig-*/dashboards/yaml/`**, reports in **`dashboards/`**, alerts in **`alerts/`**. Lab checks and migrate scripts accept the legacy flat **`yaml/`** paths too.

**ES|QL pre-upload validation** is **off** by default (scripts pass **`--es-url ""`** so **`ES_URL` in `~/.bashrc`** does not auto-enable validation). Set **`WORKSHOP_MIG_ES_VALIDATE=1`** for live **`/_query`** checks.

**Skip / force OTLP:** **`WORKSHOP_SKIP_OTEL=1`**, **`WORKSHOP_FORCE_OTEL_RESTART=1`**.

### Known gaps (upstream)

Some panels still fail on **`counter_long`** aggregations (**SUM** / **MAX** / **MIN** on counter-typed fields). Tracked in **[observability-migration-platform#148](https://github.com/elastic/observability-migration-platform/issues/148)**. Missing **field** errors on Datadog dashboards are largely addressed by the expanded fleet emitters + **`--field-profile otel`**.

## Path B — legacy workshop Python pipeline (facilitators)

Labs use **Path A** (`mig-to-kbn`). The sections below describe **legacy** **`tools/grafana_to_elastic.py`**, **`publish_grafana_drafts_kibana.py`**, etc., for comparison or **`build/*-elastic-draft.json`** flows.

### Stage 1 — Converters (source JSON → `*-elastic-draft.json`)

| Script | Input | Output |
| --- | --- | --- |
| **`tools/grafana_to_elastic.py`** | Grafana **`panels[].targets[].expr`** (PromQL) | **`migration.promql`**, notes |
| **`tools/datadog_dashboard_to_elastic.py`** | Datadog widget **`requests[].q`** | **`migration.datadog_query`**, notes |
| **`tools/datadog_to_elastic_alert.py`** | Monitor JSON | Rule drafts for **`publish_datadog_alert_drafts_kibana.py`** |

### Stage 2 — Publisher (`tools/publish_grafana_drafts_kibana.py`)

Builds **Dashboards API** payloads: Markdown canvas + **Lens** panels with **inline ES|QL**. Resolves **`FROM`** via probes (**`WORKSHOP_ESQL_FROM`** override, then **`logs-*`**, **`metrics-*`**, **`traces-*`**, unions). Classifies panels from PromQL/Datadog query text → category → ES|QL template.

**Note:** Legacy publisher templates often reference **`http.server.request.count`**-style names. **Path A** and **OTLP fleet** use **`http_requests_total`** and upstream **`datadog-migrate --field-profile otel`** field mappings (**`metrics-*`**). Prefer Path A for lab fidelity.

Key env vars: **`WORKSHOP_ESQL_FROM`**, **`WORKSHOP_ESQL_BUCKET_DURATION`** (default **`1 hour`**), **`WORKSHOP_MIN_LENS_PANELS`** / **`WORKSHOP_MAX_LENS_PANELS`**, **`WORKSHOP_DD_PAD_LENS`**, **`WORKSHOP_ESQL_HTTP_STATUS_COLUMN`**.

### Grafana Cloud app dashboards (Elasticsearch datasource)

**`tools/publish_grafana_es_app_dashboard.py`** — for **`dashboard.grafana.app/v2beta1`** JSON with Elasticsearch queries (not classic PromQL). Fixture: **`assets/grafana/fixtures/grafana-app-v2-elasticsearch-min.json`**.

### Dynamic OTLP dashboard

**`tools/generate_dynamic_o11y_dashboard.py`** (**`./scripts/generate_dynamic_o11y_dashboard.sh`**) probes **`logs-*` / `metrics-*`**, creates/replaces one ES|QL Lens dashboard (**`workshop-dynamic-otlp-overview`** by default). See **`workflows/dynamic-observability-dashboard.yaml`**.

## Layout

| Path | Purpose |
| --- | --- |
| `track.yml` / `config.yml` | Instruqt metadata + **`elastic/es3-api-v2`** VM (**`ESS_CLOUD_API_KEY`** secret) |
| `track_scripts/setup-es3-api` | Serverless project, nginx → Kibana **:8080**, venvs, Alloy + OTLP emitters |
| `01-lab-01-grafana-to-elastic/` | Lab 1 challenge (**20** Grafana dashboards + alerts) |
| `02-lab-02-datadog-dashboards-alerts-to-elastic/` | Lab 2 challenge (**10** dashboards + **4** monitors) |
| `mig-to-kbn/` | Unmodified vendored **observability-migration-platform** snapshot |
| `mig-to-kbn-upstream.lock` | Pinned upstream **`commit=`** (written by **`update_mig_to_kbn.sh`**) |
| `scripts/patches/` | Pending-upstream patches re-applied after each **`update_mig_to_kbn.sh`** (see **`scripts/patches/README.md`**) |
| `assets/grafana/` | **20** generated Grafana JSON; **`alerts/`** for **`--fetch-alerts`** |
| `assets/datadog/dashboards/` | **10** Datadog-style dashboards |
| `assets/datadog/integrations-core/` | **8** integrations-core dashboards (BSD) |
| `assets/datadog/monitor-*.json` | **4** monitor samples |
| `assets/alloy/workshop.alloy` | Alloy → mOTLP |
| `tools/` | Legacy converters/publishers + **`otel_workshop_fleet.py`**, **`datadog_otel_to_elastic.py`**, **`generate_dynamic_o11y_dashboard.py`** |
| `scripts/` | Migrate wrappers, OTLP, **`update_mig_to_kbn.sh`**, **`verify_mig_to_kbn_upstream.sh`**, **`install_workshop_mig_to_kbn.sh`**, **`ensure_workshop_mig_to_kbn_sources.sh`**, **`push_git_and_instruqt.sh`**, **`sync_workshop_from_git.sh`** |
| `tests/` | Workshop tests (e.g. **`test_workshop_fleet_metrics.py`**) |
| `agent-skills/` | Workshop skills + [elastic/agent-skills](https://github.com/elastic/agent-skills) wrappers |
| `docs/dashboards-api-getting-started.md` | Dashboards API reference |
| `workflows/` | MCP-oriented workflow YAML |
| `serverless_creds.env.example` | Template for laptop runs (**copy → `serverless_creds.env`**, never commit secrets) |

Loading slides live in each lab **`assignment.md`** frontmatter (`notes:`).

## Discover and Observability UIs

| Symptom | What to check |
| --- | --- |
| **Lab 1 — empty Grafana panels** | Time picker **Last 15m–24h**; **`FROM metrics-*`** in ES\|QL; OTLP running (**`check_workshop_otel_pipeline.sh`**) |
| **Lab 2 — empty Datadog panels** | Time picker **Last 15m–24h**; data view **`metrics-*`** (otel profile default); OTLP running; fleet emits **`trace_*`**, **`system_*`**, **`container_*`** |
| **Table has rows, chart blank** | Extend time range end to **now**; **`BUCKET(@timestamp, …)`** may lag newest docs |
| **Applications / Infrastructure / Hosts** | Need OTLP traces + resource attrs — **`start_workshop_otel.sh`** |
| **Multi-day metric history** | Fleet only writes from startup; optional **`tools/seed_workshop_telemetry.py --metrics-time-series`** (bulk, not OTLP) |
| **Panel-aligned synthetic bulk data** | Upstream **`mig-to-kbn/scripts/setup_telemetry_data.py`** or **`obs-migrate seed-sample-data`** from migrated **`yaml/`** (see upstream **`docs/command-contract.md`**) |

## Facilitator prerequisites

- **Observability Serverless** project (Instruqt creates one per play via **`ESS_CLOUD_API_KEY`**).
- Vendored **`mig-to-kbn/pyproject.toml`** in the track bundle (or public clone at bootstrap).
- Outbound **HTTPS** for **`uv`**, PyPI, and optional **`git clone`** fallback.
- **`config.yml`** secrets: **`LLM_PROXY_PROD`**, **`ESS_CLOUD_API_KEY`** (values in Instruqt team settings only).

## Maintainers: bump engine + publish track

On your **laptop** (not the learner VM):

```bash
./scripts/update_mig_to_kbn.sh              # rsync upstream main → mig-to-kbn/
./scripts/verify_mig_to_kbn_upstream.sh     # diff check (must pass before commit)
# optional: ./scripts/update_mig_to_kbn.sh --reinstall

git add mig-to-kbn mig-to-kbn-upstream.lock && git commit -m "Bump vendored observability-migration-platform"
./scripts/push_git_and_instruqt.sh
```

If Instruqt reports remote track drift: **`instruqt track pull`**, merge **`track.yml`** / **`config.yml`**, commit, push again.

**Env overrides:** **`MIG_TO_KBN_REF`**, **`MIG_TO_KBN_GIT_URL`**, **`MIG_TO_KBN_DIR`**, **`MIG_TO_KBN_VENV`**.

On an **existing Instruqt VM** after a git pull: **`sync_workshop_from_git.sh`**, then **`bash scripts/install_workshop_mig_to_kbn.sh`** when **`mig-to-kbn/`** changed.

## Local smoke test (legacy converters)

```bash
python3 scripts/generate_grafana_dashboards.py
python3 scripts/generate_datadog_dashboards.py
python3 tools/grafana_to_elastic.py assets/grafana/01-overview.json --out-dir /tmp/g
python3 tools/datadog_dashboard_to_elastic.py assets/datadog/dashboards/01-service-overview.json --out-dir /tmp/d
python3 tools/datadog_to_elastic_alert.py assets/datadog/monitor-high-5xx-rate.json
```

## Agent skills

Workshop wrappers under **`agent-skills/`** point at upstream migration flows. Pair with **[elastic/agent-skills](https://github.com/elastic/agent-skills)** (`kibana-dashboards`, `kibana-alerting-rules`, Elasticsearch/Observability skills) for post-migration refinement in Cursor or Kibana.
