# CLAUDE.md

Claude Code がこのリポジトリで作業するときの前提・決定事項・残作業をまとめたもの。

## 目的

別のAIツールで作った Threads 投稿文（テキスト）を自動投稿し、どのジャンル・投稿が伸びているかを分析する。
利用者は開発者本人のみ（自分の Threads アカウント1〜2個）。Meta のアプリ審査は不要（テスター登録で運用）。

## 決定事項（利用者と合意済み）

- 入力：AIツールの出力テキストを `posts/inbox.txt` に `---` 区切りで貼り付ける
- 投稿数：1日3件、最大5件（`config.json` の `slots` と `max_per_day`）
- 投稿時刻：初期値 7:00 / 12:15 / 21:00（JST）。5件にするなら 18:30 / 22:30 を追加。将来は分析結果から最適化する
- ジャンル：最初は手入力（各ブロック先頭の `ジャンル: xxx`）。後で Claude API による自動判定を追加する
- AI：Claude API を使う（モデルは最新の Claude を使う）
- 投稿形式：テキストのみ（画像・動画は対象外）

## 構成

```
threads_poster/
  cli.py          コマンド（import / list / post / retry / check / refresh-token）
  parser.py       inbox.txt を投稿単位に分割（500文字上限チェック）
  store.py        data/posts.json の読み書き（status: queued / posted / failed）
  scheduler.py    投稿枠の判定（定期実行の遅れを slot_window_minutes で吸収）
  threads_api.py  Threads API クライアント（標準ライブラリの urllib のみ）
tests/            unittest
config.json       タイムゾーン・アカウント・投稿枠・上限
.env              THREADS_TOKEN_<アカウント名大文字>（git 管理外）
```

## 開発ルール

- Python 3.10+、**外部ライブラリなし**（標準ライブラリのみ）を維持する。どうしても必要なら requirements.txt を追加して理由を README に書く
- 画面出力・コメント・README は日本語
- 変更したら必ずテストを実行：`python -m unittest discover -s tests -t .`
- Threads API を叩くテストは書かない。`tests/test_cli.py` の `FakeClient` のようにモックする
- 秘密情報（トークン・APIキー）はコミットしない

## Threads API メモ

- ベースURL：`https://graph.threads.net/v1.0`
- 投稿：`POST /{user-id}/threads`（media_type=TEXT, text）→ `POST /{user-id}/threads_publish`（creation_id）
- 投稿のインサイト：`GET /{media-id}/insights?metric=views,likes,replies,reposts,quotes,shares`
- アカウントのインサイト：`GET /{user-id}/threads_insights?metric=views,likes,replies,reposts,quotes,followers_count`
- 投稿上限：24時間で250件
- 長期トークンは約60日で失効。`GET /refresh_access_token?grant_type=th_refresh_token` で更新
- 必要な権限：`threads_basic`, `threads_content_publish`, `threads_manage_insights`

## 進捗

- [x] 第1段階：取り込み・予約キュー・投稿枠での自動投稿・二重投稿防止・1日上限・失敗時の再試行
- [ ] 第2段階：インサイト収集
  - `collect` コマンド：投稿済みの各投稿について指標を取得し、`data/metrics.json` に時系列で追記
  - 投稿後 24時間・48時間・7日の時点の値を比較できるように取得日時も保存する
- [ ] 第3段階：分析
  - `report` コマンド：ジャンル別・投稿時間帯別・アカウント別の平均閲覧数とエンゲージメント率（(いいね+返信+リポスト+引用)/閲覧数）、伸びた投稿トップ10
  - 投稿数が少ないジャンルは「参考値」と表示する（例：5件未満）
  - 伸びる時間帯の提案（`slots` の見直し候補）
- [ ] 第4段階：ダッシュボード（`report` の結果を静的HTMLで出力。グラフ付き）
- [ ] 第5段階：GitHub Actions で定期実行
  - 投稿枠の時刻（UTCに変換）に `post`、1日数回 `collect` を実行し、`data/` の変更をコミットして戻す
  - トークンは GitHub Secrets に保存。更新は Secrets の書き換えが必要なので方法を検討する
- [ ] 第6段階：Claude API によるジャンル自動判定（`ジャンル:` が無い投稿に付ける。既存ジャンル一覧から選ばせる）
