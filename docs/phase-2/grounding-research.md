# Phase-2 grounding research (study-swarm 6)

**Date:** 2026-06-01
**Source:** Sixth study-swarm dispatch — 4 grounding agents + 2 citation-verification agents (research-grounded advisor protocol).
**Synthesis (canon):** the actionable, corrected design is [`research-grounding.md` §11](../research-grounding.md). This file is the raw findings + the verification log.

Phase 2 = **local model characterization → data-driven role assignment** (Designer stays Claude; local cross-family models fill Judge/Critic/CohortSolver via Ollama on the RTX 5090). The four load-bearing questions, the verified findings, and the corrections below.

---

## Q1 — Characterizing an LLM as a judge for panel assignment

- **JudgeBench** — *Sijun Tan et al. 2024, arXiv:2410.12784* — objectively-labeled response pairs; many strong models score barely above 50%. → hard correctness gate; require ≥60%.
- **Judge's Verdict** — *Steve Han et al. 2025, arXiv:2510.09738* — two-gate admission: Pearson r≥0.80, then Cohen's κ z-score vs the human–human baseline; 27/54 models passed; size not decisive. → adopt as the seat rubric.
- **alt-test** — *Calderon, Reichart & Dror 2025 (ACL), arXiv:2501.10970* — replace humans only if winning-rate ω≥0.5 vs held-out annotators; needs a modest labeled subset. → seat/screen threshold.
- **Rating Roulette** — *Haldar & Hockenmaier 2025 (EMNLP Findings), arXiv:2510.27106* — LLM judges have low intra-rater reliability. → measure test-retest stability (3–5× reruns); reject non-reproducible judges.
- **Trust or Escalate** — *Jung, Brahman & Choi 2024, arXiv:2407.18370* — cascaded selective evaluation: >80% human agreement at ~80% coverage even with Mistral-7B. → all-open panel is trustworthy if it abstains + escalates the uncertain tail.
- **Jury-on-Demand** — *Xiaochuan Li et al. 2025, arXiv:2512.01786* — learned per-judge reliability → reliability-weighted aggregation beats unweighted consensus. → weight judges by measured reliability.
- **MiniCheck / LLM-AggreFact** — *Liyan Tang et al. 2024 (EMNLP), arXiv:2404.10774* — a small specialized checker is panel-grade for grounded factuality (paper tops at 74.7% with ≤770M; the "7B@77.4%" is the later Bespoke-MiniCheck on the same leaderboard). → use a small specialized checker for the factuality axis.
- *(Overconfidence in LLM judges — arXiv:2508.06225 — supports an ECE/overconfidence metric + down-weighting.)*

**Protocol:** the 6-metric admission test (objective accuracy / human-agreement two-gate / alt-test ω / consistency / calibration ECE / bias panel) over a ~150–250-item fixture set; reliability-weighted aggregation + escalation. (→ §11.1)

## Q2 — Quantization & local serving effects on judge reliability

- **"Give Me BF16 or Give Me Death?"** — *Kurtic / Neural Magic et al. 2024, arXiv:2411.02355* — **CORRECTED (see verification): the paper finds INT4 NEAR-LOSSLESS (>99% accuracy recovery), W4A16 ties BF16 on Arena-Hard.** The originally-claimed "25.9% judge collapse at 4-bit" does NOT exist in it. → do NOT assume a quant floor; measure it.
- **When Quantization Affects Confidence** — *Proskurina et al. 2024 (NAACL Findings), arXiv:2405.00632* — GPTQ-4bit shifts probabilities + worsens calibration, concentrated on already-uncertain examples. → 4-bit's real cost is calibration; measure ECE per quant.
- **Defeating Nondeterminism in LLM Inference** — *Thinking Machines Lab 2025* (already in §9.7) — temp-0 variance is from batch-invariance, not RNG. → sequential serving (`OLLAMA_NUM_PARALLEL=1`), fixed seed/ctx, warm-then-discard-first-call.
- **Ollama serving** (docs) — every loaded model + KV must fit VRAM or requests queue. → three 24–35B models can't co-reside in 32 GB; run load→judge→evict sequentially.

**Decision:** Phase 2 empirically measures judge reliability across quant levels on the calibration set (that's the characterization job). (→ §11.2)

## Q3 — Calibration-set / anchor-item design

- **ImpossibleBench** — *Zhong, Raghunathan & Carlini 2025, arXiv:2510.20270* — impossibility-by-construction: any pass implies a spec-violating shortcut. → known-impossible anchors as false-positive/leakage detectors.
- **tinyBenchmarks** — *Maia Polo et al. 2024 (ICML), arXiv:2402.14992* — IRT anchor points estimate full-benchmark score within ~2% from ~100 items. → tens of anchors validate the harness + profile models cheaply.
- **Adaptive Testing (ATLAS framework)** — *Peiyu Li et al. 2025, arXiv:2511.04689* — 3PL IRT + Fisher-information selection; 30–100 items; equal-accuracy models get different latent θ. → tag items with difficulty + discrimination.
- **Measuring what Matters: Construct Validity** — *Bean et al. 2025 (NeurIPS), arXiv:2511.04703* — **CORRECTED: of 445 benchmarks, ~6% define/justify the construct, <10% report statistical significance** (not "53%/16%"). → each item declares its construct + controlled confound.
- *(Attention-check tradition — too-hard checks false-flag good subjects; calibrate trivial items to catch harness faults, not capable models.)*

**Design:** 5 categories — known-trivial / known-impossible / known-diagnostic / difficulty-laddered IRT anchors / test-retest — with a pre-registered known-groups acceptance matrix. (→ §11.3)

## Q4 — Cross-family panel composition

- **CARE** — *Jitian Zhao et al. 2026, arXiv:2603.00039* — confounder-aware aggregation models shared latent confounders causing correlated judge errors; beats majority vote + plain reliability-weighting (error ↓ up to 26.8%). → confounder-aware/reliability-weighted aggregation.
- **CyclicJudge** — *Ziyi Zhu et al. 2026, arXiv:2603.01865* — round-robin rotation neutralizes position/length/idiosyncratic bias at single-judge cost. → rotate membership + answer-order.
- **Agreeableness bias** — *Jain et al. 2025, arXiv:2510.11822* — judges converge on consensus even when wrong; high agreement is a flag to investigate. → minority-veto on the bypass/safety axis; never reward raw consensus.
- **SE-Jury** — *Xin Zhou et al. 2025, arXiv:2505.20854* — dynamic team selection reaches inter-annotator-level agreement; calibrate against a small gold set.
- **Trust or Escalate** (Jung 2024, above) — all-open panel OK with selective abstention.

**Policy:** 5 judges (odd); compose for low *error*-correlation (reuse the ρ<0.25 submodularity gate); confounder-aware/reliability-weighted aggregation + minority-veto on bypass; rotation; gold-set anchoring + escalation. (→ §11.4)

---

## Verification log (second pass — the catches)

Two verification agents fetched every cited arXiv ID. **All IDs resolve (including every 2026 future-ID).** Defects found and corrected in §11:

| Severity | Citation | Defect | Resolution |
|---|---|---|---|
| **CRITICAL** | arXiv:2411.02355 (Kurtic/Neural Magic) | Claimed "4-bit collapses LLM-as-judge 25.9% / human-pref 10.5%". **Paper finds the OPPOSITE — INT4 near-lossless (>99% recovery), W4A16 ties BF16.** An in-loop "PDF confirmation" of the number was a model echoing the prompt. | Quant-floor decision dropped; Phase 2 measures quant effects empirically (§11.2). |
| **Misattribution** | arXiv:2602.16610 (Qian et al. 2026) | The "low inter-judge correlation beats headcount" thesis is NOT this paper (it's BT-σ, a per-judge reliability model). | Thesis re-anchored to CARE (2603.00039) + CyclicJudge (2603.01865), both verified; Qian cite dropped for this point. |
| **Fabricated numbers** | arXiv:2511.04703 (Bean) | "53% validity / 16% stats" fabricated. | Real: ~6% define the construct / <10% report stats (direction holds). |
| **Conflation** | arXiv:2404.10774 (MiniCheck) | "7B@77.4%" is a later Bespoke model, not this paper (≤770M, tops 74.7%). | Note corrected; the small-checker point stands. |
| Attribution | 2410.12784 / 2510.09738 | First authors are **Sijun Tan** / **Steve Han**. | Fixed. |
| Naming | 2511.04689 / 2510.20270 / 2505.20854 | "ATLAS"/"ImpossibleBench"/"SE-Jury" are framework names, not paper titles. | Noted. |

**Lesson reinforced:** the verification pass is load-bearing — it caught a design decision built on a *contradicted* number (the source said the opposite), which CoT/single-pass review would have propagated. This is the EXTERNAL_VERIFIER standard doing exactly its job.
