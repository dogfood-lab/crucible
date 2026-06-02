<p align="center">
  <a href="README.ja.md">日本語</a> | <a href="README.zh.md">中文</a> | <a href="README.es.md">Español</a> | <a href="README.md">English</a> | <a href="README.hi.md">हिन्दी</a> | <a href="README.it.md">Italiano</a> | <a href="README.pt-BR.md">Português (BR)</a>
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

Accès direct via **npx** (sans prérequis) à [`ai-crucible`](https://github.com/dogfood-lab/ai-crucible) —
un instrument de mesure diagnostique qui réunit un **panel de juges locaux issus de différentes familles de LLM** dans un
environnement de mesure isolé et évalue les tentatives par rapport à un oracle caché.

```bash
npx @dogfood-lab/ai-crucible --help
npx @dogfood-lab/ai-crucible characterize --k 3   # needs a local Ollama panel
```

## Fonctionnement

Ce paquet est un **lanceur léger** (via [`@mcptoolshop/npm-launcher`](https://www.npmjs.com/package/@mcptoolshop/npm-launcher)) :
lors de la première exécution, il télécharge le binaire de la plateforme à partir de la version correspondante sur
[GitHub Release](https://github.com/dogfood-lab/ai-crucible/releases), vérifie son **SHA-256**
par rapport au fichier `checksums-<version>.txt` de la version, le met en cache et l’exécute avec tous les arguments. L’outil lui-même est en Python, mais vous n’avez **pas** besoin d’avoir Python installé pour l’utiliser de cette manière. Préférez `pip install ai-crucible` si vous souhaitez utiliser la bibliothèque importable.

## Version préliminaire pour la recherche (v0.2.x)

ai-crucible est la partie de mesure d’un pipeline plus vaste, distribué en version préliminaire avant la 1.0. Le test alternatif ω du panel de juges est encore un **modèle de bootstrap circulaire** jusqu’à ce qu’une phase d’étiquetage humain soit effectuée, de sorte que les juges présents sont **provisoires** et que le panel actif **passe à un Claude Designer** lorsque le quorum n’est pas atteint. Le dépôt contient le tableau de bord complet, sans éléments cosmétiques, et les reçus vérifiables.

**Code source, documentation et reçus :** https://github.com/dogfood-lab/ai-crucible
