# Swarm Agent 14 — Third-Party Audit and Replication Infrastructure

**Date:** 2026-05-27
**Source:** Third study swarm dispatch (research-grounded advisor protocol)
**Question:** What infrastructure differentiates "publishable but unauditable" from "fully audit-ready" for an interactive LLM evaluation?

---

# Audit Infrastructure for Interactive LLM Evals — Findings for Crucible

The gap between "publishable" and "audit-ready" is not about polish — it is about specific infrastructure that lets a hostile third party rebuild and rerun your eval from scratch and arrive at numbers within a published tolerance band. Six findings, each with concrete crucible implications.

## 1. ACM's two-tier badging gives crucible its operational target

ACM distinguishes **Results Reproduced** (a different team uses *your* artifacts to obtain matching results within tolerance) from **Results Replicated** (a different team builds *independent* artifacts and obtains matching results). The reproduction badge requires the Artifact Evaluation Committee to "independently repeat the experiments and obtain results that support the claims" within an explicit allowed tolerance — not bitwise identical. Only "Artifact Evaluated" and "Artifacts Available" badges can be claimed pre-publication; the others are post-publication awards by an external committee. (https://www.acm.org/publications/policies/artifact-review-badging, https://sigir.org/general-information/acm-sigir-artifact-badging/)

**Crucible implication:** publish an explicit tolerance band per headline metric (e.g., "task success rate within +/-3pp at 95% CI"), publish your AEC-style artifact bundle, and invite a third-party evaluator to award the badge post-hoc. Without a published tolerance, every replication "fails."

## 2. Closed-API LLMs are nondeterministic even at temperature 0 — batch effects dominate

Thinking Machines Lab (Sept 2025) showed that running the same prompt 1,000 times at temperature 0 produced **80 unique completions** before they fixed it; after replacing RMSNorm, matmul, and attention with batch-invariant kernels, all 1,000 were bitwise identical. SGLang reproduced this and reported ~34% inference overhead as the cost of determinism, single-GPU only, dense models only. (https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/, https://www.lmsys.org/blog/2025-09-22-sglang-deterministic/)

**Crucible implication:** for closed-API models, pin `system_fingerprint` (OpenAI) or equivalent and *record it in every transcript*; report results as **distributions over N seeds**, not point estimates. For any in-house / open-weight component, document whether batch-invariant kernels are used. Replicators cannot achieve bitwise match on a closed API — they need a statistical tolerance to aim at.

## 3. Commercial LLM benchmark replication fails primarily from undocumented provider drift

A 2025 reflection paper on commercial LLM reproducibility in software engineering studies identifies the failure modes: silent model-version updates (the "ChatGPT behavior changing time" effect), undocumented API parameter changes (function calling, structured output), batch/temperature inconsistencies, and prompt-formatting drift (whitespace, instruction phrasing). Of "functional" artifacts from 2024-2025, **>40% fail within months** due to drifting dependencies, unpinned versions, incomplete environments, or unclear licensing. (https://arxiv.org/html/2510.25506v3, https://arxiv.org/html/2512.00651)

**Crucible implication:** publish a "reproducibility window" — dates between which the published numbers are expected to hold. Freeze prompts byte-exactly in version control. Record `provider`, `model_id`, `system_fingerprint`, `api_version`, `request_timestamp` per call. Snapshot model outputs (raw transcripts), not just scores.

## 4. The auditing-games / external-verifier pattern requires *training-based capability elicitation*, not just black-box prompting

Taylor et al. (2025), "Auditing Games for Sandbagging," ran a red-team/blue-team study where the blue team had to discriminate sandbagging models from benign ones. **Black-box approaches were defeated by competent imitation of weaker models. Linear probes showed promise but were defeatable by red-team-instilled behaviors. Only training-based elicitation reliably elicited full capability**, and required "only a single correct demonstration." (https://arxiv.org/abs/2512.07810)

**Crucible implication:** if crucible measures capability, prompt-based elicitation is insufficient against an adversarial model. Audit-ready capability claims need (a) full model access for internals analysis, OR (b) a fine-tuning/elicitation path with at least one in-distribution demonstration. State which tier you're operating at; this is the difference between "we tested" and "we audited."

## 5. The Frontier Model Forum and AALs framework formalize access tiers as the audit boundary

Frontier Model Forum's Third-Party Assessment report and arXiv 2601.11699's four AI Assurance Levels (AALs) both treat **model access tier as the load-bearing variable**: external assessors need access "with fewer safety mitigations than release versions," with affordances for "fine-tuning with custom loss functions or activations" to minimize sandbagging risk. arXiv 2601.11916 ("Expanding External Access to Frontier AI Models for Dangerous Capability Evaluations") lays out concrete access tiers from black-box API up to weight-level access. (https://www.frontiermodelforum.org/technical-reports/third-party-assessments/, https://arxiv.org/pdf/2601.11699, https://arxiv.org/html/2601.11916)

**Crucible implication:** declare your access tier explicitly in the methodology section (e.g., "Black-box API, temperature 0, seed pinned, no weights, no logprobs"). A reader can then bound what crucible's results *cannot* claim — without weight access, you cannot rule out internalized sandbagging; without logprobs you cannot probe capability ceiling.

## 6. The framework is already built — use Inspect AI + Croissant + Docker digests, not a bespoke stack

UK AISI's **Inspect AI** is now the de facto frontier eval framework: typed, sandboxed (Docker built-in, K8s/Proxmox optional), with structured logs and a viewer. Anthropic, DeepMind, and others have adopted it. **NeurIPS 2025 D&B Track** mandates Croissant metadata for datasets and persistent public repositories (HF, Kaggle, Dataverse, Zenodo) — 80% of accepted papers use one of these; self-hosted is 13% and discouraged. **Pinning Docker base images by SHA256 digest** (not tag) is the Docker-side reproducibility primitive — `FROM image@sha256:...` guarantees byte-identical pulls regardless of upstream tag mutation. (https://github.com/UKGovernmentBEIS/inspect_ai, https://blog.neurips.cc/2025/12/05/neurips-datasets-benchmarks-track-from-art-to-science-in-ai-evaluations/, https://docs.docker.com/dhi/core-concepts/digests/)

**Crucible implication:** if crucible's task harness isn't already Inspect-compatible, building Inspect-compatible task definitions is the highest-leverage move for credibility (peer auditors already have the tooling). Ship a `Dockerfile` with all `FROM` lines pinned by digest, a Croissant `metadata.json` for any dataset, and publish artifacts on Zenodo or HuggingFace for DOI/persistent hosting. These three moves alone move crucible from "publishable" to "AEC-evaluable."

## What concretely separates publishable from audit-ready (the consolidated checklist)

- **Tolerance band published per headline metric** (no claim of bitwise reproducibility against closed APIs)
- **Access tier declared** (black-box / logprobs / fine-tune / weights) per FMF & AAL framework
- **Reproducibility window declared** (calendar dates within which numbers expected to hold)
- **`system_fingerprint` / model snapshot ID recorded per call**, transcripts archived raw
- **Container pinned by SHA256 digest, not tag**; lockfile for all language deps
- **Croissant metadata** on any task/dataset; persistent hosting (Zenodo DOI or HF Hub)
- **Inspect AI task definitions** so external auditors run via tooling they already trust
- **Capability elicitation path documented** (single in-distribution demonstration available for training-based elicitation if any capability claim is load-bearing)
- **Independent third-party assessor invited post-publication** to award an ACM-style "Results Reproduced" badge against the published tolerance band

The first three items are the cheapest and highest-impact; the last item is the one that converts "we published artifacts" into "an audit happened."

---

## Sources

- [ACM Artifact Review and Badging Policy](https://www.acm.org/publications/policies/artifact-review-badging)
- [NeurIPS 2025 Datasets & Benchmarks Track Reflection](https://blog.neurips.cc/2025/12/05/neurips-datasets-benchmarks-track-from-art-to-science-in-ai-evaluations/)
- [Thinking Machines Lab — Defeating Nondeterminism in LLM Inference](https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/)
- [LMSYS SGLang Deterministic Inference Blog](https://www.lmsys.org/blog/2025-09-22-sglang-deterministic/)
- [Reflections on the Reproducibility of Commercial LLM Performance in ESE Studies (arXiv:2510.25506)](https://arxiv.org/html/2510.25506v3)
- [LLMs for Software Engineering: A Reproducibility Crisis (arXiv:2512.00651)](https://arxiv.org/html/2512.00651)
- [Taylor et al. 2025 — Auditing Games for Sandbagging (arXiv:2512.07810)](https://arxiv.org/abs/2512.07810)
- [Frontier AI Auditing: Toward Rigorous Third-Party Assessment (arXiv:2601.11699)](https://arxiv.org/abs/2601.11699)
- [Expanding External Access to Frontier AI Models (arXiv:2601.11916)](https://arxiv.org/html/2601.11916)
- [Frontier Model Forum — Third-Party Assessments Technical Report](https://www.frontiermodelforum.org/technical-reports/third-party-assessments/)
- [Inspect AI — UK AISI Evaluation Framework (GitHub)](https://github.com/UKGovernmentBEIS/inspect_ai)
- [Docker Image Digests Docs](https://docs.docker.com/dhi/core-concepts/digests/)
- [PaperBench: Evaluating AI's Ability to Replicate AI Research (arXiv:2504.01848)](https://arxiv.org/abs/2504.01848)
- [METR Example Evaluation Protocol](https://evaluations.metr.org/example-protocol/)
