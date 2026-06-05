"""LLM orchestration: prompt design, structured output, and telemetry."""

import time
import json
import logging
from dataclasses import dataclass

from groq import Groq
from django.conf import settings

logger = logging.getLogger(__name__)

# Fast and capable; swap to llama-3.3-70b-versatile for heavier tasks
MODEL = "llama-3.1-8b-instant"

SYSTEM_PROMPT = """You are a senior influencer marketing strategist at a top creator economy agency.
You write precise, actionable campaign briefs. Your tone matches the brand's requested tone exactly.
Output must be concise, specific to the platform, and immediately usable by a creator or talent manager.
Never use generic filler phrases. Every sentence must add tactical value."""

BRIEF_TOOL = {
    "type": "function",
    "function": {
        "name": "campaign_brief",
        "description": "Return a structured influencer campaign brief",
        "parameters": {
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
    client = Groq(api_key=settings.GROQ_API_KEY)
    user_prompt = build_user_prompt(brand, platform, goal, tone)

    start = time.perf_counter()
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        tools=[BRIEF_TOOL],
        tool_choice={"type": "function", "function": {"name": "campaign_brief"}},
        temperature=0.4,
        max_tokens=600,
    )
    latency_ms = int((time.perf_counter() - start) * 1000)

    tool_call = response.choices[0].message.tool_calls[0]
    data = json.loads(tool_call.function.arguments)

    usage = response.usage
    prompt_tokens = usage.prompt_tokens
    completion_tokens = usage.completion_tokens
    return BriefResult(
        brief=data["brief"],
        angles=data["angles"],
        criteria=data["criteria"],
        latency_ms=latency_ms,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens,
    )
