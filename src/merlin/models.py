# data models
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

# Raw input (currently from csv)
@dataclass
class RawCompany:
    """
    Company as it appears in our source data.
    This is everything we know *before* calling any external APIs.
    """
    name: str
    domain: str # called url in input
    description: str
    stage: str
    industry: str


# Harmonic enrichment models
# -------------------------------------------------------------------
@dataclass
class FounderContact:
    """
    Single founder from Harmonic's employees (employeeGroupType=FOUNDERS)
    TODO: Future Improvement: Integrate other types of employees
    """
    name: str
    title: Optional[str] = None
    linkedin_url: Optional[str] = None
    email: Optional[str] = None
    all_emails: Optional[str] = None


@dataclass
class EmployeeHighlight:
    """
    Rows from company.employeeHighlights (e.g. YC Backed Founder, Prior Exit)
    """
    category: str
    text: str


@dataclass
class CompanyHighlight:
    """
    Rows from company.highlights (Venture Backed, etc.)
    """
    category: str
    text: str


@dataclass
class HarmonicEnrichment:
    """
    Subset of Harmonic fields that are useful for downstream scoring.
    This mirrors our GraphQL query in a cleaned-up, Pythonic way.
    """
    # identity / keys
    website_domain: str
    harmonic_id: str    # company.entityUrn
    website_url: str = None

    # basic description
    description: Optional[str] = None
    name: Optional[str] = None  #TODO: query from Harmonic API, need to add to client
    customer_type: Optional[str] = None

    # lifecycle / stage / funding
    stage: Optional[str] = None
    funding_total: Optional[float] = None   # funding.fundingTotal
    funding_stage: Optional[str] = None # funding.fundingStage
    num_funding_rounds: Optional[int] = None    # funding.numFundingRounds
    last_funding_at: Optional[str] = None   # funding.lastFundingAt
    investors: List[str] = None # names from funding.investors 

    # size / age / location
    headcount: Optional[int] = None
    founding_date: Optional[str] = None # foundingDate.date
    founding_date_granularity: Optional[str] = None # foundingDate.granularity
    location: Optional[Dict[str, Any]] = None   # company.location {location, addressFormatted} # TODO: can probably remove addressFormatted

    # classification
    tags: List[str] = None  # from tags.displayValue
    tags_v2: List[str] = None   
    
    # classification (typed from tagsV2)
    industries: List[str] = None    # type == INDUSTRY
    market_verticals: List[str] = None  # type == MARKET_VERTICAL
    market_sub_verticals: List[str] = None  # type == MARKET_SUB_VERTICAL
    technology_types: List[str] = None  # type == TECHNOLOGY_TYPE
    product_types: List[str] = None # type == PRODUCT_TYPE          # from tagsV2.displayValue

    # highlights
    highlight_categories: List[str] = None
    highlight_texts: List[str] = None
    employee_highlights: List[EmployeeHighlight] = None

    # traction / traffic / extra signals
    traction_metrics: Optional[Dict[str, Any]] = None
    advisor_headcount: Optional[float] = None   # headcountAdvisor.latestMetricValue
    web_traffic: Optional[Dict[str, Any]] = None
    likelihood_of_backing: Optional[float] = None

    # founders
    founders: List[FounderContact] = None
# -------------------------------------------------------------------



# Place holder for additional vendor-specific enrichment models
# -------------------------------------------------------------------
@dataclass
class ApolloEnrichment:
    """
    Example second provider. Can fill in once I add another enrichment data source
    """
    apollo_id: str
    num_employees: Optional[int] = None
    annual_revenue: Optional[float] = None
    tech_stack: List[str] = None
    linkedin_url: Optional[str] = None
# -------------------------------------------------------------------



# Aggregated enrichment for a single company (all providers in one place)
@dataclass
class CompanyEnrichment:
    """
    Container for all enrichment sources tied to a single company.
    Your feature builder can look at everything here and decide how
    to merge / prioritize different providers.
    """
    harmonic: Optional[HarmonicEnrichment] = None
    #apollo: Optional[ApolloEnrichment] = None



# Provider-agnostic features used by the scoring pipeline
@dataclass
class CompanyFeatures:
    """
    Flattened, provider-agnostic features that the scoring function uses.
    This is the final representation of a company before scoring.
    """
    # id / identity
    name: str
    website_domain: str

    # raw data
    raw_stage: Optional[str]
    raw_industry: Optional[str]

    # size / stage
    headcount: Optional[int]
    stage: Optional[str]              # unified stage (Harmonic + raw)

    # geography
    geography_location: Optional[str]  # e.g. location["location"]
    # you can split to country later if you want

    # funding
    funding_total: Optional[float]
    num_funding_rounds: Optional[int]

    # traction
    has_web_traffic: bool
    web_traffic_monthly_visits: Optional[float]
    likelihood_of_backing: Optional[float]

    # founder signals
    founders: List[FounderContact]
    founder_count: int
    founder_emails_count: int
    employee_highlights: List[EmployeeHighlight]  # for YC Backed Founder, Prior Exit, etc.

    # sector / tags
    tags: List[str]
    tags_v2: List[str]

    # optional future fields
    estimated_revenue: Optional[float] = None
    tech_stack_size: Optional[int] = None