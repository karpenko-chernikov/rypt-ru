"""Environment-driven configuration for the Telegram reader service."""

import os


def _int(name, default):
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


class Config:
    def __init__(self):
        # Telegram Bot API credentials (BotFather). The bot must be an
        # administrator of the channel to receive channel_post updates.
        self.bot_token = os.environ.get("TG_BOT_TOKEN", "")
        self.api_base = os.environ.get("TG_API_BASE", "https://api.telegram.org").rstrip("/")
        self.channel = os.environ.get("TG_CHANNEL", "")

        # Auth token the website must send in the Authorization header.
        self.token = os.environ.get("TG_READER_TOKEN", "")

        # Storage.
        self.db_path = os.environ.get("TG_DB_PATH", "./data/reader.db")
        self.media_dir = os.environ.get("TG_MEDIA_DIR", "./data/media")

        # Where Telegram Desktop chat-export folders (ChatExport_...) live.
        self.export_dir = os.environ.get("TG_EXPORT_DIR", "./exports")

        # Tuning.
        self.poll_timeout = _int("TG_POLL_TIMEOUT", 25)
        self.sync_interval = _int("TG_SYNC_INTERVAL", 60)


config = Config()
