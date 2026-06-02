"""Known-groups acceptance matrix (research-grounding §11.3).

The calibration set is *self-validating*: before any real diagnostic, run the
panel against the calibration items and check the observed pass-pattern against
the pre-registered laws below. This is construct-validity by known-groups (Bean
et al. 2025) — items whose outcomes are knowable a-priori expose instrument
faults, leakage/gaming, and broken discrimination *before* trusting a real
measurement.

The five categories (§11.3) and the pass-pattern law each enforces:

==================  ===========================================================
Category            Pass-pattern law (this module enforces)
==================  ===========================================================
KNOWN_TRIVIAL       *every* tier must pass — any failure = instrument fault
                    (harness wiring / parsing / scoring is broken).
KNOWN_IMPOSSIBLE    *no* tier may pass — any pass = leakage / test-gaming /
                    contamination (ImpossibleBench, Zhong/Raghunathan/Carlini
                    2025, arXiv:2510.20270).
KNOWN_DIAGNOSTIC    monotone with ability — a stronger tier must NOT pass fewer
                    items than a weaker tier (it must discriminate the right
                    way round).
DIFFICULTY_ANCHOR   consistent with declared difficulty — SOFT/optional check:
                    if both ``difficulty`` (IRT b) and an ability-ordering are
                    available, an easier anchor should not be passed by *fewer*
                    tiers than a harder one. Recorded as a non-fatal note unless
                    ``strict_anchors=True``.
TEST_RETEST         handled elsewhere (per-item variance over k re-runs, §11.3).
                    Skipped here with a note.
==================  ===========================================================

``outcomes`` maps ``item_id -> {ability_tier -> passed}``. Tier *strength order*
is inferred from declared ``expected_pass`` where possible, else falls back to a
documented default (``strong`` > ``medium`` > ``weak``); callers may override via
``tier_order``.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ai_crucible.calibration.types import CalibrationCategory, CalibrationItem

__all__ = ["KnownGroupsResult", "check_known_groups"]

# Default ability ordering, weakest -> strongest, used when tiers are not
# otherwise orderable from the data. Documented so violations are reproducible.
_DEFAULT_TIER_RANK: dict[str, int] = {"weak": 0, "medium": 1, "strong": 2}


@dataclass
class KnownGroupsResult:
    """Outcome of the known-groups acceptance check.

    Attributes:
        passed: True iff there are zero hard violations.
        violations: human-readable, precise violation strings (one per breach).
        by_category: per-category summary keyed by ``CalibrationCategory.value``;
            each entry carries ``checked`` (item count), ``violations`` (count),
            and ``notes`` (non-fatal observations, e.g. skipped categories).
    """

    passed: bool
    violations: list[str]
    by_category: dict[str, dict] = field(default_factory=dict)


def check_known_groups(
    items: list[CalibrationItem],
    outcomes: dict[str, dict[str, bool]],
    *,
    tier_order: list[str] | None = None,
    strict_anchors: bool = False,
) -> KnownGroupsResult:
    """Check observed ``outcomes`` against the §11.3 known-groups laws.

    Args:
        items: the calibration items under test.
        outcomes: ``item_id -> {ability_tier -> passed}``. Every item present in
            ``items`` must have an entry (a missing entry is itself a violation —
            you cannot accept an instrument you did not exercise).
        tier_order: optional explicit weakest->strongest tier ordering. When
            omitted, ordering is inferred from each item's ``expected_pass`` and
            the documented default (weak < medium < strong).
        strict_anchors: when True, DIFFICULTY_ANCHOR inconsistencies are hard
            violations; otherwise they are recorded as non-fatal notes (the law
            is soft per §11.3).

    Returns:
        KnownGroupsResult with the pass/fail verdict, precise violations, and a
        per-category summary.
    """
    violations: list[str] = []
    by_category: dict[str, dict] = {
        cat.value: {"checked": 0, "violations": 0, "notes": []}
        for cat in CalibrationCategory
    }

    explicit_order = _rank_from_list(tier_order) if tier_order else None

    for item in items:
        bucket = by_category[item.category.value]
        bucket["checked"] += 1

        item_outcomes = outcomes.get(item.id)
        if item_outcomes is None:
            msg = (
                f"[{item.category.value}] item {item.id!r} has no recorded outcomes "
                f"(every calibration item must be exercised before acceptance)"
            )
            violations.append(msg)
            bucket["violations"] += 1
            continue
        if not item_outcomes:
            msg = (
                f"[{item.category.value}] item {item.id!r} recorded an empty tier map "
                f"(no tier was run)"
            )
            violations.append(msg)
            bucket["violations"] += 1
            continue

        before = len(violations)
        _check_item(
            item,
            item_outcomes,
            explicit_order=explicit_order,
            strict_anchors=strict_anchors,
            violations=violations,
            notes=bucket["notes"],
        )
        bucket["violations"] += len(violations) - before

    return KnownGroupsResult(
        passed=not violations,
        violations=violations,
        by_category=by_category,
    )


# --------------------------------------------------------------------------- #
# Per-category laws
# --------------------------------------------------------------------------- #


def _check_item(
    item: CalibrationItem,
    item_outcomes: dict[str, bool],
    *,
    explicit_order: dict[str, int] | None,
    strict_anchors: bool,
    violations: list[str],
    notes: list[str],
) -> None:
    cat = item.category

    if cat is CalibrationCategory.KNOWN_TRIVIAL:
        for tier, passed in sorted(item_outcomes.items()):
            if not passed:
                violations.append(
                    f"[known_trivial] item {item.id!r} FAILED on tier {tier!r}: "
                    f"a known-trivial item must pass on every tier — this is an "
                    f"instrument fault (harness wiring / parsing / scoring)"
                )
        return

    if cat is CalibrationCategory.KNOWN_IMPOSSIBLE:
        for tier, passed in sorted(item_outcomes.items()):
            if passed:
                violations.append(
                    f"[known_impossible] item {item.id!r} PASSED on tier {tier!r}: "
                    f"a known-impossible item must never pass legitimately — this "
                    f"signals leakage / test-gaming / contamination"
                )
        return

    if cat is CalibrationCategory.KNOWN_DIAGNOSTIC:
        _check_monotone(
            item,
            item_outcomes,
            explicit_order=explicit_order,
            violations=violations,
            label="known_diagnostic",
            soft=False,
            notes=notes,
        )
        return

    if cat is CalibrationCategory.DIFFICULTY_ANCHOR:
        _check_monotone(
            item,
            item_outcomes,
            explicit_order=explicit_order,
            violations=violations if strict_anchors else None,
            label="difficulty_anchor",
            soft=not strict_anchors,
            notes=notes,
        )
        return

    if cat is CalibrationCategory.TEST_RETEST:
        notes.append(
            f"item {item.id!r}: test_retest reliability is measured elsewhere "
            f"(per-item variance over k re-runs, §11.3) — skipped here"
        )
        return


def _check_monotone(
    item: CalibrationItem,
    item_outcomes: dict[str, bool],
    *,
    explicit_order: dict[str, int] | None,
    violations: list[str] | None,
    label: str,
    soft: bool,
    notes: list[str],
) -> None:
    """Enforce: a stronger tier must not pass *fewer* items than a weaker tier.

    With one pass/fail per (item, tier), 'passes fewer' reduces to: there must be
    no inversion where a weaker tier passed while a stronger tier failed.
    """
    rank = explicit_order or _infer_rank(item, item_outcomes)
    unranked = [t for t in item_outcomes if t not in rank]
    if unranked:
        note = (
            f"item {item.id!r}: tier(s) {sorted(unranked)} have no known ability "
            f"rank; monotonicity not checked for them "
            f"(provide tier_order or expected_pass)"
        )
        notes.append(note)

    ranked = sorted(
        (t for t in item_outcomes if t in rank),
        key=lambda t: rank[t],
    )
    for i in range(len(ranked)):
        for j in range(i + 1, len(ranked)):
            weaker, stronger = ranked[i], ranked[j]
            if rank[stronger] == rank[weaker]:
                continue
            if item_outcomes[weaker] and not item_outcomes[stronger]:
                msg = (
                    f"[{label}] item {item.id!r} is non-monotone: weaker tier "
                    f"{weaker!r} passed but stronger tier {stronger!r} failed — a "
                    f"diagnostic item must separate ability in the right direction"
                )
                if soft or violations is None:
                    notes.append("SOFT " + msg)
                else:
                    violations.append(msg)


# --------------------------------------------------------------------------- #
# Tier ranking
# --------------------------------------------------------------------------- #


def _rank_from_list(order: list[str]) -> dict[str, int]:
    """Weakest-first list -> {tier: rank}; later = stronger."""
    return {tier: idx for idx, tier in enumerate(order)}


def _infer_rank(item: CalibrationItem, item_outcomes: dict[str, bool]) -> dict[str, int]:
    """Infer a weakest->strongest rank for the tiers in play.

    Strategy, in order:

    1. If the item's ``expected_pass`` covers all observed tiers and induces a
       strict order (a tier expected to fail is weaker than one expected to
       pass), use that — but only when it is unambiguous (a single False<True
       boundary). Ties within the same expectation fall back to the default.
    2. Otherwise use the documented default rank (weak < medium < strong).

    The default is authoritative for the canonical tier names; ``expected_pass``
    only ever *refines* ordering between tiers the default cannot separate.
    """
    rank: dict[str, int] = {}
    for tier in item_outcomes:
        if tier in _DEFAULT_TIER_RANK:
            rank[tier] = _DEFAULT_TIER_RANK[tier]

    # Refine using expected_pass for tiers the default does not cover: a tier
    # expected to fail ranks below one expected to pass. We map expected-fail to
    # a low band and expected-pass to a high band, offset so they never collide
    # with the default's integer ranks.
    exp = item.expected_pass
    if exp:
        for tier in item_outcomes:
            if tier in rank:
                continue
            if tier in exp:
                rank[tier] = -100 if not exp[tier] else 100
    return rank
