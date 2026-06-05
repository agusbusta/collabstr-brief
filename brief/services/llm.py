"""LLM orchestration: prompt design, structured output, and telemetry."""

import time
import logging
from dataclasses import dataclass

import anthropic
from django.conf import settings

logger = logging.getLogger(__name__)

MODEL = "claude-haiku-4-5-20251001"

SYSTEM_PROMPT = """You are a senior influencer marketing strategist at a top creator economy agency.
You write precise, actionable campaign briefs. Your tone matches the brand's requested tone exactly.
Output must be concise, specific to the platform, and immediately usable by a creator or talent manager.
Never use generic filler phrases. Every sentence must add tactical value."""

BRIEF_TOOL = {
    "name": "campaign_brief",
    "description": "Return a structured influencer campaign brief",
    "input_schema": {
        "type": "object",
        "properties": {
            "brief": {
                "type": "string",
                "description": "4-6 sentence campaign brief tailored to the inputs",
            },
            "angles": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Exactly 3 content angle suggestions",
            },
            "criteria": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Exactly 3 creator selection criteria bullets",
            },
        },
        "required": ["brief", "angles", "criteria"],
    },
}


@dataclass
class BriefResult:
    brief: str
    angles: list
    criteria: list
    latency_ms: int
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


def build_user_prompt(brand: str, platform: str, goal: str, tone: str) -> str:
    return (
        f"Brand: {brand}\n"
        f"Platform: {platform}\n"
        f"Campaign goal: {goal}\n"
        f"Tone: {tone}\n\n"
        "Generate a campaign brief with exactly 3 content angles and 3 creator selection criteria."
    )


def generate_brief(brand: str, platform: str, goal: str, tone: str) -> BriefResult:
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    user_prompt = build_user_prompt(brand, platform, goal, tone)

    start = time.perf_counter()
    response = client.messages.create(
        model=MODEL,
        max_tokens=600,
        temperature=0.4,
        system=SYSTEM_PROMPT,
        tools=[BRIEF_TOOL],
        tool_choice={"type": "tool", "name": "campaign_brief"},
        messages=[{"role": "user", "content": user_prompt}],
    )
    latency_ms = int((time.perf_counter() - start) * 1000)

    tool_block = next(b for b in response.content if b.type == "tool_use")
    data = tool_block.input

    usage = response.usage
    prompt_tokens = usage.input_tokens
    completion_tokens = usage.output_tokens
    return BriefResult(
        brief=data["brief"],
        angles=data["angles"],
        criteria=data["criteria"],
        latency_ms=latency_ms,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens,
    )
