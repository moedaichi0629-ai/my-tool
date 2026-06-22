# My Tool - AIツール集

日常の面倒な作業を AI で自動化する個人開発ツール群です。

## ツール一覧

### 📅 日程調整支援ツール
Googleカレンダーと連携し、空き時間の候補日と送信用文章を自動生成するWebアプリ。

- Googleカレンダーの空き時間を自動で抽出
- 候補日を最大5件提案（ダブルブッキング防止）
- LINE・メール用の文章を4パターン自動生成
- 確定した予定をカレンダーに直接登録
- Streamlit Cloud でホスティング済み

**デモ:** https://my-tool-xpv5memhwjfqnsupvuudfk.streamlit.app
**ランディングページ:** https://moedaichi0629-ai.github.io/my-tool/
**詳細:** [schedule-adjustment-tool/README.md](schedule-adjustment-tool/README.md)

---

### ✍️ 文章校正ツール
入力した文章をAIが校正・改善するツール。

**詳細:** [writing-correction-tool/](writing-correction-tool/)

---

### 📸 ライブアルバムツール
LINEグループの写真を自動で取得し、Google Driveに整理するツール。

- LINE Messaging API 連携
- Google Drive・Sheets 連携

**詳細:** [live_album_tool/](live_album_tool/)

---

### 🍽️ 食事管理ツール
食事内容をAIが分析して、栄養バランスの確認とメニュー提案をするツール。

- AI食事分析（Claude API）
- 栄養バランス評価・週間メニュー提案

**詳細:** [meal_management_tool/](meal_management_tool/)

---

## 技術スタック

| カテゴリ | 技術 |
|---|---|
| 言語 | Python 3.10+ |
| UI フレームワーク | Streamlit / Flask |
| AI | Claude API / OpenAI API |
| 認証 | Google OAuth 2.0 |
| 外部サービス | Google Calendar / Drive / Sheets, LINE API |

## 注意事項

`.env`・`client_secrets.json`・`credentials.json`・`token.pickle` には認証情報が含まれるため、リポジトリには含まれていません。各自で取得・設定してください。

## ライセンス

MIT
