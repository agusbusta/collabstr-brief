# AI Brief Generator — Collabstr

A Django app that takes four campaign inputs and returns a production-ready brief, content angles, and creator criteria — all structured via Claude's tool-use API.

**Live demo:** https://collabstr-brief.onrender.com

---

## Running locally

```bash
git clone https://github.com/agusbusta/collabstr-brief
cd collabstr-brief
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # paste your ANTHROPIC_API_KEY
python manage.py runserver
```

Open `http://127.0.0.1:8000`.

---

## Prompt design

I kept both prompts short on purpose. The system prompt is one tight paragraph establishing the persona (senior influencer strategist) and two hard rules: match the tone exactly, and never use filler. Verbose system prompts tend to dilute the model's focus.

The user prompt is four key-value lines plus one instruction. That's it. I found that explicit enumeration ("Brand: X, Platform: Y") reduces hallucination more than prose descriptions, especially for short-context models.

Temperature is 0.4 — low enough for consistent, on-brand output, with just enough variance to avoid robotic repetition across runs.

---

## Structured output

I used Anthropic's **tool-use** (function-call) mode with a forced `tool_choice`. This guarantees the response is always `{ brief, angles[], criteria[] }` — no regex parsing, no fallback logic. If the schema is violated the SDK raises before we ever touch the data.

I went back and forth on whether to just ask for JSON in the prompt, but tool-use is strictly more reliable, especially for array cardinality (always exactly 3 items).

---

## Guardrails

| What | How |
|---|---|
| Input allowlist | `platform`, `goal`, `tone` validated server-side against a fixed set |
| Brand name | Max 100 chars, profanity check via `better-profanity` |
| Max tokens | Hard cap of 600 — typical output is ~350 |
| Temperature | 0.4 (under the 0.5 requirement) |
| Rate limiting | 10 req / 60 s per IP, using Django's in-memory cache |
| LLM errors | Caught and returned as a user-friendly 502 — raw exceptions never leak |

---

## Telemetry

Every response includes a `meta` block:

```json
{
  "meta": {
    "latency_ms": 820,
    "prompt_tokens": 867,
    "completion_tokens": 392,
    "total_tokens": 1259
  }
}
```

Latency is `time.perf_counter()` around the API call. Tokens come straight from `response.usage`. I surface both prompt and completion tokens separately because they have different costs — useful if you want to add a cost calculator later.

---

## Code layout

```
brief/
  views.py          ← HTTP: validation, rate-limit, error handling
  services/llm.py   ← LLM: prompt, API call, result dataclass
templates/brief/
  index.html
static/
  css/main.css
  js/main.js
```

The split between `views.py` and `services/llm.py` makes the LLM logic independently testable — you can mock `generate_brief()` in unit tests without spinning up a Django request.

---

## Deploy

Railway (or Render). Set `ANTHROPIC_API_KEY`, `DJANGO_SECRET_KEY`, `ALLOWED_HOSTS`, `DEBUG=False`. Start command: `gunicorn config.wsgi:application`.
