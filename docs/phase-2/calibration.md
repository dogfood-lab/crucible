# Phase-2 calibration research (study-swarm 7)

**Date:** 2026-06-01
**Source:** Seventh study-swarm — 4 grounding agents + 2 citation-verification agents (research-grounded advisor protocol).
**Synthesis (canon):** [`research-grounding.md` §12](../research-grounding.md). This file is the raw findings + the verification log.

**Trigger — the first characterization run self-diagnosed.** 6 local models × the 20-item set × k=3 produced: qwen3.6:27b / gemma4:31b / granite4.1:30b each **acc=1.00** (the set SATURATES — no discrimination at the top); the κ-z gate flagged those three as "supra-human → SCREEN" (z=+2.24 vs an assumed human-human κ=0.80) and **seated only devstral-small-2:24b** (κ=0.80, z=0). Known-groups passed (all nailed the 8 trivial anchors → instrument valid). alt-test ω + ECE could not run (single gold; no confidence). The panel ρ-correlation step errored (glue shape bug).

**Outcome (the corrected run, 2026-06-01).** The redesign was built and re-run on a 51-item pair set; under the one-sided gate the three κ≈1.0 models (qwen3.6:27b, gemma4:31b, granite4.1:30b) now **SEAT** (Tier-1B, review-flagged) and the old sole-seat devstral now **rejects** — the set discriminates, ECE is measured via logprob, and ρ/known-groups/IRT-prune/perturbation all produce real numbers. Full receipt + the three integration bugs the live run caught: [`research-grounding.md` §12.1](../research-grounding.md). (The earlier "known-groups passed" above was *vacuous* — records carried a prompt-hash id, not the authored id; fixed.)

---

## Q1 — Discriminating items (the set saturates)

- **Fluid Benchmarking** (Hofmann et al. 2025, arXiv:2509.11106) — IRT + Fisher-information item selection: ~50× fewer items, cuts mislabeled-item impact. → fit difficulty/discrimination, keep high-information items.
- **PSN-IRT / "Lost in Benchmarks?"** (Zhou et al. 2025, arXiv:2505.15055) — discrimination is lowest at difficulty extremes; a balanced difficulty spread maximizes discriminability. → target a spread, not a pile of traps.
- **JudgeBench** (Sijun Tan et al. 2024, arXiv:2410.12784) — judge-discrimination comes from plausible-vs-subtly-wrong PAIRS with verifiable ground truth; top judges only ~64%. → author items as pairs with a subtle, verifiable flaw.
- **ATLAS** (Peiyu Li et al. 2025, arXiv:2511.04689) — drop items with >95% accuracy / <1% variance / point-biserial r_pb<0.1; characterize in 30–100 items. → adopt these prune filters verbatim.
- **IRT sample-size** (Schroeders & Gnambs 2025, AMPPS, doi:10.1177/25152459251314798) — stable 2PL needs ~200–500 respondents; <100 only with Bayesian priors. → with ~6 models, MLE 2PL is infeasible; use the model-free screen + Bayesian-prior IRT.
- **py-irt** (Lalor, Wu & Yu 2019 EMNLP; github nd-ball/py-irt) — Pyro/PyTorch variational IRT (1PL/2PL/4PL) with posterior uncertainty. → the small-N tooling.

**Recommended set:** plausible-vs-subtly-wrong pairs; difficulty centered ~0.5–0.65 with tails; 60–80 pilot items → prune ~40% by variance/point-biserial → ~30–50 survivors; re-pilot when a new model saturates it.

## Q2 — Agreement baseline + the "too-perfect" gate (THE design fix)

- **Judge's Verdict** (Steve Han et al. 2025, arXiv:2510.09738) — **VERIFIED:** Tier 1 splits into **1A Human-Like (|z|<1)** and **1B Super-Consistent (z>1)** — BOTH valid, top-tier; super-consistent judges are NEVER screened out. Baseline κ=0.801 from 3 annotators × 1,994 items; z=(κ−μ_human)/σ_human (tiny σ on easy items inflates z). → crucible's "z>1 → screen" is an INVERSION; make it a one-sided floor.
- The four super-consistent models (Mixtral-8x22B κ=0.813 z=1.45; Llama-3-70B; Gemma-3-27B; Bagel-34B) are the **highest-κ** judges. → high agreement is good, not suspicious-by-default.
- **IAA is not the ceiling** (Richie, Grover & Tsui 2022, ACL 2022.bionlp-1.26 — *not* "Boguslav & Cohen") — a well-specified model can exceed inter-annotator agreement. → "beating humans = suspicious" is false as a general rule.
- **Trust or Escalate** (Jung, Brahman & Choi 2024, arXiv:2407.18370) — the defensible gate is a ONE-SIDED floor (guarantee ≥X% human agreement; escalate low-confidence), no upper penalty.
- **Counting on Consensus** (2026, arXiv:2603.06865) — IAA varies widely by task; z is unstable under ceiling effects (few annotators → noisy σ). → estimate the baseline per task; don't hardcode 0.80.

**Recommendation:** ONE-SIDED floor (seat if κ ≥ human-level − margin). Compute μ_human/σ_human from real data. Replace the upper "screen" with a difficulty-conditioned review trigger (suspicious only if κ≈1.0 co-occurs with high human disagreement on the same items). → the three κ=1.0 models SEAT.

## Q3 — Confidence (ECE) + multi-annotator reference (alt-test)

- **Xiong et al. 2024** (arXiv:2306.13063) — verbalized confidence is systematically overconfident; consistency/sampling-based is better calibrated. → don't trust a single verbalized number.
- **Overconfidence in LLM-as-a-Judge** (Tian et al. 2025, arXiv:2508.06225) — panel-vote-fraction confidence cuts ECE substantially. → confidence = panel vote fraction.
- **Conformal judge intervals** (Sheng & Liu et al. 2025, arXiv:2509.18658) — distribution-free coverage from a small calibration set.
- **Temperature scaling** (arXiv:2410.06707) — one-parameter post-hoc fit lowers ECE.
- **alt-test** (Calderon, Reichart & Dror 2025, arXiv:2501.10970) — **VERIFIED from the authors' repo:** ≥3 HUMAN annotators per item, ≥30 instances (50–100 recommended), ε=0.2 expert / 0.15 skilled / 0.1 crowd; leave-one-annotator-out is over HUMANS → a model jury cannot be the reference (circular).
- **Ollama logprobs** — **VERIFIED:** v0.12.11 (Nov 2025) returns `logprobs`/`top_logprobs` on both native + OpenAI-compatible endpoints; installed 0.24.0 has it.
- Multi-LLM consensus + human review (arXiv:2503.17620) + MACE aggregation (arXiv:2508.07827) — cheap gold bootstrap; humans adjudicate jury-disagreements only.

**Recommendation:** ECE via verdict-token logprob and/or panel-vote fraction + temperature scaling (NOT verbalized). alt-test: ≥3 human labels on ≥50 items (jury-bootstrap → humans adjudicate disagreements); human reference mandatory.

## Q4 — Threshold calibration / instrument validity

- **Empirical thresholds** (Sarmah 2024, arXiv:2412.12148) — derive cutoffs from labeled data (Z-score/KDE/conformal); conformal gives guaranteed coverage. → don't pick 0.6 by fiat.
- **Difficulty-normalize** (ATLAS, above) — IRT θ adjusts for item difficulty; raw accuracy is distorted on easy-only sets (crucible's exact failure). → score θ, not raw pass-rate.
- **Selective classification** (Traub 2024, arXiv:2407.01032) — single-fixed-threshold eval is inadequate (AURC can violate monotonicity); score across the curve (AUGRC). → rank judges by a continuous score, not one cut.
- **Setup sensitivity** (Eiras 2025, arXiv:2503.04474) — style-only changes shift a judge's FNR up to 0.24. → mandatory perturbation test.
- **Alzahrani 2024** (already §8.3) — single-threshold perturbation flips rankings 63%. → apply the perturbation lens to the admission gate.

**Recommendation:** retire the 7-threshold binary gate → a difficulty-normalized, calibrated, continuous judge-quality score with a **selective (CI-based) seat/screen/reject** rule + a ship-time perturbation audit (jitter ±1 SE, report decision-flip rate; block if flips exceed a small bound — Andon).

---

## Verification log (second pass)

Both 2026-future-IDs and all others resolve. The design-critical reversal is CONFIRMED; minor citation-hygiene fixes:

| Item | Verdict |
|---|---|
| Han 2025 (2510.09738) "z>1 judges are kept Tier-1B, top-ranked" | **SUPPORTED** (decisive — quoted from source; crucible's two-sided gate is an inversion) |
| Super-consistent models rank 1–3 (Mixtral/Llama-3-70B/Gemma) | SUPPORTED |
| alt-test ≥3 human annotators / ≥30 instances / ε / human-reference-mandatory (2501.10970) | **SUPPORTED** (from the authors' repo — the strongest-verified item) |
| Ollama logprobs since v0.12.11 | **SUPPORTED** (both endpoints; installed 0.24.0 has it) |
| Fluid (2509.11106), PSN-IRT (2505.15055), ATLAS (2511.04689), Xiong (2306.13063), Sarmah (2412.12148), Traub (2407.01032), Eiras (2503.04474, FNR Δ0.24) | SUPPORTED |
| "Boguslav & Cohen 2017" (IAA-not-ceiling) | **WRONG ATTRIBUTION** → actual: Richie, Grover & Tsui 2022 (ACL 2022.bionlp-1.26). Claim holds; fix the name. |
| py-irt "Lalor & Rodriguez INFORMS 2023" | **WRONG CITE** → cite Lalor, Wu & Yu 2019 (EMNLP) for the library. |
| IRT sample-size "200–500" (Schroeders & Gnambs 2025) | PARTIAL — DOI/authors/topic confirmed; exact 200–500 figure needs a page-cite (directionally right: small-N → Bayesian priors). |
| Traub / Counting-on-Consensus titles | minor paraphrase; fixed in §12. |

**Lesson reinforced:** the verification pass caught a *shipped* gate that inverts its own source — exactly the EXTERNAL_VERIFIER value. Reverse the gate to one-sided before re-running.
