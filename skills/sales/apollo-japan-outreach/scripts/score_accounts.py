#!/usr/bin/env python3
"""Step 2: add Japan-entry signals and score accounts 0-100.

Signals fetched from Apollo (no credits): Japan headcount, APAC headcount via people
search counts. With --check-jobs also pulls job postings (consumes credits).
With --offline nothing is fetched; only CSV fields are used.

Example:
  python3 score_accounts.py --in work/accounts_raw.csv --out work/accounts.csv --top 30 \
      --backlog work/accounts_backlog.csv
"""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from apollo_client import ACCOUNT_COLUMNS, ApolloClient, ApolloError, read_csv, write_csv  # noqa: E402
from presets import APAC_LOCATIONS, VERTICALS  # noqa: E402

LATE_STAGES = ("series b", "series c", "series d", "series e", "series f", "series g",
               "private equity", "ipo", "public", "acquired", "debt financing")
EARLY_STAGES = ("seed", "pre-seed", "angel", "series a", "crowdfunding")


def to_int(value) -> int | None:
    try:
        return int(float(str(value).replace(",", "")))
    except (TypeError, ValueError):
        return None


def size_score(employees: int | None) -> int:
    if employees is None:
        return 5
    if 201 <= employees <= 2000:
        return 30
    if 51 <= employees <= 200 or 2001 <= employees <= 5000:
        return 20
    return 5


def vertical_score(segment: str, keywords: str, industry: str, vertical: str) -> int:
    text = f"{keywords} {industry}".lower()
    if vertical and vertical in VERTICALS[segment]:
        tags = VERTICALS[segment][vertical][0]
        if any(t in text for t in tags):
            return 20
    for _v, (tags, _proof) in VERTICALS[segment].items():
        if any(t in text for t in tags):
            return 10
    return 0


def momentum_score(japan: int | None, apac: int | None, japan_jobs: int | None) -> int:
    if japan is None:
        base = 5
    elif 1 <= japan <= 30:
        base = 30
    elif 31 <= japan <= 100:
        base = 20
    elif japan == 0 and apac:
        base = 15
    elif japan > 100:
        base = 8
    else:
        base = 5
    if japan_jobs:
        base = min(30, base + 10)
    return base


def growth_score(stage: str, date_str: str) -> int:
    s = (stage or "").lower()
    if any(k in s for k in LATE_STAGES):
        return 10
    if date_str:
        try:
            d = dt.date.fromisoformat(date_str[:10])
            if (dt.date.today() - d).days <= 730:
                return 10
        except ValueError:
            pass
    if any(k in s for k in EARLY_STAGES):
        return 3
    return 5


def reach_score(contact_count: int | None) -> int:
    if contact_count is None:
        return 5
    return 10 if contact_count >= 2 else (5 if contact_count == 1 else 0)


def japan_job_count(postings: list[dict]) -> int:
    n = 0
    for j in postings:
        text = " ".join(str(j.get(k, "")) for k in ("title", "city", "country", "state")).lower()
        if "japan" in text or "tokyo" in text or "osaka" in text or "日本" in text or "東京" in text:
            n += 1
    return n


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--in", dest="inp", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--backlog", help="where to write accounts below the threshold")
    p.add_argument("--segment", choices=["a", "b"], default="a")
    p.add_argument("--top", type=int, default=30)
    p.add_argument("--min-score", type=int, default=55)
    p.add_argument("--max-japan-headcount", type=int, default=None,
                   help="drop accounts with more Japan staff than this (default 100 for a, 300 for b)")
    p.add_argument("--check-jobs", action="store_true", help="also pull job postings (uses credits)")
    p.add_argument("--contacts", help="contacts CSV from find_contacts.py to compute reachability")
    p.add_argument("--offline", action="store_true", help="do not call Apollo")
    p.add_argument("--sleep", type=float, default=0.0)
    p.add_argument("--verbose", action="store_true")
    args = p.parse_args()

    max_jp = args.max_japan_headcount or (100 if args.segment == "a" else 300)
    accounts = read_csv(args.inp)
    client = None if args.offline else ApolloClient(sleep=args.sleep, verbose=args.verbose)

    contact_counts: dict[str, int] = collections.Counter()
    if args.contacts:
        for c in read_csv(args.contacts):
            for key in {c.get("organization_id", ""), c.get("domain", "")}:
                if key:
                    contact_counts[key] += 1

    credits = 0
    for i, acc in enumerate(accounts, 1):
        org_id = acc.get("organization_id", "")
        if client and org_id:
            try:
                if acc.get("japan_headcount") in ("", None):
                    acc["japan_headcount"] = client.count_people(org_id, ["Japan"])
                if acc.get("apac_headcount") in ("", None):
                    acc["apac_headcount"] = client.count_people(org_id, APAC_LOCATIONS)
                if args.check_jobs and acc.get("japan_jobs") in ("", None):
                    postings = client.job_postings(org_id)
                    credits += 1
                    acc["japan_jobs"] = japan_job_count(postings)
            except ApolloError as e:
                acc["notes"] = (acc.get("notes", "") + f" signal-error:{e.status}").strip()
                if args.verbose:
                    print(f"  {acc.get('name')}: {e}", file=sys.stderr)
        if args.verbose:
            print(f"[{i}/{len(accounts)}] {acc.get('name')}: JP={acc.get('japan_headcount')} "
                  f"APAC={acc.get('apac_headcount')} jobs={acc.get('japan_jobs')}", file=sys.stderr)

        employees = to_int(acc.get("employees"))
        japan = to_int(acc.get("japan_headcount"))
        apac = to_int(acc.get("apac_headcount"))
        jobs = to_int(acc.get("japan_jobs"))
        contacts = None
        if args.contacts:
            contacts = max(contact_counts.get(org_id, 0), contact_counts.get(acc.get("domain", ""), 0))

        parts = {
            "size": size_score(employees),
            "vertical": vertical_score(args.segment, acc.get("keywords", ""), acc.get("industry", ""),
                                       acc.get("vertical", "")),
            "momentum": momentum_score(japan, apac, jobs),
            "growth": growth_score(acc.get("latest_funding_stage", ""), acc.get("latest_funding_date", "")),
            "reach": reach_score(contacts),
        }
        acc["score"] = sum(parts.values())
        acc["score_breakdown"] = " ".join(f"{k}={v}" for k, v in parts.items())
        if japan is not None and japan > max_jp:
            acc["score"] = min(acc["score"], args.min_score - 1)
            acc["notes"] = (acc.get("notes", "") + f" japan_headcount>{max_jp}").strip()

    accounts.sort(key=lambda a: (-int(a["score"]), a.get("name", "")))
    selected = [a for a in accounts if int(a["score"]) >= args.min_score][: args.top]
    selected_ids = {id(a) for a in selected}
    backlog = [a for a in accounts if id(a) not in selected_ids]

    write_csv(args.out, selected, ACCOUNT_COLUMNS)
    if args.backlog:
        write_csv(args.backlog, backlog, ACCOUNT_COLUMNS)
    calls = client.calls if client else 0
    print(f"Scored {len(accounts)} accounts: {len(selected)} selected (>= {args.min_score}, top {args.top}) "
          f"-> {args.out}; {len(backlog)} to backlog; API calls: {calls}; credits used: {credits}",
          file=sys.stderr)


if __name__ == "__main__":
    main()
