# Makes calls to Harmonic's API via GraphQL
from __future__ import annotations

import os
from typing import Any, Dict, Optional

import requests


class HarmonicGraphQLClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        endpoint: str = "https://api.harmonic.ai/graphql",
    ) -> None:
        self.api_key = api_key or os.environ.get("HARMONIC_API_KEY")
        if not self.api_key:
            raise ValueError("HARMONIC_API_KEY is not set")

        self.endpoint = endpoint
        self.session = requests.Session()
        self.session.headers.update(
    {
        "accept": "application/json",
        "content-type": "application/json",
        "apikey": self.api_key,
    }
)


        self._enrich_company_query = """
mutation($identifiers: CompanyEnrichmentIdentifiersInput!) {
  enrichCompanyByIdentifiers(identifiers: $identifiers) {
    companyFound
    company {
      entityUrn
      website {
        url
        domain
      }
      description
      foundingDate {
        date
        granularity
      }
      funding {
        fundingTotal
        fundingStage
        numFundingRounds
        lastFundingAt
        investors {
          ... on Company {
            name
          }
          ... on Person {
            fullName
          }
        }
      }
      customerType
      headcount
      stage
      highlights {
        category
        text
      }
      employeeHighlights {
        category
        text
      }
      location {
        location
        addressFormatted
      }
      tags {
        displayValue
        type
      }
      tagsV2 {
        displayValue
        type
      }
      tractionMetrics {
        headcountAdvisor {
          latestMetricValue
        }
        facebookFollowerCount {
          latestMetricValue
        }
        linkedinFollowerCount {
          latestMetricValue
        }
        instagramFollowerCount {
          latestMetricValue
        }
        twitterFollowerCount {
          latestMetricValue
        }
      }
      webTraffic
      likelihoodOfBacking
      employees(employeeSearchInput: {employeeGroupType: FOUNDERS, employeeStatus: ACTIVE_AND_NOT_ACTIVE}) {
        entityUrn
        experience {
          roleType
          title
          companyName
        }
        fullName
        highlights {
          category
          text
        }
        socials {
          linkedin {
            url
            followerCount
          }
        }
        education {
          school {
            name
          }
          degree
        }
        contact {
          emails
          phoneNumbers
        }
      }
    }
  }
}
        """

    def _post(self, query: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        resp = self.session.post(
            self.endpoint,
            json={"query": query, "variables": variables},
            timeout=30,
        )
        if resp.status_code >= 400:
            print("STATUS:", resp.status_code)
            print("Harmonic error payload:", resp.text) # temp debug
        resp.raise_for_status()
        data = resp.json()
        if "errors" in data:
            raise RuntimeError(f"Harmonic GraphQL error: {data['errors']}")
        return data

    def enrich_company_by_domain(self, website_domain: str) -> Dict[str, Any]:
        variables = {"identifiers": {"websiteDomain": website_domain}}
        data = self._post(self._enrich_company_query, variables)
        return data["data"]["enrichCompanyByIdentifiers"]
