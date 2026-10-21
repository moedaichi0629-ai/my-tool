import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest import mock
from zoneinfo import ZoneInfo

from threads_poster import cli
from threads_poster.threads_api import ThreadsAPIError

CONFIG = {
    "timezone": "Asia/Tokyo",
    "accounts": ["main", "sub"],
    "slots": ["07:00", "21:00"],
    "max_per_day": 5,
    "slot_window_minutes": 60,
}


class FakeClient:
    published: list[str] = []
    fail = False

    def __init__(self, token):
        pass

    def publish_text(self, text):
        if FakeClient.fail:
            raise ThreadsAPIError("HTTP 400: テストエラー")
        FakeClient.published.append(text)
        return f"media{len(FakeClient.published)}"

    def permalink(self, media_id):
        return f"https://www.threads.net/@me/post/{media_id}"


class CliTest(unittest.TestCase):
    def setUp(self):
        tmp = Path(tempfile.mkdtemp())
        self.inbox = tmp / "inbox.txt"
        self.data = tmp / "posts.json"
        self.now = datetime(2026, 10, 21, 7, 10, tzinfo=ZoneInfo("Asia/Tokyo"))
        FakeClient.published = []
        FakeClient.fail = False
        patches = [
            mock.patch.object(cli, "INBOX_PATH", self.inbox),
            mock.patch.object(cli, "DATA_PATH", self.data),
            mock.patch.object(cli, "ENV_PATH", tmp / ".env"),
            mock.patch.object(cli, "load_config", lambda: CONFIG),
            mock.patch.object(cli, "now_in", lambda config: self.now),
            mock.patch.object(cli, "ThreadsClient", FakeClient),
            mock.patch.dict("os.environ", {"THREADS_TOKEN_MAIN": "x", "THREADS_TOKEN_SUB": "y"}),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

    def posts(self):
        return json.loads(self.data.read_text(encoding="utf-8"))

    def test_import_then_post_once_per_slot(self):
        self.inbox.write_text("ジャンル: 副業\n投稿1\n---\n投稿2\n---\nアカウント: sub\n投稿3\n---\nアカウント: 不明\n投稿4", encoding="utf-8")
        self.assertEqual(cli.main(["import"]), 1)  # 不明アカウントの1件が残る
        self.assertIn("投稿4", self.inbox.read_text(encoding="utf-8"))
        self.assertEqual(len(self.posts()), 3)

        self.assertEqual(cli.main(["post"]), 0)
        self.assertEqual(FakeClient.published, ["投稿1", "投稿3"])
        # 同じ枠では二重投稿しない
        cli.main(["post"])
        self.assertEqual(FakeClient.published, ["投稿1", "投稿3"])

        posted = [p for p in self.posts() if p["status"] == "posted"]
        self.assertEqual({p["slot"] for p in posted}, {"2026-10-21 07:00"})
        self.assertEqual(posted[0]["genre"], "副業")

    def test_outside_slot_needs_now(self):
        self.inbox.write_text("投稿1", encoding="utf-8")
        cli.main(["import"])
        self.now = self.now.replace(hour=10)
        cli.main(["post"])
        self.assertEqual(FakeClient.published, [])
        cli.main(["post", "--now"])
        self.assertEqual(FakeClient.published, ["投稿1"])

    def test_daily_limit(self):
        self.inbox.write_text("\n---\n".join(f"投稿{i}" for i in range(7)), encoding="utf-8")
        cli.main(["import"])
        for _ in range(7):
            cli.main(["post", "--now", "--account", "main"])
        self.assertEqual(len(FakeClient.published), CONFIG["max_per_day"])

    def test_failure_then_retry(self):
        self.inbox.write_text("投稿1", encoding="utf-8")
        cli.main(["import"])
        FakeClient.fail = True
        self.assertEqual(cli.main(["post", "--now"]), 1)
        self.assertEqual(self.posts()[0]["status"], "failed")
        FakeClient.fail = False
        cli.main(["retry"])
        cli.main(["post", "--now"])
        self.assertEqual(self.posts()[0]["status"], "posted")


if __name__ == "__main__":
    unittest.main()
