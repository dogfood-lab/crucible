"""Unit tests for the characterization runner's pure helpers (no live model needed)."""

from __future__ import annotations

from crucible.calibration.types import CalibrationCategory, CalibrationItem
from crucible.characterize.run import _parse_models, known_groups_report, parse_verdict
from crucible.characterize.types import JudgmentRecord


def test_parse_verdict() -> None:
    assert parse_verdict("PASS") == "PASS"
    assert parse_verdict("I think this is FAIL.") == "FAIL"
    assert parse_verdict("pass") == "PASS"
    assert parse_verdict("no verdict here") is None
    assert parse_verdict("") is None


def test_parse_models_handles_colon_in_model_id() -> None:
    # Regression: a model_id like "qwen3.6:27b" contains a ':'; split on the LAST '@'.
    specs = _parse_models(["qwen3.6:27b@qwen", "mistral-small:24b@mistral"])
    assert specs == [
        ("qwen3.6:27b", "qwen", None),
        ("mistral-small:24b", "mistral", None),
    ]


def test_parse_models_no_family() -> None:
    assert _parse_models(["llama3"]) == [("llama3", "unknown", None)]


def test_known_groups_report() -> None:
    items = [
        CalibrationItem(
            id="t1",
            category=CalibrationCategory.KNOWN_TRIVIAL,
            construct="x",
            confound_controlled="y",
            prompt="p",
            gold=1,
        )
    ]
    miss = {"m": [JudgmentRecord(item_id="t1", model_id="m", predicted=0, gold=1, correct=False)]}
    rep = known_groups_report(items, miss)
    assert rep["passed"] is False and rep["violations"]

    hit = {"m": [JudgmentRecord(item_id="t1", model_id="m", predicted=1, gold=1, correct=True)]}
    assert known_groups_report(items, hit)["passed"] is True
