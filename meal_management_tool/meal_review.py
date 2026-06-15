"""
食事振り返りモジュール

Google Sheets に保存された食事記録を読み込み、
OpenAI API を使って日次・週次の振り返りレポートを生成します。

呼び出し方：
  records = get_today_records()
  review = create_daily_review(records)   ← 今日の振り返り

  records = get_week_records()
  review = create_weekly_review(records)  ← 週次振り返り
"""

import os
import httpx
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# McAfee などのセキュリティソフトが SSL 証明書を書き換える環境向けの対応
_http_client = httpx.Client(verify=False)

# OpenAI クライアントを初期化
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'), http_client=_http_client)


def create_daily_review(records: list) -> str:
    """
    今日の食事記録をもとに日次振り返りレポートを生成する。

    Args:
        records: get_today_records() で取得した今日の記録リスト

    Returns:
        str: LINEに送るための振り返りテキスト
    """
    # 記録データをプロンプト用テキストに変換
    records_text = _format_records(records)

    prompt = f"""あなたは栄養に詳しい食事コーチです。
今日の食事記録を見て、わかりやすい日次振り返りレポートを作成してください。
スポーツや運動をする人向けの視点（栄養バランス・食事タイミング）を大切にしてください。

【今日の食事記録】
{records_text}

以下の形式で、親しみやすい日本語で回答してください：

📊 今日の食事まとめ
（今日食べたものを2〜3文で簡潔にまとめてください）

✅ 良かった点
・（具体的に1〜2点）

💡 明日への改善アドバイス
・（具体的に1〜2点）

🏃 運動・スポーツとの関連
（今日の食事と運動パフォーマンスへの影響を1〜2文で）"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=600
    )

    review_body = response.choices[0].message.content
    return f"📅 今日の食事振り返り\n\n{review_body}"


def create_weekly_review(records: list) -> str:
    """
    直近1週間の食事記録をもとに週次振り返りレポートを生成する。

    Args:
        records: get_week_records() で取得した直近7日間の記録リスト

    Returns:
        str: LINEに送るための週次振り返りテキスト
    """
    records_text = _format_records(records)

    prompt = f"""あなたは栄養に詳しい食事コーチです。
直近1週間の食事記録を分析して、週次振り返りレポートを作成してください。
スポーツや運動をする人向けの視点で、食生活の傾向と改善点を教えてください。

【直近1週間の食事記録】
{records_text}

以下の形式で、具体的かつ親しみやすい日本語で回答してください：

📊 今週の食生活の傾向
（全体的な特徴を3〜4文で）

✅ 今週の良かった点
・（具体的に2〜3点）

⚠️ 改善が必要な点
・（具体的に2〜3点）

🥗 不足しがちな栄養素
（どんな食材を増やすべきか具体的に）

🏃 来週に向けたアドバイス
・（実践しやすい目標を2〜3点）"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=800
    )

    review_body = response.choices[0].message.content
    return f"📈 週次食事振り返り\n\n{review_body}"


def _format_records(records: list) -> str:
    """
    食事記録リストをプロンプトに貼り付けやすいテキスト形式に変換する内部関数。

    Args:
        records: 食事記録の辞書リスト

    Returns:
        str: 整形されたテキスト
    """
    if not records:
        return "記録なし"

    lines = []
    for r in records:
        date = r.get('日付', '不明')
        meal_type = r.get('食事区分', '不明')
        menu = r.get('推定メニュー', '（不明）')
        memo = r.get('メモ', '')

        line = f"・{date} [{meal_type}] {menu}"
        if memo:
            line += f"　※メモ: {memo}"
        lines.append(line)

    return '\n'.join(lines)
