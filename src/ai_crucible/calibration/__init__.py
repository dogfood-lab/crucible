"""Calibration set — self-validating anchor items for instrument validation + model profiling.

Five categories (research-grounding §11.3) with a pre-registered known-groups
acceptance matrix. Contracts live in :mod:`ai_crucible.calibration.types`; the loader,
known-groups check, and item bank are built against them.
"""

from __future__ import annotations

from ai_crucible.calibration.types import (
    CalibrationCategory,
    CalibrationItem,
)

__all__ = ["CalibrationCategory", "CalibrationItem"]
