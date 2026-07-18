import asyncio,logging
import typer
from dotenv import load_dotenv
from vortenix_newsletter.config.loader import load_config
from vortenix_newsletter.domain.models import SourceRequest
from vortenix_newsletter.ingestion.rss_connector import RSSConnector
from vortenix_newsletter.newsletter.service import NewsletterService
from vortenix_newsletter.persistence.database import init_db,session_factory
from vortenix_newsletter.persistence.repositories import NewsletterRepository,SourceRepository
from vortenix_newsletter.providers.email.console_provider import ConsoleEmailProvider
from vortenix_newsletter.providers.email.factory import create_email_provider, newsletter_recipients
from vortenix_newsletter.workflows.newsletter_workflow import run_daily, run_personalized
logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)s %(name)s %(message)s')
load_dotenv()
app=typer.Typer(help="Vortenix Newsletter"); config_app=typer.Typer(); db_app=typer.Typer(); sources_app=typer.Typer(); research_app=typer.Typer(); newsletter_app=typer.Typer(); workflow_app=typer.Typer(); subscribers_app=typer.Typer()
app.add_typer(config_app,name="config"); app.add_typer(db_app,name="db"); app.add_typer(sources_app,name="sources"); app.add_typer(research_app,name="research"); app.add_typer(newsletter_app,name="newsletter"); app.add_typer(workflow_app,name="workflow"); app.add_typer(subscribers_app,name="subscribers")
def context():
    cfg=load_config(); init_db(cfg.application.database_url); return cfg,session_factory(cfg.application.database_url)()
@config_app.command("validate")
def config_validate(): cfg=load_config(); typer.echo(f"Configuration valid: {len(cfg.verticals)} verticals, {len(cfg.sources)} sources, {len(cfg.audiences)} audiences, {len(cfg.subscribers)} private subscribers")
@subscribers_app.command("list")
def list_subscribers(audience: str|None=typer.Option(None)):
    cfg=load_config(); subscribers=cfg.subscribers_for(audience) if audience else [x for x in cfg.subscribers if x.enabled]
    for subscriber in subscribers:
        typer.echo(f"{subscriber.id}  {subscriber.name}  {', '.join(subscriber.enabled_verticals)}")
@db_app.command("init")
def db_init(): cfg=load_config(); init_db(cfg.application.database_url); typer.echo("Database initialized")
@sources_app.command("collect")
def collect():
    async def go():
        cfg,s=context(); docs=[]
        for x in cfg.sources:
            if x.enabled: docs.extend(await RSSConnector().fetch(SourceRequest(source_name=x.name,url=x.url,retrieve_articles=x.retrieve_articles)))
        SourceRepository(s).add_all(docs); return len(docs)
    typer.echo(f"Collected {asyncio.run(go())} documents")
@research_app.command("run")
def research_run(vertical: str|None=typer.Option(None)):
    cfg,s=context(); audience=cfg.audiences[0]
    if vertical: audience.enabled_verticals=[vertical]
    n=asyncio.run(run_daily(cfg,audience,s)); typer.echo(f"Research complete; newsletter {n.id} is {n.status}")
@newsletter_app.command("generate")
def generate(audience: str=typer.Option(...)):
    cfg,s=context(); n=asyncio.run(run_daily(cfg,cfg.audience(audience),s)); typer.echo(f"Newsletter ID: {n.id}\nHTML: {n.html_path}\nText: {n.text_path}\nStatus: {n.status}")
@newsletter_app.command("list")
def list_newsletters():
    _,s=context()
    for n in NewsletterRepository(s).list(): typer.echo(f"{n.id}  {n.status}  {n.edition_date}  {n.title}")
@newsletter_app.command("show")
def show(ident: str): _,s=context(); typer.echo(NewsletterRepository(s).get(ident).model_dump_json(indent=2))
@newsletter_app.command("approve")
def approve(ident: str): _,s=context(); n=NewsletterService(NewsletterRepository(s),ConsoleEmailProvider()).approve(ident); typer.echo(f"{n.id}: {n.status}")
@newsletter_app.command("reject")
def reject(ident: str): _,s=context(); n=NewsletterService(NewsletterRepository(s),ConsoleEmailProvider()).reject(ident); typer.echo(f"{n.id}: {n.status}")
@newsletter_app.command("send")
def send(ident: str,force: bool=False):
    cfg,s=context(); n=NewsletterRepository(s).get(ident)
    recipients=newsletter_recipients(n,cfg.audience(n.audience_id).recipients)
    result=asyncio.run(NewsletterService(NewsletterRepository(s),create_email_provider()).send(ident,recipients,force)); typer.echo(f"Delivery success: {result.success}")
@workflow_app.command("run-daily")
def daily(audience: str=typer.Option("anish_daily"),demo: bool=False):
    cfg,s=context(); n=asyncio.run(run_daily(cfg,cfg.audience(audience),s,demo=demo)); typer.echo(f"Newsletter ID: {n.id}\nHTML: {n.html_path}\nText: {n.text_path}\nJSON: {n.json_path}\nStatus: {n.status}")
@workflow_app.command("run-personalized")
def personalized(audience: str=typer.Option("anish_daily"),subscriber: str|None=typer.Option(None),demo: bool=False):
    cfg,s=context(); subscribers=[cfg.subscriber(subscriber)] if subscriber else cfg.subscribers_for(audience)
    newsletters=asyncio.run(run_personalized(cfg,cfg.audience(audience),subscribers,s,demo=demo))
    if not newsletters:
        raise typer.BadParameter("No enabled subscribers found; create config/subscribers.local.yaml")
    for item in newsletters:
        typer.echo(f"Subscriber: {item.subscriber_id}\nNewsletter ID: {item.id}\nHTML: {item.html_path}\nStatus: {item.status}\n")
if __name__=="__main__": app()
