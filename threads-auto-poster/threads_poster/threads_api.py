"""Threads API（graph.threads.net）の最小クライアント。標準ライブラリのみ使用。"""

import json
import time
import urllib.error
import urllib.parse
import urllib.request

BASE_URL = "https://graph.threads.net"
API_VERSION = "v1.0"


class ThreadsAPIError(Exception):
    pass


class ThreadsClient:
    def __init__(self, access_token: str):
        self.access_token = access_token
        self._user_id: str | None = None

    def _request(self, method: str, path: str, params: dict | None = None) -> dict:
        params = dict(params or {})
        params["access_token"] = self.access_token
        query = urllib.parse.urlencode(params)
        url = f"{BASE_URL}/{path}"
        if method == "GET":
            req = urllib.request.Request(f"{url}?{query}", method="GET")
        else:
            req = urllib.request.Request(url, data=query.encode(), method="POST")
        try:
            with urllib.request.urlopen(req, timeout=30) as res:
                return json.loads(res.read().decode())
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")
            try:
                message = json.loads(body)["error"]["message"]
            except (ValueError, KeyError, TypeError):
                message = body
            raise ThreadsAPIError(f"HTTP {e.code}: {message}") from None
        except urllib.error.URLError as e:
            raise ThreadsAPIError(f"接続エラー: {e.reason}") from None

    def me(self) -> dict:
        return self._request("GET", f"{API_VERSION}/me", {"fields": "id,username"})

    @property
    def user_id(self) -> str:
        if self._user_id is None:
            self._user_id = self.me()["id"]
        return self._user_id

    def publish_text(self, text: str) -> str:
        """テキスト投稿を作成して公開し、投稿（メディア）IDを返す。"""
        container = self._request(
            "POST", f"{API_VERSION}/{self.user_id}/threads", {"media_type": "TEXT", "text": text}
        )
        creation_id = container["id"]

        # コンテナの準備ができていないと公開に失敗することがあるので、数回だけ待って再試行する
        last_error: ThreadsAPIError | None = None
        for wait in (2, 5, 10):
            time.sleep(wait)
            try:
                result = self._request(
                    "POST", f"{API_VERSION}/{self.user_id}/threads_publish", {"creation_id": creation_id}
                )
                return result["id"]
            except ThreadsAPIError as e:
                last_error = e
        raise last_error

    def permalink(self, media_id: str) -> str | None:
        return self._request("GET", f"{API_VERSION}/{media_id}", {"fields": "permalink"}).get("permalink")

    def refresh_token(self) -> dict:
        """長期トークンを更新する（有効期限が約60日延びる）。"""
        return self._request("GET", "refresh_access_token", {"grant_type": "th_refresh_token"})
