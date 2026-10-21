"""投稿データ（予約キュー・投稿済み）を data/posts.json に保存する。"""

import json
import uuid
from datetime import datetime
from pathlib import Path

QUEUED = "queued"
POSTED = "posted"
FAILED = "failed"


class PostStore:
    def __init__(self, path: Path):
        self.path = path
        self.posts: list[dict] = []
        if path.exists():
            self.posts = json.loads(path.read_text(encoding="utf-8"))

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.posts, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        tmp.replace(self.path)

    def add(self, text: str, genre: str | None, account: str, now: datetime) -> dict:
        post = {
            "id": uuid.uuid4().hex[:8],
            "account": account,
            "genre": genre,
            "text": text,
            "status": QUEUED,
            "created_at": now.isoformat(timespec="seconds"),
            "slot": None,
            "posted_at": None,
            "threads_id": None,
            "permalink": None,
            "error": None,
        }
        self.posts.append(post)
        return post

    def queued(self, account: str) -> list[dict]:
        return [p for p in self.posts if p["account"] == account and p["status"] == QUEUED]

    def posted_on(self, account: str, date_str: str) -> list[dict]:
        """指定日（YYYY-MM-DD）にそのアカウントで投稿したもの。"""
        return [
            p for p in self.posts
            if p["account"] == account and p["status"] == POSTED and (p["posted_at"] or "").startswith(date_str)
        ]

    def slot_used(self, account: str, slot_key: str) -> bool:
        return any(p["account"] == account and p["slot"] == slot_key and p["status"] == POSTED for p in self.posts)
