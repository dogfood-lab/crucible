"""Characterization contracts (research-grounding §11.1).

``JudgmentRecord`` is the unit the metrics consume (one model's judgment on one
calibration item). ``JudgeProfile`` is the output of the 6-metric admission test
that decides whether a local model is seated on the panel.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class RoleSlot(StrEnum):
    """The role slots a local model can be characterized for (Designer stays Claude)."""

    JUDGE = "judge"
    CRITIC = "critic"
    COHORT_SOLVER = "cohort_solver"


class SeatDecision(StrEnum):
    """Outcome of the admission test (§11.1)."""

    SEAT = "seat"        # full panel member (reliability-weighted)
    SCREEN = "screen"    # cheap pre-filter; verdicts always escalated, never final
    REJECT = "reject"    # not usable for this role


@dataclass(slots=True)
class JudgmentRecord:
    """One model's judgment on one calibration item — the metric input unit.

    ``predicted`` / ``gold`` drive accuracy + agreement; ``confidence`` drives ECE;
    ``run_index`` drives test-retest consistency; ``position`` drives position-bias;
    ``family`` drives the same-vs-different-family preference delta.
    """

    item_id: str
    model_id: str
    predicted: Any
    gold: Any
    quant: str | None = None
    confidence: float | None = None
    correct: bool | None = None     # predicted == gold; filled by the scorer
    latency_s: float = 0.0
    run_index: int = 0              # 0..k-1 for test-retest
    position: int | None = None     # for position-swap bias (e.g. 0/1 = A-first/B-first)
    family: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class JudgeProfile:
    """Per-model role-fitness profile — the admission-test output (§11.1).

    Metrics are None when not measured. The seat decision is derived from the
    gates: objective accuracy margin, agreement two-gate (r ≥ 0.80 + κ z-score),
    alt-test ω ≥ 0.5, acceptable consistency + bias.
    """

    model_id: str
    role: RoleSlot
    n_items: int
    quant: str | None = None
    objective_accuracy: float | None = None
    agreement_r: float | None = None         # Pearson vs gold/human
    kappa_z: float | None = None             # Cohen's κ z-score vs human-human baseline
    alt_test_omega: float | None = None      # substitution winning-rate
    consistency: float | None = None         # test-retest stability (1 − flip-rate)
    ece: float | None = None                 # expected calibration error
    position_bias: float | None = None       # position-swap flip-rate
    verbosity_bias: float | None = None
    family_pref_delta: float | None = None   # same- minus different-family agreement
    reliability_weight: float | None = None  # derived weight for aggregation
    seat_decision: SeatDecision = SeatDecision.REJECT
    notes: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
