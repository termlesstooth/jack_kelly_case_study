# business logic for looping over companies + dumping to JSON
from __future__ import annotations

from typing import Any, Dict, List, Optional

from src.merlin.enrichment.harmonic_graphql_client import HarmonicGraphQLClient
from src.merlin.models import (
    RawCompany,
    CompanyEnrichment,
    HarmonicEnrichment,
    FounderContact,
    EmployeeHighlight
)


def _clean_domain(url: str) -> str:
    if not url:
        return ""
    url = url.replace("https://", "").replace("http://", "")
    return url.split("/")[0].strip()

# TODO: future improvement, update for more than just founders
def _extract_founders(company: Dict[str, Any]) -> List[FounderContact]:
    founders: List[FounderContact] = []
    for emp in company.get("employees") or []:
        name = emp.get("fullName") or ""
        if not name:
            continue

        title: Optional[str] = None
        for exp in emp.get("experience") or []:
            rt = (exp.get("roleType") or "").upper()
            if "FOUNDER" in rt: # TODO: Harmonic has other values available, explore
                title = exp.get("title")
                break
        if not title and (emp.get("experience") or []):
            title = emp["experience"][0].get("title")

        # linkedin
        linkedin_url = None
        socials = emp.get("socials") or {}
        linkedin = socials.get("linkedin") or {}
        linkedin_url = linkedin.get("url")

        # emails
        contact = emp.get("contact") or {}
        raw_emails = contact.get("emails") or []

        # filter out empty emails
        filtered = [email for email in raw_emails if email]

        # Deduplicate while preserving order
        emails = list(dict.fromkeys(filtered))

        # normalize empty list -> None
        emails = emails or None
        
        # founder-level highlights
        raw_highlights = emp.get("highlights") or []
        highlights = [
            EmployeeHighlight(
                category=h.get("category", ""),
                text=h.get("text",""),
            )
            for h in raw_highlights
            if h.get("category") or h.get("text")
        ] or None


        founders.append(
            FounderContact(
                name=name,
                title=title,
                linkedin_url=linkedin_url,
                emails=emails,
                highlights=highlights
            )
        )
    return founders


def _extract_employee_highlights(company: Dict[str, Any]) -> List[EmployeeHighlight]:
    out: List[EmployeeHighlight] = []
    for h in company.get("employeeHighlights") or []:
        out.append(
            EmployeeHighlight(
                category=h.get("category") or "",
                text=h.get("text") or "",
            )
        )
    return out


def _extract_investors(funding: Dict[str, Any]) -> List[str]:
    investors_raw = funding.get("investors") or []
    names: List[str] = []

    for inv in investors_raw:
        # accounts for both company, and name (investor can be either)
        name = inv.get("name") or inv.get("fullName")
        if name:
            names.append(name)

    return names


def _extract_highlights(company: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    """
    Flatten company.highlights into parallel lists of categories and texts.
    Each highlight is like:
      { "category": "VENTURE_BACKED", "text": "Backed By Team8" }
    """
    categories: List[str] = []
    texts: List[str] = []

    for h in company.get("highlights") or []:
        cat = h.get("category")
        txt = h.get("text")

        if cat:
            categories.append(cat)
        if txt:
            texts.append(txt)

    return categories, texts


def _extract_traction_metrics(company: Dict[str, Any]) -> Dict[str, Optional[float]]:
    """
    Extracts traction metrics like social follower counts and advisor headcount.
    Safely handles missing fields and null values.
    """
    tm = company.get("tractionMetrics") or {}

    def get_latest(key: str) -> Optional[float]:
        node = tm.get(key) or {}
        return node.get("latestMetricValue")

    return {
        "headcount_advisor": get_latest("headcountAdvisor"),
        "facebook_followers": get_latest("facebookFollowerCount"),
        "linkedin_followers": get_latest("linkedinFollowerCount"),
        "instagram_followers": get_latest("instagramFollowerCount"),
        "twitter_followers": get_latest("twitterFollowerCount"),
    }


def _extract_tag_groups(company: Dict[str, Any]) -> Dict[str, List[str]]:
    tags_v2 = company.get("tagsV2") or []

    groups = {
        "industries": [],
        "market_verticals": [],
        "market_sub_verticals": [],
        "technology_types": [],
        "product_types": [],
    }

    for t in tags_v2:
        value = t.get("displayValue")
        t_type = (t.get("type") or "").upper()
        if not value:
            continue

        if t_type == "INDUSTRY":
            groups["industries"].append(value)
        elif t_type == "MARKET_VERTICAL":
            groups["market_verticals"].append(value)
        elif t_type == "MARKET_SUB_VERTICAL":
            groups["market_sub_verticals"].append(value)
        elif t_type == "TECHNOLOGY_TYPE":
            groups["technology_types"].append(value)
        elif t_type == "PRODUCT_TYPE":
            groups["product_types"].append(value)

    return groups


def map_company_to_harmonic_enrichment(company: Dict[str, Any]) -> HarmonicEnrichment:
    website = company.get("website") or {}
    founding_date_dict = company.get("foundingDate") or {}
    funding = company.get("funding") or {}
    location = company.get("location") or {}
    tag_groups = _extract_tag_groups(company)


    # helpers
    highlight_categories, highlight_texts = _extract_highlights(company)
    traction_metrics = _extract_traction_metrics(company)

    founding_date_value = founding_date_dict.get("date")
    founding_date_grain = founding_date_dict.get("granularity")
    advisor_headcount = traction_metrics.get("headcount_advisor")

    # extract founders once
    founders = _extract_founders(company)

    
    # flatten founder highlights
    founder_employee_highlights = [
        h
        for f in (founders or [])
        for h in (f.highlights or [])
    ]


    return HarmonicEnrichment(
        # identity / keys
        harmonic_id=company.get("entityUrn") or "",
        website_domain=website.get("domain") or "",
        website_url = website.get("url") or "",

        # basic description
        description=company.get("description"),
        name=None,
        customer_type=company.get("customerType"),

        # lifecycle / stage / funding
        stage=company.get("stage"),
        funding_total=funding.get("fundingTotal"),
        funding_stage=funding.get("fundingStage"),
        num_funding_rounds=funding.get("numFundingRounds"),
        last_funding_at=funding.get("lastFundingAt"),
        investors=_extract_investors(funding),

        # size / age / location
        headcount=company.get("headcount"),
        founding_date=founding_date_value,
        founding_date_granularity=founding_date_grain,
        location=location,  # keep full dict; you can also store location.get("location")

        # classification TODO: Clean up tags vs tags v2
        tags=[t.get("displayValue") for t in (company.get("tags") or [])],
        tags_v2=[t.get("displayValue") for t in (company.get("tagsV2") or [])],

        # industries come from tags NOTE: Appears to be a legacy feature
        industries=[
            t.get("displayValue")
            for t in (company.get("tags") or [])
            if (t.get("type") or "").upper() == "INDUSTRY"
        ],


        market_verticals=tag_groups["market_verticals"],
        market_sub_verticals=tag_groups["market_sub_verticals"],
        technology_types=tag_groups["technology_types"],
        product_types=tag_groups["product_types"],

        # highlights
        highlight_categories=highlight_categories,
        highlight_texts=highlight_texts,
        employee_highlights=founder_employee_highlights or None, # NOTE: Used this originally for highlights, but have founder specific highlights now. May come in use if we want to score based on other employees

        # traction / traffic / extra signals
        traction_metrics=traction_metrics,
        advisor_headcount=advisor_headcount,
        web_traffic=company.get("webTraffic"),
        likelihood_of_backing=company.get("likelihoodOfBacking"),

        # founders
        founders=founders or None,

        # founder highlights
        founder_employee_highlights=founder_employee_highlights or None
        
    )


def enrich_company_with_harmonic(raw: RawCompany, client: HarmonicGraphQLClient) -> CompanyEnrichment:
    website_domain = raw.domain.strip()

    payload = client.enrich_company_by_domain(website_domain)

    if not payload.get("companyFound"):
        return CompanyEnrichment(harmonic=None)

    company = payload["company"]
    harmonic = map_company_to_harmonic_enrichment(company)
    return CompanyEnrichment(harmonic=harmonic)
