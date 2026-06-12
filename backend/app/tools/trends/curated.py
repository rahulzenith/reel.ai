"""Last-resort topic source: curated evergreen topics for the channel niche."""
import random

from ...domain.models import TrendCandidate

CURATED_TOPICS = [
    "AI tools that save hours of work every week",
    "How AI agents are replacing repetitive office tasks",
    "The skill that matters more than coding in the AI era",
    "What happens when you let AI plan your entire day",
    "Free AI tools most people have never heard of",
    "How small businesses are quietly using AI to win",
    "The biggest mistake people make when using ChatGPT",
    "AI features hidden inside apps you already use",
    "Why prompt engineering is becoming a real job skill",
    "How students are using AI to learn twice as fast",
    "The AI privacy settings you should change today",
    "What AI still can't do — and why that matters",
    "How to spot AI-generated content in seconds",
    "The one AI workflow that changed how I work",
    "Jobs AI will create that don't exist yet",
]


def get_curated_candidates(n: int = 5) -> list[TrendCandidate]:
    picks = random.sample(CURATED_TOPICS, min(n, len(CURATED_TOPICS)))
    return [TrendCandidate(title=t, source="curated", score=0.5) for t in picks]
