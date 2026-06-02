<p align="center">
  <a href="README.ja.md">日本語</a> | <a href="README.zh.md">中文</a> | <a href="README.es.md">Español</a> | <a href="README.fr.md">Français</a> | <a href="README.hi.md">हिन्दी</a> | <a href="README.it.md">Italiano</a> | <a href="README.md">English</a>
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

Uma ferramenta de acesso via **npx** que não exige configurações prévias para [`ai-crucible`](https://github.com/dogfood-lab/ai-crucible) —
um instrumento de medição e diagnóstico que reúne um **painel diversificado de avaliadores locais de LLM** em um
ambiente de medição isolado e avalia os resultados em comparação com um critério oculto.

```bash
npx @dogfood-lab/ai-crucible --help
npx @dogfood-lab/ai-crucible characterize --k 3   # needs a local Ollama panel
```

## Como funciona

Este pacote é um **lançador simplificado** (via [`@mcptoolshop/npm-launcher`](https://www.npmjs.com/package/@mcptoolshop/npm-launcher)):
na primeira execução, ele baixa o binário da plataforma da versão correspondente no
[GitHub Release](https://github.com/dogfood-lab/ai-crucible/releases), verifica o seu **SHA-256**
em relação ao arquivo `checksums-<version>.txt` da versão, armazena em cache e o executa com todos os argumentos. A ferramenta em si é em Python, mas você **não** precisa ter o Python instalado para usá-la desta forma. Se você quiser a biblioteca que pode ser importada, use `pip install ai-crucible`.

## Prévia de pesquisa (v0.2.x)

ai-crucible é o componente de medição de um pipeline maior, lançado de forma transparente antes da versão 1.0. O teste alternativo ω do painel de avaliadores ainda é um **modelo circular de avaliação**, até que seja realizada uma rodada de rotulagem humana,
de modo que os avaliadores presentes são **provisórios** e o painel ativo **evolui para um Claude Designer** abaixo do quórum. O repositório contém a pontuação completa e não cosmética e os comprovantes verificáveis.

**Código-fonte, documentação e comprovantes:** https://github.com/dogfood-lab/ai-crucible
