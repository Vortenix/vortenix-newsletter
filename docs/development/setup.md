# Development setup

Use Python 3.12 or newer. From the repository root:

```console
python -m venv .venv
python -m pip install -e ".[dev]"
python -m vortenix_newsletter.cli.app config validate
make check
make demo
```

Activate `.venv` using `.venv\Scripts\Activate.ps1` on PowerShell or `source .venv/bin/activate` on Unix. See [CONTRIBUTING.md](../../CONTRIBUTING.md) for branch, test, and pull-request expectations.
