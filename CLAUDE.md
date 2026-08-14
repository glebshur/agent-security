# CLAUDE.md

Guidance for Claude Code when working in this repository.

## Repository overview

Two independent parts live here:

1. **`docker/`** — a hardened, sysbox-isolated dev-container stack for running AI
   coding agents. A Docker Compose project (`agent-security`) of three containers
   across three networks; the agent runs unprivileged with no direct internet
   route, all egress forced through a Squid allowlist proxy. Fully documented in
   the top-level `README.md`.
2. **`calculator/`** — a small Python console calculator (`+`, `-`, parentheses)
   built as a classic OOP interpreter (tokenizer → parser → evaluator). This is
   the actual application code you'll usually be editing.

## calculator/ — the Python app

All commands run from the `calculator/` directory. The project uses
[uv](https://docs.astral.sh/uv/) for Python version, venv, and dependencies.

```bash
uv sync                 # create .venv, install package (editable) + pytest
uv run pytest           # run the full test suite
uv run calculator       # interactive REPL
uv run calculator "(1 + 2) - -3"   # one-shot; prints 6, non-zero exit on bad input
```

The dev toolchain (`ruff`, `black`, `mypy`) is available on `/opt/venv` inside
the dev container.

## docker/ — isolation stack

Only touch this when explicitly working on the container config. Key files:
`docker/docker-compose.yml`, `docker/Dockerfile`, `docker/squid/squid.conf`,
`docker/squid/allowlist.txt`. Common operations (run from `docker/`):

## Commit conventions

Follow [Conventional Commits](https://www.conventionalcommits.org/): a
`<type>: <summary>` subject in the imperative mood, kept under ~72 characters.

Types used in this repo:

- `feat:` — a new feature or capability
- `docs:` — documentation-only changes (README, this file, comments)
- `fix:` — a bug fix
- `refactor:` — code change that neither fixes a bug nor adds a feature
- `test:` — adding or adjusting tests
- `chore:` — tooling, config, or housekeeping

Scope the change to one logical concern per commit. Branch names mirror the
commit type: `feat/…`, `docs/…`, `fix/…` (e.g. `feat/calculator-console-app`).

Examples from history:

```
feat: add uv-based console calculator with OOP design and tests
docs: add git-auth note, theme-proof diagram, trim docker comments
```

**No attribution trailers** — no `Co-Authored-By: Claude …`. This repo's convention.


