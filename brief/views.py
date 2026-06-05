import logging
from typing import Optional
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
from better_profanity import profanity

from .services.llm import generate_brief

logger = logging.getLogger(__name__)

VALID_PLATFORMS = {"Instagram", "TikTok", "UGC"}
VALID_GOALS = {"Awareness", "Conversions", "Content Assets"}
VALID_TONES = {"Professional", "Friendly", "Playful"}

RATE_LIMIT_KEY = "brief_rate_{ip}"
RATE_LIMIT_MAX = 10
RATE_LIMIT_TTL = 60  # seconds


def index(request):
    return render(request, "brief/index.html")


@csrf_exempt
@require_POST
def generate(request):
    ip = _get_client_ip(request)
    if _is_rate_limited(ip):
        return JsonResponse({"error": "Too many requests. Please wait a moment and try again."}, status=429)

    brand = request.POST.get("brand", "").strip()
    platform = request.POST.get("platform", "").strip()
    goal = request.POST.get("goal", "").strip()
    tone = request.POST.get("tone", "").strip()

    errors = _validate_inputs(brand, platform, goal, tone)
    if errors:
        return JsonResponse({"error": errors}, status=400)

    try:
        result = generate_brief(brand=brand, platform=platform, goal=goal, tone=tone)
    except Exception as exc:
        logger.exception("LLM call failed: %s", exc)
        return JsonResponse({"error": "The AI service is temporarily unavailable. Please try again."}, status=502)

    return JsonResponse({
        "brief": result.brief,
        "angles": result.angles,
        "criteria": result.criteria,
        "meta": {
            "latency_ms": result.latency_ms,
            "prompt_tokens": result.prompt_tokens,
            "completion_tokens": result.completion_tokens,
            "total_tokens": result.total_tokens,
        },
    })


def _validate_inputs(brand: str, platform: str, goal: str, tone: str) -> Optional[str]:
    if not brand:
        return "Brand name is required."
    if len(brand) > 100:
        return "Brand name must be under 100 characters."
    if profanity.contains_profanity(brand):
        return "Brand name contains inappropriate content."
    if platform not in VALID_PLATFORMS:
        return f"Platform must be one of: {', '.join(VALID_PLATFORMS)}."
    if goal not in VALID_GOALS:
        return f"Goal must be one of: {', '.join(VALID_GOALS)}."
    if tone not in VALID_TONES:
        return f"Tone must be one of: {', '.join(VALID_TONES)}."
    return None


def _get_client_ip(request) -> str:
    x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded:
        return x_forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")


def _is_rate_limited(ip: str) -> bool:
    key = RATE_LIMIT_KEY.format(ip=ip)
    count = cache.get(key, 0)
    if count >= RATE_LIMIT_MAX:
        return True
    cache.set(key, count + 1, RATE_LIMIT_TTL)
    return False
