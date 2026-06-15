# -*- coding: utf-8 -*-
# ============================================================
# sheets.py — Google Sheetsにライブ記録を保存・取得するモジュール
# ============================================================

from datetime import datetime
from googleapiclient.discovery import build
from main import authenticate

SPREADSHEET_NAME = "ライブアルバム記録"
SHEET_NAME       = "ライブ記録"
HEADERS          = ["ユーザーID", "ライブ名", "参加日", "会場", "Google Docs URL", "記録日時"]


def _get_services():
    creds          = authenticate()
    drive_service  = build('drive',  'v3', credentials=creds)
    sheets_service = build('sheets', 'v4', credentials=creds)
    return drive_service, sheets_service


def _get_or_create_spreadsheet(drive_service, sheets_service):
    results = drive_service.files().list(
        q=f"name='{SPREADSHEET_NAME}' and mimeType='application/vnd.google-apps.spreadsheet' and trashed=false",
        fields="files(id)"
    ).execute()
    files = results.get('files', [])

    if files:
        return files[0]['id']

    spreadsheet = sheets_service.spreadsheets().create(
        body={
            'properties': {'title': SPREADSHEET_NAME},
            'sheets': [{'properties': {'title': SHEET_NAME}}]
        }
    ).execute()
    spreadsheet_id = spreadsheet['spreadsheetId']

    sheets_service.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id,
        range=f"{SHEET_NAME}!A1",
        valueInputOption='USER_ENTERED',
        body={'values': [HEADERS]}
    ).execute()

    return spreadsheet_id


def save_live_record(info: dict, doc_url: str, user_id: str):
    """ライブ情報をGoogle Sheetsに1行追記する"""
    drive_service, sheets_service = _get_services()
    spreadsheet_id = _get_or_create_spreadsheet(drive_service, sheets_service)

    row = [
        user_id,
        info['live_name'],
        info['date'],
        info['venue'],
        doc_url,
        datetime.now().strftime('%Y/%m/%d %H:%M'),
    ]

    sheets_service.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id,
        range=f"{SHEET_NAME}!A1",
        valueInputOption='USER_ENTERED',
        body={'values': [row]}
    ).execute()

    print(f"[Sheets] 記録保存完了: {info['live_name']}")


def get_lives_by_year(year: int, user_id: str) -> list:
    """指定した年・ユーザーのライブ一覧を返す"""
    drive_service, sheets_service = _get_services()
    spreadsheet_id = _get_or_create_spreadsheet(drive_service, sheets_service)

    result = sheets_service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=f"{SHEET_NAME}!A2:F"
    ).execute()

    rows = result.get('values', [])
    lives = []

    for row in rows:
        if len(row) < 5:
            continue
        if row[0] != user_id:
            continue
        if str(year) in row[2]:  # 参加日に年が含まれるか
            lives.append({
                'live_name': row[1],
                'date':      row[2],
                'venue':     row[3],
                'doc_url':   row[4],
            })

    return lives
