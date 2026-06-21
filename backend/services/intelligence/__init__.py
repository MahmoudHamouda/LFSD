"""
HELM Intelligence Layer — Core AI Pipeline

A policy-governed deterministic scoring engine flanked by lightweight LLM calls
for intent parsing and response synthesis. Heavy reasoning is reserved for novel,
high-stakes queries.

The Seven Stages:
    1. Input Processing    → InputEnvelope
    2. Context Assembly    → ContextFrame
    3. Intent Classification → IntentResult
    4. Score Evaluation    → ScoreDeltas
    5. Decision Synthesis  → ActionPlan
    6. Response Generation → ResponseEnvelope
    7. Execution & Logging → PipelineTrace
"""


def get_pipeline_class():
    """Lazy import to avoid pulling heavy dependencies at module level."""
    from .pipeline import IntelligencePipeline

    return IntelligencePipeline


__all__ = ["get_pipeline_class"]
