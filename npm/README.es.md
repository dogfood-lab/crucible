<p align="center">
  <a href="README.ja.md">日本語</a> | <a href="README.zh.md">中文</a> | <a href="README.md">English</a> | <a href="README.fr.md">Français</a> | <a href="README.hi.md">हिन्दी</a> | <a href="README.it.md">Italiano</a> | <a href="README.pt-BR.md">Português (BR)</a>
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

Una forma sencilla de acceder a [`ai-crucible`](https://github.com/dogfood-lab/ai-crucible) mediante **npx**, sin necesidad de requisitos previos.
Es un instrumento de medición diagnóstica que reúne a un **panel diverso de evaluadores locales de LLM** dentro de un entorno de medición aislado y evalúa los resultados en comparación con un oráculo oculto.

```bash
npx @dogfood-lab/ai-crucible --help
npx @dogfood-lab/ai-crucible characterize --k 3   # needs a local Ollama panel
```

## Cómo funciona

Este paquete es un **lanzador ligero** (a través de [`@mcptoolshop/npm-launcher`](https://www.npmjs.com/package/@mcptoolshop/npm-launcher)): en la primera ejecución, descarga el binario de la plataforma desde la versión correspondiente en [GitHub Release](https://github.com/dogfood-lab/ai-crucible/releases), verifica su **SHA-256** con el archivo `checksums-<version>.txt` de la versión, lo almacena en caché y lo ejecuta con todos los argumentos. La herramienta en sí está escrita en Python, pero **no** es necesario tener Python instalado para usarla de esta manera. Si desea utilizar la biblioteca como módulo, prefiera `pip install ai-crucible`.

## Versión preliminar para investigación (v0.2.x)

ai-crucible es el componente de medición de un flujo de trabajo más amplio, que se ofrece de forma transparente antes de la versión 1.0. La prueba alternativa ω del panel de evaluadores aún es un **modelo de jurado circular** hasta que se realice una ronda de etiquetado humano, por lo que los evaluadores son **provisionales** y el panel activo **se amplía a un Claude Designer** cuando no se alcanza el quórum. El repositorio contiene la puntuación completa y los comprobantes verificables.

**Código fuente, documentación y comprobantes:** https://github.com/dogfood-lab/ai-crucible
