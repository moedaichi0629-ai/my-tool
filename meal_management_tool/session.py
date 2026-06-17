"""
セッション管理モジュール

LINEは1メッセージごとに独立したリクエストが来るため、
複数ステップの会話（画像受信 → 食事区分選択 → メモ入力）を
つなぎ合わせるためにセッション管理が必要です。

状態（state）の遷移図：
  idle
    ↓ 画像を受信
  waiting_meal_type
    ↓ 「朝」「昼」「夜」「間食」のいずれかを受信
  waiting_memo
    ↓ メモ or「スキップ」を受信
  idle（AI解析→保存→返信）
"""


class UserSession:
    """
    ユーザーごとの会話状態を保持するクラス。
    セッションはメモリ上に保存するため、サーバー再起動でリセットされます。
    """

    def __init__(self):
        """セッションを初期状態で作成する"""
        self.reset()

    def reset(self):
        """セッションを完全にリセットして初期状態に戻す"""
        self.state = 'idle'       # 現在の会話状態
        self.image_id = None      # LINEの画像メッセージID（AI解析に使う）
        self.meal_type = None     # 食事区分（朝 / 昼 / 夜 / 間食）
        self.memo = ''            # ユーザーが入力した任意メモ

    def __repr__(self):
        return f"UserSession(state={self.state}, image_id={self.image_id}, meal_type={self.meal_type})"
