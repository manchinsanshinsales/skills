# Apollo.io API リファレンス (このスキルで使う範囲)

公式: https://docs.apollo.io/reference (プランによりパラメータや上限が変わるので、迷ったら公式を確認)。
以下は 2026 年時点で確認した内容。このファイルは `scripts/apollo_client.py` の実装と対応している。

## 目次

1. [認証と共通事項](#認証と共通事項)
2. [Organization Search (企業検索)](#organization-search)
3. [People Search (人物検索)](#people-search)
4. [People Enrichment (メール取得)](#people-enrichment)
5. [Organization Enrichment / Job Postings](#organization-enrichment--job-postings)
6. [レート制限とクレジット](#レート制限とクレジット)
7. [スクリプトの使い方](#スクリプトの使い方)
8. [UI 代替手順 (API キーが無いとき)](#ui-代替手順)

---

## 認証と共通事項

- Base URL: `https://api.apollo.io/api/v1`
- 認証: HTTP ヘッダー `x-api-key: <APOLLO_API_KEY>`。ボディや URL にキーを入れない。
- ヘッダー: `Content-Type: application/json`, `Cache-Control: no-cache`
- API キーは環境変数 `APOLLO_API_KEY` から読む。**キーの値をチャットに貼らないようユーザーに伝える**
  (設定 → Integrations → API から発行。Master API key が必要な操作は usage stats のみ)。
- 配列パラメータは JSON 配列で送る (`"person_titles": ["VP Marketing"]`)。旧式の `person_titles[]=` 形式の
  クエリ文字列も受け付けるが、JSON ボディに統一する。
- 検索系 (`*/search`, `*/api_search`) は **メールと電話番号を返さない**。連絡先は Enrichment で取る。
- ページング: `page` (1 始まり), `per_page` (最大 100)。表示上限 50,000 件 (500 ページ)。
  レスポンスの `pagination.total_entries` / `pagination.total_pages` で件数確認。

---

## Organization Search

`POST /mixed_companies/search` — クレジット消費なし。

| パラメータ | 型 | 例 / 備考 |
|---|---|---|
| `organization_locations` | string[] | `["United States","Germany"]` HQ 所在地。国、州、都市 (`"Tokyo, Japan"`) |
| `organization_not_locations` | string[] | `["Japan"]` |
| `organization_num_employees_ranges` | string[] | `["51,200","201,500"]` カンマ区切りの下限,上限 |
| `q_organization_keyword_tags` | string[] | `["saas","cybersecurity"]` Apollo のキーワードタグ。いずれかに一致 |
| `q_organization_name` | string | 社名部分一致 |
| `organization_industry_tag_ids` | string[] | 業種 ID (UI から取得。キーワードタグの方が扱いやすい) |
| `revenue_range[min]` / `revenue_range[max]` | int | 年商 USD |
| `organization_latest_funding_stage_cd` | string[] | 資金調達ステージコード。UI の Funding フィルタで確認 (概ね `0`=Seed…`3`=Series B 以降。プラン差あり) |
| `latest_funding_amount_range[min]` / `[max]` | int | 直近調達額 |
| `currently_using_any_of_technology_uids` | string[] | 利用技術 (例 `["salesforce","hubspot"]`) |
| `page`, `per_page` | int | `per_page` 最大 100 |

主なレスポンスフィールド (`organizations[]`): `id`, `name`, `website_url`, `primary_domain`,
`linkedin_url`, `estimated_num_employees`, `industry`, `keywords[]`, `short_description`,
`founded_year`, `latest_funding_stage`, `latest_funding_round_date`, `total_funding`,
`country`, `city`, `raw_address`, `organization_headcount_six_month_growth` (プランによる)。

`accounts[]` (自社 CRM に取り込み済みの企業) も返ることがある。`organizations[]` を主に使い、
`accounts[]` は `organization_id` で結合する。

---

## People Search

`POST /mixed_people/api_search` — クレジット消費なし。(旧 `mixed_people/search` も動作するが、
新しいキーでは `api_search` を使う。スクリプトは `api_search` → 失敗時 `search` の順で試す。)

| パラメータ | 型 | 例 / 備考 |
|---|---|---|
| `person_titles` | string[] | `["VP Marketing","Country Manager Japan"]` |
| `include_similar_titles` | bool | `true` 推奨 (Apollo が類似役職を展開) |
| `person_seniorities` | string[] | `owner, founder, c_suite, partner, vp, head, director, manager, senior, entry, intern` |
| `person_locations` | string[] | `["Japan"]`, `["Tokyo, Japan"]` 現在の居住地 |
| `organization_locations` | string[] | 勤務先 HQ |
| `organization_ids` | string[] | Organization Search で得た `id` |
| `q_organization_domains_list` | string[] | `["glean.com"]` www 無し。最大 1,000 件 |
| `organization_num_employees_ranges` | string[] | 企業検索と同じ |
| `contact_email_status` | string[] | `verified, unverified, likely_to_engage, unavailable` |
| `q_keywords` | string | 自由文 |
| `page`, `per_page` | int | 最大 100 |

主なレスポンス (`people[]`): `id`, `first_name`, `last_name`, `name`, `title`, `seniority`,
`linkedin_url`, `city`, `state`, `country`, `email_status` (メール本体は無し),
`organization: {id, name, website_url, primary_domain, ...}`。

`contacts[]` (自社 CRM 済み) も返る。人数を数えるだけなら `per_page: 1` で `pagination.total_entries` を見る
(日本在住社員数のカウントはこれで行う。クレジット不要)。

---

## People Enrichment

### 単体 `POST /people/match`

| パラメータ | 備考 |
|---|---|
| `id` | People Search の `id` があればこれだけで良い (最も確実) |
| `first_name`, `last_name`, `name` | id が無いとき |
| `organization_name`, `domain` | 同上 |
| `email`, `linkedin_url` | 同上 |
| `reveal_personal_emails` | `false` にする (個人メールは日本の営業慣行上使わない。GDPR 圏は返らない) |
| `reveal_phone_number` | `false` (8 クレジット/件。電話は使わない) |

レスポンス `person`: `email`, `email_status` (`verified` / `unverified` / `likely_to_engage` /
`unavailable`), `title`, `linkedin_url`, `organization`, `phone_numbers[]` (要求時のみ)。

### 一括 `POST /people/bulk_match`

`{"details": [ {同上のパラメータ}, ... ]}` — **1 回 10 件まで**。レスポンス `matches[]` は入力と同じ順序
(該当なしは `null`)。スクリプトはこれを使う。

### クレジット

- 仕事用メールが返った件につき **1 クレジット**。既に `email` が判明している人物 (自社 CRM 上の contact)
  は再消費しないことが多いが、保証はない。
- `email_status: unavailable` は消費されない場合が多いが、`--max-credits` は「要求件数 = 消費上限」で計算する。
- 電話番号は 1 件 8 クレジット。既定で取得しない。

---

## Organization Enrichment / Job Postings

- `GET /organizations/enrich?domain=<domain>` — 企業の詳細 (`estimated_num_employees`, `industry`,
  `keywords`, `short_description`, `latest_funding_stage`, `total_funding`, `languages`, 拠点一覧)。
  クレジット消費なし (プランによる)。Search で十分な情報が取れているので既定では呼ばない。
- `POST /organizations/bulk_enrich` `{"domains": [...]}` — 10 件まで。
- `GET /organizations/{id}/job_postings` — 求人一覧 (`title`, `city`, `country`, `posted_at`, `url`)。
  **クレジットを消費する**ため `score_accounts.py --check-jobs` を付けたときだけ呼ぶ。
  日本シグナルの判定は `country == "Japan"` または `city` に Tokyo/Osaka、title に "Japan"/"日本" を含むもの。

---

## レート制限とクレジット

- 制限は **分 / 時 / 日** の 3 つの窓で、チーム単位 (キー単位ではない)。値はプランとエンドポイントで異なる。
- 超過時は HTTP 429、`retry-after` ヘッダー (秒) に従って待つ。スクリプトは指数バックオフ (2, 4, 8, 16 秒) で
  最大 5 回リトライする。
- レスポンスヘッダー `x-rate-limit-minute`, `x-minute-usage`, `x-rate-limit-hourly`, `x-hourly-usage`,
  `x-rate-limit-daily`, `x-daily-usage` で残量を確認できる。スクリプトは `--verbose` で表示する。
- 現在の制限値: Apollo の Settings → Integrations → API Keys → Usage、または `GET /usage_stats/api_usage_stats`
  (Master key 必須)。
- 目安として、企業検索 100 社 → 人物検索 100 回 (日本人数カウント) → 人物検索 30 回 (ペルソナ) は
  無料枠でも数分で終わる。クレジットを使うのは Enrichment と Job Postings だけ。

---

## スクリプトの使い方

すべて Python 3.9+ 標準ライブラリのみ。`APOLLO_API_KEY` を環境変数で渡す。

```bash
S=skills/sales/apollo-japan-outreach/scripts

# 1. 企業検索 (プリセット)。--dry-run で送るリクエストだけ表示
python3 $S/search_accounts.py --segment a --vertical enterprise-ai --vertical saas \
  --max-accounts 150 --out work/accounts_raw.csv
#    追加オプション: --hq "United States" (複数可) --employees "201,500" (複数可)
#                    --keyword "..." (プリセットに追加) --funding-stage 3 --exclude-domains existing.txt

# 2. 採点 (日本在住社員数と APAC をカウント。--check-jobs で求人も見る = クレジット消費)
python3 $S/score_accounts.py --in work/accounts_raw.csv --out work/accounts.csv --top 30 \
  --backlog work/accounts_backlog.csv [--check-jobs] [--min-score 55]

# 3. コンタクト抽出 (メール無し)
python3 $S/find_contacts.py --segment a --in work/accounts.csv --per-account 2 --out work/contacts_raw.csv

# 4. メール enrich (クレジット消費。上限必須)
python3 $S/enrich_contacts.py --in work/contacts_raw.csv --out work/contacts.csv --max-credits 60

# 代替: Apollo UI からエクスポートした CSV を同じスキーマに正規化
python3 $S/import_apollo_export.py --companies export_companies.csv --people export_people.csv \
  --out-accounts work/accounts.csv --out-contacts work/contacts.csv
```

出力 CSV のスキーマ:

`accounts*.csv`: `organization_id, name, domain, website, linkedin_url, hq_country, hq_city, employees,
industry, keywords, short_description, founded_year, latest_funding_stage, latest_funding_date,
total_funding, vertical, japan_headcount, apac_headcount, japan_jobs, score, score_breakdown, notes`

`contacts*.csv`: `person_id, first_name, last_name, full_name, title, seniority, persona_priority,
organization_id, company, domain, person_country, person_city, linkedin_url, email, email_status,
language, outreach_status`

`language` は `person_country == Japan` かつ日本語名らしい場合 `ja`、それ以外 `en` (メールの言語判断に使う)。

---

## UI 代替手順

API キーが無い / API プランに含まれない場合:

1. `references/icp-segments.md` の「Apollo UI でのフィルタ設定」どおりに Companies → People の順で
   検索し、CSV をエクスポートする。
2. `import_apollo_export.py` で正規化し、`score_accounts.py --offline` で採点する
   (`--offline` は API を呼ばず、CSV にある情報だけで採点。日本社員数は `Company Country` や
   Keywords から推定できないので 5 点固定になり、Step 5 の Web 調査で補う)。
3. 以降は同じ。

エラー対応:

| 症状 | 原因と対処 |
|---|---|
| 401 / `Invalid API key` | キー未設定 or 無効。`echo $APOLLO_API_KEY | cut -c1-4` で設定有無だけ確認 |
| 403 on `api_search` | プランに API 検索が含まれていない。UI 代替手順へ |
| 422 `per_page` | 100 超え。スクリプトは 100 に丸める |
| 429 | レート制限。スクリプトが自動で待つ。続くなら `--sleep 2` で間隔を空ける |
| `matches: [null, ...]` | Enrichment で該当なし。LinkedIn 経由の接触リストへ |
