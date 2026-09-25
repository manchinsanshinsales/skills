#!/usr/bin/env python3
"""Normalize CSVs exported from the Apollo UI into the pipeline's accounts/contacts schema.

Use when there is no API key. Column names are matched case-insensitively against
common Apollo export headers; unknown columns are ignored.

Example:
  python3 import_apollo_export.py --companies export_companies.csv --people export_people.csv \
      --out-accounts work/accounts.csv --out-contacts work/contacts.csv --segment a
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from apollo_client import ACCOUNT_COLUMNS, CONTACT_COLUMNS, normalize_domain, read_csv, write_csv  # noqa: E402
from find_contacts import guess_language  # noqa: E402
from presets import guess_vertical  # noqa: E402

ACCOUNT_ALIASES = {
    "organization_id": ["apollo account id", "account id", "organization id", "id"],
    "name": ["company", "company name", "name", "account name"],
    "website": ["website", "company website", "website url"],
    "linkedin_url": ["company linkedin url", "linkedin url", "linkedin"],
    "hq_country": ["company country", "country", "hq country"],
    "hq_city": ["company city", "city", "hq city"],
    "employees": ["# employees", "employees", "number of employees", "estimated num employees"],
    "industry": ["industry", "industries"],
    "keywords": ["keywords", "company keywords"],
    "short_description": ["short description", "description", "seo description"],
    "founded_year": ["founded year", "founded"],
    "latest_funding_stage": ["latest funding", "latest funding stage", "last raised at"],
    "latest_funding_date": ["latest funding date", "last funding date"],
    "total_funding": ["total funding", "total funding amount"],
}

CONTACT_ALIASES = {
    "person_id": ["apollo contact id", "contact id", "person id", "id"],
    "first_name": ["first name", "firstname"],
    "last_name": ["last name", "lastname"],
    "title": ["title", "job title"],
    "seniority": ["seniority", "management level"],
    "organization_id": ["apollo account id", "account id", "organization id"],
    "company": ["company", "company name", "company name for emails", "account name"],
    "domain": ["website", "company website", "company domain", "domain"],
    "person_country": ["country", "person country"],
    "person_city": ["city", "person city"],
    "linkedin_url": ["person linkedin url", "linkedin url", "linkedin"],
    "email": ["email", "work email", "primary email"],
    "email_status": ["email status", "primary email status", "email verification status"],
}


def pick(row: dict, aliases: list[str]) -> str:
    lowered = {k.strip().lower(): v for k, v in row.items() if k}
    for a in aliases:
        if a in lowered and lowered[a] not in (None, ""):
            return str(lowered[a]).strip()
    return ""


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--companies", help="Apollo companies export CSV")
    p.add_argument("--people", help="Apollo people export CSV")
    p.add_argument("--out-accounts")
    p.add_argument("--out-contacts")
    p.add_argument("--segment", choices=["a", "b"], default="a")
    args = p.parse_args()
    if not args.companies and not args.people:
        p.error("give --companies and/or --people")

    accounts_by_domain: dict[str, dict] = {}
    if args.companies:
        for row in read_csv(args.companies):
            acc = {c: "" for c in ACCOUNT_COLUMNS}
            for col, aliases in ACCOUNT_ALIASES.items():
                acc[col] = pick(row, aliases)
            acc["domain"] = normalize_domain(acc["website"])
            acc["vertical"] = guess_vertical(args.segment, acc["keywords"], acc["industry"])
            key = acc["domain"] or acc["name"].lower()
            if key and key not in accounts_by_domain:
                accounts_by_domain[key] = acc

    contacts: list[dict] = []
    if args.people:
        for row in read_csv(args.people):
            c = {col: "" for col in CONTACT_COLUMNS}
            for col, aliases in CONTACT_ALIASES.items():
                c[col] = pick(row, aliases)
            c["domain"] = normalize_domain(c["domain"])
            c["full_name"] = f"{c['first_name']} {c['last_name']}".strip()
            c["persona_priority"] = 1 if "japan" in (c["person_country"] or "").lower() else 3
            c["language"] = guess_language({"first_name": c["first_name"], "last_name": c["last_name"],
                                            "country": c["person_country"]})
            status = (c["email_status"] or "").lower().replace(" ", "_")
            c["email_status"] = status
            c["outreach_status"] = "ready" if c["email"] and status in ("verified", "likely_to_engage") \
                else ("linkedin" if not c["email"] else "hold")
            contacts.append(c)
            # Create a stub account if the companies export did not include it.
            key = c["domain"] or c["company"].lower()
            if key and key not in accounts_by_domain:
                acc = {col: "" for col in ACCOUNT_COLUMNS}
                acc.update({"name": c["company"], "domain": c["domain"], "website": c["domain"],
                            "organization_id": c["organization_id"],
                            "hq_country": pick(row, ["company country"]),
                            "employees": pick(row, ["# employees", "employees"]),
                            "industry": pick(row, ["industry"]), "keywords": pick(row, ["keywords"])})
                acc["vertical"] = guess_vertical(args.segment, acc["keywords"], acc["industry"])
                accounts_by_domain[key] = acc

    for c in contacts:
        acc = accounts_by_domain.get(c["domain"] or c["company"].lower())
        if acc and not c["organization_id"]:
            c["organization_id"] = acc["organization_id"]

    if args.out_accounts:
        write_csv(args.out_accounts, list(accounts_by_domain.values()), ACCOUNT_COLUMNS)
        print(f"Saved {len(accounts_by_domain)} accounts -> {args.out_accounts}", file=sys.stderr)
    if args.out_contacts:
        write_csv(args.out_contacts, contacts, CONTACT_COLUMNS)
        print(f"Saved {len(contacts)} contacts -> {args.out_contacts}", file=sys.stderr)


if __name__ == "__main__":
    main()
