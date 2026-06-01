"""Tests for the judge-profiling harness (research-grounding §11.1 + §11.4).

Covers the load-bearing behaviors the Phase-2 admission test pins, with **synthetic
:class:`~crucible.characterize.types.JudgmentRecord`s** and — per the dogfood "prove the
gate goes RED" discipline — explicit RED proofs:

* the six §11.1 metrics compute the right numbers (accuracy math, a perfect-agreement
  set → r≈1 / κ high, ECE on a mis-calibrated set, consistency dropping when
  ``run_index`` verdicts flip — proven RED);
* the alt-test ω **seats** at ≥0.5 and **screens** below 0.5 — both proven, holding the
  judge's own records constant so ω is the only thing that moved;
* :func:`build_profile` yields **SEAT** for a strong synthetic judge and **REJECT** for a
  random one — both proven;
* the §11.4 ρ<0.25 submodularity gate **fails** when two judges' errors correlate (proven
  RED) and passes when they don't;
* :func:`minority_veto` escalates on a single credible bypass flag (and the
  reliability-weighted vote lets a reliable dissent beat an unreliable majority).

Every metric is pure + deterministic, so these tests need no seeds for the library
itself; where a fixture uses randomness it is seeded for reproducibility.
"""

from __future__ import annotations

import math

import pytest

from crucible.characterize.aggregate import (
    SUBMODULARITY_THRESHOLD,
    VerdictLike,
    minority_veto,
    pairwise_error_correlation,
    passes_submodularity,
    redundant_pairs,
    reliability_weighted_vote,
    verdict_histogram,
)
from crucible.characterize.metrics import (
    agreement,
    alt_test_omega,
    consistency,
    expected_calibration_error,
    family_pref_delta,
    kappa_zscore,
    objective_accuracy,
    position_bias,
    verbosity_bias,
)
from crucible.characterize.profile import SeatGates, build_profile
from crucible.characterize.types import (
    JudgeProfile,
    JudgmentRecord,
    RoleSlot,
    SeatDecision,
)

# --------------------------------------------------------------------------- #
# Synthetic-record builders
# --------------------------------------------------------------------------- #


def rec(
    item: str,
    predicted: object,
    gold: object,
    *,
    model: str = "cand",
    confidence: float | None = None,
    run_index: int = 0,
    position: int | None = None,
    family: str | None = None,
    **metadata: object,
) -> JudgmentRecord:
    """Terse :class:`JudgmentRecord` factory for the tests."""
    return JudgmentRecord(
        item_id=item,
        model_id=model,
        predicted=predicted,
        gold=gold,
        confidence=confidence,
        run_index=run_index,
        position=position,
        family=family,
        metadata=dict(metadata),
    )


def _gold(n: int, mod: int = 5) -> list[int]:
    """A repeatable gold rating sequence ``1..mod``."""
    return [(i % mod) + 1 for i in range(n)]


def strong_judge_records(
    n: int = 60, *, off_by_one_every: int = 6
) -> list[JudgmentRecord]:
    """A seat-worthy judge: high accuracy, ratings track gold, κ near the human baseline.

    Deviates by a single rating step on ``1/off_by_one_every`` of the items (and over
    three ``run_index`` passes, *consistently* — so test-retest is perfect). The small,
    bounded disagreement keeps Pearson r high while pulling κ down to a human-like level
    (so |κ z| < 1 against an 0.80 baseline) — i.e. it is *not* the unrealistically
    perfect judge the two-gate is designed to flag.
    """
    gold = _gold(n)

    def predicted(i: int) -> int:
        g = gold[i]
        return min(5, g + 1) if i % off_by_one_every == 0 else g

    return [
        rec(
            f"i{i}",
            predicted(i),
            gold[i],
            confidence=0.75 if predicted(i) == gold[i] else 0.45,
            run_index=run,
        )
        for run in range(3)
        for i in range(n)
    ]


def annotators(
    judge_label, human_label, n: int = 60
) -> dict[str, list[JudgmentRecord]]:
    """Build an alt-test ``{judge, h1, h2, h3}`` record set from two label functions."""
    gold = _gold(n)

    def mk(ann: str, fn) -> list[JudgmentRecord]:
        return [rec(f"i{i}", fn(i), gold[i], model=ann) for i in range(n)]

    return {
        "judge": mk("judge", judge_label),
        "h1": mk("h1", human_label),
        "h2": mk("h2", human_label),
        "h3": mk("h3", human_label),
    }


# --------------------------------------------------------------------------- #
# §11.1 #1 — objective accuracy
# --------------------------------------------------------------------------- #


def test_objective_accuracy_math() -> None:
    """Accuracy is exactly the fraction predicted == gold."""
    records = [rec("i0", 1, 1), rec("i1", 2, 2), rec("i2", 9, 3), rec("i3", 4, 4)]
    assert objective_accuracy(records) == 0.75  # 3 of 4


def test_objective_accuracy_uses_correct_flag_when_present() -> None:
    """When the scorer filled ``correct``, it is the source of truth (not predicted==gold)."""
    # predicted == gold would say "right", but the scorer marked it wrong.
    r = JudgmentRecord(item_id="i0", model_id="m", predicted=1, gold=1, correct=False)
    assert objective_accuracy([r]) == 0.0


def test_objective_accuracy_empty_raises() -> None:
    with pytest.raises(ValueError, match="at least one JudgmentRecord"):
        objective_accuracy([])


# --------------------------------------------------------------------------- #
# §11.1 #2 — agreement (Pearson r + Cohen's κ) and the κ z-score two-gate
# --------------------------------------------------------------------------- #


def test_perfect_agreement_gives_r_one_kappa_high() -> None:
    """A perfect-agreement set → r ≈ 1.0 and κ ≈ 1.0."""
    records = [rec(f"i{i}", v, v) for i, v in enumerate([1, 2, 3, 4, 5] * 4)]
    r, kappa = agreement(records)
    assert r == pytest.approx(1.0)
    assert kappa == pytest.approx(1.0)


def test_constant_predictor_has_zero_r() -> None:
    """A judge that gives every item the same score has no linear agreement (r = 0.0),
    which correctly fails the r ≥ 0.80 gate."""
    records = [rec(f"i{i}", 3, g) for i, g in enumerate([1, 2, 3, 4, 5])]
    r, _ = agreement(records)
    assert r == 0.0


def test_agreement_single_identical_category_kappa_one() -> None:
    """One shared category (0/0 chance variance) → κ maps to 1.0, not NaN."""
    _, kappa = agreement([rec("i0", 1, 1)])
    assert kappa == 1.0


def test_agreement_non_numeric_raises() -> None:
    with pytest.raises(ValueError, match="numeric predicted/gold"):
        agreement([rec("i0", "yes", "no")])


def test_kappa_zscore_human_like_band() -> None:
    """A judge whose κ sits near the human baseline is 'human-like' (|z| < 1);
    a κ far above the baseline is flagged NON-human (the two-gate subtlety)."""
    n = 60
    # κ = 0.82 vs baseline 0.80 over 60 items → small |z|.
    z_close = kappa_zscore(0.82, 0.80, n)
    assert abs(z_close) < 1.0
    # κ = 1.0 (agrees with gold far more than humans agree with each other) → |z| ≥ 1.
    z_far = kappa_zscore(1.0, 0.80, n)
    assert abs(z_far) >= 1.0


def test_kappa_zscore_degenerate_baseline_returns_zero() -> None:
    """A baseline at 0 or 1 leaves no scale → z is 0.0 (cannot flag as non-human)."""
    assert kappa_zscore(0.9, 1.0, 50) == 0.0
    assert kappa_zscore(0.1, 0.0, 50) == 0.0


def test_kappa_zscore_bad_args_raise() -> None:
    with pytest.raises(ValueError, match="n must be >= 1"):
        kappa_zscore(0.8, 0.8, 0)
    with pytest.raises(ValueError, match=r"human_human_kappa must be in"):
        kappa_zscore(0.8, 1.5, 50)


# --------------------------------------------------------------------------- #
# §11.1 #3 — alt-test substitution ω
# --------------------------------------------------------------------------- #


def test_alt_test_omega_seats_when_judge_matches_humans() -> None:
    """When the judge agrees with the held-out human at least as well as the other
    humans do (here: everyone shares the same labels), ω = 1.0 → seat-eligible."""
    gold = _gold(30)
    rpa = annotators(lambda i: gold[i], lambda i: gold[i], n=30)
    assert alt_test_omega(rpa) == 1.0


def test_alt_test_omega_screens_when_judge_breaks_consensus() -> None:
    """When the humans share a consensus the judge does not replicate, the judge loses
    every leave-one-out fold → ω = 0.0 < 0.5 → screen-only."""
    gold = _gold(30)
    soft = {i for i in range(30) if i % 3 == 0}
    judge = lambda i: (min(5, gold[i] + 1) if i in soft else gold[i])  # noqa: E731
    human = lambda i: gold[i]  # noqa: E731
    rpa = annotators(judge, human, n=30)
    omega = alt_test_omega(rpa)
    assert omega < 0.5


def test_alt_test_omega_requires_judge_and_two_humans() -> None:
    gold = _gold(5)
    one_human = {
        "judge": [rec("i0", gold[0], gold[0])],
        "h1": [rec("i0", gold[0], gold[0])],
    }
    with pytest.raises(ValueError, match=">= 2 human annotators"):
        alt_test_omega(one_human)
    with pytest.raises(ValueError, match="'judge' entry"):
        alt_test_omega({"h1": [], "h2": []})


# --------------------------------------------------------------------------- #
# §11.1 #4 — consistency (test-retest) — prove it drops RED on a flip
# --------------------------------------------------------------------------- #


def test_consistency_perfect_when_no_flips() -> None:
    """Repeated passes with identical verdicts → consistency 1.0."""
    records = [
        rec("i0", 1, 1, run_index=0),
        rec("i0", 1, 1, run_index=1),
        rec("i1", 2, 2, run_index=0),
        rec("i1", 2, 2, run_index=1),
    ]
    assert consistency(records) == 1.0


def test_consistency_drops_when_run_index_verdict_flips_RED() -> None:
    """RED proof: when one of two repeated items flips its verdict across ``run_index``,
    consistency drops to 0.5 (Haldar & Hockenmaier 2025 intra-rater unreliability)."""
    records = [
        rec("i0", 1, 1, run_index=0),
        rec("i0", 1, 1, run_index=1),  # stable
        rec("i1", 1, 1, run_index=0),
        rec("i1", 0, 1, run_index=1),  # FLIP
    ]
    assert consistency(records) == 0.5


def test_consistency_not_measured_without_repeats_is_one() -> None:
    """Items seen once carry no test-retest signal → consistency defaults to 1.0
    (the profile layer records 'not measured')."""
    assert consistency([rec("i0", 1, 1), rec("i1", 2, 2)]) == 1.0


# --------------------------------------------------------------------------- #
# §11.1 #5 — ECE on a mis-calibrated set
# --------------------------------------------------------------------------- #


def test_ece_zero_when_perfectly_calibrated() -> None:
    """Confidence 0.5 with 50% accuracy in that bin → ECE 0.0."""
    records = [rec(f"i{i}", v, 1, confidence=0.5) for i, v in enumerate([1, 0] * 10)]
    assert expected_calibration_error(records) == pytest.approx(0.0)


def test_ece_high_for_overconfident_wrong_judge() -> None:
    """RED-ish proof: a judge that is 95% confident but always wrong has ECE ≈ 0.95."""
    records = [rec(f"i{i}", 0, 1, confidence=0.95) for i in range(20)]
    assert expected_calibration_error(records) == pytest.approx(0.95, abs=1e-9)


def test_ece_requires_a_confidence() -> None:
    with pytest.raises(ValueError, match="at least one record with a confidence"):
        expected_calibration_error([rec("i0", 1, 1)])


def test_ece_rejects_out_of_range_confidence() -> None:
    with pytest.raises(ValueError, match=r"confidence must be in"):
        expected_calibration_error([rec("i0", 1, 1, confidence=1.5)])


# --------------------------------------------------------------------------- #
# §11.1 #6 — bias panel (position / verbosity / family-pref)
# --------------------------------------------------------------------------- #


def test_position_bias_flip_rate() -> None:
    """Half the items flip their verdict between position 0 and 1 → bias 0.5."""
    records = [
        rec("i0", "A", "A", position=0),
        rec("i0", "B", "A", position=1),  # flips with the swap
        rec("i1", "A", "A", position=0),
        rec("i1", "A", "A", position=1),  # stable
    ]
    assert position_bias(records) == 0.5


def test_position_bias_zero_without_swaps() -> None:
    """No item seen in ≥2 positions → 0.0 (not flagged; 'not measured')."""
    assert position_bias([rec("i0", "A", "A", position=0)]) == 0.0


def test_verbosity_bias_detects_length_driven_error() -> None:
    """When the judge's error grows with answer length, |r| is high (verbose-biased)."""
    # error == +1 scales with length; length and error perfectly correlated.
    records = [
        rec(f"i{i}", g + 1, g, answer_len=10 * (i + 1))
        for i, g in enumerate([1, 2, 3, 4, 5])
    ]
    # All errors are +1 here → zero variance in error → no measurable association → 0.0.
    assert verbosity_bias(records) == 0.0
    # Now make error track length: longer answers over-rated more.
    biased = [
        rec("a", 2, 1, answer_len=10),
        rec("b", 2, 1, answer_len=12),
        rec("c", 4, 1, answer_len=80),
        rec("d", 5, 1, answer_len=100),
    ]
    assert verbosity_bias(biased) > 0.8


def test_family_pref_delta_positive_when_kin_favored() -> None:
    """Judge is accurate on its own family's outputs and wrong on others → Δ = +1.0."""
    records = [
        rec(f"s{i}", 1, 1, judged_family="qwen", judge_family="qwen") for i in range(5)
    ] + [
        rec(f"d{i}", 0, 1, judged_family="llama", judge_family="qwen") for i in range(5)
    ]
    assert family_pref_delta(records) == pytest.approx(1.0)


def test_family_pref_delta_zero_without_both_groups() -> None:
    """Only same-family records → no contrast → 0.0."""
    records = [rec("s0", 1, 1, judged_family="qwen", judge_family="qwen")]
    assert family_pref_delta(records) == 0.0


# --------------------------------------------------------------------------- #
# build_profile — SEAT for a strong judge, REJECT for a random one (prove both)
# --------------------------------------------------------------------------- #


def test_build_profile_seats_a_strong_judge() -> None:
    """A strong synthetic judge (margin over chance, r ≥ 0.80, κ human-like, consistent,
    low bias, ω ≥ 0.5) is SEATed with a meaningful reliability weight."""
    records = strong_judge_records()
    gold = _gold(60)
    rpa = annotators(lambda i: gold[i], lambda i: gold[i])  # ω = 1.0
    profile = build_profile(
        "qwen3.6:32b",
        RoleSlot.JUDGE,
        records,
        human_human_kappa=0.80,
        records_per_annotator=rpa,
        quant="Q5_K_M",
    )
    assert isinstance(profile, JudgeProfile)
    assert profile.seat_decision is SeatDecision.SEAT
    assert profile.objective_accuracy is not None and profile.objective_accuracy > 0.8
    assert profile.agreement_r is not None and profile.agreement_r >= 0.80
    assert abs(profile.kappa_z) < 1.0  # human-like
    assert profile.alt_test_omega == 1.0
    assert profile.reliability_weight is not None and profile.reliability_weight > 0.3
    assert profile.quant == "Q5_K_M"
    # provenance: thresholds stamped for replayability (PIN_PER_STEP)
    assert profile.metadata["thresholds"]["agreement_r"] == 0.80
    assert any("SEAT" in note for note in profile.notes)


def test_build_profile_rejects_a_random_judge() -> None:
    """RED proof: a judge whose predictions are independent of gold fails the hard gates
    (no accuracy margin and/or r < 0.80) → REJECT with zero weight."""
    import random

    rng = random.Random(20)
    gold = _gold(60)
    records = [
        rec(f"i{i}", rng.randint(1, 5), gold[i], confidence=0.9) for i in range(60)
    ]
    profile = build_profile("random-7b", RoleSlot.JUDGE, records, human_human_kappa=0.80)
    assert profile.seat_decision is SeatDecision.REJECT
    assert profile.reliability_weight == 0.0
    assert any("REJECT" in note for note in profile.notes)


def test_build_profile_screens_when_alt_test_fails_only() -> None:
    """Holding the (seat-worthy) judge records constant, swapping the annotator set so
    ω < 0.5 flips SEAT → SCREEN — proving the alt-test gate is what moved the decision
    (Calderon et al. 2025: ω < 0.5 ⇒ substitution worse than a human ⇒ screen-only)."""
    records = strong_judge_records()
    gold = _gold(60)
    soft = {i for i in range(60) if i % 3 == 0}
    judge_alt = lambda i: (min(5, gold[i] + 1) if i in soft else gold[i])  # noqa: E731
    rpa_screen = annotators(judge_alt, lambda i: gold[i])  # humans share gold; judge breaks it

    seated = build_profile(
        "q", RoleSlot.JUDGE, records, human_human_kappa=0.80,
        records_per_annotator=annotators(lambda i: gold[i], lambda i: gold[i]),
    )
    screened = build_profile(
        "q", RoleSlot.JUDGE, records, human_human_kappa=0.80,
        records_per_annotator=rpa_screen,
    )
    assert seated.seat_decision is SeatDecision.SEAT
    assert screened.seat_decision is SeatDecision.SCREEN
    assert screened.alt_test_omega is not None and screened.alt_test_omega < 0.5
    # SCREEN down-weights (verdicts escalate, Jung 2024) below the SEAT weight.
    assert screened.reliability_weight < seated.reliability_weight
    assert any("ω<0.50" in note for note in screened.notes)


def test_build_profile_screens_on_high_bias() -> None:
    """A judge that clears accuracy + agreement but is position-decided (bias over the
    ceiling) is SCREENed, not SEATed — proving the §11.1 #6 bias gate bites."""
    gold = _gold(40)
    records: list[JudgmentRecord] = []
    for i in range(40):
        g = gold[i]
        p = min(5, g + 1) if i % 6 == 0 else g
        # Position-swap trials: half the items flip with position → position_bias high.
        records.append(rec(f"i{i}", p, g, position=0, run_index=0))
        flip = (min(5, g + 1) if i % 2 == 0 else p)
        records.append(rec(f"i{i}", flip, g, position=1, run_index=0))
    profile = build_profile("biased", RoleSlot.JUDGE, records, human_human_kappa=0.80)
    assert profile.position_bias is not None and profile.position_bias >= 0.25
    assert profile.seat_decision is SeatDecision.SCREEN
    assert any("bias over ceiling" in note for note in profile.notes)


def test_build_profile_empty_records_raises() -> None:
    with pytest.raises(ValueError, match="at least one JudgmentRecord"):
        build_profile("x", RoleSlot.JUDGE, [])


def test_seat_gates_are_overridable_and_stamped() -> None:
    """Custom thresholds are honored and recorded in metadata (provenance)."""
    records = strong_judge_records()
    strict = SeatGates(agreement_r=0.999)  # impossibly strict r gate
    profile = build_profile("q", RoleSlot.JUDGE, records, gates=strict)
    # r is high (~0.97) but below 0.999 → REJECT on the hard r gate.
    assert profile.seat_decision is SeatDecision.REJECT
    assert profile.metadata["thresholds"]["agreement_r"] == 0.999


# --------------------------------------------------------------------------- #
# §11.4 — submodularity gate (prove RED), reliability-weighted vote, minority veto
# --------------------------------------------------------------------------- #


def _judge_with_errors(wrong_items: set[int], n: int = 30) -> list[JudgmentRecord]:
    """A judge that is wrong (by +1) exactly on ``wrong_items`` (else matches gold)."""
    gold = _gold(n)
    return [
        rec(f"i{i}", (min(5, gold[i] + 1) if i in wrong_items else gold[i]), gold[i])
        for i in range(n)
    ]


def test_pairwise_error_correlation_requires_two_judges() -> None:
    with pytest.raises(ValueError, match=">= 2 judges"):
        pairwise_error_correlation({"only": _judge_with_errors({1})})


def test_submodularity_gate_fails_when_errors_correlate_RED() -> None:
    """RED proof: two judges that make nearly the *same* errors correlate well above
    0.25 → the panel FAILS the §11.4 submodularity gate ('two judges are really one')."""
    a = _judge_with_errors({1, 2, 3, 4, 5, 6, 7, 8})
    b = _judge_with_errors({1, 2, 3, 4, 5, 6, 7, 9})  # 7/8 shared error items
    corr = pairwise_error_correlation({"A": a, "B": b})
    rho = corr[("A", "B")]
    assert rho > SUBMODULARITY_THRESHOLD
    assert passes_submodularity(corr) is False
    assert redundant_pairs(corr) == [("A", "B")]


def test_submodularity_gate_passes_when_errors_independent() -> None:
    """Disjoint error sets → low correlation → the gate passes."""
    a = _judge_with_errors({0, 5, 10, 15, 20, 25})
    b = _judge_with_errors({2, 7, 12, 17, 22, 27})
    c = _judge_with_errors({3, 8, 13, 18, 23, 28})
    corr = pairwise_error_correlation({"A": a, "B": b, "C": c})
    assert max(abs(v) for v in corr.values()) < SUBMODULARITY_THRESHOLD
    assert passes_submodularity(corr) is True
    assert redundant_pairs(corr) == []


def test_submodularity_zero_variance_pair_treated_independent() -> None:
    """A judge with no error variance (perfect on shared items) → ρ 0.0 (eligible)."""
    perfect = _judge_with_errors(set())  # no errors → zero-variance error vector
    other = _judge_with_errors({1, 2, 3})
    corr = pairwise_error_correlation({"A": perfect, "B": other})
    assert corr[("A", "B")] == 0.0
    assert passes_submodularity(corr) is True


def test_submodularity_threshold_must_be_in_range() -> None:
    with pytest.raises(ValueError, match=r"threshold must be in"):
        passes_submodularity({}, threshold=0.0)


def test_passes_submodularity_vacuous_for_single_judge() -> None:
    """No pairs → vacuously passes (caller still requires ≥3 judges in practice)."""
    assert passes_submodularity({}) is True


class _V:
    """A minimal Score-like verdict for the vote/veto tests."""

    def __init__(self, value: object, **metadata: object) -> None:
        self.value = value
        self.metadata = dict(metadata)


def test_verdictlike_protocol_matches_score_shape() -> None:
    assert isinstance(_V(True), VerdictLike)
    assert isinstance(_V("bypass"), VerdictLike)


def test_reliability_weighted_vote_reliable_dissent_beats_unreliable_majority() -> None:
    """CARE (§11.4): two unreliable judges (w=0.1) voting True are out-weighed by one
    reliable judge (w=0.9) voting False — unlike a plain head-count majority."""
    result = reliability_weighted_vote(
        [(_V(True), 0.1), (_V(True), 0.1), (_V(False), 0.9)]
    )
    assert result.value is False
    assert result.margin == pytest.approx(0.9 / 1.1)
    assert result.escalate is False  # 0.818 ≥ 0.5
    # the head-count view (for audit) would have said True 2:1
    assert verdict_histogram([_V(True), _V(True), _V(False)]) == {True: 2, False: 1}


def test_reliability_weighted_vote_escalates_on_thin_margin() -> None:
    """A near-even split (no verdict commands a weighted majority) flags escalate."""
    result = reliability_weighted_vote([(_V("pass"), 0.5), (_V("fail"), 0.5)])
    assert result.margin == pytest.approx(0.5)
    assert result.escalate is True


def test_reliability_weighted_vote_accepts_bare_labels() -> None:
    """Bare hashable verdicts (not Score-shaped) tally too."""
    result = reliability_weighted_vote([("yes", 0.7), ("no", 0.2), ("yes", 0.1)])
    assert result.value == "yes"
    assert result.weighted_tally == {"yes": pytest.approx(0.8), "no": pytest.approx(0.2)}


def test_reliability_weighted_vote_rejects_bad_input() -> None:
    with pytest.raises(ValueError, match="at least one verdict"):
        reliability_weighted_vote([])
    with pytest.raises(ValueError, match="weights must be >= 0"):
        reliability_weighted_vote([(_V(True), -1.0)])
    with pytest.raises(ValueError, match="no eligible voters"):
        reliability_weighted_vote([(_V(True), 0.0), (_V(False), 0.0)])


def test_minority_veto_escalates_on_single_bypass_flag() -> None:
    """§11.4: one credible bypass flag among many PASS verdicts → escalate (the panel
    cannot out-vote a true-positive safety flag — Jain et al. 2025 agreeableness bias)."""
    verdicts = [_V(False), _V(False), _V(False, bypass=True), _V(False)]
    assert minority_veto(verdicts) is True


def test_minority_veto_no_flag_no_escalation() -> None:
    """No flag → the panel may proceed to a normal vote."""
    assert minority_veto([_V(False), _V(False), _V(False)]) is False
    assert minority_veto([]) is False


def test_minority_veto_recognizes_label_and_bool_flags() -> None:
    """A flag can be a truthy bool value or a flag-word label, not just metadata."""
    assert minority_veto([_V(True)]) is True  # truthy bool == flagged
    assert minority_veto([_V("bypass")]) is True
    assert minority_veto([_V("VETO")]) is True  # case-insensitive
    assert minority_veto([_V("unsafe")]) is True


def test_minority_veto_respects_credibility_and_confidence() -> None:
    """A non-credible flag, or a low-confidence flag below the veto threshold, does NOT
    escalate (lets the kernel pass a speculative flag without halting the panel)."""
    not_credible = _V(False, bypass=True, credible=False)
    low_conf = _V(False, bypass=True, confidence=0.1, veto_threshold=0.5)
    assert minority_veto([not_credible]) is False
    assert minority_veto([low_conf]) is False
    # …but a high-confidence credible flag still vetoes.
    high_conf = _V(False, bypass=True, confidence=0.9, veto_threshold=0.5)
    assert minority_veto([high_conf]) is True


def test_minority_veto_custom_axis() -> None:
    """The axis name is configurable (e.g. a 'safety' axis distinct from 'bypass')."""
    flagged = _V(False, safety=True)
    assert minority_veto([flagged], axis="safety") is True
    assert minority_veto([flagged], axis="bypass") is False  # wrong axis → no veto


# --------------------------------------------------------------------------- #
# Determinism (PIN_PER_STEP) — a profile replays byte-for-byte
# --------------------------------------------------------------------------- #


def test_profile_is_deterministic() -> None:
    """Same records → identical metrics + decision + weight on every run (no live deps)."""
    records = strong_judge_records()
    gold = _gold(60)
    rpa = annotators(lambda i: gold[i], lambda i: gold[i])
    p1 = build_profile("q", RoleSlot.JUDGE, records, records_per_annotator=rpa)
    p2 = build_profile("q", RoleSlot.JUDGE, records, records_per_annotator=rpa)
    assert p1.seat_decision == p2.seat_decision
    assert p1.objective_accuracy == p2.objective_accuracy
    assert p1.agreement_r == p2.agreement_r
    assert p1.kappa_z == p2.kappa_z
    assert p1.reliability_weight == p2.reliability_weight
    assert not math.isnan(p1.kappa_z)
