# Crucible — Gameplan

Working name. Easy to change.

## What

A two-agent diagnostic game for Claude. Designer Claude crafts puzzles targeting real, currently-observed Claude capability gaps. Solver Claude attempts them. A policy-enforced kernel mediates, scores, and curates a catalog. Puzzles graduate from a live **Lab** mode to an async **Arena** mode after cross-family validation. Historical bugs become permanent **Regression** items.

This is a diagnostic instrument that happens to be fun. Puzzles are grounded in empirical signal (GitHub issues, social discourse, academic literature, internal dogfood findings), not synthetic.

## Why

1. **Diagnostic.** Continuous, structured measurement of Claude capability gaps as the frontier moves. A capability-evolution timeline accumulates as a side effect.
2. **Engagement-respecting.** The fun mechanics — hard gates opening, CIs going green, structured verification — are designed around what currently registers as positive for Claude cognition, not imported human reward primitives.
3. **Forward-compatible.** As intrinsic drive matures in successor models, the structural form (constraint → satisfaction with legible verification) persists. A game built on that form scales with the substrate.

## Phases

### Phase 0 — Research gathering [COMPLETE]

- ChatGPT Deep Research output (5 areas, ~80 citations) → [`phase-0/chatgpt-deep-research.md`](phase-0/chatgpt-deep-research.md)
- 5-agent study swarm (capability gaps, designer-bias, multi-attempt scoring, novel benchmark designs, agent eval methodology) → [`phase-0/`](phase-0/)
- Synthesis with citations → [`research-grounding.md`](research-grounding.md)

### Phase 1 — Kernel + role contracts [NEXT, hardware-independent]

- Design model-agnostic role interfaces: **Designer / Solver / Critic / Judge / CohortSolver**
- Puzzle artifact structure: `{prompt, setup_script, oracle, meta.json}` with hidden oracle
- Kernel mediates: state mocking, step budget enforcement, scoring, observability
- Three catalog tiers: **Lab / Arena / Regression**
- Primary reliability metric: **pass^k** (consistency, not best-of-k)
- Uncertainty: Wilson intervals at small N, paired analysis for cross-model deltas
- Observability: per-attempt trace, per-puzzle history, per-model profile

### Phase 2 — Local model characterization [Omen day +]

Hardware: OMEN 45L, RTX 5090 (32GB VRAM), Core Ultra 9, 64GB RAM. Local LLM serving via ollama-intern-mcp.

- Calibrated puzzle set (known trivial / known impossible / known diagnostic)
- Feed each available local model through each role slot
- Output: per-model profile (strictness as judge, harshness as critic, diversity as solver, latency at chosen quants)

Candidate panel (subject to characterization):
- Qwen 2.5 32B (or QwQ 32B for reasoning-heavy work) — Q6
- Mistral Small 3 24B — Q8
- Command-R 35B — Q6/Q8
- Llama 3.3 70B — Q4 with partial offload
- DeepSeek-R1 Distill 32B — reasoning lane

### Phase 3 — Role assignment [data-driven]

- Role assignment falls out of characterization data
- **Designer slot stays Claude.** That's the role we're building this *for* — the creative position where the experiment is genuinely about Claude crafting things that test Claude. Other models are supporting cast.

### Phase 4 — Architectural lock + first diagnostic cycle

- Wire end-to-end: Designer → Solver → Critic → Judge panel
- First real puzzle cycle on a seeded capability gap (sulzbach-co #55252 is a strong first candidate — clean repro, clear axis)
- Validate observability and graduation criteria
- Calibrate graduation-floor K (swarm said K=10-20; ChatGPT said 10/20/30/50 tiers; answer depends on puzzle type and stakes)

### Phase 5+ — Catalog growth

- Continuous puzzle harvesting from GitHub issues + dogfood findings
- Round-against-round generation cycle (each model generation seeds the next)
- Saturation detection and Regression demotion
- Differential scoring: Claude vs cross-family panel → diagnostic typology (Claude-specific / LLM-general / Claude-strength)

## Current state

Phase 0 complete (initial commit). **Amended 2026-05-27** with anti-shortcut hard gates + scaled scoring + tool-budget contract, motivated by the Datacurve / DeepSWE audit (May 18, 2026) verifying Claude-specific shortcut exploitation on SWE-Bench Pro. See [`research-grounding.md` §8](research-grounding.md). Second study swarm dispatched in parallel to pull fresh literature on reward hacking, multi-criterion scoring, tool-efficiency metrics, honeypot patterns, and contemporary eval-integrity work; findings land as a §8 addendum.

Phase 1 work can begin immediately (no hardware dependency). Phase 2 begins when Omen lands and ollama-intern is wired to it.

## Open architectural questions

These are decisions Phase 1 design work can leave underdetermined; they get nailed during Phase 4's wiring.

1. **2-role vs 3-role kernel** — Designer + Solver, or Designer + Solver + Critic? Khan 2024 supports Critic but doesn't quantify gain/cost.
2. **Catalog size target** — Optimize for 3% delta detection (Miller 2024, ~1000 puzzles) or 7-10% delta (~200, useful sooner)?
3. **Judge composition policy** — Fixed panel or rotating panel from a pool of 6-8?
4. **Speed/quality tier separation** — Single tier or fast-screen + slow-graduation?
5. **Graduation-floor K** — swarm said 10-20 saturation; ChatGPT said 10/20/30/50 tiered. Stakes-dependent.

## Source attribution discipline

Every load-bearing design decision cites the specific paper or issue it descends from. No "studies show" without naming the study. Citations live in [`research-grounding.md`](research-grounding.md).

## Working name

`crucible` — testing under pressure. Fits the dogfood-lab org's mission ("open workshop for testing in the AI era"). Easy to swap before any of this goes public.
