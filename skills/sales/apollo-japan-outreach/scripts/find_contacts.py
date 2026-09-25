#!/usr/bin/env python3
"""Step 3: find decision makers per account via People Search (no credits, no emails yet).

Example:
  python3 find_contacts.py --segment a --in work/accounts.csv --per-account 2 --out work/contacts_raw.csv
"""

from __future__ import annotations

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from apollo_client import CONTACT_COLUMNS, ApolloClient, ApolloError, normalize_domain, read_csv, write_csv  # noqa: E402
from presets import JAPANESE_SURNAMES, PERSONAS  # noqa: E402

CJK = re.compile(r"[぀-ヿ一-鿿]")


def guess_language(person: dict) -> str:
    country = (person.get("country") or "").lower()
    name = f"{person.get('first_name', '')} {person.get('last_name', '')}"
    if CJK.search(name):
        return "ja"
    if "japan" in country:
        last = (person.get("last_name") or "").lower().strip()
        if last in JAPANESE_SURNAMES:
            return "ja"
    return "en"


def person_to_contact(person: dict, priority: int, account: dict) -> dict:
    org = person.get("organization") or {}
    return {
        "person_id": person.get("id", ""),
        "first_name": person.get("first_name", ""),
        "last_name": person.get("last_name", ""),
        "full_name": person.get("name") or f"{person.get('first_name', '')} {person.get('last_name', '')}".strip(),
        "title": person.get("title", ""),
        "seniority": person.get("seniority", ""),
        "persona_priority": priority,
        "organization_id": account.get("organization_id") or org.get("id", ""),
        "company": account.get("name") or org.get("name", ""),
        "domain": account.get("domain") or normalize_domain(org.get("primary_domain") or org.get("website_url")),
        "person_country": person.get("country", ""),
        "person_city": person.get("city", ""),
        "linkedin_url": person.get("linkedin_url", ""),
        "email": person.get("email") or "",
        "email_status": person.get("email_status") or "",
        "language": guess_language(person),
        "outreach_status": "pending",
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--segment", choices=["a", "b"], required=True)
    p.add_argument("--in", dest="inp", required=True, help="accounts.csv")
    p.add_argument("--out", help="output CSV (required unless --dry-run)")
    p.add_argument("--per-account", type=int, default=2)
    p.add_argument("--priorities", default="1,2,3", help="persona priorities to use, in order")
    p.add_argument("--any-email-status", action="store_true",
                   help="do not restrict to verified / likely_to_engage")
    p.add_argument("--sleep", type=float, default=0.0)
    p.add_argument("--verbose", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    if not args.out and not args.dry_run:
        p.error("--out is required")
    priorities = [int(x) for x in args.priorities.split(",") if x.strip()]
    personas = [pp for pp in PERSONAS[args.segment] if pp["priority"] in priorities]
    accounts = read_csv(args.inp)
    client = ApolloClient(sleep=args.sleep, verbose=args.verbose, dry_run=args.dry_run)

    contacts: list[dict] = []
    seen_people: set[str] = set()
    empty_accounts: list[str] = []
    for i, acc in enumerate(accounts, 1):
        found: list[dict] = []
        for persona in personas:
            if len(found) >= args.per_account:
                break
            filters: dict = {
                "person_titles": persona["titles"],
                "include_similar_titles": True,
                "person_seniorities": persona["seniorities"],
            }
            if acc.get("organization_id"):
                filters["organization_ids"] = [acc["organization_id"]]
            elif acc.get("domain"):
                filters["q_organization_domains_list"] = [acc["domain"]]
            else:
                continue
            if persona["locations"]:
                filters["person_locations"] = persona["locations"]
            if not args.any_email_status:
                filters["contact_email_status"] = ["verified", "likely_to_engage"]
            try:
                res = client.search_people(filters, page=1, per_page=10)
            except ApolloError as e:
                print(f"  {acc.get('name')}: persona {persona['priority']} failed: {e}", file=sys.stderr)
                continue
            if args.dry_run:
                continue
            people = (res.get("people") or []) + (res.get("contacts") or [])
            for person in people:
                pid = person.get("id") or person.get("linkedin_url")
                if not pid or pid in seen_people:
                    continue
                seen_people.add(pid)
                found.append(person_to_contact(person, persona["priority"], acc))
                if len(found) >= args.per_account:
                    break
        if args.verbose:
            print(f"[{i}/{len(accounts)}] {acc.get('name')}: {len(found)} contact(s) "
                  f"{[c['title'] for c in found]}", file=sys.stderr)
        if not found:
            empty_accounts.append(acc.get("name", acc.get("domain", "?")))
        contacts.extend(found)

    if args.dry_run:
        return
    write_csv(args.out, contacts, CONTACT_COLUMNS)
    print(f"Saved {len(contacts)} contacts for {len(accounts) - len(empty_accounts)}/{len(accounts)} accounts "
          f"-> {args.out}; API calls: {client.calls}; credits used: 0", file=sys.stderr)
    if empty_accounts:
        print("No persona match (try --any-email-status or LinkedIn): " + ", ".join(empty_accounts),
              file=sys.stderr)


if __name__ == "__main__":
    main()
