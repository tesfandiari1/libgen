# LangGraph Agents

A simple, lightweight implementation of LangGraph agents with memory and tools support.

## Prerequisites

- Docker and Docker Compose
- Anthropic API key

## Setup

1. **Create `.env` file** with your Anthropic API key:
```bash
echo "ANTHROPIC_API_KEY=your_api_key_here" > .env
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

- **Container won't start**: Check `.env` file exists with valid API key
- **Import errors**: Ensure you're running code inside the container
- **API errors**: Verify your Anthropic API key is valid and has credits

## License

MIT