# My Tool - AIツール集

## プロジェクト概要

**My Tool** は、日常の面倒な作業を AI で自動化する小規模ツール群です。

写真の整理・食事管理など「手間はかかるけど毎日やること」をテーマに、LINE や Google サービスと連携したツールを個人開発しています。各ツールは独立して動作し、Python + Flask をベースに構築しています。

| ツール | 目的 | 主な連携サービス |
|---|---|---|
| Live Album Tool | LINEグループの写真を自動でアルバム化 | LINE API / Google Drive |
| Meal Management Tool | 食事をAIが分析して栄養管理・献立提案 | Claude API / Flask |

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
