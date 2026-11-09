"""Minimal async Bot API client (long polling + file download).

Replaces the previous Telethon/MTProto client. Bots are not allowed to call
``GetHistoryRequest``, so channel history cannot be read with a bot token.
Instead, a bot that is an administrator of a channel receives ``channel_post``
updates through the Bot API ``getUpdates`` long-poll method.
"""

import os
import urllib.parse

import httpx

from . import config

_MAX_DOWNLOAD = 50 * 1024 * 1024  # 50 MiB
_ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp", ".mp4", ".mov", ".webm"}


class TelegramBot:
    def __init__(self):
        cfg = config.config
        if not cfg.bot_token:
            raise RuntimeError("TG_BOT_TOKEN is required")
        parsed = urllib.parse.urlparse(cfg.api_base)
        if parsed.scheme != "https" or not parsed.hostname:
            raise RuntimeError("TG_API_BASE must be an https URL")
        self.token = cfg.bot_token
        self.api_base = cfg.api_base
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(60.0, connect=10.0),
            follow_redirects=False,
        )

    async def close(self):
        await self._client.aclose()

    async def _request(self, method, path, **kwargs):
        """Send a request; raise an error that never contains the bot token."""
        try:
            resp = await self._client.request(
                method, f"{self.api_base}{path}", **kwargs
            )
            resp.raise_for_status()
            return resp
        except httpx.HTTPError as exc:
            raise RuntimeError(
                f"Bot API {method} failed: {type(exc).__name__}"
            ) from None

    async def get_updates(self, offset=0, timeout=25):
        """One long-poll. Returns the raw Bot API ``getUpdates`` response."""
        resp = await self._request(
            "POST",
            f"/bot{self.token}/getUpdates",
            json={
                "offset": offset,
                "timeout": timeout,
                "allowed_updates": ["channel_post"],
            },
            timeout=timeout + 15,
        )
        data = resp.json()
        if not data.get("ok"):
            raise RuntimeError(f"getUpdates failed: {data}")
        return data

    async def get_file_info(self, file_id):
        resp = await self._request(
            "POST",
            f"/bot{self.token}/getFile",
            json={"file_id": file_id},
        )
        data = resp.json()
        if not data.get("ok"):
            raise RuntimeError(f"getFile failed: {data}")
        return data["result"]

    async def download_file(self, file_id, directory, base_name):
        """Download a file by file_id into ``directory`` as ``base_name<ext>``."""
        info = await self.get_file_info(file_id)
        file_path = info.get("file_path")
        if not file_path:
            return None
        ext = os.path.splitext(file_path)[1].lower()
        if ext not in _ALLOWED_EXT:
            return None
        os.makedirs(directory, exist_ok=True)
        dest = os.path.join(directory, f"{base_name}{ext}")
        resp = await self._request("GET", f"/file/bot{self.token}/{file_path}")
        length = int(resp.headers.get("content-length") or 0)
        if length > _MAX_DOWNLOAD:
            raise RuntimeError("file too large")
        chunks = []
        total = 0
        async for chunk in resp.aiter_bytes(chunk_size=1024 * 1024):
            total += len(chunk)
            if total > _MAX_DOWNLOAD:
                raise RuntimeError("file too large")
            chunks.append(chunk)
        with open(dest, "wb") as fh:
            for chunk in chunks:
                fh.write(chunk)
        return dest
