from vortenix_newsletter.config.models import RankingWeights
from vortenix_newsletter.domain.models import ResearchFinding
def rank(findings: list[ResearchFinding],w: RankingWeights)->list[ResearchFinding]:
    for f in findings: f.rank_score=round(f.relevance_score*w.relevance+f.novelty_score*w.novelty+f.significance_score*w.significance+f.evidence_score*w.evidence+f.recency_score*w.recency,4)
    return sorted(findings,key=lambda x:x.rank_score,reverse=True)
