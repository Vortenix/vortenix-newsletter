# CLI reference

| Command | Purpose |
| --- | --- |
| `vortenix config validate` | Parse and validate all configuration |
| `vortenix db init` | Create current SQLAlchemy tables |
| `vortenix sources collect` | Collect enabled configured sources |
| `vortenix research run [--vertical ID]` | Collect, analyse, and generate a newsletter for one or all verticals |
| `vortenix newsletter generate --audience ID` | Collect, research, and generate a review draft |
| `vortenix newsletter list` | List persisted newsletters |
| `vortenix newsletter show ID` | Print newsletter JSON |
| `vortenix newsletter approve ID` | Approve a review-ready newsletter |
| `vortenix newsletter reject ID` | Reject a review-ready newsletter |
| `vortenix newsletter send ID [--force]` | Deliver an approved newsletter through the configured provider |
| `vortenix workflow run-daily --demo` | Run the complete offline fixture workflow |
| `vortenix subscribers list [--audience ID]` | List private subscriber IDs and selected verticals without printing addresses |
| `vortenix workflow run-personalized [--audience ID] [--subscriber ID] [--demo]` | Generate one review-ready newsletter per selected private subscriber using their tier and verticals |
| `vortenix workflow run-scheduled [--audience ID] [--demo]` | Guarded automatic generation, approval, and SMTP delivery for every enabled subscriber |

Use `python -m vortenix_newsletter.cli.app` in place of `vortenix` if the script directory is not on `PATH`.

Free subscribers always use deterministic analysis. Premium subscribers request LLM analysis and fall back per vertical to deterministic analysis on provider failure. `run-scheduled` requires `VORTENIX_EMAIL_PROVIDER=smtp` and `VORTENIX_ALLOW_AUTOMATIC_SEND=true`.
