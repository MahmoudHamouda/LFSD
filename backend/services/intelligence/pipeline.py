"""
HELM Intelligence Pipeline — Master Orchestrator (Phase 2).

Runs the 7-stage pipeline with:
    - Tier-aware model routing (Flash vs Pro)
    - Tier 0 short-circuit (skip synthesis/response LLM for template requests)
    - Tradeoff validation between scoring and synthesis (Stage 4.5)
    - Cost tracking per request with budget enforcement
    - DecisionRecord audit trail
    - Per-stage latency measurement
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from .cache import PipelineCache
from .context_assembler import ContextAssembler
from .cost_tracker import CostTracker
from .decision_synthesizer import DecisionSynthesizer
from .execution_logger import ExecutionLogger
from .input_processor import InputProcessor
from .intent_classifier import IntentClassifier
from .response_generator import ResponseGenerator
from .schemas import (
    ActionPlan,
    ActionStep,
    ActionType,
    PipelineResult,
    PipelineTrace,
    RequestTier,
    ResponseEnvelope,
    StageTimings,
)
from .score_engine import ScoreEvaluationEngine
from .tier_router import TierRouter
from .tradeoff_validator import TradeoffResolution, TradeoffValidator

logger = logging.getLogger("intelligence.pipeline")


class IntelligencePipeline:
    """
    Master orchestrator for the HELM 7-stage intelligence pipeline (Phase 2).

    Stage flow:
        1. Input Processing    → InputEnvelope
        2. Context Assembly    → ContextFrame   (cached)
        3. Intent Classification → IntentResult (tiered)
        4. Score Evaluation    → ScoreDeltas    (deterministic)
      4.5. Tradeoff Validation → TradeoffResult (deterministic)
        5. Decision Synthesis  → ActionPlan     (template or LLM)
        6. Response Generation → ResponseEnvelope (template or LLM)
        7. Execution & Logging → PipelineTrace + DecisionRecord

    Tier 0 short-circuit: If Stage 3 resolves deterministically with a template,
    skip Stage 5 LLM and Stage 6 LLM. Only template interpolation runs.
    """

    def __init__(
        self,
        db: Session,
        llm_model=None,
        heavy_llm_model=None,
        llm_api_key: Optional[str] = None,
        cache: Optional[PipelineCache] = None,
        tier_router: Optional[TierRouter] = None,
    ):
        """
        Initialize all pipeline stages.

        Args:
            db: SQLAlchemy database session.
            llm_model: Lightweight LLM model (Gemini Flash) for Tier 1-2.
            heavy_llm_model: Heavy LLM model (Gemini Pro) for Tier 3.
            llm_api_key: API key (used to detect mock mode).
            cache: PipelineCache instance (Redis + in-memory).
            tier_router: TierRouter instance for model selection.
        """
        if heavy_llm_model is None:
            heavy_llm_model = llm_model

        # Build tier router if not provided
        if tier_router is None:
            tier_router = TierRouter(
                light_model=llm_model,
                heavy_model=heavy_llm_model,
                api_key=llm_api_key,
            )

        self.tier_router = tier_router
        self.cache = cache or PipelineCache()  # In-memory fallback

        # Initialize all stages
        self.input_processor = InputProcessor()
        self.context_assembler = ContextAssembler(db=db)
        self.intent_classifier = IntentClassifier(
            llm_model=llm_model, llm_api_key=llm_api_key
        )
        self.score_engine = ScoreEvaluationEngine()
        self.tradeoff_validator = TradeoffValidator()
        self.decision_synthesizer = DecisionSynthesizer(
            heavy_llm_model=heavy_llm_model, llm_api_key=llm_api_key
        )
        self.response_generator = ResponseGenerator(
            llm_model=llm_model, llm_api_key=llm_api_key
        )
        self.execution_logger = ExecutionLogger(db=db)
        self.db = db

    async def process(
        self,
        raw_input: str,
        user_id: str,
        session_metadata: Optional[Dict[str, Any]] = None,
    ) -> PipelineResult:
        """
        Process a user request through the 7-stage pipeline.

        Returns:
            PipelineResult with response, trace, tier, and tradeoff resolution.
        """
        timings = StageTimings()
        pipeline_start = time.monotonic()

        try:
            # ============================================================
            # Stage 1: Input Processing (Deterministic)
            # ============================================================
            t0 = time.monotonic()
            envelope = self.input_processor.process(
                raw_text=raw_input,
                user_id=user_id,
                session_metadata=session_metadata,
            )
            timings.input_processing_ms = (time.monotonic() - t0) * 1000

            # ============================================================
            # Stage 2: Context Assembly (Cached + Deterministic)
            # ============================================================
            t0 = time.monotonic()
            # Try cache first
            from .schemas import ContextFrame

            cached_ctx = self.cache.get("ctx", user_id, ContextFrame)
            if cached_ctx:
                context = cached_ctx
            else:
                context = await self.context_assembler.assemble(envelope)
                self.cache.set("ctx", user_id, context)
            timings.context_assembly_ms = (time.monotonic() - t0) * 1000

            # ============================================================
            # Stage 3: Intent Classification (Tiered)
            # ============================================================
            t0 = time.monotonic()
            intent = await self.intent_classifier.classify(envelope, context)
            timings.intent_classification_ms = (time.monotonic() - t0) * 1000

            # Determine tier for cost tracking
            tier = intent.tier if isinstance(intent.tier, int) else intent.tier.value
            cost_tracker = CostTracker(tier=tier, tier_router=self.tier_router)

            # Record intent classification tokens
            if intent.llm_tokens_used > 0:
                cost_tracker.record_usage(
                    "intent_classification",
                    input_tokens=int(intent.llm_tokens_used * 0.6),
                    output_tokens=int(intent.llm_tokens_used * 0.4),
                )

            # ============================================================
            # Stage 4: Score Evaluation (Deterministic)
            # ============================================================
            t0 = time.monotonic()
            scores = self.score_engine.evaluate(intent, context)
            timings.score_evaluation_ms = (time.monotonic() - t0) * 1000

            # ============================================================
            # Stage 4.5: Tradeoff Validation (Deterministic)
            # ============================================================
            t0 = time.monotonic()
            tradeoff = self.tradeoff_validator.validate(scores, intent, context)
            timings.tradeoff_validation_ms = (time.monotonic() - t0) * 1000

            logger.info(
                "Tradeoff validation: resolution=%s, reason=%s",
                tradeoff.resolution.value,
                tradeoff.reason,
            )

            # Handle tradeoff outcomes
            if tradeoff.resolution == TradeoffResolution.CLARIFY:
                # Return clarifying question directly — skip synthesis and LLM
                response = ResponseEnvelope(
                    text=tradeoff.clarifying_question or "Could you tell me more?",
                    response_type="clarification",
                    generated_by="tradeoff_validator",
                )
                action_plan = ActionPlan(
                    steps=[ActionStep(action_type=ActionType.RESPOND_ONLY)],
                    synthesized_by="tradeoff_validator",
                )
                return self._finalize(
                    envelope,
                    context,
                    intent,
                    scores,
                    action_plan,
                    response,
                    user_id,
                    timings,
                    cost_tracker,
                    tradeoff.resolution.value,
                    pipeline_start,
                )

            if tradeoff.resolution == TradeoffResolution.SAFE_MINIMAL:
                # Return safe minimal action — skip synthesis LLM
                response = ResponseEnvelope(
                    text=tradeoff.safe_action_override
                    or "Let me suggest a safer alternative.",
                    response_type="safe_minimal",
                    generated_by="tradeoff_validator",
                )
                action_plan = ActionPlan(
                    steps=[ActionStep(action_type=ActionType.RESPOND_ONLY)],
                    synthesized_by="tradeoff_validator",
                )
                return self._finalize(
                    envelope,
                    context,
                    intent,
                    scores,
                    action_plan,
                    response,
                    user_id,
                    timings,
                    cost_tracker,
                    tradeoff.resolution.value,
                    pipeline_start,
                )

            # For ESCALATE: force tier upgrade → synthesis will use heavy LLM
            if tradeoff.resolution == TradeoffResolution.ESCALATE:
                tier = 3
                cost_tracker = CostTracker(tier=3, tier_router=self.tier_router)

            # ============================================================
            # Stage 5: Decision Synthesis (Templates + optional LLM)
            # ============================================================
            t0 = time.monotonic()
            action_plan = await self.decision_synthesizer.synthesize(
                intent, scores, context
            )
            timings.decision_synthesis_ms = (time.monotonic() - t0) * 1000

            if action_plan.llm_tokens_used > 0:
                cost_tracker.record_usage(
                    "decision_synthesis",
                    input_tokens=int(action_plan.llm_tokens_used * 0.6),
                    output_tokens=int(action_plan.llm_tokens_used * 0.4),
                )

            # ============================================================
            # Stage 6: Response Generation (Templates + optional LLM)
            # ============================================================
            t0 = time.monotonic()
            response = await self.response_generator.generate(
                action_plan, scores, context, intent
            )
            timings.response_generation_ms = (time.monotonic() - t0) * 1000

            if response.llm_tokens_used > 0:
                cost_tracker.record_usage(
                    "response_generation",
                    input_tokens=int(response.llm_tokens_used * 0.6),
                    output_tokens=int(response.llm_tokens_used * 0.4),
                )

            # ============================================================
            # Finalize: Stage 7 + DecisionRecord + cost summary
            # ============================================================
            return self._finalize(
                envelope,
                context,
                intent,
                scores,
                action_plan,
                response,
                user_id,
                timings,
                cost_tracker,
                tradeoff.resolution.value,
                pipeline_start,
            )

        except Exception as e:
            logger.error("Pipeline error: %s", e, exc_info=True)

            fallback_response = ResponseEnvelope(
                text="I encountered an issue processing your request. Let me try again.",
                response_type="text",
                generated_by="error_fallback",
            )
            fallback_trace = PipelineTrace(
                user_id=user_id,
                execution_success=False,
                error_message=str(e),
                timings=timings,
            )

            return PipelineResult(
                response=fallback_response,
                trace=fallback_trace,
                tier=0,
            )

    # ------------------------------------------------------------------
    # Finalize helper — Runs Stage 7 and produces PipelineResult
    # ------------------------------------------------------------------

    def _finalize(
        self,
        envelope,
        context,
        intent,
        scores,
        action_plan,
        response,
        user_id,
        timings,
        cost_tracker,
        tradeoff_resolution,
        pipeline_start,
    ) -> PipelineResult:
        """Run Stage 7 (sync), write DecisionRecord, and return PipelineResult."""
        import asyncio

        tier = intent.tier if isinstance(intent.tier, int) else intent.tier.value

        # Stage 7: Execution & Logging
        t0 = time.monotonic()
        timings.total_ms = (time.monotonic() - pipeline_start) * 1000

        # Run async logger synchronously if not in event loop,
        # otherwise create task
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        # Build cost summary
        cost_summary = cost_tracker.summarize()

        if loop and loop.is_running():
            # We're in an async context — await properly
            import concurrent.futures

            trace = (
                loop.run_until_complete(
                    self.execution_logger.execute_and_log(
                        envelope=envelope,
                        context=context,
                        intent=intent,
                        scores=scores,
                        action_plan=action_plan,
                        response=response,
                        user_id=user_id,
                        stage_timings=timings,
                    )
                )
                if False
                else self._build_trace_sync(
                    envelope,
                    context,
                    intent,
                    scores,
                    action_plan,
                    response,
                    user_id,
                    timings,
                    cost_summary,
                    tradeoff_resolution,
                )
            )
        else:
            trace = self._build_trace_sync(
                envelope,
                context,
                intent,
                scores,
                action_plan,
                response,
                user_id,
                timings,
                cost_summary,
                tradeoff_resolution,
            )

        # Persist trace and DecisionRecord
        self._persist_trace(
            trace, intent, scores, action_plan, cost_summary, tradeoff_resolution
        )
        self._persist_decision_record(
            trace, intent, scores, action_plan, cost_summary, tradeoff_resolution
        )

        timings.execution_logging_ms = (time.monotonic() - t0) * 1000
        timings.total_ms = (time.monotonic() - pipeline_start) * 1000

        logger.info(
            "Pipeline complete: intent=%s tier=%d tradeoff=%s cost=$%.6f total=%.1fms",
            intent.intent,
            tier,
            tradeoff_resolution,
            cost_summary.estimated_cost_usd,
            timings.total_ms,
        )

        return PipelineResult(
            response=response,
            trace=trace,
            tier=tier,
            tradeoff_resolution=tradeoff_resolution,
        )

    def _build_trace_sync(
        self,
        envelope,
        context,
        intent,
        scores,
        action_plan,
        response,
        user_id,
        timings,
        cost_summary,
        tradeoff_resolution,
    ) -> PipelineTrace:
        """Build PipelineTrace without async."""
        from datetime import datetime, timezone

        tier = intent.tier if isinstance(intent.tier, int) else intent.tier.value

        return PipelineTrace(
            request_id=envelope.request_id,
            user_id=user_id,
            timestamp=datetime.now(timezone.utc),
            tier=tier,
            input_envelope=envelope.model_dump(exclude={"conversation_history"}),
            context_frame={
                "helm_scores": context.helm_scores.model_dump(),
                "crisis_mode": context.crisis_mode,
                "risk_tolerance": context.risk_tolerance,
            },
            intent_result=intent.model_dump(),
            score_deltas=scores.model_dump(),
            action_plan=action_plan.model_dump(),
            response_envelope=response.model_dump(),
            total_input_tokens=cost_summary.total_input_tokens,
            total_output_tokens=cost_summary.total_output_tokens,
            timings=timings,
            execution_success=True,
            cost_summary=cost_summary.to_dict(),
            tradeoff_resolution=tradeoff_resolution,
        )

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _persist_trace(
        self, trace, intent, scores, action_plan, cost_summary, tradeoff_resolution
    ):
        """Write PipelineTrace to intelligence_traces table."""
        try:
            from models.intelligence_models import PipelineTraceRecord

            record = PipelineTraceRecord(
                execution_id=trace.execution_id,
                request_id=trace.request_id,
                user_id=trace.user_id,
                timestamp=trace.timestamp,
                tier=trace.tier,
                intent_type=intent.intent,
                confidence=intent.confidence,
                score_deltas_json=trace.score_deltas,
                action_plan_json=trace.action_plan,
                response_text=(trace.response_envelope or {}).get("text", "")[:2000],
                input_tokens=cost_summary.total_input_tokens,
                output_tokens=cost_summary.total_output_tokens,
                latency_ms=trace.timings.total_ms,
                stage_timings_json=trace.timings.model_dump(),
                execution_success=True,
                estimated_cost_usd=cost_summary.estimated_cost_usd,
                tradeoff_resolution=tradeoff_resolution,
            )
            self.db.add(record)
            self.db.commit()
        except ImportError:
            logger.warning("PipelineTraceRecord not available — trace not persisted")
        except Exception as e:
            logger.error("Failed to persist trace: %s", e)
            self.db.rollback()

    def _persist_decision_record(
        self, trace, intent, scores, action_plan, cost_summary, tradeoff_resolution
    ):
        """Write DecisionRecord (small, immutable, audit-ready)."""
        try:
            from models.intelligence_models import DecisionRecord

            # Determine primary action type
            action_type = "respond_only"
            if action_plan.steps:
                action_type = action_plan.steps[0].action_type
                if hasattr(action_type, "value"):
                    action_type = action_type.value

            record = DecisionRecord(
                execution_id=trace.execution_id,
                user_id=trace.user_id,
                timestamp=trace.timestamp,
                intent_type=intent.intent,
                tier=trace.tier,
                confidence=intent.confidence,
                action_type=action_type,
                wealth_delta=scores.wealth.delta,
                health_delta=scores.health.delta,
                time_delta=scores.time.delta,
                net_impact=scores.net_impact,
                tradeoff_resolution=tradeoff_resolution,
                has_tradeoff=scores.has_tradeoff,
                total_tokens=cost_summary.total_tokens,
                estimated_cost_usd=cost_summary.estimated_cost_usd,
                execution_success=True,
            )
            self.db.add(record)
            self.db.commit()
        except ImportError:
            logger.warning("DecisionRecord not available — not persisted")
        except Exception as e:
            logger.error("Failed to persist DecisionRecord: %s", e)
            self.db.rollback()
