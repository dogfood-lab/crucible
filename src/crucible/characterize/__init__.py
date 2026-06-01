"""Characterization — profile a model's fitness per role slot (research-grounding §11.1).

The 6-metric judge-admission test consumes :class:`JudgmentRecord`s and produces a
:class:`JudgeProfile` with a seat/screen/reject decision. Contracts live in
:mod:`crucible.characterize.types`; the metrics, profiler, and panel aggregation are
built against them.
"""

from __future__ import annotations

from crucible.characterize.types import (
    JudgeProfile,
    JudgmentRecord,
    RoleSlot,
    SeatDecision,
)

__all__ = ["JudgeProfile", "JudgmentRecord", "RoleSlot", "SeatDecision"]
