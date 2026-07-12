# My Tool - AIツール集

日常の面倒な作業をAIで自動化する個人開発ツール群です。Web開発の学習用に作った小さなアプリも含めて、作ったものを一覧にしています。

## 目次

- [AI活用ツール](#ai活用ツール)
- [学習用ミニアプリ](#学習用ミニアプリ)
- [技術スタック](#技術スタック)
- [注意事項](#注意事項)

---

## AI活用ツール

### 📅 日程調整支援ツール
Googleカレンダーと連携し、空き時間の候補日と送信用文章を自動生成するWebアプリ。

- Googleカレンダーの空き時間を自動で抽出
- 候補日を最大5件提案（ダブルブッキング防止）
- LINE・メール用の文章を自動生成
- 確定した予定をカレンダーに直接登録

**デモ:** https://my-tool-xpv5memhwjfqnsupvuudfk.streamlit.app
**詳細:** [schedule-adjustment-tool/](schedule-adjustment-tool/)

---

### 🏠 AIホームページたたき台ジェネレーター
Google Places APIで公式サイト未設定の店舗を検索し、AIがホームページのたたき台を自動生成するWebアプリ。

- 地域・業種から店舗検索、公式サイト未設定店舗を抽出
- AIによるホームページたたき台生成（キャッチコピー〜お問い合わせまで7セクション）
- 生成したHPプレビューを単体HTMLファイルとしてダウンロード
- 検索結果をGoogleスプレッドシートに保存

**詳細:** [hp-tataki-generator/](hp-tataki-generator/)

---

### 📸 ライブアルバムツール
LINEグループの写真を自動で取得し、Google Drive・スプレッドシートに整理するツール。

- LINE Messaging API連携
- Google Drive・Sheets連携

**詳細:** [live_album_tool/](live_album_tool/)

---

### 🍽️ 食事管理ツール（LINE食事記録Bot）
食事写真をLINEに送るだけで、AIが食事内容を解析してGoogleスプレッドシートに記録するBot。

- AIによる食事写真解析（料理名・食材の自動判定）
- 日次・週次の振り返りレポート自動生成
- 翌週の献立・買い物リスト自動生成

**詳細:** [meal_management_tool/](meal_management_tool/)

---

### ✍️ 文章校正ツール
入力した文章をAIが校正・改善するツール。

**デモ:** https://writing-correction-tool-mygnto9hpkyehkzquhma9q.streamlit.app
**リポジトリ:** https://github.com/moedaichi0629-ai/writing-correction-tool

---

### 🎭 歌舞伎予習チャットボット
歌舞伎観劇前の予習をAIがサポートするチャットWebアプリ。

- AIとのチャットで演目・役者・用語を質問できる
- 配役情報を入力するだけで観劇前予習を自動生成
- 20演目・17シネマ歌舞伎作品・役者・用語をローカルデータで即検索

**デモ:** https://heroic-blini-04272e.netlify.app
**リポジトリ:** https://github.com/moedaichi0629-ai/kabuki-chatbot

---

### 🤖 LINE × Dify AIチャットボット
LINEで送ったメッセージをDify AIに転送し、AIの回答をLINEに返信するチャットボット。

**リポジトリ:** https://github.com/moedaichi0629-ai/line-dify-bot

---

## 学習用ミニアプリ

Web開発の基礎（外部API連携・状態管理・データ永続化）を学ぶために作った小規模アプリです。

### ✅ Todoリスト（Flask + Googleスプレッドシート）
タスクをGoogleスプレッドシートに保存するTodo管理アプリ。データベース不要で、スプレッドシートを開けばデータを直接確認・編集できる。

**デモ:** https://todo-app-1p8e.onrender.com
**リポジトリ:** https://github.com/moedaichi0629-ai/todo-app

### ✅ Todoリスト（Next.js + localStorage）
カテゴリ・タグ・期限日管理に対応したブラウザ完結型のTodoアプリ。

**デモ:** https://todo-list-app-six-blue.vercel.app/
**リポジトリ:** https://github.com/moedaichi0629-ai/todo-list-app

### ☀️ 天気予報アプリ
都市名を入力すると気温・天気・湿度・降水確率をまとめて確認できるWebアプリ。OpenWeatherMap API連携。

**デモ:** https://weather-forecast-app-liart-two.vercel.app/
**リポジトリ:** https://github.com/moedaichi0629-ai/weather-forecast-app

---

## 技術スタック

| カテゴリ | 技術 |
|---|---|
| 言語 | Python 3.10+ / TypeScript |
| フレームワーク | Next.js / React / Streamlit / Flask |
| AI | Claude API / OpenAI API / Dify |
| 認証 | Google OAuth 2.0 |
| 外部サービス | Google Calendar / Drive / Sheets / Places API, LINE API, OpenWeatherMap API |

## 注意事項

`.env`・`credentials.json`・`token.pickle`などの認証情報ファイルには機密情報が含まれるため、リポジトリには含まれていません。各自で取得・設定してください。

このリポジトリに含まれる一部のツール（文章校正ツール・歌舞伎予習チャットボット・LINE×Difyチャットボット・Todoリスト2種・天気予報アプリ）は、それぞれ独立したGitHubリポジトリとして管理しており、フォルダとしてはローカルに存在しますがこのリポジトリの管理対象外です（`.gitignore`で除外）。

## ライセンス

MIT
