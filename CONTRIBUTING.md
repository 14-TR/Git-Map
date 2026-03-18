# Contributing to Git-Map

Thanks for your interest in contributing! Git-Map is open-source (MIT) and welcomes contributions from GIS professionals and Python developers alike.

See the full [Contributing Guide](https://14-tr.github.io/Git-Map/contributing/) in the documentation for setup instructions, code style, and PR guidelines.

## Quick Links

- [Bug Reports](https://github.com/14-TR/Git-Map/issues/new?template=bug_report.yml)
- [Feature Requests](https://github.com/14-TR/Git-Map/issues/new?template=feature_request.yml)
- [Documentation](https://14-tr.github.io/Git-Map)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Security Policy](SECURITY.md)

## Quick Start for Contributors

```bash
git clone https://github.com/14-TR/Git-Map.git
cd Git-Map
python3 -m venv .venv && source .venv/bin/activate
pip install -e "packages/gitmap_core[dev]"
pytest packages/gitmap_core/tests -v   # must all pass
```

Open a PR from a `feature/` branch with a clear description of what changed and why.
