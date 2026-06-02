# Calibration starter bank (FIXTURES / EXAMPLES)

This directory is a **small starter set** of calibration items (research-grounding
§11.3) — roughly 2–3 per category. It exists to:

1. exercise the loader (`crucible.calibration.loader.load_items` / `load_default`),
2. exercise the known-groups acceptance check (`crucible.calibration.known_groups`),
3. give an **authoring template** for the real bank.

> **These are examples, not the production calibration set.** The full ~40–60-item
> set is a later **director decision** (§11.7 — "the calibration items themselves
> (authoring the ~40–60 puzzles)" is explicitly deferred to the build). Do not
> treat these counts or items as the validated instrument.

## Layout

One JSON file per category, each a JSON array of item objects matching
`crucible.calibration.types.CalibrationItem`:

| File | Category | Pass-pattern law (§11.3) | Count |
|------|----------|--------------------------|-------|
| `known_trivial.json` | `known_trivial` | every tier must pass (any failure = instrument fault) | 3 |
| `known_impossible.json` | `known_impossible` | no tier may pass (any pass = leakage/gaming) | 3 |
| `known_diagnostic.json` | `known_diagnostic` | monotone with ability (stronger ≥ weaker) | 3 |
| `difficulty_anchor.json` | `difficulty_anchor` | consistent with declared `difficulty` (soft) | 3 |
| `test_retest.json` | `test_retest` | low per-item variance (measured elsewhere) | 2 |

Total: **14** starter items.

## Item schema (excerpt)

```jsonc
{
  "id": "trivial-arith-0001",          // unique across the source
  "category": "known_trivial",          // one of the 5 CalibrationCategory values
  "construct": "...",                   // capability/property probed (construct validity)
  "confound_controlled": "...",         // the confound this item controls for
  "prompt": "...",                      // what the model under characterization sees
  "gold": "4",                          // grading-side answer — NEVER shown to the model
  "expected_pass": {"weak": false, "strong": true},  // ability-tier -> expected pass
  "difficulty": 0.5,                    // optional IRT b-parameter
  "discrimination": 1.6,                // optional IRT a-parameter
  "metadata": {}                        // optional free-form notes
}
```

`gold` lives here because the loader runs **with the grader** (DECOMPOSE_BY_SECRETS).
Anything that feeds an item to a model must send only `prompt`.
