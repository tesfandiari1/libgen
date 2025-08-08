# Simple, lightweight Dockerfile for LangGraph Agents
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY examples/ ./examples/

# Create a simple entrypoint script that keeps the container running
RUN echo '#!/bin/bash\n\
echo "LangGraph Agent Container Ready"\n\
echo "==============================="\n\
echo ""\n\
echo "You can run examples with:"\n\
echo "  docker compose exec agent python examples/quickstart.py"\n\
echo "  docker compose exec agent python examples/with_memory.py"\n\
echo ""\n\
echo "Or interact with Python:"\n\
echo "  docker compose exec agent python"\n\
echo ""\n\
# Keep container running\n\
tail -f /dev/null' > /entrypoint.sh && \
    chmod +x /entrypoint.sh

# Default command - keep container running
CMD ["/entrypoint.sh"]