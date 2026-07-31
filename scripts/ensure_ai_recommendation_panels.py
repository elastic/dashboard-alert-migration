#!/usr/bin/env python3
"""
Ensure Agent Builder–driven metrics-adoption notes on workshop dashboards.

Mirrors the dbmonitoring pattern:
  - library Markdown saved objects (workshop-ai-rec-grafana | workshop-ai-rec-datadog)
  - Elasticsearch index metrics-adoption-recommendations
  - dedicated Kibana dashboard + optional strip on Traffic overview / Service overview
  - optional --seed-now via POST /api/agent_builder/converse (instant demo content)

Usage:
  python3 scripts/ensure_ai_recommendation_panels.py
  python3 scripts/ensure_ai_recommendation_panels.py --seed-now
  python3 scripts/ensure_ai_recommendation_panels.py --platform grafana

Env: KIBANA_URL + ES_API_KEY (or KIBANA_API_KEY) + ES_URL for index create.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid

KIBANA_URL = os.environ.get("KIBANA_URL", "").rstrip("/")
ES_URL = os.environ.get("ES_URL", "").rstrip("/")
API_KEY = (
    os.environ.get("KIBANA_API_KEY", "")
    or os.environ.get("ES_API_KEY", "")
    or os.environ.get("ELASTICSEARCH_API_KEY", "")
)
ES_USER = os.environ.get("ES_USERNAME", "admin")
ES_PASS = os.environ.get("ES_PASSWORD", "") or os.environ.get("ELASTICSEARCH_PASSWORD", "")

REC_INDEX = "metrics-adoption-recommendations"
REC_MARKDOWN_MAX = 48000
PLATFORMS = ("grafana", "datadog")
OVERVIEW_DASHBOARD_ID = "workshop-metrics-adoption-ai-notes"
OVERVIEW_TITLE = "Metrics adoption — AI notes"

# Append AI strip to these migrated dashboard titles when present.
ATTACH_TITLES = {
    "grafana": "Traffic overview",
    "datadog": "Service overview",
}

SEED_PROMPTS = {
    "grafana": """You are an Elastic Observability specialist helping existing Elastic customers
adopt metrics on Observability Serverless. Workshop context: OTLP → Alloy → mOTLP into metrics-*/logs-*/traces-*;
Grafana/PromQL boards (Traffic overview, latency, errors) with http_requests_total, service.name, host.name.
Produce concise markdown (max ~35 lines): (1) what to validate first on PromQL-shaped boards,
(2) Discover/ES|QL checks on metrics-*, (3) first alerts to enable from drafts, (4) why reusing PromQL
dashboard IP accelerates metrics adoption. Keep advice generic.""",
    "datadog": """You are an Elastic Observability specialist helping existing Elastic customers
adopt metrics on Observability Serverless. Workshop context: same OTLP path; Datadog-shaped boards
(Service overview, host CPU/memory) via datadog-migrate --field-profile otel; monitors become disabled rule drafts.
Produce concise markdown (max ~35 lines): (1) what to validate first, (2) OTel attrs vs DD tags,
(3) monitor→rule governance, (4) why DD exports accelerate metrics adoption on Elastic. Keep advice generic.""",
}


def _auth_header() -> str:
    if API_KEY:
        return f"ApiKey {API_KEY}"
    if ES_PASS:
        return "Basic " + base64.b64encode(f"{ES_USER}:{ES_PASS}".encode()).decode()
    sys.exit("ERROR: Set ES_API_KEY / KIBANA_API_KEY or ES_PASSWORD")


HEADERS = {
    "Authorization": _auth_header() if KIBANA_URL else "",
    "kbn-xsrf": "true",
    "x-elastic-internal-origin": "kibana",
    "Content-Type": "application/json",
    "Elastic-Api-Version": os.environ.get("KIBANA_ELASTIC_API_VERSION", "2023-10-31"),
    "User-Agent": "elastic-agentic",
}


def gid() -> str:
    return str(uuid.uuid4())


def rec_markdown_so_id(platform: str) -> str:
    return f"workshop-ai-rec-{platform}"


def _request(method: str, url: str, body: dict | None = None, headers: dict | None = None):
    data = None if body is None else json.dumps(body).encode()
    hdrs = dict(headers or HEADERS)
    if body is None:
        hdrs.pop("Content-Type", None)
    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req) as r:
            raw = r.read()
            if not raw:
                return None, r.status
            try:
                return json.loads(raw), r.status
            except json.JSONDecodeError:
                return raw.decode(), r.status
    except urllib.error.HTTPError as e:
        err = e.read().decode() if e.fp else ""
        return {"_http_error": e.code, "_body": err}, e.code


def kbn(method: str, path: str, body: dict | None = None):
    return _request(method, f"{KIBANA_URL}{path}", body)


def es(method: str, path: str, body: dict | None = None):
    if not ES_URL:
        return {"_http_error": 0, "_body": "ES_URL unset"}, 0
    return _request(method, f"{ES_URL}{path}", body, headers={
        "Authorization": HEADERS["Authorization"],
        "Content-Type": "application/json",
    })


def ensure_rec_index() -> bool:
    mappings = {
        "mappings": {
            "properties": {
                "@timestamp": {"type": "date"},
                "execution_id": {"type": "keyword"},
                "workflow_name": {"type": "keyword"},
                "source": {"type": "keyword"},
                "dashboard_platform": {"type": "keyword"},
                "recommendation": {"type": "text"},
            }
        }
    }
    payload, status = es("PUT", f"/{REC_INDEX}", mappings)
    if status in (200, 201):
        print(f"  ✓ index {REC_INDEX} ready (HTTP {status})")
        return True
    if status == 400 and isinstance(payload, dict) and "resource_already_exists" in str(payload.get("_body", "")):
        print(f"  ✓ index {REC_INDEX} already exists")
        return True
    # Already exists often returns 400 with different body; try GET
    _, gstatus = es("GET", f"/{REC_INDEX}")
    if gstatus == 200:
        print(f"  ✓ index {REC_INDEX} already exists")
        return True
    print(f"  WARN: ensure index {REC_INDEX} → HTTP {status}: {str(payload)[:300]}", file=sys.stderr)
    return False


def markdown_exists(so_id: str) -> bool:
    qid = urllib.parse.quote(so_id, safe="")
    _, status = kbn("GET", f"/api/saved_objects/markdown/{qid}")
    return status == 200


def post_markdown(so_id: str, title: str, content: str) -> bool:
    qid = urllib.parse.quote(so_id, safe="")
    payload, status = kbn(
        "POST",
        f"/api/saved_objects/markdown/{qid}?overwrite=true",
        {
            "attributes": {
                "title": title,
                "description": "",
                "content": content[:REC_MARKDOWN_MAX],
            }
        },
    )
    if status in (200, 201):
        return True
    print(f"  WARN: markdown {so_id} → HTTP {status}: {str(payload)[:300]}", file=sys.stderr)
    return False


def ensure_markdown_placeholders(platforms: tuple[str, ...]) -> bool:
    placeholder = (
        "### AI metrics adoption notes\n\n"
        "_This panel updates when **Metrics adoption — AI dashboard notes** runs "
        "(every 10 minutes or on manual run in **Management → Workflows**). "
        "Or re-run: `python3 scripts/ensure_ai_recommendation_panels.py --seed-now`._"
    )
    ok = True
    for p in platforms:
        sid = rec_markdown_so_id(p)
        title = f"AI metrics adoption notes — {p}"
        if markdown_exists(sid):
            print(f"  ✓ markdown {sid} exists")
            continue
        if post_markdown(sid, title, placeholder):
            print(f"  ✓ created markdown {sid}")
        else:
            ok = False
    return ok


def markdown_panel(platform: str, box: tuple[int, int, int, int]) -> dict:
    x, y, w, h = box
    return {
        "type": "markdown",
        "id": gid(),
        "grid": {"x": x, "y": y, "w": w, "h": h},
        "config": {"ref_id": rec_markdown_so_id(platform)},
    }


def list_dashboards_by_title() -> dict[str, str]:
    payload, status = kbn("GET", "/api/dashboards?apiVersion=1")
    out: dict[str, str] = {}
    if status != 200 or not isinstance(payload, dict):
        return out
    for row in payload.get("dashboards") or []:
        if not isinstance(row, dict):
            continue
        did = row.get("id")
        data = row.get("data") or {}
        title = (data.get("title") or "").strip()
        if did and title:
            out[title] = did
    return out


def get_dashboard(dash_id: str) -> dict | None:
    qid = urllib.parse.quote(dash_id, safe="")
    payload, status = kbn("GET", f"/api/dashboards/{qid}?apiVersion=1")
    if status != 200 or not isinstance(payload, dict):
        return None
    return payload


def put_dashboard(dash_id: str, data: dict) -> bool:
    qid = urllib.parse.quote(dash_id, safe="")
    body = {
        "title": data.get("title"),
        "description": data.get("description") or "",
        "panels": data.get("panels") or [],
    }
    if data.get("time_range"):
        body["time_range"] = data["time_range"]
    _, status = kbn("PUT", f"/api/dashboards/{qid}?apiVersion=1", body)
    return status in (200, 201)


def post_dashboard(data: dict) -> str | None:
    payload, status = kbn("POST", "/api/dashboards?apiVersion=1", data)
    if status not in (200, 201) or not isinstance(payload, dict):
        print(f"  WARN: POST dashboard → HTTP {status}: {str(payload)[:400]}", file=sys.stderr)
        return None
    return payload.get("id") or (payload.get("data") or {}).get("id")


def ensure_overview_dashboard(platforms: tuple[str, ...]) -> None:
    panels = []
    y = 0
    for p in platforms:
        panels.append(markdown_panel(p, (0, y, 48, 16)))
        y += 16
    body = {
        "id": OVERVIEW_DASHBOARD_ID,
        "title": OVERVIEW_TITLE,
        "description": (
            "Agent Builder metrics-adoption notes for existing Elastic customers. "
            "Content refreshes from the Metrics adoption — AI dashboard notes workflow."
        ),
        "time_range": {"from": "now-30m", "to": "now"},
        "panels": panels,
    }
    existing = get_dashboard(OVERVIEW_DASHBOARD_ID)
    if existing:
        data = existing.get("data") or existing
        data["panels"] = panels
        data["title"] = OVERVIEW_TITLE
        data["description"] = body["description"]
        if put_dashboard(OVERVIEW_DASHBOARD_ID, data):
            print(f"  ✓ updated dashboard {OVERVIEW_TITLE!r} ({OVERVIEW_DASHBOARD_ID})")
            return
    did = post_dashboard(body)
    if did:
        print(f"  ✓ created dashboard {OVERVIEW_TITLE!r} (id={did})")
    else:
        # Retry without fixed id
        body.pop("id", None)
        did = post_dashboard(body)
        if did:
            print(f"  ✓ created dashboard {OVERVIEW_TITLE!r} (id={did})")


def _panel_refs_markdown(panels: list) -> set[str]:
    refs = set()
    for p in panels or []:
        if not isinstance(p, dict):
            continue
        cfg = p.get("config") or {}
        rid = cfg.get("ref_id") or ""
        if rid:
            refs.add(rid)
        # nested / alternate shapes
        for key in ("embeds", "panels"):
            nested = p.get(key)
            if isinstance(nested, list):
                refs |= _panel_refs_markdown(nested)
    return refs


def attach_to_migrated_dashboard(platform: str) -> None:
    title = ATTACH_TITLES.get(platform)
    if not title:
        return
    by_title = list_dashboards_by_title()
    dash_id = by_title.get(title)
    if not dash_id:
        print(f"  · skip attach — dashboard {title!r} not found yet (run migrate first)")
        return
    payload = get_dashboard(dash_id)
    if not payload:
        print(f"  WARN: could not GET dashboard {title!r}", file=sys.stderr)
        return
    data = payload.get("data") or payload
    panels = list(data.get("panels") or [])
    sid = rec_markdown_so_id(platform)
    if sid in _panel_refs_markdown(panels):
        print(f"  ✓ {title!r} already has AI panel ({sid})")
        return
    max_y = 0
    for p in panels:
        if not isinstance(p, dict):
            continue
        g = p.get("grid") or p.get("gridData") or {}
        max_y = max(max_y, int(g.get("y", 0)) + int(g.get("h", 0)))
    panels.append(markdown_panel(platform, (0, max_y + 1, 48, 14)))
    data["panels"] = panels
    if put_dashboard(dash_id, data):
        print(f"  ✓ attached AI panel to {title!r}")
    else:
        print(f"  WARN: could not PUT {title!r} (Lens layout may be API-incompatible); overview dashboard still works", file=sys.stderr)


def seed_via_agent_builder(platforms: tuple[str, ...]) -> None:
    for p in platforms:
        prompt = SEED_PROMPTS[p]
        print(f"  → Agent Builder converse ({p})...")
        payload, status = kbn(
            "POST",
            "/api/agent_builder/converse",
            {"input": prompt},
        )
        if status not in (200, 201) or not isinstance(payload, dict):
            print(f"  WARN: converse {p} → HTTP {status}: {str(payload)[:400]}", file=sys.stderr)
            continue
        msg = (
            ((payload.get("response") or {}).get("message"))
            or payload.get("message")
            or ""
        )
        if not msg and isinstance(payload.get("output"), dict):
            msg = (payload["output"].get("response") or {}).get("message") or ""
        if not msg:
            # Some builds nest differently
            msg = json.dumps(payload)[:2000]
            print(f"  WARN: unexpected converse shape for {p}; writing raw excerpt", file=sys.stderr)
        title = f"AI metrics adoption notes — {p}"
        if post_markdown(rec_markdown_so_id(p), title, str(msg)):
            print(f"  ✓ seeded markdown {rec_markdown_so_id(p)}")
        es(
            "POST",
            f"/{REC_INDEX}/_doc",
            {
                "@timestamp": __import__("datetime").datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "execution_id": f"seed-{gid()}",
                "workflow_name": "ensure_ai_recommendation_panels.py",
                "source": "agent_builder_seed",
                "dashboard_platform": p,
                "recommendation": str(msg)[:REC_MARKDOWN_MAX],
            },
        )


def main() -> int:
    if not KIBANA_URL:
        sys.exit("ERROR: KIBANA_URL not set")

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seed-now", action="store_true", help="Call Agent Builder now to fill markdown")
    ap.add_argument(
        "--platform",
        choices=PLATFORMS,
        action="append",
        help="Limit to one platform (repeatable). Default: both.",
    )
    ap.add_argument("--skip-attach", action="store_true", help="Do not append panels to migrated dashboards")
    args = ap.parse_args()
    platforms = tuple(args.platform) if args.platform else PLATFORMS

    print("==> Metrics adoption AI recommendation panels")
    ensure_rec_index()
    ensure_markdown_placeholders(platforms)
    if args.seed_now:
        seed_via_agent_builder(platforms)
    ensure_overview_dashboard(platforms)
    if not args.skip_attach:
        for p in platforms:
            attach_to_migrated_dashboard(p)
    print("==> Done. Open Elastic Serverless → Dashboards → Metrics adoption — AI notes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
