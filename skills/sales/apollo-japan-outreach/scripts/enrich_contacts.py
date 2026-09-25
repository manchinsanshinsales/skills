#!/usr/bin/env python3
"""Step 4: reveal work emails with People Bulk Enrichment. CONSUMES CREDITS.

One credit per revealed work email (phone numbers are never requested).
--max-credits is required so the run can never exceed the agreed budget.

Example:
  python3 enrich_contacts.py --in work/contacts_raw.csv --out work/contacts.csv --max-credits 60
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from apollo_client import CONTACT_COLUMNS, ApolloClient, ApolloError, read_csv, write_csv  # noqa: E402

SEND_OK = {"verified", "likely_to_engage"}


def outreach_status(email: str, status: str) -> str:
    if not email or status == "unavailable":
        return "linkedin"          # no work email: reach out via LinkedIn instead
    if status in SEND_OK:
        return "ready"
    return "hold"                  # unverified: do not send, risk of bounce


def match_details(contact: dict) -> dict:
    d: dict = {}
    if contact.get("person_id"):
        d["id"] = contact["person_id"]
    if contact.get("first_name"):
        d["first_name"] = contact["first_name"]
    if contact.get("last_name"):
        d["last_name"] = contact["last_name"]
    if contact.get("company"):
        d["organization_name"] = contact["company"]
    if contact.get("domain"):
        d["domain"] = contact["domain"]
    if contact.get("linkedin_url"):
        d["linkedin_url"] = contact["linkedin_url"]
    return d


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--in", dest="inp", required=True)
    p.add_argument("--out", help="output CSV (required unless --dry-run)")
    p.add_argument("--max-credits", type=int, required=True, help="hard cap on people to enrich")
    p.add_argument("--only-status", default="ready,pending",
                   help="outreach_status values eligible for enrichment (default ready,pending)")
    p.add_argument("--sleep", type=float, default=0.5)
    p.add_argument("--verbose", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    if not args.out and not args.dry_run:
        p.error("--out is required")
    contacts = read_csv(args.inp)
    eligible_status = {s.strip() for s in args.only_status.split(",")}
    todo = [c for c in contacts if not c.get("email") and c.get("outreach_status", "pending") in eligible_status]
    todo = todo[: args.max_credits]
    print(f"{len(contacts)} contacts loaded, {len(todo)} to enrich (cap {args.max_credits} credits).",
          file=sys.stderr)
    if not todo:
        write_csv(args.out, contacts, CONTACT_COLUMNS)
        return

    client = ApolloClient(sleep=args.sleep, verbose=args.verbose, dry_run=args.dry_run)
    revealed = 0
    for start in range(0, len(todo), 10):
        batch = todo[start:start + 10]
        try:
            matches = client.bulk_match([match_details(c) for c in batch])
        except ApolloError as e:
            print(f"  batch {start // 10 + 1} failed: {e}", file=sys.stderr)
            continue
        if args.dry_run:
            continue
        for contact, person in zip(batch, matches):
            if not person:
                # Apollo could not match this person: keep the row, route to LinkedIn.
                contact["email_status"] = "no_match"
                contact["outreach_status"] = outreach_status("", "unavailable")
                continue
            contact["email"] = person.get("email") or ""
            contact["email_status"] = person.get("email_status") or contact.get("email_status") or ""
            if person.get("title") and not contact.get("title"):
                contact["title"] = person["title"]
            if person.get("linkedin_url") and not contact.get("linkedin_url"):
                contact["linkedin_url"] = person["linkedin_url"]
            contact["outreach_status"] = outreach_status(contact["email"], contact["email_status"])
            if contact["email"]:
                revealed += 1
        if args.verbose:
            print(f"  batch {start // 10 + 1}: {revealed} emails so far", file=sys.stderr)

    if args.dry_run:
        return
    for c in contacts:
        if c.get("email") and c.get("outreach_status") in ("", "pending"):
            c["outreach_status"] = outreach_status(c["email"], c.get("email_status", ""))
    write_csv(args.out, contacts, CONTACT_COLUMNS)
    ready = sum(1 for c in contacts if c.get("outreach_status") == "ready")
    print(f"Saved {args.out}: {revealed} emails revealed (<= {len(todo)} credits), "
          f"{ready} contacts ready to send, API calls: {client.calls}", file=sys.stderr)


if __name__ == "__main__":
    main()
