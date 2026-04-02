# Contributing

Git-Map is open-source (MIT). Contributions are welcome from everyone — whether you're a GIS professional, Python developer, or just someone with a good idea.

## Ways to Contribute

- **Report bugs** — use the [Bug Report issue template](https://github.com/14-TR/Git-Map/issues/new?template=bug_report.yml)
- **Request features** — use the [Feature Request template](https://github.com/14-TR/Git-Map/issues/new?template=feature_request.yml)
- **Fix bugs** — check [open issues labeled `bug`](https://github.com/14-TR/Git-Map/issues?q=is%3Aopen+label%3Abug)
- **Improve docs** — every page has an edit link at the top
- **Add tests** — the test suite is at `packages/gitmap_core/tests/`

## Dev Setup

```bash
git clone https://github.com/14-TR/Git-Map.git
cd Git-Map
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e "packages/gitmap_core[dev]"
pip install click rich
```

## Running Tests

```bash
pytest packages/gitmap_core/tests -v
```

All 734+ tests must pass before opening a PR. The CI pipeline runs the same suite on Python 3.11, 3.12, 3.13, and 3.14.

## Project Structure

```
Git-Map/
├── packages/
│   └── gitmap_core/        # Core library — version control engine
│       └── tests/          # 734+ tests live here
├── apps/
│   ├── cli/gitmap/         # `gitmap` CLI (Click + Rich)
│   ├── mcp/                # MCP server for AI agent integration
│   └── client/             # GUI client (WIP)
├── integrations/           # OpenClaw and other integrations
├── docs/                   # This documentation site (MkDocs Material)
└── .github/
    ├── workflows/          # CI, docs deploy, PyPI publish
    └── ISSUE_TEMPLATE/     # Bug + feature templates
```

## Making Changes

1. Fork the repo and create a `feature/` branch from `main`.
2. Write tests for any new functionality.
3. Ensure all tests pass locally.
4. Open a PR — the PR template will guide you through the required fields.

## Code Style

- **Formatter:** [ruff](https://docs.astral.sh/ruff/) (included in dev deps)
- **Type hints:** use them; the codebase is progressively typed
- **Docstrings:** Google style for public functions/classes

Run the linter:

```bash
ruff check packages/gitmap_core
```

## Docs

The site is built with [MkDocs Material](https://squidfunk.github.io/mkdocs-material/). Preview locally:

```bash
pip install mkdocs-material
mkdocs serve
```

Then open `http://127.0.0.1:8000`.

## Code of Conduct

Please read [CODE_OF_CONDUCT.md](https://github.com/14-TR/Git-Map/blob/main/CODE_OF_CONDUCT.md) before participating. We follow the Contributor Covenant.

## License

MIT — see [LICENSE](https://github.com/14-TR/Git-Map/blob/main/LICENSE).
