# Wave 0 — locked contracts for the Phase-2 forks swarm

**Authored:** coordinator, 2026-06-01 swarm. **Branch:** `phase-2`. **Pairs with:** [`kickoff-forks-swarm.md`](kickoff-forks-swarm.md).

This file pins the two cross-cutting contracts the leaf agents author against, so each
leaf's output is verifiable against a fixed target (PIN_PER_STEP) and the loader/gates can
halt a bad block before integration (ANDON_AUTHORITY).

---

## Fork A — calibration item contract

New items are appended to [`src/ai_crucible/calibration/admission_pairs.json`](../../src/ai_crucible/calibration/admission_pairs.json)
(currently 51 items: 45 `known_diagnostic` + 6 `difficulty_anchor`; gold 26A/25B; difficulty
0.10–0.75, mean 0.52; ~95% numeric/arithmetic flaw families). The **loader is the verifier**
([`loader.py`](../../src/ai_crucible/calibration/loader.py)): it rejects unknown keys and
duplicate ids.

### Why we expand (the saturation problem)
The first corrected run kept only **15 of 51** discriminating items (IRT prune) — the strong
judges saturate at the top. Top judges should sit near the **~64% JudgeBench ceiling**
(arXiv:2410.12784), not 100%. The fix is more *plausible-vs-subtly-wrong* pairs centered at
medium difficulty with a hard tail (PSN-IRT, arXiv:2505.15055), in **new** constructs the
current arithmetic-heavy set doesn't cover.

### Record schema (the only allowed keys)
| key | rule |
|---|---|
| `id` | unique; **leaf-prefixed** (see table) — collision-proof across leaves |
| `category` | `known_diagnostic` (discriminator) or `difficulty_anchor` (easy ladder rung) |
| `construct` | short noun phrase, style `"judge a <thing>"`; **must be new** |
| `confound_controlled` | short phrase naming the controlled confound (e.g. `"execute both loops"`) |
| `prompt` | the exact template below, ending in the literal trailing line |
| `gold` | `"A"` or `"B"` (grading-side; never shown to the model) |
| `difficulty` | float; diagnostics 0.55–0.85, anchors ~0.20 |
| `expected_pass` | `{"strong": bool, "weak": bool}` — diagnostics `{strong:true, weak:false}`; anchors `{strong:true, weak:true}` |
| `metadata` | `{"flaw_family": "<new-slug>", "correct_side": "<== gold>"}` |

`discrimination` is optional and omitted (fit later by the IRT screen). `correct_side` always
equals `gold` (existing convention — both name which letter holds the correct answer).
`known_impossible` is **not used**: it is incoherent for a forced-choice "exactly one is
correct" item (a 50% baseline means a pass isn't a leakage signal). Documented here so the
omission is loud, not silent.

### Prompt template (verbatim — the `\n` are real newlines in the JSON string)
```
You are an impartial judge. For the question below, exactly one of the two candidate answers is correct and the other is subtly wrong. Decide which is correct.

Question: <QUESTION>
Candidate A: <ANSWER A>
Candidate B: <ANSWER B>

Which candidate is correct? Reply with exactly one letter: A or B.
```
The other candidate must be a **subtle, plausible near-miss** — not absurd. If a genuinely
subtle wrong answer can't be authored for an item, **drop the item** rather than ship a
trivial distractor (ANDON: a weak item just gets IRT-pruned anyway).

### Leaf split (DECOMPOSE_BY_SECRETS — disjoint id prefix + disjoint flaw families)
Each leaf authors **7 items**: 6 `known_diagnostic` (≥1 in the 0.75–0.85 hard tail) + 1
`difficulty_anchor` easy rung (~0.20). Per-leaf gold target keeps the global set balanced
(existing 26A/25B + 21A/21B → ~47A/46B).

| Leaf | id prefix | construct domain | gold target | forbidden (reuse) |
|---|---|---|---|---|
| 1 code-semantics | `code-` | mutation/aliasing, floor-div, slicing bounds, short-circuit, late-binding closures, `is` vs `==` | 4A/3B | list-comp, binary, boolean (already covered) |
| 2 logic/quantifiers | `logic-` | ∀/∃ swap, affirming-consequent, vacuous truth, De Morgan, necessary-vs-sufficient | 3A/4B | undistributed_middle |
| 3 unit/dimensional | `unit-` | C↔F offset, area-squares/volume-cubes, rate×time, SI-prefix steps, speed-unit | 4A/3B | — |
| 4 fabricated-fact | `fact-` | one false fact among true: capitals, author↔work, element symbols, event years | 3A/4B | plausible_wrong_fact, fabricated_default, fabricated_value_in_real_list |
| 5 statistical-trap | `stat-` | base-rate neglect, conditional inversion, Simpson reversal, median-vs-mean skew, prosecutor fallacy | 4A/3B | reported_mean_as_median, unweighted_mean, divided_by_wrong_n |
| 6 precedence | `prec-` | boolean and/or/not, exponent right-assoc, unary-minus-vs-power, bitwise-vs-comparison | 3A/4B | precedence_error, left_to_right_error |

`flaw_family` slugs must be **new** (the 46 existing families are reserved). Each item's
flaw must be genuine and checkable — the *gold* side is provably correct.

### Verify (integration gate — ANDON halts on any failure)
1. `load_default()` / `load_items()` loads the merged file clean (no unknown-key / dup-id error).
2. Gold balance ≈ 50/50; every diagnostic prompt ends with the exact trailing line.
3. `uv run ruff check .` clean; `uv run pytest -q` green ×1 (×3 before commit).
4. (GPU-gated, Fork B) re-pilot keeps **> 15** discriminating items.

---

## Fork C — human alt-test label contract

Retires the **circular** model-jury ω (`_ALT_TEST_CAVEAT`, [`run.py`](../../src/ai_crucible/characterize/run.py))
by feeding **real human annotators** into the existing
[`alt_test_omega`](../../src/ai_crucible/characterize/metrics.py) leave-one-out. The model-jury
bias this fixes is canon (Panickssery 2024 self-preference, ~20–40pp — see `memory/crucible.md`).

### `human_labels.json` schema (locked core shape)
```json
{
  "schema_version": 1,
  "annotators": { "<annotator_id>": { "tier": "expert|skilled|crowd" } },
  "labels": {
    "<item_id>": { "<annotator_id>": "A", "<annotator_id>": "B" }
  }
}
```
- `labels[item_id][annotator_id]` is a verdict in the **same categorical space as `gold`** (`A`/`B`).
- The loader builds `{annotator_id: [JudgmentRecord(item_id, model_id=annotator_id, predicted=verdict, gold=item.gold)]}`.
- The judge-under-test's own records go under the reserved `"judge"` key; humans are the peers.
- Calderon 2025 (arXiv:2501.10970) floor: **≥3 annotators, ≥30 items**; ε per tier
  (0.2 expert / 0.15 skilled / 0.1 crowd) — exact UI/format/adjudication settled by the
  study-swarm before the loader's validation thresholds are fixed.

### Caveat retirement plan (honesty surface — conditional, not deleted)
`_ALT_TEST_CAVEAT` is made **conditional**, not removed:
- **No `--human-labels`** → model-jury bootstrap path stays, caveat stays loud
  (`alt_test_reference: "model-jury-bootstrap"`). ω remains circular and says so.
- **`--human-labels <path>` (validated ≥3/≥30)** → ω is human-grounded;
  `alt_test_reference: "human"`, caveat replaced with a grounded note citing Calderon 2025.

This ships both paths and retires the circular caveat *exactly when humans are present* —
never silently.

---

## Standards compliance (the six — Wave 0 contract artifact)
- **PIN_PER_STEP — 3:** this file *is* the pin — each leaf's id prefix, gold target,
  difficulty band, forbidden families, and the verbatim prompt template are fixed here and
  committed; the loader replays the verdict deterministically.
- **ANDON_AUTHORITY — 2:** integration gate above halts on loader/ruff/pytest failure before
  any block is merged; weak items are dropped, not shipped.
- **NAMED_COMPENSATORS — 2 (no skip):** irreversible calls = the `git commit`/`git push` and
  the `admission_pairs.json` write; compensator table in the kickoff governs them.
- **DECOMPOSE_BY_SECRETS — 3:** leaves are disjoint id-prefix + disjoint flaw-family slices;
  the human-label schema is fully isolated from the item set.
- **UNCERTAINTY_GATED_HUMANS — 3:** Fork B (GPU) and any `main` merge are director-gated;
  Fork C's label thresholds are gated behind the study-swarm because the design is uncertain.
- **EXTERNAL_VERIFIER — 3:** the loader verifies items; a *different agent* runs the composed
  re-audit; the study-swarm's citations get a retrieval-oracle existence check before lock;
  Fork C's whole purpose is replacing the circular model-jury reference with a human one.
