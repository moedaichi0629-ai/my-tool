#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ライブ思い出アルバム自動生成ツール
=====================================
ライブ参加時に撮影した写真と基本情報を入力すると、
Googleドキュメント上にライブ思い出アルバムを自動生成・保存するツールです。

【処理の流れ】
1. ユーザーがライブ情報を入力
2. 写真フォルダから画像ファイルを取得
3. Googleアカウントの認証
4. Googleドキュメントを新規作成
5. 画像をGoogle Driveにアップロード
6. 画像をドキュメントに挿入
7. 完成したドキュメントのURLを表示
"""

import os
import pickle

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


# ========================================
# 定数の設定
# ========================================

# Google APIのアクセス権限（スコープ）
# GoogleドキュメントとドライブのAPIを使用するために両方必要
SCOPES = [
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/spreadsheets',
]

# 処理対象の画像拡張子（小文字で定義）
IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png')

# 認証情報ファイルのパス（Google Cloud Consoleからダウンロードするファイル）
CREDENTIALS_FILE = 'credentials.json'

# 認証トークンの保存先（2回目以降の認証を省略するために使用）
TOKEN_FILE = 'token.pickle'

# 写真フォルダのパス（main.pyと同じフォルダにあるimagesフォルダを自動で使う）
# __file__ は「このスクリプト自身のパス」を意味する
# os.path.dirname でそのフォルダ名を取り出し、imagesフォルダのパスを作る
IMAGES_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'images')

# ドキュメントに挿入する画像のサイズ（単位: ポイント）
IMAGE_WIDTH_PT  = 350
IMAGE_HEIGHT_PT = 250


# ========================================
# 1. 情報入力機能
# ========================================

def get_user_input():
    """
    ターミナルからユーザーにライブ情報を入力してもらう関数。

    Returns:
        dict: ライブ名・参加日・会場・写真フォルダのパスを含む辞書
    """
    print("=" * 50)
    print("  ライブ思い出アルバム自動生成ツール")
    print("=" * 50)
    print()

    live_name = input("ライブ名を入力してください: ").strip()
    date      = input("参加日を入力してください（例: 2024年6月1日）: ").strip()
    venue     = input("会場を入力してください: ").strip()

    # 写真フォルダは自動でimagesフォルダを使う（手入力不要）
    folder_path = IMAGES_FOLDER

    # 入力内容の確認表示
    print()
    print("【入力内容の確認】")
    print(f"  ライブ名　　：{live_name}")
    print(f"  参加日　　　：{date}")
    print(f"  会場　　　　：{venue}")
    print(f"  写真フォルダ：{folder_path}")
    print()

    return {
        'live_name':   live_name,
        'date':        date,
        'venue':       venue,
        'folder_path': folder_path
    }


# ========================================
# 2. 写真取得機能
# ========================================

def get_images_from_folder(folder_path):
    """
    指定したフォルダから画像ファイルの一覧を取得する関数。

    対象拡張子: .jpg / .jpeg / .png（大文字・小文字を区別しない）

    Args:
        folder_path (str): 画像が入ったフォルダのパス

    Returns:
        list[str]: 画像ファイルのフルパスのリスト（ファイル名順でソート済み）

    Raises:
        FileNotFoundError: フォルダが存在しない場合
        NotADirectoryError: パスがフォルダではない場合
        ValueError: フォルダ内に対象の画像ファイルがない場合
    """
    # フォルダの存在確認
    if not os.path.exists(folder_path):
        raise FileNotFoundError(f"フォルダが見つかりません: {folder_path}")

    if not os.path.isdir(folder_path):
        raise NotADirectoryError(f"指定したパスはフォルダではありません: {folder_path}")

    # ファイル名順にソートしながら画像ファイルを収集
    images = []
    for filename in sorted(os.listdir(folder_path)):
        # 拡張子を小文字に変換して判定（大文字の .JPG にも対応）
        if filename.lower().endswith(IMAGE_EXTENSIONS):
            full_path = os.path.join(folder_path, filename)
            images.append(full_path)

    # 対象の画像が見つからない場合はエラーを発生させる
    if not images:
        raise ValueError(
            f"指定したフォルダに画像ファイル（jpg / jpeg / png）が見つかりませんでした。\n"
            f"フォルダ: {folder_path}"
        )

    # 見つかった画像の一覧を表示
    print(f"  → {len(images)} 枚の写真を検出しました")
    for img in images:
        print(f"    ・{os.path.basename(img)}")

    return images


# ========================================
# Google API 認証
# ========================================

def authenticate():
    """
    Google APIの認証を行う関数。

    初回実行時はブラウザが開き、Googleアカウントへのログインが求められます。
    認証後はトークンを token.pickle に保存するため、2回目以降は自動認証されます。

    Returns:
        google.oauth2.credentials.Credentials: 認証済みのCredentialsオブジェクト

    Raises:
        FileNotFoundError: credentials.json が見つからない場合
    """
    creds = None

    # 保存済みのトークンがあれば読み込む（2回目以降の認証を省略）
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)

    # 認証情報が存在しないか無効な場合は再認証する
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # アクセストークンの有効期限が切れた場合はリフレッシュ
            creds.refresh(Request())
        else:
            # 初回認証: credentials.json の存在を確認してからブラウザを開く
            if not os.path.exists(CREDENTIALS_FILE):
                raise FileNotFoundError(
                    f"認証ファイルが見つかりません: {CREDENTIALS_FILE}\n"
                    "Google Cloud Console から OAuth 2.0 クライアント ID を\n"
                    "ダウンロードし、このフォルダに credentials.json として保存してください。"
                )
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        # 次回以降の認証を省略するため、トークンをファイルに保存
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)

    print("  → Google認証が完了しました")
    return creds


# ========================================
# 4. Google Drive 保存機能
# ========================================

def upload_image_to_drive(drive_service, image_path):
    """
    画像ファイルをGoogle Driveにアップロードし、ドキュメントで使用できるURLを返す関数。

    アップロードした画像は「リンクを知っている全員が閲覧可能」に設定されます。
    これはGoogleドキュメントAPIが画像を読み込むために必要な設定です。

    Args:
        drive_service: Google Drive APIのクライアント
        image_path (str): アップロードする画像ファイルのパス

    Returns:
        str: Googleドキュメントに挿入できる画像のURL
    """
    filename = os.path.basename(image_path)

    # ファイルの種類に応じたMIMEタイプを設定
    ext = os.path.splitext(filename)[1].lower()
    mime_type_map = {
        '.jpg':  'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png':  'image/png'
    }
    mime_type = mime_type_map.get(ext, 'image/jpeg')

    # Google Drive へファイルをアップロード
    file_metadata = {'name': filename}
    media = MediaFileUpload(image_path, mimetype=mime_type)

    uploaded_file = drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()

    file_id = uploaded_file.get('id')

    # 「リンクを知っている全員が閲覧可能」に権限を設定
    # ※ Google Docs API が画像を取得するために公開アクセスが必要
    drive_service.permissions().create(
        fileId=file_id,
        body={
            'type': 'anyone',   # 誰でもアクセス可能
            'role': 'reader'    # 閲覧のみ（編集不可）
        }
    ).execute()

    # Googleドキュメントに埋め込む際に使用するURLを生成
    image_url = f"https://drive.google.com/uc?id={file_id}"
    return image_url


# ========================================
# 3. Googleドキュメント生成機能
# ========================================

def create_google_doc(docs_service):
    """
    新しいGoogleドキュメントを作成する関数。

    Args:
        docs_service: Google Docs APIのクライアント

    Returns:
        str: 作成されたドキュメントのID
    """
    document = docs_service.documents().create(
        body={'title': 'ライブ思い出アルバム'}
    ).execute()

    document_id = document.get('documentId')
    print(f"  → ドキュメントを作成しました（ID: {document_id[:8]}...）")
    return document_id


def add_info_text(docs_service, document_id, info):
    """
    Googleドキュメントにライブ情報のテキストを追加する関数。

    挿入するテキスト:
    - タイトル「ライブ思い出アルバム」
    - ライブ名・参加日・会場
    - 「写真一覧」の見出し

    Args:
        docs_service: Google Docs APIのクライアント
        document_id (str): テキストを追加するドキュメントのID
        info (dict): ライブ情報（live_name, date, venue）
    """
    # endOfSegmentLocation を使うと「ドキュメントの末尾」に追加できる
    # 各リクエストは順番に処理されるため、この順番でテキストが並ぶ
    requests = [
        # メインタイトル
        {
            'insertText': {
                'endOfSegmentLocation': {'segmentId': ''},
                'text': 'ライブ思い出アルバム\n'
            }
        },
        # 空行（タイトルと情報の間のスペース）
        {
            'insertText': {
                'endOfSegmentLocation': {'segmentId': ''},
                'text': '\n'
            }
        },
        # ライブ情報（名前・日付・会場）
        {
            'insertText': {
                'endOfSegmentLocation': {'segmentId': ''},
                'text': f"ライブ名　：{info['live_name']}\n"
            }
        },
        {
            'insertText': {
                'endOfSegmentLocation': {'segmentId': ''},
                'text': f"参加日　　：{info['date']}\n"
            }
        },
        {
            'insertText': {
                'endOfSegmentLocation': {'segmentId': ''},
                'text': f"会場　　　：{info['venue']}\n"
            }
        },
        # 空行
        {
            'insertText': {
                'endOfSegmentLocation': {'segmentId': ''},
                'text': '\n'
            }
        },
        # 写真一覧の見出し
        {
            'insertText': {
                'endOfSegmentLocation': {'segmentId': ''},
                'text': '写真一覧\n'
            }
        },
        # 空行（見出しと写真の間のスペース）
        {
            'insertText': {
                'endOfSegmentLocation': {'segmentId': ''},
                'text': '\n'
            }
        },
    ]

    # テキストをドキュメントに一括書き込み
    docs_service.documents().batchUpdate(
        documentId=document_id,
        body={'requests': requests}
    ).execute()

    # タイトルと「写真一覧」に見出しスタイルを適用
    apply_heading_styles(docs_service, document_id)

    print("  → ライブ情報を書き込みました")


def apply_heading_styles(docs_service, document_id):
    """
    「ライブ思い出アルバム」と「写真一覧」にHEADINGスタイルを適用する関数。

    ドキュメントの現在の内容を取得してから、
    該当する段落を特定してスタイルを適用します。

    Args:
        docs_service: Google Docs APIのクライアント
        document_id (str): スタイルを適用するドキュメントのID
    """
    # 現在のドキュメント内容を取得して段落の位置を調べる
    doc = docs_service.documents().get(documentId=document_id).execute()
    body_content = doc.get('body', {}).get('content', [])

    style_requests = []

    for element in body_content:
        # 段落要素以外はスキップ
        if 'paragraph' not in element:
            continue

        # 段落内のテキストを結合して取得
        paragraph = element.get('paragraph', {})
        text = ''
        for text_run in paragraph.get('elements', []):
            text += text_run.get('textRun', {}).get('content', '')

        start = element.get('startIndex', 1)
        end   = element.get('endIndex', 1)

        # 「ライブ思い出アルバム」にHEADING_1（最大見出し）を適用
        if 'ライブ思い出アルバム' in text:
            style_requests.append({
                'updateParagraphStyle': {
                    'range': {'startIndex': start, 'endIndex': end},
                    'paragraphStyle': {'namedStyleType': 'HEADING_1'},
                    'fields': 'namedStyleType'
                }
            })

        # 「写真一覧」にHEADING_2（中見出し）を適用
        elif '写真一覧' in text:
            style_requests.append({
                'updateParagraphStyle': {
                    'range': {'startIndex': start, 'endIndex': end},
                    'paragraphStyle': {'namedStyleType': 'HEADING_2'},
                    'fields': 'namedStyleType'
                }
            })

    # スタイルを適用（適用対象がある場合のみAPIを呼び出す）
    if style_requests:
        docs_service.documents().batchUpdate(
            documentId=document_id,
            body={'requests': style_requests}
        ).execute()


def add_images_to_doc(docs_service, document_id, image_urls):
    """
    GoogleドキュメントにDriveの画像を順番に挿入する関数。

    各画像は縦 IMAGE_HEIGHT_PT × 横 IMAGE_WIDTH_PT のサイズで挿入されます。
    挿入に失敗した画像はスキップして処理を続けます。

    Args:
        docs_service: Google Docs APIのクライアント
        document_id (str): 画像を挿入するドキュメントのID
        image_urls (list[str]): 挿入する画像のURLリスト
    """
    total = len(image_urls)

    for i, url in enumerate(image_urls, 1):
        print(f"  写真 {i}/{total} をドキュメントに挿入中...")

        try:
            # 1枚の画像挿入と改行を1つのリクエストにまとめて送信
            requests = [
                # 画像の挿入（ドキュメント末尾に追加）
                {
                    'insertInlineImage': {
                        'endOfSegmentLocation': {'segmentId': ''},
                        'uri': url,
                        'objectSize': {
                            'height': {'magnitude': IMAGE_HEIGHT_PT, 'unit': 'PT'},
                            'width':  {'magnitude': IMAGE_WIDTH_PT,  'unit': 'PT'}
                        }
                    }
                },
                # 画像の後に改行を追加（次の画像との間にスペースを作る）
                {
                    'insertText': {
                        'endOfSegmentLocation': {'segmentId': ''},
                        'text': '\n'
                    }
                }
            ]

            docs_service.documents().batchUpdate(
                documentId=document_id,
                body={'requests': requests}
            ).execute()

        except Exception as e:
            # 画像挿入に失敗した場合はスキップして次の画像へ
            print(f"    ※ 写真 {i} の挿入をスキップしました: {e}")

    print("  → 写真の挿入が完了しました")


# ========================================
# 5. 完了通知機能 + メイン処理
# ========================================

def main():
    """
    ツール全体の処理を管理するメイン関数。

    各ステップの処理を順番に呼び出し、
    完了後にGoogleドキュメントのURLを表示します。
    """
    try:
        # ---- Step 1: ユーザーからライブ情報を入力 ----
        info = get_user_input()

        print("処理を開始します...\n")

        # ---- Step 2: 写真フォルダから画像ファイルを取得 ----
        print("[1/5] 写真フォルダを確認中...")
        image_paths = get_images_from_folder(info['folder_path'])

        # ---- Step 3: Google API の認証 ----
        print("\n[2/5] Googleアカウントを認証中...")
        print("  ブラウザが開いたらGoogleアカウントにログインしてください。")
        creds = authenticate()

        # Google ドキュメントとドライブのAPIクライアントを作成
        docs_service  = build('docs',  'v1', credentials=creds)
        drive_service = build('drive', 'v3', credentials=creds)

        # ---- Step 4: Googleドキュメントを新規作成 ----
        print("\n[3/5] Googleドキュメントを作成中...")
        document_id = create_google_doc(docs_service)

        # ---- Step 5: ライブ情報テキストを書き込む ----
        add_info_text(docs_service, document_id, info)

        # ---- Step 6: 画像をGoogle Driveにアップロード ----
        print(f"\n[4/5] 写真をGoogle Driveにアップロード中（{len(image_paths)}枚）...")
        image_urls = []
        for i, path in enumerate(image_paths, 1):
            filename = os.path.basename(path)
            print(f"  写真 {i}/{len(image_paths)}: {filename}")
            url = upload_image_to_drive(drive_service, path)
            image_urls.append(url)

        # ---- Step 7: 画像をドキュメントに挿入 ----
        print(f"\n[5/5] 写真をドキュメントに挿入中...")
        add_images_to_doc(docs_service, document_id, image_urls)

        # ---- 完了通知: ドキュメントのURLを表示 ----
        doc_url = f"https://docs.google.com/document/d/{document_id}/edit"

        print()
        print("=" * 50)
        print("  完了しました！")
        print("=" * 50)
        print()
        print("作成されたGoogleドキュメントのURL:")
        print(f"  {doc_url}")
        print()
        print("ブラウザで上記のURLを開くとアルバムを確認できます。")
        print()

    except FileNotFoundError as e:
        print(f"\n[エラー] ファイルが見つかりません:\n  {e}")
    except NotADirectoryError as e:
        print(f"\n[エラー] フォルダではありません:\n  {e}")
    except ValueError as e:
        print(f"\n[エラー] 入力内容に問題があります:\n  {e}")
    except Exception as e:
        print(f"\n[エラー] 予期しないエラーが発生しました:\n  {e}")
        print("READMEの「エラーが出たときの確認ポイント」を参照してください。")


# このファイルが直接実行された場合にのみ main() を呼び出す
if __name__ == '__main__':
    main()
