"""Provider-neutral structured drafts returned by LLM analysis."""

from pydantic import BaseModel, Field


class LLMCitationDraft(BaseModel):
    """Reference to one supplied source document."""

    source_document_id: str
    supporting_excerpt: str = Field(max_length=300)


class LLMCompanySolutionDraft(BaseModel):
    """Closed schema for a company and its observed solution."""

    company: str
    solution: str


class LLMFindingDraft(BaseModel):
    """Evidence-linked finding before application scoring and domain mapping."""

    title: str
    summary: str
    development: str
    significance: str
    pain_points: list[str] = Field(default_factory=list)
    company_solutions: list[LLMCompanySolutionDraft] = Field(default_factory=list)
    affected_companies: list[str] = Field(default_factory=list)
    opportunities: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    citations: list[LLMCitationDraft]


class LLMVerticalDraft(BaseModel):
    """Structured research output that excludes application-owned scores and IDs."""

    executive_summary: str
    findings: list[LLMFindingDraft]
    emerging_trends: list[str] = Field(default_factory=list)
    important_companies: list[str] = Field(default_factory=list)
    what_to_watch: list[str] = Field(default_factory=list)
