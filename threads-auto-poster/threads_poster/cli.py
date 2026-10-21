"""コマンドライン操作。`python -m threads_poster <コマンド>` で実行する。"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from .parser import parse_inbox
from .scheduler import due_slot, slot_key
from .store import FAILED, POSTED, QUEUED, PostStore
from .threads_api import ThreadsAPIError, ThreadsClient

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config.json"
INBOX_PATH = ROOT / "posts" / "inbox.txt"
DATA_PATH = ROOT / "data" / "posts.json"
ENV_PATH = ROOT / ".env"


def load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def load_env() -> None:
    """.env の KEY=VALUE を環境変数に読み込む（既に設定済みの値は上書きしない）。"""
    if not ENV_PATH.exists():
        return
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def token_env_name(account: str) -> str:
    return f"THREADS_TOKEN_{account.upper()}"


def client_for(account: str) -> ThreadsClient:
    token = os.environ.get(token_env_name(account))
    if not token:
        raise ThreadsAPIError(f"{token_env_name(account)} が設定されていません（.env を確認してください）")
    return ThreadsClient(token)


def resolve_account(name: str | None, accounts: list[str]) -> str | None:
    if name is None:
        return accounts[0]
    for a in accounts:
        if a.lower() == name.lower():
            return a
    return None


def now_in(config: dict) -> datetime:
    return datetime.now(ZoneInfo(config["timezone"]))


def cmd_import(args, config) -> int:
    if not INBOX_PATH.exists():
        print(f"{INBOX_PATH} がありません")
        return 1
    raw = INBOX_PATH.read_text(encoding="utf-8")
    drafts, errors = parse_inbox(raw)

    store = PostStore(DATA_PATH)
    now = now_in(config)
    leftovers = [e.raw for e in errors]
    added = 0
    for d in drafts:
        account = resolve_account(d.account, config["accounts"])
        if account is None:
            print(f"× 不明なアカウント「{d.account}」: {d.text[:30]}…")
            leftovers.append(_to_block(d.text, d.genre, d.account))
            continue
        store.add(d.text, d.genre, account, now)
        added += 1
    store.save()

    for e in errors:
        print(f"× {e.index}件目: {e.message}")
    # 取り込めなかったものだけ inbox に残す
    INBOX_PATH.write_text("\n---\n".join(leftovers) + ("\n" if leftovers else ""), encoding="utf-8")
    print(f"{added}件を予約キューに追加しました" + (f"（{len(leftovers)}件は inbox に残しています）" if leftovers else ""))
    return 1 if leftovers else 0


def _to_block(text: str, genre: str | None, account: str | None) -> str:
    head = []
    if genre:
        head.append(f"ジャンル: {genre}")
    if account:
        head.append(f"アカウント: {account}")
    return "\n".join(head + [text])


def cmd_list(args, config) -> int:
    store = PostStore(DATA_PATH)
    labels = {QUEUED: "予約中", POSTED: "投稿済", FAILED: "失敗"}
    shown = [p for p in store.posts if args.all or p["status"] != POSTED]
    if not shown:
        print("表示する投稿はありません")
    for p in shown:
        first_line = p["text"].splitlines()[0][:30]
        when = f" {p['posted_at']}" if p["posted_at"] else ""
        print(f"[{p['id']}] {labels[p['status']]} {p['account']} 〈{p['genre'] or 'ジャンルなし'}〉{when} {first_line}")
        if p["error"] and p["status"] == FAILED:
            print(f"    エラー: {p['error']}")
    for account in config["accounts"]:
        print(f"{account}: 予約 {len(store.queued(account))}件")
    return 0


def cmd_post(args, config) -> int:
    store = PostStore(DATA_PATH)
    now = now_in(config)
    today = now.date().isoformat()
    accounts = config["accounts"]
    if args.account:
        account = resolve_account(args.account, accounts)
        if account is None:
            print(f"不明なアカウント: {args.account}")
            return 1
        accounts = [account]

    key = None
    if not args.now:
        slot = due_slot(now, config["slots"], config["slot_window_minutes"])
        if slot is None:
            print(f"{now:%H:%M} は投稿枠（{', '.join(config['slots'])}）の時間外です。今すぐ投稿するには --now を付けてください")
            return 0
        key = slot_key(now, slot)

    failed = False
    for account in accounts:
        if key and store.slot_used(account, key):
            print(f"{account}: {key} の枠は投稿済みです")
            continue
        if len(store.posted_on(account, today)) >= config["max_per_day"]:
            print(f"{account}: 今日は上限（{config['max_per_day']}件）に達しています")
            continue
        queue = store.queued(account)
        if not queue:
            print(f"{account}: 予約中の投稿がありません")
            continue

        post = queue[0]
        preview = post["text"].replace("\n", " ")[:40]
        if args.dry_run:
            print(f"{account}: [お試し] 次に投稿するもの → [{post['id']}] {preview}")
            continue

        try:
            client = client_for(account)
            media_id = client.publish_text(post["text"])
        except ThreadsAPIError as e:
            post.update(status=FAILED, error=str(e))
            store.save()
            print(f"{account}: × 投稿失敗 [{post['id']}] {e}")
            failed = True
            continue

        post.update(
            status=POSTED,
            posted_at=now_in(config).isoformat(timespec="seconds"),
            threads_id=media_id,
            slot=key,
            error=None,
        )
        try:
            post["permalink"] = client.permalink(media_id)
        except ThreadsAPIError:
            pass  # URL が取れなくても投稿自体は成功している
        store.save()
        print(f"{account}: ✓ 投稿しました [{post['id']}] {post['permalink'] or media_id}")

    return 1 if failed else 0


def cmd_retry(args, config) -> int:
    store = PostStore(DATA_PATH)
    count = 0
    for p in store.posts:
        if p["status"] == FAILED and (args.id is None or p["id"] == args.id):
            p.update(status=QUEUED, error=None)
            count += 1
    store.save()
    print(f"{count}件を予約キューに戻しました")
    return 0


def cmd_check(args, config) -> int:
    ok = True
    for account in config["accounts"]:
        try:
            me = client_for(account).me()
            print(f"{account}: ✓ @{me.get('username')}（ID {me['id']}）")
        except ThreadsAPIError as e:
            print(f"{account}: × {e}")
            ok = False
    return 0 if ok else 1


def cmd_refresh_token(args, config) -> int:
    ok = True
    for account in config["accounts"]:
        try:
            result = client_for(account).refresh_token()
        except ThreadsAPIError as e:
            print(f"{account}: × 更新失敗 {e}")
            ok = False
            continue
        _write_env(token_env_name(account), result["access_token"])
        days = int(result.get("expires_in", 0)) // 86400
        print(f"{account}: ✓ トークンを更新しました（あと約{days}日有効）")
    return 0 if ok else 1


def _write_env(key: str, value: str) -> None:
    lines = ENV_PATH.read_text(encoding="utf-8").splitlines() if ENV_PATH.exists() else []
    for i, line in enumerate(lines):
        if line.split("=", 1)[0].strip() == key:
            lines[i] = f"{key}={value}"
            break
    else:
        lines.append(f"{key}={value}")
    ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    os.environ[key] = value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="threads_poster", description="Threads 自動投稿ツール")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("import", help="posts/inbox.txt の投稿を予約キューに取り込む").set_defaults(func=cmd_import)

    p = sub.add_parser("list", help="予約中・失敗した投稿を表示する")
    p.add_argument("--all", action="store_true", help="投稿済みも表示する")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("post", help="投稿枠の時間なら次の予約投稿を公開する")
    p.add_argument("--now", action="store_true", help="投稿枠に関係なく今すぐ投稿する")
    p.add_argument("--dry-run", action="store_true", help="実際には投稿せず、次に投稿するものを表示する")
    p.add_argument("--account", help="対象アカウント（省略時は全アカウント）")
    p.set_defaults(func=cmd_post)

    p = sub.add_parser("retry", help="失敗した投稿を予約キューに戻す")
    p.add_argument("id", nargs="?", help="投稿ID（省略時は失敗した投稿すべて）")
    p.set_defaults(func=cmd_retry)

    sub.add_parser("check", help="各アカウントのトークンが使えるか確認する").set_defaults(func=cmd_check)
    sub.add_parser("refresh-token", help="アクセストークンを更新して .env に保存する").set_defaults(func=cmd_refresh_token)

    args = parser.parse_args(argv)
    load_env()
    return args.func(args, load_config())


if __name__ == "__main__":
    sys.exit(main())
