# crucible

Diagnostic adversarial game for Claude. One Claude session ("Designer") crafts puzzles targeting real, currently-observed Claude capability gaps. Another Claude session ("Solver") attempts them. A policy-enforced kernel mediates, scores, and curates a catalog with a `Lab → Arena → Regression` lifecycle.

Puzzles are grounded in empirical signal — GitHub issues, social discourse, academic literature, internal dogfood findings — not synthetic. The system is a diagnostic instrument that happens to be fun.

**Working name.** Easy to swap before anything ships.
**Private.** Pre-Phase-1.

## Where to look

- [`docs/gameplan.md`](docs/gameplan.md) — phases, current state, open questions
- [`docs/research-grounding.md`](docs/research-grounding.md) — design decisions with citations (§1-7 foundations, §8 auditing-game design, §9 scientific instrument design)
- [`docs/attestia-integration-roadmap.md`](docs/attestia-integration-roadmap.md) — planned future dogfood swarm to extend `mcp-tool-shop-org/Attestia` into crucible's audit-chain backbone
- [`docs/phase-0/`](docs/phase-0/) — raw research outputs (ChatGPT Deep Research + three study swarms covering capability gaps, designer-bias, scoring methodology, benchmark designs, agent eval, reward-hacking detection, multi-criterion scoring, tool-efficiency metrics, honeypot patterns, eval-integrity, replication packages, pre-registration, cryptographic provenance, third-party audit, ablation/tuning)
