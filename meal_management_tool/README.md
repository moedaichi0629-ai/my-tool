# LINE食事記録Bot

食事写真をLINEに送るだけで、AIが食事内容を解析してGoogleスプレッドシートに記録するBotです。

## 機能

- 食事写真をLINEに送信 → AIが料理名・食材を自動解析
- 食事区分（朝/昼/夜/間食）のクイックリプライ選択
- 任意メモの記録（体調・練習メモなど）
- Googleスプレッドシートへ自動保存
- 「今日の振り返り」コマンドで日次レポート生成
- 「週次振り返り」コマンドで週次レポート生成
- 「献立」コマンドで翌週の夕食メニュー＆買い物リスト生成

## 技術スタック

- Python 3.12
- Flask + Gunicorn
- LINE Messaging API v3
- OpenAI GPT-4o（Vision）
- Google Sheets API（サービスアカウント認証）

---

## ローカル開発環境のセットアップ

```bash
# リポジトリをクローン
git clone https://github.com/moedaichi0629-ai/my-tool.git
cd my-tool/meal_management_tool

# 仮想環境を作成・有効化
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux

# 依存パッケージをインストール
pip install -r requirements.txt

# 環境変数を設定
cp .env.example .env
# .envファイルを開いて各APIキーを入力

# アプリを起動
python app.py
```

---

## Render へのデプロイ手順（初心者向け）

**Render とは？** クラウド上でアプリを24時間動かせる無料サービスです。
PCを閉じても LINE Bot が動き続けます。

---

### 事前準備

#### ① Google サービスアカウントを作成する

> **なぜ必要？** ローカル開発では `credentials.json` ファイルを使っていましたが、
> Render にファイルを置けないため、JSON の中身を環境変数として設定します。

1. [Google Cloud Console](https://console.cloud.google.com/) を開く
2. プロジェクトを選択 → 「IAMと管理」→「サービスアカウント」
3. 既存のサービスアカウントをクリック →「キー」タブ →「鍵を追加」→「JSON」
4. ダウンロードされた `credentials.json` をメモ帳で開く
5. 内容をすべてコピーして、**1行のJSON文字列**にする

   PowerShell で1行にする方法：
   ```powershell
   (Get-Content credentials.json -Raw) -replace "`r`n|`n", "" | Set-Clipboard
   ```
   （これを実行するとクリップボードに1行JSONがコピーされます）

#### ② コードをGitHubにpushする

```bash
git add .
git commit -m "feat: Renderデプロイ用に設定を更新"
git push origin main
```

---

### Render でのデプロイ手順

#### ステップ1：Render にサインアップ

1. [https://render.com](https://render.com) を開く
2. 「Get Started for Free」をクリック
3. 「GitHub でサインアップ」を選択してGitHubアカウントと連携

---

#### ステップ2：新しい Web Service を作成

1. Render ダッシュボードで「**New +**」→「**Web Service**」をクリック
2. 「Connect a repository」で `my-tool` リポジトリを選択
3. 以下の項目を設定する：

   | 項目 | 設定値 |
   |------|--------|
   | **Name** | `meal-management-bot`（任意） |
   | **Root Directory** | `meal_management_tool` |
   | **Runtime** | `Python 3` |
   | **Build Command** | `pip install -r requirements.txt` |
   | **Start Command** | `gunicorn app:app` |
   | **Instance Type** | `Free` |

---

#### ステップ3：環境変数を設定する

「Environment Variables」セクションで以下を追加：

| Key | Value |
|-----|-------|
| `LINE_CHANNEL_SECRET` | LINE Developersで確認したシークレット |
| `LINE_CHANNEL_ACCESS_TOKEN` | LINE Developersで発行したトークン |
| `OPENAI_API_KEY` | OpenAI APIキー（sk-から始まる） |
| `GOOGLE_SPREADSHEET_ID` | スプレッドシートのURL中のID |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | credentials.jsonの中身（1行JSON） |

> **重要：** `GOOGLE_SERVICE_ACCOUNT_JSON` には、事前準備①で作った
> 1行のJSON文字列を貼り付けてください。

---

#### ステップ4：デプロイを実行

「**Create Web Service**」ボタンをクリック。

ログが流れ始め、最後に以下が表示されれば成功：
```
==> Your service is live 🎉
```

アプリのURL（例：`https://meal-management-bot.onrender.com`）が表示されます。

---

#### ステップ5：動作確認

ブラウザでアプリのURLにアクセスして、以下が表示されればOKです：
```
LINE食事記録Bot は正常に動作しています ✅
```

---

#### ステップ6：LINE Webhook URL を設定する

1. [LINE Developers Console](https://developers.line.biz/console/) を開く
2. チャンネルを選択 →「Messaging API設定」タブ
3. 「Webhook URL」に以下を入力：
   ```
   https://（あなたのRenderのURL）/callback
   ```
   例：`https://meal-management-bot.onrender.com/callback`
4. 「検証」ボタンをクリック → 「成功」と表示されればOK
5. 「Webhookの利用」を **オン** にする

---

### デプロイ後の注意点

**無料プランのスリープについて**

Renderの無料プランでは、**15分間アクセスがないと自動的にスリープ**します。
スリープ中はWebhookを受信できず、最初のメッセージへの返信が遅れます（30秒〜1分）。

解消するには：
- 有料プランにアップグレード（$7/月〜）
- または [UptimeRobot](https://uptimerobot.com/) などの外部サービスで定期的にヘルスチェックURLを叩く

UptimeRobot の設定例：
- Monitor Type: `HTTP(S)`
- URL: `https://（あなたのRenderのURL）/`
- Monitoring Interval: `5 minutes`

---

## 環境変数一覧

| 変数名 | 説明 | 取得場所 |
|--------|------|---------|
| `LINE_CHANNEL_SECRET` | LINEチャンネルシークレット | LINE Developers Console |
| `LINE_CHANNEL_ACCESS_TOKEN` | LINEアクセストークン | LINE Developers Console |
| `OPENAI_API_KEY` | OpenAI APIキー | platform.openai.com |
| `GOOGLE_SPREADSHEET_ID` | スプレッドシートID | スプレッドシートのURL |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | サービスアカウントJSON | Google Cloud Console |

## 使えるLINEコマンド

| コマンド | 内容 |
|----------|------|
| 食事写真を送る | 自動解析・記録開始 |
| `今日の振り返り` | 今日の食事レポートを送信 |
| `週次振り返り` | 直近1週間のレポートを送信 |
| `献立` | 翌週の夕食メニュー＆買い物リストを送信 |
| `キャンセル` | 進行中の操作をリセット |
