# HELM Decision Engine & Intelligence Pipeline

This document describes how HELM turns a user message into a grounded,
deterministic answer — the "policy-first, AI-assisted" decision path. It is the
authoritative reference for the intelligence pipeline, the intent taxonomy, the
universal decision engine, and the honesty rules the product commits to.

> **Guiding principle — no mock data, ever.** HELM never fabricates numbers,
> venues, drivers, fares, or capabilities. When it lacks a data source it says
> so plainly and offers what it genuinely can do. Every recommendation traces
> back to real signals (the user's scores, finances, health, and memory).

---

## 1. Two decision layers

A chat message (`/history/generate` → `GeminiService.generate_response`) is
handled by two deterministic layers, in order:

1. **Orchestrator** (`backend/orchestration/`) — a tool-first layer that owns
   **MOBILITY** only. If it can satisfy the request deterministically it returns
   the answer; otherwise it declines (`is_orchestrator=False`) and the message
   falls through to the pipeline.
2. **Intelligence Pipeline** (`backend/services/intelligence/`) — the 7-stage
   "policy-first" pipeline that handles everything else (finance, health, time,
   local search, trade-offs, general conversation).

Rollback: `USE_LEGACY_PIPELINE=true` bypasses the pipeline; the orchestrator
still runs for mobility.

---

## 2. The 7-stage intelligence pipeline

`services/intelligence/pipeline.py` runs:

| Stage | Module | Job |
|-------|--------|-----|
| 1. Input | `input_processor.py` | Normalize/sanitize; validate browser `location` (rejects the `(0,0)` "geolocation denied" placeholder). |
| 2. Context | `context_assembler.py` | Assemble the `ContextFrame` — HELM scores, financial snapshot, health/time baselines, goals, and **commitments** (recurring bills). Cached per user. |
| 3. Intent | `intent_classifier.py` + `intent_taxonomy.py` | Deterministic keyword/regex first; LLM fallback with **referent resolution** (see §3). |
| 4. Score | `score_engine.py` | Deterministic W/H/T deltas per scoring policy. |
| 4.5 Trade-off | `tradeoff_validator.py` | Clarify / safe-minimal / escalate. |
| 5. Synthesis | `decision_synthesizer.py` | Template plan, or heavy-LLM escalation. |
| 6. Response | `response_generator.py` | Renders the answer — delegates decisions to the **Decision Engine** and location asks to **local search** (see §4–6). |
| 7. Log | `execution_logger.py` | Trace + `DecisionRecord` audit rows. |

---

## 3. Intent taxonomy, routing & referent resolution

`intent_taxonomy.py` holds ~60 intents across wealth / health / time / mobility /
**lifestyle** / cross-domain. Deterministic matching (`match_deterministic`)
tries regex first, then whole-word keywords.

Key behaviours added for correctness:

- **`local_search`** (lifestyle) — "find a gym near me", "gyms nearby". Patterns
  are deliberately conservative so an explicit ride ("uber to X") and comparative
  "should I X or Y" (→ `tradeoff_analysis`) still win.
- **Referent resolution** — the LLM classifier receives a compact
  `conversation_context` (last substantive assistant turn + recent user turns)
  and is instructed to resolve "some / them / those / it" to the prior topic. So
  after the assistant lists walk/run/yoga, *"find some near me"* is understood as
  those activities, **not** a taxi. The resolved context is threaded onto
  `IntentResult.conversation_context` for downstream stages.
- **Activity guard (orchestrator)** — `orchestration/intent.py` no longer treats
  wellbeing phrasing ("go out to run", "walk or do yoga") as a ride. Only an
  explicit ride token (`uber`/`careem`/`taxi`/`cab`/`ride`) routes to mobility.

---

## 4. The Decision Engine (`decision_engine.py`)

Every decision — **binary or multi-option** — is weighed on the three HELM
dimensions and grounded in the user's memory. `response_generator` delegates
`tradeoff_analysis` / `financial_advisory` / `car_purchase` /
`general_conversation` to it.

**Detection & options.** `looks_like_decision()` gates on "should I…",
"buy/afford…", or "X or Y". Options are enumerated per family, adding the
**baseline** for binary decisions:

- "Should I go for a run?" → **run vs rest**
- "Should I buy a car?" → **buy vs hold off**

**Scoring.** Each option gets a directional impact (`↑ / ↓ / →`) on
**Wealth / Health / Time** with a grounded note. Only real numbers are shown
(balance, subscription amounts); costs/times we don't know are never invented.

**Memory grounding** (the "check against memory" step):

| Source | Model | Used for |
|--------|-------|----------|
| Recurring commitments | `RecurringBill` → `ContextFrame.commitments` | "you already pay AED 49/mo for Careem Plus" |
| Goals | `LifeGoal` → `ContextFrame.life_goals` | "goal in play: 'New Apartment'" |
| Affordability | financial snapshot (balance/savings) | whether a purchase strains cash |

**Recommendation.** Weighted by current scores + signals: elevated stress →
calmer option; low Time → shorter; low activity/Health → cardio; low recovery
(HRV) → gentle/low-impact; low Wealth → free/cheaper. When the price of a
purchase is unknown, it **withholds the pick and asks** rather than guessing.

**Families:** `exercise` (multi + binary), `purchase` (car/general), and an
honest `general` fallback that frames W/H/T and asks the key clarifying question.
Adding a family = adding one builder.

---

## 5. Local search (real places, honest numbers)

`response_generator._generate_local_search` answers "find X near me / how far /
how much" with **real data** when the browser shared location (the client sends
`context.location`; the route now forwards it through `session_metadata`):

- **Places** — `GoogleMapsService.places_search` (Places Text Search).
- **"How far"** — real walking distance/ETA via Distance Matrix.
- **"How much"** — Google's coarse `price_level` (`Free`/`$`–`$$$$`) **only**,
  with an explicit "not exact fees" disclaimer. Maps has no real venue prices.
- No location or no Maps key → asks for the user's area. **Never fabricates**
  venues, distances, or prices.

Requires `GOOGLE_MAPS_API_KEY`.

---

## 6. Mobility: honest booking + deep links

HELM has **no live ride-booking integration** — Uber and Careem retired their
public booking APIs, and `uber_service.book_ride` is always mock. So:

- The composer (`orchestration/response.py`) **never fabricates a driver, plate,
  or "Ride Booked!"** confirmation.
- It surfaces the real fare **estimate** and hands off with pre-filled deep links
  (`mobility/executor.build_ride_deeplinks`):
  - **Uber** universal link (`m.uber.com/ul`) with pickup + dropoff coordinates.
  - **Google Maps** directions (universal fallback).
- "Drive Yourself" is treated as *not a booking* (offers directions instead).
- Price **estimates** use the real Uber API when `UBER_SERVER_TOKEN` is set,
  otherwise Dubai-tariff estimates (never presented as live quotes).

The chat renderer (`ChatMessage.tsx`) renders `[text](https-url)` as a safe
`<a target="_blank" rel="noopener noreferrer">` (DOMPurify allow-list; non-http(s)
schemes blocked), so the deep links are one tap.

---

## 7. Honesty rules (enforced in code + tests)

- **Missing capability** (weather, news, live quotes, real-time data) → the
  response persona states the limit plainly ("I don't have a live weather
  connection"), never deflects.
- **No fabricated venues / drivers / fares / distances / prices.**
- **Governance** (consent + PII redaction) runs on the advisory path behind
  `RAI_GOVERNANCE_ENABLED` (see the `responsible-ai` package).

---

## 8. Configuration

| Env var | Effect |
|---------|--------|
| `GEMINI_API_KEY` | LLM for classification/synthesis/response. `mock` disables LLM paths. |
| `USE_LEGACY_PIPELINE` | `true` bypasses the intelligence pipeline. |
| `RAI_GOVERNANCE_ENABLED` | `true` (default) enables consent + PII governance. |
| `GOOGLE_MAPS_API_KEY` | Enables real local search + geocoding/distance. |
| `UBER_SERVER_TOKEN` | Enables real Uber price estimates (booking is always a hand-off). |

---

## 9. Tests

- `tests/unit/test_intelligence_pipeline.py` — pipeline stages, taxonomy,
  local-search honesty, location parsing.
- `tests/unit/test_decision_engine.py` — decision detection, W/H/T scoring,
  memory grounding, per-family recommendations.
- `tests/orchestration/test_mobility_guard.py` — activity phrasing is not a ride.
- `tests/orchestration/test_mobility_composer.py` — no fabricated driver; honest
  hand-off; real deep links.

All are deterministic (no LLM/DB). Run: `pytest tests/unit tests/orchestration`.
