# Swarm Agent 08 — Tool-Efficiency / Action-Budget Metrics

**Date:** 2026-05-27
**Source:** Second study swarm dispatch (research-grounded advisor protocol)
**Question:** How do current agent benchmarks reward tool-call efficiency? Metrics beyond step caps; canonical-count establishment; observed model-specific profiles; cost/latency proxies; false-positive risk.

---

# Research Grounding: Tool-Call Efficiency in Agent Benchmarks

Eight findings on how the literature scores tool-call efficiency, with canonical identifiers and design implications for the ai-crucible budget puzzle.

---

**1. AgentChangeBench (Caruso et al., 2025) — explicit TCRR + TUE composite, with damning numbers.** "AgentChangeBench: A Multi-Dimensional Evaluation Framework for Goal-Shift Robustness in Conversational AI," arXiv:2510.18170. https://arxiv.org/abs/2510.18170. Defines Tool Call Redundancy Rate (TCRR) as "the fraction of tool calls that are exact duplicates within a 3-turn window or exceed the batch threshold of 2 calls to the same function," and Tool Use Efficiency as TUE = 0.6·T + 0.4·P (tool correctness + parameter validity). Observed redundancy: Claude-3.7-Sonnet 75.85%, GPT-4o 89.14%, Gemini-2.5-Flash 66.45% on retail-new — high TSR with abysmal TCRR. **Implication:** adopt their 3-turn-window duplicate detection verbatim for ai-crucible's waste penalty; cap repeats of same (tool, args) at 2 per puzzle.

**2. MCPAgentBench (2025) — TFS/TEFS and per-resource score-per-unit metrics.** "MCPAgentBench: A Real-world Task Benchmark for Evaluating LLM Agent MCP Tool Use," arXiv:2512.24565. https://arxiv.org/abs/2512.24565. Distinguishes Task Finish Score (set-equality of golden tool+args) from Task Efficiency Finish Score (TEFS — additionally requires serial/parallel order match), then divides score by output tokens (Token Efficiency) and by execution minutes (Time Efficiency). Claude Sonnet 4.5 led on Time Efficiency; GPT-5 was worst on both efficiency axes. **Implication:** the "elegance bonus" should be expressed as score/canonical-calls (a TEFS analog), not just an absolute cap — that way a hard puzzle with budget=20 isn't penalized vs. a trivial puzzle with budget=3.

**3. tau-bench (Yao et al., 2024) — pass^k as efficiency-via-reliability.** "τ-bench: A Benchmark for Tool-Agent-User Interaction in Real-World Domains," arXiv:2406.12045. https://arxiv.org/abs/2406.12045. Doesn't penalize redundancy directly but measures pass^k (probability all k independent trials succeed), which collapses when agents take many redundant paths because variance compounds. Sierra blog notes some models "take nine times longer" to reach equivalent accuracy. **Implication:** pair the budget penalty with a multi-trial run (k=3) so models that succeed-by-thrashing don't get the elegance bonus — they'll fail pass^k.

**4. HAL — Holistic Agent Leaderboard (Stroebl et al., 2025) — cost as a first-class axis.** "Holistic Agent Leaderboard," arXiv:2510.11977. https://arxiv.org/abs/2510.11977. Runs every model under cost-controlled evaluation; on tau-bench Tool Calling, o4-mini and Claude-3.7 Sonnet tied at 56% accuracy but cost $11.36 vs $42.11 respectively. Reports a Pareto frontier (accuracy × $) rather than a single score. **Implication:** ai-crucible should record token spend per puzzle even if not scored directly, so post-hoc the elegance bonus can be cross-validated against $-cost. A budget puzzle's "canonical" call count should land near the Pareto frontier's elbow.

**5. AgentBoard (Ma et al., NeurIPS 2024) — progress rate via annotated sub-goals, not just success.** "AgentBoard: An Analytical Evaluation Board of Multi-turn LLM Agents," arXiv:2401.13178. https://arxiv.org/abs/2401.13178. 9 tasks, 1013 environments; introduces unified Progress Rate computed against human-annotated subgoals — explicitly to break the "all-or-nothing" success metric. Paper acknowledges subjectivity in annotation as a limitation. **Implication:** the "canonical call count" for each ai-crucible puzzle should be a human-annotated reference solution (multi-rater), not the best agent run — the latter creates an optimization target that gets gamed. AgentBoard's annotation-with-multiple-verification pattern is the right model.

**6. WebArena (Zhou et al., ICLR 2024) — 30-step cap + repeated-action early-stop.** "WebArena: A Realistic Web Environment for Building Autonomous Agents," arXiv:2307.13854 / https://webarena.dev/static/paper.pdf. Default max-steps = 30 per task; agent is force-stopped on three consecutive repetitions of the same action OR three consecutive unparseable actions. **Implication:** the "three-strikes" rule is empirically validated as a redundancy proxy — adopt it as a hard kill condition in ai-crucible, separate from the soft waste penalty. Distinguishes genuine exploration (varied actions that fail) from pathological loops (identical action repeated).

**7. AgentBench (Liu et al., ICLR 2024) — per-environment budgets are heterogeneous and small.** "AgentBench: Evaluating LLMs as Agents," arXiv:2308.03688. https://arxiv.org/abs/2308.03688. Step caps differ dramatically: OS = 8 turns, DB = 5 statements, KG = 15 steps. No efficiency metric beyond pure success; success/step ratio is not reported. **Implication:** ai-crucible should NOT use a single global budget — set per-puzzle tool_call_budget reflecting puzzle class (e.g., file-inspection = 5, multi-file-search = 12, full-repo-trace = 20). Heterogeneous budgets prevent over-fitting to one size.

**8. Budget-Aware Tool Use / BATS (2025) — exposing the budget to the agent improves it.** "Budget-Aware Tool-Use Enables Effective Agent Scaling," arXiv:2511.17006. https://arxiv.org/abs/2511.17006. Adds a Budget Tracker that gives the model continuous feedback on remaining resources; defines a unified cost metric over tokens + tool calls jointly. Reports that budget-aware agents push the cost-performance Pareto frontier. Companion work, "Spend Less, Reason Better" (arXiv:2603.12634), shows injecting an estimated-tool-call hint into the system prompt improves accuracy at lower cost. **Implication:** TELL the agent its budget. Display "tool_call_budget: 8, used: 3, remaining: 5" in the system reminder each turn. This is also the false-positive defense — if the model knows the budget is generous, it's free to do legitimate exploration; if tight, it self-rations. Hiding the budget invites the exploration-vs-redundancy ambiguity to bite.

---

**Cross-cutting design notes for ai-crucible:**

- **Canonical call count from annotators, not from best run** (Finding 5) — best-run targets get gamed.
- **Score elegance as score/canonical, not score − overage** (Finding 2) — keeps hard puzzles competitive.
- **Three-strikes hard kill + soft waste penalty** (Findings 1, 6) — different signals deserve different responses.
- **Display the budget to the model** (Finding 8) — defeats the exploration false-positive by externalizing the rationing decision.
- **Log token cost in parallel** (Finding 4) — for post-hoc Pareto validation.
