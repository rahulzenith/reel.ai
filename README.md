# Shorts Factory

A fully autonomous AI shorts pipeline. Every day at 08:00 it finds a trending
topic, writes a viral-style script with RAG, gates it through an LLM judge,
generates a voiceover, assembles a 9:16 captioned video, and publishes to
YouTube Shorts — while a React dashboard shows every agent working live.

## System overview

```
                                  ┌─────────────────────────────────────────┐
                                  │            EXTERNAL SERVICES            │
                                  │                                         │
                                  │  Azure OpenAI (chat)   Azure OpenAI     │
                                  │  gpt-4o                (embeddings)     │
                                  │       ▲                     ▲           │
                                  │  ElevenLabs   Pexels   Tavily/Trends    │
                                  │  (voice)      (b-roll) (topics)         │
                                  │       ▲          ▲          ▲           │
                                  │  YouTube API  LangSmith                 │
                                  │  (publish)    (tracing)                 │
                                  └───────┼──────────┼──────────┼───────────┘
                                          │          │          │
┌──────────────┐   WebSocket   ┌──────────┴──────────┴──────────┴───────────┐
│   REACT      │ ◄════════════ │              FASTAPI BACKEND                │
│   DASHBOARD  │  live events  │                                             │
│  (Vite:5173) │               │  ┌─────────────┐      ┌──────────────────┐  │
│              │   REST        │  │  APScheduler │────► │ LANGGRAPH        │  │
│  AgentRows   │ ────────────► │  │  daily 08:00 │      │ PIPELINE         │  │
│  ScorePanel  │  POST /run    │  └─────────────┘      │ (7 agent nodes)  │  │
│  LiveLog     │  GET /status  │         ▲             └────────┬─────────┘  │
│  History     │  GET /history │         │                      │            │
└──────────────┘               │   manual trigger        reads/writes        │
                               └─────────────────────────────┼───────────────┘
                                                             ▼
                               ┌─────────────────────────────────────────────┐
                               │       POSTGRES + PGVECTOR (Docker)          │
                               │                                             │
                               │  runs            ← episodic memory          │
                               │  learnings       ← semantic memory          │
                               │  channel_history ← topic dedup (vector)     │
                               │  viral_patterns  ← RAG hook library         │
                               │  style_profile   ← procedural memory        │
                               └─────────────────────────────────────────────┘
                                                             │
                                                  ┌──────────┴──────────┐
                                                  │  outputs/<run_id>/  │
                                                  │  voiceover.mp3      │
                                                  │  broll/clip_*.mp4   │
                                                  │  short.mp4   ◄──── final video
                                                  │  publish_metadata.json
                                                  └─────────────────────┘
```

## The agent pipeline

```
                              START (08:00 cron or POST /api/run)
                                │
                                ▼
                    ┌───────────────────────┐
                    │  1. TREND SCOUT       │  Tavily → Google Trends RSS → curated list
                    │                       │  LLM ranks candidates
                    │  reads: channel_history ──── skips topics covered in last 30 days
                    └───────────┬───────────┘
                                │ selected topic
                                ▼
                    ┌───────────────────────┐
              ┌───► │  2. SCRIPT WRITER     │  reads: viral_patterns (RAG hybrid search)
              │     │                       │         learnings (top-3 by similarity)
              │     │                       │         style_profile (always)
              │     └───────────┬───────────┘         eval feedback (on retry only)
              │                 │ script {hook, body, cta}
   retry      │                 ▼
   with       │     ┌───────────────────────┐
   feedback   │     │  3. EVALUATOR         │  LLM-as-judge rubric:
              │     │     (quality gate)    │  hook ≥ 0.7? retention? clarity?
              │     └───────────┬───────────┘
              │                 │
              └──── hook < 0.7 AND retries left
                                │ passed (or retries exhausted)
                ┌───────────────┴────────────────┐
                ▼         RUNS IN PARALLEL        ▼
   ┌───────────────────────┐         ┌───────────────────────┐
   │  4. VOICE GENERATOR   │         │  5. B-ROLL SELECTOR   │
   │  ElevenLabs TTS       │         │  Pexels portrait clips│
   │  fallback: silent trk │         │  fallback: gradients  │
   └───────────┬───────────┘         └───────────┬───────────┘
               │ voiceover.mp3                   │ clip_0..n.mp4
               └───────────────┬─────────────────┘
                               ▼  JOIN — waits for BOTH
                   ┌───────────────────────┐
                   │  6. ASSEMBLER         │  MoviePy: crop b-roll to 9:16,
                   │                       │  concat to audio length,
                   │                       │  burn timed captions (3-4 words)
                   └───────────┬───────────┘
                               │ short.mp4 (1080x1920)
                               ▼
                   ┌───────────────────────┐
                   │  7. PUBLISHER         │  dry_run: save metadata locally
                   │                       │  live: YouTube OAuth upload
                   │  writes: runs (episodic), channel_history (dedup)
                   └───────────┬───────────┘
                               ▼
                              END
        every node ──── broadcasts status over WebSocket ────► dashboard
        every LLM call ──── traced ────► LangSmith (when key configured)
```

## The learning loop

```
  Day 1, 08:00          Day 1-3                Day 3, poll             Day 4+, 08:00
┌─────────────┐    ┌────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│ pipeline    │    │ video collects │    │ ANALYTICS POLLER │    │ next runs read   │
│ publishes   │───►│ real views on  │───►│ fetches CTR,     │───►│ learnings in     │
│ video       │    │ YouTube        │    │ watch-time;      │    │ script prompts   │
│             │    │                │    │ distills insight │    │                  │
│ writes:     │    │                │    │ writes:          │    │ scripts improve  │
│ runs row    │    │                │    │ learnings table  │    │ from REAL data   │
│ channel_hist│    │                │    │                  │    │                  │
└─────────────┘    └────────────────┘    └──────────────────┘    └──────────────────┘
     episodic                                  semantic                feedback loop
                        (dormant in dry-run mode — activates when publishing goes live)
```

## Quickstart

Prerequisites: Docker Desktop, Python 3.11+ (Homebrew `python3.13` recommended), Node 18+.

```bash
# 1. Infrastructure
docker compose up -d

# 2. Backend setup
cd backend
python3.13 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp ../.env.example .env            # then fill in your keys (see below)
.venv/bin/python -m app.db.migrate
.venv/bin/python -m app.rag.ingest # seeds the viral hook library

# 3. Start backend
.venv/bin/uvicorn app.main:app --port 8000

# 4. Frontend (new terminal)
cd frontend
npm install
npm run dev                        # → http://localhost:5173

# 5. Trigger a run
curl -X POST localhost:8000/api/run   # or click "Run now" on the dashboard
```

## Environment keys

**The two Azure groups are separate deployments with separate keys and endpoints
— don't reuse one for the other:**

| Group | Variables | Notes |
|---|---|---|
| Azure chat | `AZURE_OPENAI_CHAT_{ENDPOINT,API_KEY,DEPLOYMENT,API_VERSION}` | e.g. a gpt-4o deployment |
| Azure embeddings | `AZURE_OPENAI_EMBEDDING_{ENDPOINT,API_KEY,DEPLOYMENT,API_VERSION}` + `EMBEDDING_DIM` | 1536 for text-embedding-3-small |
| ElevenLabs | `ELEVENLABS_API_KEY`, `ELEVENLABS_VOICE_ID`, `ELEVENLABS_MODEL_ID` | required for real voiceover |

Optional — everything degrades gracefully when blank:

| Missing | Behavior | UI signal |
|---|---|---|
| `TAVILY_API_KEY` | Google Trends RSS (keyless) → curated topic list | topic source badge |
| `PEXELS_API_KEY` | Generated 9:16 gradient clips | "generated" in log |
| YouTube creds / dry_run | Video renders locally + `publish_metadata.json`, no upload | DRY RUN badge |
| `LANGSMITH_API_KEY` | Tracing silently off | none |
| ElevenLabs API failure | Silent track at words/2.5s, run continues | log line |

## Memory model

| Memory | Table | Holds | Accessed |
|---|---|---|---|
| Episodic | `runs` | What happened each run (topic, script, scores, outcome) | Exact lookup by id/date — dashboard, poller |
| Semantic | `learnings`, `channel_history` | Lessons from real performance; published topics | Vector similarity — script prompts, topic dedup |
| Procedural | `style_profile` | The channel's standing rules (tone, CTA style, banned topics) | Loaded fully into every script prompt |

The loop: runs accumulate (episodic) → analytics distill lessons (semantic) →
proven lessons get promoted to standing rules (procedural).

## Going live on YouTube

1. Create a Google Cloud project → enable **YouTube Data API v3**.
2. Create an OAuth client (Desktop app) → download as `backend/client_secret.json`.
3. Set `PUBLISH_MODE=live` in `backend/.env`.
4. The first live publish opens a one-time browser consent; the token is cached
   to `token.json` after that.
5. The analytics poller (`app/evals/analytics_poll.py`) starts finding published
   videos automatically; implement its YouTube Analytics call to close the
   learning loop (TODO marked in the file).

## Design divergences from the original spec

- **No Redis** — a single daily linear run needs no checkpointer; one fewer service.
- **Postgres FTS instead of rank_bm25** — the sparse half of hybrid retrieval is
  a `tsvector` column fused with pgvector cosine via Reciprocal Rank Fusion in one query.
- **HNSW instead of ivfflat** — works well from row one on small tables.
- **MoviePy 2.x** — no ImageMagick dependency for captions.
- **Scheduler calls the pipeline in-process** — no self-HTTP.
