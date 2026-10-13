"""FastAPI app: background Telegram sync plus posts/media API.

The website (running in Russia) pulls posts via ``GET /api/posts`` and media via
``GET /media/<file>``. Every request must carry a bearer token in the
``Authorization`` header when ``TG_READER_TOKEN`` is set.
"""

import asyncio
import contextlib
import hmac
import json
import os

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.responses import FileResponse

from . import config
from .store import Store
from .sync import Syncer

cfg = config.config
store = Store(cfg.db_path)
syncer = Syncer()


def _authorize(authorization: str = Header(default="")):
    if not cfg.token:
        return
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    supplied = authorization[len("Bearer "):]
    if not hmac.compare_digest(supplied, cfg.token):
        raise HTTPException(status_code=401, detail="Unauthorized")


async def _sync_loop():
    while True:
        try:
            await syncer.run_once()
        except Exception as exc:  # pragma: no cover - keep the API alive
            print(f"[telegram-reader] sync error: {exc!r}", flush=True)
            await asyncio.sleep(cfg.sync_interval)


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(_sync_loop())
    yield
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task
    await syncer.bot.close()


app = FastAPI(title="Telegram reader", version="1.0.0", lifespan=lifespan)


@app.get("/healthz")
def healthz():
    return {"ok": True}


@app.get("/api/posts", dependencies=[Depends(_authorize)])
def list_posts(after: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500)):
    items = store.posts_after(after, limit)
    next_cursor = items[-1]["id"] if items else after
    return {"channel": cfg.channel, "posts": items, "next": next_cursor}


@app.post("/api/import", dependencies=[Depends(_authorize)])
def import_export(folder: str = Query(..., description="ChatExport_... folder name or path")):
    """Import a Telegram Desktop chat-export folder into the post list."""
    from . import importer

    try:
        return importer.import_folder(folder)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except (json.JSONDecodeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/media/{path:path}", dependencies=[Depends(_authorize)])
def get_media(path: str):
    base = os.path.abspath(cfg.media_dir)
    target = os.path.abspath(os.path.join(base, path))
    if not (target == base or target.startswith(base + os.sep)):
        raise HTTPException(status_code=400, detail="Bad path")
    if not os.path.isfile(target):
        raise HTTPException(status_code=404, detail="Not found")
    return FileResponse(target)
