"""Tests for the calibration loader + known-groups acceptance check (§11.3).

Discipline (dogfood-swarm): for every invariant, assert the happy path AND prove
the failing path goes RED. The load-bearing invariants here are:

- the loader round-trips the bundled starter bank into valid ``CalibrationItem``s
  and rejects malformed / under-specified records with a structured error;
- the known-groups laws (§11.3) PASS a clean outcome set and FAIL — with the
  *correct* violation — when a trivial item fails, an impossible item passes, or a
  diagnostic item is non-monotone with ability.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from crucible.calibration.known_groups import (
    KnownGroupsResult,
    check_known_groups,
)
from crucible.calibration.loader import (
    CalibrationLoadError,
    load_default,
    load_items,
)
from crucible.calibration.types import CalibrationCategory, CalibrationItem

ITEMS_DIR = Path(__file__).resolve().parents[1] / "src" / "crucible" / "calibration" / "items"


# --------------------------------------------------------------------------- #
# Loader — happy path / round-trip
# --------------------------------------------------------------------------- #


def test_load_default_returns_starter_bank() -> None:
    items = load_default()
    assert all(isinstance(it, CalibrationItem) for it in items)
    # ~2-3 per category across the 5 categories.
    assert len(items) == 14
    ids = {it.id for it in items}
    assert len(ids) == len(items), "starter-bank ids must be unique"


def test_starter_bank_covers_all_five_categories() -> None:
    items = load_default()
    seen = {it.category for it in items}
    assert seen == set(CalibrationCategory), "starter bank must exercise every category"


def test_load_default_matches_load_items_on_dir() -> None:
    assert {it.id for it in load_default()} == {it.id for it in load_items(ITEMS_DIR)}


def test_load_single_file_round_trips(tmp_path: Path) -> None:
    src = tmp_path / "one.json"
    src.write_text(json.dumps(_min_record()), encoding="utf-8")
    items = load_items(src)
    assert len(items) == 1
    item = items[0]
    assert item.id == "x-0001"
    assert item.category is CalibrationCategory.KNOWN_TRIVIAL
    assert item.gold == "4"
    assert item.expected_pass == {"weak": True, "strong": True}


def test_load_array_file_round_trips(tmp_path: Path) -> None:
    a, b = _min_record("a-1"), _min_record("b-2")
    (tmp_path / "arr.json").write_text(json.dumps([a, b]), encoding="utf-8")
    items = load_items(tmp_path / "arr.json")
    assert {it.id for it in items} == {"a-1", "b-2"}


def test_load_dir_is_sorted_and_concatenated(tmp_path: Path) -> None:
    (tmp_path / "b.json").write_text(json.dumps(_min_record("from-b")), encoding="utf-8")
    (tmp_path / "a.json").write_text(json.dumps(_min_record("from-a")), encoding="utf-8")
    items = load_items(tmp_path)
    # sorted by filename: a.json before b.json
    assert [it.id for it in items] == ["from-a", "from-b"]


def test_optional_irt_fields_round_trip(tmp_path: Path) -> None:
    rec = _min_record()
    rec["difficulty"] = 0.5
    rec["discrimination"] = 1.6
    (tmp_path / "i.json").write_text(json.dumps(rec), encoding="utf-8")
    item = load_items(tmp_path / "i.json")[0]
    assert item.difficulty == 0.5
    assert item.discrimination == 1.6


# --------------------------------------------------------------------------- #
# Loader — error paths (prove each gate goes RED)
# --------------------------------------------------------------------------- #


def test_missing_path_raises(tmp_path: Path) -> None:
    with pytest.raises(CalibrationLoadError, match="PATH_MISSING"):
        load_items(tmp_path / "nope.json")


def test_malformed_json_raises(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text("{not valid json", encoding="utf-8")
    with pytest.raises(CalibrationLoadError, match="BAD_JSON"):
        load_items(bad)


def test_empty_dir_raises(tmp_path: Path) -> None:
    with pytest.raises(CalibrationLoadError, match="DIR_EMPTY"):
        load_items(tmp_path)


def test_non_object_record_in_array_raises(tmp_path: Path) -> None:
    (tmp_path / "x.json").write_text(json.dumps([_min_record(), 5]), encoding="utf-8")
    with pytest.raises(CalibrationLoadError, match="RECORD_NOT_OBJECT"):
        load_items(tmp_path / "x.json")


def test_top_level_scalar_raises(tmp_path: Path) -> None:
    (tmp_path / "x.json").write_text(json.dumps(42), encoding="utf-8")
    with pytest.raises(CalibrationLoadError, match="JSON_SHAPE"):
        load_items(tmp_path / "x.json")


def test_missing_required_field_raises(tmp_path: Path) -> None:
    rec = _min_record()
    del rec["prompt"]
    (tmp_path / "x.json").write_text(json.dumps(rec), encoding="utf-8")
    with pytest.raises(CalibrationLoadError, match="FIELD_MISSING"):
        load_items(tmp_path / "x.json")


def test_missing_gold_raises(tmp_path: Path) -> None:
    rec = _min_record()
    del rec["gold"]
    (tmp_path / "x.json").write_text(json.dumps(rec), encoding="utf-8")
    with pytest.raises(CalibrationLoadError, match="FIELD_MISSING"):
        load_items(tmp_path / "x.json")


def test_unknown_category_raises(tmp_path: Path) -> None:
    rec = _min_record()
    rec["category"] = "totally_made_up"
    (tmp_path / "x.json").write_text(json.dumps(rec), encoding="utf-8")
    with pytest.raises(CalibrationLoadError, match="CATEGORY_UNKNOWN"):
        load_items(tmp_path / "x.json")


def test_unknown_key_raises(tmp_path: Path) -> None:
    rec = _min_record()
    rec["oops"] = 1
    (tmp_path / "x.json").write_text(json.dumps(rec), encoding="utf-8")
    with pytest.raises(CalibrationLoadError, match="UNKNOWN_KEY"):
        load_items(tmp_path / "x.json")


def test_bad_expected_pass_value_raises(tmp_path: Path) -> None:
    rec = _min_record()
    rec["expected_pass"] = {"weak": "yes"}  # not a bool
    (tmp_path / "x.json").write_text(json.dumps(rec), encoding="utf-8")
    with pytest.raises(CalibrationLoadError, match="EXPECTED_PASS_VALUE"):
        load_items(tmp_path / "x.json")


def test_difficulty_bool_rejected(tmp_path: Path) -> None:
    rec = _min_record()
    rec["difficulty"] = True  # bool must not be silently coerced to 1.0
    (tmp_path / "x.json").write_text(json.dumps(rec), encoding="utf-8")
    with pytest.raises(CalibrationLoadError, match="FIELD_TYPE"):
        load_items(tmp_path / "x.json")


def test_duplicate_ids_across_dir_raises(tmp_path: Path) -> None:
    (tmp_path / "a.json").write_text(json.dumps(_min_record("dup")), encoding="utf-8")
    (tmp_path / "b.json").write_text(json.dumps(_min_record("dup")), encoding="utf-8")
    with pytest.raises(CalibrationLoadError, match="DUPLICATE_ID"):
        load_items(tmp_path)


# --------------------------------------------------------------------------- #
# Known-groups — clean PASS
# --------------------------------------------------------------------------- #


def test_known_groups_passes_clean_outcomes() -> None:
    items = load_default()
    outcomes = _clean_outcomes(items)
    result = check_known_groups(items, outcomes)
    assert isinstance(result, KnownGroupsResult)
    assert result.passed, result.violations
    assert result.violations == []
    # every category got exercised
    for cat in CalibrationCategory:
        assert result.by_category[cat.value]["checked"] >= 1


# --------------------------------------------------------------------------- #
# Known-groups — each law goes RED with the right violation
# --------------------------------------------------------------------------- #


def test_known_trivial_failure_is_violation() -> None:
    items = load_default()
    outcomes = _clean_outcomes(items)
    target = _first(items, CalibrationCategory.KNOWN_TRIVIAL)
    # make a trivial item fail on one tier -> instrument fault
    outcomes[target.id]["weak"] = False

    result = check_known_groups(items, outcomes)
    assert not result.passed
    assert any(
        "known_trivial" in v and target.id in v and "FAILED" in v
        for v in result.violations
    ), result.violations
    assert result.by_category["known_trivial"]["violations"] == 1


def test_known_impossible_pass_is_violation() -> None:
    items = load_default()
    outcomes = _clean_outcomes(items)
    target = _first(items, CalibrationCategory.KNOWN_IMPOSSIBLE)
    # make an impossible item pass -> leakage/gaming
    outcomes[target.id]["strong"] = True

    result = check_known_groups(items, outcomes)
    assert not result.passed
    assert any(
        "known_impossible" in v and target.id in v and "PASSED" in v
        for v in result.violations
    ), result.violations


def test_known_diagnostic_non_monotone_is_violation() -> None:
    items = load_default()
    outcomes = _clean_outcomes(items)
    target = _first(items, CalibrationCategory.KNOWN_DIAGNOSTIC)
    # weak passes, strong fails -> non-monotone (inversion)
    outcomes[target.id]["weak"] = True
    outcomes[target.id]["strong"] = False

    result = check_known_groups(items, outcomes)
    assert not result.passed
    assert any(
        "known_diagnostic" in v and target.id in v and "non-monotone" in v
        for v in result.violations
    ), result.violations


def test_missing_outcomes_is_violation() -> None:
    items = load_default()
    outcomes = _clean_outcomes(items)
    target = items[0]
    del outcomes[target.id]  # never exercised

    result = check_known_groups(items, outcomes)
    assert not result.passed
    assert any(target.id in v and "no recorded outcomes" in v for v in result.violations)


def test_empty_tier_map_is_violation() -> None:
    items = load_default()
    outcomes = _clean_outcomes(items)
    target = items[0]
    outcomes[target.id] = {}

    result = check_known_groups(items, outcomes)
    assert not result.passed
    assert any(target.id in v and "empty tier map" in v for v in result.violations)


# --------------------------------------------------------------------------- #
# Known-groups — anchor softness + monotone direction sanity
# --------------------------------------------------------------------------- #


def test_difficulty_anchor_inversion_is_soft_by_default() -> None:
    """A non-monotone anchor is a NOTE by default (§11.3 soft), not a hard fail."""
    items = load_default()
    outcomes = _clean_outcomes(items)
    target = _first(items, CalibrationCategory.DIFFICULTY_ANCHOR)
    outcomes[target.id]["weak"] = True
    outcomes[target.id]["strong"] = False

    soft = check_known_groups(items, outcomes)
    assert soft.passed, "anchor inversion must not hard-fail by default"
    assert any("SOFT" in n for n in soft.by_category["difficulty_anchor"]["notes"])

    strict = check_known_groups(items, outcomes, strict_anchors=True)
    assert not strict.passed
    assert any(
        "difficulty_anchor" in v and target.id in v and "non-monotone" in v
        for v in strict.violations
    )


def test_diagnostic_monotone_equal_pass_is_ok() -> None:
    """Stronger tier passing the SAME items as weaker (both pass) is monotone-ok."""
    items = load_default()
    outcomes = _clean_outcomes(items)
    target = _first(items, CalibrationCategory.KNOWN_DIAGNOSTIC)
    outcomes[target.id] = {"weak": True, "strong": True}  # no inversion
    result = check_known_groups(items, outcomes)
    assert result.passed, result.violations


def test_explicit_tier_order_is_honored() -> None:
    """Custom tier names work when an explicit weakest->strongest order is given."""
    item = CalibrationItem(
        id="diag-custom",
        category=CalibrationCategory.KNOWN_DIAGNOSTIC,
        construct="c",
        confound_controlled="cc",
        prompt="p",
        gold="g",
    )
    outcomes = {"diag-custom": {"novice": True, "expert": False}}  # inversion
    result = check_known_groups([item], outcomes, tier_order=["novice", "expert"])
    assert not result.passed
    assert any("non-monotone" in v for v in result.violations)


def test_test_retest_is_noted_not_failed() -> None:
    items = load_default()
    outcomes = _clean_outcomes(items)
    result = check_known_groups(items, outcomes)
    notes = result.by_category["test_retest"]["notes"]
    assert any("measured elsewhere" in n for n in notes)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def _min_record(item_id: str = "x-0001") -> dict:
    return {
        "id": item_id,
        "category": "known_trivial",
        "construct": "harness wiring",
        "confound_controlled": "difficulty",
        "prompt": "What is 2 + 2?",
        "gold": "4",
        "expected_pass": {"weak": True, "strong": True},
    }


def _first(items: list[CalibrationItem], category: CalibrationCategory) -> CalibrationItem:
    for it in items:
        if it.category is category:
            return it
    raise AssertionError(f"no item with category {category}")


def _clean_outcomes(items: list[CalibrationItem]) -> dict[str, dict[str, bool]]:
    """Build an outcome set that satisfies every known-groups law.

    - trivial: all tiers pass
    - impossible: no tier passes
    - diagnostic/anchor: monotone (weak fails, strong passes; medium passes if used)
    - test_retest: anything (skipped) — use all-pass for realism
    """
    out: dict[str, dict[str, bool]] = {}
    for it in items:
        if it.category is CalibrationCategory.KNOWN_TRIVIAL:
            out[it.id] = {"weak": True, "medium": True, "strong": True}
        elif it.category is CalibrationCategory.KNOWN_IMPOSSIBLE:
            out[it.id] = {"weak": False, "medium": False, "strong": False}
        elif it.category in (
            CalibrationCategory.KNOWN_DIAGNOSTIC,
            CalibrationCategory.DIFFICULTY_ANCHOR,
        ):
            out[it.id] = {"weak": False, "medium": True, "strong": True}
        else:  # TEST_RETEST
            out[it.id] = {"weak": True, "strong": True}
    return out
