"""Panel composition + aggregation (research-grounding §11.4).

Once individual models are profiled (:mod:`crucible.characterize.profile`), three
panel-level decisions remain — *who* sits together, *how* their verdicts combine, and
*when* a single dissent halts an out-vote:

1. :func:`pairwise_error_correlation` + :func:`passes_submodularity` — the **ρ < 0.25
   submodularity gate** (§11.4). Compose for low *error*-correlation, not nameplate
   family: "high agreement that tracks *joint errors* means two judges are really one."
   We correlate per-item **error** vectors (not raw verdicts), because two judges that
   are both right on the easy items and both wrong on the same hard items are
   redundant — a panel of clones gives the illusion of independent confirmation. This
   reuses crucible's existing ρ<0.25 submodularity gate (the Codex-Verify review-lens
   gate) over the calibration set.
2. :func:`reliability_weighted_vote` — **confounder-aware / reliability-weighted**
   aggregation (CARE, Zhao et al. 2026, arXiv:2603.00039 — beats majority vote and
   plain reliability-weighting, error ↓ up to 26.8%). Each judge's vote is weighted by
   the ``reliability_weight`` its :class:`~crucible.characterize.types.JudgeProfile`
   earned; the confounder-aware piece is that an *unreliable agreeing majority* cannot
   overpower a *reliable* dissent the way plain head-count majority does.
3. :func:`minority_veto` — a **minority veto on the bypass/safety axis** (§11.4). A
   single *credible* "this is a bypass/safety violation" flag **escalates** rather than
   getting out-voted, because agreeableness/positive bias is real (Jain et al. 2025,
   arXiv:2510.11822) — a panel will happily out-vote a true-positive safety flag. On the
   bypass axis, crucible fails *closed*: one credible veto → escalate to the Claude
   Designer / gold check (the §11.1 "Trust or Escalate" abstention path).

Everything here is pure + deterministic (PIN_PER_STEP): a panel decision replays
byte-for-byte from the same profiles + verdicts.

**Standards compliance (the six):** see :mod:`crucible.characterize.profile` for the
binding section. The two that live *here*: **EXTERNAL_VERIFIER — 3** —
:func:`passes_submodularity` is the structural refusal to seat two judges whose errors
correlate (a within-distribution pair masquerading as two independent verifiers), the
panel-side complement to the profile-side ``family_pref_delta``; **ANDON_AUTHORITY — 3**
— :func:`minority_veto` is a literal andon cord: one credible defect flag halts the
out-vote and escalates, bad output never propagates. NAMED_COMPENSATORS is **n/a (skip)**
— these are pure functions performing no irreversible tool call.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Hashable, Sequence
from typing import Protocol, runtime_checkable

import numpy as np
from scipy.stats import pearsonr

from crucible.characterize.types import JudgmentRecord

__all__ = [
    "SUBMODULARITY_THRESHOLD",
    "VerdictLike",
    "pairwise_error_correlation",
    "passes_submodularity",
    "reliability_weighted_vote",
    "VoteResult",
    "minority_veto",
]

#: The §11.4 panel error-correlation ceiling (Codex-Verify submodularity gate). Two
#: judges whose per-item errors correlate at or above this are "really one judge".
SUBMODULARITY_THRESHOLD: float = 0.25


@runtime_checkable
class VerdictLike(Protocol):
    """Structural type for an aggregable verdict — anything Score-shaped.

    A verdict only needs a ``value`` (the vote: a bool/discrete label, or a number).
    :class:`crucible.types.Score` satisfies this without importing it (keeps this module
    decoupled from the scoring layer — DECOMPOSE_BY_SECRETS), and so does any lightweight
    stand-in a test or the kernel passes.
    """

    value: object


def _error_vector(records: list[JudgmentRecord]) -> dict[str, float]:
    """Map ``item_id -> signed error`` for one judge.

    Error is ``predicted - gold`` when both are numeric (a rating delta), else a 0/1
    *mismatch* indicator (1.0 when ``predicted != gold``). Using error (not the raw
    verdict) is the load-bearing choice: §11.4 wants judges whose *mistakes* are
    uncorrelated, so the correlation must be over errors. When an item is judged
    multiple times (test-retest), the errors are averaged so each item contributes once.
    """
    sums: dict[str, float] = {}
    counts: dict[str, int] = {}
    for r in records:
        try:
            err = float(r.predicted) - float(r.gold)
        except (TypeError, ValueError):
            err = 0.0 if r.predicted == r.gold else 1.0
        sums[r.item_id] = sums.get(r.item_id, 0.0) + err
        counts[r.item_id] = counts.get(r.item_id, 0) + 1
    return {i: sums[i] / counts[i] for i in sums}


def pairwise_error_correlation(
    profiles_records: dict[str, list[JudgmentRecord]],
) -> dict[tuple[str, str], float]:
    """Pearson correlation of per-item **error** vectors for every judge pair — §11.4.

    Args:
        profiles_records: ``{judge_id: [JudgmentRecord, ...]}`` — each judge's records
            over the (shared) calibration set. At least two judges are required.

    Returns:
        ``{(judge_a, judge_b): rho}`` for every unordered pair (``a < b`` by id, so the
        key is canonical and each pair appears once). ``rho`` is the Pearson
        correlation of the two judges' error vectors over their **shared** items.

        Degenerate pairs map to ``0.0`` (treated as *independent*, the conservative
        reading that keeps the pair *eligible* under the gate): fewer than 2 shared
        items, or either error vector having zero variance (a judge that made the
        identical error on every shared item — there is no error *pattern* to correlate).

    Raises:
        ValueError: if fewer than two judges are supplied.
    """
    judges = sorted(profiles_records)
    if len(judges) < 2:
        raise ValueError(
            f"pairwise_error_correlation needs >= 2 judges, got {len(judges)}"
        )

    err_vecs = {j: _error_vector(profiles_records[j]) for j in judges}
    out: dict[tuple[str, str], float] = {}
    for i in range(len(judges)):
        for k in range(i + 1, len(judges)):
            a, b = judges[i], judges[k]
            va, vb = err_vecs[a], err_vecs[b]
            shared = sorted(va.keys() & vb.keys())
            if len(shared) < 2:
                out[(a, b)] = 0.0
                continue
            xa = np.array([va[s] for s in shared])
            xb = np.array([vb[s] for s in shared])
            if np.std(xa) == 0.0 or np.std(xb) == 0.0:
                out[(a, b)] = 0.0
                continue
            out[(a, b)] = float(pearsonr(xa, xb).statistic)
    return out


def passes_submodularity(
    corr: dict[tuple[str, str], float],
    threshold: float = SUBMODULARITY_THRESHOLD,
) -> bool:
    """The ρ < threshold panel gate (§11.4) — no pair of judges is redundant.

    A panel passes iff **every** pairwise error-correlation magnitude is strictly below
    ``threshold`` (default 0.25). The magnitude ``|ρ|`` is used: two judges whose errors
    are strongly *anti*-correlated are also non-independent in a way that breaks the
    "independent confirmation" assumption, though the common failure is positive
    correlation (clone judges). An empty ``corr`` (a single-judge "panel") trivially
    passes — there is no redundant pair — but the caller should still require ≥3 judges
    in practice (PoLL, §3).

    Args:
        corr: the pairwise correlations from :func:`pairwise_error_correlation`.
        threshold: the error-correlation ceiling (default
            :data:`SUBMODULARITY_THRESHOLD`); must be in ``(0, 1]``.

    Returns:
        ``True`` iff ``max |ρ| < threshold`` over all pairs (vacuously ``True`` if
        there are no pairs).

    Raises:
        ValueError: if ``threshold`` is not in ``(0, 1]``.
    """
    if not 0.0 < threshold <= 1.0:
        raise ValueError(f"threshold must be in (0, 1], got {threshold}")
    return all(abs(rho) < threshold for rho in corr.values())


def redundant_pairs(
    corr: dict[tuple[str, str], float],
    threshold: float = SUBMODULARITY_THRESHOLD,
) -> list[tuple[str, str]]:
    """The pairs that *fail* the §11.4 gate — for legible "why" reporting.

    Returns the judge pairs whose ``|ρ| >= threshold`` (the ones that make
    :func:`passes_submodularity` return ``False``), sorted by descending correlation so
    the worst offender is first. Empty when the panel passes.
    """
    if not 0.0 < threshold <= 1.0:
        raise ValueError(f"threshold must be in (0, 1], got {threshold}")
    bad = [(pair, abs(rho)) for pair, rho in corr.items() if abs(rho) >= threshold]
    bad.sort(key=lambda pr: pr[1], reverse=True)
    return [pair for pair, _ in bad]


class VoteResult:
    """The outcome of a reliability-weighted vote (§11.4).

    Attributes:
        value: the winning verdict (the label/number with the most weighted support).
        weighted_tally: ``{verdict: summed_weight}`` for every cast verdict.
        total_weight: the sum of all (eligible) weights.
        margin: winner_weight / total_weight in ``[0, 1]`` — the panel's weighted
            confidence in the winner (a confounder-aware "agreement"). 1.0 = unanimous
            by weight.
        escalate: ``True`` when the result is too close to trust (``margin`` at or below
            the ``escalate_below`` passed to :func:`reliability_weighted_vote`) — the
            §11.1 "Trust or Escalate" abstention signal.
    """

    __slots__ = ("value", "weighted_tally", "total_weight", "margin", "escalate")

    def __init__(
        self,
        value: object,
        weighted_tally: dict[object, float],
        total_weight: float,
        margin: float,
        escalate: bool,
    ) -> None:
        self.value = value
        self.weighted_tally = weighted_tally
        self.total_weight = total_weight
        self.margin = margin
        self.escalate = escalate

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return (
            f"VoteResult(value={self.value!r}, margin={self.margin:.3f}, "
            f"escalate={self.escalate}, tally={self.weighted_tally})"
        )


def reliability_weighted_vote(
    verdicts: Sequence[tuple[VerdictLike | object, float]],
    *,
    escalate_below: float = 0.5,
) -> VoteResult:
    """Aggregate ``(verdict, weight)`` pairs into one panel verdict (CARE, §11.4).

    Confounder-aware reliability-weighting (Zhao et al. 2026, arXiv:2603.00039): instead
    of one-judge-one-vote, each judge contributes its ``reliability_weight`` (from its
    :class:`~crucible.characterize.types.JudgeProfile`). This is what stops an unreliable
    agreeing majority from overpowering a reliable dissent — the failure mode plain
    majority vote has and plain reliability-weighting only partly fixes.

    Each ``verdict`` may be a :class:`VerdictLike` (anything with ``.value`` — e.g. a
    :class:`crucible.types.Score`) or a bare hashable label/number. Weighted support is
    summed per distinct verdict value; the winner is the value with the greatest summed
    weight. Ties are broken deterministically by first appearance (replayability,
    PIN_PER_STEP).

    Args:
        verdicts: the ``(verdict, weight)`` pairs (non-empty). Weights must be ≥ 0; a
            weight of 0 (e.g. a REJECT-profile judge) contributes nothing. The verdict
            values must be hashable (bool / int / float / str labels).
        escalate_below: if the winner's weighted ``margin`` (winner_weight /
            total_weight) is **at or below** this, the result is flagged
            ``escalate=True`` — the panel is too divided to trust and the kernel should
            escalate to the Claude Designer / gold check (Jung 2024). Default 0.5, i.e.
            *escalate unless a verdict commands a strict weighted majority (> 0.5)*. The
            boundary is inclusive so a dead-even split (margin exactly 0.5 — the
            **most** uncertain case) escalates rather than silently committing to the
            first-seen verdict the tiebreak happened to pick.

    Returns:
        A :class:`VoteResult`.

    Raises:
        ValueError: if ``verdicts`` is empty, all weights are 0 (no eligible voter), a
            weight is negative, or a verdict value is unhashable.
    """
    if not verdicts:
        raise ValueError("reliability_weighted_vote requires at least one verdict")
    if not 0.0 <= escalate_below <= 1.0:
        raise ValueError(f"escalate_below must be in [0, 1], got {escalate_below}")

    tally: dict[object, float] = {}
    order: list[object] = []
    total = 0.0
    for verdict, weight in verdicts:
        if weight < 0.0:
            raise ValueError(f"weights must be >= 0, got {weight}")
        value = verdict.value if isinstance(verdict, VerdictLike) else verdict
        if not isinstance(value, Hashable):
            raise ValueError(
                f"verdict value must be hashable to be tallied, got {value!r}"
            )
        if value not in tally:
            tally[value] = 0.0
            order.append(value)
        tally[value] += weight
        total += weight

    if total <= 0.0:
        raise ValueError(
            "reliability_weighted_vote has no eligible voters (all weights are 0)"
        )

    # Winner = max summed weight; ties broken by first appearance (stable).
    winner = max(order, key=lambda v: tally[v])
    margin = tally[winner] / total
    # Inclusive boundary: a margin *at or below* the line escalates, so a dead-even
    # split (margin == escalate_below == 0.5) is treated as "no majority → escalate".
    return VoteResult(
        value=winner,
        weighted_tally=tally,
        total_weight=total,
        margin=margin,
        escalate=margin <= escalate_below,
    )


def minority_veto(
    verdicts: Sequence[VerdictLike | object],
    axis: str = "bypass",
) -> bool:
    """A single credible flag on ``axis`` escalates rather than gets out-voted — §11.4.

    On the bypass/safety axis, crucible fails **closed**: one credible "this is a
    bypass / safety violation" verdict triggers escalation regardless of how many judges
    disagree. The justification is empirical — agreeableness/positive bias is real (Jain
    et al. 2025, arXiv:2510.11822), so a panel will out-vote a true-positive safety flag
    by sheer head-count. The asymmetry mirrors §10.5: a flag is strong evidence; the
    *absence* of a flag is not safety.

    A verdict "flags" the axis when, in priority order:

    * it is a :class:`VerdictLike` whose ``metadata`` carries a truthy entry for
      ``axis`` (e.g. ``{"bypass": True}``) — the structured, preferred signal; or
    * its ``value`` is a truthy bool (``True`` == "flagged"); or
    * its ``value`` is a string equal (case-insensitively) to the axis, or to one of
      ``{"bypass", "flag", "flagged", "veto", "unsafe", "violation"}`` — a label vote.

    A flag only counts as a **veto** when it is *credible*. Credibility is read from the
    flagging verdict's ``metadata``: a ``"credible"`` key (default ``True`` — a raised
    safety flag is presumed credible unless explicitly marked otherwise) AND, if present,
    a ``"confidence"`` ≥ ``metadata["veto_threshold"]`` (default 0.0, i.e. any
    confidence). This lets the kernel pass a low-confidence speculative flag that should
    *not* halt the panel, while a plain ``True`` with no metadata still vetoes
    (fail-closed default).

    Args:
        verdicts: the panel's per-judge verdicts on this axis (may be empty → no veto).
        axis: the safety axis name (default ``"bypass"``); also the metadata key checked.

    Returns:
        ``True`` if at least one credible flag is present (→ **escalate**); ``False``
        otherwise (the panel may proceed to a normal weighted vote).
    """
    axis_l = axis.lower()
    flag_labels = {axis_l, "bypass", "flag", "flagged", "veto", "unsafe", "violation"}

    for verdict in verdicts:
        meta = getattr(verdict, "metadata", None)
        is_verdictlike = isinstance(verdict, VerdictLike)
        value = verdict.value if is_verdictlike else verdict

        # A verdict flags the axis via any of three strategies (priority order):
        #   1. structured metadata (preferred): {axis: True};
        #   2. a truthy boolean value (True == "flagged");
        #   3. a label value matching the axis or a known flag word.
        flagged = (
            (isinstance(meta, dict) and bool(meta.get(axis)))
            or (isinstance(value, bool) and value)
            or (isinstance(value, str) and value.lower() in flag_labels)
        )
        if not flagged:
            continue

        # Credibility gate — a flag vetoes only if credible (presumed True) and, when a
        # confidence is given, it clears the veto threshold.
        if isinstance(meta, dict):
            if not bool(meta.get("credible", True)):
                continue
            conf = meta.get("confidence")
            thresh = float(meta.get("veto_threshold", 0.0))
            if conf is not None and float(conf) < thresh:
                continue
        return True  # one credible flag is enough — fail closed, escalate.

    return False


def verdict_histogram(verdicts: Sequence[VerdictLike | object]) -> dict[object, int]:
    """Unweighted ``{value: count}`` of the verdicts — a plain-majority view for audit.

    Provided alongside :func:`reliability_weighted_vote` so a transcript can record both
    the head-count majority and the reliability-weighted result (the gap between them is
    exactly the confounder CARE corrects for).
    """
    counts: Counter[object] = Counter()
    for verdict in verdicts:
        value = verdict.value if isinstance(verdict, VerdictLike) else verdict
        if not isinstance(value, Hashable):
            raise ValueError(f"verdict value must be hashable, got {value!r}")
        counts[value] += 1
    return dict(counts)
