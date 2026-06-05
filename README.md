# AI Brief Generator — Collabstr Take-Home

A minimal, production-minded Django app that generates influencer campaign briefs using Claude Haiku 4.5 (Anthropic).

## Live Demo

> [https://your-deployed-url.com](https://your-deployed-url.com)

---

## Setup

```bash
git clone https://github.com/YOUR_USERNAME/collabstr-brief
cd collabstr-brief
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add your ANTHROPIC_API_KEY
python manage.py runserver
```

Open `http://127.0.0.1:8000`.

---

## Prompt Design

### System prompt

A single, tightly-scoped paragraph telling the model it is a senior influencer marketing strategist. Key constraints:
- Match the brand's requested tone exactly.
- Be specific to the platform — TikTok copy ≠ Instagram copy.
- No generic filler. Every sentence must add tactical value.

### User prompt

A compact, structured block of four key-value lines (`Brand`, `Platform`, `Goal`, `Tone`) followed by an explicit instruction to produce exactly 3 angles and 3 criteria. Compact prompts cost fewer tokens and produce more predictable output than verbose instructions.

### Why temperature 0.4?

The brief is a professional deliverable. We want consistent, reliable output with just enough creativity to avoid robotic repetition. Anything above 0.5 risks off-brand tone drift.

---

## Guardrails

| Guardrail | Implementation |
|---|---|
| **Input validation** | Server-side allowlist for `platform`, `goal`, `tone`; `brand` length cap of 100 chars |
| **Profanity filter** | `better-profanity` checks the brand name field before any LLM call |
| **Structured output** | OpenAI JSON Schema response format — model is forced to return `brief`, `angles[]`, `criteria[]` with exact cardinality; no post-processing guesswork |
| **Max tokens** | Hard cap of 600 completion tokens; brief output fits well within ~300 |
| **Temperature** | Set to 0.4 (≤ 0.5 as required) |
| **Rate limiting** | IP-based counter in Django's in-memory cache: 10 requests / 60 seconds per IP |
| **Error handling** | LLM failures return a 502 with a user-friendly message; never expose raw exceptions |

---

## Token & Latency Telemetry

Every API response includes a `meta` object:

```json
{
  "meta": {
    "latency_ms": 842,
    "prompt_tokens": 174,
    "completion_tokens": 231,
    "total_tokens": 405
  }
}
```

- **Latency** — measured with `time.perf_counter()` around the OpenAI call, reported in milliseconds.
- **Tokens** — read directly from `response.usage` (OpenAI SDK). Prompt + completion tokens are reported separately so cost can be calculated per model pricing.
- The frontend renders these as small chips below the generated brief, giving full visibility without cluttering the UI.

---

## Code Organisation

```
brief/
  views.py          ← HTTP layer: validation, rate-limit, error handling
  services/
    llm.py          ← All LLM logic: prompt building, API call, result dataclass
templates/brief/
  index.html        ← Single-page UI
static/
  css/main.css      ← Design tokens + component styles
  js/main.js        ← jQuery AJAX, render, copy, toast
```

---

## Deploy (Railway / Render)

1. Set env vars: `DJANGO_SECRET_KEY`, `OPENAI_API_KEY`, `ALLOWED_HOSTS`, `DEBUG=False`
2. Add `whitenoise` middleware for static files (already in `requirements.txt`)
3. Start command: `gunicorn config.wsgi:application`
