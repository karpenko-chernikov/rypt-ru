"""Minimal async Bot API client (long polling + file download).

Replaces the previous Telethon/MTProto client. Bots are not allowed to call
``GetHistoryRequest``, so channel history cannot be read with a bot token.
Instead, a bot that is an administrator of a channel receives ``channel_post``
updates through the Bot API ``getUpdates`` long-poll method.
"""

import os

import httpx

from . import config


class TelegramBot:
    def __init__(self):
        cfg = config.config
        if not cfg.bot_token:
            raise RuntimeError("TG_BOT_TOKEN is required")
        self.token = cfg.bot_token
        self.api_base = cfg.api_base
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(60.0, connect=10.0)
        )

    async def close(self):
        await self._client.aclose()

    async def get_updates(self, offset=0, timeout=25):
        """One long-poll. Returns the raw Bot API ``getUpdates`` response."""
        resp = await self._client.post(
            f"{self.api_base}/bot{self.token}/getUpdates",
            json={
                "offset": offset,
                "timeout": timeout,
                "allowed_updates": ["channel_post"],
            },
            timeout=timeout + 15,
        )
        resp.raise_for_status()
        data = resp.json()
        if not data.get("ok"):
            raise RuntimeError(f"getUpdates failed: {data}")
        return data

    async def get_file_info(self, file_id):
        resp = await self._client.post(
            f"{self.api_base}/bot{self.token}/getFile",
            json={"file_id": file_id},
        )
        resp.raise_for_status()
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
        ext = os.path.splitext(file_path)[1] or ".bin"
        os.makedirs(directory, exist_ok=True)
        dest = os.path.join(directory, f"{base_name}{ext}")
        resp = await self._client.get(
            f"{self.api_base}/file/bot{self.token}/{file_path}"
        )
        resp.raise_for_status()
        with open(dest, "wb") as fh:
            fh.write(resp.content)
        return dest
