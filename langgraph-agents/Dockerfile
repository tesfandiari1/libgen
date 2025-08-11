# Simple, lightweight Dockerfile for LangGraph Agents
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Set working directory
WORKDIR /app

# Copy project metadata and application code first (lock includes -e .)
COPY pyproject.toml ./
COPY README.md ./
COPY src/ ./src/
COPY examples/ ./examples/
COPY requirements.txt ./
COPY ui/ ./ui/

## Install pinned dependencies from lockfile (includes editable install)
COPY requirements.lock ./
RUN pip install --no-cache-dir -r requirements.lock && \
    pip install --no-cache-dir -r requirements.txt

# Create a simple entrypoint script that keeps the container running
RUN echo '#!/bin/bash\n\
echo "LangGraph Agent Container Ready"\n\
echo "==============================="\n\
echo ""\n\
echo "You can run examples with:"\n\
echo "  docker compose exec agent python examples/quickstart.py"\n\
echo "  docker compose exec agent python examples/with_memory.py"\n\
echo ""\n\
echo "CLI available (\"anna-agent\"):"\n\
echo "  docker compose run --rm agent anna-agent search \"machine learning 2023\""\n\
echo "  docker compose exec agent anna-agent list --limit 20"\n\
echo "  docker compose exec agent anna-agent export /app/data/books.csv"\n\
echo "(Database at /app/data/books.db)"\n\
echo ""\n\
tail -f /dev/null' > /entrypoint.sh && chmod +x /entrypoint.sh

# Default command - keep container running
CMD ["/entrypoint.sh"]
