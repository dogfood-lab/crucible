# Swarm Agent 05 — Agent Eval Methodology

**Date:** 2026-05-27
**Source:** Study swarm dispatch (research-grounded advisor protocol)
**Question:** What's the state-of-the-art on evaluating interactive agent tasks — rollout horizons, state mocking, partial credit, reproducibility under stochastic policies?

---

# State-of-the-Art on Evaluating Interactive Agent Tasks

## 1. Jimenez et al., 2023 — *SWE-bench: Can Language Models Resolve Real-World GitHub Issues?* (arXiv:2310.06770)
URL: https://arxiv.org/abs/2310.06770
2,294 instances from 12 Python repos; scoring is **binary execution-based**: model patch must flip a held-out `FAIL_TO_PASS` set (mean ~9.1 tests/instance) AND preserve `PASS_TO_PASS` regression tests (~51/instance) — tests are never shown to the agent.
**Kernel implication:** scoring should reuse the agent's own oracle (hidden assertion set + regression set) rather than string-matching a "correct answer," because string-equality scoring inflates false positives when multiple valid solutions exist.

## 2. Zhou et al., 2023 — *WebArena: A Realistic Web Environment for Building Autonomous Agents* (arXiv:2307.13854)
URL: https://arxiv.org/abs/2307.13854
812 long-horizon tasks; **30-step hard cap** per episode (App. A.6); three programmatic evaluator types — `exact_match`, `must_include`, `fuzzy_match` (LLM-judged semantic equivalence); state reset by **stopping/restarting Docker containers from a baseline image** (Appendix A.2), seconds-to-1-minute per reset.
**Kernel implication:** the kernel needs a step budget (treat 30 as a calibrated upper bound for "long-horizon") AND multiple evaluator backends, because not every puzzle answer is a string — some are state-change assertions checkable only programmatically.

## 3. Xie et al., 2024 — *OSWorld: Benchmarking Multimodal Agents for Open-Ended Tasks in Real Computer Environments* (arXiv:2404.07972, NeurIPS 2024)
URL: https://arxiv.org/abs/2404.07972
369 real OS tasks; each task ships an **initial-state setup config + custom execution-based evaluation script**; humans 72.36%, best model 12.24% (binary success). Real VM-backed (Ubuntu/Windows/macOS).
**Kernel implication:** ship every puzzle as `{setup_script, eval_script}` co-located with the task definition — running the puzzle and grading it should be two separate sandboxed processes, not the agent's word-for-it.

## 4. Liu et al., 2023 — *AgentBench: Evaluating LLMs as Agents* (arXiv:2308.03688, ICLR 2024)
URL: https://arxiv.org/abs/2308.03688
8 environments with **per-environment metrics**: OS/DB/HH use Success Rate, KG uses Answer F1, DCG uses Reward+Win-rate, LTP uses Game Progress, WS uses Reward, WB uses Step-SR. Step budgets vary by environment: 5 (DB, WS) up to **35 (HouseHolding)**.
**Kernel implication:** don't force a single metric across puzzle types — wire metric per puzzle-class (binary / partial-credit / progress / F1) because a one-size-fits-all score throws away signal on continuous tasks.

## 5. Yao et al., 2024 — *τ-bench: Tool-Agent-User Interaction in Real-World Domains* (arXiv:2406.12045, ICLR 2025)
URL: https://arxiv.org/abs/2406.12045
115 retail + 50 airline tasks; scoring compares **end-of-conversation database state to annotated goal state** (not just final text). Introduces **pass^k = "all k independent trials succeeded"** (P^k, exponentially decaying) versus pass@k = "≥1 succeeded." GPT-4o: <50% pass@1, **pass^8 < 25%** in retail.
**Kernel implication:** report pass^k (consistency), not just pass@1, because Solver Claude's reliability matters more than its peak — a kernel that grades only best-of-N hides the inconsistency that breaks production agents.

## 6. Mialon et al., 2023 — *GAIA: A Benchmark for General AI Assistants* (arXiv:2311.12983)
URL: https://arxiv.org/abs/2311.12983
466 questions, 3 difficulty levels, **quasi-exact-match scoring with type-aware normalization** against a single unambiguous answer; **3 runs averaged per task** when API allows; explicitly designed so scoring is "robust to randomness of token generation since only the final answer is evaluated" (§7.3).
**Kernel implication:** if the puzzle has a unique final answer, normalize types before comparing (numbers, lists, strings) and **average ≥3 rollouts** — single-run scoring is statistical noise.

## 7. Qin et al., 2023 / Guo et al., 2024 — *ToolLLM* (arXiv:2307.16789) → *StableToolBench* (arXiv:2403.07714)
URL: https://arxiv.org/abs/2403.07714
Original ToolBench used 16,464 live RapidAPI endpoints; **API instability made results irreproducible across days**. StableToolBench replaces live APIs with a caching virtual server + LLM API simulator (MirrorAPI) to eliminate environment-side variance.
**Kernel implication:** never let puzzle outcomes depend on live external services — cache/mock every external call so the same trajectory grades identically tomorrow.

## 8. Zhang et al., 2025 — *SWE-bench Goes Live!* (arXiv:2505.23419)
URL: https://arxiv.org/abs/2505.23419
1,319 tasks from GitHub issues filed Jan 2024–Apr 2025 with **automated curation pipeline** for continuous additions; contamination-resistant by construction (post-cutoff issues only).
**Kernel implication:** version puzzle sets by creation date and rotate the public set, because the moment a puzzle leaks into training data its diagnostic signal is dead.

---

## Cross-cutting numbers worth pinning

- **Typical horizons:** 5–35 steps (AgentBench per-env), 30 (WebArena), unbounded but human-bounded (OSWorld, GAIA, τ-bench)
- **Typical success-rate ranges (2024 frontier):** 12% (OSWorld), 14% (WebArena GPT-4), 15% (GAIA GPT-4+plugins), <50% pass@1 / <25% pass^8 (τ-bench retail GPT-4o), 78–93% (SWE-bench Verified, post-saturation)
- **Reproducibility floor:** Bjarnason et al. 2026 (*On Randomness in Agentic Evals*, arXiv:2602.07150) show pass@1 single-run estimates vary **2.2–6.0 pp** between runs even at temperature 0; std-dev > 1.5pp — meaning any claimed improvement under ~3pp is noise without multi-run averaging.

## Sources

- [SWE-bench (Jimenez et al. 2023)](https://arxiv.org/abs/2310.06770)
- [WebArena (Zhou et al. 2023)](https://arxiv.org/abs/2307.13854)
- [OSWorld (Xie et al. 2024)](https://arxiv.org/abs/2404.07972)
- [AgentBench (Liu et al. 2023)](https://arxiv.org/abs/2308.03688)
- [τ-bench (Yao et al. 2024)](https://arxiv.org/abs/2406.12045)
- [GAIA (Mialon et al. 2023)](https://arxiv.org/abs/2311.12983)
- [ToolLLM (Qin et al. 2023)](https://arxiv.org/abs/2307.16789)
- [StableToolBench (Guo et al. 2024)](https://arxiv.org/abs/2403.07714)
- [SWE-bench Live (Zhang et al. 2025)](https://arxiv.org/abs/2505.23419)
- [On Randomness in Agentic Evals (Bjarnason et al. 2026)](https://arxiv.org/pdf/2602.07150)
- [VisualWebArena (Koh et al. 2024)](https://arxiv.org/abs/2401.13649)
