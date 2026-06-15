# -*- coding: utf-8 -*-
# ============================================================
# app.py — LINE Messaging API Webhook サーバー（Flask）
#
# 【処理の流れ】
# 1. ユーザーが写真を送る → imagesフォルダに保存
# 2. ユーザーが「完了」と送る → ライブ名を尋ねる
# 3. ライブ名を受け取る → 参加日を尋ねる
# 4. 参加日を受け取る → 会場を尋ねる
# 5. 会場を受け取る → バックグラウンドでアルバム作成開始
# 6. 完成したらLINEにGoogle DocsのURLを返信
# ============================================================

import os
import threading
from pathlib import Path

from flask import Flask, request, abort
from dotenv import load_dotenv

from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    MessagingApiBlob,
    ReplyMessageRequest,
    PushMessageRequest,
    TextMessage,
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent,
    ImageMessageContent,
)

# セッション管理モジュール（session.pyから読み込み）
from session import (
    get_session,
    reset_session,
    STATE_IDLE,
    STATE_COLLECTING,
    STATE_WAIT_LIVE_NAME,
    STATE_WAIT_DATE,
    STATE_WAIT_VENUE,
    STATE_PROCESSING,
    STATE_WAIT_YEAR,
)

# アルバム作成モジュール（album.pyから読み込み）
from album import run_album_pipeline


# ============================================================
# 初期設定
# ============================================================

# .envファイルから環境変数を読み込む
load_dotenv()

# LINE Messaging APIの認証情報を環境変数から取得
LINE_CHANNEL_SECRET       = os.environ.get('LINE_CHANNEL_SECRET', '')
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN', '')

if not LINE_CHANNEL_SECRET or not LINE_CHANNEL_ACCESS_TOKEN:
    print("[エラー] .env ファイルに LINE_CHANNEL_SECRET と LINE_CHANNEL_ACCESS_TOKEN を設定してください。")
    print("  .env.example を参考に .env ファイルを作成してください。")
    exit(1)

# Flaskアプリを作成
app = Flask(__name__)

# LINEのWebhook署名を検証するハンドラー
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# LINE APIクライアントの設定
configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)

# 写真の一時保存先フォルダ（images/{user_id}/ という構成で保存）
IMAGES_TEMP_DIR = Path(__file__).parent / 'images'
IMAGES_TEMP_DIR.mkdir(exist_ok=True)


# ============================================================
# ヘルパー関数
# ============================================================

def reply_text(reply_token: str, text: str):
    """
    LINEに返信メッセージを送る関数。
    返信トークン（reply_token）は1回しか使えないため、最初のメッセージ返信に使う。
    """
    with ApiClient(configuration) as api_client:
        api = MessagingApi(api_client)
        api.reply_message(ReplyMessageRequest(
            reply_token=reply_token,
            messages=[TextMessage(text=text)]
        ))


def push_text(user_id: str, text: str):
    """
    LINEにプッシュメッセージを送る関数。
    アルバム作成完了後など、任意のタイミングでメッセージを送るために使う。
    """
    with ApiClient(configuration) as api_client:
        api = MessagingApi(api_client)
        api.push_message(PushMessageRequest(
            to=user_id,
            messages=[TextMessage(text=text)]
        ))


def download_image(message_id: str, save_path: Path):
    """
    LINEから送られた画像をダウンロードしてローカルファイルに保存する関数。

    Args:
        message_id: LINEメッセージのID（画像を特定するために使う）
        save_path:  保存先のファイルパス
    """
    with ApiClient(configuration) as api_client:
        blob_api = MessagingApiBlob(api_client)
        # LINEサーバーから画像データ（バイト列）を取得
        content = blob_api.get_message_content(message_id=message_id)

    # ファイルに書き込む
    with open(str(save_path), 'wb') as f:
        f.write(content)


# ============================================================
# アルバム作成（バックグラウンド処理）
# ============================================================

def process_album_in_background(user_id: str):
    """
    アルバム作成をバックグラウンドで実行する関数。

    LINEのWebhookは5秒以内に応答しなければならないため、
    時間のかかるアルバム作成処理は別スレッドで実行します。
    完成したらLINEにプッシュメッセージでURLを送ります。
    """
    session = get_session(user_id)

    try:
        # セッションからライブ情報と写真パスを取り出す
        info = {
            'live_name': session['live_name'],
            'date':      session['date'],
            'venue':     session['venue'],
        }
        image_paths = session['photos']

        # アルバム作成を実行してURLを取得（user_idを渡してSheetsに記録）
        doc_url = run_album_pipeline(info, image_paths, user_id)

        # 完成をLINEで通知
        push_text(
            user_id,
            f"✅ アルバムが完成しました！\n\n"
            f"📄 GoogleドキュメントURL:\n{doc_url}\n\n"
            f"URLをタップして開いてください。"
        )

        # 処理が終わったら一時保存した写真ファイルを削除する
        for path in image_paths:
            try:
                os.remove(path)
            except Exception:
                pass

    except Exception as e:
        # エラーが発生した場合もLINEで通知する
        push_text(
            user_id,
            f"❌ エラーが発生しました。\n\n"
            f"エラー内容:\n{e}\n\n"
            f"credentials.json が正しく設置されているか確認してください。"
        )

    finally:
        # 成功・失敗に関わらずセッションをリセットして次の利用に備える
        reset_session(user_id)


# ============================================================
# 振り返り（バックグラウンド処理）
# ============================================================

def send_yearly_review_in_background(user_id: str, year: int):
    """指定した年のライブ一覧をGoogle Sheetsから取得してLINEに送る"""
    try:
        from sheets import get_lives_by_year
        lives = get_lives_by_year(year, user_id)

        if not lives:
            push_text(user_id, f"📅 {year}年のライブ記録はまだありません。")
            return

        lines = [f"📅 {year}年のライブ一覧（{len(lives)}件）\n"]
        for i, live in enumerate(lives, 1):
            lines.append(
                f"{i}. {live['live_name']}\n"
                f"   📅 {live['date']}\n"
                f"   📍 {live['venue']}"
            )

        push_text(user_id, "\n\n".join(lines))

    except Exception as e:
        push_text(user_id, f"❌ 振り返りの取得に失敗しました。\n{e}")


# ============================================================
# Webhookエンドポイント（LINEからのリクエストを受け取る）
# ============================================================

@app.route('/callback', methods=['POST'])
def callback():
    """
    LINEプラットフォームからWebhookリクエストを受け取るエンドポイント。
    署名を検証してから各イベントのハンドラーに処理を渡す。
    """
    # LINEからのリクエストに含まれる署名を取得
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)

    try:
        # 署名を検証（不正なリクエストを弾く）
        handler.handle(body, signature)
    except InvalidSignatureError:
        # 署名が不正な場合は400エラーを返す
        abort(400)

    return 'OK'


# ============================================================
# 画像メッセージのハンドラー（写真を受け取ったとき）
# ============================================================

@handler.add(MessageEvent, message=ImageMessageContent)
def handle_image(event):
    """
    ユーザーが写真を送ったときの処理。
    写真をimagesフォルダにダウンロードして保存する。
    """
    user_id     = event.source.user_id
    reply_token = event.reply_token
    session     = get_session(user_id)

    # アルバム作成中は新しい写真を受け付けない
    if session['state'] == STATE_PROCESSING:
        reply_text(reply_token, "⏳ 現在アルバムを作成中です。完了までお待ちください。")
        return

    # ユーザーごとの一時フォルダを作成
    user_dir = IMAGES_TEMP_DIR / user_id
    user_dir.mkdir(exist_ok=True)

    # 受け取った枚数に基づいてファイル名を決める（例: photo_001.jpg）
    photo_index = len(session['photos']) + 1
    save_path = user_dir / f"photo_{photo_index:03d}.jpg"

    # LINEから画像をダウンロードして保存
    download_image(event.message.id, save_path)
    session['photos'].append(str(save_path))

    # 状態を「写真収集中」に更新
    session['state'] = STATE_COLLECTING

    count = len(session['photos'])
    reply_text(
        reply_token,
        f"📷 写真 {count} 枚を受け取りました。\n"
        f"他にも送れます。\n\n"
        f"写真が揃ったら「完了」と送ってください。"
    )


# ============================================================
# テキストメッセージのハンドラー（文字を受け取ったとき）
# ============================================================

@handler.add(MessageEvent, message=TextMessageContent)
def handle_text(event):
    """
    ユーザーがテキストを送ったときの処理。
    会話の状態（state）に応じて、ライブ名・日付・会場を順番に受け取る。
    """
    user_id     = event.source.user_id
    reply_token = event.reply_token
    text        = event.message.text.strip()
    session     = get_session(user_id)
    state       = session['state']

    print(f"[受信] state={state!r} text={text!r} (len={len(text)})")

    # ---- アルバム作成中は受け付けない ----
    if state == STATE_PROCESSING:
        reply_text(reply_token, "⏳ 現在アルバムを作成中です。完了までお待ちください。")
        return

    # ---- 「キャンセル」→ セッションをリセットして最初からやり直し ----
    if text == 'キャンセル':
        reset_session(user_id)
        reply_text(
            reply_token,
            "❌ キャンセルしました。\n\n"
            "最初からやり直す場合は写真を送ってください。"
        )
        return

    # ---- 写真収集中 + 「完了」→ ライブ名を尋ねる ----
    if state == STATE_COLLECTING and text == '完了':
        session['state'] = STATE_WAIT_LIVE_NAME
        reply_text(
            reply_token,
            f"✅ 写真 {len(session['photos'])} 枚を受け取りました。\n\n"
            f"📝 ライブ名を入力してください。\n"
            f"例：〇〇 LIVE TOUR 2024"
        )
        return

    # ---- ライブ名を受け取る → 参加日を尋ねる ----
    if state == STATE_WAIT_LIVE_NAME:
        session['live_name'] = text
        session['state']     = STATE_WAIT_DATE
        reply_text(
            reply_token,
            f"📅 参加日を入力してください。\n"
            f"例：2024年3月15日"
        )
        return

    # ---- 参加日を受け取る → 会場を尋ねる ----
    if state == STATE_WAIT_DATE:
        session['date']  = text
        session['state'] = STATE_WAIT_VENUE
        reply_text(
            reply_token,
            f"📍 会場を入力してください。\n"
            f"例：東京ドーム"
        )
        return

    # ---- 会場を受け取る → アルバム作成を開始 ----
    if state == STATE_WAIT_VENUE:
        session['venue'] = text
        session['state'] = STATE_PROCESSING

        # 受け取った内容を確認メッセージとして送る
        reply_text(
            reply_token,
            f"✅ 情報を受け取りました！\n\n"
            f"ライブ名：{session['live_name']}\n"
            f"参加日　：{session['date']}\n"
            f"会場　　：{session['venue']}\n"
            f"写真　　：{len(session['photos'])}枚\n\n"
            f"⏳ アルバムを作成中です...\n"
            f"完成したらこちらにURLをお送りします。"
        )

        # バックグラウンドスレッドでアルバム作成を開始
        # （Webhookは5秒以内に応答が必要なため、重い処理は別スレッドで実行）
        thread = threading.Thread(
            target=process_album_in_background,
            args=(user_id,),
            daemon=True,
        )
        thread.start()
        return

    # ---- 待機中 + 「振り返り」→ 年を尋ねる ----
    if state == STATE_IDLE and text == '振り返り':
        session['state'] = STATE_WAIT_YEAR
        reply_text(
            reply_token,
            "📅 何年の振り返りを見ますか？\n\n"
            "年を数字4桁で入力してください。\n"
            "例：2025"
        )
        return

    # ---- 年の入力を受け取る → ライブ一覧を返す ----
    if state == STATE_WAIT_YEAR:
        if not text.isdigit() or len(text) != 4:
            reply_text(reply_token, "⚠️ 4桁の年を入力してください。\n例：2025")
            return

        year = int(text)
        reset_session(user_id)
        reply_text(reply_token, f"⏳ {year}年のライブを検索中...")

        thread = threading.Thread(
            target=send_yearly_review_in_background,
            args=(user_id, year),
            daemon=True,
        )
        thread.start()
        return

    # ---- 待機中（IDLE）または想定外のテキスト → 使い方を案内 ----
    reply_text(
        reply_token,
        "📸 まず写真を送ってください。\n"
        "複数枚送れます。\n\n"
        "写真を送り終えたら「完了」と入力してください。\n\n"
        "過去のライブを振り返るには「振り返り」と送ってください。"
    )


# ============================================================
# サーバー起動
# ============================================================

if __name__ == '__main__':
    print("=" * 50)
    print("  ライブ思い出アルバム LINEボット 起動中...")
    print("=" * 50)
    print()
    print("【重要】Google認証を事前に完了させます。")
    print("初回起動時はブラウザが開くのでGoogleアカウントにログインしてください。")
    print()

    # サーバー起動前にGoogle認証を完了させておく
    # （バックグラウンドスレッドからブラウザを開けない場合があるため）
    try:
        from main import authenticate
        authenticate()
        print()
        print("Google認証完了。LINEボットを起動します。")
        print()
        print("ngrok を起動して Webhook URL を LINE Developers に設定してください。")
        print("  例: https://xxxx-xx-xx.ngrok-free.app/callback")
        print()
    except Exception as e:
        print(f"[警告] Google認証に失敗しました: {e}")
        print("credentials.json が正しく設置されているか確認してください。")
        print()

    # Flaskサーバーを起動（ポート5000番）
    app.run(host='0.0.0.0', port=5000, debug=False)
