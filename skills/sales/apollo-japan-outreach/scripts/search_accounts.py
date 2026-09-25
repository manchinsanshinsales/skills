#!/usr/bin/env python3
"""Step 1: search Apollo for target companies (no credits used).

Example:
  python3 search_accounts.py --segment a --vertical enterprise-ai --vertical saas \
      --max-accounts 150 --out work/accounts_raw.csv

Use --dry-run to print the request body without calling the API.
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from apollo_client import (ACCOUNT_COLUMNS, ApolloClient, ApolloError, normalize_domain,  # noqa: E402
                           org_to_account, read_lines, write_csv)
from presets import EMPLOYEE_RANGES, EXCLUDE_KEYWORDS, VERTICALS, guess_vertical, vertical_keywords  # noqa: E402


def build_filters(args) -> dict:
    segment = args.segment
    filters: dict = {
        "organization_not_locations": ["Japan"] + list(args.not_hq or []),
        "organization_num_employees_ranges": list(args.employees or EMPLOYEE_RANGES[segment]),
    }
    if args.hq:
        filters["organization_locations"] = list(args.hq)
    tags = vertical_keywords(segment, args.vertical) if args.vertical else []
    tags += list(args.keyword or [])
    if tags:
        filters["q_organization_keyword_tags"] = tags
    if args.funding_stage:
        filters["organization_latest_funding_stage_cd"] = list(args.funding_stage)
    if args.min_revenue is not None:
        filters["revenue_range[min]"] = args.min_revenue
    if args.max_revenue is not None:
        filters["revenue_range[max]"] = args.max_revenue
    if args.name:
        filters["q_organization_name"] = args.name
    return filters


def is_excluded(account: dict, exclude_keywords: list[str]) -> str:
    text = f"{account['keywords']} {account['industry']} {account['short_description']}".lower()
    for kw in exclude_keywords:
        if kw in text:
            return kw
    return ""


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--segment", choices=["a", "b"], required=True, help="a = B2B tech, b = consumer brand")
    p.add_argument("--vertical", action="append",
                   help=f"repeatable. a: {', '.join(VERTICALS['a'])} | b: {', '.join(VERTICALS['b'])}")
    p.add_argument("--keyword", action="append", help="extra q_organization_keyword_tags (repeatable)")
    p.add_argument("--hq", action="append", help="organization_locations (repeatable)")
    p.add_argument("--not-hq", action="append", help="extra organization_not_locations (Japan always excluded)")
    p.add_argument("--employees", action="append", help='employee ranges like "201,500" (repeatable)')
    p.add_argument("--funding-stage", action="append", help="organization_latest_funding_stage_cd values")
    p.add_argument("--min-revenue", type=int)
    p.add_argument("--max-revenue", type=int)
    p.add_argument("--name", help="q_organization_name partial match")
    p.add_argument("--max-accounts", type=int, default=100)
    p.add_argument("--exclude-domains", help="file with one domain per line to skip (existing clients)")
    p.add_argument("--no-default-excludes", action="store_true",
                   help="do not drop agencies/consultancies by keyword")
    p.add_argument("--out", help="output CSV (required unless --dry-run)")
    p.add_argument("--sleep", type=float, default=0.0)
    p.add_argument("--verbose", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    if not args.vertical and not args.keyword and not args.name:
        p.error("give at least one --vertical, --keyword or --name")
    if not args.out and not args.dry_run:
        p.error("--out is required")

    filters = build_filters(args)
    client = ApolloClient(sleep=args.sleep, verbose=args.verbose, dry_run=args.dry_run)
    if args.dry_run:
        client.search_organizations(filters, page=1, per_page=100)
        return

    exclude_domains = read_lines(args.exclude_domains)
    exclude_keywords = [] if args.no_default_excludes else EXCLUDE_KEYWORDS
    per_page = min(100, args.max_accounts)
    accounts: list[dict] = []
    seen: set[str] = set()
    dropped = {"excluded_domain": 0, "excluded_keyword": 0, "duplicate": 0}
    page, total_pages = 1, 1
    while page <= total_pages and len(accounts) < args.max_accounts:
        try:
            res = client.search_organizations(filters, page=page, per_page=per_page)
        except ApolloError as e:
            sys.exit(f"search failed on page {page}: {e}")
        pagination = res.get("pagination") or {}
        total_pages = int(pagination.get("total_pages") or 1)
        if page == 1:
            print(f"Apollo reports {pagination.get('total_entries', '?')} matching organizations "
                  f"({total_pages} pages of {per_page}).", file=sys.stderr)
        orgs = res.get("organizations") or []
        if not orgs:
            break
        for org in orgs:
            acc = org_to_account(org)
            key = acc["organization_id"] or acc["domain"]
            if not key or key in seen:
                dropped["duplicate"] += 1
                continue
            seen.add(key)
            if acc["domain"] in exclude_domains or normalize_domain(acc["website"]) in exclude_domains:
                dropped["excluded_domain"] += 1
                continue
            hit = is_excluded(acc, exclude_keywords)
            if hit:
                dropped["excluded_keyword"] += 1
                continue
            acc["vertical"] = guess_vertical(args.segment, acc["keywords"], acc["industry"]) or \
                (args.vertical[0] if args.vertical else "")
            accounts.append(acc)
            if len(accounts) >= args.max_accounts:
                break
        page += 1

    write_csv(args.out, accounts, ACCOUNT_COLUMNS)
    print(f"Saved {len(accounts)} accounts to {args.out} "
          f"(dropped: {dropped}; API calls: {client.calls}; credits used: 0)", file=sys.stderr)


if __name__ == "__main__":
    main()
