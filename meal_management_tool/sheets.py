"""
Google Sheets 連携モジュール

食事記録の保存・読み取りを行います。
スプレッドシートの構成：

  | 日付       | 食事区分 | 推定メニュー | AIコメント | メモ | 記録時刻            |
  |------------|----------|-------------|------------|------|---------------------|
  | 2024-01-15 | 夜       | 白米、唐揚げ | タンパク質... | 練習後 | 2024-01-15 20:30:00 |

前提：
  - プロジェクトルートに credentials.json が必要です
  - .env に GOOGLE_SPREADSHEET_ID を設定してください
"""

import os
import ssl
import urllib3
import requests
from datetime import datetime, timedelta
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

# McAfee などが SSL 証明書を書き換える環境向けの対応（ローカル開発環境用）
ssl._create_default_https_context = ssl._create_unverified_context
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# requests ライブラリのデフォルト SSL 検証を無効化
_original_request = requests.Session.request
def _patched_request(self, *args, **kwargs):
    kwargs.setdefault('verify', False)
    return _original_request(self, *args, **kwargs)
requests.Session.request = _patched_request

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
    ワークシートが存在しない場合は自動作成し、ヘッダーを追加します。

    Returns:
        gspread.Worksheet: ワークシートオブジェクト

    Raises:
        FileNotFoundError: credentials.json が見つからない場合
        Exception: スプレッドシートIDが無効な場合など
    """
    # credentials.json が存在するか確認
    if not os.path.exists('credentials.json'):
        raise FileNotFoundError(
            "credentials.json が見つかりません。\n"
            "README.md の「Google Cloud の設定」を参照して配置してください。"
        )

    # サービスアカウントの認証情報を読み込む
    creds = Credentials.from_service_account_file('credentials.json', scopes=SCOPES)
    client = gspread.authorize(creds)

    # .env から スプレッドシートID を取得
    spreadsheet_id = os.getenv('GOOGLE_SPREADSHEET_ID')
    if not spreadsheet_id:
        raise ValueError(
            "GOOGLE_SPREADSHEET_ID が .env に設定されていません。\n"
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

    # 現在時刻を文字列で取得
    recorded_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # 1行分のデータをリストで作成
    row_data = [date_str, meal_type, menu, comment, memo, recorded_at]

    # スプレッドシートの末尾に1行追加
    worksheet.append_row(row_data, value_input_option='USER_ENTERED')
    print(f"✅ Google Sheets に保存: {date_str} [{meal_type}]")


def get_today_records() -> list:
    """
    今日の食事記録をすべて取得する。

    Returns:
        list[dict]: 今日の記録リスト。
                    各要素は {'日付': ..., '食事区分': ..., ...} の辞書。
    """
    worksheet = _get_worksheet()
    today = datetime.now().strftime('%Y-%m-%d')

    # スプレッドシートの全行を辞書のリストとして取得
    all_records = worksheet.get_all_records()

    # 今日の日付に一致する行だけを抽出
    return [r for r in all_records if r.get('日付') == today]


def get_week_records() -> list:
    """
    直近7日間の食事記録をすべて取得する。

    Returns:
        list[dict]: 直近7日間の記録リスト。
    """
    worksheet = _get_worksheet()

    # 7日前〜今日の日付範囲を計算
    today = datetime.now().strftime('%Y-%m-%d')
    week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

    all_records = worksheet.get_all_records()

    # 日付でフィルタリング（文字列比較で大小比較できる YYYY-MM-DD 形式）
    return [
        r for r in all_records
        if week_ago <= r.get('日付', '') <= today
    ]
