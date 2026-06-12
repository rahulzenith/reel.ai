CREATE EXTENSION IF NOT EXISTS vector;

-- ─────────────────────────────────────────────────────────────────────────────
-- Episodic memory: one row per pipeline run
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS runs (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  started_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  finished_at     TIMESTAMPTZ,
  status          TEXT NOT NULL DEFAULT 'running',  -- running | completed | failed
  trigger         TEXT,                              -- manual | cron
  topic           TEXT,
  topic_source    TEXT,                              -- tavily | google-trends | curated
  script          JSONB,
  hook_score      FLOAT,
  retention_score FLOAT,
  clarity_score   FLOAT,
  eval_feedback   TEXT,
  retry_count     INTEGER DEFAULT 0,
  video_path      TEXT,
  youtube_id      TEXT,
  youtube_url     TEXT,
  publish_mode    TEXT,
  ctr_48h         FLOAT,
  avg_view_pct    FLOAT,
  error           TEXT,
  meta            JSONB
);

CREATE INDEX IF NOT EXISTS runs_started_at_idx ON runs (started_at DESC);

-- ─────────────────────────────────────────────────────────────────────────────
-- RAG: viral hook patterns library (seeded from rag/seed/seed_hooks.json)
-- tsv column powers the lexical half of hybrid retrieval (no rank_bm25 needed)
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS viral_patterns (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  hook_text     TEXT NOT NULL UNIQUE,
  category      TEXT,
  why_it_works  TEXT,
  source        TEXT DEFAULT 'seed',
  embedding     vector({EMBEDDING_DIM}),
  tsv           tsvector GENERATED ALWAYS AS
                  (to_tsvector('english', hook_text || ' ' || coalesce(why_it_works, ''))) STORED,
  created_at    TIMESTAMPTZ DEFAULT now()
);

-- HNSW over ivfflat: works well from row one (ivfflat builds poor lists on small tables)
CREATE INDEX IF NOT EXISTS viral_patterns_embedding_idx
  ON viral_patterns USING hnsw (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS viral_patterns_tsv_idx
  ON viral_patterns USING gin (tsv);

-- ─────────────────────────────────────────────────────────────────────────────
-- Semantic memory: generalized learnings distilled from real performance
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS learnings (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id      UUID REFERENCES runs(id),
  learning    TEXT NOT NULL,
  kind        TEXT DEFAULT 'analytics',   -- analytics | manual | reflection
  embedding   vector({EMBEDDING_DIM}),
  created_at  TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS learnings_embedding_idx
  ON learnings USING hnsw (embedding vector_cosine_ops);

-- ─────────────────────────────────────────────────────────────────────────────
-- Semantic memory: published-topic record — powers 30-day topic dedup
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS channel_history (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  topic         TEXT NOT NULL,
  title         TEXT,
  youtube_id    TEXT,
  publish_mode  TEXT,
  embedding     vector({EMBEDDING_DIM}),
  published_at  TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS channel_history_embedding_idx
  ON channel_history USING hnsw (embedding vector_cosine_ops);

-- ─────────────────────────────────────────────────────────────────────────────
-- Procedural memory: the channel's standing rules (key-value jsonb)
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS style_profile (
  key         TEXT PRIMARY KEY,
  value       JSONB NOT NULL,
  updated_at  TIMESTAMPTZ DEFAULT now()
);

INSERT INTO style_profile (key, value) VALUES
  ('tone',        '"casual, energetic, conversational — no corporate jargon"'),
  ('pacing',      '"~2.5 words per second; short punchy sentences"'),
  ('cta_style',   '"soft ask only: follow for more, save this, comment your take — never beg"'),
  ('banned',      '["clickbait words like SHOCKING", "crypto shilling", "politics"]')
ON CONFLICT (key) DO NOTHING;
