## Repository Fix Report — LangGraph Agents

Purpose: Homogenize configuration, dependencies, and tooling; fix security hygiene; and establish reproducible builds and minimal CI — without changing runtime behavior or developer workflows centered on Docker Compose.

Security note: A real Anthropic API key is currently present in `langgraph-agents/.env`. Rotate this key immediately at the provider, then proceed with Task 1 to remove the file from version control and rely on `.env.example`.


### Task 1 — Secrets and .env hygiene (Immediate)

DO NOT:
- ❌ Commit any `.env`, `.env.local`, or secrets to version control
- ❌ Rewrite Git history in this step
- ❌ Install any packages

MODIFY EXACTLY 2 FILES:
- `langgraph-agents/.gitignore`
- `langgraph-agents/.env.example`

CREATE EXACTLY 0 FILES:

REQUIREMENTS:
- Ensure `langgraph-agents/.gitignore` ignores `.env`, `.env.*`, and local overrides.
- Trim `langgraph-agents/.env.example` to only required variables actually used by code: `ANTHROPIC_API_KEY` and optional `INTEGRATION_EXPORT_PATH` (used in `tests/integration_test.py`). Remove unused items (Redis, API_HOST/PORT, Jupyter, Docker limits) to avoid sprawl.
- Remove tracked `.env` from Git without deleting local file: `git rm --cached langgraph-agents/.env`.
- Document precedence in README later: `.env.local > .env`.

VALIDATION:
- `git ls-files langgraph-agents/.env` returns nothing
- `grep -R "REDIS_HOST\|API_HOST\|JUPYTER_PORT" langgraph-agents/src || true` shows no code references
- `.env.example` contains only required and optional documented vars

STOP.


### Task 2 — Env consistency in code

DO NOT:
- ❌ Add new environment variables
- ❌ Change public CLI/API behavior
- ❌ Install any packages

MODIFY EXACTLY 1 FILE:
- `langgraph-agents/src/utils/config.py`

CREATE EXACTLY 0 FILES:

REQUIREMENTS:
- Keep `Config` minimal and consistent with `.env.example`:
  - `ANTHROPIC_API_KEY` required (warn if missing, do not raise)
  - Optional `INTEGRATION_EXPORT_PATH` with default `/app/data/integration_export.csv` (read with `os.getenv`)
- Do not introduce Redis or server envs; do not change defaults used elsewhere.

VALIDATION:
- `ripgrep -n "os.getenv\(" langgraph-agents/src` shows only the above keys are read from env in `config.py` (or callsites)
- Running examples and tests still works with only `ANTHROPIC_API_KEY` set

STOP.


### Task 3 — Dependency unification and reproducible builds

DO NOT:
- ❌ Leave runtime dependencies split across `pyproject.toml` and `requirements.txt`
- ❌ Change Python version (keep 3.11)
- ❌ Install any packages (tooling usage must rely on what’s already available)

MODIFY EXACTLY 2 FILES:
- `langgraph-agents/pyproject.toml`
- `langgraph-agents/Dockerfile`

CREATE EXACTLY 1 FILE:
- `langgraph-agents/requirements.lock`

REQUIREMENTS:
- Move/ensure all runtime deps live in `[project.dependencies]` in `pyproject.toml`. Include items currently only in `requirements.txt`: `httpx`, `selectolax`, `beautifulsoup4`, `lxml`, `tenacity`, `aiofiles`.
- Generate a pinned lock file `requirements.lock` from `pyproject.toml` (e.g., `uv export -o requirements.lock` or `pip-compile` if already available). Do NOT add new tools to the project.
- Update `Dockerfile` to install from the lock file: `COPY requirements.lock ./` then `pip install --no-cache-dir -r requirements.lock`.
- Keep editable install `pip install -e .` to expose the `anna-agent` console script.
- Retain Docker Compose as-is.

VALIDATION:
- `docker compose build` succeeds offline with only the lock file (network may still be required for first build on a clean machine)
- `pip check` inside the container reports no conflicts

STOP.


### Task 4 — Lint, format, type-check, and Make targets

DO NOT:
- ❌ Introduce conflicting formatters/linters
- ❌ Enforce changes on legacy code beyond formatter/linter defaults
- ❌ Install any packages

MODIFY EXACTLY 2 FILES:
- `langgraph-agents/pyproject.toml` (add tool configs)
- `langgraph-agents/Makefile` (add new targets; keep existing ones)

CREATE EXACTLY 3 FILES:
- `langgraph-agents/.editorconfig`
- `langgraph-agents/.gitattributes`
- `langgraph-agents/.pre-commit-config.yaml`

REQUIREMENTS:
- Configure Ruff (lint + format) and mypy in `pyproject.toml` with permissive baseline (strict on new code sections later). Sample:
  - Ruff: enable formatter, basic rules; exclude `data/`, `.venv/`.
  - Mypy: Python 3.11, ignore-missing-imports initially.
- Add Make targets: `fmt` (ruff format), `lint` (ruff check), `type` (mypy), `test` (pytest), and keep `up|down|build|run|shell|python|logs|status|restart`.
- Pre-commit config: ruff, ruff-format, mypy (as optional local hook), end-of-file-fixer, trailing-whitespace, detect-private-key.

VALIDATION:
- `make fmt && make lint && make type && make test` runs locally and in container
- Pre-commit runs successfully on staged files

STOP.


### Task 5 — Minimal CI (GitHub Actions)

DO NOT:
- ❌ Add long-running or matrix builds
- ❌ Install any packages beyond the project dependencies
- ❌ Run on documentation-only changes

MODIFY EXACTLY 0 FILES:

CREATE EXACTLY 1 FILE:
- `.github/workflows/ci.yml`

REQUIREMENTS:
- Single job on Ubuntu, Python 3.11: cache, install from `requirements.lock`, then run `make lint`, `make type`, `make test`.
- Skip workflow on paths limited to docs-only changes.
- Target runtime under 5 minutes.

VALIDATION:
- CI returns green on main branch and PRs

STOP.


### Task 6 — Documentation and repo metadata

DO NOT:
- ❌ Reference non-existent scripts (e.g., `setup.sh`)
- ❌ Change the Docker Compose-based workflow
- ❌ Install any packages

MODIFY EXACTLY 2 FILES:
- `README.md` (root)
- `langgraph-agents/README.md`

CREATE EXACTLY 2 FILES:
- `CONTRIBUTING.md`
- `LICENSE` (MIT, matching README statement)

REQUIREMENTS:
- Root README: remove references to `setup.sh`/`setup.bat`; provide quick start using Docker Compose; summarize repo layout; link to package README.
- Package README: tighten quickstart, document `.env` variables (only the trimmed set), show one-command DX via Make, include integration test invocation.
- CONTRIBUTING: commit style, branching, pre-commit, PR checks.
- LICENSE: MIT.

VALIDATION:
- Commands in READMEs copy-paste and work as written
- No dead links or missing files

STOP.


### Task 7 — Minor code cleanup (non-breaking)

DO NOT:
- ❌ Remove or rename public CLI entrypoints or agent APIs
- ❌ Delete files without archival
- ❌ Install any packages

MODIFY EXACTLY 0 FILES:

CREATE EXACTLY 0 FILES:

REQUIREMENTS:
- Archive unused placeholders instead of deleting: move `langgraph-agents/src/cli/init.py` to `langgraph-agents/archive/<YYYYMMDD>/src/cli/init.py` using `git mv`.
- Verify no imports reference the archived file.

VALIDATION:
- `ripgrep -n "from src\.cli\.init|import .*cli\.init" langgraph-agents/src || true` returns no matches
- App and tests still run

STOP.


## Execution Checklist (to follow in order)

1) Secrets and .env hygiene
- Rotate Anthropic key at provider
- Ensure `.gitignore` entries for `.env*`
- Trim `.env.example` to minimal set
- `git rm --cached langgraph-agents/.env`

2) Env consistency in code
- Update `src/utils/config.py` to only read documented keys
- Sanity run: examples + tests

3) Dependency unification
- Add missing deps to `pyproject.toml`
- Generate `requirements.lock`
- Update Dockerfile to install from lock
- `docker compose build`

4) Tooling
- Add `.editorconfig`, `.gitattributes`, `.pre-commit-config.yaml`
- Add Make targets: fmt|lint|type|test
- Configure Ruff + mypy in `pyproject.toml`

5) CI
- Add `.github/workflows/ci.yml`
- Ensure it skips docs-only changes

6) Docs & metadata
- Update root and package READMEs
- Add `CONTRIBUTING.md` and `LICENSE`

7) Cleanup
- Archive `src/cli/init.py` if unused
- Final run: `make fmt && make lint && make type && make test`


## Validation Gates (must be green before merge)
- Docker build succeeds from a clean checkout
- `make` targets work locally and inside container
- CI passes under 5 minutes
- No secrets tracked; `.env` is ignored
- Examples and tests run with `.env` containing only `ANTHROPIC_API_KEY`


