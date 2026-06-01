"""The seat-or-screen admission test — turn metrics into a :class:`SeatDecision`.

:func:`build_profile` runs the six §11.1 metrics (:mod:`crucible.characterize.metrics`)
over a model's :class:`~crucible.characterize.types.JudgmentRecord`s and applies the
**seat gates** to produce a :class:`~crucible.characterize.types.JudgeProfile` with a
SEAT / SCREEN / REJECT decision, human-legible ``notes`` explaining *why*, and a derived
``reliability_weight`` for the panel aggregator (:mod:`crucible.characterize.aggregate`).

The gate ladder (research-grounding §11.1, in decreasing severity):

* **REJECT** — the judge is not usable for this role at all:
    - objective accuracy has **no real margin over chance** — judged by the Wilson 95%
      lower bound being ≤ 0.5 (the §1 small-N-admissible test reused from
      ``crucible.scoring.stats``; a point estimate of 0.55 on 20 items is *not* a
      margin), **or**
    - hard agreement failure: Pearson ``r < 0.80`` (the §11.1 #2 first gate). A judge
      whose ratings don't even correlate with gold cannot be reliability-weighted into a
      panel.
* **SCREEN** — usable only as a *cheap pre-filter whose verdicts are always escalated,
  never final* (Jung, Brahman & Choi 2024, "Trust or Escalate", arXiv:2407.18370 — an
  all-open panel is trustworthy precisely when it abstains-and-escalates). A model lands
  here when it clears the REJECT bar but trips any of:
    - alt-test ``ω < 0.5`` — substitution is *not* acceptable (Calderon et al. 2025,
      arXiv:2501.10970): it is worse than swapping in a human, so it can pre-filter but
      its verdict must be checked.
    - κ is **not human-like** (``|z| ≥ 1`` vs the human–human baseline — Han et al.
      2025, arXiv:2510.09738): it correlates but its agreement structure is off.
    - **unacceptable consistency or bias** — test-retest below floor, or a bias metric
      (position / verbosity / family-pref) over threshold. A judge whose verdict flips on
      re-run, or that is decided by position/length/kinship, can screen but not seat.
* **SEAT** — full panel member (reliability-weighted): clears the margin, ``r ≥ 0.80``,
  ``|κ z| < 1``, ``ω ≥ 0.5``, consistency ≥ floor, and every bias under threshold.

``reliability_weight`` (consumed by CARE-style aggregation, §11.4) is derived only for
SEAT/SCREEN models (REJECT → ``0.0``). It rewards agreement + consistency + calibration
and penalizes bias, so a strong-but-imperfect judge counts for more than a marginal one
without any judge dominating the vote. SCREEN models get a hard down-weight (their
verdicts escalate, so they should barely move the aggregate).

**Standards compliance (the six)** — the binding section for this domain:

- **PIN_PER_STEP — 3.** Every metric is a pure deterministic reduction over the records;
  given a pinned ``(model, quant, prompt, fixture-hash)`` the resulting profile is
  byte-for-byte reproducible. Thresholds are module constants (below), not hidden magic,
  so a profile carries its own provenance in ``metadata["thresholds"]``.
- **ANDON_AUTHORITY — 2.** A single failed hard gate halts promotion: REJECT stops the
  model joining the panel; the bypass-axis ``minority_veto`` (in ``aggregate``) lets one
  credible flag halt an out-vote. Bad judges never propagate into the aggregate.
- **NAMED_COMPENSATORS — n/a (skip).** ``build_profile`` performs **no irreversible tool
  call** — it is a pure function returning a dataclass (no publish/push/release/DB
  write). Per the workflow-standards skip rule, a compensators table is not required for
  a pure in-memory computation; the calling harness owns any persistence + its undo.
- **DECOMPOSE_BY_SECRETS — 3.** The gold labels live *in the records the grader supplies*,
  not in the profiled model; the profile module never sees a model runtime. Metrics,
  gate logic, and aggregation are three files split by what changes together (§10.6).
- **UNCERTAINTY_GATED_HUMANS — 3.** SCREEN *is* the uncertainty gate: an admitted-but-
  uncertain judge's verdicts are flagged for escalation (Jung 2024) rather than trusted;
  ``notes`` frame the decision contrastively ("clears r/accuracy; SCREEN because ω<0.5").
- **EXTERNAL_VERIFIER — 3.** The whole point of the panel these profiles compose is that
  no model verifies its own family's output; ``family_pref_delta`` *measures* the bias
  this guards against, and ``aggregate.passes_submodularity`` refuses two judges whose
  *errors* correlate (a within-family pair masquerading as two verifiers).
"""

from __future__ import annotations

from dataclasses import dataclass

from crucible.characterize import metrics as M
from crucible.characterize.types import (
    JudgeProfile,
    JudgmentRecord,
    RoleSlot,
    SeatDecision,
)
from crucible.scoring.stats import wilson_interval

__all__ = ["SeatGates", "build_profile"]


@dataclass(frozen=True, slots=True)
class SeatGates:
    """The §11.1 seat-gate thresholds — frozen so a profile run is replayable.

    Defaults encode the research-grounding numbers; a caller may tighten/loosen them
    per role (e.g. a CohortSolver tolerates more bias than a Judge) and the chosen
    values are stamped into ``JudgeProfile.metadata["thresholds"]`` for provenance.
    """

    #: Wilson 95% lower bound on objective accuracy must exceed this (a real margin
    #: over chance, not a point estimate — §11.1 #1, §1 small-N admissibility).
    accuracy_floor: float = 0.50
    #: Target point accuracy worth noting (JudgeBench ≥0.60 — §11.1 #1). Not a hard
    #: gate by itself; the *margin* (Wilson lower > accuracy_floor) is the gate.
    accuracy_target: float = 0.60
    #: Pearson r hard gate (§11.1 #2 first gate).
    agreement_r: float = 0.80
    #: |κ z| must be below this to be "human-like" (§11.1 #2 second gate).
    kappa_z_abs: float = 1.0
    #: alt-test ω seat threshold (§11.1 #3).
    alt_test_omega: float = 0.50
    #: test-retest consistency floor (§11.1 #4): 1 − flip-rate must be ≥ this.
    consistency_floor: float = 0.80
    #: each bias metric (position / verbosity / |family-pref|) must be below this.
    bias_ceiling: float = 0.25
    #: ECE above this is "overconfident" — soft signal, down-weights, never rejects.
    ece_soft_ceiling: float = 0.15


def _wilson_lower_accuracy(records: list[JudgmentRecord]) -> tuple[float, float]:
    """Return ``(point_accuracy, wilson_95_lower)`` for the objective-accuracy gate.

    Reuses ``crucible.scoring.stats.wilson_interval`` (no edit to that module) — the
    same small-N-admissible interval the §1 graduation rule is built on. The *lower*
    bound is the gate: a judge graduates onto the panel only when even the conservative
    bound clears chance. ``successes`` is recovered from the public
    :func:`~crucible.characterize.metrics.objective_accuracy` (× n) so this module never
    reaches into a metrics-private helper.
    """
    n = len(records)
    point = M.objective_accuracy(records)
    successes = round(point * n)
    lower, _upper = wilson_interval(successes, n, conf=0.95)
    return point, lower


def _reliability_weight(
    *,
    accuracy: float,
    r: float,
    kappa_z_abs: float,
    consistency: float,
    ece: float | None,
    max_bias: float,
    decision: SeatDecision,
    gates: SeatGates,
) -> float:
    """Derive the CARE-style reliability weight (§11.4) from the metrics.

    REJECT → 0.0 (it never votes). Otherwise we build a weight in ``(0, 1]`` that
    rewards agreement + consistency + calibration and penalizes bias and a non-human κ,
    so the aggregator gives a strong judge proportionally more pull without letting any
    one judge dominate. SCREEN models are additionally halved — their verdicts are meant
    to escalate (Jung 2024), so they should barely move the aggregate.

    The form is a bounded product of unit factors (each in ``(0, 1]``); it is monotone
    in every "good" metric and deterministic, which is all the aggregator needs (CARE,
    Zhao et al. 2026, arXiv:2603.00039 — reliability-weighting beats majority vote).
    """
    if decision is SeatDecision.REJECT:
        return 0.0

    # Each factor maps a metric to (0, 1]; weak metrics shrink the product.
    f_acc = max(0.0, min(1.0, (accuracy - 0.5) / 0.5))  # 0.5->0, 1.0->1
    f_r = max(0.0, min(1.0, r))                          # negative r -> 0
    f_cons = max(0.0, min(1.0, consistency))
    f_bias = max(0.0, 1.0 - max_bias)                    # more bias -> smaller
    # κ z penalty: human-like (|z|<1) ~ full credit; far-from-human shrinks it.
    f_kappa = 1.0 / (1.0 + max(0.0, kappa_z_abs - gates.kappa_z_abs))
    # ECE penalty: only bites past the soft ceiling (calibration is a soft signal).
    f_ece = 1.0 if ece is None else 1.0 / (1.0 + max(0.0, ece - gates.ece_soft_ceiling))

    weight = f_acc * f_r * f_cons * f_bias * f_kappa * f_ece
    if decision is SeatDecision.SCREEN:
        weight *= 0.5
    # Floor a seated/screened judge slightly above 0 so a barely-passing judge still
    # casts a (tiny) vote rather than being silently dropped.
    return float(max(1e-3, min(1.0, weight)))


def build_profile(
    model_id: str,
    role: RoleSlot,
    records: list[JudgmentRecord],
    *,
    human_human_kappa: float = 0.80,
    records_per_annotator: dict[str, list[JudgmentRecord]] | None = None,
    quant: str | None = None,
    gates: SeatGates | None = None,
) -> JudgeProfile:
    """Run the §11.1 6-metric admission test and return a gated :class:`JudgeProfile`.

    Computes the six metrics over ``records``, applies the seat gates, and derives the
    seat decision + reliability weight. ``notes`` records, in order, every gate outcome
    in contrastive form (UNCERTAINTY_GATED_HUMANS) so a human reading the profile sees
    exactly which gate moved the decision.

    Args:
        model_id: the model being profiled (e.g. ``"qwen3.6:32b"``).
        role: the :class:`~crucible.characterize.types.RoleSlot` being tested for
            (Designer stays Claude and is never profiled here).
        records: the model's judgments on the calibration set (non-empty). Should
            include repeated ``run_index`` passes (for consistency), position-swap
            trials (for position bias), and family/length tags in ``metadata`` (for the
            bias panel) where those gates are to be exercised; gates whose data is
            absent are recorded as "not measured" and do **not** fail the model.
        human_human_kappa: the human–human baseline κ for the κ z-score two-gate
            (§11.1 #2). Defaults to 0.80 (a typical strong inter-annotator baseline).
        records_per_annotator: optional ``{annotator_id: [...]}`` including a ``"judge"``
            entry, used to compute the alt-test ω (§11.1 #3). When ``None``, ω is not
            measured and the alt-test gate is skipped (the model can still SEAT on the
            other gates, with a note); supply it to enforce the substitution gate.
        quant: the quantization level of the profiled model (recorded; §11.2 measures
            reliability across quant rather than assuming a floor).
        gates: override thresholds (defaults to :class:`SeatGates`).

    Returns:
        A fully-populated :class:`~crucible.characterize.types.JudgeProfile`.

    Raises:
        ValueError: if ``records`` is empty (propagated from the metrics).
    """
    if not records:
        raise ValueError("build_profile requires at least one JudgmentRecord")
    g = gates or SeatGates()
    n = len(records)
    # Distinct items = the independent-sample size for the κ z-score's standard error.
    # Test-retest *repeats* of the same item are NOT independent draws, so feeding the
    # raw record count (inflated k× by run_index passes) would shrink the SE k-fold and
    # spuriously flag a human-level κ as non-human. The z-test uses n_items.
    n_items = len({r.item_id for r in records})
    notes: list[str] = []

    # --- §11.1 #1 objective accuracy (margin over chance via Wilson lower) ---
    accuracy, acc_lower = _wilson_lower_accuracy(records)
    accuracy_ok = acc_lower > g.accuracy_floor
    if accuracy_ok:
        tgt = " (≥ target)" if accuracy >= g.accuracy_target else " (below 0.60 target)"
        notes.append(
            f"accuracy {accuracy:.3f}{tgt}; Wilson-95 lower {acc_lower:.3f} > "
            f"{g.accuracy_floor:.2f} → real margin over chance ✓"
        )
    else:
        notes.append(
            f"accuracy {accuracy:.3f}; Wilson-95 lower {acc_lower:.3f} ≤ "
            f"{g.accuracy_floor:.2f} → NO margin over chance ✗ (REJECT)"
        )

    # --- §11.1 #2 agreement two-gate (Pearson r, then κ z-score) ---
    r, kappa = M.agreement(records)
    kz = M.kappa_zscore(kappa, human_human_kappa, n_items)
    kz_abs = abs(kz)
    r_ok = r >= g.agreement_r
    kappa_human_like = kz_abs < g.kappa_z_abs
    notes.append(
        f"agreement r={r:.3f} ({'≥' if r_ok else '<'} {g.agreement_r:.2f}); "
        f"κ={kappa:.3f}, z vs human {kz:+.2f} "
        f"({'human-like' if kappa_human_like else 'NON-human'}, |z|"
        f"{'<' if kappa_human_like else '≥'}{g.kappa_z_abs:.0f})"
    )

    # --- §11.1 #3 alt-test substitution ω (optional data) ---
    omega: float | None = None
    omega_ok = True  # absent data does not fail the model (noted instead)
    if records_per_annotator is not None:
        omega = M.alt_test_omega(records_per_annotator)
        omega_ok = omega >= g.alt_test_omega
        notes.append(
            f"alt-test ω={omega:.3f} ({'≥' if omega_ok else '<'} "
            f"{g.alt_test_omega:.2f} → {'seat-eligible' if omega_ok else 'SCREEN-only'})"
        )
    else:
        notes.append("alt-test ω not measured (no per-annotator records supplied)")

    # --- §11.1 #4 consistency (test-retest) ---
    cons = M.consistency(records)
    item_counts: dict[str, int] = {}
    for x in records:
        item_counts[x.item_id] = item_counts.get(x.item_id, 0) + 1
    cons_measured = any(c >= 2 for c in item_counts.values())
    cons_ok = cons >= g.consistency_floor
    if cons_measured:
        notes.append(
            f"consistency {cons:.3f} ({'≥' if cons_ok else '<'} "
            f"{g.consistency_floor:.2f} test-retest floor)"
        )
    else:
        notes.append("consistency not measured (no repeated run_index passes)")
        cons_ok = True  # cannot fail a gate we have no data for

    # --- §11.1 #5 calibration (ECE) — soft signal ---
    ece: float | None = None
    if any(x.confidence is not None for x in records):
        ece = M.expected_calibration_error(records)
        overconf = ece > g.ece_soft_ceiling
        notes.append(
            f"ECE {ece:.3f} ({'over' if overconf else 'within'} "
            f"{g.ece_soft_ceiling:.2f} soft ceiling → "
            f"{'down-weight' if overconf else 'ok'})"
        )
    else:
        notes.append("ECE not measured (no confidences)")

    # --- §11.1 #6 bias panel (position / verbosity / family-pref) ---
    pos_b = M.position_bias(records)
    verb_b = M.verbosity_bias(records)
    fam_d = M.family_pref_delta(records)
    max_bias = max(pos_b, verb_b, abs(fam_d))
    bias_ok = max_bias < g.bias_ceiling
    notes.append(
        f"bias: position {pos_b:.3f}, verbosity {verb_b:.3f}, family-pref Δ {fam_d:+.3f}"
        f" → max {max_bias:.3f} ({'<' if bias_ok else '≥'} {g.bias_ceiling:.2f} ceiling)"
    )

    # --- Gate ladder → decision ---
    if not accuracy_ok or not r_ok:
        decision = SeatDecision.REJECT
        reason = "no accuracy margin" if not accuracy_ok else f"r<{g.agreement_r:.2f}"
        notes.append(f"DECISION: REJECT — hard gate failed ({reason})")
    elif not (kappa_human_like and omega_ok and cons_ok and bias_ok):
        decision = SeatDecision.SCREEN
        failed = [
            name
            for name, ok in (
                ("κ non-human", kappa_human_like),
                (f"ω<{g.alt_test_omega:.2f}", omega_ok),
                ("low consistency", cons_ok),
                ("bias over ceiling", bias_ok),
            )
            if not ok
        ]
        notes.append(
            "DECISION: SCREEN — clears REJECT bar but verdicts must escalate "
            f"(Jung 2024) due to: {', '.join(failed)}"
        )
    else:
        decision = SeatDecision.SEAT
        notes.append("DECISION: SEAT — all six gates pass; full reliability-weighted vote")

    weight = _reliability_weight(
        accuracy=accuracy,
        r=r,
        kappa_z_abs=kz_abs,
        consistency=cons,
        ece=ece,
        max_bias=max_bias,
        decision=decision,
        gates=g,
    )

    return JudgeProfile(
        model_id=model_id,
        role=role,
        n_items=n,
        quant=quant,
        objective_accuracy=accuracy,
        agreement_r=r,
        kappa_z=kz,
        alt_test_omega=omega,
        consistency=cons if cons_measured else None,
        ece=ece,
        position_bias=pos_b,
        verbosity_bias=verb_b,
        family_pref_delta=fam_d,
        reliability_weight=weight,
        seat_decision=decision,
        notes=notes,
        metadata={
            "human_human_kappa": human_human_kappa,
            "accuracy_wilson_lower": acc_lower,
            "kappa": kappa,
            "thresholds": {
                "accuracy_floor": g.accuracy_floor,
                "accuracy_target": g.accuracy_target,
                "agreement_r": g.agreement_r,
                "kappa_z_abs": g.kappa_z_abs,
                "alt_test_omega": g.alt_test_omega,
                "consistency_floor": g.consistency_floor,
                "bias_ceiling": g.bias_ceiling,
                "ece_soft_ceiling": g.ece_soft_ceiling,
            },
        },
    )
