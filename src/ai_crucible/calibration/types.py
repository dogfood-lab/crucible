"""Calibration-item contracts (research-grounding §11.3).

A calibration set validates the instrument AND profiles models. Each item declares
the *construct* it probes and the *confound* it controls (construct validity —
Bean et al. 2025), carries a known-groups expectation, and may carry IRT
difficulty/discrimination parameters (tinyBenchmarks; ATLAS).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class CalibrationCategory(StrEnum):
    """The five self-validating categories (§11.3)."""

    KNOWN_TRIVIAL = "known_trivial"          # everything should pass; a failure = instrument fault
    KNOWN_IMPOSSIBLE = "known_impossible"    # nothing passes legitimately; a pass = leakage/gaming
    KNOWN_DIAGNOSTIC = "known_diagnostic"    # discriminating; monotone with ability
    DIFFICULTY_ANCHOR = "difficulty_anchor"  # IRT-laddered, for the latent-ability scale
    TEST_RETEST = "test_retest"              # re-run k× to measure stochastic noise


@dataclass(slots=True)
class CalibrationItem:
    """One calibration item. ``gold`` is grading-side and is NEVER shown to the
    model under characterization (the sealed-boundary principle applies here too)."""

    id: str
    category: CalibrationCategory
    construct: str                 # the capability/property this probes (construct validity)
    confound_controlled: str       # the confound it controls for
    prompt: str                    # what the model under characterization sees
    gold: Any                      # the correct verdict/answer (grading-side; never shown)
    difficulty: float | None = None        # IRT b-parameter, if known/fit
    discrimination: float | None = None    # IRT a-parameter, if known/fit
    # known-groups expectation: ability-tier -> expected pass, e.g. {"strong": True, "weak": False}
    expected_pass: dict[str, bool] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
