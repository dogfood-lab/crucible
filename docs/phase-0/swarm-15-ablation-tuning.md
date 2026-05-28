# Swarm Agent 15 — Ablation Methodology and Parameter Tuning

**Date:** 2026-05-27
**Source:** Third study swarm dispatch (research-grounded advisor protocol)
**Question:** How to tune the parameters of an AI evaluation instrument without contaminating the diagnostic? Calibration/validation/test separation, ablation methodology, sensitivity analysis, tuning provenance.

---

# Tuning crucible without contaminating the diagnostic — research grounding

**Core problem framing:** crucible is an evaluation **instrument**, not a model. Its parameters (penalty weights, point thresholds, time budgets, panel composition, judge prompts) are hyperparameters of a *measurement device*. The literature on tuning measurement devices without compromising their measurements is small but specific, and converges on one structural answer: **multi-split separation + tuning-budget accounting + frozen-rubric publishing**.

---

**1. Three-set partition, with a fourth for "calibration of the calibration." (Dwork, Feldman, Hardt, Pitassi, Reingold, Roth 2015 — "The reusable holdout: Preserving validity in adaptive data analysis," Science 349(6248):636-638; arXiv:1506.02629)**
Reusing a single holdout adaptively across many parameter decisions overfits the holdout itself — validity decays roughly with the number of queries. Their **Thresholdout** algorithm uses differential privacy (Laplace noise on validation queries) to bound how much the analyst can learn about the holdout, letting it be reused for ~O(holdout_size²) adaptive queries instead of ~O(log holdout_size).
**Crucible implication:** split puzzles into (a) **calibration** set — tune freely; (b) **dev** set — Thresholdout-style noisy queries with an explicit query budget; (c) **validation** set — touched once per locked candidate config; (d) **private test** set — touched only at locked release. Track queries against the dev set and stop tuning when budget exhausted.

**2. Nested CV is the textbook fix when you cannot afford four physical splits. (Cawley & Talbot 2010 "On Over-fitting in Model Selection and Subsequent Selection Bias," JMLR 11:2079-2107; restated in modern AI-eval form by Vabalas et al. 2019 PLOS ONE)**
Inner loop selects hyperparameters; outer loop estimates generalization of the *full procedure including selection*. The reported number is "the performance of the tuning protocol," not "the performance of one tuned config."
**Crucible implication:** if puzzle inventory is small, run nested CV over puzzle-folds, and publish "crucible v1.0 = the protocol (tuner + frozen weights), not the weights alone."

**3. Variance-based sensitivity analysis tells you which weights actually matter. (Saltelli, Annoni, Azzini, Campolongo, Ratto, Tarantola 2010 — "Variance based sensitivity analysis of model output: Design and estimator for the total sensitivity index," Computer Physics Communications 181(2):259-270)**
Compute Sobol first-order indices S_i (how much output variance comes from parameter i alone) and total-effect indices T_i (parameter i + all its interactions). Parameters with T_i ≈ 0 can be frozen at any reasonable value; parameters with S_i ≫ 0 are load-bearing and deserve explicit calibration. SciPy ships this as `scipy.stats.sobol_indices(method='saltelli_2010')`.
**Crucible implication:** before tuning, run Sobol on the calibration set with each weight as an input and final puzzle-score variance as output. Tune only the top-T_i parameters; freeze the rest as constants with a comment in the rubric.

**4. Adversarial multi-round benchmarks separate "data we used to fool the model" from "data we test on." (Nie, Williams, Dinan, Bansal, Weston, Kiela 2020 — "Adversarial NLI: A New Benchmark for Natural Language Understanding," ACL 2020; Kiela et al. 2021 — "Dynabench: Rethinking Benchmarking in NLP," NAACL 2021, arXiv:2104.14337)**
ANLI's three rounds each have **train/dev/test splits**, and rounds 2 and 3 are collected adversarially **against models trained on the previous round's train+dev**. Test is never used for adversarial collection. Dynabench formalizes this as "human-and-model-in-the-loop" where the loop touches train/dev but never test.
**Crucible implication:** every time you iterate the rubric to "make this puzzle land right," you are doing an adversarial collection round — those iterations must touch only calibration/dev, and the test set must be sealed before each locked release.

**5. The locked-rubric pattern: version, immutable-bundle, and execute deterministically. (Hong, Yao, Shen, Xu, Wei, Dong 2026 — "RULERS: Locked Rubrics and Evidence-Anchored Scoring for Robust LLM Evaluation," arXiv:2601.08654)**
RULERS compiles natural-language rubrics into **versioned immutable bundles** with structured decoding and deterministic evidence verification, then applies post-hoc Wasserstein calibration. The locking step is what gives auditability — the bundle hash is the rubric.
**Crucible implication:** crucible v1.0.0 should ship a **rubric bundle** (penalty weights + thresholds + judge prompts) addressed by content hash. Tuning produces a new bundle hash. The leaderboard records `(score, bundle_hash)`. No silent retuning.

**6. Judge prompt sensitivity is itself a hyperparameter and must be ablated. (Bellibatlu, Raff, Zhang 2026 — "JudgeSense: A Benchmark for Prompt Sensitivity in LLM-as-a-Judge Systems," arXiv:2604.23478)**
Semantically equivalent prompt paraphrases produce measurably unstable judge scores, with coherence judgments most sensitive and pairwise comparisons exhibiting position bias. Model scale does NOT reliably fix this.
**Crucible implication:** for every judge prompt in the panel, generate 5-10 paraphrases on the calibration set and report variance. If a finding's sign flips under paraphrase, it is below crucible's resolution and should not be reported. Lock the exact prompt string in the rubric bundle (point 5).

**7. Tuning provenance must be disclosed at the granularity of each parameter. (Pineau et al. 2020 — "Improving Reproducibility in Machine Learning Research (A Report from the NeurIPS 2019 Reproducibility Program)," arXiv:2003.12206; Gebru, Morgenstern, Vecchione, Vaughan, Wallach, Daumé III, Crawford 2018/2021 — "Datasheets for Datasets," CACM 64(12):86-92, arXiv:1803.09010)**
The NeurIPS checklist (mandatory since 2019) requires: (a) range of hyperparameters considered, (b) method used to select among them, (c) the final values, (d) the statistic used to report results. Datasheets for Datasets formalizes documenting the *provenance* of every artifact in 57 questions across 7 categories.
**Crucible implication:** publish a `TUNING.md` next to the rubric bundle listing, per weight: `range_searched, search_method (grid/Bayes/manual), calibration_set_id, N_puzzles, dev_queries_used_of_budget, final_value, sensitivity_T_i`. Without this, anyone tuning against crucible has no way to detect that you tuned crucible against them.

**8. When parameter dim is high, use Bayesian optimization with a fixed evaluation budget — not unbounded grid sweeps. (Snoek, Larochelle, Adams 2012 — "Practical Bayesian Optimization of Machine Learning Algorithms," NeurIPS 2012)**
BO with a **fixed budget** of dev-set evaluations is the disciplined alternative to "I tweaked it until it looked right." It produces a reproducible search trace and naturally aligns with the Thresholdout query budget from finding 1.
**Crucible implication:** if you have >3 weights to tune jointly, run BO with `n_evaluations ≤ Thresholdout_budget` on the dev set, log the GP posterior, and publish the trace alongside the rubric bundle.

---

## Concrete protocol crucible should adopt before locking weights (v1):

1. **Split puzzle inventory 60/20/10/10** into `calibration / dev / validation / private_test`. Hash each manifest.
2. **Sobol screen** all candidate weights on `calibration`; freeze any with T_i < threshold and document.
3. **BO-search the top-T_i weights** on `dev` with a fixed query budget; log the trace.
4. **Ablate the judge prompts** with 5-10 paraphrases each; freeze the most stable phrasing.
5. **Validate the locked bundle once** on `validation`. If it fails, you must restart from step 2 with a fresh dev split — you cannot iterate on validation.
6. **Seal `private_test`**; touch only at release.
7. **Publish** `crucible-v1.0.0/rubric.bundle` (content-hashed), `TUNING.md` with per-weight provenance, the Sobol report, the BO trace, and a datasheet for each split. Score on the leaderboard is `(score, bundle_hash)`.

The rule that ties it all together: **a tuned crucible reports the protocol, not the weights — and the validation set is touched exactly once per bundle hash.**

## Sources

- [Dwork et al. 2015 — Generalization in Adaptive Data Analysis and Holdout Reuse (arXiv:1506.02629)](https://arxiv.org/abs/1506.02629)
- [Dwork et al. 2015 — The reusable holdout (Science)](https://www.science.org/doi/10.1126/science.aaa9375)
- [Saltelli et al. 2010 — Variance based sensitivity analysis (Comp. Phys. Comm.)](https://www.andreasaltelli.eu/file/repository/PUBLISHED_PAPER.pdf)
- [SciPy `sobol_indices` reference (Saltelli 2010 estimator)](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.sobol_indices.html)
- [Nie et al. 2020 — Adversarial NLI (ACL Anthology)](https://aclanthology.org/2020.acl-main.441/)
- [Kiela et al. 2021 — Dynabench: Rethinking Benchmarking in NLP (arXiv:2104.14337)](https://arxiv.org/abs/2104.14337)
- [Hong et al. 2026 — RULERS: Locked Rubrics and Evidence-Anchored Scoring (arXiv:2601.08654)](https://arxiv.org/pdf/2601.08654)
- [Bellibatlu, Raff, Zhang 2026 — JudgeSense (arXiv:2604.23478)](https://arxiv.org/abs/2604.23478)
- [Pineau et al. 2020 — Improving Reproducibility in ML Research (arXiv:2003.12206)](https://arxiv.org/pdf/2003.12206)
- [Gebru et al. 2018/2021 — Datasheets for Datasets (arXiv:1803.09010)](https://arxiv.org/abs/1803.09010)
- [Cawley & Talbot 2010 — Over-fitting in Model Selection (restated, nested-CV survey)](https://arxiv.org/pdf/1809.09446)
- [Snoek et al. 2012 — Practical Bayesian Optimization of Machine Learning Algorithms (NeurIPS 2012)](https://papers.nips.cc/paper/2012/hash/05311655a15b75fab86956663e1819cd-Abstract.html)
