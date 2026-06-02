<p align="center">
  <a href="README.md">English</a> | <a href="README.zh.md">中文</a> | <a href="README.es.md">Español</a> | <a href="README.fr.md">Français</a> | <a href="README.hi.md">हिन्दी</a> | <a href="README.it.md">Italiano</a> | <a href="README.pt-BR.md">Português (BR)</a>
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

[`ai-crucible`](https://github.com/dogfood-lab/ai-crucible) への、前提条件なしの **npx** を使用した簡単なアクセス方法 —
これは、**異なるモデル群から選ばれたローカルLLMの審査員**を、
密閉された測定境界内で配置し、隠された基準に対して試行を評価する診断測定ツールです。

```bash
npx @dogfood-lab/ai-crucible --help
npx @dogfood-lab/ai-crucible characterize --k 3   # needs a local Ollama panel
```

## 仕組み

このパッケージは、**軽量ランチャー**（[`@mcptoolshop/npm-launcher`](https://www.npmjs.com/package/@mcptoolshop/npm-launcher) を介して）です。
初回実行時に、対応する [GitHub リリース](https://github.com/dogfood-lab/ai-crucible/releases) からプラットフォームバイナリをダウンロードし、その **SHA-256** をリリースの `checksums-<version>.txt` と照合して検証し、キャッシュし、すべての引数をそのまま渡して実行します。このツール自体は Python で記述されていますが、この方法で使用するには Python をインストールする必要はありません。インポート可能なライブラリが必要な場合は、`pip install ai-crucible` を使用してください。

## リサーチプレビュー（v0.2.x）

ai-crucible は、より大規模なパイプラインの一部であり、1.0 より前に正直に公開されています。その審査員パネルの代替テスト ω は、人間のラベル付けラウンドが実行されるまでは、**循環モデルによる審査員グループのブートストラップ**であり、そのため、配置された審査員は**一時的**であり、必要な人数に達するまで、審査員パネルは**Claude Designer** に切り替わります。リポジトリには、完全な、装飾のないスコアカードと検証可能な記録が含まれています。

**ソースコード、ドキュメント、および記録:** https://github.com/dogfood-lab/ai-crucible
