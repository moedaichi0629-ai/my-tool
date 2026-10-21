# Threads 自動投稿ツール

AIで作った投稿文を `posts/inbox.txt` に貼り付けておくと、決めた時間帯に Threads へ自動投稿します。
投稿にはジャンルを付けて記録するので、あとで「どのジャンル・投稿が伸びているか」を分析できます（分析機能は次の段階で追加予定）。

- Python 3.10 以上（外部ライブラリ不要）
- 自分のアカウント1〜2個で利用（Meta のアプリ審査は不要）

## 1. 準備（最初の1回だけ）

1. [Meta for Developers](https://developers.facebook.com/) でアプリを作成し、ユースケースに「Threads API にアクセス」を選ぶ
2. 権限 `threads_basic` `threads_content_publish` `threads_manage_insights` を追加
3. 「アプリの役割」で投稿したい Threads アカウントを **Threadsテスター** に追加し、Threads アプリ側（設定 → アカウント → ウェブサイトのアクセス許可）で招待を承認
4. ユーザートークン生成ツールでアカウントごとに**長期アクセストークン**を発行
5. `.env.example` を `.env` にコピーしてトークンを書き込む

```
THREADS_TOKEN_MAIN=発行したトークン
THREADS_TOKEN_SUB=2つ目のアカウントのトークン（使わないなら config.json の accounts から sub を削除）
```

6. 接続確認

```bash
python -m threads_poster check
```

## 2. 毎日の使い方

### 投稿を貼り付ける

`posts/inbox.txt` に `---` で区切って貼り付けます。先頭の「ジャンル:」「アカウント:」は省略できます（アカウント省略時は `main`）。

```
ジャンル: 副業
月5万円を達成するまでにやった3つのこと
1. …
---
ジャンル: 朝活
アカウント: sub
朝5時に起きて気づいたこと…
```

### 予約キューに取り込む

```bash
python -m threads_poster import   # inbox の中身をキューへ（取り込めたものは inbox から消える）
python -m threads_poster list     # 予約中・失敗した投稿を確認
```

### 投稿する

```bash
python -m threads_poster post            # 投稿枠の時間内なら、各アカウント1件ずつ投稿
python -m threads_poster post --dry-run  # 実際には投稿せず、次に投稿するものを確認
python -m threads_poster post --now      # 時間に関係なく今すぐ1件投稿
python -m threads_poster retry           # 失敗した投稿をキューに戻す
```

`post` を定期実行（次の段階で GitHub Actions に設定予定）すると、投稿枠ごとに1件ずつ自動投稿されます。
同じ枠で二重投稿はせず、1日の上限（`max_per_day`）を超えることもありません。

### トークンの更新

長期トークンは約60日で切れます。期限内に次を実行すると `.env` のトークンが更新されます。

```bash
python -m threads_poster refresh-token
```

## 3. 設定（config.json）

| 項目 | 説明 |
|---|---|
| `accounts` | 使うアカウント名。`.env` の `THREADS_TOKEN_<名前>` と対応 |
| `slots` | 投稿時刻。初期値はインプが伸びやすいと言われる 7:00 / 12:15 / 21:00。5件にするなら `"18:30"` `"22:30"` を追加 |
| `max_per_day` | 1アカウントあたりの1日の投稿上限 |
| `slot_window_minutes` | 投稿枠の時刻から何分後までを「その枠」とみなすか（定期実行の遅れ対策） |

## データ

投稿の記録は `data/posts.json` に保存されます（本文・ジャンル・アカウント・投稿日時・Threads の投稿ID・URL）。分析機能はこのデータを使います。

## テスト

```bash
python -m unittest discover -s tests -t .
```
