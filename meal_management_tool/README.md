# LINE 食事写真記録・平日献立提案ツール

LINEで食事写真を送るだけで、AIが食事内容を読み取り、  
Google スプレッドシートへ自動記録してくれるツールです。

---

## 1. このツールでできること

| 操作 | 内容 |
|------|------|
| 食事写真を送る | AIが料理を推定 → スプレッドシートに保存 → LINEに結果返信 |
| `今日の振り返り` と送る | その日の食事記録をもとにAIがコメントを作成 |
| `週次振り返り` と送る | 直近1週間の食生活を分析・フィードバック |
| `献立` と送る | 翌週月〜金の夕食献立 ＋ 買い物リストを提案 |
| `キャンセル` と送る | 操作を途中でリセット |

---

## 2. 必要なもの（事前準備）

- **Python 3.10 以上**（インストール済みであること）
- **LINE アカウント**（普段使いのもので OK）
- **OpenAI アカウント** と APIキー（有料）
- **Google アカウント**
- **ngrok** のインストール（ローカルを外部公開するツール）

---

## 3. インストール手順

### ① このフォルダを開いてターミナルを起動する

```
cd meal_management_tool
```

### ② Python の仮想環境を作成・有効化する

```bash
# 仮想環境を作成
python -m venv venv

# 有効化（Windows）
venv\Scripts\activate

# 有効化（Mac / Linux）
source venv/bin/activate
```

### ③ 必要なライブラリを一括インストールする

```bash
pip install -r requirements.txt
```

---

## 4. Google Cloud の設定

食事記録を Google スプレッドシートに保存するために、  
Google のサービスアカウントを作成して認証情報を取得します。

### ステップ 1：Google Cloud Console でプロジェクトを作成

1. [https://console.cloud.google.com/](https://console.cloud.google.com/) を開く
2. 画面上部の「プロジェクトを選択」→「新しいプロジェクト」をクリック
3. プロジェクト名（例：`meal-record-tool`）を入力して「作成」

### ステップ 2：Google Sheets API を有効化する

1. 左メニューの「APIとサービス」→「ライブラリ」を開く
2. 検索欄に `Google Sheets API` と入力して選択
3. 「有効にする」をクリック
4. 同様に `Google Drive API` も検索して有効化する

### ステップ 3：サービスアカウントを作成する

1. 左メニューの「APIとサービス」→「認証情報」を開く
2. 上部の「＋ 認証情報を作成」→「サービスアカウント」をクリック
3. サービスアカウント名（例：`meal-bot`）を入力して「作成して続行」
4. ロールは「編集者」を選択して「完了」

### ステップ 4：credentials.json をダウンロードする

1. 作成したサービスアカウントのメールアドレスをクリック
2. 上部の「キー」タブを開く
3. 「鍵を追加」→「新しい鍵を作成」→「JSON」を選択して「作成」
4. ダウンロードされた JSON ファイルを `credentials.json` という名前に変更して、  
   **このフォルダ（`meal_management_tool/`）直下** に配置する

### ステップ 5：Google スプレッドシートを作成して共有する

1. [Google スプレッドシート](https://sheets.google.com/) で新しいシートを作成
2. URL をコピーして `GOOGLE_SPREADSHEET_ID` を確認する  
   → URL の形式：`https://docs.google.com/spreadsheets/d/【ここがID】/edit`
3. 右上の「共有」ボタンをクリック
4. 先ほど作成したサービスアカウントのメールアドレスを入力して「編集者」として共有

> ⚠️ 共有しないとスプレッドシートに書き込めません。必ず行ってください。

---

## 5. LINE Developers の設定

### ステップ 1：LINE Developers に登録

1. [https://developers.line.biz/](https://developers.line.biz/) を開く
2. 右上「ログイン」→ LINE アカウントでログイン

### ステップ 2：プロバイダーとチャンネルを作成

1. 「プロバイダーを作成」→ 名前を入力（例：`食事記録Bot`）
2. 「Messaging API チャンネルを作成」をクリック
3. 必要事項を入力して作成

### ステップ 3：APIキーを取得

1. チャンネルの「チャンネル基本設定」タブを開く
2. `チャンネルシークレット` をコピーして `.env` の `LINE_CHANNEL_SECRET` に貼り付ける
3. 「Messaging API 設定」タブを開く
4. 一番下の「チャンネルアクセストークン（長期）」→「発行」をクリック
5. コピーして `.env` の `LINE_CHANNEL_ACCESS_TOKEN` に貼り付ける

### ステップ 4：応答設定を変更

1. 「Messaging API 設定」タブの中の「LINE公式アカウント機能」の「応答メッセージ」を**オフ**にする  
   （自動応答がオンのままだとBotの返信と重複する）
2. 「Webhook の利用」を**オン**にする

---

## 6. OpenAI API キーの取得

1. [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys) を開く
2. 「Create new secret key」をクリック
3. 生成されたキー（`sk-` から始まる文字列）をコピー
4. `.env` の `OPENAI_API_KEY` に貼り付ける

> ⚠️ APIキーは一度しか表示されません。必ずコピーしておいてください。  
> ⚠️ GPT-4o は有料です。使用量に応じて課金されます。

---

## 7. .env ファイルの書き方

`.env.example` をコピーして `.env` という名前で保存し、各値を書き換えてください。

```bash
# Windows
copy .env.example .env

# Mac / Linux
cp .env.example .env
```

書き換え後の `.env` の中身（例）：

```
LINE_CHANNEL_SECRET=abc123def456...
LINE_CHANNEL_ACCESS_TOKEN=eyJhbGciOiJIUzI1...
OPENAI_API_KEY=sk-proj-xxxx...
GOOGLE_SPREADSHEET_ID=1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms
```

> ⚠️ `.env` ファイルは絶対に GitHub などに公開しないでください！

---

## 8. credentials.json の置き場所

```
meal_management_tool/
├── app.py
├── credentials.json   ← ここに置く（Google Cloud からダウンロードしたファイル）
├── .env
└── ...
```

---

## 9. ngrok の設定と Webhook URL の登録

ngrok はローカル PC 上で動いている Flask サーバーを、  
外部（LINE のサーバー）から接続できるように一時公開するツールです。

### ngrok のインストール

[https://ngrok.com/download](https://ngrok.com/download) からダウンロードして PATH に追加  
または Homebrew（Mac）や Chocolatey（Windows）でインストール

```bash
# Mac
brew install ngrok

# Windows（Chocolatey）
choco install ngrok
```

### ngrok を起動する

Flask と **別のターミナル** で以下を実行：

```bash
ngrok http 5000
```

成功すると以下のような表示が出ます：

```
Forwarding  https://xxxx-xxx-xxx-xx.ngrok-free.app -> http://localhost:5000
```

`https://xxxx-xxx-xxx-xx.ngrok-free.app` の部分が公開 URL です。

### LINE Developers に Webhook URL を登録する

1. LINE Developers → チャンネル → 「Messaging API 設定」を開く
2. 「Webhook URL」に以下を入力して保存：
   ```
   https://xxxx-xxx-xxx-xx.ngrok-free.app/callback
   ```
3. 「検証」ボタンを押して「成功」と表示されれば OK

> ⚠️ ngrok を再起動するたびに URL が変わります。変わったら LINE にも再登録が必要です。  
>    （固定 URL が必要な場合は ngrok の有料プランをご利用ください）

---

## 10. ツールの起動方法

ターミナルで以下を順番に実行します。

```bash
# ターミナル 1：Flask サーバーを起動
cd meal_management_tool
venv\Scripts\activate   # Windows
python app.py

# ターミナル 2：ngrok で外部公開
ngrok http 5000
```

`* Running on http://127.0.0.1:5000` と表示されれば起動成功です。

---

## 11. LINE での使い方

LINE でボットの友達追加後（QR コードは LINE Developers のチャンネルページにあります）：

### 食事を記録する

1. 食事の写真を送信
2. 「朝食 / 昼食 / 夕食 / 間食」のボタンが表示されるので選択
3. メモがあれば入力（なければ「スキップ」をタップ）
4. しばらくすると AI の解析結果と記録完了メッセージが届く

### 特殊コマンド

| 送るテキスト | 動作 |
|---|---|
| `今日の振り返り` | その日の食事をまとめてコメント |
| `週次振り返り` | 直近1週間の食生活を分析 |
| `献立` | 翌週の夕食献立 ＋ 買い物リストを提案 |
| `キャンセル` | 入力中の操作をリセット |

---

## 12. エラーが出たときの確認ポイント

### ❌ Flask が起動しない

```
ModuleNotFoundError: No module named 'flask'
```
→ 仮想環境が有効化されていません。`venv\Scripts\activate` を実行してから再度試してください。

### ❌ LINE の Webhook 検証が失敗する

- ngrok が起動していますか？（ターミナル 2 で `ngrok http 5000` を実行）
- Flask が起動していますか？（ターミナル 1 で `python app.py` を実行）
- Webhook URL の末尾に `/callback` がついていますか？
- `LINE_CHANNEL_SECRET` が正しく `.env` に設定されていますか？

### ❌ スプレッドシートに書き込めない

```
gspread.exceptions.SpreadsheetNotFound
```
→ `GOOGLE_SPREADSHEET_ID` が間違っているか、スプレッドシートをサービスアカウントと共有していません。

```
google.auth.exceptions.DefaultCredentialsError
```
→ `credentials.json` が `meal_management_tool/` フォルダに置かれていません。

### ❌ OpenAI の画像解析でエラーが出る

```
openai.AuthenticationError
```
→ `OPENAI_API_KEY` が間違っています。Platform の API Keys ページで確認してください。

```
openai.RateLimitError
```
→ OpenAI の利用制限に達しました。しばらく待ってから再試行してください。

### ❌ LINE にメッセージが届かない（プッシュ通知）

`push_text` を使うにはチャンネルが「Messaging API」タイプであることが必要です。  
また、フリープランでは月のプッシュメッセージ数に上限があります。

### ❌ ngrok を再起動したら動かなくなった

ngrok の URL は再起動するたびに変わります。  
LINE Developers の Webhook URL を新しい ngrok URL に更新してください。

---

## 13. 今後追加できる機能

- [ ] **毎日の自動振り返り通知**（LINE の push 通知を毎晩自動送信）
- [ ] **カロリー・PFC（タンパク質・脂質・糖質）の推定表示**
- [ ] **LINE ログイン連携**（家族・チームメンバーと記録を共有）
- [ ] **週ごとのスプレッドシートシートを自動切り替え**
- [ ] **Cloud Run / Heroku へのデプロイ**（ngrok 不要の常時稼働）
- [ ] **食事画像のスプレッドシートへの保存**（Google Drive 連携）
- [ ] **練習スケジュールとの連動**（ハード練習日は高カロリー献立に）
- [ ] **Flex Message で見やすいUIに改善**

---

## ファイル構成

```
meal_management_tool/
├── app.py              ← メインアプリ（Flask + LINE Webhook）
├── session.py          ← ユーザーごとの会話状態管理
├── ai_analyzer.py      ← OpenAI Vision による食事解析
├── sheets.py           ← Google Sheets への保存・読み取り
├── meal_review.py      ← 日次・週次振り返りレポート生成
├── menu_generator.py   ← 翌週の夕食献立・買い物リスト生成
├── requirements.txt    ← 必要なPythonライブラリ一覧
├── .env.example        ← 環境変数のテンプレート（.env を作る元）
├── .env                ← 実際のAPIキー（自分で作成・非公開）
├── credentials.json    ← Google Cloud のサービスアカウントキー（自分で配置）
└── README.md           ← このファイル
```
