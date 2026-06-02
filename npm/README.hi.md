<p align="center">
  <a href="README.ja.md">日本語</a> | <a href="README.zh.md">中文</a> | <a href="README.es.md">Español</a> | <a href="README.fr.md">Français</a> | <a href="README.md">English</a> | <a href="README.it.md">Italiano</a> | <a href="README.pt-BR.md">Português (BR)</a>
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

शून्य पूर्व-आवश्यकताओं वाला **npx** फ्रंट-एंड, जो [`ai-crucible`](https://github.com/dogfood-lab/ai-crucible) तक पहुंच प्रदान करता है —
यह एक नैदानिक माप उपकरण है जो **स्थानीय एलएलएम न्यायाधीशों के एक क्रॉस-परिवार पैनल** को एक
सीमित माप सीमा के भीतर बैठाता है और एक छिपे हुए ओरेकल के विरुद्ध प्रयासों का मूल्यांकन करता है।

```bash
npx @dogfood-lab/ai-crucible --help
npx @dogfood-lab/ai-crucible characterize --k 3   # needs a local Ollama panel
```

## यह कैसे काम करता है

यह पैकेज एक **सरल लॉन्चर** है ([`@mcptoolshop/npm-launcher`](https://www.npmjs.com/package/@mcptoolshop/npm-launcher) के माध्यम से):
पहली बार चलाने पर, यह संबंधित [गिटहब रिलीज़](https://github.com/dogfood-lab/ai-crucible/releases) से प्लेटफ़ॉर्म बाइनरी डाउनलोड करता है, इसकी **SHA-256** को रिलीज़ के `checksums-<version>.txt` से सत्यापित करता है, इसे कैश करता है, और सभी तर्कों के साथ चलाता है। उपकरण स्वयं पायथन में है — लेकिन इसे इस तरह उपयोग करने के लिए आपको पायथन स्थापित करने की आवश्यकता **नहीं** है। यदि आप आयात करने योग्य लाइब्रेरी चाहते हैं, तो `pip install ai-crucible` का उपयोग करें।

## अनुसंधान पूर्वावलोकन (v0.2.x)

ai-crucible एक बड़े पाइपलाइन का माप भाग है, जिसे 1.0 से पहले ईमानदारी से जारी किया गया है। इसके न्यायाधीश पैनल का वैकल्पिक परीक्षण ω अभी भी एक **चक्रीय मॉडल-जूरी बूटस्ट्रैप** है, जब तक कि मानव-लेबलिंग दौर नहीं चलता, इसलिए बैठे हुए न्यायाधीश **अस्थायी** हैं और लाइव पैनल **न्यूनतम संख्या से नीचे एक क्लाउड डिज़ाइनर** तक विस्तारित होता है। रिपॉजिटरी में पूर्ण, गैर-सौंदर्य स्कोरकार्ड और सत्यापित रसीदें शामिल हैं।

**स्रोत, दस्तावेज़ और रसीदें:** https://github.com/dogfood-lab/ai-crucible
