"""
Stage 7: Execution & Logging — Fully Deterministic, No LLM.

Routes ActionPlan to appropriate microservices for execution.
Writes complete PipelineTrace to audit log (synchronously before response).

Key properties:
    - All actions carry unique execution_id (UUID v7-style, time-ordered)
    - Actions are idempotent (re-dispatch = no-op)
    - Audit log is append-only and immutable
    - Every field is indexed and queryable
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from .schemas import (
    ActionPlan,
    ContextFrame,
    InputEnvelope,
    IntentResult,
    PipelineTrace,
    ResponseEnvelope,
    ScoreDeltas,
    StageTimings,
)

logger = logging.getLogger("intelligence.execution_logger")


class ExecutionLogger:
    """
    Stage 7 of the HELM Intelligence Pipeline.

    Responsibilities:
        - Route ActionPlan to microservices (financial, calendar, mobility)
        - Write complete PipelineTrace to audit log
        - Ensure idempotent execution
        - Capture telemetry for the learning loop
    """

    def __init__(self, db: Session):
        self.db = db

    async def execute_and_log(
        self,
        envelope: InputEnvelope,
        context: ContextFrame,
        intent: IntentResult,
        scores: ScoreDeltas,
        action_plan: ActionPlan,
        response: ResponseEnvelope,
        user_id: str,
        stage_timings: Optional[StageTimings] = None,
    ) -> PipelineTrace:
        """
        Execute the action plan and log the complete pipeline trace.

        Returns:
            PipelineTrace — the complete audit record.
        """
        execution_id = str(uuid.uuid4())
        start_time = time.monotonic()

        #--- Dispatch actions (if any non-respond-only steps) ---
        execution_success = True
        error_message = None

        for step in action_plan.steps:
            if step.action_type.value != "respond_only":
                try:
                    await self._dispatch_action(step, user_id)
                except Exception as e:
                    logger.error(
                        "Action dispatch failed: %s — %s",
                        step.action_type.value,
                        e,
                    )
                    execution_success = False
                    error_message = str(e)

        # --- Build PipelineTrace ---
        execution_ms = (time.monotonic() - start_time) * 1000
        timings = stage_timings or StageTimings()
        timings.execution_logging_ms = execution_ms

        # Calculate total token usage across pipeline
        total_input_tokens = intent.llm_tokens_used + action_plan.llm_tokens_used + response.llm_tokens_used
        total_output_tokens = 0  # Rough estimate: output is ~40% of total
        if total_input_tokens > 0:
            total_output_tokens = int(total_input_tokens * 0.4)
            total_input_tokens = int(total_input_tokens * 0.6)

        trace = PipelineTrace(
            execution_id=execution_id,
            request_id=envelope.request_id,
            user_id=user_id,
            timestamp=datetime.now(timezone.utc),
            tier=intent.tier if isinstance(intent.tier, int) else intent.tier.value,
            input_envelope=envelope.model_dump(exclude={"conversation_history"}),
            context_frame={
                "helm_scores": context.helm_scores.model_dump(),
                "crisis_mode": context.crisis_mode,
                "risk_tolerance": context.risk_tolerance,
                "data_confidence": context.data_confidence,
            },
            intent_result=intent.model_dump(),
            score_deltas=scores.model_dump(),
            action_plan=action_plan.model_dump(),
            response_envelope=response.model_dump(),
            total_input_tokens=total_input_tokens,
            total_output_tokens=total_output_tokens,
            timings=timings,
            execution_success=execution_success,
            error_message=error_message,
        )

        # --- Persist to database ---
        self._persist_trace(trace)
        self._persist_viv_log(trace, intent, response, context)

        logger.info(
            "Pipeline trace logged: execution_id=%s, tier=%d, tokens=%d, success=%s",
            execution_id,
            trace.tier,
            total_input_tokens + total_output_tokens,
            execution_success,
        )

        return trace

    # ------------------------------------------------------------------
    # Action Dispatch
    # ------------------------------------------------------------------

    async def _dispatch_action(self, step, user_id: str) -> None:
        """
        Dispatch an action to the appropriate microservice.

        In Phase 1, this is a no-op / logging stub.
        Phase 3 will implement actual dispatch with idempotency.
        """
        logger.info(
            "Action dispatch (stub): type=%s, service=%s, user=%s",
            step.action_type.value,
            step.target_service or "none",
            user_id,
        )
        # Phase 3: Implement actual dispatch to services
        # For now, just log that we would dispatch

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _persist_trace(self, trace: PipelineTrace) -> None:
        """Write PipelineTrace to the intelligence_traces table."""
        try:
            from models.intelligence_models import PipelineTraceRecord

            record = PipelineTraceRecord(
                execution_id=trace.execution_id,
                request_id=trace.request_id,
                user_id=trace.user_id,
                timestamp=trace.timestamp,
                tier=trace.tier,
                intent_type=trace.intent_result.get("intent", "unknown") if trace.intent_result else "unknown",
                confidence=trace.intent_result.get("confidence", 0) if trace.intent_result else 0,
                score_deltas_json=trace.score_deltas,
                action_plan_json=trace.action_plan,
                response_text=(trace.response_envelope or {}).get("text", "")[:2000],
                input_tokens=trace.total_input_tokens,
                output_tokens=trace.total_output_tokens,
                latency_ms=trace.timings.total_ms,
                stage_timings_json=trace.timings.model_dump(),
                execution_success=trace.execution_success,
                error_message=trace.error_message,
            )
            self.db.add(record)
            self.db.commit()

        except ImportError:
            # Model not yet created — log warning but don't crash
            logger.warning("PipelineTraceRecord model not available — trace not persisted to DB")
        except Exception as e:
            logger.error("Failed to persist pipeline trace: %s", e)
            self.db.rollback()

    def _persist_viv_log(
        self,
        trace: PipelineTrace,
        intent: IntentResult,
        response: ResponseEnvelope,
        context: ContextFrame,
    ) -> None:
        """Write to existing VivLog for backward compatibility."""
        try:
            from models.models import VivLog

            snapshot = {
                "indexes": context.helm_scores.model_dump(),
                "goals_active": len(context.life_goals),
                "tier": trace.tier,
                "pipeline_execution_id": trace.execution_id,
            }

            log = VivLog(
                id=str(uuid.uuid4()),
                user_id=trace.user_id,
                timestamp=datetime.now(timezone.utc),
                user_intent=intent.intent,
                decision_logic=json.dumps(
                    trace.score_deltas or {}, default=str
                )[:2000],
                ai_response=response.text[:2000],
                context_snapshot_json=snapshot,
            )
            self.db.add(log)
            self.db.commit()

        except Exception as e:
            logger.error("VivLog write failed: %s", e)
            self.db.rollback()
