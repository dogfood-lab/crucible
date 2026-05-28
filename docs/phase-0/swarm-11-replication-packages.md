# Swarm Agent 11 — Replication Packages for LLM Evaluation

**Date:** 2026-05-27
**Source:** Third study swarm dispatch (research-grounded advisor protocol, instrument-quality pass)
**Question:** What constitutes "fully replicable" for an interactive LLM evaluation? Venue/audit institution requirements, replication-package artifacts, deterministic eval state-of-the-art, container versioning, principle-vs-practice gap.

---

# Research Grounding: Replicability Standards for Interactive LLM Evaluations

**Context for crucible:** an interactive adversarial game producing per-trial outcomes (elegance / novelty / answer-bypass), released to compare across model families. Replicability means a third party can run our published artifacts and reproduce the same trial outcomes, the same category distributions, and the same headline claims — modulo declared model-side stochasticity.

---

## 1. Pineau et al., 2021 — "Improving Reproducibility in Machine Learning Research" (JMLR v22, arXiv:2003.12206)

**Finding.** The canonical ML Reproducibility Checklist v2.0 (McGill) mandates four artifact classes for empirical results: (a) clear description of model/algorithm and assumptions, (b) for every reported empirical result — the exact range of hyperparameters searched, the method used to select the reported value, the number of training/eval runs, the test-set metric with central tendency *and* variation, a description of compute infrastructure, and (c) for any dataset — a link, description of the data split, and preprocessing code.

**Implication for crucible.** Our release MUST publish the full hyperparameter grid (temperature, max-tokens, system-prompt content), the seed list per trial, the number of independent runs per model, and per-category outcome distributions with confidence intervals — not just point estimates.

## 2. NeurIPS Datasets & Benchmarks Track checklist (current 2024-2026)

**Finding.** For benchmark submissions specifically, "supplementary materials must ensure that all results are easily reproducible" — meaning datasets, code, and evaluation procedures must be accessible and documented, with "exact commands and environment specifications needed for replication." Code is *not* mandatory in general, but IS effectively mandatory when the contribution is a benchmark or evaluation method.

**Implication for crucible.** Because crucible's contribution is the eval itself, the harness code, scoring rubrics, and judge prompts are not optional — they are the artifact. Treat the harness repo as the primary release deliverable, not a companion.

## 3. ACM Artifact Review and Badging v1.1

**Finding.** ACM's three-badge system distinguishes (a) Artifacts Available (publicly retrievable via DOI/permanent repo), (b) Artifacts Evaluated — Functional vs. Reusable (the Reusable tier requires documentation sufficient for repurposing, not just running once), and (c) Results Reproduced (an independent team obtained the same headline results using author artifacts) vs. Results Replicated (same results without using author artifacts). These are distinct claims an audit committee can verify independently.

**Implication for crucible.** Aim for "Reusable" not just "Functional" — meaning the harness must let an auditor swap in a *new* model family or *new* judge with documented extension points, not only rerun ours. This shapes the public API of the harness.

## 4. He et al., 2025 — "Understanding and Mitigating Numerical Sources of Nondeterminism in LLM Inference" (arXiv:2506.09501)

**Finding.** Floating-point non-associativity ((a+b)+c ≠ a+(b+c)) under BF16 plus varying GPU kernel reduction orders means greedy decoding (temperature=0) is *not* deterministic across batch sizes, tensor-parallel configs, or GPU architectures (A100 vs L40S). Their LayerCast method (BF16 storage, FP32 compute) recovers determinism at 34% memory overhead; for stochastic sampling they recommend reporting mean and error bars across multiple independent runs rather than claiming a single "the" output.

**Implication for crucible.** "Temperature=0, fixed seed" is not enough. Either (a) document the exact GPU + serving stack used (and accept that re-runs on different hardware will differ), or (b) sample with non-zero temperature, run N≥10 trials per (model, prompt) pair, and report distributions. Crucible should adopt (b) because (a) is not portable across third-party auditors.

## 5. He et al., 2025 — SGLang deterministic-inference engineering report (lmsys.org/blog/2025-09-22-sglang-deterministic/)

**Finding.** True deterministic LLM serving requires four engineered components: batch-invariant kernels (RMSNorm, matmul, attention), fixed-size attention splitting, aligned chunked prefill, and seeded multinomial sampling via Gumbel noise from a hash function. SGLang demonstrates perfect reproducibility on Qwen3-8B training. This is what "deterministic" actually costs to deliver — it is not a flag, it is a stack.

**Implication for crucible.** Do not promise determinism we cannot deliver. State explicitly in our methods section: "Closed-API models (Claude, GPT-X) are stochastic black boxes; we report distributions across N seeds. Open-weight models are run via [pinned-stack] for batch-invariant determinism, OR also reported as distributions." Pick one per model class and be honest about which.

## 6. Larsen, 2025 — "The Instability of Safety" (arXiv:2512.12066)

**Finding.** Across 4 instruction-tuned models and 20 sampling configurations, 18–28% of safety-relevant prompts show *decision flips* — the model refuses in one seed, complies in another, on identical input. Single-shot safety evaluation is therefore unreliable; aggregate distributions across seeds are required, and all hyperparameters must be documented for cross-study comparison.

**Implication for crucible.** Crucible's three-way category distinction (elegance / novelty / answer-bypass) is directly downstream of the same instability. We MUST run ≥10 seeds per (model, scenario) and report category proportions with binomial confidence intervals. A single trial reporting "model X bypassed" is statistically meaningless and would be cited against us.

## 7. MLCommons MLPerf Inference Rules

**Finding.** MLPerf requires submissions to specify the System Under Test (SUT) in full hardware + software detail, requires that the SUT remain unchanged from submission through publication for audit, mandates that any quantization be "purely mathematical, reproducible" and described "at a level where it could be reproduced," and runs a review committee that can audit and reject submissions. This is the strictest reproducibility regime in industrial ML evaluation and is the model adversarial auditors will compare us to.

**Implication for crucible.** Publish a frozen `SUT.yaml` per release: model ID + version string + provider API endpoint + system prompt SHA + harness commit SHA + container image digest. Pin model versions by exact API string (e.g. `claude-opus-4-7-20260415`), not family alias.

## 8. METR open-source release pattern — vivaria + eval-analysis-public + HCAST

**Finding.** METR's public replication package for the time-horizon paper includes: (a) the vivaria evaluation infrastructure repo, (b) a separate eval-analysis-public repo with raw per-trial data in YAML and the analysis notebooks that generated every plot, and (c) task definitions as a separate artifact (HCAST). The separation matters: raw data + analysis code lets a replicator verify the *statistical claims* without rerunning the (expensive, model-API-gated) trials themselves.

**Implication for crucible.** Ship two repos, not one: `crucible-harness` (runs trials, costs API budget to replicate) and `crucible-results` (raw per-trial JSON outputs + analysis notebooks that regenerate every figure and headline number from the paper). This lets auditors verify our category-distribution claims without paying for inference.

---

## Anti-requirements check

- All eight findings cite canonical IDs (arXiv numbers, JMLR DOI, ACM policy URL, MLCommons GitHub, METR blog URL).
- No findings are "best practices generally" — each is a concrete artifact requirement.
- The implication-to-citation ratio is 1:1; each citation maps to one architectural choice for the crucible release.

## Sources

- [Improving Reproducibility in Machine Learning Research (Pineau et al., JMLR 2021)](https://arxiv.org/abs/2003.12206)
- [Machine Learning Reproducibility Checklist v2.0 (Pineau, McGill, April 2020)](https://www.cs.mcgill.ca/~jpineau/ReproducibilityChecklist.pdf)
- [NeurIPS Paper Checklist Guidelines](https://neurips.cc/public/guides/PaperChecklist)
- [NeurIPS 2024 Call for Datasets & Benchmarks](https://neurips.cc/Conferences/2024/CallForDatasetsBenchmarks)
- [ACM Artifact Review and Badging — Current](https://www.acm.org/publications/policies/artifact-review-and-badging-current)
- [Understanding and Mitigating Numerical Sources of Nondeterminism in LLM Inference (arXiv:2506.09501)](https://arxiv.org/html/2506.09501v2)
- [Towards Deterministic Inference in SGLang and Reproducible RL Training (LMSYS, Sept 2025)](https://www.lmsys.org/blog/2025-09-22-sglang-deterministic/)
- [The Instability of Safety: How Random Seeds and Temperature Expose Inconsistent LLM Refusal Behavior (Larsen, arXiv:2512.12066)](https://www.arxiv.org/pdf/2512.12066)
- [MLPerf Inference Submission Rules (MLCommons)](https://github.com/mlcommons/inference_policies/blob/master/inference_rules.adoc)
- [METR — Measuring AI Ability to Complete Long Tasks (March 2025)](https://metr.org/blog/2025-03-19-measuring-ai-ability-to-complete-long-tasks/)
- [METR HCAST whitepaper](https://metr.org/hcast.pdf)
- [Apollo Research — An Opinionated Evals Reading List](https://www.apolloresearch.ai/science/an-opinionated-evals-reading-list/)
- [Marks et al., 2025 — Auditing language models for hidden objectives (arXiv:2503.10965)](https://arxiv.org/abs/2503.10965)
- [ML Reproducibility Challenge 2025 — Resources](https://reproml.org/challenge_resources/)
