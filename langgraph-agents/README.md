# LangGraph Agents

A simple, lightweight implementation of LangGraph agents with memory and tools support.

## Prerequisites

- Docker and Docker Compose
- Anthropic API key

## Setup

1. **Create `.env` file**. You can start from the example and set your Anthropic API key:
```bash
cp .env.example .env
echo "ANTHROPIC_API_KEY=your_api_key_here" >> .env
```

2. **Build and start the container**:
```bash
docker compose up -d --build
```

## Usage

### Running Examples

```bash
# Run the quickstart example
docker compose exec agent python examples/quickstart.py

# Run memory agent example
docker compose exec agent python examples/with_memory.py

# Run structured output example
docker compose exec agent python examples/structured_output.py
```

### Anna's Archive: CLI Search Workflow

The CLI is exposed as `anna-agent`.

```bash
# Search and save results to SQLite
docker compose exec agent anna-agent search "Python programming" --limit 25

# List saved books (most recent first)
docker compose exec agent anna-agent list --limit 20

# Export all saved books to CSV
docker compose exec agent anna-agent export /app/data/books.csv
```

You can also run the LangGraph-powered agent to parse intent, search, rank, and optionally save:

```bash
docker compose exec agent anna-agent agent "Find Python programming books 2020+ pdf" --save
```

### CLI Commands

```text
anna-agent search "<query>" [--limit|-n <int>]   # Search Anna's Archive and persist results
anna-agent list [--limit|-n <int>]                # List saved books
anna-agent export <path.csv>                      # Export saved books to CSV
anna-agent agent "<query>" [--save]              # Run the discovery agent
```

### Interactive Development

```bash
# Open Python REPL
docker compose exec agent python

# Open bash shell
docker compose exec agent /bin/bash
```

### Container Management

```bash
# View logs
docker compose logs -f

# Check status
docker compose ps

# Stop container
docker compose down

# Rebuild image
docker compose build

# Restart container
docker compose restart
```

### Using Makefile (Optional)

For convenience, you can also use the Makefile:

```bash
make up      # Start container
make run     # Run quickstart example
make python  # Open Python REPL
make shell   # Open bash shell
make logs    # View logs
make down    # Stop container
```

### Integration Test (End-to-End)

```bash
# Run the end-to-end integration test inside the container
docker compose exec agent python -m tests.integration_test
```

## Project Structure

```
langgraph-agents/
├── src/
│   ├── agents/        # Agent implementations
│   ├── tools/         # Custom tools
│   └── utils/         # Configuration and utilities
├── examples/          # Example scripts
├── requirements.txt   # Python dependencies
├── Dockerfile        # Simple container definition
└── docker-compose.yml # Docker Compose configuration

## Environment Variables

Only the following variables are required/optional:

- `ANTHROPIC_API_KEY` (required) — Anthropic API key for Claude models
- `INTEGRATION_EXPORT_PATH` (optional) — CSV export path for the integration test (default: `/app/data/integration_export.csv`)

Precedence: `.env.local > .env`.
```

## Examples

### Basic Agent
```python
from src.agents.basic_agent import create_basic_agent

agent = create_basic_agent()
response = agent.invoke(
    {"messages": [{"role": "user", "content": "What's the weather in Tokyo?"}]}
)
print(response['messages'][-1].content)
```

### Memory Agent
```python
from src.agents.memory_agent import create_memory_agent

agent = create_memory_agent()
config = {"configurable": {"thread_id": "session_1"}}

# First message
response = agent.invoke(
    {"messages": [{"role": "user", "content": "Remember my name is Alice"}]},
    config
)

# Second message (remembers context)
response = agent.invoke(
    {"messages": [{"role": "user", "content": "What's my name?"}]},
    config
)
```

## Troubleshooting

- **Container won't start**: Ensure `.env` exists (you can copy from `.env.example`).
- **Import errors**: Run commands inside the container with `docker compose exec agent ...`.
- **No results / HTTP errors**: Anna's Archive may throttle. The scraper respects a 1 req/sec pace. Retry later.
- **Database location**: SQLite file is at `/app/data/books.db` (mounted from `./data`). Ensure the `data/` folder exists.
- **CSV export path**: Use a path under `/app/data/` to persist on host (e.g., `/app/data/books.csv`).

## License

MIT

## Streamlit UI

You can use a simple Streamlit app to interact with the LangGraph book discovery agent.

Start the UI service:

```bash
docker compose up -d --build ui
```

Open `http://localhost:8501` in your browser. Enter queries like:

```
Python programming 2020+ pdf
```

The UI calls the same graph as `examples/book_search.py` under the hood.
