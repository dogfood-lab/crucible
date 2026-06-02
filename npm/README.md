<p align="center">
  <a href="README.ja.md">日本語</a> | <a href="README.zh.md">中文</a> | <a href="README.es.md">Español</a> | <a href="README.fr.md">Français</a> | <a href="README.hi.md">हिन्दी</a> | <a href="README.it.md">Italiano</a> | <a href="README.pt-BR.md">Português (BR)</a>
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/dogfood-lab/ai-crucible/main/assets/logo.png" alt="ai-crucible" width="420">
</p>

<p align="center">
  <a href="https://pypi.org/project/ai-crucible/"><img src="https://img.shields.io/pypi/v/ai-crucible" alt="PyPI"></a>
  <a href="https://www.npmjs.com/package/@dogfood-lab/ai-crucible"><img src="https://img.shields.io/npm/v/@dogfood-lab/ai-crucible" alt="npm"></a>
  <a href="https://github.com/dogfood-lab/ai-crucible"><img src="https://img.shields.io/badge/source-GitHub-blue" alt="source"></a>
  <a href="https://dogfood-lab.github.io/ai-crucible/"><img src="https://img.shields.io/badge/docs-handbook-orange" alt="docs"></a>
</p>

# @dogfood-lab/ai-crucible

Zero-prerequisite **npx** front door to [`ai-crucible`](https://github.com/dogfood-lab/ai-crucible) —
a diagnostic measurement instrument that seats a **cross-family panel of local LLM judges** under a
sealed measurement boundary and scores attempts against a hidden oracle.

```bash
npx @dogfood-lab/ai-crucible --help
npx @dogfood-lab/ai-crucible characterize --k 3   # needs a local Ollama panel
```

## How it works

This package is a **thin launcher** (via [`@mcptoolshop/npm-launcher`](https://www.npmjs.com/package/@mcptoolshop/npm-launcher)):
on first run it downloads the platform binary from the matching
[GitHub Release](https://github.com/dogfood-lab/ai-crucible/releases), verifies its **SHA-256**
against the release's `checksums-<version>.txt`, caches it, and runs it with full argument
passthrough. The tool itself is Python — but you do **not** need Python installed to use it this
way. Prefer `pip install ai-crucible` if you want the importable library surface.

## Research preview (v0.2.x)

ai-crucible is the measurement arm of a larger pipeline, shipped honestly pre-1.0. Its judge
panel's alt-test ω is still a **circular model-jury bootstrap** until a human-labeling round runs,
so seated judges are **provisional** and the live panel **escalates to a Claude Designer** below
quorum. The repository carries the full, non-cosmetic scorecard and the verifiable receipts.

**Source, docs, and receipts:** https://github.com/dogfood-lab/ai-crucible
