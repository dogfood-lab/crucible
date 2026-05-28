# Swarm Agent 13 — Cryptographic Provenance for ML Eval

**Date:** 2026-05-27
**Source:** Third study swarm dispatch (research-grounded advisor protocol)
**Question:** What's the state-of-the-art on tamper-evident, cryptographically-provable research records beyond simple SHA-hashing?

---

# Tamper-Evident Research Records: State-of-the-Art

## Findings (8 grounded in canonical sources)

### 1. Sigstore Model Transparency — Kerner et al. / Google Security, 2025
"Taming the Wild West of ML: Practical Model Signing with Sigstore" (Google Security Blog, April 2025) and the `sigstore/model-transparency` repo apply Sigstore's keyless OIDC signing + Rekor transparency log to ML model artifacts, producing an in-toto/DSSE attestation whose subjects are file-path/digest pairs.
**Implication for crucible:** if puzzle attempts produce result artifacts (JSONL trajectories, judge outputs), signing each artifact with `cosign sign-blob` and recording in Rekor would give external auditors a public, OIDC-bound provenance trail — no long-lived keys.
**Classification:** (a) standard practice in serious ML supply-chain work as of 2025; trending toward (a) for evals too.

### 2. in-toto Attestation Framework v1.0 — in-toto/attestation spec, 2023+
The in-toto v1 spec defines a DSSE envelope wrapping a typed `predicate` over a list of `subjects` (artifact digests). It is the de facto interchange format used by SLSA, Sigstore, and GitHub Artifact Attestations.
**Implication:** crucible's per-run record (model id, judge id, puzzle hash, transcript digest, score) is exactly a `predicate`-shaped claim. Adopting in-toto v1 means tooling (cosign verify, slsa-verifier) works out of the box.
**Classification:** (a) standard — costs almost nothing to emit attestations alongside results.

### 3. SLSA v1.0 — OpenSSF, April 2023 (current track v1.1)
SLSA defines Build levels L1–L3 specifying provenance authenticity (signed by builder), non-falsifiability (builder identity verified), and isolation. It does NOT cover ML training/eval workloads directly, but its provenance schema generalizes.
**Implication:** mapping eval-runner identity → signed provenance (GitHub Actions OIDC) gives crucible "SLSA-equivalent L2" provenance for free in CI. Useful framing for auditors who already speak SLSA.
**Classification:** (a) standard for CI-built artifacts; (b) overkill if eval runs are interactive/local — the levels don't map cleanly to manual research workflows.

### 4. RFC 3161 Time-Stamp Protocol (TSP) — IETF, 2001 (still canonical)
A Trusted Third Party countersigns a hash, producing a TimeStampToken that proves "this hash existed at this time." Stanford runs a free TSA at `timestamp.stanford.edu`; Sectigo, DigiCert, and FreeTSA also operate qualified TSAs.
**Implication for crucible:** stamping the daily roll-up hash (or each batch's Merkle root) with one TSA call (~100 ms, free) anchors all results in legally-recognized time. Single line of cron.
**Classification:** (c) genuinely necessary even at small scale — git commit timestamps are author-set and trivially forgeable; a TSA token is the cheapest defense against "you backdated those scores."

### 5. OpenTimestamps — Todd, 2016+ (active)
OTS aggregates user hashes into a Merkle tree whose root is committed to Bitcoin via OP_RETURN. Proofs are independently verifiable by anyone running a Bitcoin node — no trusted TSA required.
**Implication:** stamping crucible's release hashes with OTS gives public, third-party-independent existence proofs anchored to Bitcoin's PoW. Free, ~3 hour confirmation latency.
**Classification:** (b) overkill for a private diagnostic instrument — RFC 3161 covers 99% of attacks at lower latency. OTS becomes (c) only if crucible records are litigated or claimed as priority of discovery.

### 6. Transparent Logs for Skeptical Clients — Cox, 2019 (research.swtch.com/tlog)
Russ Cox's specification (the basis of Go's `sumdb` and Sigstore's Rekor) shows how an append-only Merkle tree exposes five APIs (Latest, RecordProof, TreeProof, Lookup) giving clients O(log N) proofs that any record is included AND that earlier observations are prefixes of the current tree. RFC 6962/9162 (Certificate Transparency) is the formal expression.
**Implication for crucible:** running a Tessera/trillian instance — or just publishing a Merkle-DAG of result batches with periodic signed tree heads — lets auditors verify nothing was retroactively deleted or edited, not just that individual records are signed. Distinct from per-record signatures: defends against silent log truncation.
**Classification:** (c) necessary if "no result was suppressed" is a claim the instrument needs to make; (b) otherwise. Most evals don't make this claim explicitly, but if crucible compares models, suppression bias is exactly the threat.

### 7. zkLLM — Sun et al., CCS 2024 (arXiv:2404.16109)
Zero-knowledge proof that a specific LLM (≤13B params) produced a specific output, with <200 KB proof in <15 min on GPU. Verifier learns nothing about weights.
**Implication for crucible:** would let crucible prove "model X actually produced this transcript" without API-provider trust. But the prover is the model owner — Anthropic, OpenAI, etc. would need to ship proofs. They don't, and won't soon.
**Classification:** (b) overkill — depends on cooperation crucible cannot obtain. Watch but don't adopt.

### 8. MLCommons MedPerf Smart-Contract Attestation — MLCommons, March 2025
MedPerf uses bi-directional attestation between smart contracts and enclave-resident "digital guardians" so that benchmark results on private medical data are provably executed under policy. Closest production example of cryptographic eval-integrity at scale.
**Implication:** demonstrates that serious benchmarking orgs are now adopting enclave + on-chain attestation, not just signed artifacts. Confirms the direction; the implementation is far heavier than crucible needs.
**Classification:** (b) overkill — useful as a citation when auditors ask "what does state-of-the-art look like," not as a target.

---

## Synthesis for crucible

Minimum viable upgrade above signed git commits: **RFC 3161 timestamp on each batch's Merkle root + in-toto v1 attestation per result, optionally logged to Rekor.** That covers (a) "did X happen at time T" (TSA), (b) "what was the content of result Y" (in-toto digest), (c) "who produced it" (OIDC identity in Fulcio cert). The Sigstore + RFC 3161 combination is what serious 2025 ML supply-chain work uses, costs ~one engineering day to wire, and gives auditors a verification path that matches existing tooling.

Treat OpenTimestamps, transparent-log servers, and zkLLM as optional ceiling — adopt only if a specific threat (priority disputes, silent suppression, untrusted model-provider) requires it.

## Sources

- [Taming the Wild West of ML: Practical Model Signing with Sigstore (Google Security, 2025)](https://security.googleblog.com/2025/04/taming-wild-west-of-ml-practical-model.html)
- [sigstore/model-transparency repo](https://github.com/sigstore/model-transparency)
- [in-toto Attestation Framework spec v1](https://github.com/in-toto/attestation/blob/main/spec/v1/envelope.md)
- [OpenSSF SLSA v1.0 release announcement](https://openssf.org/press-release/2023/04/19/openssf-announces-slsa-version-1-0-release/)
- [RFC 3161: Time-Stamp Protocol](https://datatracker.ietf.org/doc/html/rfc3161) ; [Stanford Free TSA](https://timestamp.stanford.edu/)
- [OpenTimestamps protocol & Wikipedia](https://en.wikipedia.org/wiki/OpenTimestamps)
- [Russ Cox — Transparent Logs for Skeptical Clients](https://research.swtch.com/tlog)
- [RFC 6962: Certificate Transparency](https://www.rfc-editor.org/rfc/rfc6962.html) ; [RFC 9162: CT v2](https://datatracker.ietf.org/doc/html/rfc9162)
- [zkLLM: Zero Knowledge Proofs for Large Language Models (Sun et al., CCS 2024, arXiv:2404.16109)](https://arxiv.org/abs/2404.16109)
- [MLCommons MedPerf smart-contract attestation (March 2025)](https://mlcommons.org/2025/03/medperf-smart-contracts/)
- [Rekor transparency log overview (Sigstore docs)](https://docs.sigstore.dev/logging/overview/)
