"""
AI食事解析モジュール

OpenAI の GPT-4o（画像認識対応モデル）を使って、
食事写真から料理名・食材を推定し、コメントを生成します。

使い方：
  image_bytes = download_image(message_id)  ← LINEから画像を取得
  menu, comment = analyze_meal_image(image_bytes)  ← このモジュールで解析
"""

import os
import base64
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# OpenAI クライアントを初期化（APIキーは環境変数から読み込む）
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))


def analyze_meal_image(image_bytes: bytes) -> tuple:
    """
    食事画像をAIで解析し、推定メニューとコメントを返す。

    Args:
        image_bytes: LINEからダウンロードした画像のバイナリデータ

    Returns:
        tuple: (推定メニュー文字列, AIコメント文字列)

    例外:
        OpenAI APIのエラーはそのまま上位に伝播させる
    """
    # 画像バイナリを Base64 文字列に変換（OpenAI API の要件）
    base64_image = base64.b64encode(image_bytes).decode('utf-8')

    # GPT-4o に送るプロンプト（日本語で返答させる）
    prompt = """あなたは栄養に詳しい食事記録アシスタントです。
この食事写真を見て、以下の形式で日本語で回答してください。

【推定メニュー】
（料理名と主な食材を具体的にリストアップしてください。
  例：白米、鶏の唐揚げ（2個）、味噌汁（豆腐・わかめ）、キャベツサラダ）

【一言コメント】
（食事のバランスや特徴について2〜3文で簡潔にコメントしてください。
  スポーツや運動をする人向けの視点（エネルギー補給・タンパク質など）も
  さりげなく入れてください。）

※ 料理が判別できない場合は「不明な食事」と記載し、
  写真から読み取れた情報（色・形・容器など）を教えてください。"""

    # OpenAI Vision API を呼び出す
    response = client.chat.completions.create(
        model="gpt-4o",                    # 画像認識に対応したモデル
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}",
                            "detail": "high"   # 画像を高精度で解析
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ],
        max_tokens=600   # レスポンスの最大トークン数
    )

    full_response = response.choices[0].message.content

    # レスポンスから「推定メニュー」と「一言コメント」を分離する
    menu, comment = _parse_response(full_response)
    return menu, comment


def _parse_response(response_text: str) -> tuple:
    """
    GPT-4o のレスポンスを「メニュー」と「コメント」に分割する内部関数。

    Args:
        response_text: GPT-4o が返したテキスト全体

    Returns:
        tuple: (メニュー文字列, コメント文字列)
    """
    menu = ""
    comment = ""

    # 【推定メニュー】と【一言コメント】の両方が存在する場合は分割
    if "【推定メニュー】" in response_text and "【一言コメント】" in response_text:
        parts = response_text.split("【一言コメント】")
        menu = parts[0].replace("【推定メニュー】", "").strip()
        comment = parts[1].strip() if len(parts) > 1 else "（コメントなし）"
    else:
        # フォーマットが崩れた場合は全体をメニューとして扱う
        menu = response_text.strip()
        comment = "（コメントの取得に失敗しました）"

    return menu, comment
