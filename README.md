# Library Repository

## 📦 Main Project

The main project is located in the `langgraph-agents/` directory.

See `langgraph-agents/README.md` for detailed documentation.

## 🚀 Quick Start (Docker Compose)

```bash
cd langgraph-agents
cp .env.example .env   # Fill ANTHROPIC_API_KEY
docker compose up -d --build

# Run an example
docker compose exec agent python examples/quickstart.py
```

## 📁 Repository Structure

```
library/
├── langgraph-agents/      # Main LangGraph agents project
│   ├── src/               # Source code
│   ├── examples/          # Example scripts
│   ├── tests/             # Tests
│   ├── pyproject.toml     # Project configuration
│   └── README.md          # Detailed documentation
└── README.md              # This file
```
