from pydantic import BaseModel, Field


class TrendCandidate(BaseModel):
    title: str
    url: str = ""
    snippet: str = ""
    source: str = "curated"  # tavily | google-trends | curated
    score: float = 0.5


class Script(BaseModel):
    """Structured output target for the script writer LLM call."""

    hook: str = Field(description="Opening 1-2 sentences — a pattern interrupt that stops the scroll")
    body: str = Field(description="3-5 punchy sentences delivering the core content")
    cta: str = Field(description="One-sentence soft call to action")
    full_text: str = Field(description="hook + body + cta combined, as it will be spoken")
    title: str = Field(description="YouTube title, max 90 chars, includes #Shorts")
    keywords: list[str] = Field(description="3-4 visual search keywords for stock B-roll footage")


class EvalResult(BaseModel):
    """Structured output target for the LLM-as-judge."""

    hook_score: float = Field(ge=0, le=1, description="Does the hook create immediate curiosity or tension?")
    retention_score: float = Field(ge=0, le=1, description="Will viewers stay to the end?")
    clarity_score: float = Field(ge=0, le=1, description="Easy to follow at speaking pace?")
    feedback: str = Field(description="One sentence on the weakest point and how to fix it")


class RetrievedDoc(BaseModel):
    hook_text: str
    category: str = ""
    why_it_works: str = ""
    score: float = 0.0


class PublishResult(BaseModel):
    youtube_id: str | None = None
    url: str | None = None
    dry_run: bool = True
    metadata: dict = {}
