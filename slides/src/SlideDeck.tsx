import { useCallback, useEffect, useState } from "react";
import { ChevronLeft, ChevronRight, ExternalLink } from "lucide-react";
import { FallingPattern } from "@/components/ui/falling-pattern";
import { cn } from "@/lib/utils";

export type StatCard = {
  /** Big figure (e.g. 4–10×, 30, 2) */
  figure: string;
  title: string;
  caption?: string;
};

export type Slide = {
  title: string;
  subtitle?: string;
  bullets?: string[];
  /** Elastic-by-the-numbers style grid */
  statCards?: StatCard[];
  /** Instruqt (or other) lab — opens in a new browser tab */
  workshopUrl?: string;
  workshopLinkLabel?: string;
  /**
   * File in `slides/public/` (copied to site root). Use with Git LFS for large MP4s.
   * URL respects Vite `base` (GitHub Pages project path).
   */
  videoSrc?: string;
  /** Optional source citation under the slide body */
  sourceLabel?: string;
  sourceUrl?: string;
};

const INSTRUQT_INVITE = "https://play.instruqt.com/elastic/invite/fmt96ftdm41w";

/** Upstream repos for the Instruqt labs — open issues & PRs here (migration CLI + YAML compiler). */
const UPSTREAM_REPOS: {
  label: string;
  repoUrl: string;
  issuesUrl: string;
  pullsUrl: string;
  note?: string;
}[] = [
  {
    label: "elastic/observability-migration-platform",
    repoUrl: "https://github.com/elastic/observability-migration-platform",
    issuesUrl: "https://github.com/elastic/observability-migration-platform/issues",
    pullsUrl: "https://github.com/elastic/observability-migration-platform/pulls",
    note: "grafana-migrate / datadog-migrate — accelerate metrics dashboards & monitors onto Kibana.",
  },
  {
    label: "strawgate/kb-yaml-to-lens",
    repoUrl: "https://github.com/strawgate/kb-yaml-to-lens",
    issuesUrl: "https://github.com/strawgate/kb-yaml-to-lens/issues",
    pullsUrl: "https://github.com/strawgate/kb-yaml-to-lens/pulls",
    note: "kb-dashboard-cli — YAML dashboards → Kibana NDJSON (used by compile/upload).",
  },
];

const SLIDES: Slide[] = [
  {
    title: "Workshop walkthrough",
    subtitle:
      "Quick tour of the Instruqt lab — metrics adoption on Elastic Observability Serverless.",
    videoSrc: "dashboard-alert-migration.mp4",
  },
  {
    title: "Try the guided experience",
    subtitle:
      "Browser sandbox: live OTLP → metrics-*, PromQL & Datadog boards on Kibana, alert drafts, Agent Builder notes — no install.",
    workshopUrl: INSTRUQT_INVITE,
    workshopLinkLabel: "Launch Elastic sandbox (Instruqt)",
  },
  {
    title: "Five themes of this workshop",
    subtitle:
      "Existing Elastic customers — deepen metrics on the same plane as logs and traces.",
    statCards: [
      {
        figure: "1",
        title: "Metrics on Elastic",
        caption:
          "OTLP → managed ingest → live metrics-* alongside logs-* and traces-* — one Observability plane.",
      },
      {
        figure: "2",
        title: "Prometheus / PromQL",
        caption:
          "Bring PromQL-oriented (Grafana) dashboards onto Kibana without redrawing every panel.",
      },
      {
        figure: "3",
        title: "Datadog metric IP",
        caption:
          "Dashboards + monitors → Kibana boards and alert drafts — review before you enable.",
      },
      {
        figure: "4",
        title: "Platform depth",
        caption:
          "PromQL where you already live; ES|QL + columnar metrics where Elastic wins on query and storage.",
      },
      {
        figure: "5",
        title: "Agent Builder",
        caption:
          "AI notes on live dashboards — what to validate next after migrate, not slideware screenshots.",
      },
      {
        figure: "Labs",
        title: "How you practice",
        caption:
          "Lab 1: PromQL / Grafana → Kibana. Lab 2: Datadog boards + monitors → drafts. Both on live OTLP.",
      },
    ],
  },
  {
    title: "Why migrate Grafana & Datadog boards?",
    subtitle:
      "Dashboards and alerts are operational IP. Leaving them stranded means dual tooling, dual on-call, and slower incident response.",
    statCards: [
      {
        figure: "1",
        title: "Operations plane",
        caption:
          "Stop pivoting between Grafana/Datadog UIs and Kibana for the same incident — metrics, logs, and traces in one place.",
      },
      {
        figure: "IP",
        title: "Keep what you built",
        caption:
          "Years of PromQL panels and Datadog monitors are assets. Migration preserves intent instead of rebuilding every chart by hand.",
      },
      {
        figure: "Gov",
        title: "Draft → approve → enforce",
        caption:
          "Alert definitions become Kibana rule drafts so SREs review thresholds and connectors before go-live.",
      },
      {
        figure: "4–10×",
        title: "Less rebuild work",
        caption:
          "Bulk conversion + Dashboards API publish compresses analyst-days of hand recreation into scripted, reviewable waves.",
      },
      {
        figure: "CI",
        title: "Repeatable cutover",
        caption:
          "Exports + automation fit the same IaC discipline you already use — rerun, diff, and promote across environments.",
      },
      {
        figure: "OTLP",
        title: "Open ingest path",
        caption:
          "Standardize on OpenTelemetry while dual-publishing; migrate the UI/alert layer when the data plane is ready.",
      },
    ],
  },
  {
    title: "Elastic Metrics: columnar engine",
    subtitle:
      "Platform depth — store OTel metrics next to logs and traces with no compromise on query or storage.",
    statCards: [
      {
        figure: "30×",
        title: "Faster queries vs Prometheus",
        caption:
          "Up to 30× better query performance vs Prometheus, Mimir, and ClickHouse on competitive benchmarks.",
      },
      {
        figure: "3.75 B",
        title: "Per OTel data point",
        caption:
          "Storage down from ~25 bytes/point a year ago — up to 6.6× more efficient TSDS packing for high-cardinality metrics.",
      },
      {
        figure: "2.5×",
        title: "Better storage efficiency",
        caption:
          "Exceeds dedicated metrics stores on footprint while keeping Elasticsearch’s unified data model.",
      },
      {
        figure: "50%",
        title: "Higher indexing throughput",
        caption:
          "OTel/protobuf entrypoints + doc-value skippers cut CPU and I/O on the hot ingest path.",
      },
      {
        figure: "160×",
        title: "Query latency wins",
        caption:
          "Vectorized ES|QL time-series compute (TS + RATE + TBUCKET) vs prior TSDS aggregation paths.",
      },
      {
        figure: "ES|QL",
        title: "Beyond PromQL alone",
        caption:
          "PromQL where you already live; ES|QL joins metrics with logs and traces — what siloed PromQL stacks cannot do.",
      },
    ],
    sourceLabel: "Elasticsearch Labs — columnar metrics engine",
    sourceUrl:
      "https://www.elastic.co/search-labs/blog/elasticsearch-columnar-metrics-engine-30x-faster-prometheus",
  },
  {
    title: "Metrics on Elastic — live OTLP",
    subtitle:
      "Theme 1: the same open ingest path customers use when standardizing metrics on Observability Serverless.",
    bullets: [
      "Collectors and agents forward OTLP; Elastic managed OTLP (mOTLP) lands series in metrics-* next to logs-* and traces-*.",
      "Prometheus scrape still fits sidecars and meshes — Elastic becomes the metrics sink, not another siloed store.",
      "In the sandbox, Alloy + emitters confirm Lens and Discover against real series — not screenshots.",
      "Scoped API keys and Org security match how enterprises govern cross-team observability projects.",
    ],
  },
  {
    title: "Prometheus / PromQL → Kibana (Lab 1)",
    subtitle:
      "Theme 2: bring PromQL-oriented Grafana dashboards onto Kibana without redrawing every panel.",
    bullets: [
      "One command runs grafana-migrate: 20 PromQL/Grafana-shaped boards + workshop alert drafts onto live metrics-*.",
      "PromQL intent is preserved in the migration path; Lens / ES|QL is what executes against Elastic’s metrics store.",
      "Operating model: platform SREs run conversion; application owners validate visuals against golden datasets.",
      "Agent Builder AI notes land on each board so owners know what to validate next — not a static “what/why” strip.",
    ],
  },
  {
    title: "Datadog metric IP → Kibana (Lab 2)",
    subtitle:
      "Theme 3: dashboards and monitors become Kibana boards and alert drafts — review before enable.",
    bullets: [
      "One command runs datadog-migrate: 10 metric dashboards + 4 monitors → Kibana with the same OTLP metrics plane.",
      "Monitors surface as disabled Kibana rule drafts — SecOps and SREs approve thresholds before enforcement.",
      "Tag-heavy APM and host maps align with OTLP resource attributes already landing in Elastic.",
      "Optional integrations-core boards (NGINX, Postgres, Redis, RabbitMQ, …) extend the same Datadog IP story.",
    ],
  },
  {
    title: "Agent Builder on live boards",
    subtitle:
      "Theme 5: AI notes attached to migrated dashboards — adoption guidance grounded in what you just published.",
    bullets: [
      "After migrate, each Grafana/Datadog board gets an Agent Builder markdown strip (workshop-ai-rec-*).",
      "Notes focus on what to validate next: series freshness, field mappings, draft rules, and owner sign-off.",
      "A workshop workflow can refresh recommendations — same pattern as production Agent Builder + Workflows.",
      "Pair with Lab verify steps: open a board, scroll to AI notes, then check Observability → Rules (still disabled).",
    ],
  },
  {
    title: "A deliberate two-stage adoption path",
    subtitle:
      "Reduce risk: separate “capture metric intent” from “publish executable analytics.”",
    bullets: [
      "Stage 1 — Ingest Grafana/Datadog exports and emit Elastic-oriented drafts with traceable metadata.",
      "Stage 2 — Publish Lens panels and rules through Kibana APIs, with ES|QL grounded in your indices.",
      "Original PromQL and Datadog queries remain referenced for audit — they are not silently reinterpreted.",
      "Rerun, diff, and promote the same assets through dev → staging → prod.",
    ],
  },
  {
    title: "Elastic by the numbers",
    subtitle:
      "Directional benefits for metrics adoption business cases — timelines depend on complexity and cutover windows.",
    statCards: [
      {
        figure: "4–10×",
        title: "Less manual dashboard work",
        caption:
          "Bulk conversion plus Dashboards API publish vs hand-rebuilding every visualization from scratch.",
      },
      {
        figure: "30",
        title: "Metric dashboards in this journey",
        caption:
          "Twenty PromQL/Grafana-shaped and ten Datadog-shaped boards — enough volume to prove classification.",
      },
      {
        figure: "2",
        title: "Controlled phases",
        caption:
          "Phase 1: preserve source metric intent. Phase 2: publish executable ES|QL in Lens via API.",
      },
      {
        figure: "Hours",
        title: "Time to a reviewable wave",
        caption:
          "Scripted runs, validation, and SME sign-off — then rerun as you tune mappings.",
      },
      {
        figure: "1",
        title: "Unified ingest plane",
        caption:
          "One OTLP-oriented path for logs, metrics, and traces while you expand metrics coverage.",
      },
      {
        figure: "4",
        title: "Sample alert definitions",
        caption:
          "Monitor-style JSON becomes Kibana rule drafts — the same governance model as adopted dashboards.",
      },
    ],
  },
  {
    title: "Your next 30 days of metrics adoption",
    subtitle: "Treat the sandbox as a rehearsal — the same checklist scales once connectivity and roles are ready.",
    bullets: [
      "Metrics on Elastic — Confirm OTLP coverage: the series you care about appear in metrics-* with expected tags.",
      "PromQL / Datadog IP — Land three canonical boards (Grafana and/or Datadog path) and review with owners.",
      "Governance — Exercise two draft rules end-to-end before enabling enforcement.",
      "Platform depth + Agent Builder — Use ES|QL where it wins; refresh Agent Builder notes as boards evolve.",
    ],
  },
];

export function SlideDeck() {
  const [i, setI] = useState(0);
  const n = SLIDES.length;
  const slide = SLIDES[i];

  const prev = useCallback(() => setI((x) => (x <= 0 ? n - 1 : x - 1)), [n]);
  const next = useCallback(() => setI((x) => (x >= n - 1 ? 0 : x + 1)), [n]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "ArrowRight" || e.key === " " || e.key === "PageDown") {
        e.preventDefault();
        next();
      }
      if (e.key === "ArrowLeft" || e.key === "PageUp") {
        e.preventDefault();
        prev();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [next, prev]);

  return (
    <div className="relative min-h-screen w-full overflow-hidden">
      {/* Full pattern (no CSS mask — masks often drop the whole layer cross-browser). Legibility: content card below. */}
      <FallingPattern className="fixed inset-0 z-0 h-screen" />

      <div className="relative z-10 flex min-h-screen flex-col">
        <header className="flex items-center justify-between border-b border-white/10 bg-black/20 px-4 py-3 backdrop-blur-sm">
          <span className="font-mono text-xs text-white/70">
            Metrics adoption · Elastic Observability
          </span>
          <span className="font-mono text-xs text-white/50">
            {i + 1} / {n}
          </span>
        </header>

        <main className="flex flex-1 flex-col items-center justify-center px-4 py-10 text-center sm:px-6">
          <div
            className={cn(
              "w-full rounded-2xl px-6 py-8 md:px-10 md:py-12",
              "border border-white/15 bg-zinc-950/85 shadow-2xl backdrop-blur-md",
              "ring-1 ring-black/40",
              slide.statCards?.length ? "max-w-6xl" : slide.videoSrc ? "max-w-5xl" : "max-w-4xl",
            )}
          >
            <h1
              className={cn(
                "max-w-4xl font-mono text-3xl font-extrabold tracking-tight sm:text-5xl md:text-6xl",
                "text-zinc-50 [text-shadow:0_2px_24px_rgba(0,0,0,0.85)]",
              )}
            >
              {slide.title}
            </h1>
            {slide.subtitle ? (
              <p className="mx-auto mt-4 max-w-3xl text-lg text-zinc-200/95">{slide.subtitle}</p>
            ) : null}
            {slide.videoSrc ? (
              <div className="mt-8 w-full">
                <video
                  className="mx-auto w-full max-h-[min(60vh,720px)] rounded-xl border border-white/15 bg-black/70 shadow-xl"
                  controls
                  playsInline
                  preload="metadata"
                  aria-label="Workshop overview video"
                >
                  <source
                    src={`${import.meta.env.BASE_URL}${slide.videoSrc}`}
                    type="video/mp4"
                  />
                  Your browser does not support embedded video — open the MP4 from the repository{" "}
                  <code className="rounded bg-white/10 px-1 text-sm">slides/public/</code> or run the lab in Instruqt.
                </video>
              </div>
            ) : null}
            {slide.statCards?.length ? (
              <div className="mt-10 grid w-full gap-4 sm:grid-cols-2 xl:grid-cols-3">
                {slide.statCards.map((s) => (
                  <div
                    key={s.title}
                    className={cn(
                      "flex flex-col rounded-xl border border-[var(--primary)]/25 bg-gradient-to-br from-zinc-900/90 to-zinc-950/90",
                      "px-5 py-5 text-left shadow-lg ring-1 ring-white/5",
                    )}
                  >
                    <p
                      className={cn(
                        "font-mono text-4xl font-extrabold tracking-tight text-[var(--primary)] md:text-5xl",
                        "[text-shadow:0_0_40px_color-mix(in_oklab,var(--primary)_35%,transparent)]",
                      )}
                    >
                      {s.figure}
                    </p>
                    <p className="mt-3 font-mono text-sm font-semibold uppercase tracking-wide text-zinc-200">
                      {s.title}
                    </p>
                    {s.caption ? (
                      <p className="mt-2 text-sm leading-snug text-zinc-400">{s.caption}</p>
                    ) : null}
                  </div>
                ))}
              </div>
            ) : null}
            {slide.workshopUrl ? (
              <div className="mt-8 flex flex-col items-center gap-2">
                <a
                  href={slide.workshopUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={cn(
                    "inline-flex items-center justify-center gap-2 rounded-xl px-6 py-3.5",
                    "bg-[var(--primary)] font-mono text-sm font-semibold text-white shadow-lg",
                    "ring-1 ring-white/20 transition hover:brightness-110 focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--primary)] focus-visible:ring-offset-2 focus-visible:ring-offset-zinc-950",
                  )}
                  aria-label={`${slide.workshopLinkLabel ?? "Open workshop"} (opens in new tab)`}
                >
                  <ExternalLink className="size-4 shrink-0 opacity-90" aria-hidden />
                  {slide.workshopLinkLabel ?? "Open workshop"}
                </a>
                <span className="font-mono text-xs text-zinc-500">Opens in a new tab</span>
              </div>
            ) : null}
            {slide.bullets?.length ? (
              <ul className="mx-auto mt-10 max-w-3xl space-y-3 text-left text-base text-zinc-100 sm:text-lg">
                {slide.bullets.map((b) => (
                  <li key={b} className="flex gap-3 leading-snug">
                    <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-[var(--primary)]" />
                    <span className="[text-shadow:0_1px_8px_rgba(0,0,0,0.85)]">{b}</span>
                  </li>
                ))}
              </ul>
            ) : null}
            {slide.sourceUrl ? (
              <p className="mx-auto mt-8 max-w-3xl font-mono text-xs text-zinc-500">
                Source:{" "}
                <a
                  href={slide.sourceUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-[var(--primary)] underline decoration-white/20 underline-offset-2 hover:decoration-[var(--primary)]"
                >
                  {slide.sourceLabel ?? slide.sourceUrl}
                </a>
              </p>
            ) : null}
          </div>
        </main>

        <footer className="border-t border-white/10 bg-black/30 px-4 py-4 backdrop-blur-md">
          <div className="mx-auto flex max-w-4xl flex-col gap-3 sm:flex-row sm:items-center sm:justify-between sm:gap-4">
            <div className="flex items-center justify-center gap-4 sm:justify-start">
              <button
                type="button"
                onClick={prev}
                className="flex items-center gap-1 rounded-lg border border-white/20 bg-white/5 px-4 py-2 text-sm text-white transition hover:bg-white/10"
                aria-label="Previous slide"
              >
                <ChevronLeft className="size-4" />
                Prev
              </button>
              <div className="flex gap-1.5">
                {SLIDES.map((_, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => setI(idx)}
                    className={cn(
                      "h-2 w-2 rounded-full transition",
                      idx === i ? "bg-[var(--primary)]" : "bg-white/30 hover:bg-white/50",
                    )}
                    aria-label={`Go to slide ${idx + 1}`}
                  />
                ))}
              </div>
              <button
                type="button"
                onClick={next}
                className="flex items-center gap-1 rounded-lg border border-white/20 bg-white/5 px-4 py-2 text-sm text-white transition hover:bg-white/10"
                aria-label="Next slide"
              >
                Next
                <ChevronRight className="size-4" />
              </button>
            </div>
            <div className="text-center font-mono text-[10px] leading-relaxed text-zinc-500 sm:max-w-md sm:text-left sm:text-xs">
              <p className="text-zinc-400">
                Upstream feedback — <span className="text-zinc-300">Subham</span> and team ship the metrics
                adoption / migration stack in{" "}
                <a
                  href={UPSTREAM_REPOS[0].repoUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-[var(--primary)] underline decoration-white/20 underline-offset-2 hover:decoration-[var(--primary)]"
                >
                  {UPSTREAM_REPOS[0].label}
                </a>
                ; open{" "}
                <a
                  href={UPSTREAM_REPOS[0].issuesUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-[var(--primary)] underline decoration-white/20 underline-offset-2 hover:decoration-[var(--primary)]"
                >
                  Issues
                </a>{" "}
                or{" "}
                <a
                  href={UPSTREAM_REPOS[0].pullsUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-[var(--primary)] underline decoration-white/20 underline-offset-2 hover:decoration-[var(--primary)]"
                >
                  PRs
                </a>
                . Compiler:{" "}
                <a
                  href={UPSTREAM_REPOS[1].repoUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-[var(--primary)] underline decoration-white/20 underline-offset-2 hover:decoration-[var(--primary)]"
                >
                  {UPSTREAM_REPOS[1].label}
                </a>{" "}
                (
                <a
                  href={UPSTREAM_REPOS[1].issuesUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-[var(--primary)] underline decoration-white/20 underline-offset-2 hover:decoration-[var(--primary)]"
                >
                  Issues
                </a>
                ,{" "}
                <a
                  href={UPSTREAM_REPOS[1].pullsUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-[var(--primary)] underline decoration-white/20 underline-offset-2 hover:decoration-[var(--primary)]"
                >
                  PRs
                </a>
                ).
              </p>
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
}
