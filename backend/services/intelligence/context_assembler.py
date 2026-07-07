"""
Stage 2: Context Assembly — Deterministic with Cached Lookups, No LLM.

Builds a ContextFrame by pulling from multiple data sources:
    - User profile store (financial accounts, health baselines, calendar metadata)
    - Recent interaction history
    - Current HELM scores (VivIndex)
    - Life goals

The ContextFrame is compressed to ~200 tokens when serialized for LLM consumption.

Performance target: < 50ms (cache hit), < 200ms (cache miss).
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, date, timezone
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from .schemas import (
    ContextFrame,
    FinancialSnapshot,
    HealthBaseline,
    HelmScores,
    InputEnvelope,
    TimeBaseline,
)

logger = logging.getLogger("intelligence.context_assembler")

# In-memory cache (fallback when Redis unavailable)
_context_cache: Dict[str, tuple] = {}  # user_id -> (ContextFrame, expiry_timestamp)
CACHE_TTL_SECONDS = 300  # 5 minutes


class ContextAssembler:
    """
    Stage 2 of the HELM Intelligence Pipeline.

    Responsibilities:
        - Assemble user context from profile store, scores, and history
        - Compress context to ~200 tokens for LLM consumption
        - Cache hot profiles (5-minute TTL)
        - Graceful fallback to defaults if data is missing
    """

    def __init__(self, db: Session):
        self.db = db

    async def assemble(self, envelope: InputEnvelope) -> ContextFrame:
        """
        Build a ContextFrame for the given user.

        Checks cache first, then assembles from database.
        """
        user_id = envelope.user_id

        # Check cache
        cached = self._get_cached(user_id)
        if cached is not None:
            logger.debug("Context cache HIT for user %s", user_id)
            return cached

        # Assemble from DB
        logger.debug("Context cache MISS for user %s — assembling from DB", user_id)
        start = time.monotonic()
        context = self._assemble_from_db(user_id)
        elapsed_ms = (time.monotonic() - start) * 1000
        logger.info("Context assembled in %.1fms for user %s", elapsed_ms, user_id)

        # Cache it
        self._set_cached(user_id, context)

        return context

    def invalidate_cache(self, user_id: str) -> None:
        """Invalidate cached context for a user (call after data mutations)."""
        _context_cache.pop(user_id, None)

    # ------------------------------------------------------------------
    # Private: Database assembly
    # ------------------------------------------------------------------

    def _assemble_from_db(self, user_id: str) -> ContextFrame:
        """Pull all context from database and build ContextFrame."""
        try:
            from models.models import (
                User,
                VivIndex,
                LifeGoal,
                HealthDailySummary,
                FinancialAccount,
                FinancialTransaction,
            )
            from models.models_scores import DBUserScore

            user = self.db.query(User).filter(User.id == user_id).first()

            if not user:
                logger.warning("User %s not found — returning default context", user_id)
                return ContextFrame(user_id=user_id)

            # --- HELM Scores ---
            helm_scores = self._load_helm_scores(user_id, VivIndex)

            # --- Financial Snapshot ---
            financial = self._load_financial_snapshot(user, user_id)

            # --- Health Baseline ---
            health = self._load_health_baseline(user, user_id, HealthDailySummary)

            # --- Time Baseline ---
            time_baseline = self._load_time_baseline(user_id, DBUserScore)

            # --- Life Goals ---
            life_goals = [
                {
                    "title": g.title,
                    "target_amount": g.target_amount,
                    "saved_amount": g.saved_amount,
                    "deadline": (
                        g.deadline.isoformat() if getattr(g, "deadline", None) else None
                    ),
                    "priority": g.priority,
                    "pillar": g.pillar if hasattr(g, "pillar") else "wealth",
                }
                for g in (user.life_goals or [])
            ]

            # --- Memory: recurring commitments (subscriptions/bills) ---
            commitments = self._load_commitments(user_id)

            # --- Crisis Detection ---
            crisis_dims = []
            if helm_scores.wealth < 30:
                crisis_dims.append("wealth")
            if helm_scores.health < 30:
                crisis_dims.append("health")
            if helm_scores.time < 30:
                crisis_dims.append("time")

            # --- Preferences ---
            prefs = user.viv_preferences or {}

            # --- Data Confidence ---
            confidence = {
                "wealth": 1.0 if financial.monthly_income > 0 else 0.3,
                "health": 1.0 if health.hrv_avg is not None else 0.5,
                "time": 0.5,  # Default until calendar data enriches this
            }

            return ContextFrame(
                user_id=user_id,
                user_name=user.email.split("@")[0] if user.email else "User",
                user_email=user.email,
                helm_scores=helm_scores,
                financial=financial,
                health=health,
                time=time_baseline,
                life_goals=life_goals,
                commitments=commitments,
                risk_tolerance=prefs.get("risk_tolerance", "medium"),
                trade_off_rule=prefs.get("trade_off_rule", "balanced_living"),
                crisis_mode=len(crisis_dims) > 0,
                crisis_dimensions=crisis_dims,
                data_confidence=confidence,
            )

        except Exception as e:
            logger.error("Failed to assemble context for user %s: %s", user_id, e)
            return ContextFrame(user_id=user_id)

    def _load_helm_scores(self, user_id: str, VivIndex) -> HelmScores:
        """Load latest VivIndex scores."""
        latest = (
            self.db.query(VivIndex)
            .filter(VivIndex.user_id == user_id)
            .order_by(VivIndex.timestamp.desc())
            .first()
        )
        if latest:
            return HelmScores(
                wealth=latest.financial_score or 50.0,
                health=latest.health_score or 50.0,
                time=latest.time_score or 50.0,
            )
        return HelmScores()

    def _load_commitments(self, user_id: str) -> list:
        """Load verified recurring commitments (subscriptions/bills) for memory."""
        try:
            from models.models import RecurringBill

            bills = (
                self.db.query(RecurringBill)
                .filter(RecurringBill.user_id == user_id)
                .all()
            )
            return [
                {
                    "name": b.name,
                    "amount": float(b.amount or 0.0),
                    "cadence": b.cadence or "monthly",
                }
                for b in bills
            ]
        except Exception as e:
            logger.debug("No commitments loaded for %s: %s", user_id, e)
            return []

    def _load_financial_snapshot(self, user, user_id: str) -> FinancialSnapshot:
        """Build compressed financial context."""
        try:
            from models.models import FinancialScore

            score = (
                self.db.query(FinancialScore)
                .filter(FinancialScore.user_id == user_id)
                .order_by(FinancialScore.timestamp.desc())
                .first()
            )

            if score:
                return FinancialSnapshot(
                    total_balance=sum(
                        a.current_balance for a in (user.financial_accounts or [])
                    ),
                    monthly_income=score.total_monthly_income or 0.0,
                    monthly_expenses=(score.total_monthly_expenses or 0.0)
                    + (score.total_monthly_bills or 0.0),
                    monthly_savings=score.total_monthly_savings or 0.0,
                )
            else:
                # Fallback: derive from accounts
                total_balance = sum(
                    a.current_balance for a in (user.financial_accounts or [])
                )
                return FinancialSnapshot(total_balance=total_balance)

        except Exception as e:
            logger.warning("Financial snapshot fallback for %s: %s", user_id, e)
            return FinancialSnapshot()

    def _load_health_baseline(
        self, user, user_id: str, HealthDailySummary
    ) -> HealthBaseline:
        """Build compressed health context from latest daily summary."""
        try:
            prefs = user.viv_preferences or {}
            if not prefs.get("share_health_data", True):
                return HealthBaseline()

            today = date.today()
            summary = (
                self.db.query(HealthDailySummary)
                .filter(
                    HealthDailySummary.user_id == user_id,
                    HealthDailySummary.date == today,
                )
                .first()
            )

            if summary:
                return HealthBaseline(
                    sleep_hours_avg=(summary.sleep_duration_minutes or 0) / 60.0,
                    sleep_quality=summary.sleep_quality_score or 50.0,
                    hrv_avg=summary.hrv_average,
                    steps_avg=summary.steps_count or 5000,
                )

            return HealthBaseline()

        except Exception as e:
            logger.warning("Health baseline fallback for %s: %s", user_id, e)
            return HealthBaseline()

    def _load_time_baseline(self, user_id: str, DBUserScore) -> TimeBaseline:
        """Build compressed time/productivity context."""
        try:
            score = (
                self.db.query(DBUserScore)
                .filter(DBUserScore.user_id == user_id)
                .first()
            )
            if score:
                return TimeBaseline(
                    focus_time_hours=score.focus_time_hours or 4.0,
                    meeting_hours_daily=score.meeting_hours or 2.0,
                    work_life_balance=score.work_life_balance or 50.0,
                    productivity_score=score.productivity_score or 50.0,
                )
            return TimeBaseline()

        except Exception as e:
            logger.warning("Time baseline fallback for %s: %s", user_id, e)
            return TimeBaseline()

    # ------------------------------------------------------------------
    # Private: Caching
    # ------------------------------------------------------------------

    def _get_cached(self, user_id: str) -> Optional[ContextFrame]:
        """Retrieve from in-memory cache if valid."""
        entry = _context_cache.get(user_id)
        if entry is None:
            return None
        context, expiry = entry
        if time.time() > expiry:
            del _context_cache[user_id]
            return None
        return context

    def _set_cached(self, user_id: str, context: ContextFrame) -> None:
        """Store in in-memory cache with TTL."""
        _context_cache[user_id] = (context, time.time() + CACHE_TTL_SECONDS)
