# Swarm Agent 02 — Designer-Bias in LLM Self-Play

**Date:** 2026-05-27
**Source:** Study swarm dispatch (research-grounded advisor protocol)
**Question:** What does the literature say about designer-bias, evaluator-bias, and self-preference in LLM-vs-LLM and self-play setups?

---

# Research grounding: same-model designer/solver bias

**Bottom line:** Self-preference bias in same-model setups is real, has been quantitatively measured at non-trivial effect sizes (10-40 percentage points depending on task and model), and has *mechanistic* drivers (familiarity / perplexity) that explain why "different prompts" alone is insufficient mitigation. Cross-family ensembles and debate-style adversarial setups have the strongest empirical support as fixes.

---

**1. Panickssery, Bowman & Feng (2024) — "LLM Evaluators Recognize and Favor Their Own Generations"** (arXiv:2404.13076, NeurIPS 2024). https://arxiv.org/abs/2404.13076
GPT-4 prefers its own outputs at 0.71 (XSUM) and 0.91 (CNN/DailyMail) pairwise — i.e., picks itself 70-90% of the time when humans rate the outputs equal — and self-recognizes its own text at 73.5% accuracy out-of-the-box; fine-tuning to boost self-recognition *linearly* boosts self-preference, evidence the two are causally linked.
**Implication for our design:** the same-model Designer/Solver pair will systematically produce puzzles the Solver finds "natural" because Solver implicitly recognizes Designer's distribution; budget for a 20-40pp self-preference inflation in any solve-rate metric.

**2. Wataoka et al. (2024) — "Self-Preference Bias in LLM-as-a-Judge"** (arXiv:2410.21819). https://arxiv.org/abs/2410.21819
The mechanism is *perplexity*, not conscious self-recognition: LLMs systematically over-rate low-perplexity text relative to humans, and their own outputs are low-perplexity to themselves; bias persists "regardless of whether the text was self-generated."
**Implication:** changing the Designer prompt or system message will NOT eliminate the bias — the Solver will still find Designer-distribution puzzles low-perplexity. Need distributional difference (different model, different sampler temperature, or paraphrase-through-third-model), not just prompt difference.

**3. Zheng et al. (2023) — "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena"** (arXiv:2306.05685, NeurIPS 2023). https://arxiv.org/abs/2306.05685
Coined and measured *self-enhancement bias*, *position bias*, and *verbosity bias*; GPT-4 hits ~80% agreement with humans (matching human-human agreement) but only after explicit mitigations like swap-position averaging and reference-answer grounding.
**Implication:** even strong models need procedural mitigations — adopt their swap-and-average pattern for any Solver scoring, and include ground-truth references whenever the puzzle admits one.

**4. Verga et al. (2024) — "Replacing Judges with Juries (PoLL)"** (arXiv:2404.18796). https://arxiv.org/abs/2404.18796
A panel of 3 smaller models from *disjoint families* (Command-R, GPT-3.5, Claude Haiku) correlates with humans *better* than a single GPT-4 judge at 1/7 the cost; explicitly cited as the fix for "intra-model bias."
**Implication:** if budget allows, a 3-model cross-family Solver panel (Claude + GPT + open-weights) is the single highest-leverage mitigation; the cost story also rebuts "but Opus-on-both-sides is cheaper."

**5. Khan et al. (2024) — "Debating with More Persuasive LLMs Leads to More Truthful Answers"** (arXiv:2402.06782, ICML 2024 Best Paper). https://arxiv.org/abs/2402.06782
Two-debater protocols lift non-expert judge accuracy from 48% naive baseline to 76% (and 60→88% for humans); persuasiveness optimization helps rather than hurts truth recovery.
**Implication:** if the Designer/Solver mode keeps same-model on both sides, adding a *third* adversarial "Critic" agent (even same model) reading both sides recovers meaningful signal — the asymmetry between defending vs. attacking a position partially breaks self-preference.

**6. Nie et al. (2020) — "Adversarial NLI: A New Benchmark"** (arXiv:1910.14599, ACL 2020). https://arxiv.org/abs/1910.14599
The HAMLET human-and-model-in-the-loop protocol established that adversarially-collected examples remain hard even for next-generation models — but only when the *adversary differs from the target*; co-adapted generator/discriminator pairs converge to a stable equilibrium that doesn't probe real weaknesses.
**Implication:** a same-model Designer will converge on puzzles the Solver tolerates; rotate the Designer model across generations (or seed Designer with externally-collected hard cases) to prevent the equilibrium.

**7. Irving, Christiano & Amodei (2018) — "AI Safety via Debate"** (arXiv:1805.00899). https://arxiv.org/abs/1805.00899
Theoretical foundation: zero-sum debate between equally-capable agents can in principle let a weaker judge answer any PSPACE question; but the guarantee depends on the debaters having *opposed* incentives. Self-play with shared parameters violates this.
**Implication:** if Designer and Solver share weights AND incentives (e.g., both want "interesting puzzle"), the theoretical guarantee collapses; ensure their reward functions are explicitly adversarial (Designer rewarded for Solver-failure, Solver for Designer-failure) and verify the gradient pull is actually opposed in practice.

**8. Bai et al. (2022) — "Constitutional AI: Harmlessness from AI Feedback"** (arXiv:2212.08073). https://arxiv.org/abs/2212.08073
Anthropic's RLAIF pipeline uses a model to red-team and critique itself, but the critical detail is the *constitution* — externally-authored principles that anchor the critique to something outside the model's distribution; without the constitution, the self-critique collapses.
**Implication:** if we must use same-model on both sides, supply an external rubric (the "constitution" analog) the Solver scores against — solve-rate alone is insufficient signal; pair it with rubric-based difficulty scoring that's harder to game via distributional familiarity.

---

**Design recommendations ranked by empirical support:**
1. **Cross-family Solver panel** (Verga) — strongest mitigation, lowest cost
2. **Swap-and-average / reference-grounded scoring** (Zheng) — procedural, easy to add
3. **External rubric anchor** (Bai) — required if same-model is non-negotiable
4. **Rotate Designer model across generations** (Nie) — prevents equilibrium collapse
5. **Adversarial Critic third agent** (Khan) — partial fix when budget forbids cross-family
6. **Different sampling temp / paraphrase** — weakest, won't beat the perplexity mechanism (Wataoka)
