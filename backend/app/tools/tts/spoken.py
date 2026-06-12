"""Build the TTS transcript: clean script text plus <break> pauses between
sections so beat changes breathe instead of landing abruptly.

Both Cartesia (sonic) and ElevenLabs honor <break time="..."/> tags. Captions
never see this text — they render from the script's clean full_text.
"""
import re

SECTION_BREAK = '<break time="0.4s" />'


def build_spoken_text(script: dict) -> str:
    sections = [script.get("hook", ""), script.get("body", ""), script.get("cta", "")]
    sections = [s.strip() for s in sections if s and s.strip()]
    if not sections:
        return script.get("full_text", "")
    return f" {SECTION_BREAK} ".join(sections)


def strip_break_tags(text: str) -> str:
    return re.sub(r"<break[^>]*/>", " ", text)
