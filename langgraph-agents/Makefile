.PHONY: help up down build run shell python logs status clean

# Default target
help:
	@echo "LangGraph Agents - Docker Commands"
	@echo ""
	@echo "Available commands:"
	@echo "  make up       - Start the agent container"
	@echo "  make down     - Stop and remove container"
	@echo "  make build    - Build Docker image"
	@echo "  make run      - Run the quickstart example"
	@echo "  make shell    - Open bash shell in container"
	@echo "  make python   - Open Python REPL in container"
	@echo "  make logs     - Show container logs"
	@echo "  make status   - Show container status"
	@echo "  make clean    - Stop containers and remove image"

# Docker commands
up:
	docker compose up -d --build

down:
	docker compose down

build:
	docker compose build

run:
	docker compose exec agent python examples/quickstart.py

shell:
	docker compose exec agent /bin/bash

python:
	docker compose exec agent python

logs:
	docker compose logs -f

status:
	docker compose ps

clean:
	docker compose down
	docker rmi langgraph-agents-agent 2>/dev/null || true

# Quick restart
restart: down up