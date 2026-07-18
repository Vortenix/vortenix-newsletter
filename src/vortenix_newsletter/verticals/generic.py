import re
from vortenix_newsletter.config.models import VerticalConfig
from vortenix_newsletter.domain.models import Citation,ResearchContext,ResearchFinding,ResearchPlan,SourceDocument,VerticalResearchResult
from vortenix_newsletter.research.ranker import rank
class GenericVertical:
    """Deterministic research vertical driven by validated YAML configuration."""

    def __init__(self,config: VerticalConfig): self.config=config
    @property
    def vertical_id(self)->str: return self.config.id
    def build_research_plan(self,context: ResearchContext)->ResearchPlan: return ResearchPlan(vertical_id=self.vertical_id,research_areas=self.config.research_areas,keywords=self.config.keywords)
    async def analyse(self,documents: list[SourceDocument])->VerticalResearchResult:
        findings=[]
        for doc in documents:
            if doc.metadata.get("verticals") and self.vertical_id not in doc.metadata["verticals"]: continue
            text=f"{doc.title} {doc.content}"; matches=sum(1 for k in self.config.keywords if k.casefold() in text.casefold())
            if not matches: continue
            sentences=re.split(r"(?<=[.!?])\s+",doc.content); summary=(sentences[0] if sentences else doc.title)[:500]
            companies=sorted(set(re.findall(r"\b[A-Z][A-Za-z0-9&.-]+(?:\s+[A-Z][A-Za-z0-9&.-]+){0,2}",text)))[:5]
            pain=[s[:200] for s in sentences if re.search(r"\b(challenge|bottleneck|shortage|cost|risk|difficult)\b",s,re.I)][:3]
            relevance=min(1,matches/max(1,min(4,len(self.config.keywords))))
            community=doc.metadata.get("trust_level") == "community"
            findings.append(ResearchFinding(vertical_id=self.vertical_id,title=doc.title,summary=summary,development=f"Observed: {summary}",significance="Community signal requiring corroboration." if community else "Interpretation: this development matches configured research priorities.",pain_points=pain,affected_companies=companies,opportunities=["Monitor adoption and solution activity."],risks=["Unverified community report; corroborate with an authoritative source."] if community else ["Evidence is limited to the cited source."],relevance_score=relevance,novelty_score=.6,significance_score=.4 if community else .6,confidence_score=.45 if community else .7,evidence_score=.35 if community else .7,recency_score=.9,citations=[Citation(source_document_id=doc.id,source_title=doc.title,url=doc.url,supporting_excerpt=summary[:300])]))
        ranked=self.rank_findings(findings)
        return VerticalResearchResult(vertical_id=self.vertical_id,executive_summary=f"{len(ranked)} cited development(s) matched {self.config.name}.",findings=ranked,important_companies=sorted({c for f in ranked for c in f.affected_companies})[:10],what_to_watch=[f.title for f in ranked[:3]])
    def rank_findings(self,findings): return rank(findings,self.config.ranking_weights)
