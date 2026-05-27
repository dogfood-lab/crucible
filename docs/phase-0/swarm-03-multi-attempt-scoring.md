# Swarm Agent 03 — Multi-Attempt Scoring Methodology

**Date:** 2026-05-27
**Source:** Study swarm dispatch (research-grounded advisor protocol)
**Question:** What's the state-of-the-art on scoring stochastic models with multiple attempts? Specifically: pass@k methodology, attempts needed to distinguish "occasionally fails" from "consistently fails," confidence intervals, saturation declaration.

---

# Research Grounding: Scoring Stochastic Models with Multiple Attempts

Six findings, all with canonical identifiers, ordered by relevance to the Lab→Arena graduation criteria.

---

**1. Chen et al. (2021), "Evaluating Large Language Models Trained on Code" (arXiv:2107.03374).**
URL: https://arxiv.org/abs/2107.03374
Introduces the unbiased pass@k estimator `pass@k = 1 − C(n−c, k)/C(n, k)` with n ≥ k samples per problem; the naive estimator `1 − (1−p̂)^k` systematically underestimates because it treats sampling as with-replacement. Their experimental protocol uses **n = 200, k ≤ 100**, with **temperature 0.2 for pass@1** and **temperature 0.8 for pass@100**.
*Implication:* Lab→Arena should compute pass@k via the unbiased estimator with n ≥ 2k attempts; use T=0.2 if the puzzle measures best-shot competence, T=0.8 if it measures coverage across k attempts. Mixing temperatures across modes confounds the metric.

**2. Miller (2024), "Adding Error Bars to Evals: A Statistical Approach to Language Model Evaluations" (arXiv:2411.00640, Anthropic).**
URL: https://arxiv.org/abs/2411.00640
Worked power calculation: to detect a 3% absolute accuracy gap at α=0.05, β=0.20 (80% power) with uniformly-distributed difficulty and paired analysis, **n ≈ 969 questions** are required; with n=198 questions, the Minimum Detectable Effect drops from 13.2% to 7.5% by increasing K (resamples per question) from 1 to 10. Miller also explicitly warns: **"Don't touch the thermostat"** — lowering temperature to reduce variance injects bias and may *increase* the variance of the conditional means.
*Implication:* For Arena graduation, hold temperature fixed at whatever the diagnostic targets, use paired analysis across models on the same puzzle bank, and budget K ≥ 5 resamples per puzzle to reach roughly 7-8% MDE on banks of ~200; insist on ~1,000 puzzles to detect 3% deltas.

**3. Bowyer, Aitchison & Ivanova (2025), "Position: Don't Use the CLT in LLM Evals With Fewer Than a Few Hundred Datapoints" (arXiv:2503.01747, ICML 2025 Spotlight).**
URL: https://arxiv.org/abs/2503.01747
With fewer than "a few hundred" items, CLT-based intervals (Wald / SE × 1.96) **systematically underestimate uncertainty**; recommend Wilson, Clopper-Pearson, bootstrap, or Bayesian beta-binomial intervals instead. Direct disagreement with Miller (2024) on small-n regime: Miller treats CLT as adequate, Bowyer et al. show it fails below ~300.
*Implication:* For Lab-mode puzzles attempted N ≤ 50 times, compute Wilson score intervals (stable from n≈10), not normal approximations. The disagreement matters: a graduation rule using `mean ± 1.96·SE` will pass spuriously-fair puzzles in the Lab; switching to Wilson is conservative and correct.

**4. Chiang et al. (2024), "Chatbot Arena: An Open Platform for Evaluating LLMs by Human Preference" (arXiv:2403.04132).**
URL: https://arxiv.org/abs/2403.04132
Methodology paper formalizes Bradley-Terry maximum-likelihood ranking with **95% bootstrap CIs computed via 1000 resamples** of observed votes (2.5%/97.5% percentile); a simulation study shows bootstrap and sandwich-estimator CIs are nearly identical. Operational thresholds reported for stable rankings: ~5,000 pairwise votes for text models, ~3,000 for code, ~2,500 for vision; below these, models are tagged "Preliminary" with CIs of ±10–15 Elo vs ±4–7 for established. A 100-point Elo gap corresponds to ~64% win rate.
*Implication:* If Arena ranks models against each other (not just against a fixed puzzle bank), require ≥ ~3,000 puzzle-attempt outcomes per model before that model's rating is binding, with 1000-bootstrap 95% CIs. Don't declare ranking changes when CIs overlap.

**5. Aggarwal, Madaan et al. (2023), "Let's Sample Step by Step: Adaptive-Consistency for Efficient Reasoning" (arXiv:2305.11860).**
URL: https://arxiv.org/abs/2305.11860
Empirical saturation curves for self-consistency sampling: most accuracy gains arrive by **K ≈ 10–20 samples per question** across reasoning benchmarks, with diminishing returns thereafter; adaptive stopping reduces samples by up to 7.9× with <0.1% accuracy drop.
*Implication:* For per-puzzle "consistency" measurement (does the model solve it reliably?), **K = 10 attempts** is a defensible lower bound and **K = 20** approaches saturation. Below K=5, "occasionally fails" is statistically indistinguishable from "consistently fails."

**6. Kiela et al. and Tedeschi et al. — benchmark saturation criteria** (representative: "What's the Meta-Evaluation?", arXiv:2304.00936; and "Benchmark Health Index", arXiv:2602.11674 in 2026 references).
URL: https://arxiv.org/abs/2602.11674
Operational definition of saturation: a benchmark is **saturated when top models' 95% CIs overlap and aggregate accuracy approaches the empirical ceiling** (MMLU at 88–94% is the canonical case). The Benchmark Health Index proposes three axes: Capability Discrimination (how sharply does the benchmark separate models), Anti-Saturation (headroom before ceiling), and Impact. Variance collapses to zero as accuracy → 1.0, eliminating discriminative power.
*Implication:* For Arena graduation, declare a puzzle "saturated" (and demote it from the diagnostic bank) when the top-quartile model achieves **pass@k ≥ 0.95 with Wilson lower-bound > 0.90**, *or* when the pass@k 95% CIs of the top 3 models overlap. Floor symmetrically: "trivial" if bottom-quartile model already passes ≥ 0.95.

---

## Surfaced Disagreement

- **Miller (2024) vs Bowyer et al. (2025) on CLT validity.** Miller treats CLT-based SE as adequate for typical LLM evals and dismisses bootstrap as "unnecessary"; Bowyer et al. (ICML 2025 Spotlight) show CLT dramatically underestimates uncertainty below ~300 items. For Lab mode where puzzles may have N ≈ 20–50 attempts, follow Bowyer (use Wilson). For Arena with N ≥ 500 puzzles, Miller's CLT framework is fine.
- **Temperature for evaluation.** Chen et al. (2021) actively tune temperature per metric (T=0.2 for pass@1, T=0.8 for pass@100); Miller (2024) explicitly forbids tuning temperature for variance reduction. These are reconcilable: tune temperature *to the metric* (Chen), do not tune *during* the metric (Miller).
- **K (samples per question).** Aggarwal/Madaan see saturation at K=10–20; Miller's example uses K=1 to 10 with MDE shrinking smoothly; Chen et al. use n=200 for k=100. Take K=10 as the consensus floor for "consistency," K=20 as the saturation point, n≥2k for the pass@k unbiased estimator.

## Concrete Recommendations for Graduation Criteria

- **Lab mode (per-puzzle diagnostic):** N = 20 attempts at fixed temperature (the diagnostic temperature, e.g., T=0.7); compute Wilson 95% CI on pass rate; graduate to Arena only if **0.10 ≤ Wilson-lower-bound and Wilson-upper-bound ≤ 0.90** (rules out trivial and impossible).
- **Arena mode (cross-model ranking):** ≥ 200 puzzles, K=5 attempts each, paired analysis across models (Miller §4.2), 1000-bootstrap 95% CIs (Chiang et al.), declare ranking change only when CIs disjoint. Detects ~5–8% absolute pass-rate deltas reliably.
- **Saturation retirement:** retire a puzzle when top model's pass@k Wilson-lower-bound > 0.90 OR when top-3 models' CIs all overlap; this is the empirical operationalization of Kiela/Tedeschi.
