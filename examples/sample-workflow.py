"""Run the checked-in offline workflow programmatically from the repository root."""
import asyncio
from vortenix_newsletter.config.loader import load_config
from vortenix_newsletter.persistence.database import init_db, session_factory
from vortenix_newsletter.workflows.newsletter_workflow import run_daily

async def main() -> None:
    config = load_config()
    init_db(config.application.database_url)
    with session_factory(config.application.database_url)() as session:
        newsletter = await run_daily(config, config.audience("anish_daily"), session, demo=True)
    print(newsletter.id, newsletter.status, newsletter.html_path)

if __name__ == "__main__":
    asyncio.run(main())
