# ML Robust Eval

![ml-eval-robust-logo](./assets/ML%20Eval.png)

[![PyPI](https://img.shields.io/pypi/v/ml-eval-robust?color=blue&logo=PyPI)]()
[![License](https://img.shields.io/pypi/l/ml-eval-robust)](https://github.com/VikhyatChoppa18/ml_robust_eval/blob/main/LICENSE)

---

**ML Eval Robust** is a pure Python, object-oriented library for comprehensive machine learning model evaluation, validation, and robustness testing.  
It's an all-in-one toolkit that features:

- 📊 **Metrics** for classification, regression, NLP, and computer vision tasks  
- 🔁 **Cross-validation** and **A/B testing** helpers  
- 📈 **Visualization** tools for confusion matrices and ROC curves (stdout-based, no dependencies!)  
- 🦾 **Automated test case generation**: edge cases, adversarial samples, and boundary value tests  
- 📡 **Production Monitoring** (optional): Real-time model degradation tracking with Prometheus & Grafana
- 🧩 **Zero dependencies** (core) – works anywhere Python runs!

---

## 🚀 Installation

**Basic installation:**
```bash
pip install ml_robust_eval
```

**With production monitoring support (Prometheus/Grafana):**
```bash
pip install ml_robust_eval[monitoring]
```

---

## 🧠 Features

- **Classification, Regression, NLP, and CV Metrics**  
  - Accuracy, Precision, Recall, F1, MAE, MSE, R², BLEU, IoU, and more!
- **Cross-Validation & A/B Testing**
  - K-fold splitting, group comparison, and statistical difference calculation
- **Visualization**
  - Confusion matrices and ROC curves printed directly to your console
- **Robustness Test Case Generation**
  - Edge, boundary, and adversarial sample generation for any tabular data
- **Production Monitoring** (Optional)
  - Real-time model performance tracking with Prometheus
  - Automatic degradation detection compared to baseline
  - Pre-configured Grafana dashboards
  - Docker Compose setup for easy deployment
- **Zero Dependencies (Core)**
  - Core library uses only standard library, OOP-based, and lightweight
  - Monitoring module is optional and requires prometheus-client

---

## 📚 Documentation

- [API Reference](https://ml-robust-eval.readthedocs.io/en/latest/api_reference.html)
- [Examples & Tutorials](https://ml-robust-eval.readthedocs.io/en/latest/usage.html)
- [Production Monitoring Guide](monitoring/README.md) - Real-time model degradation tracking

---

## 💡 Why ML Eval Robust?

- **Universal:** No dependencies, works in any Python environment
- **Educational:** Clear, readable OOP code for learning and teaching
- **Robust:** Covers the full ML evaluation and validation pipeline, including adversarial and edge testing
- **Production-Ready:** Optional monitoring module for real-time model tracking in production

---

## 🤝 Contributing

All contributions, bug reports, and suggestions are welcome!  
See the [contributing guide](https://github.com/VikhyatChoppa18/ml_robust_eval/blob/main/blob/contributing.md).

---

## 📜 License

[MIT License](https://github.com/VikhyatChoppa18/ml_robust_eval/blob/main/LICENSE)

---

## 📬 Contact

Questions? Open an [issue](https://github.com/VikhyatChoppa18/ml_robust_eval/issues) or reach out at [vikhyathchoppa699@gmail.com].

---

**Let your models earn their confidence. Test, validate, and challenge them with ML Robust Eval!**
