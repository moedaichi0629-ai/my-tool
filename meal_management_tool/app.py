"""
LINE食事記録ツール - メインアプリケーション

【処理の流れ（MVP）】
  1. LINEユーザーが食事写真を送信
  2. LINE Webhookがこのアプリに届く（/callback エンドポイント）
  3. 食事区分（朝/昼/夜/間食）をクイックリプライで尋ねる
  4. ユーザーが食事区分を選択
  5. 任意のメモ入力を促す（スキップ可）
  6. バックグラウンドで AI 解析 + Google Sheets 保存 + LINE 返信

【追加コマンド】
  「今日の振り返り」 → 日次レポートを生成して送信
  「週次振り返り」   → 週次レポートを生成して送信
  「献立」          → 翌週の夕食献立と買い物リストを生成して送信
  「キャンセル」     → 進行中の操作をリセット
"""

import os
import threading
from datetime import datetime

from flask import Flask, request, abort
from dotenv import load_dotenv

from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.webhooks import MessageEvent, TextMessageContent, ImageMessageContent
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    MessagingApiBlob,
    ReplyMessageRequest,
    PushMessageRequest,
    TextMessage,
    QuickReply,
    QuickReplyItem,
    MessageAction,
)

# 各機能モジュールをインポート
from session import UserSession
from ai_analyzer import analyze_meal_image
from sheets import save_meal_record, get_today_records, get_week_records
from meal_review import create_daily_review, create_weekly_review
from menu_generator import generate_weekly_menu

# .env ファイルから環境変数を読み込む
load_dotenv()

# Flask アプリを初期化
app = Flask(__name__)

# LINE API の設定値（.env から読み込む）
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')

# LINE Webhook ハンドラーと API クライアント設定を初期化
handler = WebhookHandler(LINE_CHANNEL_SECRET)
configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)

# ユーザーセッションをメモリ上で管理
# キー: LINE の user_id（文字列）、値: UserSession オブジェクト
sessions: dict = {}


# ─────────────────────────────────────────────
# セッション管理ヘルパー
# ─────────────────────────────────────────────

def get_session(user_id: str) -> UserSession:
    """指定した user_id のセッションを返す（なければ新規作成）"""
    if user_id not in sessions:
        sessions[user_id] = UserSession()
    return sessions[user_id]


# ─────────────────────────────────────────────
# LINE メッセージ送信ヘルパー
# ─────────────────────────────────────────────

def reply_text(reply_token: str, text: str) -> None:
    """reply_token を使ってテキストを即座に返信する（Webhook 応答に使う）"""
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=reply_token,
                messages=[TextMessage(text=text)]
            )
        )


def reply_with_quick_reply(reply_token: str, text: str, items: list) -> None:
    """クイックリプライボタン付きのメッセージを返信する"""
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=reply_token,
                messages=[
                    TextMessage(
                        text=text,
                        quick_reply=QuickReply(items=items)
                    )
                ]
            )
        )


def push_text(user_id: str, text: str) -> None:
    """
    プッシュメッセージをユーザーに送信する。
    reply_token が使えない場面（バックグラウンド処理後など）で使用する。
    ※ プッシュメッセージは有料プランで使用量によって課金される場合があります。
    """
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.push_message(
            PushMessageRequest(
                to=user_id,
                messages=[TextMessage(text=text)]
            )
        )


def download_image(message_id: str) -> bytes:
    """LINE から画像のバイナリデータを取得する"""
    with ApiClient(configuration) as api_client:
        blob_api = MessagingApiBlob(api_client)
        return blob_api.get_message_content(message_id)


# ─────────────────────────────────────────────
# Webhook エンドポイント
# ─────────────────────────────────────────────

@app.route('/callback', methods=['POST'])
def callback():
    """
    LINE からの Webhook を受け取るエンドポイント。
    LINE サーバーから送られてくる署名を検証し、
    問題なければ handler に処理を委譲する。
    """
    # LINE が送ってくる署名（セキュリティ検証用）
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        # 署名が一致しない場合は不正なリクエストとして 400 を返す
        abort(400)

    # LINE サーバーには必ず 200 OK を返す（返さないと再送が繰り返される）
    return 'OK'


# ─────────────────────────────────────────────
# LINE イベントハンドラー
# ─────────────────────────────────────────────

@handler.add(MessageEvent, message=ImageMessageContent)
def on_image(event):
    """
    画像メッセージを受け取ったとき：
    セッションに画像IDを保存し、食事区分をクイックリプライで尋ねる。
    """
    user_id = event.source.user_id
    session = get_session(user_id)

    # 前のセッションをリセットして新しい記録を開始
    session.reset()
    session.image_id = event.message.id
    session.state = 'waiting_meal_type'

    # 食事区分のクイックリプライボタンを作成
    items = [
        QuickReplyItem(action=MessageAction(label="朝食", text="朝")),
        QuickReplyItem(action=MessageAction(label="昼食", text="昼")),
        QuickReplyItem(action=MessageAction(label="夕食", text="夜")),
        QuickReplyItem(action=MessageAction(label="間食", text="間食")),
    ]

    reply_with_quick_reply(
        event.reply_token,
        "📸 写真を受け取りました！\n食事区分を選んでください。",
        items
    )


@handler.add(MessageEvent, message=TextMessageContent)
def on_text(event):
    """
    テキストメッセージを受け取ったとき：
    ・特殊コマンド（今日の振り返り / 週次振り返り / 献立 / キャンセル）を処理
    ・セッションの状態に応じて食事区分やメモの入力を処理
    """
    user_id = event.source.user_id
    text = event.message.text.strip()
    session = get_session(user_id)

    # ── キャンセルコマンド ──
    if text == 'キャンセル':
        session.reset()
        reply_text(
            event.reply_token,
            "❌ キャンセルしました。\n食事写真を送って記録を再開できます！"
        )
        return

    # ── 今日の振り返り ──
    if text == '今日の振り返り':
        reply_text(event.reply_token, "⏳ 今日の振り返りを作成しています...\nしばらくお待ちください。")
        threading.Thread(target=_run_daily_review, args=(user_id,), daemon=True).start()
        return

    # ── 週次振り返り ──
    if text == '週次振り返り':
        reply_text(event.reply_token, "⏳ 週次振り返りを作成しています...\nしばらくお待ちください。")
        threading.Thread(target=_run_weekly_review, args=(user_id,), daemon=True).start()
        return

    # ── 献立提案 ──
    if text == '献立':
        reply_text(event.reply_token, "⏳ 翌週の献立を作成しています...\n少々お待ちください（30秒ほどかかる場合があります）。")
        threading.Thread(target=_run_menu_generation, args=(user_id,), daemon=True).start()
        return

    # ── セッション状態に応じた処理 ──

    if session.state == 'waiting_meal_type':
        # 食事区分の入力を受け付ける
        valid_types = ['朝', '昼', '夜', '間食']
        if text not in valid_types:
            reply_text(
                event.reply_token,
                "「朝」「昼」「夜」「間食」のいずれかを選んでください。\n「キャンセル」で最初からやり直せます。"
            )
            return

        session.meal_type = text
        session.state = 'waiting_memo'

        # メモ入力を促す（スキップボタン付き）
        items = [QuickReplyItem(action=MessageAction(label="スキップ", text="スキップ"))]
        reply_with_quick_reply(
            event.reply_token,
            f"食事区分：{text} ✅\n\nメモがあれば入力してください。\n（体調・水分量・練習メモなど）\n\n不要な場合は「スキップ」を押してください。",
            items
        )

    elif session.state == 'waiting_memo':
        # メモを記録し、AI 解析をバックグラウンドで開始する
        memo = '' if text == 'スキップ' else text

        # スレッドに渡す前にセッション値をローカル変数にコピー
        image_id = session.image_id
        meal_type = session.meal_type

        # セッションをリセット（次のリクエストに備える）
        session.reset()

        # 即座に「解析中」と返信（reply_token を消費）
        reply_text(
            event.reply_token,
            "⏳ 食事内容をAIが解析中です...\n結果はすぐに送ります！"
        )

        # バックグラウンドスレッドで解析・保存・返信を行う
        # （AI API 呼び出しに数秒かかるため、Webhook のタイムアウトを避けるための工夫）
        threading.Thread(
            target=_run_meal_analysis,
            args=(user_id, image_id, meal_type, memo),
            daemon=True
        ).start()

    else:
        # セッションが idle 状態のときに想定外のテキストが来た場合
        reply_text(
            event.reply_token,
            "食事写真を送ってください📸\n\n【使えるコマンド】\n"
            "・今日の振り返り\n"
            "・週次振り返り\n"
            "・献立\n"
            "・キャンセル"
        )


# ─────────────────────────────────────────────
# バックグラウンド処理（スレッドで実行）
# ─────────────────────────────────────────────

def _run_meal_analysis(user_id: str, image_id: str, meal_type: str, memo: str) -> None:
    """
    AI 解析 → Google Sheets 保存 → LINE 返信 を一連で行う。
    threading.Thread のターゲットとして呼ばれる。
    """
    try:
        # 1. LINE から画像を取得
        image_bytes = download_image(image_id)

        # 2. OpenAI Vision で食事内容を解析
        menu, comment = analyze_meal_image(image_bytes)

        # 3. Google Sheets に保存
        today = datetime.now().strftime('%Y-%m-%d')
        save_meal_record(today, meal_type, menu, comment, memo)

        # 4. 解析結果を LINE にプッシュ送信
        result_message = (
            "✅ 食事記録が完了しました！\n\n"
            f"🍽️ 推定メニュー：\n{menu}\n\n"
            f"💬 AIコメント：\n{comment}\n\n"
            "📊 記録内容：\n"
            f"  日付：{today}\n"
            f"  食事区分：{meal_type}\n"
            f"  メモ：{memo if memo else 'なし'}\n\n"
            "Googleスプレッドシートに保存しました📋"
        )
        push_text(user_id, result_message)

    except Exception as e:
        # エラーが発生した場合もユーザーに通知する
        push_text(user_id, f"❌ エラーが発生しました。\n{str(e)}\n\nしばらくしてから再度お試しください。")


def _run_daily_review(user_id: str) -> None:
    """今日の振り返りを生成してプッシュ送信する"""
    try:
        records = get_today_records()
        if not records:
            push_text(user_id, "📭 今日の食事記録がまだありません。\n食事写真を送って記録を始めましょう！")
            return
        review = create_daily_review(records)
        push_text(user_id, review)
    except Exception as e:
        push_text(user_id, f"❌ 振り返りの作成中にエラーが発生しました。\n{str(e)}")


def _run_weekly_review(user_id: str) -> None:
    """週次振り返りを生成してプッシュ送信する"""
    try:
        records = get_week_records()
        if not records:
            push_text(user_id, "📭 直近1週間の食事記録がありません。\nまずは食事写真を送って記録を積みましょう！")
            return
        review = create_weekly_review(records)
        push_text(user_id, review)
    except Exception as e:
        push_text(user_id, f"❌ 週次振り返りの作成中にエラーが発生しました。\n{str(e)}")


def _run_menu_generation(user_id: str) -> None:
    """翌週の献立を生成してプッシュ送信する"""
    try:
        records = get_week_records()
        menu_proposal = generate_weekly_menu(records)
        push_text(user_id, menu_proposal)
    except Exception as e:
        push_text(user_id, f"❌ 献立の作成中にエラーが発生しました。\n{str(e)}")


# ─────────────────────────────────────────────
# アプリ起動
# ─────────────────────────────────────────────

if __name__ == '__main__':
    print("=" * 50)
    print("LINE 食事記録ツール を起動します")
    print("ポート: 5000")
    print("ngrok で公開してから LINE の Webhook URL を設定してください")
    print("=" * 50)
    # debug=True にすると変更を自動で再読み込みするが、本番では False にする
    app.run(port=5000, debug=True)
