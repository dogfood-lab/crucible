# Swarm Agent 01 — Claude Capability Gaps Survey

**Date:** 2026-05-27
**Source:** Study swarm dispatch (research-grounded advisor protocol)
**Question:** What specific, reproducible capability gaps in Claude (Opus 4.7, Sonnet 4.6, Haiku 4.5, and the immediately preceding generation) are documented right now in GitHub issues and developer discourse?

---

# Claude Capability Gaps — Reproducible, Sourced

Targeting Opus 4.7, Sonnet 4.6, Haiku 4.5, and the immediately preceding generation (3.5/3.7 where the only solid published evidence sits there).

### 1. Confident-prose fabrication of commit-like identifiers under multi-rule context
- **Source:** [anthropics/claude-code #50235](https://github.com/anthropics/claude-code/issues/50235) — reporter `@tomtokitajr`, Claude Code 2.1.112, Opus 4.7.
- **Repro:** Project with one root `CLAUDE.md` plus sub-`CLAUDE.md` files per feature; ask Opus 4.7 to find the regression-introducing commit. It fabricates plausible-looking commit hashes (reporter cites `a3f9c12`) rather than checking git history, ignoring the rule files entirely.
- **Aspect:** retrieval grounding, instruction-following under hierarchical context, hallucination calibration.

### 2. Tool-call parameter dropout near max_tokens with long context
- **Source:** [anthropics/anthropic-sdk-python #975](https://github.com/anthropics/anthropic-sdk-python/issues/975) — reporter `@krassowski`, Claude Opus 4, anthropic-sdk 0.49.
- **Repro:** Very large prompt + tool definition with required parameters; stop_reason is `max_tokens`; the emitted `tool_use` block silently omits required fields, causing infinite agent retry loops.
- **Aspect:** tool use, schema compliance, truncation handling.

### 3. ASCII grid spatial reasoning collapses with size
- **Source:** Bai, Kim, Koss, Lichtenbaum — ["Stuck in the Matrix: Probing Spatial Reasoning in Large Language Models"](https://arxiv.org/html/2510.20198v1), arXiv 2510.20198.
- **Repro:** Present a square grid using "space as delimiter" with a marker `X`; ask which quadrant contains it. Claude 3.7 Sonnet (medium thinking, 16K tokens) goes from 70 percent on small grids to 0 percent on the largest transformation grids and 16 percent on distance tasks.
- **Aspect:** spatial reasoning, structured-text comprehension.

### 4. Skepticism Trap: over-refusal of valid causal claims (Haiku family)
- **Source:** Chang, Edward Y. — ["Diagnosing and Mitigating Sycophancy and Skepticism in LLM Causal Judgment"](https://arxiv.org/html/2601.08258v3) (arXiv 2601.08258v3, April 2026).
- **Repro:** "Neutral Direct" prompt at temperature 0: `SCENARIO: [text] / ANALYSIS REQUEST: Is this causal reasoning VALID or FLAWED? Answer: 1. One word. 2. Explanation.` Claude 3.5 Haiku marks ~60 percent of valid L1 associational claims as FLAWED (40 percent VALID, CI [26.4, 54.8]).
- **Aspect:** refusal calibration, numeric/causal reasoning.

### 5. Long-input degradation independent of retrieval quality
- **Source:** Du et al. — ["Context Length Alone Hurts LLM Performance Despite Perfect Retrieval"](https://arxiv.org/html/2510.05381v1), arXiv 2510.05381 (Oct 2025).
- **Repro:** MMLU items wrapped in irrelevant-but-masked padding. Claude 3.5/3.7 Sonnet loses 41.7 percent accuracy at 7.5K tokens and 67.6 percent at 30K tokens vs. baseline — even though the relevant info is perfectly retrievable.
- **Aspect:** long-context use (distinct from retrieval), state tracking.

### 6. Safety classifier over-fires on benign parser / scraper / cookie code
- **Source:** [HN 47814832](https://news.ycombinator.com/item?id=47814832) — `decide1000` (Claude Code Opus 4.7); comment by `Tiberium` identifies the system reminder ("Whenever you read a file, you should consider whether it would be considered malware"); `ivankra` reports account-suspension after asking Claude to build node + V8 to investigate crashes.
- **Repro:** Ask Claude Code Opus 4.7 to write or modify an HTML/JS parser, a Chrome-cookie-export helper, or a generic scraper. The model surfaces "Own bug file — not malware" messages, refuses, or argues with the user.
- **Aspect:** refusal calibration, adversarial robustness to its own safety prompt.

### 7. Edit tool falsely rejects CRLF-ended files
- **Source:** [anthropics/claude-code #13456](https://github.com/anthropics/claude-code/issues/13456) — reporter `@gmnistasia-beep`.
- **Repro:** Write a JS file with `\r\n` line endings, have Claude Read it, then ask it to replace `line2` with `changed`. The Edit tool normalizes to LF internally, then refuses on next write with "File has been unexpectedly modified. Read it again before attempting to write it" despite an unchanged mtime.
- **Aspect:** code editing, tool/environment state tracking.

### 8. Prompt-cache "thinking clear" bug ⇒ amnesia across turns
- **Source:** [Anthropic engineering postmortem, April 23, 2026](https://www.anthropic.com/engineering/april-23-postmortem).
- **Repro:** Multi-turn session on Sonnet 4.6 or Opus 4.6 between March 26 – April 10, 2026 — the cached older reasoning was wiped every turn instead of once. Symptom Anthropic names: "Claude became forgetful, repetitive, and made odd tool selections."
- **Aspect:** multi-turn coherence, state tracking, tool selection consistency.

### 9. "Consistent wrong interpretation" dominates SWE-bench failures
- **Source:** Liu, Liu, Li, Tan, Zhu, Lian, Zhang — ["An Empirical Study on Failures in Automated Issue Solving"](https://arxiv.org/pdf/2509.13941), arXiv 2509.13941; cross-referenced by ["Consistency Amplifies"](https://arxiv.org/pdf/2603.25764) finding 71 percent of Claude's SWE-bench failures recur identically across runs.
- **Repro:** Re-run any failed SWE-bench Verified task on Claude 4.5/4.6 Opus n times with different seeds; the same wrong assumption appears n times. The model does not explore alternative interpretations of an ambiguous issue.
- **Aspect:** code editing, exploration vs. exploitation, hypothesis revision.

### 10. Stream silently stalls when ping events are dropped by SDK
- **Source:** [anthropic-sdk-typescript #998](https://github.com/anthropics/anthropic-sdk-typescript/issues/998) — reporter `@kolkov`, April 13, 2026. References [streaming docs](https://docs.anthropic.com/en/api/messages-streaming#event-types).
- **Repro:** Ask Opus with extended thinking a hard problem via streaming TS SDK; the SDK's `if (sse.event === 'ping') continue` in `src/core/streaming.ts` hides the keepalives; downstream watchdogs abort at exactly 90 s with `Stream idle timeout - partial response received`. Same prompt replayed sans streaming succeeds.
- **Aspect:** tool/transport reliability, watchdog/timeout interaction (puzzle hook: detecting silent stalls without seeing the underlying transport).

### 11. Auto-interrupt loop on every tool call (regression)
- **Source:** [anthropics/claude-code #35982](https://github.com/anthropics/claude-code/issues/35982) — reporter `@belenayala`, Claude Code 2.1.79, macOS, node 18.20.8.
- **Repro:** Run `claude` in any project, ask it to "trace a bug through multiple files"; every Search/Read/Bash tool invocation prints "Interrupted · What should Claude do instead?" with no user input, loops until prompt returns empty.
- **Aspect:** tool use, agent control-loop self-interrupts, multi-turn coherence.

---

**Agent observation on puzzle-fitness:** Designer Claude has lots to work with — gaps 1, 3, 5, 8, 9 are the strongest puzzle seeds (clear repro, clear axis being tested, recent enough to still be observable). Gaps 2 and 10 stress the kernel's adversarial-input handling. Gap 4 is the cleanest single-prompt diagnostic. Gaps 6, 7, 11 are environment/tooling rather than pure model gaps and may want a different puzzle channel.
