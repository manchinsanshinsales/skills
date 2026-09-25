"""Segment / vertical / persona presets.

Keep in sync with references/icp-segments.md. Values are Apollo filter inputs.
"""

from __future__ import annotations

EMPLOYEE_RANGES = {
    "a": ["51,200", "201,500", "501,1000", "1001,5000"],
    "b": ["51,200", "201,500", "501,1000", "1001,5000", "5001,10000"],
}

# vertical -> (keyword tags, proof client)
VERTICALS = {
    "a": {
        "enterprise-ai": (["artificial intelligence", "enterprise search", "generative ai",
                           "machine learning", "knowledge management", "llm"], "Glean"),
        "saas": (["saas", "enterprise software", "b2b software", "cloud software",
                  "digital experience", "customer experience"], "Yext / Hootsuite"),
        "adtech-martech": (["adtech", "advertising technology", "martech", "marketing technology",
                            "marketing automation", "social media management", "cdp"],
                           "InMobi / Hootsuite"),
        "cyber": (["cybersecurity", "information security", "cloud security", "identity management",
                   "zero trust"], "Glean"),
        "devtools": (["developer tools", "devops", "observability", "api", "data infrastructure",
                      "database"], "Yext"),
        "hardware": (["hardware", "semiconductor", "iot", "robotics", "edge computing",
                      "networking equipment"], "Fluence"),
        "energy": (["energy storage", "renewable energy", "battery", "cleantech", "solar", "grid",
                    "ev charging"], "Fluence"),
        "deeptech": (["quantum computing", "photonics", "hpc", "scientific computing",
                      "space technology"], "Classiq"),
    },
    "b": {
        "gaming": (["gaming", "gaming hardware", "gaming peripherals", "esports", "game accessories",
                    "pc gaming"], "Razer"),
        "consumer-electronics": (["consumer electronics", "audio", "headphones", "wearables",
                                  "smart home", "cameras", "drones", "mobile accessories"], "Razer"),
        "beauty": (["beauty", "cosmetics", "skincare", "haircare", "fragrance", "personal care"],
                   "Razer"),
        "lifestyle": (["apparel", "footwear", "outdoor", "sporting goods", "toys", "home goods",
                       "direct to consumer", "dtc"], "Razer"),
    },
}

# Keywords that mark agencies / consultancies we do not sell to.
EXCLUDE_KEYWORDS = ["marketing agency", "advertising agency", "consulting", "staffing", "recruiting",
                    "outsourcing", "public relations", "pr agency", "translation services"]

# persona priority -> dict(titles, seniorities, locations or None)
PERSONAS = {
    "a": [
        {"priority": 1, "label": "Japan lead",
         "titles": ["Country Manager Japan", "General Manager Japan", "Head of Japan",
                    "Japan Country Lead", "President Japan", "Managing Director Japan",
                    "Japan Marketing Manager", "Marketing Manager Japan",
                    "Field Marketing Manager Japan"],
         "seniorities": ["c_suite", "vp", "head", "director", "manager"],
         "locations": ["Japan"]},
        {"priority": 2, "label": "APAC / International marketing",
         "titles": ["Head of APAC Marketing", "APAC Marketing Director", "VP Marketing APAC",
                    "Head of International Marketing", "Director of International Marketing",
                    "Head of Global Expansion", "Head of International Expansion",
                    "VP International", "VP International Growth", "General Manager APAC",
                    "Managing Director APAC", "VP APAC", "Head of Field Marketing APAC",
                    "Regional Marketing Manager APAC", "Head of International Partnerships"],
         "seniorities": ["c_suite", "vp", "head", "director"],
         "locations": None},
        {"priority": 3, "label": "HQ marketing leader",
         "titles": ["Chief Marketing Officer", "Chief Commercial Officer", "VP Marketing",
                    "Vice President of Marketing", "VP Global Marketing", "Head of Global Marketing",
                    "Director of Global Marketing", "Head of Marketing", "Head of Demand Generation",
                    "VP Demand Generation", "Director of Field Marketing", "Head of Partner Marketing"],
         "seniorities": ["c_suite", "vp", "head"],
         "locations": None},
    ],
    "b": [
        {"priority": 1, "label": "Japan marketing / PR",
         "titles": ["Marketing Manager Japan", "Japan Marketing Manager", "PR Manager Japan",
                    "Country Manager Japan", "Brand Manager Japan", "Community Manager Japan"],
         "seniorities": ["head", "director", "manager"],
         "locations": ["Japan"]},
        {"priority": 2, "label": "APAC PR / marketing",
         "titles": ["Head of APAC Marketing", "APAC PR Manager", "Regional Marketing Manager APAC",
                    "Head of Communications APAC", "Influencer Marketing Manager APAC",
                    "Head of International Partnerships"],
         "seniorities": ["vp", "head", "director", "manager"],
         "locations": None},
        {"priority": 3, "label": "HQ PR / brand leader",
         "titles": ["Head of PR", "Director of Communications", "VP Communications",
                    "Head of Global Communications", "Head of Influencer Marketing",
                    "Director of Influencer Marketing", "Influencer Marketing Lead",
                    "Head of Brand Marketing", "VP Brand Marketing", "VP Brand", "Head of Community",
                    "Head of Global PR"],
         "seniorities": ["c_suite", "vp", "head", "director"],
         "locations": None},
    ],
}

# Job-posting keywords that signal Japan / APAC investment (used by score_accounts.py).
JAPAN_JOB_KEYWORDS = ["japan", "tokyo", "osaka", "日本", "東京", "japanese", "apac", "country manager",
                      "localization", "localisation"]

APAC_LOCATIONS = ["Singapore", "Australia", "Hong Kong", "South Korea", "Taiwan", "New Zealand"]

# Romanized Japanese surnames used to guess the email language for Japan-based contacts.
JAPANESE_SURNAMES = {
    "sato", "suzuki", "takahashi", "tanaka", "watanabe", "ito", "yamamoto", "nakamura", "kobayashi",
    "kato", "yoshida", "yamada", "sasaki", "yamaguchi", "matsumoto", "inoue", "kimura", "hayashi",
    "shimizu", "saito", "yamazaki", "mori", "abe", "ikeda", "hashimoto", "yamashita", "ishikawa",
    "nakajima", "maeda", "fujita", "ogawa", "goto", "okada", "hasegawa", "murakami", "kondo",
    "ishii", "sakamoto", "endo", "aoki", "fujii", "nishimura", "fukuda", "ota", "miura", "fujiwara",
    "okamoto", "matsuda", "nakagawa", "nakano", "harada", "ono", "tamura", "takeuchi", "kaneko",
    "wada", "nakayama", "ishida", "ueda", "morita", "hara", "shibata", "sakai", "kudo", "yokoyama",
    "miyazaki", "miyamoto", "uchida", "takagi", "ando", "taniguchi", "ohno", "maruyama", "imai",
    "takada", "fujimoto", "takeda", "murata", "ueno", "sugiyama", "masuda", "sugawara", "hirano",
    "kojima", "otsuka", "chiba", "kubo", "matsui", "iwasaki", "sakurai", "kinoshita", "noguchi",
    "matsuo", "nomura", "kikuchi", "sano", "onishi", "sugimoto", "arai", "hamada", "ichikawa",
    "koyama", "takano", "kawasaki", "kawaguchi", "yoshikawa", "hirata", "nagai", "kawamura",
    "kikuchi", "oshima", "nishida", "shimada", "kawakami", "kanda", "hoshino", "yokota", "iwata",
}


def vertical_keywords(segment: str, verticals: list[str]) -> list[str]:
    tags: list[str] = []
    for v in verticals:
        if v not in VERTICALS[segment]:
            raise SystemExit(f"unknown vertical '{v}' for segment {segment}. "
                             f"Choose from: {', '.join(VERTICALS[segment])}")
        for t in VERTICALS[segment][v][0]:
            if t not in tags:
                tags.append(t)
    return tags


def guess_vertical(segment: str, keywords: str, industry: str = "") -> str:
    """Pick the vertical whose tags overlap most with the org's keywords."""
    text = f"{keywords} {industry}".lower()
    best, best_hits = "", 0
    for v, (tags, _proof) in VERTICALS[segment].items():
        hits = sum(1 for t in tags if t in text)
        if hits > best_hits:
            best, best_hits = v, hits
    return best


def proof_client(segment: str, vertical: str) -> str:
    return VERTICALS.get(segment, {}).get(vertical, ([], ""))[1]
