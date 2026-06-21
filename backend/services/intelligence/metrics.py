"""
Health Metrics — The 5 Numbers That Tell You If You've Won.

Computed from DecisionRecord + OutcomeRecord.
All metrics are deterministic aggregations — no LLM.

The 5 Key Metrics:
    1. Escalation Rate         — % of requests that hit Tier 3 (overall + by intent)
    2. Clarify Success Rate    — did 1 question resolve the request?
    3. SAFE_MINIMAL Frequency  — trend + whether it reduces user stress/repeats
    4. Cost per Resolved       — average cost per COMPLETED request (not raw)
    5. Action Completion Rate  — % of actions that completed + time saved

Usage:
    metrics = MetricsEngine()
    report = metrics.compute(decision_records, outcome_records)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger("intelligence.metrics")


# ============================================================================
# Metric Result Types
# ============================================================================


@dataclass
class EscalationMetric:
    """Escalation rate overall and by intent."""

    total_requests: int = 0
    escalated_requests: int = 0
    escalation_rate: float = 0.0
    by_intent: Dict[str, float] = field(default_factory=dict)


@dataclass
class ClarifyMetric:
    """Clarify success rate — did 1 question resolve?"""

    total_clarify_requests: int = 0
    resolved_after_clarify: int = 0
    success_rate: float = 0.0


@dataclass
class SafeMinimalMetric:
    """SAFE_MINIMAL frequency and trend."""

    total_requests: int = 0
    safe_minimal_count: int = 0
    frequency: float = 0.0
    repeat_rate: float = 0.0  # % of users who hit SAFE_MINIMAL again within 24h


@dataclass
class CostMetric:
    """Cost per resolved request."""

    total_cost_usd: float = 0.0
    total_resolved: int = 0
    cost_per_resolved_usd: float = 0.0
    by_tier: Dict[int, float] = field(default_factory=dict)


@dataclass
class CompletionMetric:
    """Action completion rate."""

    total_actions: int = 0
    completed_actions: int = 0
    completion_rate: float = 0.0
    avg_time_to_complete_ms: float = 0.0
    user_satisfaction_avg: float = 0.0


@dataclass
class MetricsReport:
    """
    Complete metrics report.

    Generated from DecisionRecord + OutcomeRecord data.
    """

    period: str = "all_time"
    escalation: EscalationMetric = field(default_factory=EscalationMetric)
    clarify: ClarifyMetric = field(default_factory=ClarifyMetric)
    safe_minimal: SafeMinimalMetric = field(default_factory=SafeMinimalMetric)
    cost: CostMetric = field(default_factory=CostMetric)
    completion: CompletionMetric = field(default_factory=CompletionMetric)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for API/dashboard."""
        return {
            "period": self.period,
            "escalation": {
                "rate": self.escalation.escalation_rate,
                "total": self.escalation.total_requests,
                "escalated": self.escalation.escalated_requests,
                "by_intent": self.escalation.by_intent,
            },
            "clarify": {
                "success_rate": self.clarify.success_rate,
                "total": self.clarify.total_clarify_requests,
                "resolved": self.clarify.resolved_after_clarify,
            },
            "safe_minimal": {
                "frequency": self.safe_minimal.frequency,
                "count": self.safe_minimal.safe_minimal_count,
                "repeat_rate": self.safe_minimal.repeat_rate,
            },
            "cost": {
                "per_resolved_usd": self.cost.cost_per_resolved_usd,
                "total_usd": self.cost.total_cost_usd,
                "by_tier": self.cost.by_tier,
            },
            "completion": {
                "rate": self.completion.completion_rate,
                "avg_time_ms": self.completion.avg_time_to_complete_ms,
                "satisfaction_avg": self.completion.user_satisfaction_avg,
            },
        }


# ============================================================================
# Metrics Engine
# ============================================================================


class MetricsEngine:
    """
    Computes the 5 health metrics from DecisionRecord + OutcomeRecord data.

    Takes lists of dicts (from DB queries) and produces a MetricsReport.
    All computations are deterministic — no LLM, no external calls.
    """

    def compute(
        self,
        decisions: List[Dict[str, Any]],
        outcomes: List[Dict[str, Any]],
        period: str = "all_time",
    ) -> MetricsReport:
        """
        Compute all 5 metrics from decision and outcome records.

        Args:
            decisions: List of DecisionRecord dicts (from DB).
            outcomes: List of OutcomeRecord dicts (from DB).
            period: Label for the time period.

        Returns:
            MetricsReport with all 5 metrics populated.
        """
        report = MetricsReport(period=period)

        report.escalation = self._compute_escalation(decisions)
        report.clarify = self._compute_clarify(decisions, outcomes)
        report.safe_minimal = self._compute_safe_minimal(decisions)
        report.cost = self._compute_cost(decisions, outcomes)
        report.completion = self._compute_completion(outcomes)

        return report

    # ------------------------------------------------------------------
    # Individual Metric Computations
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_escalation(decisions: List[Dict[str, Any]]) -> EscalationMetric:
        """Metric 1: Escalation rate (% hitting Tier 3)."""
        total = len(decisions)
        if total == 0:
            return EscalationMetric()

        escalated = sum(1 for d in decisions if d.get("tier", 0) >= 3)

        # By intent
        intent_counts: Dict[str, int] = {}
        intent_escalated: Dict[str, int] = {}
        for d in decisions:
            intent = d.get("intent_type", "unknown")
            intent_counts[intent] = intent_counts.get(intent, 0) + 1
            if d.get("tier", 0) >= 3:
                intent_escalated[intent] = intent_escalated.get(intent, 0) + 1

        by_intent = {
            intent: (intent_escalated.get(intent, 0) / count) * 100
            for intent, count in intent_counts.items()
            if count >= 3  # Only show intents with >= 3 occurrences
        }

        return EscalationMetric(
            total_requests=total,
            escalated_requests=escalated,
            escalation_rate=(escalated / total) * 100,
            by_intent=by_intent,
        )

    @staticmethod
    def _compute_clarify(
        decisions: List[Dict[str, Any]],
        outcomes: List[Dict[str, Any]],
    ) -> ClarifyMetric:
        """Metric 2: Clarify success rate — did the question resolve?"""
        clarify_decisions = [
            d for d in decisions if d.get("tradeoff_resolution") == "clarify"
        ]
        total_clarify = len(clarify_decisions)
        if total_clarify == 0:
            return ClarifyMetric()

        # A clarify is "resolved" if the next outcome for the same user shows
        # execution_success=True and user_satisfaction >= 0
        clarify_exec_ids = {d.get("execution_id") for d in clarify_decisions}
        resolved = sum(
            1
            for o in outcomes
            if o.get("execution_id") in clarify_exec_ids and o.get("completed", False)
        )

        return ClarifyMetric(
            total_clarify_requests=total_clarify,
            resolved_after_clarify=resolved,
            success_rate=(resolved / total_clarify) * 100 if total_clarify > 0 else 0,
        )

    @staticmethod
    def _compute_safe_minimal(decisions: List[Dict[str, Any]]) -> SafeMinimalMetric:
        """Metric 3: SAFE_MINIMAL frequency."""
        total = len(decisions)
        if total == 0:
            return SafeMinimalMetric()

        safe_minimal = [
            d for d in decisions if d.get("tradeoff_resolution") == "safe_minimal"
        ]
        count = len(safe_minimal)

        # Repeat rate: users who hit SAFE_MINIMAL more than once
        users_with_sm = {}
        for d in safe_minimal:
            uid = d.get("user_id", "")
            users_with_sm[uid] = users_with_sm.get(uid, 0) + 1

        repeat_users = sum(1 for c in users_with_sm.values() if c > 1)
        total_sm_users = len(users_with_sm)

        return SafeMinimalMetric(
            total_requests=total,
            safe_minimal_count=count,
            frequency=(count / total) * 100,
            repeat_rate=(
                (repeat_users / total_sm_users) * 100 if total_sm_users > 0 else 0
            ),
        )

    @staticmethod
    def _compute_cost(
        decisions: List[Dict[str, Any]],
        outcomes: List[Dict[str, Any]],
    ) -> CostMetric:
        """Metric 4: Cost per resolved request."""
        total_cost = sum(d.get("estimated_cost_usd", 0) for d in decisions)
        resolved = sum(1 for o in outcomes if o.get("completed", False))

        # By tier
        tier_costs: Dict[int, float] = {}
        tier_counts: Dict[int, int] = {}
        for d in decisions:
            tier = d.get("tier", 0)
            tier_costs[tier] = tier_costs.get(tier, 0) + d.get("estimated_cost_usd", 0)
            tier_counts[tier] = tier_counts.get(tier, 0) + 1

        by_tier = {
            tier: cost / tier_counts[tier]
            for tier, cost in tier_costs.items()
            if tier_counts.get(tier, 0) > 0
        }

        return CostMetric(
            total_cost_usd=total_cost,
            total_resolved=resolved,
            cost_per_resolved_usd=total_cost / resolved if resolved > 0 else 0,
            by_tier=by_tier,
        )

    @staticmethod
    def _compute_completion(outcomes: List[Dict[str, Any]]) -> CompletionMetric:
        """Metric 5: Action completion rate."""
        total = len(outcomes)
        if total == 0:
            return CompletionMetric()

        completed = sum(1 for o in outcomes if o.get("completed", False))
        times = [
            o.get("time_to_complete_ms", 0)
            for o in outcomes
            if o.get("completed", False)
        ]
        avg_time = sum(times) / len(times) if times else 0

        satisfactions = [
            o.get("user_satisfaction", 0)
            for o in outcomes
            if o.get("user_satisfaction", 0) != 0
        ]
        avg_satisfaction = (
            sum(satisfactions) / len(satisfactions) if satisfactions else 0
        )

        return CompletionMetric(
            total_actions=total,
            completed_actions=completed,
            completion_rate=(completed / total) * 100,
            avg_time_to_complete_ms=avg_time,
            user_satisfaction_avg=avg_satisfaction,
        )
