# -*- coding: utf-8 -*-
# ============================================================
# album.py — Google Docs/Drive APIを使ってアルバムを作成するモジュール
#
# main.py にある既存の関数をそのまま流用し、
# LINEから呼び出しやすい「run_album_pipeline」関数を追加しています。
# ============================================================

from googleapiclient.discovery import build

# main.py から既存の関数をすべてインポート（コードの再利用）
from main import (
    authenticate,
    upload_image_to_drive,
    create_google_doc,
    add_info_text,
    add_images_to_doc,
)


def run_album_pipeline(info: dict, image_paths: list, user_id: str = None) -> str:
    """
    アルバム作成の全工程を実行してGoogle DocsのURLを返す関数。

    LINEから写真とライブ情報を受け取ったあと、この関数を呼び出すだけで
    Google DriveとGoogle Docsへの一連の処理がすべて完了します。

    Args:
        info (dict): ライブ情報
            - live_name (str): ライブ名
            - date      (str): 参加日
            - venue     (str): 会場
        image_paths (list): ローカルに保存した写真ファイルのパスリスト

    Returns:
        str: 作成したGoogleドキュメントのURL
    """
    print(f"[アルバム作成開始] ライブ名: {info['live_name']} / 写真: {len(image_paths)}枚")

    # Step 1: Google APIの認証（token.pickleがあれば自動スキップ）
    print("  Google APIを認証中...")
    creds = authenticate()

    # Google DocsとDriveのAPIクライアントを作成
    docs_service  = build('docs',  'v1', credentials=creds)
    drive_service = build('drive', 'v3', credentials=creds)

    # Step 2: Googleドキュメントを新規作成
    print("  Googleドキュメントを作成中...")
    document_id = create_google_doc(docs_service)

    # Step 3: ライブ情報（タイトル・名前・日付・会場）をドキュメントに書き込む
    add_info_text(docs_service, document_id, info)

    # Step 4: 写真をGoogle Driveにアップロードして埋め込みURLを取得
    print(f"  写真を Google Drive にアップロード中（{len(image_paths)}枚）...")
    image_urls = []
    for i, path in enumerate(image_paths, 1):
        print(f"    ({i}/{len(image_paths)}) {path}")
        url = upload_image_to_drive(drive_service, path)
        image_urls.append(url)

    # Step 5: アップロードした写真をドキュメントに挿入
    print("  写真をドキュメントに挿入中...")
    add_images_to_doc(docs_service, document_id, image_urls)

    doc_url = f"https://docs.google.com/document/d/{document_id}/edit"
    print(f"[アルバム作成完了] URL: {doc_url}")

    # Google Sheetsに記録を保存
    if user_id:
        try:
            from sheets import save_live_record
            save_live_record(info, doc_url, user_id)
        except Exception as e:
            print(f"[警告] Sheets保存に失敗しました: {e}")

    return doc_url
