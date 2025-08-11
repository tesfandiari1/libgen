# Contributing

## Workflow
- Branch from main
- Small, atomic commits
- Open PRs by category (structure, deps, tooling, docs)

## Quality
- Use Docker Compose for runtime
- Run locally:
  - `make fmt`
  - `make lint`
  - `make type`
  - `make test`

## Pre-commit
- Install pre-commit (optional) and run `pre-commit install`
- Hooks: ruff, ruff-format, EOF fixer, trailing whitespace, detect private keys

## CI
- CI runs lint, format-check, type-check, tests on Python 3.11

## Secrets
- Do not commit `.env` or secrets
- Use `.env.example` for documentation only

