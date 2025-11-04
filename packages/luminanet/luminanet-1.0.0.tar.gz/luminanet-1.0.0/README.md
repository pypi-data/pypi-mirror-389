# LuminaNet 🌟

**Illuminate Your AI Journey with Pure Python Deep Learning**

[![PyPI version](https://img.shields.io/pypi/v/luminanet.svg)](https://pypi.org/project/luminanet/)
[![Python Versions](https://img.shields.io/pypi/pyversions/luminanet.svg)](https://pypi.org/project/luminanet/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Termux Compatible](https://img.shields.io/badge/Termux-Compatible-brightgreen.svg)](https://termux.com/)
[![GitHub stars](https://img.shields.io/github/stars/yourusername/luminanet.svg)](https://github.com/yourusername/luminanet/stargazers)

**LuminaNet** adalah framework deep learning pure Python yang dirancang untuk edukasi dan production dengan dependencies minimal. Hanya menggunakan **NumPy, SciPy, NLTK, dan Sastrawi**.

## 🎯 **Why LuminaNet?**

| Feature | LuminaNet | Others |
|---------|-----------|--------|
| **Dependencies** | 🟢 4 libraries | 🔴 10+ libraries |
| **Termux Support** | 🟢 Perfect | 🔴 Limited |
| **Pure Python** | 🟢 100% | 🟡 Mixed |
| **Educational** | 🟢 Excellent | 🟡 Good |
| **Indonesian NLP** | 🟢 Built-in | 🔴 None |

## 🚀 **Quick Installation**

### From PyPI
```bash
pip install luminanet
```

### From Source
```bash
git clone https://github.com/yourusername/luminanet.git
cd luminanet
pip install -e .
```

### For Termux (Android)
```bash
pkg install python python-pip
pip install numpy scipy nltk sastrawi
pip install luminanet
```

## 💡 **Quick Start**

```python
from luminanet import NeuralNetwork, Dense
import numpy as np

# XOR Example
X = np.array([[0, 0], [0, 1], [1, 0], [1, 1]])
y = np.array([[1, 0], [0, 1], [0, 1], [1, 0]])

model = NeuralNetwork("XORSolver")
model.add(Dense(4, activation='relu'))
model.add(Dense(2, activation='softmax'))
model.compile(optimizer='adam', loss='categorical_crossentropy')
model.train(X, y, epochs=1000)

print(model.predict(X))
```


## 🤝 **Contributing**

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 **Author**

Your Name - [GitHub](https://github.com/yourusername) - your.email@example.com

## 🙏 **Acknowledgments**

- NumPy team untuk komputasi numerik
- NLTK team untuk NLP capabilities  
- Sastrawi team untuk Indonesian language support
- Python community untuk ecosystem yang luar biasa
