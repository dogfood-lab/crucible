<p align="center">
  <a href="README.ja.md">日本語</a> | <a href="README.zh.md">中文</a> | <a href="README.es.md">Español</a> | <a href="README.fr.md">Français</a> | <a href="README.hi.md">हिन्दी</a> | <a href="README.md">English</a> | <a href="README.pt-BR.md">Português (BR)</a>
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

Un punto di accesso **npx** che non richiede prerequisiti per [`ai-crucible`](https://github.com/dogfood-lab/ai-crucible) —
uno strumento di misurazione diagnostica che riunisce un **gruppo eterogeneo di valutatori locali di LLM** all'interno di
un ambiente di misurazione isolato e valuta i tentativi rispetto a un oracolo nascosto.

```bash
npx @dogfood-lab/ai-crucible --help
npx @dogfood-lab/ai-crucible characterize --k 3   # needs a local Ollama panel
```

## Come funziona

Questo pacchetto è un **launcher leggero** (tramite [`@mcptoolshop/npm-launcher`](https://www.npmjs.com/package/@mcptoolshop/npm-launcher)):
alla prima esecuzione, scarica il binario della piattaforma dalla corrispondente
[versione su GitHub](https://github.com/dogfood-lab/ai-crucible/releases), ne verifica l'**SHA-256**
confrontandolo con il file `checksums-<versione>.txt` della versione, lo memorizza nella cache e lo esegue passando tutti gli argomenti. Lo strumento stesso è scritto in Python, ma non è necessario avere Python installato per utilizzarlo in questo modo. Se si desidera utilizzare la libreria importabile, è preferibile utilizzare `pip install ai-crucible`.

## Anteprima di ricerca (v0.2.x)

ai-crucible è la parte di misurazione di una pipeline più ampia, fornita in versione pre-1.0. Il test alternativo ω del gruppo di valutatori è ancora un **modello di bootstrap circolare** fino a quando non viene eseguito un ciclo di etichettatura umana, quindi i valutatori sono **provvisori** e il gruppo attivo **si amplia fino a includere un Claude Designer** quando non si raggiunge il quorum. Il repository contiene il punteggio completo e non modificato e le ricevute verificabili.

**Codice sorgente, documentazione e ricevute:** https://github.com/dogfood-lab/ai-crucible
