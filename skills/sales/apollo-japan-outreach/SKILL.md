---
name: apollo-japan-outreach
description: >-
  日本市場参入を目指す海外企業への新規顧客開拓(アウトバウンド営業)を、Apollo.io でのターゲット企業
  の絞り込み・リスト作成 → 担当者(コンタクト)情報の抽出 → 企業ごとにカスタマイズした
  アウトリーチメールの作成まで一気通貫で行うスキル。対象セグメントは (A) 日本で B2B マーケティング
  (戦略立案・展示会・イベント・ローカライズ・コンテンツ・オウンドメディア・広告) を行いたい海外の
  ソフトウェア/テック/ハードウェア/エネルギー企業、(B) 日本で PR・記者発表・インフルエンサー提携を
  行いたい海外コンシューマブランド。「Apollo でリストを作って」「ターゲット企業を絞り込んで」
  「コンタクト情報を抽出して」「営業メール/コールドメール/アウトリーチメールを書いて」「日本進出
  したい海外企業を探して」「新規開拓」「見込み客リスト」「ICP に合う企業」など、リード獲得・
  プロスペクティング・アウトバウンドに関する依頼があれば、Apollo という単語がなくても必ずこの
  スキルを使うこと。Apollo の CSV エクスポートを渡された場合や、既にある企業リストに対して
  メールを書く依頼にも使う。
---

# Apollo Japan Outreach — 海外企業向け日本市場参入支援の新規開拓スキル

海外企業に「日本でのマーケティング / PR を任せられるパートナー」として最初の返信をもらうための
一連の作業をこなす。成果物は 3 つ:

1. **ターゲット企業リスト** (`accounts.csv`) — Apollo で絞り込み、フィット度をスコアリングした企業
2. **コンタクトリスト** (`contacts.csv`) — 各企業の意思決定者と連絡先 (メールは Apollo で enrich)
3. **企業別アウトリーチメール** (`outreach/<company>.md`) — 3 通の初回シーケンスを企業ごとに書き分けたもの

自社情報 (サービス、実績、送信者) は `references/company-profile.md` に集約してある。
メールを書く前に必ず読み、**プレースホルダーが残っていれば埋めるようユーザーに一度だけ確認**する。

## いつ何を読むか

| 状況 | 読むファイル |
|---|---|
| セグメント・ペルソナ・Apollo フィルタ値・スコアリング基準を決める | `references/icp-segments.md` |
| Apollo API を叩く / スクリプトの引数を確認する / エラー・クレジット | `references/apollo-api.md` |
| メールを書く (構成・件名・実績の使い分け・日英・例文・法令) | `references/email-playbook.md` |
| 自社の実績と提供サービスの言い回し | `references/company-profile.md` |
| 企業ごとの調査メモとメール出力のフォーマット | `assets/outreach_brief_template.md` |

## 全体の流れ

```
Step 0  依頼の解釈 (セグメント・件数・地域・出力形式を確定)
Step 1  Apollo で企業を絞り込む       → scripts/search_accounts.py   → accounts_raw.csv
Step 2  日本進出シグナルを付けて採点    → scripts/score_accounts.py    → accounts.csv (上位 N 社)
Step 3  意思決定者を抽出              → scripts/find_contacts.py     → contacts_raw.csv
Step 4  メールアドレスを enrich       → scripts/enrich_contacts.py   → contacts.csv
Step 5  企業ごとに調査してメールを書く → outreach/<company>.md + summary.md
```

各ステップは独立して使える。ユーザーが「Apollo の CSV を渡すのでメールだけ書いて」と言えば
`scripts/import_apollo_export.py` で CSV を正規化して Step 5 だけやる。API キーが無ければ
Step 1〜4 を Apollo の画面操作手順として案内する (`references/apollo-api.md` の「UI 代替手順」)。

### Step 0: 依頼を確定する

最初に次の 4 点を決める。ユーザーが明示していなければ、括弧内のデフォルトで進めて最後に報告する
(質問で作業を止めない)。

- **セグメント**: A = B2B テック企業の日本マーケ支援 / B = コンシューマブランドの日本 PR (指定なければ A)
- **バーティカル**: A なら enterprise-ai / saas / adtech-martech / cyber / devtools / hardware / energy / deeptech、
  B なら gaming / consumer-electronics / beauty / lifestyle (指定なければ自社実績が最も近いものを 2〜3 個)
- **件数**: 企業 N 社、1 社あたりコンタクト M 名 (デフォルト 30 社 × 2 名)
- **出力先**: 作業ディレクトリ (デフォルト `./outreach-<セグメント>-<YYYYMMDD>/`)

作業ディレクトリと成果物の場所は最後の報告に含める。

### Step 1: Apollo で企業を絞り込む

`scripts/search_accounts.py` を使う。セグメントとバーティカルのプリセット (`references/icp-segments.md`
と同じ値) を組み込んであるので、通常はプリセットだけで十分。

```bash
export APOLLO_API_KEY=...   # 未設定ならユーザーに設定を依頼 (値は聞かない、環境変数で渡してもらう)
python3 scripts/search_accounts.py \
  --segment a --vertical enterprise-ai --vertical saas \
  --max-accounts 150 \
  --out ./work/accounts_raw.csv
```

考え方:

- **HQ が日本以外**の企業を探す (`organization_not_locations: ["Japan"]`)。日本企業は対象外。
- **従業員 51〜5,000 名**が主戦場。50 名未満は予算が無く、5,000 名超は日本法人にマーケ部門があることが多い。
- 検索エンドポイントはクレジットを消費しないので、広めに取って Step 2 で絞る方が良い。
  ただし 1 ページ 100 件 × 最大 500 ページの表示上限があるため、条件を絞って複数回に分ける。
- 検索結果はメールを含まない。メールは Step 4 で初めて取得する (ここでクレジットを使う)。

### Step 2: 日本進出シグナルを付けて採点する

`scripts/score_accounts.py` が各企業について次を確認し、0〜100 点を付ける (基準の詳細は
`references/icp-segments.md` の「スコアリング」)。

- **日本在住の社員数** (people search で `person_locations: ["Japan"]` を数える。クレジット不要)
  — 1〜30 名が最も熱い。「日本に人はいるが、マーケ/PR チームは無い」状態だから。
- **APAC 拠点の有無** (Singapore / Australia / Korea 等の社員)
- **規模・バーティカルの自社実績との近さ**
- **資金調達ステージ** (Series B 以降、または直近 24 か月の調達)
- **日本関連の求人** (`--check-jobs` を付けたときのみ。job postings API はクレジットを消費する)

```bash
python3 scripts/score_accounts.py --in ./work/accounts_raw.csv --out ./work/accounts.csv --top 30
```

上位 N 社を `accounts.csv` に残す。閾値は 55 点以上を目安にし、それ未満は `accounts_backlog.csv` に退避する。

### Step 3: 意思決定者を抽出する

`scripts/find_contacts.py` が `accounts.csv` の各企業について、セグメント別のペルソナ (役職リストは
`references/icp-segments.md`) で people search を行う。1 社あたり最大 M 名、優先順位は:

1. **日本を管轄する人** (Country Manager Japan / GM Japan / Head of Japan / Marketing Manager Japan)
2. **APAC / International を管轄するマーケ責任者**
3. **本社のマーケ / PR 責任者** (VP Marketing, CMO, Head of Communications)

日本担当者がいる企業ではその人を必ず 1 名入れる。返信率が最も高く、かつ日本語メールが効く相手だから。

```bash
python3 scripts/find_contacts.py --segment a --in ./work/accounts.csv --per-account 2 --out ./work/contacts_raw.csv
```

### Step 4: メールアドレスを enrich する

`scripts/enrich_contacts.py` は `people/bulk_match` を 10 名ずつ呼び、`email` と `email_status` を埋める。
**クレジットを消費する**ので `--max-credits` で上限を必ず指定し、実行前に「N 名分 = 最大 N クレジット
使います」と伝える。`email_status` が `verified` または `likely_to_engage` のものだけを送信対象とし、
`unavailable` は LinkedIn 経由の接触に回す。

```bash
python3 scripts/enrich_contacts.py --in ./work/contacts_raw.csv --out ./work/contacts.csv --max-credits 60
```

### Step 5: 企業ごとに調査してメールを書く

ここがこのスキルの価値の 8 割。テンプレの差し込みではなく、**1 社ごとに 5 分の調査をして 1 つの
「観察」を掴む**。手順:

1. `accounts.csv` の `short_description`, `keywords`, `japan_headcount`, `latest_funding` を読む。
2. Web 検索が使えれば、`<company> Japan`, `<company> 日本`, `<company> APAC expansion`, `<company> Tokyo`
   で直近 12 か月のニュース・求人・日本語サイトの有無・日本の展示会出展 (Japan IT Week, Interop Tokyo,
   CEATEC, Tokyo Game Show, AWS Summit Tokyo 等) を確認する。
3. `assets/outreach_brief_template.md` の形式で企業ごとに「観察 → 仮説 → 使う実績 → CTA」を 4 行で決める。
4. `references/email-playbook.md` に従って 3 通 (初回 / 4 日後 / 10 日後) を書く。
   - 宛先が本社 (英語圏) の人 → 英語
   - 宛先が日本担当者で日本語名 → 日本語 (英語版も併記)
   - 1 通目 120 語以内。件名 6 語以内。CTA は 1 つ。実績は相手の業界に最も近い 1 社だけ引く。
5. `summary.md` に全社の一覧 (企業 / スコア / 宛先 / 観察 / 使った実績 / 送信言語) を表でまとめる。

メールを Gmail の下書きとして作る依頼があれば、下書き作成までは行い**送信はしない**。送信は必ず
ユーザーの判断に委ねる (誤送信は取り返しがつかず、相手企業との最初の接点だから)。

## 品質チェック (納品前に自分で確認する)

- 企業ごとの 1 通目を並べたとき、冒頭 2 文が**入れ替え不能**になっているか (相手企業名を伏せても
  どの会社宛か分かるのが合格)。
- 自社実績を 2 社以上並べていないか (信頼より押し売りに見える)。
- 「日本市場は特殊」「ご存知の通り」など相手を教える調子になっていないか。
- 日本担当者宛の日本語メールが、翻訳調でなく営業メールとして自然か (敬語は丁寧語ベース、謙譲語過多にしない)。
- `contacts.csv` の `email_status` が `unavailable` の人にメールを書いていないか。
- 特定電子メール法 / CAN-SPAM の要件 (送信者の実名・会社名・住所・オプトアウト文) が署名に入っているか。

## 最後の報告に含めること

- 作業ディレクトリと 3 つの成果物のパス
- 何社検索し、何社が閾値を超え、何名の連絡先を取り、何クレジット使ったか (表で)
- 使ったデフォルト (セグメント、バーティカル、件数) と、次にユーザーが決めるべきこと
  (例: プロフィールのプレースホルダー、送信のタイミング、Gmail 下書き化の要否)
