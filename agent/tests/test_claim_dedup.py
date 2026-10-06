"""Regression for multiple filings reporting an identical period value."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from norway_company_agent.claims import materialise_claims  # noqa: E402
from norway_company_agent.evidence import evidence  # noqa: E402


class ClaimDedupTests(unittest.TestCase):
    def test_same_filing_fact_is_once_and_currency_remains_distinct(self):
        period = {"fraDato": "2023-01-01", "tilDato": "2023-12-31"}
        profile = {
            "organisation_number": "975387011",
            "evidence": {
                "financials": evidence(
                    "financials", "available", "official_annual_accounts", "https://example.test/accounts",
                    content_sha256="a" * 64,
                    value={"records": [
                        {"record_id": 1, "period": period, "currency": "NOK", "revenue": 100},
                        {"record_id": 2, "period": period, "currency": "NOK", "revenue": 100},
                        {"record_id": 3, "period": period, "currency": "EUR", "revenue": 100},
                    ]},
                ),
            },
        }
        claims = materialise_claims(profile)
        self.assertEqual([claim["currency"] for claim in claims], ["NOK", "EUR"])
        self.assertEqual(len({claim["id"] for claim in claims}), len(claims))


if __name__ == "__main__":
    unittest.main()
