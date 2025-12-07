# Makes calls to Harmonic's API via rest. Probably can deprecate since I'm going with GraphQL
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Dict, Any
import os
import requests


class HarmonicError(Exception):
    """Custom error for Harmonic API issues."""


@dataclass
class HarmonicConfig:
    api_key: str
    base_url: str = "https://api.harmonic.ai"
    timeout: int = 10  # seconds


class HarmonicClient:
    def __init__(self, config: HarmonicConfig):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update(
            {
                "accept": "application/json",
                "apikey": config.api_key,
            }
        )

    @classmethod
    def from_env(cls) -> "HarmonicClient":
        api_key = os.getenv("HARMONIC_API_KEY")
        if not api_key:
            raise RuntimeError("HARMONIC_API_KEY not set in environment")
        return cls(HarmonicConfig(api_key=api_key))

    def enrich_company(
        self,
        *,
        website_domain: Optional[str] = None,
        website_url: Optional[str] = None,
        linkedin_url: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Call Harmonic's /companies enrichment endpoint for a single company."""

        params: Dict[str, str] = {}
        if website_domain:
            params["website_domain"] = website_domain
        if website_url:
            params["website_url"] = website_url
        if linkedin_url:
            params["linkedin_url"] = linkedin_url

        if not params:
            raise ValueError("At least one identifier must be provided")

        url = f"{self.config.base_url}/companies"
        resp = self.session.post(url, params=params, timeout=self.config.timeout)

        if resp.status_code == 200:
            return resp.json()

        if resp.status_code == 404:
            # Custom status code. Harmonic is enriching in the background, not ready to use yet
            return None

        raise HarmonicError(
            f"Harmonic error {resp.status_code}: {resp.text}"
        )
