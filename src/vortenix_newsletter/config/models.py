from pydantic import BaseModel, Field, model_validator

class RankingWeights(BaseModel):
    relevance: float=.3; novelty: float=.2; significance: float=.2; evidence: float=.15; recency: float=.15
    @model_validator(mode="after")
    def total(self):
        if abs(sum((self.relevance,self.novelty,self.significance,self.evidence,self.recency))-1)>0.01: raise ValueError("ranking weights must total 1.0")
        return self
class VerticalConfig(BaseModel):
    id: str; name: str; enabled: bool=True; implementation: str="generic"
    research_areas: list[str]=Field(default_factory=list); keywords: list[str]
    ranking_weights: RankingWeights=Field(default_factory=RankingWeights)
    newsletter: dict[str,object]=Field(default_factory=dict)
class SourceConfig(BaseModel):
    name: str; url: str; enabled: bool=True; retrieve_articles: bool=False
class AppConfig(BaseModel):
    database_url: str="sqlite:///data/vortenix.db"; confidence_threshold: float=.35
