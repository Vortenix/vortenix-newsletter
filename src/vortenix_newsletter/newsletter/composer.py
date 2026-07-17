from vortenix_newsletter.config.models import VerticalConfig
from vortenix_newsletter.domain.models import Audience,Newsletter,NewsletterSection,VerticalResearchResult
def compose(audience: Audience,results: list[VerticalResearchResult],configs: list[VerticalConfig])->Newsletter:
    by_id={c.id:c for c in configs}; seen=set(); sections=[]
    for result in results:
        cfg=by_id[result.vertical_id]; chosen=[]; maximum=int(cfg.newsletter.get("maximum_items",5))
        for finding in result.findings:
            key=(str(finding.citations[0].url) if finding.citations else finding.title).casefold()
            if key not in seen and len(chosen)<maximum: seen.add(key); chosen.append(finding)
        sections.append(NewsletterSection(vertical_id=result.vertical_id,heading=str(cfg.newsletter.get("section_title",cfg.name)),introduction=result.executive_summary,items=chosen,what_to_watch=result.what_to_watch))
    summary=" ".join(s.introduction for s in sections) or "No qualifying developments were found."
    return Newsletter(title=f"Vortenix Research Brief — {audience.name}",executive_summary=summary,sections=sections,audience_id=audience.id)
