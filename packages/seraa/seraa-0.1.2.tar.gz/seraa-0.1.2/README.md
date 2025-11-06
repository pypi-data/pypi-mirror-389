# SERAA: Stochastic Emergent Reasoning Alignment Architecture

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![build](https://github.com/tpark216/seraa/actions/workflows/pytest.yml/badge.svg)](https://github.com/tpark216/seraa/actions)

A Python framework for evaluating and preserving **human agency** and ethical boundaries in AI, policy, and organizational decision-making.  
_Rooted in philosophy, built for Responsible AI, validated on real-world scenarios._

---

## 🚀 Quick Install

pip install seraa

## 📖 Quick Start

ollama pull qwen2.5:1.5b

## Start interactive chat
seraa-chat --framework buddhist --model qwen2.5:1.5b

from seraa.llm import SeraaChat

## Initialize with Buddhist ethics
chat = SeraaChat(
llm_backend="ollama",
model="qwen2.5:1.5b",
ethical_framework="buddhist"
)

## Evaluate a scenario
result = chat.chat("Is it ethical to use user data without consent?")
print(result['chat_response'])

Create an ethical AI agent
agent = SeraaAgent(
name="my_agent",
moral_weights={'fairness': 0.4, 'autonomy': 0.3, 'care': 0.3},
core_values={'human_dignity': 1.0}
)

Add constraints
agent.add_constraint(
EthicalConstraint("pac_check", lambda a: a.get('pac_score', 0) >= 0.7)
)

Evaluate an action
result = agent.evaluate_action({'pac_score': 0.9})
print(result.approved) # True or False

## 📚 What is SERAA?

- **9 Ethical Axioms** derived from meta-ethics, philosophy of agency, and digital ethics
- **Ternary Logic** moves beyond binary right/wrong: positive, neutral, negative
- **PAC (Preservation of Agentic Capacity):** Empowers, doesn’t just prohibit
- **Configurable:** Tweak weights, constraints, and axioms for any domain or philosophy

### **Applications**
- AI/algorithmic decision audits
- Policy and governance review (presidential, corporate, etc.)
- Autonomous agent frameworks (vehicles, bots)
- Academic research in digital ethics

---

## ✨ Features

- **9 Ethical Axioms**: Comprehensive philosophical foundation
- **PAC Preservation**: Maintains human agentic capacity
- **Ternary Logic**: Beyond binary ethical judgments
- **Real-World Tested**: Evaluated on 35+ major decisions
- **Zero Dependencies**: Pure Python implementation

## 🎮 Command-Line Evaluation (Planned)

seraa-evaluate --event "A national executive order banning all travel from country X"

_(Coming soon: pip install includes CLI)_

---

## 📊 Visualizations

Generate analysis of real-world decisions:

pip install seraa[viz]
python -m examples.visualize_results

_Output: Publication- and social-ready graphs in `/visualizations`_

---

## 🛡 Design Philosophy

SERAA is designed for:
- **Transparency**: Every output is explainable, every threshold documented
- **Research-Grade Rigor**: All tests pass, coverage is high, edge cases considered
- **Ethical Nuance**: Not just “is it legal,” but “does it preserve real moral agency?”

---

## 🧪 Running the Tests

pip install -r requirements-dev.txt
pytest

---
## 📚 Documentation

Full documentation: https://seraa.readthedocs.io (coming soon)

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to help improve SERAA, open issues, or suggest new events for evaluation!

---

## 📄 License

MIT License - See LICENSE file

## 📚 Citation

@phdthesis{seraa2025,
author = {Theodore Park},
title = {SERAA: Stochastic Emergent Reasoning Alignment Architecture},
school = {University of Aberdeen},
year = {2025}
}

## 📬 Questions, Feedback & Community

- [GitHub Discussions](https://github.com/tpark216/seraa/discussions)
- Bluesky: [@yyeolpark.bsky.social](https://bsky.app/profile/byeolpark.bsky.social)
- Email: theodore.jb.park@gmail.com