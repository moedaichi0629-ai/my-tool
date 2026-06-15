"""
献立提案モジュール

直近1週間の食事傾向をもとに、翌週の平日5日分（月〜金）の
夕食献立を OpenAI API で自動生成します。
主菜・副菜・汁物の3品構成と買い物リストを出力します。
"""

import os
from datetime import datetime, timedelta
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# OpenAI クライアントを初期化（APIキーは環境変数から読み込む）
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))


def generate_weekly_menu(records: list) -> str:
    """
    翌週の平日5日分の夕食献立と買い物リストを生成する。

    Args:
        records: get_week_records() で取得した直近1週間の記録リスト
                 （記録がなくても動作します。その場合は傾向考慮なし）

    Returns:
        str: 献立提案テキスト（買い物リスト付き）
    """
    # 翌週の月〜金の日付を計算
    weekday_dates = _get_next_weekday_dates()

    # 直近の夕食記録をテキスト化（重複を避けるためのヒント）
    recent_dinners_text = _summarize_recent_dinners(records)

    prompt = f"""あなたは栄養バランスに詳しい料理家です。
以下の条件で翌週の平日5日分の夕食献立を提案してください。

{recent_dinners_text}

【献立の条件】
・月〜金の5日分（夕食のみ）
・作りやすく、練習・仕事後でも調理しやすい料理
・たんぱく質・鉄分・ビタミンなど不足しがちな栄養素を意識する
・直近に食べたものとなるべく重複しない
・主菜・副菜・汁物の3品構成で記載する

【翌週の日程】
・月曜日：{weekday_dates[0]}
・火曜日：{weekday_dates[1]}
・水曜日：{weekday_dates[2]}
・木曜日：{weekday_dates[3]}
・金曜日：{weekday_dates[4]}

以下の形式で回答してください：

🍽️ 翌週の夕食献立

【月曜日 {weekday_dates[0]}】
・主菜：（料理名）
・副菜：（料理名）
・汁物：（料理名）

【火曜日 {weekday_dates[1]}】
・主菜：（料理名）
・副菜：（料理名）
・汁物：（料理名）

【水曜日 {weekday_dates[2]}】
・主菜：（料理名）
・副菜：（料理名）
・汁物：（料理名）

【木曜日 {weekday_dates[3]}】
・主菜：（料理名）
・副菜：（料理名）
・汁物：（料理名）

【金曜日 {weekday_dates[4]}】
・主菜：（料理名）
・副菜：（料理名）
・汁物：（料理名）

---

🛒 買い物リスト

【野菜・きのこ類】
・
・

【肉・魚・卵・豆腐】
・
・

【その他（調味料・缶詰・乾物など）】
・
・"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1400
    )

    return response.choices[0].message.content


def _get_next_weekday_dates() -> list:
    """
    翌週の月曜〜金曜の日付（MM/DD形式）をリストで返す内部関数。

    Returns:
        list[str]: ['01/15', '01/16', '01/17', '01/18', '01/19'] のような5要素リスト
    """
    today = datetime.now()
    weekday = today.weekday()  # 0=月曜, 6=日曜

    # 次の月曜日までの日数を計算
    days_until_monday = (7 - weekday) % 7
    if days_until_monday == 0:
        # 今日が月曜の場合は来週の月曜へ
        days_until_monday = 7

    next_monday = today + timedelta(days=days_until_monday)

    # 月〜金の5日分を生成
    return [
        (next_monday + timedelta(days=i)).strftime('%m/%d（%a）')
        for i in range(5)
    ]


def _summarize_recent_dinners(records: list) -> str:
    """
    直近の夕食記録を献立プロンプト用に整形する内部関数。
    直近に食べたものを把握することで、献立の重複を防ぎます。

    Args:
        records: 食事記録の辞書リスト

    Returns:
        str: プロンプトに挿入するためのテキスト（記録なしなら空文字）
    """
    if not records:
        return ""

    # 夕食（食事区分が「夜」）の記録だけ抽出
    dinner_records = [r for r in records if r.get('食事区分') == '夜']

    if not dinner_records:
        return ""

    lines = ["【直近の夕食（重複を避けるための参考情報）】"]
    for r in dinner_records:
        date = r.get('日付', '')
        menu = r.get('推定メニュー', '')
        if menu:
            # メニューが長い場合は先頭60文字だけ使用
            lines.append(f"・{date}：{menu[:60]}")

    return '\n'.join(lines) + '\n'
