# ICP セグメント定義・Apollo フィルタ・ペルソナ・スコアリング

`scripts/search_accounts.py` と `scripts/find_contacts.py` のプリセットはこのファイルと同じ値を持つ。
プリセットを変えるときは両方を更新する。

## 目次

1. [セグメント A: 海外 B2B テック企業 (日本マーケティング)](#セグメント-a)
2. [セグメント B: 海外コンシューマブランド (日本 PR / インフルエンサー)](#セグメント-b)
3. [共通の除外条件](#共通の除外条件)
4. [日本進出シグナル](#日本進出シグナル)
5. [スコアリング (0〜100)](#スコアリング)
6. [Apollo UI でのフィルタ設定](#apollo-ui-でのフィルタ設定)

---

## セグメント A

**誰か**: 日本で B2B マーケティングを立ち上げたい、または小さな日本チームを本社マーケが支えている
海外テック企業。日本法人があっても「営業 2〜3 名 + カントリーマネージャー」で、マーケ担当が
いない状態が典型。

### 企業フィルタ (organization search)

| Apollo パラメータ | 値 | 理由 |
|---|---|---|
| `organization_not_locations` | `["Japan"]` | 日本 HQ 企業は対象外 |
| `organization_locations` | 指定しない (全世界)。絞るなら `["United States","United Kingdom","Germany","France","Netherlands","Sweden","Israel","Singapore","Australia","Canada","India","South Korea","Taiwan"]` | 実績のある本社所在国 |
| `organization_num_employees_ranges` | `["51,200","201,500","501,1000","1001,5000"]` | 50 名未満は予算なし、5,000 名超は日本に既存マーケ部門 |
| `q_organization_keyword_tags` | バーティカル別 (下表) | Apollo のキーワードタグは OR 条件 |
| `organization_latest_funding_stage_cd` (任意) | `["3","4","5","6","7","10"]` = Series B〜E / Private Equity / IPO 相当 | 日本進出予算があるステージ (値はプランにより異なるため `references/apollo-api.md` 参照) |

### バーティカル別キーワードタグ

| vertical | `q_organization_keyword_tags` | 引く実績 |
|---|---|---|
| `enterprise-ai` | `artificial intelligence, enterprise search, generative ai, machine learning, knowledge management, llm` | Glean |
| `saas` | `saas, enterprise software, b2b software, cloud software, digital experience, customer experience` | Yext / Hootsuite |
| `adtech-martech` | `adtech, advertising technology, martech, marketing technology, marketing automation, social media management, cdp` | InMobi / Hootsuite |
| `cyber` | `cybersecurity, information security, cloud security, identity management, zero trust` | Glean (エンタープライズ営業モデルが近い) |
| `devtools` | `developer tools, devops, observability, api, data infrastructure, database` | Yext (テック系 SaaS) |
| `hardware` | `hardware, semiconductor, iot, robotics, edge computing, networking equipment` | Fluence (ハード + 商社チャネル) |
| `energy` | `energy storage, renewable energy, battery, cleantech, solar, grid, ev charging` | Fluence |
| `deeptech` | `quantum computing, photonics, hpc, scientific computing, space technology` | Classiq |

### ペルソナ (people search)

優先度順。`person_titles` は `include_similar_titles: true` で使う。

| 優先 | 役割 | `person_titles` | `person_seniorities` |
|---|---|---|---|
| 1 | 日本責任者 | `Country Manager Japan, General Manager Japan, Head of Japan, Japan Country Lead, President Japan, Managing Director Japan, Japan Marketing Manager, Marketing Manager Japan, Field Marketing Manager Japan` | `c_suite, vp, head, director, manager` |
| 2 | APAC / International マーケ | `Head of APAC Marketing, APAC Marketing Director, VP Marketing APAC, Head of International Marketing, Director of International Marketing, Head of Global Expansion, Head of International Expansion, VP International, General Manager APAC, Head of Field Marketing APAC, Regional Marketing Manager APAC` | `c_suite, vp, head, director` |
| 3 | 本社マーケ責任者 | `Chief Marketing Officer, VP Marketing, Vice President of Marketing, Head of Marketing, Head of Demand Generation, VP Demand Generation, Director of Field Marketing, Head of Partner Marketing` | `c_suite, vp, head` |

補足: 優先 1 を探すときは `person_locations: ["Japan"]` も付ける。優先 2 は `person_locations` に
`["Singapore","Australia","Hong Kong","South Korea","Japan"]` を付けると精度が上がる。

---

## セグメント B

**誰か**: 日本で売っている、または売り始めたい海外コンシューマブランドで、日本のメディア露出と
クリエイター施策を本社 PR / ブランドチームが英語圏の代理店経由で回している状態。

### 企業フィルタ

| Apollo パラメータ | 値 |
|---|---|
| `organization_not_locations` | `["Japan"]` |
| `organization_num_employees_ranges` | `["51,200","201,500","501,1000","1001,5000","5001,10000"]` (コンシューマは大手でも日本 PR を外注する) |
| `q_organization_keyword_tags` | バーティカル別 (下表) |

| vertical | `q_organization_keyword_tags` | 引く実績 |
|---|---|---|
| `gaming` | `gaming, gaming hardware, gaming peripherals, esports, game accessories, pc gaming` | Razer |
| `consumer-electronics` | `consumer electronics, audio, headphones, wearables, smart home, cameras, drones, mobile accessories` | Razer |
| `beauty` | `beauty, cosmetics, skincare, haircare, fragrance, personal care` | Razer (インフルエンサー運用の型が同じ) |
| `lifestyle` | `apparel, footwear, outdoor, sporting goods, toys, home goods, direct to consumer, dtc` | Razer |

### ペルソナ

| 優先 | 役割 | `person_titles` | `person_seniorities` |
|---|---|---|---|
| 1 | 日本マーケ / PR | `Marketing Manager Japan, Japan Marketing Manager, PR Manager Japan, Country Manager Japan, Brand Manager Japan, Community Manager Japan` | `head, director, manager` |
| 2 | APAC PR / マーケ | `Head of APAC Marketing, APAC PR Manager, Regional Marketing Manager APAC, Head of Communications APAC, Influencer Marketing Manager APAC` | `vp, head, director, manager` |
| 3 | 本社 PR / ブランド | `Head of PR, Director of Communications, VP Communications, Head of Global Communications, Head of Influencer Marketing, Director of Influencer Marketing, Head of Brand Marketing, VP Brand, Head of Community` | `c_suite, vp, head, director` |

---

## 共通の除外条件

企業リストから外す (スクリプトは `--exclude-keywords` で受け付ける):

- 日本に **100 名超**の社員がいる (既に日本マーケ / PR 組織がある可能性が高い。ただし B は 300 名まで許容)
- 業種が代理店・コンサル・受託開発・人材 (`marketing agency, consulting, staffing, outsourcing, public relations`)
- 日本市場に法規制上入れない (オンラインギャンブル、成人向け、暗号資産取引所の一部)
- 既存クライアント・既に商談中の企業 (ユーザーから `--exclude-domains` で受け取る)

---

## 日本進出シグナル

強い順。Step 2 (`score_accounts.py`) と Step 5 (メールの「観察」) の両方で使う。

| シグナル | 取り方 | 意味 |
|---|---|---|
| 日本在住社員 1〜30 名 | people search `organization_ids` + `person_locations: ["Japan"]` の `total_entries` | 拠点はあるが機能が足りない。**最も熱い** |
| 日本の求人 (Tokyo, Japan, 日本語) | `organizations/{id}/job_postings` (クレジット消費) or Web 検索 `<company> careers Tokyo` | 投資意思が確定している |
| 直近 12 か月の Japan 関連プレスリリース | Web 検索 `<company> Japan launch` / `<company> 日本 提携` | 出て行く決意 or 出たが伸びていない |
| 日本語サイトがある / 無い | `<domain>/ja` `<domain>/jp` を確認 | 無い = ローカライズが刺さる。ある = 質を見て事例・オウンドメディアを提案 |
| 日本企業との提携・代理店契約 | Web 検索 `<company> 販売代理店` `<company> パートナー 日本` | 商社任せ = 自社マーケ不在 |
| 日本の展示会に出展 | Web 検索 `<company> Japan IT Week` `Interop Tokyo` `CEATEC` `Tokyo Game Show` | 展示会運営・イベントの提案が直球 |
| APAC 拠点 (Singapore / Sydney / Seoul) はあるが日本なし | people search `person_locations` | 「次は日本」の議論が社内で起きている |
| Series B 以降 or 直近 24 か月で調達 | organization search の `latest_funding_stage`, `latest_funding_round_date` | 海外展開の予算がある |
| 日本の競合が強い / 米国競合が日本で成功している | 業界知識 | 「競合 X は日本でこうしている」がメールの観察に使える |

---

## スコアリング

`score_accounts.py` の実装と同じ。合計 100 点、55 点以上を送信対象にする。

| 軸 | 配点 | 基準 |
|---|---|---|
| 規模フィット | 30 | 201〜2,000 名 = 30 / 51〜200 = 20 / 2,001〜5,000 = 20 / それ以外 = 5 |
| バーティカル近接 | 20 | キーワードが自社実績のバーティカルに一致 = 20 / 隣接 = 10 / 無し = 0 |
| 日本モメンタム | 30 | 日本社員 1〜30 = 30 / 31〜100 = 20 / 0 名だが APAC 社員あり = 15 / 101 名超 = 8 / 何もなし = 5 (+ 日本求人あり = 上限 30 まで +10) |
| 成長シグナル | 10 | Series B 以降 or 24 か月以内に調達 = 10 / 情報あり不一致 = 3 / 不明 = 5 |
| 到達性 | 10 | Step 3 でペルソナ 2 名以上 = 10 / 1 名 = 5 / 0 = 0 (Step 3 前は暫定 5) |

スコアはあくまで並べ替えのため。人間が見て「この会社に出したい」と思う定性の理由 (観察) が
メールの中身になる。

---

## Apollo UI でのフィルタ設定

API キーが無い場合、Apollo の Search 画面で同じ条件を作り CSV エクスポートする。
`scripts/import_apollo_export.py` で読み込める。

**Companies タブ (セグメント A / enterprise-ai の例)**

1. Location → **Company HQ** → Exclude: Japan
2. # Employees → 51-200, 201-500, 501-1000, 1001-5000
3. Keywords → `artificial intelligence`, `enterprise search`, `generative ai` (Include any)
4. Funding → Series B 以降 (任意)
5. 「Save as list」→ 名前 `JP-outreach-A-enterprise-ai-<日付>`
6. Export → CSV (Company 列は Name, Website, # Employees, Industry, Keywords, Short Description,
   Founded Year, Latest Funding, Latest Funding Amount, Company Country を含める)

**People タブ**

1. Lists → 上で作った企業リストを選ぶ (または Company Domain に貼り付け)
2. Job Titles → ペルソナ表の役職を貼る、Include similar titles = ON
3. Management Level → C-Suite / VP / Head / Director (優先 1 は Manager も)
4. Location → Person location: Japan (優先 1 のとき)
5. Email Status → Verified, Likely to engage
6. Select all → Export (この時点でクレジット消費)

エクスポートの列名は Apollo の既定 (`First Name`, `Last Name`, `Title`, `Company`, `Email`,
`Email Status`, `Seniority`, `Person Linkedin Url`, `Website`, `# Employees`, `Industry`, `Keywords`,
`City`, `Country`, `Company Country`) を想定している。
