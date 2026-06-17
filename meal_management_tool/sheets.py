"""
Google Sheets 連携モジュール

食事記録の保存・読み取りを行います。
スプレッドシートの構成：

  | 日付       | 食事区分 | 推定メニュー | AIコメント | メモ | 記録時刻            |
  |------------|----------|-------------|------------|------|---------------------|
  | 2024-01-15 | 夜       | 白米、唐揚げ | タンパク質... | 練習後 | 2024-01-15 20:30:00 |

前提：
  - 環境変数 GOOGLE_SERVICE_ACCOUNT_JSON にサービスアカウントのJSONを設定してください
  - 環境変数 GOOGLE_SPREADSHEET_ID にスプレッドシートIDを設定してください
"""

import os
import json
from datetime import datetime, timedelta

import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

load_dotenv()

# Google API に必要な権限スコープ
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

# スプレッドシートのヘッダー行（初回作成時に自動挿入される）
HEADER_ROW = ['日付', '食事区分', '推定メニュー', 'AIコメント', 'メモ', '記録時刻']

# シート名
WORKSHEET_NAME = '食事記録'


def _get_worksheet():
    """
    Google Sheets のワークシートオブジェクトを取得する内部関数。
    環境変数 GOOGLE_SERVICE_ACCOUNT_JSON からサービスアカウント認証情報を読み込みます。
    ワークシートが存在しない場合は自動作成し、ヘッダーを追加します。

    Returns:
        gspread.Worksheet: ワークシートオブジェクト

    Raises:
        ValueError: 環境変数が未設定またはJSONが不正な場合
    """
    # 環境変数からサービスアカウントのJSON文字列を取得
    service_account_json = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
    if not service_account_json:
        raise ValueError(
            "GOOGLE_SERVICE_ACCOUNT_JSON が環境変数に設定されていません。\n"
            "Render の Environment Variables に credentials.json の内容を貼り付けてください。"
        )

    try:
        service_account_info = json.loads(service_account_json)
    except json.JSONDecodeError as e:
        raise ValueError(f"GOOGLE_SERVICE_ACCOUNT_JSON の JSON 形式が正しくありません: {e}")

    # サービスアカウントの認証情報を生成
    creds = Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
    client = gspread.authorize(creds)

    # .env から スプレッドシートID を取得
    spreadsheet_id = os.getenv('GOOGLE_SPREADSHEET_ID')
    if not spreadsheet_id:
        raise ValueError(
            "GOOGLE_SPREADSHEET_ID が環境変数に設定されていません。\n"
            ".env.example を参考に設定してください。"
        )

    # スプレッドシートを開く
    spreadsheet = client.open_by_key(spreadsheet_id)

    # ワークシートを取得（なければ新規作成）
    try:
        worksheet = spreadsheet.worksheet(WORKSHEET_NAME)
    except gspread.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(
            title=WORKSHEET_NAME,
            rows=2000,
            cols=10
        )
        worksheet.append_row(HEADER_ROW)
        print(f"✅ ワークシート「{WORKSHEET_NAME}」を新規作成しました")

    return worksheet


def save_meal_record(date_str: str, meal_type: str, menu: str, comment: str, memo: str = '') -> None:
    """
    食事記録を Google Sheets に1行追記する。

    Args:
        date_str:  日付文字列（例：'2024-01-15'）
        meal_type: 食事区分（'朝' / '昼' / '夜' / '間食'）
        menu:      推定メニュー（AIの解析結果）
        comment:   AIコメント
        memo:      ユーザーが入力したメモ（省略可）
    """
    worksheet = _get_worksheet()

    recorded_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    row_data = [date_str, meal_type, menu, comment, memo, recorded_at]

    worksheet.append_row(row_data, value_input_option='USER_ENTERED')
    print(f"✅ Google Sheets に保存: {date_str} [{meal_type}]")


def get_today_records() -> list:
    """
    今日の食事記録をすべて取得する。

    Returns:
        list[dict]: 今日の記録リスト。
    """
    worksheet = _get_worksheet()
    today = datetime.now().strftime('%Y-%m-%d')
    all_records = worksheet.get_all_records()
    return [r for r in all_records if r.get('日付') == today]


def get_week_records() -> list:
    """
    直近7日間の食事記録をすべて取得する。

    Returns:
        list[dict]: 直近7日間の記録リスト。
    """
    worksheet = _get_worksheet()

    today = datetime.now().strftime('%Y-%m-%d')
    week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

    all_records = worksheet.get_all_records()
    return [
        r for r in all_records
        if week_ago <= r.get('日付', '') <= today
    ]
