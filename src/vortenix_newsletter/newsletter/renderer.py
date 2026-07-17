from pathlib import Path
from jinja2 import Environment,PackageLoader,select_autoescape
from vortenix_newsletter.domain.models import Newsletter
class Renderer:
    """Render newsletter domain objects into reviewable local artifacts."""

    def __init__(self,root=Path("data/newsletters")):
        self.root=root; self.env=Environment(loader=PackageLoader("vortenix_newsletter","templates"),autoescape=select_autoescape(["html","xml"]))
    def render(self,n: Newsletter)->Newsletter:
        folder=self.root/n.id; folder.mkdir(parents=True,exist_ok=True)
        html=folder/"newsletter.html"; text=folder/"newsletter.txt"; js=folder/"newsletter.json"
        html.write_text(self.env.get_template("newsletter.html.j2").render(newsletter=n),encoding="utf-8")
        text.write_text(self.env.get_template("newsletter.txt.j2").render(newsletter=n),encoding="utf-8")
        n.html_path=str(html); n.text_path=str(text); n.json_path=str(js); js.write_text(n.model_dump_json(indent=2),encoding="utf-8")
        return n
