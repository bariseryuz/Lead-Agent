from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class LeadStatus(str, Enum):
    """
    Pipeline status of a lead as decided by the Architect.
    - READY: has a company_name and location, good to deliver
    - REQUIRES_ENRICHMENT: real project but missing contact info, loop back to Scout
    - TRASH: junk data, discard
    """
    READY = "ready"
    REQUIRES_ENRICHMENT = "requires_enrichment"
    TRASH = "trash"


class Lead(BaseModel):
    """
    Schema for a single business lead.
    This is the 'Data Contract' the Architect agent produces.
    """

    company_name: Optional[str] = Field(
        default=None,
        description="The company / contractor name. Null if not yet discovered."
    )

    location: Optional[str] = Field(
        default=None,
        description="The physical address or city/region of the project."
    )

    budget: Optional[float] = Field(
        default=None,
        description="Estimated dollar value of the project. None if unknown."
    )

    why_this_lead: str = Field(
        default="",
        description="1-2 sentence explanation of why this lead matches the user's intent."
    )

    status: LeadStatus = Field(
        default=LeadStatus.READY,
        description="Pipeline status used by the graph router."
    )

    enrichment_query: Optional[str] = Field(
        default=None,
        description="Search query the Scout should run next, set when status == REQUIRES_ENRICHMENT."
    )

    confidence_score: float = Field(
        default=0.0,
        description="AI's certainty about this data (0-100)."
    )

    @field_validator("confidence_score")
    @classmethod
    def validate_score(cls, v: float) -> float:
        if not 0 <= v <= 100:
            raise ValueError("Confidence score must be between 0 and 100")
        return v


class LeadReport(BaseModel):
    """Top-level container for all findings from a specific source."""
    source_url: str = Field(description="The URL of the website where the data was found.")
    leads: List[Lead] = Field(description="A list of lead objects extracted from the site.")
    summary: str = Field(description="A 1-2 sentence overview of the search results.")
