# Swarm Agent 12 — Pre-Registration and Statistical Rigor

**Date:** 2026-05-27
**Source:** Third study swarm dispatch (research-grounded advisor protocol)
**Question:** What's the current state of pre-registration and statistical methodology rigor in LLM evaluation? Pre-registration platforms, multiple-comparison corrections, effect-size reporting, sample size justification, adversarial collaboration.

---

# Statistical methodology rigor in LLM evaluation — research findings for ai-crucible

**1. Bowyer, Aitchison & Ivanova (2025) — "Position: Don't Use the CLT in LLM Evals With Fewer Than a Few Hundred Datapoints"** (ICML 2025 Spotlight Position Paper; arXiv:2503.01747).
CLT-based error bars dramatically underestimate uncertainty in LLM evals with fewer than a few hundred datapoints, and the authors recommend exact frequentist (Clopper-Pearson) and Bayesian beta-binomial intervals instead, with a reference implementation at github.com/sambowyer/bayes_evals.
*Implication for ai-crucible:* with K=10-20 puzzles per axis the CLT is inadmissible — ai-crucible's published intervals must be Clopper-Pearson or beta-binomial Bayesian, never normal-approximation, and the bayes_evals library is a citable off-the-shelf dependency.

**2. Miller (2024) — "Adding Error Bars to Evals: A Statistical Approach to Language Model Evaluations"** (arXiv:2411.00640; Anthropic).
Clustered standard errors on benchmark items can be over 3× larger than naive SEs, and Miller derives variance formulas, paired-difference tests for model A vs. B, and sample-size planning targets per benchmark.
*Implication for ai-crucible:* every cross-model delta must use a paired test (same puzzle seed across both models), and clustering by puzzle family is required since axis scores within a family are correlated — naive SEs will fabricate significance.

**3. Simmons, Nelson & Simonsohn (2011) — "False-Positive Psychology"** (Psychological Science 22(11), 1359-1366; doi:10.1177/0956797611417632).
Undisclosed flexibility in stopping rules, covariate inclusion, and outlier exclusion inflates the false-positive rate from a nominal 5% to ~60%, and the authors prescribe six disclosure requirements (every measure collected, every condition run, sample-size rule fixed in advance, etc.).
*Implication for ai-crucible:* the published methodology must declare, before the K-puzzle run, which axes count, which puzzle families count, what counts as a "pass," and the exact stopping rule — otherwise selective reporting across the multi-criterion surface invalidates any p-value.

**4. Gelman & Loken (2013/2014) — "The Garden of Forking Paths"** (Department of Statistics, Columbia; informal report later published as "The Statistical Crisis in Science," American Scientist 102(6):460).
Even with a pre-specified hypothesis, researcher degrees of freedom in coding choices yield uncorrected multiplicity because each unrealized analytic branch was a path that *could* have been taken if data had looked different.
*Implication for ai-crucible:* the multi-axis scoring rubric *is* a forking-paths surface — every threshold and weight chosen after looking at pilot data is an implicit comparison; the only defense is locking the scoring formula in a pre-registration before the production run.

**5. Benjamini & Hochberg (1995) — "Controlling the False Discovery Rate"** (JRSS-B 57(1):289-300) and Westfall & Young (1993) — "Resampling-Based Multiple Testing" (Wiley; ISBN 0-471-55761-7).
BH-FDR controls expected false-discovery proportion at α and is the standard when tests are independent or positively dependent; Westfall-Young permutation is asymptotically optimal under block-dependence because it estimates the joint null empirically rather than assuming independence.
*Implication for ai-crucible:* when comparing N models across K puzzles × A axes, the (N choose 2) × A pairwise p-values must be BH-corrected at minimum; because axes are correlated within a puzzle, Westfall-Young permutation (resampling puzzle-level scores) is the correct procedure and gives uniformly more power than Bonferroni.

**6. Dror, Baumer, Shlomov & Reichart (2018) — "The Hitchhiker's Guide to Testing Statistical Significance in NLP"** (ACL 2018, P18-1128).
A survey of ACL/TACL 2017 found statistical testing is "often ignored or misused" and the authors prescribe McNemar's test for paired binary outcomes, bootstrap or permutation for non-paired, and explicit family-wise correction across reported metrics.
*Implication for ai-crucible:* model-vs-model on the same puzzle set is a paired binary problem — McNemar's exact test is the canonical primary test, and ai-crucible should report it alongside the Bayesian intervals rather than only point accuracies.

**7. Kapoor et al. (2024) — "REFORMS: Consensus-based Recommendations for Machine-learning-based Science"** (Science Advances 10(18):eadk3452; arXiv:2308.07832).
A 19-author consensus of 32 items across study design, data, modeling, and reporting that quantifies leakage as affecting "hundreds of papers across 17 fields" and supplies a checklist journals can enforce.
*Implication for ai-crucible:* publish a filled REFORMS checklist alongside results — it's the most-cited consensus standard, costs an hour, and pre-empts the "where's your reporting standard?" objection from reviewers in adjacent fields.

**8. Chambers & Tzavella (2022) — "The past, present and future of Registered Reports"** (Nature Human Behaviour 6:29-42; doi:10.1038/s41562-021-01193-7) plus AsPredicted (https://aspredicted.org) and OSF Registries (https://osf.io/registries).
Registered Reports give Stage-1 in-principle acceptance based on methods alone before data collection, eliminating publication bias on the results; AsPredicted's 9-question short form is the lightweight alternative (no IRB needed for benchmark research).
*Implication for ai-crucible:* file an AsPredicted preregistration (timestamped, citable URL) before the production K-puzzle run that locks the rubric, axes, model list, K, primary test (McNemar), and correction procedure (BH-FDR + Westfall-Young permutation) — this is the single highest-leverage methodological move and costs 30 minutes.

---

## Sources

- [Bowyer et al. 2025 — Position: Don't Use the CLT in LLM Evals (arXiv:2503.01747)](https://arxiv.org/abs/2503.01747)
- [bayes_evals reference implementation (GitHub)](https://github.com/sambowyer/bayes_evals)
- [Miller 2024 — Adding Error Bars to Evals (arXiv:2411.00640)](https://arxiv.org/abs/2411.00640)
- [Simmons, Nelson & Simonsohn 2011 — False-Positive Psychology](https://journals.sagepub.com/doi/abs/10.1177/0956797611417632)
- [Gelman & Loken — The Garden of Forking Paths](https://sites.stat.columbia.edu/gelman/research/unpublished/p_hacking.pdf)
- [Gelman & Loken 2014 — The Statistical Crisis in Science (American Scientist)](https://www.americanscientist.org/article/the-statistical-crisis-in-science)
- [Benjamini-Hochberg FDR overview](https://stats.libretexts.org/Bookshelves/Applied_Statistics/Biological_Statistics_(McDonald)/06%3A_Multiple_Tests/6.01%3A_Multiple_Comparisons)
- [Westfall-Young permutation procedure (arXiv:1106.2068)](https://arxiv.org/abs/1106.2068)
- [Dror et al. 2018 — Hitchhiker's Guide to Statistical Significance in NLP (ACL P18-1128)](https://aclanthology.org/P18-1128/)
- [Kapoor et al. 2024 — REFORMS (arXiv:2308.07832 / Science Advances)](https://arxiv.org/abs/2308.07832)
- [Chambers & Tzavella 2022 — Registered Reports (Nature Human Behaviour)](https://www.nature.com/articles/s41562-021-01193-7)
- [AsPredicted preregistration platform](https://aspredicted.org/)
- [OSF Registries](https://osf.io/registries)
- [Pineau et al. 2020 — Improving Reproducibility in Machine Learning Research (arXiv:2003.12206)](https://arxiv.org/abs/2003.12206)
