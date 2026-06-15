# -*- coding: utf-8 -*-
# ============================================================
# session.py — LINEユーザーごとの会話状態を管理するモジュール
#
# LINEは「1回のメッセージ = 1回のWebhook」という仕組みのため、
# ユーザーが複数回に分けて送った情報（写真・ライブ名・日付・会場）を
# 一時的に記憶しておく必要があります。
# このファイルはその「記憶」を担当します。
# ============================================================

# ---- 会話の状態を表す定数 ----
# どの入力を待っているかをこの定数で管理します
STATE_IDLE           = 'IDLE'           # 待機中（最初の状態）
STATE_COLLECTING     = 'COLLECTING'     # 写真を受け取り中
STATE_WAIT_LIVE_NAME = 'WAIT_LIVE_NAME' # ライブ名の入力待ち
STATE_WAIT_DATE      = 'WAIT_DATE'      # 参加日の入力待ち
STATE_WAIT_VENUE     = 'WAIT_VENUE'     # 会場の入力待ち
STATE_PROCESSING     = 'PROCESSING'     # アルバム作成中（処理中）
STATE_WAIT_YEAR      = 'WAIT_YEAR'      # 振り返り年の入力待ち

# ---- セッションデータの保存先 ----
# キー: LINEのユーザーID（文字列）
# 値:   そのユーザーの現在の状態・入力データ
_sessions = {}


def get_session(user_id: str) -> dict:
    """
    ユーザーのセッション（状態と入力データ）を取得する。
    まだセッションがない場合は初期状態で作成して返す。
    """
    if user_id not in _sessions:
        reset_session(user_id)
    return _sessions[user_id]


def reset_session(user_id: str):
    """
    ユーザーのセッションを初期状態にリセットする。
    アルバム作成が完了したとき、またはエラー時に呼び出す。
    """
    _sessions[user_id] = {
        'state':     STATE_IDLE,  # 現在の会話の状態
        'photos':    [],          # ダウンロードした写真のパスリスト
        'live_name': None,        # ライブ名
        'date':      None,        # 参加日
        'venue':     None,        # 会場
    }
