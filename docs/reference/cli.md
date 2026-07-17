# CLI reference

| Command | Purpose |
| --- | --- |
| `vortenix config validate` | Parse and validate all configuration |
| `vortenix db init` | Create current SQLAlchemy tables |
| `vortenix sources collect` | Collect enabled configured sources |
| `vortenix research run [--vertical ID]` | Run current workflow, including newsletter generation |
| `vortenix newsletter generate --audience ID` | Collect, research, and generate a review draft |
| `vortenix newsletter list` | List persisted newsletters |
| `vortenix newsletter show ID` | Print newsletter JSON |
| `vortenix newsletter approve ID` | Approve a review-ready newsletter |
| `vortenix newsletter reject ID` | Reject a review-ready newsletter |
| `vortenix newsletter send ID [--force]` | Console-deliver an approved newsletter |
| `vortenix workflow run-daily --demo` | Run the complete offline fixture workflow |

Use `python -m vortenix_newsletter.cli.app` in place of `vortenix` if the script directory is not on `PATH`.
