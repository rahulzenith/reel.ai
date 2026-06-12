# Shorts Factory — Claude Code guide

Autonomous YouTube Shorts pipeline: a LangGraph agent graph (trend scout → script
writer → LLM-judge evaluator → parallel voice+b-roll → MoviePy assembler →
publisher) runs daily at 08:00 via APScheduler, broadcasting live status over
WebSockets to a React dashboard. Azure OpenAI powers chat + embeddings (two
separate deployments), Postgres+pgvector holds all memory/RAG tables.

## Commands

All backend commands run from `backend/` using the venv (`.venv/bin/python`, Python 3.13):

```bash
docker compose up -d                       # start Postgres+pgvector (from repo root)
.venv/bin/python -m app.db.migrate         # apply migrations (idempotent)
.venv/bin/python -m app.rag.ingest         # seed viral_patterns (idempotent)
.venv/bin/uvicorn app.main:app --port 8000 # start backend
curl -X POST localhost:8000/api/run        # trigger a pipeline run
```

Frontend (from `frontend/`): `npm run dev` → http://localhost:5173 (proxies /api, /ws, /outputs to :8000).

## Architecture map

- `app/pipeline/graph.py` — graph wiring. ONE conditional edge after evaluator
  (retry vs fan-out list); `add_edge([voice, broll], assembler)` is the join.
- `app/pipeline/routing.py` — retry_count includes the first attempt, so the
  proceed threshold is `max_script_retries + 1`.
- `app/ws/events.py` — every pipeline broadcast goes through `emit()`, which
  updates the `/api/status` registry AND broadcasts. Never call manager.broadcast directly.
- `app/tools/*/service.py` — fallback facades. Nodes import ONLY service.py,
  never the underlying clients.

## Conventions

- Every external tool is a 3-file package: real client / fallback / `service.py`
  facade that never raises on missing keys (returns a `source` tag instead).
- Prompts live in `app/prompts/` — templates only, no logic. Nodes format them.
- API routes contain no business logic; they call `pipeline/runner.py` or `ws/registry.py`.
- All DB access via the asyncpg pool (`app/db/pool.py`) — no SQLAlchemy. The pool's
  init callback registers pgvector + jsonb codecs; without it vectors come back as strings.
- MoviePy 2.x API ONLY: `from moviepy import ...` (no `.editor`), `.resized/.cropped/
  .subclipped/.with_audio/.with_duration/.with_position`, `TextClip(font=<file path>, font_size=...)`.
- LLM structured output via `.with_structured_output(PydanticModel)` — no manual JSON parsing.
- Blocking work (MoviePy render, audio measurement, YouTube upload) goes through `asyncio.to_thread`.

## Gotchas

- The two Azure env groups (`AZURE_OPENAI_CHAT_*`, `AZURE_OPENAI_EMBEDDING_*`) are
  separate deployments with separate keys/endpoints — never share one across both.
- `EMBEDDING_DIM` must match the embedding deployment (1536 for 3-small, 3072 for
  3-large). Changing it requires re-running migrate against a fresh DB (or ALTERing
  the vector columns) and re-ingesting.
- `PUBLISH_MODE=dry_run` is the safe default — publisher writes publish_metadata.json
  instead of uploading. Live mode needs client_secret.json + one-time browser OAuth.
- Topic dedup records dry-run topics too (intentional — dedup works before going live).
- The system Python is 3.9 — too old. Use the venv (built from Homebrew python3.13).
- macOS: use `open -a Docker` if the Docker daemon isn't running.
