# Contributing

Git-Map is open-source (MIT). Contributions are welcome!

## Setup

```bash
git clone https://github.com/14-TR/Git-Map.git
cd Git-Map
python3 -m venv .venv
source .venv/bin/activate
pip install -e "packages/gitmap_core[dev]"
```

## Running Tests

```bash
pytest packages/gitmap_core/tests -v
```

All 663+ tests must pass before opening a PR.

## Structure

```
Git-Map/
├── packages/
│   └── gitmap_core/    # Core library (version-controlled here)
├── apps/
│   ├── cli/            # gitmap CLI
│   ├── mcp/            # MCP server
│   └── client/         # GUI client
├── integrations/       # OpenClaw and other integrations
└── docs/               # This documentation site
```

## Making Changes

1. Fork the repo and create a `feature/` branch.
2. Write tests for new functionality.
3. Ensure all tests pass.
4. Open a PR with a clear description of what changed and why.

## Docs

This site is built with [MkDocs Material](https://squidfunk.github.io/mkdocs-material/). To preview locally:

```bash
pip install mkdocs-material
mkdocs serve
```

Then open `http://127.0.0.1:8000`.

## License

MIT — see [LICENSE](https://github.com/14-TR/Git-Map/blob/main/LICENSE).
