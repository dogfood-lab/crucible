<p align="center">
  <a href="README.ja.md">日本語</a> | <a href="README.md">English</a> | <a href="README.es.md">Español</a> | <a href="README.fr.md">Français</a> | <a href="README.hi.md">हिन्दी</a> | <a href="README.it.md">Italiano</a> | <a href="README.pt-BR.md">Português (BR)</a>
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

一个无需任何先决条件的 **npx** 前端，用于访问 [`ai-crucible`](https://github.com/dogfood-lab/ai-crucible)——
这是一种诊断测量工具，它将一个**由不同模型的本地 LLM 评委组成的评审团**置于一个封闭的测量边界内，并根据隐藏的参考标准对尝试进行评分。

```bash
npx @dogfood-lab/ai-crucible --help
npx @dogfood-lab/ai-crucible characterize --k 3   # needs a local Ollama panel
```

## 工作原理

此软件包是一个**轻量级启动器**（通过 [`@mcptoolshop/npm-launcher`](https://www.npmjs.com/package/@mcptoolshop/npm-launcher)）：
首次运行时，它会从匹配的 [GitHub 发布](https://github.com/dogfood-lab/ai-crucible/releases) 下载平台二进制文件，并将其 **SHA-256** 值与发布的 `checksums-<version>.txt` 文件进行验证，然后将其缓存，并以完全传递参数的方式运行。该工具本身是 Python 编写的——但您**不需要**安装 Python 即可以这种方式使用它。如果您需要可导入的库，请使用 `pip install ai-crucible`。

## 研究预览版 (v0.2.x)

ai-crucible 是一个更大流水线中的测量模块，在 1.0 版本之前发布。其评审团的替代测试 ω 仍然是一个**循环模型评审引导**，直到进行一轮人工标注，因此，评审团成员是**暂定的**，并且当评审团人数不足时，**评审团会升级到 Claude Designer**。该仓库包含完整的、非装饰性的评分表和可验证的记录。

**源代码、文档和记录：**https://github.com/dogfood-lab/ai-crucible
