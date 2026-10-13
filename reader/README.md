# Telegram reader service

Lightweight, standalone service that mirrors a **public Telegram channel** and
serves the result over a small authenticated HTTP API. It runs on a server
outside Russia where Telegram is reachable; the Django website only talks HTTPS
to this service.

- Reads via the **Telegram Bot API** (long polling `getUpdates`). The bot must
  be an **administrator of the channel**; that is how it receives
  `channel_post` updates. Bots cannot read message history, so only **new
  posts** are mirrored (no backfill of pre-existing posts).
- Converts text + entities to a tiny HTML dialect: `<p> <b> <i> <a href> <br/>`.
  Emoji pass through. Polls/stickers/documents/voice are skipped.
- Downloads photos and videos/animation to disk.
- Serves `GET /api/posts` and `GET /media/<file>`, both behind a bearer token.

## Prerequisites

1. Create a bot with [@BotFather](https://t.me/BotFather) to get
   `TG_BOT_TOKEN`.
2. Add the bot as an **administrator** of the target channel (otherwise
   Telegram never delivers `channel_post` updates and nothing will sync).
3. Make sure no webhook is set on the bot — long polling conflicts with a
   configured webhook. Clear it with:
   `https://api.telegram.org/bot<TOKEN>/deleteWebhook`.
4. Know the channel username, e.g. `@mychannel`.

## Run with Docker

```bash
cp .env.example .env          # fill in the values
docker compose -f deploy/docker-compose.yml up -d --build
```

Or run directly with uvicorn:

```bash
pip install -r requirements.txt
export $(grep -v '^#' .env | xargs)
uvicorn reader.main:app --host 0.0.0.0 --port 8000
```

In production put nginx (with a valid TLS certificate) in front of port 8000.

## API

All requests must send the token:

```
Authorization: Bearer <TG_READER_TOKEN>
```

- `GET /api/posts?after=<message_id>&limit=<n>` — posts with id greater than
  `after`, ascending. `limit` defaults to 100, max 500. Response:
  `{"channel": ..., "posts": [...], "next": <last id or after>}`.
- `POST /api/import?folder=<name>` — import a Telegram Desktop chat-export
  folder (`ChatExport_...`) into the same post list. The folder is looked up
  inside `TG_EXPORT_DIR` (default `./exports`), falling back to a path relative
  to the working directory; an absolute path also works. Media files are copied
  into `TG_MEDIA_DIR`. Response: `{"imported": <n>, "folder": ..., "channel": ...}`.
- `GET /media/<file>` — a downloaded photo/video. `url` in each attachment is
  relative to this endpoint.
- `GET /healthz` — liveness check (no auth).

Attachment shape:

```json
{"kind": "photo", "url": "photo_2026-09-25_18-00-00.jpg",
 "original_url": "https://t.me/mychannel/123", "width": 1280, "height": 720}
{"kind": "video", "url": "video_2026-09-25_18-00-00.mp4",
 "original_url": "https://t.me/mychannel/124", "duration": 12}
```

## How syncing works

A background task inside the FastAPI process repeatedly calls
`getUpdates` (long polling, `TG_POLL_TIMEOUT` seconds per call) and persists
each `channel_post`. The update cursor (`update_offset`) is kept in SQLite
(`TG_DB_PATH`), so restarts resume where they left off and are idempotent. On a
failed cycle the task waits `TG_SYNC_INTERVAL` seconds before retrying; the API
stays available even if a sync cycle errors.

## Known limitations

- **No backfill.** Bot API cannot read channel history, so posts created before
  the bot became an admin (or while the service was down) are never fetched.
  Mirroring old posts requires a user account (MTProto), which bots are not
  allowed to use (`GetHistoryRequest` is bot-restricted).
- The bot must be a channel admin; otherwise no updates arrive.
- Media albums are grouped by `media_group_id` within a single `getUpdates`
  batch; an album that straddles a batch boundary could be split. In practice
  albums are delivered in one batch.
- Underline, strikethrough, code/pre and spoiler formatting is dropped (kept as
  plain text) because the website's rich text features don't include them.
