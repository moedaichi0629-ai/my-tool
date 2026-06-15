# My Tool - AIツール集

日常をもっと便利にするAIツールを開発・公開するプロジェクトです。

## ツール一覧

### Live Album Tool
LINEグループのライブ写真を自動で取得し、Googleスプレッドシートに整理するツール。

- LINE Messaging API連携
- Google Sheets・Google Drive連携
- 写真の自動アルバム化

### Meal Management Tool
食事内容をAIが分析して、栄養バランスの確認とメニュー提案をするツール。

- AI食事分析
- 栄養バランス評価
- 週間メニュー自動生成

## セットアップ

```bash
# リポジトリをクローン
git clone https://github.com/moedaichi0629-ai/my-tool.git
cd my-tool

# 各ツールのディレクトリへ移動
cd live_album_tool   # または meal_management_tool

# 依存パッケージをインストール
pip install -r requirements.txt

# 環境変数を設定（.env.exampleを参考に）
cp .env.example .env
# .envファイルを編集してAPIキー等を入力
```

## 技術スタック

- Python 3.12
- LINE Messaging API
- Google Sheets API / Google Drive API
- Flask

## 注意事項

`.env` ファイル、`credentials.json`、`token.pickle` には認証情報が含まれるため、
リポジトリには含まれていません。各自で取得・設定してください。

## ライセンス

MIT
