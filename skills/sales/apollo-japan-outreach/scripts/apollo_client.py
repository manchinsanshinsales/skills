#!/usr/bin/env python3
"""Minimal Apollo.io API client + CSV helpers shared by the pipeline scripts.

Standard library only. The API key is read from the APOLLO_API_KEY environment
variable and sent in the ``x-api-key`` header. Nothing is ever printed that
contains the key.

Offline testing: set APOLLO_FIXTURE_DIR to a directory containing JSON files
named after the endpoint path with slashes replaced by underscores
(e.g. ``mixed_companies_search.json``). The client then returns those files
instead of calling the network.
"""

from __future__ import annotations

import csv
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BASE_URL = "https://api.apollo.io/api/v1"

ACCOUNT_COLUMNS = [
    "organization_id", "name", "domain", "website", "linkedin_url", "hq_country", "hq_city",
    "employees", "industry", "keywords", "short_description", "founded_year",
    "latest_funding_stage", "latest_funding_date", "total_funding", "vertical",
    "japan_headcount", "apac_headcount", "japan_jobs", "score", "score_breakdown", "notes",
]

CONTACT_COLUMNS = [
    "person_id", "first_name", "last_name", "full_name", "title", "seniority", "persona_priority",
    "organization_id", "company", "domain", "person_country", "person_city", "linkedin_url",
    "email", "email_status", "language", "outreach_status",
]


class ApolloError(RuntimeError):
    def __init__(self, status: int, message: str):
        super().__init__(f"Apollo API error {status}: {message}")
        self.status = status


class ApolloClient:
    def __init__(self, api_key: str | None = None, sleep: float = 0.0, verbose: bool = False,
                 dry_run: bool = False, max_retries: int = 5):
        self.api_key = api_key or os.environ.get("APOLLO_API_KEY", "")
        self.fixture_dir = os.environ.get("APOLLO_FIXTURE_DIR")
        self.sleep = sleep
        self.verbose = verbose
        self.dry_run = dry_run
        self.max_retries = max_retries
        self.calls = 0
        if not self.api_key and not self.fixture_dir and not dry_run:
            sys.exit("APOLLO_API_KEY is not set. Export it in your shell (never paste the key into chat) "
                     "or use the Apollo UI export path described in references/apollo-api.md.")

    # ------------------------------------------------------------------ core
    def request(self, method: str, path: str, body: dict | None = None,
                params: dict | None = None) -> dict:
        path = path.strip("/")
        if self.dry_run:
            print(json.dumps({"method": method, "path": path, "params": params, "body": body},
                             ensure_ascii=False, indent=2))
            return {}
        if self.fixture_dir:
            return self._fixture(path, body, params)

        url = f"{BASE_URL}/{path}"
        if params:
            url += "?" + urllib.parse.urlencode(params, doseq=True)
        data = json.dumps(body).encode("utf-8") if body is not None else None
        headers = {
            "Content-Type": "application/json",
            "Cache-Control": "no-cache",
            "accept": "application/json",
            "x-api-key": self.api_key,
        }
        delay = 2.0
        for attempt in range(1, self.max_retries + 1):
            req = urllib.request.Request(url, data=data, headers=headers, method=method)
            try:
                with urllib.request.urlopen(req, timeout=60) as resp:
                    self.calls += 1
                    payload = json.loads(resp.read().decode("utf-8") or "{}")
                    if self.verbose:
                        self._print_rate_headers(resp.headers)
                    if self.sleep:
                        time.sleep(self.sleep)
                    return payload
            except urllib.error.HTTPError as e:
                text = e.read().decode("utf-8", errors="replace")
                if e.code == 429 or e.code >= 500:
                    retry_after = e.headers.get("retry-after")
                    wait = float(retry_after) if retry_after and retry_after.isdigit() else delay
                    if attempt == self.max_retries:
                        raise ApolloError(e.code, text[:300])
                    if self.verbose:
                        print(f"  [{e.code}] retrying in {wait:.0f}s ({attempt}/{self.max_retries})",
                              file=sys.stderr)
                    time.sleep(wait)
                    delay = min(delay * 2, 32)
                    continue
                raise ApolloError(e.code, text[:300])
            except urllib.error.URLError as e:
                if attempt == self.max_retries:
                    raise ApolloError(0, str(e.reason))
                time.sleep(delay)
                delay = min(delay * 2, 32)
        return {}

    def _fixture(self, path: str, body, params) -> dict:
        name = path.replace("/", "_") + ".json"
        fpath = os.path.join(self.fixture_dir, name)
        if not os.path.exists(fpath):
            # Allow fixtures keyed by org id for job postings: organizations_<id>_job_postings.json
            raise ApolloError(404, f"no fixture {name}")
        self.calls += 1
        with open(fpath, encoding="utf-8") as f:
            data = json.load(f)
        # Fixture files may be a list of {"match": {...}, "response": {...}} to vary by request.
        if isinstance(data, list):
            for entry in data:
                match = entry.get("match", {})
                if all(_deep_get(body or {}, k) == v for k, v in match.items()):
                    return entry["response"]
            return data[-1].get("response", {}) if data else {}
        return data

    @staticmethod
    def _print_rate_headers(headers) -> None:
        keys = ["x-rate-limit-minute", "x-minute-usage", "x-rate-limit-hourly", "x-hourly-usage",
                "x-rate-limit-daily", "x-daily-usage"]
        found = {k: headers.get(k) for k in keys if headers.get(k)}
        if found:
            print("  rate: " + ", ".join(f"{k.replace('x-', '')}={v}" for k, v in found.items()),
                  file=sys.stderr)

    # ------------------------------------------------------------- endpoints
    def search_organizations(self, filters: dict, page: int = 1, per_page: int = 100) -> dict:
        body = dict(filters)
        body.update({"page": page, "per_page": min(per_page, 100)})
        return self.request("POST", "mixed_companies/search", body)

    def search_people(self, filters: dict, page: int = 1, per_page: int = 25) -> dict:
        body = dict(filters)
        body.update({"page": page, "per_page": min(per_page, 100)})
        try:
            return self.request("POST", "mixed_people/api_search", body)
        except ApolloError as e:
            if e.status in (403, 404):
                return self.request("POST", "mixed_people/search", body)
            raise

    def count_people(self, organization_id: str, locations: list[str]) -> int:
        """Number of people at an org living in the given locations. No credits used."""
        res = self.search_people({"organization_ids": [organization_id],
                                  "person_locations": locations}, page=1, per_page=1)
        return int((res.get("pagination") or {}).get("total_entries") or 0)

    def bulk_match(self, details: list[dict]) -> list[dict | None]:
        assert len(details) <= 10, "bulk_match accepts at most 10 people per call"
        body = {"details": details, "reveal_personal_emails": False, "reveal_phone_number": False}
        res = self.request("POST", "people/bulk_match", body)
        return res.get("matches") or []

    def job_postings(self, organization_id: str) -> list[dict]:
        res = self.request("GET", f"organizations/{organization_id}/job_postings")
        return res.get("organization_job_postings") or res.get("job_postings") or []


def _deep_get(d: dict, dotted: str):
    cur = d
    for part in dotted.split("."):
        if isinstance(cur, dict):
            cur = cur.get(part)
        else:
            return None
    return cur


# ------------------------------------------------------------------ CSV I/O
def read_csv(path: str) -> list[dict]:
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: str, rows: list[dict], columns: list[str]) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({c: ("" if r.get(c) is None else r.get(c)) for c in columns})


def read_lines(path: str | None) -> set[str]:
    if not path:
        return set()
    with open(path, encoding="utf-8") as f:
        return {line.strip().lower() for line in f if line.strip() and not line.startswith("#")}


def normalize_domain(value: str | None) -> str:
    if not value:
        return ""
    v = value.strip().lower()
    v = v.replace("https://", "").replace("http://", "")
    v = v.split("/")[0]
    if v.startswith("www."):
        v = v[4:]
    return v


def org_to_account(org: dict, vertical: str = "") -> dict:
    return {
        "organization_id": org.get("id", ""),
        "name": org.get("name", ""),
        "domain": normalize_domain(org.get("primary_domain") or org.get("website_url")),
        "website": org.get("website_url", ""),
        "linkedin_url": org.get("linkedin_url", ""),
        "hq_country": org.get("country", ""),
        "hq_city": org.get("city", ""),
        "employees": org.get("estimated_num_employees", ""),
        "industry": org.get("industry", ""),
        "keywords": "; ".join(org.get("keywords") or []),
        "short_description": (org.get("short_description") or "").replace("\n", " ").strip(),
        "founded_year": org.get("founded_year", ""),
        "latest_funding_stage": org.get("latest_funding_stage", ""),
        "latest_funding_date": (org.get("latest_funding_round_date") or "")[:10],
        "total_funding": org.get("total_funding", ""),
        "vertical": vertical,
        "japan_headcount": "", "apac_headcount": "", "japan_jobs": "",
        "score": "", "score_breakdown": "", "notes": "",
    }
