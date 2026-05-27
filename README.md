# crucible

Diagnostic adversarial game for Claude. One Claude session ("Designer") crafts puzzles targeting real, currently-observed Claude capability gaps. Another Claude session ("Solver") attempts them. A policy-enforced kernel mediates, scores, and curates a catalog with a `Lab → Arena → Regression` lifecycle.

Puzzles are grounded in empirical signal — GitHub issues, social discourse, academic literature, internal dogfood findings — not synthetic. The system is a diagnostic instrument that happens to be fun.

**Working name.** Easy to swap before anything ships.
**Private.** Pre-Phase-1.

## Where to look

- [`docs/gameplan.md`](docs/gameplan.md) — phases, current state, open questions
- [`docs/research-grounding.md`](docs/research-grounding.md) — design decisions with citations
- [`docs/phase-0/`](docs/phase-0/) — raw research outputs (ChatGPT Deep Research + 5-agent study swarm)
