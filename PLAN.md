# Autonomous Shorts Factory — Implementation Plan

## Context

Build a fully autonomous AI shorts pipeline from scratch in the empty directory `/Users/rahulupreti2/Desktop/reel.ai`, per the user's master spec: a LangGraph agent pipeline that runs daily at 08:00, finds a trending topic, writes a viral YouTube Shorts script with RAG, gates it with an LLM-as-judge (retry if hook score < 0.7), generates an ElevenLabs voiceover, fetches Pexels B-roll, assembles a 9:16 captioned video with MoviePy, and publishes to YouTube — with a FastAPI backend broadcasting live agent status over WebSockets to a React + Vite + Tailwind dashboard.

**User decisions (firm):**
- **LLM: Azure OpenAI** (not Claude as the spec body said). **Embeddings: a separate Azure OpenAI deployment with its own key and base URL** — config has two distinct env groups.
- **Vector DB: pgvector in Docker** (one Postgres for everything).
- **Publishing: dry-run first** — `PUBLISH_MODE=dry_run` default; full YouTube OAuth upload code built but inactive until creds exist.
- **Keys available now: Azure OpenAI + ElevenLabs only.** Tavily and Pexels get graceful fallbacks so the pipeline runs end-to-end without them.
- **Maximally modular structure** — small single-purpose modules; every external tool is a package of real-client / fallback / service-facade; prompts separated from logic; frontend separates state/transport/presentation.
- Use current stable package versions (the spec's mid-2024 pins have known breakages).

**Deliberate divergences from the spec (with rationale):**
- **No Redis** — the spec's `RedisSaver.from_conn_string` usage is broken in current langgraph anyway; v1 compiles the graph without a checkpointer (single linear daily run, no resume/HITL need). A `CHECKPOINTER=none|postgres` flag allows opting into `AsyncPostgresSaver` later, reusing the same Postgres. Cuts one Docker service.
- **Postgres full-text search instead of `rank_bm25`** for the sparse half of hybrid retrieval — fused with pgvector cosine via Reciprocal Rank Fusion in one SQL query; no in-memory index to keep in sync.
- **HNSW indexes instead of ivfflat** — ivfflat builds poor lists on near-empty tables.
- **Spec's graph.py bug fixed**: it called `add_conditional_edges` twice on the evaluator (invalid). Correct design: one conditional edge whose router returns a *list* for parallel fan-out, and `add_edge(["voice_generator","broll_selector"], "assembler")` for a proper join.
- **MoviePy 2.x API** throughout (`from moviepy import ...`, `.resized/.cropped/.subclipped/.with_audio/...`, `TextClip(font=<file path>, font_size=...)`) — no ImageMagick dependency.
- **Scheduler calls `run_pipeline()` in-process** instead of HTTP-POSTing to localhost.
- **Plain asyncpg pool** (no SQLAlchemy) with `pgvector.asyncpg.register_vector` in the pool init callback so vector columns round-trip properly.
- **ElevenLabs current SDK**: `AsyncElevenLabs().text_to_speech.convert(...)` (the spec's `client.generate()` was removed).

**Observability (three layers):**
1. **Live dashboard** — WS events per node (running/done/error, topic, script preview, eval scores, logs); `ws/registry.py` snapshot backs `GET /status` for mid-run reloads.
2. **Persistent run records** — `runs` table stores topic, scores, retry count, paths, errors, timings; surfaced via `GET /history` + HistoryTable.
3. **LangSmith tracing (user-confirmed)** — env-var driven (`LANGSMITH_TRACING=true`, `LANGSMITH_API_KEY`, `LANGSMITH_PROJECT=shorts-factory` — modern naming; the legacy `LANGCHAIN_*` aliases are the same thing); traces every LLM call and the retry loop automatically via LangChain/LangGraph. Gracefully off while the key is blank — same fallback pattern as Pexels/Tavily. Wrap non-LLM nodes with `@traceable` where useful.

## Folder structure (maximally modular)

```
reel.ai/
├── docker-compose.yml              # postgres (pgvector/pgvector:pg17) — single service
├── .env.example  .gitignore  README.md
│
├── backend/
│   ├── requirements.txt
│   ├── assets/fonts/               # caption .ttf (downloaded at scaffold)
│   └── app/
│       ├── main.py                 # create_app() factory — mounts routers only
│       ├── lifespan.py             # startup/shutdown: db pool, scheduler
│       ├── core/
│       │   ├── config.py           # Settings — dual Azure env groups, all flags
│       │   ├── llm.py              # get_chat_model() → AzureChatOpenAI
│       │   ├── embeddings.py       # get_embeddings() → AzureOpenAIEmbeddings
│       │   ├── logging.py
│       │   └── paths.py            # run_dir(run_id) output helpers
│       ├── api/routes/
│       │   ├── runs.py             # POST /run, GET /history, GET /runs/{id}
│       │   ├── status.py           # GET /status, GET /health
│       │   └── ws.py               # WS /ws endpoint
│       ├── ws/
│       │   ├── manager.py          # ConnectionManager (never raises)
│       │   ├── events.py           # typed event builders
│       │   └── registry.py         # RunStatusRegistry — /status snapshot
│       ├── scheduler/scheduler.py  # AsyncIOScheduler daily cron → runner
│       ├── db/
│       │   ├── pool.py             # asyncpg pool + register_vector init
│       │   ├── migrate.py          # python -m app.db.migrate ({EMBEDDING_DIM} substitution)
│       │   └── migrations/001_init.sql
│       ├── domain/models.py        # pydantic: Script, EvalResult, TrendCandidate,
│       │                           #   RetrievedDoc, PublishResult
│       ├── prompts/                # templates only — no logic
│       │   ├── script_writer.py
│       │   ├── evaluator.py        # judge rubric
│       │   └── trend_ranker.py
│       ├── pipeline/
│       │   ├── state.py            # PipelineState TypedDict + log/error reducers
│       │   ├── routing.py          # route_after_eval (retry vs parallel fan-out)
│       │   ├── graph.py            # wiring + compile
│       │   ├── runner.py           # run_pipeline() — shared by API + cron
│       │   └── nodes/
│       │       ├── base.py         # @pipeline_node decorator (broadcast + error capture)
│       │       ├── trend_scout.py  script_writer.py  evaluator.py
│       │       ├── voice_generator.py  broll_selector.py
│       │       └── assembler.py  publisher.py
│       ├── rag/
│       │   ├── retriever.py        # hybrid_search() — RRF over dense + FTS
│       │   ├── ingest.py           # python -m app.rag.ingest
│       │   └── seed/seed_hooks.json  # ~25 authored viral hooks
│       ├── memory/
│       │   ├── episodic.py         # runs CRUD
│       │   ├── semantic.py         # learnings, topic dedupe, channel history
│       │   └── procedural.py       # style profile
│       ├── evals/
│       │   ├── hook_scorer.py      # LLM-as-judge scoring
│       │   └── analytics_poll.py   # YT analytics poller (stub in dry-run)
│       └── tools/                  # each: real client + fallback + service facade
│           ├── trends/{tavily.py, google_trends.py, curated.py, service.py}
│           ├── broll/{pexels.py, generated.py, service.py}
│           ├── tts/{elevenlabs.py, silent.py, service.py}
│           ├── video/{captions.py, compositing.py, assembler.py}
│           └── publish/{youtube.py, dry_run.py, service.py}
│
├── frontend/
│   ├── package.json  vite.config.ts  tsconfig.json  index.html
│   └── src/
│       ├── main.tsx  App.tsx       # App = layout only; state lives in hooks
│       ├── api/{client.ts, ws.ts}  # REST wrappers / WS connection helper
│       ├── state/{types.ts, reducer.ts}  # WS event union + event→state reducer
│       ├── hooks/{useWebSocket.ts, useRunState.ts, useHistory.ts}
│       ├── lib/format.ts
│       └── components/
│           ├── layout/Topbar.tsx
│           ├── pipeline/{AgentPipeline,AgentRow,StatusBadge}.tsx
│           ├── topic/TopicCard.tsx
│           ├── scores/{ScorePanel,ScoreBar}.tsx
│           ├── logs/LiveLog.tsx
│           └── history/{HistoryTable,HistoryRow}.tsx
│
└── outputs/                        # gitignored: <run_id>/{voiceover.mp3, broll/, short.mp4,
                                    #   publish_metadata.json}
```

**Modularity rules enforced throughout:**
- API routes contain no business logic — they call `pipeline/runner.py` or `ws/registry.py`.
- Every external tool is a 3-file package: real client, fallback, and a `service.py` facade that picks between them (nodes import only the service).
- Prompts live in `prompts/` apart from node logic — tunable without touching flow.
- Video assembly splits caption timing (`captions.py`) from 9:16 compositing (`compositing.py`).
- Frontend separates state (`state/`), transport (`api/`), presentation (`components/`).

## Implementation phases

### Phase 0 — Scaffold
`git init`, directory tree with `__init__.py` files, `.gitignore` (`.env`, `outputs/`, `node_modules/`, `token.json`, `client_secret*.json`, media files). Download a bold OFL font (Anton) into `backend/assets/fonts/`; README documents `CAPTION_FONT_PATH` override if download fails.

### Phase 1 — Infra
- **docker-compose.yml**: single `postgres` service (`pgvector/pgvector:pg17`, healthcheck, volume).
- **app/db/migrations/001_init.sql**: tables `runs`, `viral_patterns` (with generated `tsv tsvector` column + GIN index), `learnings`, `channel_history`, `style_profile`; all embeddings `vector({EMBEDDING_DIM})` placeholder; HNSW cosine indexes; seed default style_profile rows.
- **app/db/migrate.py**: substitutes `{EMBEDDING_DIM}` from settings, executes idempotently.
- **app/core/config.py**: pydantic-settings with **two Azure groups** — `AZURE_OPENAI_CHAT_{ENDPOINT,API_KEY,DEPLOYMENT,API_VERSION}` and `AZURE_OPENAI_EMBEDDING_{ENDPOINT,API_KEY,DEPLOYMENT,API_VERSION}` — plus `has_tavily/has_pexels/has_youtube_creds` helpers. Client factories live in `core/llm.py` and `core/embeddings.py`.
- **requirements.txt** (pin-major, resolve latest at install): fastapi, uvicorn[standard], langgraph, langchain-openai, langchain-core, openai, asyncpg, pgvector, pydantic-settings, apscheduler<4, elevenlabs>=2, moviepy>=2.1, numpy, pillow, httpx, feedparser, tavily-python (guarded import), google-api-python-client, google-auth-oauthlib, imageio-ffmpeg (bundles ffmpeg).

### Phase 2 — DB layer
`app/db/pool.py`: asyncpg pool with `init=` callback calling `pgvector.asyncpg.register_vector(conn)` + jsonb codec. Pool lifecycle owned by `app/lifespan.py` and by standalone entrypoints (migrate/ingest).

### Phase 3 — Tools (each service never raises on missing keys; results tagged `source: "fallback"`)
- **tools/trends/** — `service.search_trends()`: `tavily.py` (guarded import) → `google_trends.py` (keyless RSS via httpx+feedparser) → `curated.py` (~15 static topics).
- **tools/broll/** — `service.fetch_broll(keywords, n, out_dir)`: `pexels.py` portrait search+download → `generated.py` 1080×1920 gradient clips (varied hue, slow zoom). Always returns ≥1 clip.
- **tools/tts/** — `service.synthesize(text, out_path)`: `elevenlabs.py` via `AsyncElevenLabs.text_to_speech.convert(voice_id, text, model_id, output_format="mp3_44100_128")` → `silent.py` silent track sized `words/2.5` seconds on failure.
- **tools/publish/** — `service.publish(...)`: `dry_run.py` writes `publish_metadata.json`, returns `youtube_id=None`; `youtube.py` installed-app OAuth flow (client_secret.json → cached token.json), resumable `videos().insert` in `to_thread`.
- **tools/video/** — sync `assembler.assemble(broll_paths, audio_path, script_text, out_path, font_path)` composing `compositing.py` (center-crop b-roll to 9:16, concat to audio duration) + `captions.py` (3–4-word `TextClip` chunks timed proportionally); `write_videofile(fps=30, libx264, aac)`. Called via `asyncio.to_thread` from the node. MoviePy 2.x API only.

### Phase 4 — RAG
- **app/domain/models.py**: `TrendCandidate`, `Script(hook, body, cta, full_text, title, keywords)`, `EvalResult(hook_score, retention_score, clarity_score, feedback, passed)`, `RetrievedDoc`, `PublishResult`.
- **app/rag/seed/seed_hooks.json**: ~25 authored viral hooks across categories (curiosity gap, contrarian, stat-shock, challenge, listicle, story-open) with `why_it_works`.
- **app/rag/ingest.py**: batch-embed via `aembed_documents`, idempotent upsert into `viral_patterns`.
- **app/rag/retriever.py**: `hybrid_search(query, k=5)` — single SQL with RRF over pgvector cosine + `ts_rank_cd` FTS; dense-only fallback when lexical empty.

### Phase 5 — Memory
- **episodic.py**: `create_run`, `update_run(run_id, **fields)`, `recent_runs(limit)`.
- **semantic.py**: `store_learning`, `recall_learnings`, `is_topic_recent(topic)` (cosine < 0.25 vs last-30-day `channel_history` — trend_scout dedupe), `record_published`.
- **procedural.py**: `get_style_profile` / `update_style_profile` (jsonb key-value).

### Phase 6 — Graph nodes
- **pipeline/state.py** — `PipelineState(TypedDict, total=False)` with `logs: Annotated[list[str], operator.add]` and `errors` reducers so parallel branches merge safely; branches otherwise write disjoint keys.
- **pipeline/nodes/base.py** — `@pipeline_node(name)` decorator: WS broadcast running/done/error (via `ws/events.py` builders), updates registry, captures exceptions into `errors` (re-raise only for fatal nodes).
- **trend_scout** → candidates from trends service, LLM-ranked via `prompts/trend_ranker.py`, `is_topic_recent` dedupe.
- **script_writer** → `hybrid_search` patterns + `recall_learnings` + style profile into `prompts/script_writer.py` template; **includes `eval_feedback` when `retry_count > 0`**; `with_structured_output(Script)`; ~130 words / 45–55s target.
- **evaluator** → `evals/hook_scorer.score()` (rubric from `prompts/evaluator.py`, `with_structured_output(EvalResult)`); increments `retry_count`; persists scores.
- **voice_generator** → tts service + measure `audio_duration`.
- **broll_selector** → keywords from `script.keywords` (no extra LLM call) → broll service.
- **assembler** → `asyncio.to_thread(assemble, ...)` → `outputs/<run_id>/short.mp4`.
- **publisher** → publish service (dry_run aware), `record_published` when live, finalize run row, broadcast `run_complete`.

### Phase 7 — Graph wiring (`pipeline/graph.py` + `pipeline/routing.py`)
```python
def route_after_eval(state):
    if state["eval_result"]["passed"] or state["retry_count"] >= settings.MAX_SCRIPT_RETRIES:
        return ["voice_generator", "broll_selector"]   # parallel fan-out
    return "script_writer"                             # retry with feedback

g.add_edge(START, "trend_scout"); g.add_edge("trend_scout", "script_writer")
g.add_edge("script_writer", "evaluator")
g.add_conditional_edges("evaluator", route_after_eval,
                        ["script_writer", "voice_generator", "broll_selector"])  # ONE call
g.add_edge(["voice_generator", "broll_selector"], "assembler")  # join waits for BOTH
g.add_edge("assembler", "publisher"); g.add_edge("publisher", END)
graph = g.compile()   # no checkpointer v1
```

### Phase 8 — FastAPI + WS + scheduler
- **ws/manager.py**: `broadcast` never raises (per-socket try/except, prune dead). **ws/registry.py**: current run, per-node status, scores, last 200 logs — backs `GET /status` snapshot for mid-run page reloads.
- **pipeline/runner.py**: `run_pipeline(trigger)` — concurrent-run guard (asyncio.Lock), `create_run`, `graph.ainvoke`, failure handling + broadcast.
- **scheduler/scheduler.py**: `AsyncIOScheduler` + `CronTrigger(hour, minute, timezone)` calling `run_pipeline("cron")` in-process; `SCHEDULER_ENABLED` flag.
- **main.py + lifespan.py**: app factory; lifespan inits pool → scheduler → teardown. Routes per `api/routes/`; CORS for `localhost:5173`; static-serve `outputs/` for dashboard video preview.

### Phase 9 — Frontend
- Vite react-ts scaffold + Tailwind v4 via `@tailwindcss/vite` plugin.
- `vite.config.ts` proxies `/api` and `/ws` (ws:true) to `localhost:8000` — components never hardcode the port.
- `api/ws.ts` + `hooks/useWebSocket.ts`: JSON events → `state/reducer.ts` dispatch, exponential-backoff reconnect (1s→10s) + `/api/status` rehydrate on reconnect.
- `state/types.ts`: discriminated union of WS events; `AGENTS` list of the 7 pipeline stages.
- Components: Topbar (run button, PUBLISH_MODE badge, connection dot), AgentPipeline/AgentRow/StatusBadge (idle/running/done/error + spinner), TopicCard (topic + source badge incl. fallback), ScorePanel/ScoreBar (3 bars + 0.7 threshold line + retry count), LiveLog (autoscroll), HistoryTable/HistoryRow (`/api/history`, links to rendered mp4s).
- Single reducer via `useRunState`; no state library.

### Phase 10 — Documentation (README.md + CLAUDE.md + PLAN.md)

**README.md** (project root) — full project documentation:
- **Three detailed ASCII architecture diagrams** (already drafted during planning — reproduce these):
  1. *System overview* — React dashboard ↔ FastAPI (WS + REST) ↔ APScheduler → LangGraph pipeline ↔ external services (dual Azure OpenAI, ElevenLabs, Pexels, Tavily, YouTube, LangSmith) ↔ Postgres/pgvector (5 tables mapped to memory types) ↔ outputs/ dir.
  2. *Agent pipeline flow* — 7 nodes with the evaluator retry loop (feedback → script_writer, max 2), parallel voice+broll fan-out, join at assembler, what each node reads/writes (viral_patterns, learnings, style_profile, channel_history), WS broadcast + LangSmith tracing annotations.
  3. *Learning loop timeline* — publish (day 1) → real views (days 1–3) → analytics poller distills learnings (day 3) → future scripts improve (day 4+); dormant in dry-run.
- Quickstart: docker compose → migrate → ingest → uvicorn → npm run dev → POST /run.
- Env setup with the **two separate Azure deployment groups** explained explicitly.
- Memory model explainer (episodic/semantic/procedural — what, when queried, example rows).
- Fallback matrix; dry-run → live publishing upgrade path (Google Cloud OAuth steps).
- Spec divergences with rationale (no Redis, HNSW, Postgres FTS, MoviePy 2.x).

**CLAUDE.md** (project root) — guide for future Claude Code sessions:
- One-paragraph project summary + condensed architecture (pipeline node order, retry/fan-out shape).
- Commands: run backend (`uvicorn app.main:app --port 8000` from `backend/`), frontend (`npm run dev`), migrate (`python -m app.db.migrate`), ingest (`python -m app.rag.ingest`), trigger run (`curl -X POST localhost:8000/run`), docker compose.
- Conventions: tools are 3-file packages (client/fallback/service — nodes import only `service.py`); prompts live in `app/prompts/`, never inline in nodes; API routes contain no business logic; MoviePy 2.x API only (no `.editor`, use `.resized/.with_audio/...`); all DB access via asyncpg pool in `app/db/pool.py`; WS broadcasts never raise.
- Gotchas: dual Azure env groups are separate deployments/keys — never share; `EMBEDDING_DIM` must match the embedding deployment (re-run migrate if changed); blocking work (render, upload) goes through `asyncio.to_thread`; `PUBLISH_MODE=dry_run` is the safe default.

**PLAN.md** — copy this plan file into the repo root for reference.

## .env.example (key variables)

```bash
AZURE_OPENAI_CHAT_ENDPOINT= / _API_KEY= / _DEPLOYMENT=gpt-4o / _API_VERSION=2024-10-21
AZURE_OPENAI_EMBEDDING_ENDPOINT= / _API_KEY= / _DEPLOYMENT=text-embedding-3-small / _API_VERSION=2024-10-21
EMBEDDING_DIM=1536                  # 3072 for -3-large; re-run migrate
ELEVENLABS_API_KEY= / ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM / ELEVENLABS_MODEL_ID=eleven_turbo_v2_5
TAVILY_API_KEY= / PEXELS_API_KEY=   # optional — fallbacks engage when blank
LANGSMITH_TRACING=true / LANGSMITH_API_KEY= / LANGSMITH_PROJECT=shorts-factory  # tracing off while key blank
YOUTUBE_CLIENT_SECRET_FILE=client_secret.json / YOUTUBE_TOKEN_FILE=token.json
PUBLISH_MODE=dry_run                # dry_run | live
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/shortsfactory
HOOK_SCORE_THRESHOLD=0.7 / MAX_SCRIPT_RETRIES=2 / TARGET_DURATION_SECONDS=50
NICHE=ai and technology / CAPTION_FONT_PATH=backend/assets/fonts/Anton-Regular.ttf
SCHEDULE_HOUR=8 / SCHEDULE_MINUTE=0 / TZ=Asia/Kolkata / SCHEDULER_ENABLED=true
CHECKPOINTER=none / OUTPUT_DIR=outputs
```

## Fallback matrix

| Missing | Behavior | UI signal |
|---|---|---|
| TAVILY_API_KEY | Google Trends RSS → curated topic list | TopicCard source badge |
| PEXELS_API_KEY | Generated gradient 9:16 clips | `broll_source: "generated"` log |
| YouTube creds / dry_run | Render locally + `publish_metadata.json`; no upload | DRY RUN badge |
| ElevenLabs API failure | Silent track @ words/2.5s; run continues | error log line |
| LANGSMITH_API_KEY | Tracing silently disabled; dashboard + DB records still full | none needed |

## Verification

1. `docker compose up -d` → healthy; `python -m app.db.migrate` → tables with vector(1536).
2. `python -m app.rag.ingest` → ~25 rows in `viral_patterns`; quick `hybrid_search("ai productivity")` smoke test (proves dual-endpoint embeddings + register_vector).
3. `uvicorn app.main:app --port 8000` with real Azure+ElevenLabs keys, Tavily/Pexels blank, dry_run.
4. `cd frontend && npm install && npm run dev` → dashboard at :5173.
5. `curl -X POST localhost:8000/run` → watch live: topic (fallback badge) → script → eval scores (observe retry loop if < 0.7) → voice + broll rows running **simultaneously** → assembler → publisher dry-run.
6. Assert `outputs/<run_id>/short.mp4` exists, is 1080×1920, has audio + burned captions; `publish_metadata.json` present; `runs` row completed.
7. Reload dashboard mid-run → `/status` snapshot rehydrates.

**Watch-outs during implementation:** verify the resolved langgraph version supports `add_edge(list, target)` join + list-returning router (present since 0.2, low risk); verify elevenlabs v2 convert chunk iteration; ffmpeg ships via imageio-ffmpeg (no brew install needed).
